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
    ema_fast = 20
    ema_slow = 50
    
    def init(self):
        close = self.data.Close.astype(float)
        high = self.data.High.astype(float)
        low = self.data.Low.astype(float)
        volume = self.data.Volume.astype(float)
        
        # 🌙 CORE INDICATORS - Enhanced with trend filters
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std
        )
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        
        # 🌙 TREND FILTERS - Added to avoid choppy markets
        self.ema_fast_line = self.I(talib.EMA, close, timeperiod=self.ema_fast)
        self.ema_slow_line = self.I(talib.EMA, close, timeperiod=self.ema_slow)
        
        # 🌙 VOLUME CONFIRMATION - Added volume filter for stronger signals
        self.volume_sma = self.I(talib.SMA, volume, timeperiod=20)
        
        # 🌙 MOMENTUM CONFIRMATION - Added MACD for additional momentum filter
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, close)
        
        # 🌙 DIVERGENCE DETECTION - Enhanced with stronger confirmation
        self.price_lows = self.I(talib.MIN, low, timeperiod=7)  # Increased to 7 for stronger signals
        self.price_highs = self.I(talib.MAX, high, timeperiod=7)
        self.rsi_lows = self.I(talib.MIN, self.rsi, timeperiod=7)
        self.rsi_highs = self.I(talib.MAX, self.rsi, timeperiod=7)
        
        self.last_long_signal = 0
        self.last_short_signal = 0
        self.trade_count = 0
        
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
        volume_sma = self.volume_sma[-1]
        macd = self.macd[-1] if self.macd[-1] is not None else 0
        macd_signal = self.macd_signal[-1] if self.macd_signal[-1] is not None else 0
        
        # 🌙 TREND DIRECTION - Only trade with the trend
        uptrend = ema_fast > ema_slow
        downtrend = ema_fast < ema_slow
        
        # 🌙 VOLUME CONFIRMATION - Require above average volume for entries
        volume_strong = current_volume > volume_sma * 1.1
        
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
        
        # 🌙 ENHANCED DIVERGENCE DETECTION - Stronger confirmation with multiple points
        if ((price_low_4 > price_low_3 > price_low_2 and rsi_low_4 < rsi_low_3 < rsi_low_2) or
            (price_low_3 > price_low_2 and rsi_low_3 < rsi_low_2)) and \
           current_close > bb_lower and current_rsi > 30 and current_rsi < 60:  # Added RSI range filter
            bullish_divergence = True
            print(f"🌙 BULLISH DIVERGENCE DETECTED! Price: {current_close:.2f}, RSI: {current_rsi:.1f}")
            
        if ((price_high_4 < price_high_3 < price_high_2 and rsi_high_4 > rsi_high_3 > rsi_high_2) or
            (price_high_3 < price_high_2 and rsi_high_3 > rsi_high_2)) and \
           current_close < bb_upper and current_rsi < 70 and current_rsi > 40:  # Added RSI range filter
            bearish_divergence = True
            print(f"🌙 BEARISH DIVERGENCE DETECTED! Price: {current_close:.2f}, RSI: {current_rsi:.1f}")
        
        if not self.position:
            # 🌙 DYNAMIC RISK MANAGEMENT - Scale risk based on performance
            base_risk = self.risk_per_trade
            if self.trade_count > 10 and self.equity > 1000000:
                base_risk = min(0.03, base_risk * 1.2)  # Increase risk slightly after proving strategy
            risk_amount = self.equity * base_risk
            
            # 🌙 ENTRY CONDITIONS - Much stricter with multiple confirmations
            long_conditions = (
                bullish_divergence and 
                self.last_long_signal < len(self.data) - 3 and  # Increased cooldown
                uptrend and  # Must be in uptrend for longs
                volume_strong and  # Require volume confirmation
                macd > macd_signal and  # MACD momentum confirmation
                current_close > bb_middle  # Price above middle BB for stronger trend
            )
            
            short_conditions = (
                bearish_divergence and 
                self.last_short_signal < len(self.data) - 3 and  # Increased cooldown
                downtrend and  # Must be in downtrend for shorts
                volume_strong and  # Require volume confirmation
                macd < macd_signal and  # MACD momentum confirmation
                current_close < bb_middle  # Price below middle BB for stronger trend
            )
            
            if long_conditions:
                # 🌙 IMPROVED STOP LOSS - Tighter but smarter placement
                stop_price = min(current_low - (atr * 1.2), bb_lower - (atr * 0.5))
                position_size = int(round(risk_amount / (current_close - stop_price)))
                
                if position_size > 0:
                    self.buy(size=position_size, sl=stop_price)
                    self.last_long_signal = len(self.data)
                    self.trade_count += 1
                    print(f"🚀 ENHANCED LONG ENTRY! Size: {position_size}, Stop: {stop_price:.2f}")
                    
            elif short_conditions:
                # 🌙 IMPROVED STOP LOSS - Tighter but smarter placement
                stop_price = max(current_high + (atr * 1.2), bb_upper + (atr * 0.5))
                position_size = int(round(risk_amount / (stop_price - current_close)))
                
                if position_size > 0:
                    self.sell(size=position_size, sl=stop_price)
                    self.last_short_signal = len(self.data)
                    self.trade_count += 1
                    print(f"📉 ENHANCED SHORT ENTRY! Size: {position_size}, Stop: {stop_price:.2f}")
                    
        else:
            # 🌙 IMPROVED EXIT STRATEGY - Trailing stops and multiple exit conditions
            if self.position.is_long:
                # 🌙 TRAILING STOP - Dynamic trailing based on ATR
                current_sl = self.position.sl or 0
                new_sl = current_close - (atr * 1.5)
                
                # Exit conditions - multiple ways to take profits
                exit_conditions = (
                    current_close >= bb_upper or 
                    current_rsi >= 75 or  # More aggressive overbought level
                    bearish_divergence or
                    (current_close > self.position.entry_price * 1.02 and current_rsi > 70) or  # Quick profit taking
                    not uptrend  # Trend reversal
                )
                
                if exit_conditions:
                    self.position.close()
                    print(f"✨ ENHANCED LONG EXIT! Multiple exit conditions triggered")
                elif new_sl > current_sl:
                    self.position.sl = new_sl
                    
            elif self.position.is_short:
                # 🌙 TRAILING STOP - Dynamic trailing based on ATR
                current_sl = self.position.sl or float('inf')
                new_sl = current_close + (atr * 1.5)
                
                # Exit conditions - multiple ways to take profits
                exit_conditions = (
                    current_close <= bb_lower or 
                    current_rsi <= 25 or  # More aggressive oversold level
                    bullish_divergence or
                    (current_close < self.position.entry_price * 0.98 and current_rsi < 30) or  # Quick profit taking
                    not downtrend  # Trend reversal
                )
                
                if exit_conditions:
                    self.position.close()
                    print(f"✨ ENHANCED SHORT EXIT! Multiple exit conditions triggered")
                elif new_sl < current_sl:
                    self.position.sl = new_sl

data = load_data()
bt = Backtest(data, VolatilityDivergence, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)