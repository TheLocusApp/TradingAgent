import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
import yfinance as yf

class VolumeBounce(Strategy):
    # Strategy parameters
    support_lookback = 20
    resistance_lookback = 20
    volume_multiplier = 1.5
    risk_per_trade = 2.0
    stop_loss_pct = 0.15
    rr_ratio = 2.0
    
    def init(self):
        # Clean and prepare data for TA-Lib (convert to float64)
        close_prices = self.data.Close.astype(float)
        high_prices = self.data.High.astype(float)
        low_prices = self.data.Low.astype(float)
        volume_data = self.data.Volume.astype(float)
        
        # Calculate indicators using TA-Lib
        self.ema20 = self.I(talib.EMA, close_prices, timeperiod=20)
        self.volume_sma = self.I(talib.SMA, volume_data, timeperiod=20)
        
        # Support and resistance levels using rolling highs/lows
        self.support_levels = self.I(talib.MIN, low_prices, timeperiod=self.support_lookback)
        self.resistance_levels = self.I(talib.MAX, high_prices, timeperiod=self.resistance_lookback)
        
        # Track entry price manually
        self.entry_price = None
        self.reversal_candle_high = None
        self.reversal_candle_low = None
        
        print("🌙 Moon Dev VolumeBounce Strategy Initialized")
        print(f"📊 Support Lookback: {self.support_lookback}")
        print(f"📊 Resistance Lookback: {self.resistance_lookback}")
        print(f"📊 Volume Multiplier: {self.volume_multiplier}x")

    def calculate_position_size(self, entry_price, stop_loss_price):
        """Calculate position size based on risk percentage"""
        risk_distance = abs(entry_price - stop_loss_price) / entry_price
        risk_amount = self.equity * (self.risk_per_trade / 100)
        position_value = risk_amount / risk_distance
        size = position_value / self.equity
        size = max(0.01, min(size, 0.5))  # Cap at 50% equity
        return size

    def is_trading_hours(self, timestamp):
        """Check if current time is during high-volume trading hours"""
        hour = timestamp.hour
        minute = timestamp.minute
        
        # First 2 hours (9:30-11:30 ET)
        morning_session = (hour == 9 and minute >= 30) or (hour == 10) or (hour == 11 and minute <= 30)
        
        # Last hour (15:00-16:00 ET)
        afternoon_session = hour == 15
        
        return morning_session or afternoon_session

    def detect_reversal_pattern(self, current_idx):
        """Detect bullish or bearish reversal candlestick patterns"""
        if current_idx < 2:
            return None
            
        # Get recent candles for pattern detection
        open_prices = self.data.Open.astype(float)
        high_prices = self.data.High.astype(float)
        low_prices = self.data.Low.astype(float)
        close_prices = self.data.Close.astype(float)
        
        # Bullish patterns (hammer, bullish engulfing)
        prev_close = close_prices[current_idx-1]
        prev_open = open_prices[current_idx-1]
        prev_high = high_prices[current_idx-1]
        prev_low = low_prices[current_idx-1]
        
        current_close = close_prices[current_idx]
        current_open = open_prices[current_idx]
        current_high = high_prices[current_idx]
        current_low = low_prices[current_idx]
        
        # Hammer pattern
        hammer_body = abs(prev_close - prev_open)
        hammer_lower_wick = min(prev_open, prev_close) - prev_low
        hammer_upper_wick = prev_high - max(prev_open, prev_close)
        
        is_hammer = (hammer_lower_wick >= 2 * hammer_body and 
                    hammer_upper_wick <= hammer_body * 0.5)
        
        # Bullish engulfing
        is_bullish_engulfing = (prev_close < prev_open and 
                               current_close > current_open and
                               current_open <= prev_close and 
                               current_close >= prev_open)
        
        # Bearish patterns (shooting star, bearish engulfing)
        # Shooting star
        shooting_star_body = abs(prev_close - prev_open)
        shooting_star_upper_wick = prev_high - max(prev_open, prev_close)
        shooting_star_lower_wick = min(prev_open, prev_close) - prev_low
        
        is_shooting_star = (shooting_star_upper_wick >= 2 * shooting_star_body and 
                           shooting_star_lower_wick <= shooting_star_body * 0.5)
        
        # Bearish engulfing
        is_bearish_engulfing = (prev_close > prev_open and 
                               current_close < current_open and
                               current_open >= prev_close and 
                               current_close <= prev_open)
        
        if (is_hammer or is_bullish_engulfing) and current_close > prev_close:
            return "bullish"
        elif (is_shooting_star or is_bearish_engulfing) and current_close < prev_close:
            return "bearish"
        
        return None

    def next(self):
        current_idx = len(self.data) - 1
        current_price = self.data.Close[-1]
        current_volume = self.data.Volume[-1]
        current_time = self.data.index[-1]
        
        # Skip if not in high-volume trading hours
        if not self.is_trading_hours(current_time):
            return
            
        # Calculate current support and resistance
        support_level = self.support_levels[-1]
        resistance_level = self.resistance_levels[-1]
        avg_volume = self.volume_sma[-1]
        
        # Detect reversal pattern
        reversal_pattern = self.detect_reversal_pattern(current_idx)
        
        # Check for volume confirmation
        volume_confirm = current_volume > avg_volume * self.volume_multiplier
        
        if not self.position:
            # LONG ENTRY: Support bounce with bullish reversal
            if (reversal_pattern == "bullish" and 
                volume_confirm and
                abs(current_price - support_level) / support_level <= 0.002):  # Within 0.2% of support
                
                entry_price = current_price
                stop_loss = support_level * (1 - self.stop_loss_pct / 100)
                take_profit = entry_price + (entry_price - stop_loss) * self.rr_ratio
                
                # Validate order parameters
                if stop_loss < entry_price < take_profit:
                    size = self.calculate_position_size(entry_price, stop_loss)
                    self.buy(size=size, sl=stop_loss, tp=take_profit)
                    self.entry_price = entry_price
                    print(f"🚀 LONG ENTRY | Price: {entry_price:.2f} | SL: {stop_loss:.2f} | TP: {take_profit:.2f} | Size: {size:.1%}")
            
            # SHORT ENTRY: Resistance rejection with bearish reversal
            elif (reversal_pattern == "bearish" and 
                  volume_confirm and
                  abs(current_price - resistance_level) / resistance_level <= 0.002):  # Within 0.2% of resistance
                
                entry_price = current_price
                stop_loss = resistance_level * (1 + self.stop_loss_pct / 100)
                take_profit = entry_price - (stop_loss - entry_price) * self.rr_ratio
                
                # Validate order parameters
                if take_profit < entry_price < stop_loss:
                    size = self.calculate_position_size(entry_price, stop_loss)
                    self.sell(size=size, sl=stop_loss, tp=take_profit)
                    self.entry_price = entry_price
                    print(f"📉 SHORT ENTRY | Price: {entry_price:.2f} | SL: {stop_loss:.2f} | TP: {take_profit:.2f} | Size: {size:.1%}")
        
        else:
            # Check for exit conditions based on volume momentum
            if self.position.is_long:
                # Exit if volume decreases significantly during move
                if current_volume < avg_volume * 0.7:
                    self.position.close()
                    print(f"🌊 Volume momentum lost | Closing LONG | Price: {current_price:.2f}")
            
            elif self.position.is_short:
                # Exit if volume decreases significantly during move
                if current_volume < avg_volume * 0.7:
                    self.position.close()
                    print(f"🌊 Volume momentum lost | Closing SHORT | Price: {current_price:.2f}")

# Download SPY data using yfinance
print("📥 Downloading SPY data...")
ticker = yf.Ticker("SPY")
data = ticker.history(period="730d", interval="1h")  # Using 1h instead of 5m for reliability

# Clean and prepare data
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

print(f"📊 Data loaded: {len(data)} bars")
print(f"📅 Date range: {data.index.min()} to {data.index.max()}")

# Run backtest
print("🌙 Starting Moon Dev VolumeBounce Backtest...")
bt = Backtest(data, VolumeBounce, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)