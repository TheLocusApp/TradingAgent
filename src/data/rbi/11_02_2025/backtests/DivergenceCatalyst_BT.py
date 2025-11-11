import yfinance as yf
import pandas as pd
import talib
from backtesting import Backtest, Strategy
import numpy as np

class DivergenceCatalyst(Strategy):
    # Strategy parameters
    rsi_period = 14
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    rsi_overbought = 70
    rsi_oversold = 30
    max_hold_days = 10
    
    def init(self):
        # 🌙 Moon Dev Indicators - Using proper talib with float conversion
        print("🌙 Initializing DivergenceCatalyst Strategy...")
        
        # RSI for divergence detection
        self.rsi = self.I(talib.RSI, self.data.Close.astype(float), timeperiod=self.rsi_period)
        
        # MACD for momentum confirmation
        self.macd, self.macd_signal_line, self.macd_hist = self.I(
            talib.MACD, self.data.Close.astype(float), 
            fastperiod=self.macd_fast, slowperiod=self.macd_slow, signalperiod=self.macd_signal
        )
        
        # Volume for confirmation
        self.volume_sma = self.I(talib.SMA, self.data.Volume.astype(float), timeperiod=20)
        
        # Track entry days for time-based exit
        self.entry_day = None
        self.current_day = 0
        
        print("✨ Indicators initialized successfully!")

    def find_local_extremes(self, data_series, lookback=5):
        """Find local highs and lows in price/indicator data"""
        highs = []
        lows = []
        
        for i in range(lookback, len(data_series) - lookback):
            # Check if current point is a local high
            if all(data_series[i] >= data_series[i-j] for j in range(1, lookback+1)) and \
               all(data_series[i] >= data_series[i+j] for j in range(1, lookback+1)):
                highs.append((i, data_series[i]))
            
            # Check if current point is a local low
            if all(data_series[i] <= data_series[i-j] for j in range(1, lookback+1)) and \
               all(data_series[i] <= data_series[i+j] for j in range(1, lookback+1)):
                lows.append((i, data_series[i]))
        
        return highs, lows

    def detect_divergence(self):
        """Detect bullish and bearish divergences between price and RSI"""
        if len(self.data) < 20:  # Need enough data
            return None, None
            
        current_idx = len(self.data) - 1
        
        # Find local extremes in price and RSI
        price_highs, price_lows = self.find_local_extremes(self.data.Close, lookback=3)
        rsi_highs, rsi_lows = self.find_local_extremes(self.rsi, lookback=3)
        
        bullish_divergence = False
        bearish_divergence = False
        
        # Check for bullish divergence (price lower low, RSI higher low)
        if len(price_lows) >= 2 and len(rsi_lows) >= 2:
            recent_price_low_idx, recent_price_low = price_lows[-1]
            prev_price_low_idx, prev_price_low = price_lows[-2]
            recent_rsi_low_idx, recent_rsi_low = rsi_lows[-1]
            prev_rsi_low_idx, prev_rsi_low = rsi_lows[-2]
            
            # Price makes lower low but RSI makes higher low
            if (recent_price_low < prev_price_low and 
                recent_rsi_low > prev_rsi_low and
                abs(recent_price_low_idx - recent_rsi_low_idx) <= 5):
                bullish_divergence = True
                print(f"🚀 BULLISH DIVERGENCE detected! Price: {prev_price_low:.2f} -> {recent_price_low:.2f}, RSI: {prev_rsi_low:.2f} -> {recent_rsi_low:.2f}")
        
        # Check for bearish divergence (price higher high, RSI lower high)
        if len(price_highs) >= 2 and len(rsi_highs) >= 2:
            recent_price_high_idx, recent_price_high = price_highs[-1]
            prev_price_high_idx, prev_price_high = price_highs[-2]
            recent_rsi_high_idx, recent_rsi_high = rsi_highs[-1]
            prev_rsi_high_idx, prev_rsi_high = rsi_highs[-2]
            
            # Price makes higher high but RSI makes lower high
            if (recent_price_high > prev_price_high and 
                recent_rsi_high < prev_rsi_high and
                abs(recent_price_high_idx - recent_rsi_high_idx) <= 5):
                bearish_divergence = True
                print(f"📉 BEARISH DIVERGENCE detected! Price: {prev_price_high:.2f} -> {recent_price_high:.2f}, RSI: {prev_rsi_high:.2f} -> {recent_rsi_high:.2f}")
        
        return bullish_divergence, bearish_divergence

    def next(self):
        current_idx = len(self.data) - 1
        current_close = self.data.Close[-1]
        current_rsi = self.rsi[-1] if len(self.rsi) > current_idx else 50
        current_macd = self.macd[-1] if len(self.macd) > current_idx else 0
        current_macd_signal = self.macd_signal_line[-1] if len(self.macd_signal_line) > current_idx else 0
        current_macd_hist = self.macd_hist[-1] if len(self.macd_hist) > current_idx else 0
        
        # Update current day counter
        self.current_day += 1
        
        # Exit conditions for existing positions
        if self.position:
            # Time-based exit (max hold days)
            if self.entry_day and (self.current_day - self.entry_day) >= self.max_hold_days:
                print(f"⏰ Time-based exit after {self.max_hold_days} days")
                self.position.close()
                return
            
            # RSI-based exit conditions
            if self.position.is_long and current_rsi >= self.rsi_overbought:
                print(f"🎯 Long exit - RSI overbought: {current_rsi:.2f}")
                self.position.close()
                return
            elif self.position.is_short and current_rsi <= self.rsi_oversold:
                print(f"🎯 Short exit - RSI oversold: {current_rsi:.2f}")
                self.position.close()
                return
        
        # Only enter if no current position
        if not self.position:
            bullish_div, bearish_div = self.detect_divergence()
            
            # LONG ENTRY: Bullish divergence with MACD confirmation
            if bullish_div:
                # MACD momentum confirmation (histogram positive and/or MACD above signal)
                macd_confirmation = (current_macd_hist > 0 and current_macd_hist > self.macd_hist[-2] if len(self.macd_hist) > 1 else False) or \
                                   (current_macd > current_macd_signal)
                
                if macd_confirmation and current_rsi < 60:  # Avoid overbought entries
                    print(f"🚀 ENTERING LONG - Bullish divergence confirmed!")
                    
                    # Calculate position size (2% risk)
                    risk_per_trade = self.equity * 0.02
                    
                    # Find recent swing low for stop loss
                    price_lows, _ = self.find_local_extremes(self.data.Close, lookback=5)
                    if price_lows:
                        stop_price = price_lows[-1][1] * 0.99  # 1% below swing low
                        risk_per_share = current_close - stop_price
                        
                        if risk_per_share > 0:
                            size = min(risk_per_trade / risk_per_share, self.equity * 0.95 / current_close)
                            tp_price = current_close + (2 * risk_per_share)  # 2:1 reward ratio
                            
                            if size > 0:
                                self.buy(size=size, sl=stop_price, tp=tp_price)
                                self.entry_day = self.current_day
                                print(f"📊 Long: Size={size:.2f}, SL={stop_price:.2f}, TP={tp_price:.2f}")
            
            # SHORT ENTRY: Bearish divergence with MACD confirmation
            elif bearish_div:
                # MACD momentum confirmation (histogram negative and/or MACD below signal)
                macd_confirmation = (current_macd_hist < 0 and current_macd_hist < self.macd_hist[-2] if len(self.macd_hist) > 1 else False) or \
                                   (current_macd < current_macd_signal)
                
                if macd_confirmation and current_rsi > 40:  # Avoid oversold entries
                    print(f"📉 ENTERING SHORT - Bearish divergence confirmed!")
                    
                    # Calculate position size (2% risk)
                    risk_per_trade = self.equity * 0.02
                    
                    # Find recent swing high for stop loss
                    _, price_highs = self.find_local_extremes(self.data.Close, lookback=5)
                    if price_highs:
                        stop_price = price_highs[-1][1] * 1.01  # 1% above swing high
                        risk_per_share = stop_price - current_close
                        
                        if risk_per_share > 0:
                            size = min(risk_per_trade / risk_per_share, self.equity * 0.95 / current_close)
                            tp_price = current_close - (2 * risk_per_share)  # 2:1 reward ratio
                            
                            if size > 0:
                                self.sell(size=size, sl=stop_price, tp=tp_price)
                                self.entry_day = self.current_day
                                print(f"📊 Short: Size={size:.2f}, SL={stop_price:.2f}, TP={tp_price:.2f}")

# 🌙 Moon Dev Data Fetching
print("🌙 Fetching SPY data from yfinance...")
ticker = yf.Ticker("SPY")
data = ticker.history(period="2y", interval="1d")
data.index.name = 'datetime'

print(f"📊 Data columns: {list(data.columns)}")
print(f"📈 Data shape: {data.shape}")
print(f"📅 Date range: {data.index[0]} to {data.index[-1]}")

# Verify we have the required columns in Title Case
required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
if all(col in data.columns for col in required_columns):
    print("✅ All required columns present!")
else:
    print("❌ Missing required columns!")

# Run backtest with 1,000,000 initial capital
print("🚀 Starting Backtest...")
bt = Backtest(data, DivergenceCatalyst, cash=1000000, commission=.002)

stats = bt.run()
print(stats)