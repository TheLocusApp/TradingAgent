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
        
        # 🌙 CORE INDICATORS
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std
        )
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        
        # 🌙 TREND FILTERS - Added to avoid choppy markets
        self.ema_fast_line = self.I(talib.EMA, close, timeperiod=self.ema_fast)
        self.ema_slow_line = self.I(talib.EMA, close, timeperiod=self.ema_slow)
        
        # 🌙 MOMENTUM CONFIRMATION - Added for better signal quality
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, close, fastperiod=12, slowperiod=26, signalperiod=9)
        
        # 🌙 VOLUME CONFIRMATION - Added to filter low-volume signals
        self.volume_sma = self.I(talib.SMA, volume, timeperiod=20)
        
        # 🌙 DIVERGENCE DETECTION
        self.price_lows = self.I(talib.MIN, low, timeperiod=5)
        self.price_highs = self.I(talib.MAX, high, timeperiod=5)
        self.rsi_lows = self.I(talib.MIN, self.rsi, timeperiod=5)
        self.rsi_highs = self.I(talib.MAX, self.rsi, timeperiod=5)
        
        self.last_long_signal = 0
        self.last_short_signal = 0
        
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
        macd = self.macd[-1]
        macd_signal = self.macd_signal[-1]
        volume_sma = self.volume_sma[-1]
        
        # 🌙 TREND DIRECTION - Added trend filter
        uptrend = ema_fast > ema_slow
        downtrend = ema_fast < ema_slow
        
        # 🌙 MOMENTUM DIRECTION - Added momentum confirmation
        bullish_momentum = macd > macd_signal
        bearish_momentum = macd < macd_signal
        
        # 🌙 VOLUME FILTER - Added volume confirmation
        high_volume = current_volume > volume_sma * 1.1
        
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
        
        # 🌙 IMPROVED DIVERGENCE DETECTION - Added stronger confirmation
        if (price_low_3 > price_low_2 and rsi_low_3 < rsi_low_2 and 
            current_close > bb_lower and current_rsi > 30 and
            current_close > bb_middle):  # Added: Price above BB middle for stronger bullish signal
            bullish_divergence = True
            print(f"🌙 BULLISH DIVERGENCE DETECTED! Price: {current_close:.2f}, RSI: {current_rsi:.1f}")
            
        if (price_high_3 < price_high_2 and rsi_high_3 > rsi_high_2 and 
            current_close < bb_upper and current_rsi < 70 and
            current_close < bb_middle):  # Added: Price below BB middle for stronger bearish signal
            bearish_divergence = True
            print(f"🌙 BEARISH DIVERGENCE DETECTED! Price: {current_close:.2f}, RSI: {current_rsi:.1f}")
        
        if not self.position:
            risk_amount = self.equity * self.risk_per_trade
            
            # 🌙 OPTIMIZED LONG ENTRY - Added trend, momentum, and volume filters
            if (bullish_divergence and self.last_long_signal < len(self.data) - 2 and
                uptrend and bullish_momentum and high_volume):  # Added multiple filters
                
                stop_price = current_low - (atr * 1.2)  # Tighter stop loss
                position_size = int(round(risk_amount / (current_close - stop_price)))
                
                if position_size > 0:
                    self.buy(size=position_size, sl=stop_price)
                    self.last_long_signal = len(self.data)
                    print(f"🚀 OPTIMIZED LONG ENTRY! Size: {position_size}, Stop: {stop_price:.2f}")
                    
            # 🌙 OPTIMIZED SHORT ENTRY - Added trend, momentum, and volume filters
            elif (bearish_divergence and self.last_short_signal < len(self.data) - 2 and
                  downtrend and bearish_momentum and high_volume):  # Added multiple filters
                
                stop_price = current_high + (atr * 1.2)  # Tighter stop loss
                position_size = int(round(risk_amount / (stop_price - current_close)))
                
                if position_size > 0:
                    self.sell(size=position_size, sl=stop_price)
                    self.last_short_signal = len(self.data)
                    print(f"📉 OPTIMIZED SHORT ENTRY! Size: {position_size}, Stop: {stop_price:.2f}")
                    
        else:
            # 🌙 IMPROVED EXIT STRATEGY - Added trailing stops and profit targets
            if self.position.is_long:
                # Trailing stop based on ATR
                trailing_stop = self.data.Low[-1] - (atr * 1.0)
                if trailing_stop > self.position.sl or self.position.sl is None:
                    self.position.sl = trailing_stop
                
                # Multiple exit conditions
                exit_signal = (current_close >= bb_upper or 
                              current_rsi >= 75 or  # More conservative overbought level
                              bearish_divergence or
                              not bullish_momentum)  # Added momentum exit
                
                if exit_signal:
                    self.position.close()
                    print(f"✨ OPTIMIZED LONG EXIT! Multiple exit conditions triggered")
                    
            elif self.position.is_short:
                # Trailing stop based on ATR
                trailing_stop = self.data.High[-1] + (atr * 1.0)
                if trailing_stop < self.position.sl or self.position.sl is None:
                    self.position.sl = trailing_stop
                
                # Multiple exit conditions
                exit_signal = (current_close <= bb_lower or 
                              current_rsi <= 25 or  # More conservative oversold level
                              bullish_divergence or
                              not bearish_momentum)  # Added momentum exit
                
                if exit_signal:
                    self.position.close()
                    print(f"✨ OPTIMIZED SHORT EXIT! Multiple exit conditions triggered")

data = load_data()
bt = Backtest(data, VolatilityDivergence, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)