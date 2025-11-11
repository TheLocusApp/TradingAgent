import yfinance as yf
import pandas as pd
import talib
from backtesting import Backtest, Strategy
import numpy as np

# Fetch data using yfinance
print("🌙 Moon Dev Backtest AI - Fetching Bitcoin Data...")
ticker = yf.Ticker("BTC-USD")
data = ticker.history(period="2y", interval="1d")
data.index.name = 'datetime'

# Clean and prepare data
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High', 
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

print(f"✨ Data loaded: {len(data)} candles | Period: {data.index[0]} to {data.index[-1]}")

class DivergentOscillator(Strategy):
    # Strategy parameters
    rsi_period = 14
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    atr_period = 14
    swing_lookback = 10
    
    def init(self):
        print("🚀 Initializing DivergentOscillator Strategy...")
        
        # Calculate indicators using self.I()
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, self.data.Close, 
                                                            fastperiod=self.macd_fast, 
                                                            slowperiod=self.macd_slow, 
                                                            signalperiod=self.macd_signal)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        
        # Swing highs and lows
        self.swing_high = self.I(talib.MAX, self.data.High, timeperiod=self.swing_lookback)
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=self.swing_lookback)
        
        print("📊 Indicators calculated: RSI, MACD, ATR, Swing Points")
        
        # Track divergence states
        self.bullish_divergence = False
        self.bearish_divergence = False
        self.last_swing_high = None
        self.last_swing_low = None
        
    def next(self):
        current_idx = len(self.data) - 1
        if current_idx < 30:  # Need enough data for reliable signals
            return
            
        # Get current values
        price = self.data.Close[-1]
        rsi_current = self.rsi[-1]
        macd_current = self.macd[-1]
        macd_signal_current = self.macd_signal[-1]
        macd_hist_current = self.macd_hist[-1]
        atr_current = self.atr[-1]
        swing_high_current = self.swing_high[-1]
        swing_low_current = self.swing_low[-1]
        
        # Look for divergence patterns (simplified implementation)
        self.detect_divergence()
        
        # Entry logic
        if not self.position:
            # Bullish divergence entry
            if (self.bullish_divergence and 
                price > swing_high_current and 
                macd_hist_current > self.macd_hist[-2] and 
                macd_current > macd_signal_current):
                
                stop_loss = price - (2 * atr_current)
                take_profit = price + (4 * atr_current)  # 1:2 risk-reward
                
                if stop_loss > 0:
                    print(f"📈 BULLISH DIVERGENCE ENTRY | Price: {price:.2f} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}")
                    self.buy(size=0.02, sl=stop_loss, tp=take_profit)
                    self.bullish_divergence = False
            
            # Bearish divergence entry  
            elif (self.bearish_divergence and 
                  price < swing_low_current and 
                  macd_hist_current < self.macd_hist[-2] and 
                  macd_current < macd_signal_current):
                  
                stop_loss = price + (2 * atr_current)
                take_profit = price - (4 * atr_current)  # 1:2 risk-reward
                
                print(f"📉 BEARISH DIVERGENCE ENTRY | Price: {price:.2f} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}")
                self.sell(size=0.02, sl=stop_loss, tp=take_profit)
                self.bearish_divergence = False
        
        # Check for opposite divergence to exit
        elif self.position and self.position.is_long:
            if self.bearish_divergence:
                print(f"🔄 EXIT LONG - Bearish divergence detected")
                self.position.close()
                
        elif self.position and self.position.is_short:
            if self.bullish_divergence:
                print(f"🔄 EXIT SHORT - Bullish divergence detected")
                self.position.close()
    
    def detect_divergence(self):
        """Simplified divergence detection - looks for basic RSI/price divergence patterns"""
        lookback = 20
        
        if len(self.data) < lookback + 10:
            return
            
        # Get recent price and RSI data
        recent_prices = self.data.Close[-lookback:]
        recent_rsi = self.rsi[-lookback:]
        recent_macd_hist = self.macd_hist[-lookback:]
        
        # Find significant highs and lows
        price_highs = []
        price_lows = []
        rsi_highs = []
        rsi_lows = []
        
        for i in range(5, len(recent_prices)-5):
            # Price highs
            if (recent_prices[i] == max(recent_prices[i-5:i+6])):
                price_highs.append((i, recent_prices[i]))
            # Price lows
            if (recent_prices[i] == min(recent_prices[i-5:i+6])):
                price_lows.append((i, recent_prices[i]))
            # RSI highs
            if (recent_rsi[i] == max(recent_rsi[i-3:i+4])):
                rsi_highs.append((i, recent_rsi[i]))
            # RSI lows
            if (recent_rsi[i] == min(recent_rsi[i-3:i+4])):
                rsi_lows.append((i, recent_rsi[i]))
        
        # Check for bearish divergence (price higher high, RSI lower high)
        if len(price_highs) >= 2 and len(rsi_highs) >= 2:
            last_price_high = price_highs[-1][1]
            prev_price_high = price_highs[-2][1]
            last_rsi_high = rsi_highs[-1][1]
            prev_rsi_high = rsi_highs[-2][1]
            
            if (last_price_high > prev_price_high and 
                last_rsi_high < prev_rsi_high and 
                abs(price_highs[-1][0] - price_highs[-2][0]) >= 3):
                
                # Check MACD confirmation
                current_macd_hist = self.macd_hist[-1]
                if current_macd_hist < 0 and current_macd_hist < self.macd_hist[-2]:
                    self.bearish_divergence = True
                    print(f"⚠️ BEARISH DIVERGENCE DETECTED | Price: {last_price_high:.2f} > {prev_price_high:.2f} | RSI: {last_rsi_high:.1f} < {prev_rsi_high:.1f}")
        
        # Check for bullish divergence (price lower low, RSI higher low)
        if len(price_lows) >= 2 and len(rsi_lows) >= 2:
            last_price_low = price_lows[-1][1]
            prev_price_low = price_lows[-2][1]
            last_rsi_low = rsi_lows[-1][1]
            prev_rsi_low = rsi_lows[-2][1]
            
            if (last_price_low < prev_price_low and 
                last_rsi_low > prev_rsi_low and 
                abs(price_lows[-1][0] - price_lows[-2][0]) >= 3):
                
                # Check MACD confirmation
                current_macd_hist = self.macd_hist[-1]
                if current_macd_hist > 0 and current_macd_hist > self.macd_hist[-2]:
                    self.bullish_divergence = True
                    print(f"⚠️ BULLISH DIVERGENCE DETECTED | Price: {last_price_low:.2f} < {prev_price_low:.2f} | RSI: {last_rsi_low:.1f} > {prev_rsi_low:.1f}")

print("🌙 Starting Backtest...")
bt = Backtest(data, DivergentOscillator, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)