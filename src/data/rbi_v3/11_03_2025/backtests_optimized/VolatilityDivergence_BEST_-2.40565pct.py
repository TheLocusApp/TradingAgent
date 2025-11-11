import pandas as pd
import numpy as np
import yfinance as yf
from backtesting import Backtest, Strategy
import talib

def load_data():
    ticker = yf.Ticker("SPY")
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

class VolatilityDivergence(Strategy):
    bb_period = 20
    bb_std = 2
    rsi_period = 14
    atr_period = 14
    risk_per_trade = 0.02
    
    def init(self):
        close = self.data.Close.astype(float)
        high = self.data.High.astype(float)
        low = self.data.Low.astype(float)
        volume = self.data.Volume.astype(float)
        
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std
        )
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        
        self.price_lows = self.I(talib.MIN, low, timeperiod=5)
        self.price_highs = self.I(talib.MAX, high, timeperiod=5)
        self.rsi_lows = self.I(talib.MIN, self.rsi, timeperiod=5)
        self.rsi_highs = self.I(talib.MAX, self.rsi, timeperiod=5)
        
        self.last_long_signal = 0
        self.last_short_signal = 0
        
    def next(self):
        if len(self.data) < 30:
            return
            
        current_close = self.data.Close[-1]
        current_rsi = self.rsi[-1]
        current_low = self.data.Low[-1]
        current_high = self.data.High[-1]
        
        bb_upper = self.bb_upper[-1]
        bb_lower = self.bb_lower[-1]
        atr = self.atr[-1]
        
        price_low_2 = self.price_lows[-2] if len(self.price_lows) > 2 else current_low
        price_low_3 = self.price_lows[-3] if len(self.price_lows) > 3 else current_low
        rsi_low_2 = self.rsi_lows[-2] if len(self.rsi_lows) > 2 else current_rsi
        rsi_low_3 = self.rsi_lows[-3] if len(self.rsi_lows) > 3 else current_rsi
        
        price_high_2 = self.price_highs[-2] if len(self.price_highs) > 2 else current_high
        price_high_3 = self.price_highs[-3] if len(self.price_highs) > 3 else current_high
        rsi_high_2 = self.rsi_highs[-2] if len(self.rsi_highs) > 2 else current_rsi
        rsi_high_3 = self.rsi_highs[-3] if len(self.rsi_highs) > 3 else current_rsi
        
        bullish_divergence = False
        bearish_divergence = False
        
        if (price_low_3 > price_low_2 and rsi_low_3 < rsi_low_2 and 
            current_close > bb_lower and current_rsi > 30):
            bullish_divergence = True
            print(f"🌙 BULLISH DIVERGENCE DETECTED! Price: {current_close:.2f}, RSI: {current_rsi:.1f}")
            
        if (price_high_3 < price_high_2 and rsi_high_3 > rsi_high_2 and 
            current_close < bb_upper and current_rsi < 70):
            bearish_divergence = True
            print(f"🌙 BEARISH DIVERGENCE DETECTED! Price: {current_close:.2f}, RSI: {current_rsi:.1f}")
        
        if not self.position:
            risk_amount = self.equity * self.risk_per_trade
            
            if bullish_divergence and self.last_long_signal < len(self.data) - 2:
                stop_price = current_low - (atr * 1.5)
                position_size = int(round(risk_amount / (current_close - stop_price)))
                
                if position_size > 0:
                    self.buy(size=position_size, sl=stop_price)
                    self.last_long_signal = len(self.data)
                    print(f"🚀 LONG ENTRY! Size: {position_size}, Stop: {stop_price:.2f}")
                    
            elif bearish_divergence and self.last_short_signal < len(self.data) - 2:
                stop_price = current_high + (atr * 1.5)
                position_size = int(round(risk_amount / (stop_price - current_close)))
                
                if position_size > 0:
                    self.sell(size=position_size, sl=stop_price)
                    self.last_short_signal = len(self.data)
                    print(f"📉 SHORT ENTRY! Size: {position_size}, Stop: {stop_price:.2f}")
                    
        else:
            if self.position.is_long:
                if current_close >= bb_upper or current_rsi >= 70 or bearish_divergence:
                    self.position.close()
                    print(f"✨ LONG EXIT! Price touched BB upper or RSI overbought")
                    
            elif self.position.is_short:
                if current_close <= bb_lower or current_rsi <= 30 or bullish_divergence:
                    self.position.close()
                    print(f"✨ SHORT EXIT! Price touched BB lower or RSI oversold")

data = load_data()
bt = Backtest(data, VolatilityDivergence, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)