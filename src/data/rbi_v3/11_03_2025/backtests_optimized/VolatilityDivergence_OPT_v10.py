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
        
        # 🌙 TREND FILTERS - Added EMA trend confirmation
        self.ema_fast_line = self.I(talib.EMA, close, timeperiod=self.ema_fast)
        self.ema_slow_line = self.I(talib.EMA, close, timeperiod=self.ema_slow)
        
        # 🌙 VOLUME CONFIRMATION - Added volume filter
        self.volume_ma_line = self.I(talib.SMA, volume, timeperiod=self.volume_ma)
        
        # 🌙 DIVERGENCE DETECTION
        self.price_lows = self.I(talib.MIN, low, timeperiod=5)
        self.price_highs = self.I(talib.MAX, high, timeperiod=5)
        self.rsi_lows = self.I(talib.MIN, self.rsi, timeperiod=5)
        self.rsi_highs = self.I(talib.MAX, self.rsi, timeperiod=5)
        
        # 🌙 MOMENTUM CONFIRMATION - Added MACD for extra momentum filter
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, close)
        
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
        volume_ma = self.volume_ma_line[-1]
        macd = self.macd[-1] if self.macd[-1] is not None else 0
        macd_signal = self.macd_signal[-1] if self.macd_signal[-1] is not None else 0
        
        # 🌙 TREND DIRECTION FILTER
        uptrend = ema_fast > ema_slow
        downtrend = ema_fast < ema_slow
        
        # 🌙 VOLUME CONFIRMATION FILTER
        volume_strong = current_volume > volume_ma * 1.1
        
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
        
        # 🌙 IMPROVED DIVERGENCE DETECTION with stronger conditions
        if (price_low_3 > price_low_2 and rsi_low_3 < rsi_low_2 and 
            current_close > bb_lower and current_rsi > 30 and
            (rsi_low_2 - rsi_low_3) > 3):  # Minimum RSI divergence threshold
            bullish_divergence = True
            print(f"🌙 BULLISH DIVERGENCE DETECTED! Price: {current_close:.2f}, RSI: {current_rsi:.1f}")
            
        if (price_high_3 < price_high_2 and rsi_high_3 > rsi_high_2 and 
            current_close < bb_upper and current_rsi < 70 and
            (rsi_high_3 - rsi_high_2) > 3):  # Minimum RSI divergence threshold
            bearish_divergence = True
            print(f"🌙 BEARISH DIVERGENCE DETECTED! Price: {current_close:.2f}, RSI: {current_rsi:.1f}")
        
        if not self.position:
            # 🌙 DYNAMIC RISK MANAGEMENT based on recent performance
            base_risk = self.risk_per_trade
            if self.trade_count > 10 and self.equity > 1000000:
                base_risk = min(0.03, base_risk * 1.2)  # Scale up after proving strategy
                
            risk_amount = self.equity * base_risk
            
            # 🌙 ENTRY CONDITIONS WITH MULTIPLE FILTERS
            long_conditions = (
                bullish_divergence and 
                self.last_long_signal < len(self.data) - 3 and  # Increased cooldown
                uptrend and  # Must be in uptrend for long
                volume_strong and  # Volume confirmation
                macd > macd_signal  # MACD momentum confirmation
            )
            
            short_conditions = (
                bearish_divergence and 
                self.last_short_signal < len(self.data) - 3 and  # Increased cooldown
                downtrend and  # Must be in downtrend for short
                volume_strong and  # Volume confirmation
                macd < macd_signal  # MACD momentum confirmation
            )
            
            if long_conditions:
                # 🌙 IMPROVED STOP LOSS using ATR and recent low
                stop_price = min(current_low - (atr * 1.2), bb_lower - (atr * 0.5))
                position_size = int(round(risk_amount / (current_close - stop_price)))
                
                if position_size > 0:
                    self.buy(size=position_size, sl=stop_price)
                    self.last_long_signal = len(self.data)
                    self.trade_count += 1
                    print(f"🚀 LONG ENTRY! Size: {position_size}, Stop: {stop_price:.2f}, TP: {bb_upper:.2f}")
                    
            elif short_conditions:
                # 🌙 IMPROVED STOP LOSS using ATR and recent high
                stop_price = max(current_high + (atr * 1.2), bb_upper + (atr * 0.5))
                position_size = int(round(risk_amount / (stop_price - current_close)))
                
                if position_size > 0:
                    self.sell(size=position_size, sl=stop_price)
                    self.last_short_signal = len(self.data)
                    self.trade_count += 1
                    print(f"📉 SHORT ENTRY! Size: {position_size}, Stop: {stop_price:.2f}, TP: {bb_lower:.2f}")
                    
        else:
            # 🌙 IMPROVED EXIT STRATEGY with trailing stops and profit targets
            if self.position.is_long:
                # 🌙 TRAILING STOP based on ATR
                trailing_stop = self.data.Low[-1] - (atr * 1.0)
                current_sl = self.position.sl if self.position.sl else 0
                
                # Update trailing stop if better
                if trailing_stop > current_sl:
                    self.position.sl = trailing_stop
                
                exit_conditions = (
                    current_close >= bb_upper or 
                    current_rsi >= 75 or  # Tighter overbought threshold
                    bearish_divergence or
                    macd < macd_signal  # MACD turning down
                )
                
                if exit_conditions:
                    self.position.close()
                    print(f"✨ LONG EXIT! Price: {current_close:.2f}, RSI: {current_rsi:.1f}")
                    
            elif self.position.is_short:
                # 🌙 TRAILING STOP based on ATR
                trailing_stop = self.data.High[-1] + (atr * 1.0)
                current_sl = self.position.sl if self.position.sl else 0
                
                # Update trailing stop if better
                if trailing_stop < current_sl or current_sl == 0:
                    self.position.sl = trailing_stop
                
                exit_conditions = (
                    current_close <= bb_lower or 
                    current_rsi <= 25 or  # Tighter oversold threshold
                    bullish_divergence or
                    macd > macd_signal  # MACD turning up
                )
                
                if exit_conditions:
                    self.position.close()
                    print(f"✨ SHORT EXIT! Price: {current_close:.2f}, RSI: {current_rsi:.1f}")

data = load_data()
bt = Backtest(data, VolatilityDivergence, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)