import pandas as pd
import numpy as np
import yfinance as yf
import talib
from backtesting import Backtest, Strategy

def load_data():
    ticker = yf.Ticker("BTC-USD")
    data = ticker.history(period="2y", interval="1d")
    data.columns = data.columns.str.strip()
    required = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in data.columns for col in required):
        raise ValueError(f"Missing required columns. Got: {list(data.columns)}")
    return data

class DivergenceConfirmer(Strategy):
    rsi_period = 14
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    risk_per_trade = 0.02
    max_positions = 3
    
    def init(self):
        close_prices = self.data.Close.astype(float)
        high_prices = self.data.High.astype(float)
        low_prices = self.data.Low.astype(float)
        
        self.rsi = self.I(talib.RSI, close_prices, timeperiod=self.rsi_period)
        self.macd, self.macd_signal_line, self.macd_hist = self.I(talib.MACD, close_prices, 
                                                                  fastperiod=self.macd_fast,
                                                                  slowperiod=self.macd_slow, 
                                                                  signalperiod=self.macd_signal)
        
        self.high_20 = self.I(talib.MAX, high_prices, timeperiod=20)
        self.low_20 = self.I(talib.MIN, low_prices, timeperiod=20)
        
        self.swing_highs = []
        self.swing_lows = []
        self.divergence_signals = []
        
    def next(self):
        if len(self.data) < 30:
            return
            
        current_idx = len(self.data) - 1
        current_close = self.data.Close[-1]
        current_rsi = self.rsi[-1]
        current_macd_hist = self.macd_hist[-1] if self.macd_hist[-1] is not None else 0
        
        if len(self.positions) >= self.max_positions:
            return
            
        self.detect_swing_points(current_idx)
        self.detect_divergence(current_idx)
        
        if self.has_bullish_divergence() and self.bullish_macd_confirmation():
            self.enter_long()
            
        elif self.has_bearish_divergence() and self.bearish_macd_confirmation():
            self.enter_short()
            
        self.manage_exits()
    
    def detect_swing_points(self, current_idx):
        if current_idx < 5:
            return
            
        lookback = 5
        high_slice = self.data.High[current_idx-lookback:current_idx+1]
        low_slice = self.data.Low[current_idx-lookback:current_idx+1]
        
        if len(high_slice) >= 3:
            center_idx = len(high_slice) // 2
            if high_slice[center_idx] == max(high_slice):
                self.swing_highs.append((current_idx - (lookback - center_idx), high_slice[center_idx]))
                
        if len(low_slice) >= 3:
            center_idx = len(low_slice) // 2
            if low_slice[center_idx] == min(low_slice):
                self.swing_lows.append((current_idx - (lookback - center_idx), low_slice[center_idx]))
                
        self.swing_highs = [sh for sh in self.swing_highs if current_idx - sh[0] <= 20]
        self.swing_lows = [sl for sl in self.swing_lows if current_idx - sl[0] <= 20]
    
    def detect_divergence(self, current_idx):
        if len(self.swing_highs) < 2 or len(self.swing_lows) < 2:
            return
            
        latest_swing_high_idx, latest_swing_high = self.swing_highs[-1]
        prev_swing_high_idx, prev_swing_high = self.swing_highs[-2]
        
        latest_swing_low_idx, latest_swing_low = self.swing_lows[-1]
        prev_swing_low_idx, prev_swing_low = self.swing_lows[-2]
        
        latest_rsi_high = max(self.rsi[max(0,latest_swing_high_idx-1):latest_swing_high_idx+2])
        prev_rsi_high = max(self.rsi[max(0,prev_swing_high_idx-1):prev_swing_high_idx+2])
        
        latest_rsi_low = min(self.rsi[max(0,latest_swing_low_idx-1):latest_swing_low_idx+2])
        prev_rsi_low = min(self.rsi[max(0,prev_swing_low_idx-1):prev_swing_low_idx+2])
        
        bearish_div = (latest_swing_high > prev_swing_high and 
                      latest_rsi_high < prev_rsi_high and
                      current_idx - latest_swing_high_idx <= 3)
        
        bullish_div = (latest_swing_low < prev_swing_low and 
                      latest_rsi_low > prev_rsi_low and
                      current_idx - latest_swing_low_idx <= 3)
        
        if bearish_div:
            self.divergence_signals.append(('bearish', current_idx))
        elif bullish_div:
            self.divergence_signals.append(('bullish', current_idx))
            
        self.divergence_signals = [sig for sig in self.divergence_signals if current_idx - sig[1] <= 10]
    
    def has_bullish_divergence(self):
        return any(sig[0] == 'bullish' for sig in self.divergence_signals)
    
    def has_bearish_divergence(self):
        return any(sig[0] == 'bearish' for sig in self.divergence_signals)
    
    def bullish_macd_confirmation(self):
        if len(self.macd_hist) < 3:
            return False
        current_hist = self.macd_hist[-1] if self.macd_hist[-1] is not None else 0
        prev_hist = self.macd_hist[-2] if self.macd_hist[-2] is not None else 0
        return current_hist > 0 and current_hist > prev_hist
    
    def bearish_macd_confirmation(self):
        if len(self.macd_hist) < 3:
            return False
        current_hist = self.macd_hist[-1] if self.macd_hist[-1] is not None else 0
        prev_hist = self.macd_hist[-2] if self.macd_hist[-2] is not None else 0
        return current_hist < 0 and current_hist < prev_hist
    
    def enter_long(self):
        if len(self.swing_lows) < 1:
            return
            
        entry_price = self.data.Close[-1]
        stop_loss_level = min(sl[1] for sl in self.swing_lows[-2:]) if len(self.swing_lows) >= 2 else self.swing_lows[-1][1]
        stop_loss_price = stop_loss_level * 0.995
        
        if stop_loss_price >= entry_price:
            print(f"🌙 MOON DEV DEBUG: Long order validation failed - SL: {stop_loss_price}, Entry: {entry_price}")
            return
            
        risk_amount = entry_price - stop_loss_price
        if risk_amount <= 0:
            return
            
        position_size = (self.risk_per_trade * self.equity) / risk_amount
        position_size = int(round(position_size))
        
        take_profit_price = entry_price + (2 * risk_amount)
        
        if take_profit_price <= entry_price:
            print(f"🌙 MOON DEV DEBUG: Long order validation failed - TP: {take_profit_price}, Entry: {entry_price}")
            return
            
        if position_size > 0:
            print(f"🌙 MOON DEV: BULLISH DIVERGENCE CONFIRMED! Entering LONG at {entry_price:.2f}")
            self.buy(size=position_size, sl=stop_loss_price, tp=take_profit_price)
    
    def enter_short(self):
        if len(self.swing_highs) < 1:
            return
            
        entry_price = self.data.Close[-1]
        stop_loss_level = max(sh[1] for sh in self.swing_highs[-2:]) if len(self.swing_highs) >= 2 else self.swing_highs[-1][1]
        stop_loss_price = stop_loss_level * 1.005
        
        if stop_loss_price <= entry_price:
            print(f"🌙 MOON DEV DEBUG: Short order validation failed - SL: {stop_loss_price}, Entry: {entry_price}")
            return
            
        risk_amount = stop_loss_price - entry_price
        if risk_amount <= 0:
            return
            
        position_size = (self.risk_per_trade * self.equity) / risk_amount
        position_size = int(round(position_size))
        
        take_profit_price = entry_price - (2 * risk_amount)
        
        if take_profit_price >= entry_price:
            print(f"🌙 MOON DEV DEBUG: Short order validation failed - TP: {take_profit_price}, Entry: {entry_price}")
            return
            
        if position_size > 0:
            print(f"🌙 MOON DEV: BEARISH DIVERGENCE CONFIRMED! Entering SHORT at {entry_price:.2f}")
            self.sell(size=position_size, sl=stop_loss_price, tp=take_profit_price)
    
    def manage_exits(self):
        for position in self.positions:
            if len(position.entry_bar) > 0:
                days_in_trade = len(self.data) - position.entry_bar
                if days_in_trade >= 7:
                    print(f"🌙 MOON DEV: Time-based exit after 7 days")
                    position.close()

data = load_data()
bt = Backtest(data, DivergenceConfirmer, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)