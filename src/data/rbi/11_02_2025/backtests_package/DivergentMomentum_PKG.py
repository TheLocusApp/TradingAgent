import yfinance as yf
import pandas as pd
import talib
from backtesting import Backtest, Strategy
import numpy as np

class DivergentMomentum(Strategy):
    # Strategy parameters
    rsi_period = 14
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    rsi_overbought = 70
    rsi_oversold = 30
    position_size_pct = 0.02  # 2% of capital per trade
    risk_reward_ratio = 2.0
    
    def init(self):
        # Calculate indicators using talib with proper float conversion
        print("🌙 Initializing DivergentMomentum Strategy...")
        
        # RSI indicator
        self.rsi = self.I(talib.RSI, self.data.Close.astype(float), timeperiod=self.rsi_period)
        
        # MACD indicator
        self.macd, self.macd_signal_line, self.macd_hist = self.I(
            talib.MACD, self.data.Close.astype(float), 
            fastperiod=self.macd_fast, 
            slowperiod=self.macd_slow, 
            signalperiod=self.macd_signal
        )
        
        print("✨ Indicators loaded: RSI(14), MACD(12,26,9)")
        
        # Track swing highs and lows for divergence detection
        self.swing_highs = []
        self.swing_lows = []
        self.bullish_divergences = []
        self.bearish_divergences = []
        
    def next(self):
        current_index = len(self.data) - 1
        
        # Skip if we don't have enough data
        if current_index < max(self.rsi_period, self.macd_slow) + 10:
            return
            
        # Detect swing highs and lows for divergence analysis
        self._detect_swings(current_index)
        
        # Check for divergences
        self._detect_divergences(current_index)
        
        # Calculate position size
        position_size = int(self.equity * self.position_size_pct / self.data.Close[-1])
        if position_size <= 0:
            return
            
        # ENTRY LOGIC
        if not self.position:
            # LONG ENTRY: Bullish RSI divergence + MACD confirmation
            if (self._has_bullish_divergence(current_index) and 
                self._macd_bullish_confirmation(current_index)):
                
                # Calculate stop loss below recent swing low
                stop_price = self._get_recent_swing_low(current_index)
                if stop_price and stop_price < self.data.Close[-1]:
                    # Calculate take profit based on risk-reward ratio
                    risk = self.data.Close[-1] - stop_price
                    tp_price = self.data.Close[-1] + (risk * self.risk_reward_ratio)
                    
                    print(f"🚀 LONG ENTRY: Price={self.data.Close[-1]:.2f}, SL={stop_price:.2f}, TP={tp_price:.2f}")
                    self.buy(size=position_size, sl=stop_price, tp=tp_price)
            
            # SHORT ENTRY: Bearish RSI divergence + MACD confirmation  
            elif (self._has_bearish_divergence(current_index) and 
                  self._macd_bearish_confirmation(current_index)):
                
                # Calculate stop loss above recent swing high
                stop_price = self._get_recent_swing_high(current_index)
                if stop_price and stop_price > self.data.Close[-1]:
                    # Calculate take profit based on risk-reward ratio
                    risk = stop_price - self.data.Close[-1]
                    tp_price = self.data.Close[-1] - (risk * self.risk_reward_ratio)
                    
                    print(f"📉 SHORT ENTRY: Price={self.data.Close[-1]:.2f}, SL={stop_price:.2f}, TP={tp_price:.2f}")
                    self.sell(size=position_size, sl=stop_price, tp=tp_price)
        
        # EXIT LOGIC for existing positions
        else:
            if self.position.is_long:
                # LONG EXIT conditions
                if (self.rsi[-1] >= self.rsi_overbought or
                    self._macd_bearish_confirmation(current_index)):
                    
                    print(f"💰 LONG EXIT: RSI={self.rsi[-1]:.1f}, Price={self.data.Close[-1]:.2f}")
                    self.position.close()
                    
            elif self.position.is_short:
                # SHORT EXIT conditions
                if (self.rsi[-1] <= self.rsi_oversold or
                    self._macd_bullish_confirmation(current_index)):
                    
                    print(f"💰 SHORT EXIT: RSI={self.rsi[-1]:.1f}, Price={self.data.Close[-1]:.2f}")
                    self.position.close()
    
    def _detect_swings(self, current_index):
        """Detect swing highs and lows in price and RSI"""
        lookback = 5
        
        # Only process every few bars to avoid excessive calculations
        if current_index % 3 != 0:
            return
            
        # Price swing highs (peaks)
        if current_index >= lookback * 2:
            window_highs = [self.data.High[i] for i in range(current_index - lookback, current_index + 1)]
            max_high_idx = np.argmax(window_highs)
            
            if max_high_idx == lookback:  # Current bar is the highest in the window
                self.swing_highs.append((current_index, self.data.High[current_index]))
                if len(self.swing_highs) > 10:
                    self.swing_highs.pop(0)
        
        # Price swing lows (valleys)
        if current_index >= lookback * 2:
            window_lows = [self.data.Low[i] for i in range(current_index - lookback, current_index + 1)]
            min_low_idx = np.argmin(window_lows)
            
            if min_low_idx == lookback:  # Current bar is the lowest in the window
                self.swing_lows.append((current_index, self.data.Low[current_index]))
                if len(self.swing_lows) > 10:
                    self.swing_lows.pop(0)
    
    def _detect_divergences(self, current_index):
        """Detect RSI divergences"""
        min_swings_required = 2
        
        # Bullish divergence: Lower price lows but higher RSI lows
        if len(self.swing_lows) >= min_swings_required:
            recent_lows = self.swing_lows[-2:]
            price_lows = [low for _, low in recent_lows]
            rsi_at_lows = [self.rsi[idx] for idx, _ in recent_lows]
            
            if (price_lows[-1] < price_lows[-2] and  # Lower price low
                rsi_at_lows[-1] > rsi_at_lows[-2] and  # Higher RSI low
                abs(price_lows[-1] - price_lows[-2]) / price_lows[-2] > 0.01):  # Significant price move
                
                self.bullish_divergences.append(current_index)
                print(f"🔍 BULLISH DIVERGENCE detected at {current_index}")
        
        # Bearish divergence: Higher price highs but lower RSI highs  
        if len(self.swing_highs) >= min_swings_required:
            recent_highs = self.swing_highs[-2:]
            price_highs = [high for _, high in recent_highs]
            
            # Get RSI values at swing high indices
            rsi_at_highs = []
            for idx, _ in recent_highs:
                if idx < len(self.rsi):
                    rsi_at_highs.append(self.rsi[idx])
            
            if (len(rsi_at_highs) == 2 and
                price_highs[-1] > price_highs[-2] and  # Higher price high
                rsi_at_highs[-1] < rsi_at_highs[-2] and  # Lower RSI high
                abs(price_highs[-1] - price_highs[-2]) / price_highs[-2] > 0.01):  # Significant price move
                
                self.bearish_divergences.append(current_index)
                print(f"🔍 BEARISH DIVERGENCE detected at {current_index}")
    
    def _has_bullish_divergence(self, current_index):
        """Check if we have a recent bullish divergence"""
        lookback = 10
        return any(idx >= current_index - lookback for idx in self.bullish_divergences)
    
    def _has_bearish_divergence(self, current_index):
        """Check if we have a recent bearish divergence"""
        lookback = 10
        return any(idx >= current_index - lookback for idx in self.bearish_divergences)
    
    def _macd_bullish_confirmation(self, current_index):
        """MACD bullish confirmation: MACD above signal OR histogram positive"""
        if current_index < 1:
            return False
            
        return (self.macd[-1] > self.macd_signal_line[-1] or 
                (self.macd_hist[-1] > 0 and self.macd_hist[-2] <= 0))
    
    def _macd_bearish_confirmation(self, current_index):
        """MACD bearish confirmation: MACD below signal OR histogram negative"""
        if current_index < 1:
            return False
            
        return (self.macd[-1] < self.macd_signal_line[-1] or 
                (self.macd_hist[-1] < 0 and self.macd_hist[-2] >= 0))
    
    def _get_recent_swing_low(self, current_index):
        """Get most recent swing low for stop loss placement"""
        if not self.swing_lows:
            return None
            
        # Find the most recent swing low that's not the current potential low
        recent_lows = [price for idx, price in self.swing_lows if idx < current_index - 2]
        return min(recent_lows) if recent_lows else None
    
    def _get_recent_swing_high(self, current_index):
        """Get most recent swing high for stop loss placement"""
        if not self.swing_highs:
            return None
            
        # Find the most recent swing high that's not the current potential high
        recent_highs = [price for idx, price in self.swing_highs if idx < current_index - 2]
        return max(recent_highs) if recent_highs else None

# Fetch Bitcoin data using yfinance
print("🌙 Fetching Bitcoin data from yfinance...")
ticker = yf.Ticker("BTC-USD")
data = ticker.history(period="2y", interval="1d")  # 2 years of daily data

# Clean and prepare data
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()], errors='ignore')

# Ensure proper column names for backtesting.py
data = data.rename(columns={
    'open': 'Open',
    'high': 'High', 
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

print(f"📊 Data loaded: {len(data)} bars from {data.index[0].date()} to {data.index[-1].date()}")

# Initialize and run backtest
print("🚀 Starting DivergentMomentum backtest...")
bt = Backtest(data, DivergentMomentum, cash=1000000, commission=.002)

# Run backtest
stats = bt.run()
print(stats)
print(stats._strategy)