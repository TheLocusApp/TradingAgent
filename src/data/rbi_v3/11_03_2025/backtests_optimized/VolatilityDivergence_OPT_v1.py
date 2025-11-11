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
    risk_per_trade = 0.03  # 🌙 INCREASED RISK FOR HIGHER RETURNS
    ema_fast = 20
    ema_slow = 50
    volume_ma = 20
    
    def init(self):
        close = self.data.Close.astype(float)
        high = self.data.High.astype(float)
        low = self.data.Low.astype(float)
        volume = self.data.Volume.astype(float)
        
        # 🌙 CORE INDICATORS
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std
        )
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        
        # 🌙 ADDED TREND FILTERS FOR BETTER DIRECTIONAL BIAS
        self.ema_fast_line = self.I(talib.EMA, close, timeperiod=self.ema_fast)
        self.ema_slow_line = self.I(talib.EMA, close, timeperiod=self.ema_slow)
        
        # 🌙 ADDED VOLUME CONFIRMATION
        self.volume_ma_line = self.I(talib.SMA, volume, timeperiod=self.volume_ma)
        
        # 🌙 IMPROVED DIVERGENCE DETECTION WITH MORE ROBUST PERIODS
        self.price_lows = self.I(talib.MIN, low, timeperiod=7)  # Extended to 7 periods
        self.price_highs = self.I(talib.MAX, high, timeperiod=7)
        self.rsi_lows = self.I(talib.MIN, self.rsi, timeperiod=7)
        self.rsi_highs = self.I(talib.MAX, self.rsi, timeperiod=7)
        
        # 🌙 ADDED MOMENTUM CONFIRMATION
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, close)
        
        self.last_long_signal = 0
        self.last_short_signal = 0
        self.signal_cooldown = 3  # 🌙 PREVENT OVER-TRADING
        
    def next(self):
        if len(self.data) < 50:  # Increased minimum bars for better indicator stability
            return
            
        current_close = self.data.Close[-1]
        current_rsi = self.rsi[-1]
        current_low = self.data.Low[-1]
        current_high = self.data.High[-1]
        current_volume = self.data.Volume[-1]
        
        bb_upper = self.bb_upper[-1]
        bb_lower = self.bb_lower[-1]
        bb_middle = self.bb_middle[-1]
        atr = self.atr[-1]
        ema_fast = self.ema_fast_line[-1]
        ema_slow = self.ema_slow_line[-1]
        volume_ma = self.volume_ma_line[-1]
        macd = self.macd[-1]
        macd_signal = self.macd_signal[-1]
        
        # 🌙 IMPROVED DIVERGENCE DETECTION WITH STRONGER CONDITIONS
        price_low_2 = self.price_lows[-2] if len(self.price_lows) > 2 else current_low
        price_low_3 = self.price_lows[-3] if len(self.price_lows) > 3 else current_low
        price_low_4 = self.price_lows[-4] if len(self.price_lows) > 4 else current_low
        rsi_low_2 = self.rsi_lows[-2] if len(self.rsi_lows) > 2 else current_rsi
        rsi_low_3 = self.rsi_lows[-3] if len(self.rsi_lows) > 3 else current_rsi
        rsi_low_4 = self.rsi_lows[-4] if len(self.rsi_lows) > 4 else current_rsi
        
        price_high_2 = self.price_highs[-2] if len(self.price_highs) > 2 else current_high
        price_high_3 = self.price_highs[-3] if len(self.price_highs) > 3 else current_high
        price_high_4 = self.price_highs[-4] if len(self.price_highs) > 4 else current_high
        rsi_high_2 = self.rsi_highs[-2] if len(self.rsi_highs) > 2 else current_rsi
        rsi_high_3 = self.rsi_highs[-3] if len(self.rsi_highs) > 3 else current_rsi
        rsi_high_4 = self.rsi_highs[-4] if len(self.rsi_highs) > 4 else current_rsi
        
        bullish_divergence = False
        bearish_divergence = False
        
        # 🌙 STRONGER BULLISH DIVERGENCE: PRICE MAKES LOWER LOWS BUT RSI MAKES HIGHER LOWS
        if ((price_low_4 > price_low_3 > price_low_2 and rsi_low_4 < rsi_low_3 < rsi_low_2) or
            (price_low_3 > price_low_2 and rsi_low_3 < rsi_low_2)):
            # 🌙 ADDED TREND AND VOLUME FILTERS
            if (current_close > bb_lower and current_rsi > 35 and  # Tighter RSI filter
                ema_fast > ema_slow and  # Uptrend filter
                current_volume > volume_ma * 0.8 and  # Volume confirmation
                macd > macd_signal):  # Momentum confirmation
                bullish_divergence = True
                print(f"🌙 BULLISH DIVERGENCE DETECTED! Price: {current_close:.2f}, RSI: {current_rsi:.1f}")
            
        # 🌙 STRONGER BEARISH DIVERGENCE: PRICE MAKES HIGHER HIGHS BUT RSI MAKES LOWER HIGHS
        if ((price_high_4 < price_high_3 < price_high_2 and rsi_high_4 > rsi_high_3 > rsi_high_2) or
            (price_high_3 < price_high_2 and rsi_high_3 > rsi_high_2)):
            # 🌙 ADDED TREND AND VOLUME FILTERS
            if (current_close < bb_upper and current_rsi < 65 and  # Tighter RSI filter
                ema_fast < ema_slow and  # Downtrend filter
                current_volume > volume_ma * 0.8 and  # Volume confirmation
                macd < macd_signal):  # Momentum confirmation
                bearish_divergence = True
                print(f"🌙 BEARISH DIVERGENCE DETECTED! Price: {current_close:.2f}, RSI: {current_rsi:.1f}")
        
        if not self.position:
            risk_amount = self.equity * self.risk_per_trade
            
            if bullish_divergence and self.last_long_signal < len(self.data) - self.signal_cooldown:
                # 🌙 IMPROVED STOP LOSS: 1.2x ATR INSTEAD OF 1.5x FOR BETTER RISK-REWARD
                stop_price = current_low - (atr * 1.2)
                # 🌙 DYNAMIC POSITION SIZING BASED ON VOLATILITY
                position_size = int(round(risk_amount / (current_close - stop_price)))
                
                if position_size > 0 and current_close > bb_middle:  # Only trade above BB middle for longs
                    self.buy(size=position_size, sl=stop_price)
                    self.last_long_signal = len(self.data)
                    print(f"🚀 LONG ENTRY! Size: {position_size}, Stop: {stop_price:.2f}")
                    
            elif bearish_divergence and self.last_short_signal < len(self.data) - self.signal_cooldown:
                # 🌙 IMPROVED STOP LOSS: 1.2x ATR INSTEAD OF 1.5x FOR BETTER RISK-REWARD
                stop_price = current_high + (atr * 1.2)
                # 🌙 DYNAMIC POSITION SIZING BASED ON VOLATILITY
                position_size = int(round(risk_amount / (stop_price - current_close)))
                
                if position_size > 0 and current_close < bb_middle:  # Only trade below BB middle for shorts
                    self.sell(size=position_size, sl=stop_price)
                    self.last_short_signal = len(self.data)
                    print(f"📉 SHORT ENTRY! Size: {position_size}, Stop: {stop_price:.2f}")
                    
        else:
            # 🌙 IMPROVED EXIT STRATEGY WITH TRAILING STOPS AND MULTIPLE EXIT CONDITIONS
            if self.position.is_long:
                # 🌙 TRAILING STOP: MOVE STOP TO BREAK-EVEN + 0.5x ATR WHEN PROFITABLE
                if current_close > self.position.entry_price + (atr * 1):
                    new_stop = self.position.entry_price + (atr * 0.5)
                    if new_stop > self.position.sl:
                        self.position.sl = new_stop
                        print(f"🌙 TRAILING STOP UPDATED: {new_stop:.2f}")
                
                # 🌙 MULTIPLE EXIT CONDITIONS
                exit_signal = (
                    current_close >= bb_upper or 
                    current_rsi >= 75 or  # More aggressive overbought
                    bearish_divergence or
                    ema_fast < ema_slow  # Trend reversal
                )
                
                if exit_signal:
                    self.position.close()
                    print(f"✨ LONG EXIT! Multiple exit conditions triggered")
                    
            elif self.position.is_short:
                # 🌙 TRAILING STOP: MOVE STOP TO BREAK-EVEN - 0.5x ATR WHEN PROFITABLE
                if current_close < self.position.entry_price - (atr * 1):
                    new_stop = self.position.entry_price - (atr * 0.5)
                    if new_stop < self.position.sl:
                        self.position.sl = new_stop
                        print(f"🌙 TRAILING STOP UPDATED: {new_stop:.2f}")
                
                # 🌙 MULTIPLE EXIT CONDITIONS
                exit_signal = (
                    current_close <= bb_lower or 
                    current_rsi <= 25 or  # More aggressive oversold
                    bullish_divergence or
                    ema_fast > ema_slow  # Trend reversal
                )
                
                if exit_signal:
                    self.position.close()
                    print(f"✨ SHORT EXIT! Multiple exit conditions triggered")

data = load_data()
bt = Backtest(data, VolatilityDivergence, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)