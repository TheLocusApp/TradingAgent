import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
import yfinance as yf

def load_data():
    ticker = yf.Ticker("BTC-USD")
    data = ticker.history(period="2y", interval="1d")
    
    data = data.reset_index()
    data.columns = data.columns.str.strip()
    data = data.rename(columns={
        'Date': 'datetime',
        'Open': 'Open',
        'High': 'High',
        'Low': 'Low',
        'Close': 'Close',
        'Volume': 'Volume'
    })
    
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    
    return data

class DivergentMomentum(Strategy):
    rsi_period = 14
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    risk_per_trade = 0.02
    atr_period = 14
    
    def init(self):
        close = self.data.Close.astype(float)
        high = self.data.High.astype(float)
        low = self.data.Low.astype(float)
        
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.macd, self.macd_signal_line, self.macd_hist = self.I(talib.MACD, close, 
                                                                  fastperiod=self.macd_fast,
                                                                  slowperiod=self.macd_slow,
                                                                  signalperiod=self.macd_signal)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        
        self.swing_highs = self.I(talib.MAX, high, timeperiod=5)
        self.swing_lows = self.I(talib.MIN, low, timeperiod=5)
        
        self.last_rsi_high = None
        self.last_rsi_low = None
        self.last_price_high = None
        self.last_price_low = None
        
    def next(self):
        if len(self.data) < 30:
            return
            
        current_rsi = self.rsi[-1]
        current_price = self.data.Close[-1]
        current_macd = self.macd[-1] if self.macd[-1] is not None else 0
        current_macd_signal = self.macd_signal_line[-1] if self.macd_signal_line[-1] is not None else 0
        current_macd_hist = self.macd_hist[-1] if self.macd_hist[-1] is not None else 0
        
        if np.isnan(current_rsi) or np.isnan(current_macd):
            return
            
        self.detect_swings()
        
        if not self.position:
            self.check_entries(current_rsi, current_price, current_macd, current_macd_signal, current_macd_hist)
        else:
            self.check_exits(current_rsi, current_macd, current_macd_signal)
    
    def detect_swings(self):
        if len(self.data) < 10:
            return
            
        current_rsi = self.rsi[-1]
        current_price = self.data.Close[-1]
        
        if len(self.rsi) >= 5:
            rsi_window = self.rsi[-5:]
            price_window = self.data.Close[-5:]
            
            if current_rsi == max(rsi_window):
                self.last_rsi_high = current_rsi
                self.last_price_high = current_price
                
            if current_rsi == min(rsi_window):
                self.last_rsi_low = current_rsi
                self.last_price_low = current_price
    
    def check_entries(self, current_rsi, current_price, current_macd, current_macd_signal, current_macd_hist):
        bullish_divergence = self.check_bullish_divergence()
        bearish_divergence = self.check_bearish_divergence()
        macd_bullish = current_macd > current_macd_signal or current_macd_hist > 0
        macd_bearish = current_macd < current_macd_signal or current_macd_hist < 0
        
        if bullish_divergence and macd_bullish:
            self.enter_long(current_price)
        elif bearish_divergence and macd_bearish:
            self.enter_short(current_price)
    
    def check_bullish_divergence(self):
        if self.last_rsi_low is None or self.last_price_low is None:
            return False
            
        current_rsi = self.rsi[-1]
        current_price = self.data.Close[-1]
        prev_rsi = self.rsi[-2] if len(self.rsi) >= 2 else current_rsi
        prev_price = self.data.Close[-2] if len(self.data) >= 2 else current_price
        
        price_making_lower_lows = current_price < prev_price and prev_price < self.last_price_low
        rsi_making_higher_lows = current_rsi > prev_rsi and prev_rsi > self.last_rsi_low
        
        return price_making_lower_lows and rsi_making_higher_lows
    
    def check_bearish_divergence(self):
        if self.last_rsi_high is None or self.last_price_high is None:
            return False
            
        current_rsi = self.rsi[-1]
        current_price = self.data.Close[-1]
        prev_rsi = self.rsi[-2] if len(self.rsi) >= 2 else current_rsi
        prev_price = self.data.Close[-2] if len(self.data) >= 2 else current_price
        
        price_making_higher_highs = current_price > prev_price and prev_price > self.last_price_high
        rsi_making_lower_highs = current_rsi < prev_rsi and prev_rsi < self.last_rsi_high
        
        return price_making_higher_highs and rsi_making_lower_highs
    
    def enter_long(self, entry_price):
        atr_value = self.atr[-1] if self.atr[-1] is not None else entry_price * 0.02
        stop_loss = entry_price - (2 * atr_value)
        take_profit = entry_price + (4 * atr_value)
        
        risk_amount = self.risk_per_trade * self.equity
        risk_per_share = entry_price - stop_loss
        position_size = int(round(risk_amount / risk_per_share)) if risk_per_share > 0 else 0
        
        if position_size > 0:
            print(f"🌙 MOON DEV LONG SIGNAL! 🚀")
            print(f"💰 Entry: ${entry_price:.2f} | SL: ${stop_loss:.2f} | TP: ${take_profit:.2f}")
            print(f"📊 Position Size: {position_size} shares")
            self.buy(size=position_size, sl=stop_loss, tp=take_profit)
    
    def enter_short(self, entry_price):
        atr_value = self.atr[-1] if self.atr[-1] is not None else entry_price * 0.02
        stop_loss = entry_price + (2 * atr_value)
        take_profit = entry_price - (4 * atr_value)
        
        risk_amount = self.risk_per_trade * self.equity
        risk_per_share = stop_loss - entry_price
        position_size = int(round(risk_amount / risk_per_share)) if risk_per_share > 0 else 0
        
        if position_size > 0:
            print(f"🌙 MOON DEV SHORT SIGNAL! 📉")
            print(f"💰 Entry: ${entry_price:.2f} | SL: ${stop_loss:.2f} | TP: ${take_profit:.2f}")
            print(f"📊 Position Size: {position_size} shares")
            self.sell(size=position_size, sl=stop_loss, tp=take_profit)
    
    def check_exits(self, current_rsi, current_macd, current_macd_signal):
        if self.position.is_long:
            if current_rsi >= 70:
                print(f"🌙 MOON DEV TP HIT! RSI Overbought at {current_rsi:.1f} ✨")
                self.position.close()
            elif current_macd < current_macd_signal:
                print(f"🌙 MOON DEV EXIT! MACD Bearish Crossover 📉")
                self.position.close()
                
        elif self.position.is_short:
            if current_rsi <= 30:
                print(f"🌙 MOON DEV TP HIT! RSI Oversold at {current_rsi:.1f} ✨")
                self.position.close()
            elif current_macd > current_macd_signal:
                print(f"🌙 MOON DEV EXIT! MACD Bullish Crossover 🚀")
                self.position.close()

data = load_data()
bt = Backtest(data, DivergentMomentum, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)