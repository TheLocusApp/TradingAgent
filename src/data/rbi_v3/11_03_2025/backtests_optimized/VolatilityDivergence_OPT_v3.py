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
        
        # 🌙 IMPROVED: Added EMA trend filter for better market regime detection
        self.ema_fast = self.I(talib.EMA, close, timeperiod=20)
        self.ema_slow = self.I(talib.EMA, close, timeperiod=50)
        
        # 🌙 IMPROVED: Added volume confirmation for stronger signals
        self.volume_sma = self.I(talib.SMA, volume, timeperiod=20)
        
        # 🌙 IMPROVED: Enhanced divergence detection with longer lookback
        self.price_lows = self.I(talib.MIN, low, timeperiod=7)
        self.price_highs = self.I(talib.MAX, high, timeperiod=7)
        self.rsi_lows = self.I(talib.MIN, self.rsi, timeperiod=7)
        self.rsi_highs = self.I(talib.MAX, self.rsi, timeperiod=7)
        
        self.last_long_signal = 0
        self.last_short_signal = 0
        
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
        bb_middle = self.bb_middle[-1]
        atr = self.atr[-1]
        ema_fast = self.ema_fast[-1]
        ema_slow = self.ema_slow[-1]
        volume_sma = self.volume_sma[-1]
        
        # 🌙 IMPROVED: Enhanced divergence detection with more robust conditions
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
        
        # 🌙 IMPROVED: Stronger bullish divergence with trend filter and volume confirmation
        if ((price_low_3 > price_low_2 and rsi_low_3 < rsi_low_2) or 
            (price_low_4 > price_low_3 and rsi_low_4 < rsi_low_3)) and \
           current_close > bb_lower and current_rsi > 30 and \
           ema_fast > ema_slow and current_volume > volume_sma * 0.8:  # 🌙 Added trend and volume filters
            bullish_divergence = True
            print(f"🌙 BULLISH DIVERGENCE DETECTED! Price: {current_close:.2f}, RSI: {current_rsi:.1f}, Volume: {current_volume:.0f}")
            
        # 🌙 IMPROVED: Stronger bearish divergence with trend filter and volume confirmation
        if ((price_high_3 < price_high_2 and rsi_high_3 > rsi_high_2) or 
            (price_high_4 < price_high_3 and rsi_high_4 > rsi_high_3)) and \
           current_close < bb_upper and current_rsi < 70 and \
           ema_fast < ema_slow and current_volume > volume_sma * 0.8:  # 🌙 Added trend and volume filters
            bearish_divergence = True
            print(f"🌙 BEARISH DIVERGENCE DETECTED! Price: {current_close:.2f}, RSI: {current_rsi:.1f}, Volume: {current_volume:.0f}")
        
        if not self.position:
            risk_amount = self.equity * self.risk_per_trade
            
            # 🌙 IMPROVED: Dynamic position sizing based on ATR volatility
            atr_position_size = max(0.01, min(0.05, 0.03 * (50 / atr)))  # 🌙 Scale risk based on volatility
            dynamic_risk_amount = self.equity * atr_position_size
            
            if bullish_divergence and self.last_long_signal < len(self.data) - 3:  # 🌙 Reduced signal frequency
                stop_price = current_low - (atr * 1.2)  # 🌙 Tighter stop loss
                position_size = int(round(dynamic_risk_amount / (current_close - stop_price)))
                
                if position_size > 0 and current_close > bb_middle:  # 🌙 Added BB middle filter
                    self.buy(size=position_size, sl=stop_price)
                    self.last_long_signal = len(self.data)
                    print(f"🚀 LONG ENTRY! Size: {position_size}, Stop: {stop_price:.2f}, ATR Risk: {atr_position_size:.3f}")
                    
            elif bearish_divergence and self.last_short_signal < len(self.data) - 3:  # 🌙 Reduced signal frequency
                stop_price = current_high + (atr * 1.2)  # 🌙 Tighter stop loss
                position_size = int(round(dynamic_risk_amount / (stop_price - current_close)))
                
                if position_size > 0 and current_close < bb_middle:  # 🌙 Added BB middle filter
                    self.sell(size=position_size, sl=stop_price)
                    self.last_short_signal = len(self.data)
                    print(f"📉 SHORT ENTRY! Size: {position_size}, Stop: {stop_price:.2f}, ATR Risk: {atr_position_size:.3f}")
                    
        else:
            # 🌙 IMPROVED: Enhanced exit logic with trailing stops and profit targets
            if self.position.is_long:
                # 🌙 Trailing stop logic
                if current_close > self.position.entry_price + (atr * 2):
                    new_sl = current_close - (atr * 1.5)
                    if new_sl > self.position.sl:
                        self.position.sl = new_sl
                        print(f"🌙 LONG TRAILING STOP UPDATED: {new_sl:.2f}")
                
                # 🌙 Improved exit conditions
                exit_condition = (current_close >= bb_upper and current_rsi >= 65) or \
                                current_rsi >= 75 or \
                                bearish_divergence or \
                                current_close < ema_fast  # 🌙 Added trend break exit
                
                if exit_condition:
                    self.position.close()
                    print(f"✨ LONG EXIT! Price: {current_close:.2f}, RSI: {current_rsi:.1f}")
                    
            elif self.position.is_short:
                # 🌙 Trailing stop logic
                if current_close < self.position.entry_price - (atr * 2):
                    new_sl = current_close + (atr * 1.5)
                    if new_sl < self.position.sl:
                        self.position.sl = new_sl
                        print(f"🌙 SHORT TRAILING STOP UPDATED: {new_sl:.2f}")
                
                # 🌙 Improved exit conditions
                exit_condition = (current_close <= bb_lower and current_rsi <= 35) or \
                                current_rsi <= 25 or \
                                bullish_divergence or \
                                current_close > ema_fast  # 🌙 Added trend break exit
                
                if exit_condition:
                    self.position.close()
                    print(f"✨ SHORT EXIT! Price: {current_close:.2f}, RSI: {current_rsi:.1f}")

data = load_data()
bt = Backtest(data, VolatilityDivergence, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)