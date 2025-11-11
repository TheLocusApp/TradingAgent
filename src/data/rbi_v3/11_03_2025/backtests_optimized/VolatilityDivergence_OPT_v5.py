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
        
        # 🌙 CORE INDICATORS
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std
        )
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        
        # 🌙 IMPROVED DIVERGENCE DETECTION - Longer lookback for stronger signals
        self.price_lows = self.I(talib.MIN, low, timeperiod=7)
        self.price_highs = self.I(talib.MAX, high, timeperiod=7)
        self.rsi_lows = self.I(talib.MIN, self.rsi, timeperiod=7)
        self.rsi_highs = self.I(talib.MAX, self.rsi, timeperiod=7)
        
        # 🌙 ADDITIONAL FILTERS FOR BETTER SIGNAL QUALITY
        self.ema_fast = self.I(talib.EMA, close, timeperiod=20)
        self.ema_slow = self.I(talib.EMA, close, timeperiod=50)
        self.volume_sma = self.I(talib.SMA, volume, timeperiod=20)
        
        self.last_long_signal = 0
        self.last_short_signal = 0
        self.signal_cooldown = 3  # 🌙 Reduced cooldown for more opportunities
        
    def next(self):
        if len(self.data) < 50:  # 🌙 Increased minimum bars for better indicator reliability
            return
            
        current_close = self.data.Close[-1]
        current_rsi = self.rsi[-1]
        current_low = self.data.Low[-1]
        current_high = self.data.High[-1]
        current_volume = self.data.Volume[-1]
        
        bb_upper = self.bb_upper[-1]
        bb_lower = self.bb_lower[-1]
        atr = self.atr[-1]
        ema_fast = self.ema_fast[-1]
        ema_slow = self.ema_slow[-1]
        volume_sma = self.volume_sma[-1]
        
        # 🌙 IMPROVED DIVERGENCE DETECTION - More robust pattern recognition
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
        
        # 🌙 STRONGER BULLISH DIVERGENCE CONDITIONS
        # Multiple divergence patterns + trend filter + volume confirmation
        bullish_pattern1 = (price_low_3 > price_low_2 and rsi_low_3 < rsi_low_2)
        bullish_pattern2 = (price_low_4 > price_low_3 and rsi_low_4 < rsi_low_3)
        uptrend = ema_fast > ema_slow  # 🌙 Only trade bullish in uptrend
        volume_ok = current_volume > volume_sma * 0.8  # 🌙 Volume filter
        
        if ((bullish_pattern1 or bullish_pattern2) and 
            current_close > bb_lower and 
            current_rsi > 25 and current_rsi < 45 and  # 🌙 Tighter RSI range for better entries
            uptrend and volume_ok):
            bullish_divergence = True
            print(f"🌙 BULLISH DIVERGENCE DETECTED! Price: {current_close:.2f}, RSI: {current_rsi:.1f}")
            
        # 🌙 STRONGER BEARISH DIVERGENCE CONDITIONS  
        bearish_pattern1 = (price_high_3 < price_high_2 and rsi_high_3 > rsi_high_2)
        bearish_pattern2 = (price_high_4 < price_high_3 and rsi_high_4 > rsi_high_3)
        downtrend = ema_fast < ema_slow  # 🌙 Only trade bearish in downtrend
        
        if ((bearish_pattern1 or bearish_pattern2) and 
            current_close < bb_upper and 
            current_rsi > 55 and current_rsi < 75 and  # 🌙 Tighter RSI range for better entries
            downtrend and volume_ok):
            bearish_divergence = True
            print(f"🌙 BEARISH DIVERGENCE DETECTED! Price: {current_close:.2f}, RSI: {current_rsi:.1f}")
        
        if not self.position:
            # 🌙 DYNAMIC POSITION SIZING BASED ON VOLATILITY
            atr_ratio = atr / current_close
            if atr_ratio > 0.02:  # 🌙 Reduce size in high volatility
                adjusted_risk = self.risk_per_trade * 0.7
            else:
                adjusted_risk = self.risk_per_trade
                
            risk_amount = self.equity * adjusted_risk

            if bullish_divergence and self.last_long_signal < len(self.data) - self.signal_cooldown:
                # 🌙 IMPROVED STOP LOSS - Tighter but with ATR buffer
                stop_price = current_low - (atr * 1.2)
                position_size = int(round(risk_amount / (current_close - stop_price)))
                
                if position_size > 0:
                    self.buy(size=position_size, sl=stop_price)
                    self.last_long_signal = len(self.data)
                    print(f"🚀 LONG ENTRY! Size: {position_size}, Stop: {stop_price:.2f}")
                    
            elif bearish_divergence and self.last_short_signal < len(self.data) - self.signal_cooldown:
                # 🌙 IMPROVED STOP LOSS - Tighter but with ATR buffer
                stop_price = current_high + (atr * 1.2)
                position_size = int(round(risk_amount / (stop_price - current_close)))
                
                if position_size > 0:
                    self.sell(size=position_size, sl=stop_price)
                    self.last_short_signal = len(self.data)
                    print(f"📉 SHORT ENTRY! Size: {position_size}, Stop: {stop_price:.2f}")
                    
        else:
            # 🌙 IMPROVED EXIT STRATEGY - Trailing stops and partial profit taking
            if self.position.is_long:
                # 🌙 SCALED EXITS - Take partial profits at resistance levels
                if current_close >= bb_upper and self.position.size > 1:
                    partial_size = self.position.size // 2
                    self.position.close(partial_size)
                    print(f"✨ PARTIAL LONG EXIT! Price touched BB upper, closed {partial_size} shares")
                
                # 🌙 TRAILING STOP - Move stop to breakeven + small profit after move
                elif current_close > self.position.entry_price + (atr * 2):
                    new_stop = self.position.entry_price + (atr * 0.5)
                    if new_stop > self.position.sl:
                        self.position.sl = new_stop
                        print(f"🌙 TRAILING STOP UPDATED! New stop: {new_stop:.2f}")
                
                # 🌙 FULL EXIT CONDITIONS
                elif current_rsi >= 75 or bearish_divergence:
                    self.position.close()
                    print(f"✨ FULL LONG EXIT! RSI overbought or bearish divergence")
                    
            elif self.position.is_short:
                # 🌙 SCALED EXITS - Take partial profits at support levels
                if current_close <= bb_lower and self.position.size > 1:
                    partial_size = self.position.size // 2
                    self.position.close(partial_size)
                    print(f"✨ PARTIAL SHORT EXIT! Price touched BB lower, closed {partial_size} shares")
                
                # 🌙 TRAILING STOP - Move stop to breakeven + small profit after move
                elif current_close < self.position.entry_price - (atr * 2):
                    new_stop = self.position.entry_price - (atr * 0.5)
                    if new_stop < self.position.sl:
                        self.position.sl = new_stop
                        print(f"🌙 TRAILING STOP UPDATED! New stop: {new_stop:.2f}")
                
                # 🌙 FULL EXIT CONDITIONS
                elif current_rsi <= 25 or bullish_divergence:
                    self.position.close()
                    print(f"✨ FULL SHORT EXIT! RSI oversold or bullish divergence")

data = load_data()
bt = Backtest(data, VolatilityDivergence, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)