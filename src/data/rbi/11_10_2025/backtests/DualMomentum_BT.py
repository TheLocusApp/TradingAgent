import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import talib

class DualMomentum(Strategy):
    # Strategy parameters
    ema_fast_period = 8
    ema_slow_period = 13
    risk_per_trade = 1.5  # 1.5% risk per trade
    max_daily_loss = 5.0  # 5% maximum daily loss
    
    def init(self):
        # Clean data and ensure proper types for TA-Lib
        close_prices = self.data.Close.astype(float)
        high_prices = self.data.High.astype(float)
        low_prices = self.data.Low.astype(float)
        
        # Calculate EMAs using TA-Lib
        self.ema_fast = self.I(talib.EMA, close_prices, timeperiod=self.ema_fast_period)
        self.ema_slow = self.I(talib.EMA, close_prices, timeperiod=self.ema_slow_period)
        
        # Track daily metrics
        self.daily_equity = [self.equity]
        self.daily_dates = [self.data.index[0].date()]
        self.entry_price = None
        
        print(f"🌙 MOON DEV: DualMomentum Strategy Initialized")
        print(f"🌙 EMA Fast: {self.ema_fast_period}, EMA Slow: {self.ema_slow_period}")
        print(f"🌙 Risk per trade: {self.risk_per_trade}%, Max daily loss: {self.max_daily_loss}%")

    def calculate_position_size(self, entry_price, stop_loss_price):
        """Calculate position size based on risk percentage"""
        if entry_price == 0:
            return 0.0
            
        # Calculate risk distance as percentage
        risk_distance_pct = abs(entry_price - stop_loss_price) / entry_price
        
        if risk_distance_pct == 0:
            return 0.0
            
        # Calculate position size as fraction of equity
        risk_amount = self.equity * (self.risk_per_trade / 100)
        position_value = risk_amount / risk_distance_pct
        size = position_value / self.equity
        
        # Ensure size is between 0.01 and 0.5 (1% to 50% of equity)
        size = max(0.01, min(size, 0.5))
        
        return size

    def calculate_stop_loss(self, is_long, current_price):
        """Calculate stop loss based on recent swing levels"""
        lookback = 5
        if len(self.data.Close) < lookback:
            return current_price * 0.99 if is_long else current_price * 1.01
            
        if is_long:
            # For long positions: stop below recent low
            recent_low = min(self.data.Low.astype(float)[-lookback:])
            stop_loss = recent_low * 0.995  # 0.5% below recent low
        else:
            # For short positions: stop above recent high
            recent_high = max(self.data.High.astype(float)[-lookback:])
            stop_loss = recent_high * 1.005  # 0.5% above recent high
            
        return stop_loss

    def check_daily_loss_limit(self):
        """Check if daily loss limit has been exceeded"""
        current_date = self.data.index[-1].date()
        
        # Update daily tracking
        if current_date != self.daily_dates[-1]:
            self.daily_dates.append(current_date)
            self.daily_equity.append(self.equity)
        else:
            self.daily_equity[-1] = self.equity
            
        # Calculate today's return
        if len(self.daily_equity) >= 2:
            today_return = (self.daily_equity[-1] - self.daily_equity[-2]) / self.daily_equity[-2] * 100
            if today_return <= -self.max_daily_loss:
                print(f"🌙 MOON DEV: Daily loss limit reached! Today's return: {today_return:.2f}%")
                return True
                
        return False

    def next(self):
        current_price = self.data.Close[-1]
        current_time = self.data.index[-1]
        
        # Skip trading during first 30 minutes (if data has time information)
        if hasattr(current_time, 'hour'):
            if current_time.hour == 9 and current_time.minute < 30:
                return
        
        # Check daily loss limit
        if self.check_daily_loss_limit():
            if self.position:
                print(f"🌙 MOON DEV: Closing position due to daily loss limit")
                self.position.close()
            return
        
        # Ensure we have enough data for EMAs
        if (self.ema_fast[-1] is None or self.ema_slow[-1] is None or 
            self.ema_fast[-2] is None or self.ema_slow[-2] is None):
            return
            
        # Calculate crossover signals
        fast_above_slow_now = self.ema_fast[-1] > self.ema_slow[-1]
        fast_above_slow_prev = self.ema_fast[-2] > self.ema_slow[-2]
        
        bullish_crossover = not fast_above_slow_prev and fast_above_slow_now
        bearish_crossover = fast_above_slow_prev and not fast_above_slow_now
        
        if not self.position:
            # No position - look for entry signals
            if bullish_crossover:
                # LONG ENTRY: EMA fast crosses above EMA slow
                entry_price = current_price
                stop_loss = self.calculate_stop_loss(True, entry_price)
                
                # Validate long order: SL < Entry
                if stop_loss < entry_price:
                    size = self.calculate_position_size(entry_price, stop_loss)
                    if size > 0:
                        self.buy(size=size, sl=stop_loss)
                        self.entry_price = entry_price
                        print(f"🌙 MOON DEV: LONG ENTRY | Price: {entry_price:.2f} | Size: {size:.3f} | SL: {stop_loss:.2f}")
                
            elif bearish_crossover:
                # SHORT ENTRY: EMA fast crosses below EMA slow
                entry_price = current_price
                stop_loss = self.calculate_stop_loss(False, entry_price)
                
                # Validate short order: Entry < SL
                if entry_price < stop_loss:
                    size = self.calculate_position_size(entry_price, stop_loss)
                    if size > 0:
                        self.sell(size=size, sl=stop_loss)
                        self.entry_price = entry_price
                        print(f"🌙 MOON DEV: SHORT ENTRY | Price: {entry_price:.2f} | Size: {size:.3f} | SL: {stop_loss:.2f}")
                        
        else:
            # We have a position - look for exit signals
            if self.position.is_long and bearish_crossover:
                # EXIT LONG: EMA fast crosses below EMA slow
                self.position.close()
                print(f"🌙 MOON DEV: EXIT LONG | Price: {current_price:.2f} | Crossover Exit")
                
            elif self.position.is_short and bullish_crossover:
                # EXIT SHORT: EMA fast crosses above EMA slow
                self.position.close()
                print(f"🌙 MOON DEV: EXIT SHORT | Price: {current_price:.2f} | Crossover Exit")

# Data preparation and backtest execution
import yfinance as yf

print("🌙 MOON DEV: Downloading QQQ data...")
ticker = yf.Ticker("QQQ")

# Use 1-hour data instead of 5-minute for reliable backtesting
data = ticker.history(period="730d", interval="1h")

# Reset index and clean columns
data = data.reset_index()
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Rename columns to match backtesting.py requirements
data = data.rename(columns={
    'datetime': 'datetime',
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# Set datetime as index
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

print(f"🌙 MOON DEV: Data loaded successfully | Period: {len(data)} bars")
print(f"🌙 MOON DEV: Data range: {data.index[0]} to {data.index[-1]}")

# Run backtest
bt = Backtest(data, DualMomentum, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)