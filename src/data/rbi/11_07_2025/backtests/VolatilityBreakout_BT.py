import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
import yfinance as yf

class VolatilityBreakout(Strategy):
    # Strategy parameters
    atr_period = 14
    ema_period = 9
    atr_multiplier = 1.5
    risk_per_trade = 0.02
    max_daily_loss = 0.05
    max_trades_per_day = 3
    
    def init(self):
        # Clean and prepare data for TA-Lib (convert to float64)
        close_prices = self.data.Close.astype(float)
        high_prices = self.data.High.astype(float)
        low_prices = self.data.Low.astype(float)
        volume_data = self.data.Volume.astype(float)
        
        # Calculate indicators using TA-Lib
        self.atr = self.I(talib.ATR, high_prices, low_prices, close_prices, timeperiod=self.atr_period)
        self.ema = self.I(talib.EMA, close_prices, timeperiod=self.ema_period)
        
        # Calculate VWAP manually (volume-weighted average price)
        def calculate_vwap(data):
            typical_price = (data.High + data.Low + data.Close) / 3
            vwap = (typical_price * data.Volume).cumsum() / data.Volume.cumsum()
            return vwap.values
        
        self.vwap = self.I(calculate_vwap, self.data)
        
        # Track daily metrics
        self.daily_trades = 0
        self.daily_pnl = 0
        self.current_date = None
        self.entry_price = None
        self.opening_atr = None
        self.thirty_min_high = None
        self.thirty_min_low = None
        
        # Moon Dev debug tracking
        self.trade_count = 0
        
    def calculate_position_size(self, entry_price, stop_loss):
        """Calculate position size based on 2% risk per trade"""
        risk_distance = abs(entry_price - stop_loss) / entry_price
        risk_amount = self.equity * self.risk_per_trade
        position_value = risk_amount / risk_distance
        size = position_value / self.equity
        return max(0.01, min(size, 0.5))  # Cap at 50% of equity
    
    def next(self):
        current_price = self.data.Close[-1]
        current_time = self.data.index[-1]
        
        # Reset daily counters on new day
        if self.current_date != current_time.date():
            self.current_date = current_time.date()
            self.daily_trades = 0
            self.daily_pnl = 0
            self.opening_atr = None
            self.thirty_min_high = None
            self.thirty_min_low = None
            print(f"🌙 Moon Dev: New trading day {self.current_date}")
        
        # Skip first 30 minutes (9:30-10:00 AM)
        if current_time.hour == 9 and current_time.minute < 30:
            return
            
        # Calculate opening ATR after 30 minutes
        if current_time.hour == 10 and current_time.minute == 0 and self.opening_atr is None:
            # Use first 30 minutes of data to calculate opening ATR
            morning_data = self.data.df.loc[self.data.df.index.time >= pd.Timestamp('09:30:00').time()]
            morning_data = morning_data.loc[morning_data.index.time <= pd.Timestamp('10:00:00').time()]
            
            if len(morning_data) > 0:
                high_30m = morning_data.High.astype(float).values
                low_30m = morning_data.Low.astype(float).values
                close_30m = morning_data.Close.astype(float).values
                
                if len(high_30m) >= 14:
                    opening_atr_val = talib.ATR(high_30m, low_30m, close_30m, timeperiod=14)[-1]
                    self.opening_atr = opening_atr_val
                    self.thirty_min_high = morning_data.High.max()
                    self.thirty_min_low = morning_data.Low.min()
                    print(f"🌙 Moon Dev: Opening ATR calculated: {self.opening_atr:.4f}")
                    print(f"🌙 Moon Dev: 30-min High: {self.thirty_min_high:.2f}, Low: {self.thirty_min_low:.2f}")
        
        # Check daily limits
        if self.daily_trades >= self.max_trades_per_day:
            return
            
        # Check daily loss limit
        if self.daily_pnl <= -self.max_daily_loss * self.equity:
            print(f"🚨 Moon Dev: Daily loss limit reached! PnL: {self.daily_pnl:.2f}")
            return
            
        # Exit all positions by 2:00 PM EST
        if current_time.hour >= 14 and self.position:
            print(f"🌙 Moon Dev: Time-based exit at 2:00 PM")
            self.position.close()
            return
            
        # Ensure we have all required data
        if (self.atr[-1] is None or self.ema[-1] is None or self.vwap[-1] is None or 
            self.opening_atr is None or self.thirty_min_high is None or self.thirty_min_low is None):
            return
        
        current_atr = self.atr[-1]
        current_ema = self.ema[-1]
        current_vwap = self.vwap[-1]
        current_volume = self.data.Volume[-1]
        
        # Calculate ATR threshold
        atr_threshold = self.opening_atr * self.atr_multiplier
        
        if not self.position:
            # Check for LONG entry conditions
            long_condition = (
                current_price > self.thirty_min_high and  # Break above 30-min high
                current_atr > atr_threshold and          # ATR exceeds threshold
                current_price > current_ema and          # Above EMA
                current_price > current_vwap and         # Above VWAP
                current_volume > self.data.Volume[-10:].mean()  # Volume expansion
            )
            
            # Check for SHORT entry conditions
            short_condition = (
                current_price < self.thirty_min_low and   # Break below 30-min low
                current_atr > atr_threshold and          # ATR exceeds threshold
                current_price < current_ema and          # Below EMA
                current_price < current_vwap and         # Below VWAP
                current_volume > self.data.Volume[-10:].mean()  # Volume expansion
            )
            
            if long_condition:
                entry_price = current_price
                stop_loss = entry_price - (current_atr * 0.5)  # 0.5x ATR stop
                take_profit = entry_price + current_atr        # 1x ATR target
                
                # Validate order conditions for long
                if stop_loss < entry_price < take_profit:
                    size = self.calculate_position_size(entry_price, stop_loss)
                    self.buy(size=size, sl=stop_loss, tp=take_profit)
                    self.entry_price = entry_price
                    self.daily_trades += 1
                    self.trade_count += 1
                    print(f"🚀 Moon Dev: LONG Entry #{self.trade_count} | Price: {entry_price:.2f} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}")
                    
            elif short_condition:
                entry_price = current_price
                stop_loss = entry_price + (current_atr * 0.5)  # 0.5x ATR stop
                take_profit = entry_price - current_atr        # 1x ATR target
                
                # Validate order conditions for short
                if take_profit < entry_price < stop_loss:
                    size = self.calculate_position_size(entry_price, stop_loss)
                    self.sell(size=size, sl=stop_loss, tp=take_profit)
                    self.entry_price = entry_price
                    self.daily_trades += 1
                    self.trade_count += 1
                    print(f"🔻 Moon Dev: SHORT Entry #{self.trade_count} | Price: {entry_price:.2f} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}")
        
        # Update daily PnL tracking
        if self.position:
            self.daily_pnl = self.position.pl

# Download QQQ data
print("🌙 Moon Dev: Downloading QQQ data...")
ticker = yf.Ticker("QQQ")
data = ticker.history(period="730d", interval="1h")  # Using 1h data for reliable backtesting

# Clean and prepare data
data = data.reset_index()
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Rename columns for backtesting.py
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

print(f"🌙 Moon Dev: Data loaded - {len(data)} bars from {data.index[0]} to {data.index[-1]}")

# Run backtest
bt = Backtest(data, VolatilityBreakout, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)