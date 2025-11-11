import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
import yfinance as yf
from datetime import time, datetime

class MicroMomentum(Strategy):
    # Strategy parameters
    ema_period = 2
    risk_per_trade = 0.02  # 2% risk per trade
    stop_loss_pct = 0.005  # 0.5% stop loss
    max_positions = 3
    daily_loss_limit = 0.05  # 5% daily loss limit
    
    def init(self):
        # Clean and prepare data for TA-Lib (convert to float64)
        close_prices = self.data.Close.astype(float)
        high_prices = self.data.High.astype(float)
        low_prices = self.data.Low.astype(float)
        volume_data = self.data.Volume.astype(float)
        
        # Calculate 2-period EMA using TA-Lib
        self.ema_2 = self.I(talib.EMA, close_prices, timeperiod=self.ema_period)
        
        # Track entry prices and daily P&L
        self.entry_price = None
        self.daily_equity = [self.equity]
        self.current_positions = 0
        
        print("🌙 Moon Dev MicroMomentum Strategy Initialized")
        print(f"📊 EMA Period: {self.ema_period}")
        print(f"💰 Risk per Trade: {self.risk_per_trade*100}%")
        print(f"🛑 Stop Loss: {self.stop_loss_pct*100}%")
        
    def calculate_position_size(self, entry_price, stop_loss_price):
        """Calculate position size as fraction of equity (0-1)"""
        risk_distance = abs(entry_price - stop_loss_price) / entry_price
        risk_amount = self.equity * self.risk_per_trade
        position_value = risk_amount / risk_distance
        size = position_value / self.equity
        return max(0.01, min(size, 0.5))  # Cap at 50% equity
        
    def is_market_hours(self, current_time):
        """Check if current time is within trading hours (9:30 AM - 4:00 PM)"""
        market_open = time(9, 30)
        market_close = time(16, 0)
        return market_open <= current_time.time() <= market_close
        
    def avoid_first_last_30min(self, current_time):
        """Avoid first and last 30 minutes of trading"""
        first_30_end = time(10, 0)
        last_30_start = time(15, 30)
        return first_30_end <= current_time.time() <= last_30_start
        
    def should_exit_early(self, current_time):
        """Mandatory exit by 3:45 PM"""
        exit_time = time(15, 45)
        return current_time.time() >= exit_time
        
    def check_daily_loss_limit(self):
        """Check if daily loss limit reached"""
        if len(self.daily_equity) > 1:
            daily_return = (self.equity - self.daily_equity[0]) / self.daily_equity[0]
            if daily_return <= -self.daily_loss_limit:
                print(f"🚨 DAILY LOSS LIMIT REACHED: {daily_return*100:.2f}%")
                return True
        return False
        
    def next(self):
        current_time = self.data.index[-1]
        current_price = self.data.Close[-1]
        current_ema = self.ema_2[-1]
        prev_price = self.data.Close[-2] if len(self.data.Close) > 1 else current_price
        prev_ema = self.ema_2[-2] if len(self.ema_2) > 1 else current_ema
        
        # Update daily equity tracking
        if len(self.daily_equity) == 0 or current_time.date() != pd.Timestamp(self.daily_equity[0]).date():
            self.daily_equity = [self.equity]
        else:
            self.daily_equity.append(self.equity)
            
        # Check daily loss limit
        if self.check_daily_loss_limit():
            if self.position:
                self.position.close()
                print("🔴 FORCED EXIT: Daily loss limit reached")
            return
            
        # Mandatory exit by 3:45 PM
        if self.position and self.should_exit_early(current_time):
            self.position.close()
            print("🕒 MANDATORY EXIT: 3:45 PM cutoff")
            return
            
        # Only trade during market hours
        if not self.is_market_hours(current_time):
            return
            
        # Avoid first and last 30 minutes
        if not self.avoid_first_last_30min(current_time):
            return
            
        # Check if we have enough data for EMA calculation
        if pd.isna(current_ema) or pd.isna(prev_ema):
            return
            
        # Count current positions
        self.current_positions = 1 if self.position else 0
        
        if not self.position and self.current_positions < self.max_positions:
            # LONG ENTRY SIGNAL: Price crosses above EMA with confirmation
            if (prev_price <= prev_ema and current_price > current_ema and 
                self.data.Close[-2] > self.ema_2[-2]):  # Confirmation candle
                
                entry_price = current_price
                stop_loss = entry_price * (1 - self.stop_loss_pct)
                take_profit = entry_price * (1 + (2 * self.stop_loss_pct))  # 2:1 reward:risk
                
                # Validate order parameters
                if stop_loss < entry_price < take_profit:
                    size = self.calculate_position_size(entry_price, stop_loss)
                    self.buy(size=size, sl=stop_loss, tp=take_profit)
                    self.entry_price = entry_price
                    print(f"🟢 LONG ENTRY | Price: ${entry_price:.2f} | EMA: ${current_ema:.2f} | Size: {size:.3f}")
                    
            # SHORT ENTRY SIGNAL: Price crosses below EMA with confirmation  
            elif (prev_price >= prev_ema and current_price < current_ema and 
                  self.data.Close[-2] < self.ema_2[-2]):  # Confirmation candle
                  
                entry_price = current_price
                stop_loss = entry_price * (1 + self.stop_loss_pct)
                take_profit = entry_price * (1 - (2 * self.stop_loss_pct))  # 2:1 reward:risk
                
                # Validate order parameters
                if take_profit < entry_price < stop_loss:
                    size = self.calculate_position_size(entry_price, stop_loss)
                    self.sell(size=size, sl=stop_loss, tp=take_profit)
                    self.entry_price = entry_price
                    print(f"🔴 SHORT ENTRY | Price: ${entry_price:.2f} | EMA: ${current_ema:.2f} | Size: {size:.3f}")
                    
        elif self.position:
            # EXIT LOGIC: Price crosses back through EMA
            if self.position.is_long:
                # Long exit: Price crosses below EMA with confirmation
                if (prev_price >= prev_ema and current_price < current_ema and 
                    self.data.Close[-2] < self.ema_2[-2]):
                    self.position.close()
                    pnl_pct = (current_price - self.entry_price) / self.entry_price * 100
                    print(f"🟡 LONG EXIT | Price: ${current_price:.2f} | PnL: {pnl_pct:.2f}%")
                    
            elif self.position.is_short:
                # Short exit: Price crosses above EMA with confirmation
                if (prev_price <= prev_ema and current_price > current_ema and 
                    self.data.Close[-2] > self.ema_2[-2]):
                    self.position.close()
                    pnl_pct = (self.entry_price - current_price) / self.entry_price * 100
                    print(f"🟡 SHORT EXIT | Price: ${current_price:.2f} | PnL: {pnl_pct:.2f}%")

# Download QQQ data
print("📥 Downloading QQQ data...")
ticker = yf.Ticker("QQQ")
data = ticker.history(period="60d", interval="1h")  # Using 1h instead of 2m due to yfinance limits

# Clean and prepare data
data = data.reset_index()
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()], errors='ignore')

# Rename columns for backtesting.py
data = data.rename(columns={
    'date': 'datetime',
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# Set datetime as index
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

print(f"📊 Data loaded: {len(data)} bars")
print(f"📅 Date range: {data.index[0]} to {data.index[-1]}")

# Run backtest
print("🚀 Starting backtest...")
bt = Backtest(data, MicroMomentum, cash=1000000, commission=0.002)
stats = bt.run()
print(stats)
print(stats._strategy)