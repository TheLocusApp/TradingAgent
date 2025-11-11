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
        
        # 🌙 TREND FILTERS - NEW OPTIMIZATION
        self.ema_fast_line = self.I(talib.EMA, close, timeperiod=self.ema_fast)
        self.ema_slow_line = self.I(talib.EMA, close, timeperiod=self.ema_slow)
        self.volume_ma_line = self.I(talib.SMA, volume, timeperiod=self.volume_ma)
        
        # 🌙 MOMENTUM CONFIRMATION - NEW OPTIMIZATION
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, close, fastperiod=12, slowperiod=26, signalperiod=9)
        
        # 🌙 DIVERGENCE DETECTION
        self.price_lows = self.I(talib.MIN, low, timeperiod=5)
        self.price_highs = self.I(talib.MAX, high, timeperiod=5)
        self.rsi_lows = self.I(talib.MIN, self.rsi, timeperiod=5)
        self.rsi_highs = self.I(talib.MAX, self.rsi, timeperiod=5)
        
        self.last_long_signal = 0
        self.last_short_signal = 0
        self.trade_count = 0
        
    def next(self):
        if len(self.data) < 50:  # Increased minimum bars for better indicator reliability
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
        
        # 🌙 TREND ANALYSIS - NEW OPTIMIZATION
        ema_fast = self.ema_fast_line[-1]
        ema_slow = self.ema_slow_line[-1]
        volume_ma = self.volume_ma_line[-1]
        macd = self.macd[-1] if self.macd[-1] is not None else 0
        macd_signal = self.macd_signal[-1] if self.macd_signal[-1] is not None else 0
        
        # 🌙 VOLUME CONFIRMATION - NEW OPTIMIZATION
        volume_above_avg = current_volume > volume_ma * 1.2
        
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
        
        # 🌙 TIGHTER DIVERGENCE CONDITIONS - OPTIMIZATION
        if (price_low_3 > price_low_2 and rsi_low_3 < rsi_low_2 and 
            current_close > bb_lower and current_rsi > 35 and  # Increased RSI threshold
            current_close > ema_slow and  # Must be above slow EMA for longs
            macd > macd_signal):  # MACD bullish confirmation
            bullish_divergence = True
            print(f"🌙 BULLISH DIVERGENCE DETECTED! Price: {current_close:.2f}, RSI: {current_rsi:.1f}")
            
        if (price_high_3 < price_high_2 and rsi_high_3 > rsi_high_2 and 
            current_close < bb_upper and current_rsi < 65 and  # Decreased RSI threshold
            current_close < ema_slow and  # Must be below slow EMA for shorts
            macd < macd_signal):  # MACD bearish confirmation
            bearish_divergence = True
            print(f"🌙 BEARISH DIVERGENCE DETECTED! Price: {current_close:.2f}, RSI: {current_rsi:.1f}")
        
        if not self.position:
            # 🌙 DYNAMIC POSITION SIZING - OPTIMIZATION
            volatility_factor = max(0.5, min(2.0, atr / current_close * 100))  # ATR-based sizing
            adjusted_risk = self.risk_per_trade / volatility_factor
            risk_amount = self.equity * adjusted_risk
            
            # 🌙 COOLDOWN PERIOD - OPTIMIZATION
            min_bars_between_trades = 3
            
            if bullish_divergence and self.last_long_signal < len(self.data) - min_bars_between_trades and volume_above_avg:
                stop_price = current_low - (atr * 1.2)  # Tighter stop loss
                position_size = int(round(risk_amount / (current_close - stop_price)))
                
                if position_size > 0:
                    self.buy(size=position_size, sl=stop_price)
                    self.last_long_signal = len(self.data)
                    self.trade_count += 1
                    print(f"🚀 LONG ENTRY! Size: {position_size}, Stop: {stop_price:.2f}, ATR Factor: {volatility_factor:.2f}")
                    
            elif bearish_divergence and self.last_short_signal < len(self.data) - min_bars_between_trades and volume_above_avg:
                stop_price = current_high + (atr * 1.2)  # Tighter stop loss
                position_size = int(round(risk_amount / (stop_price - current_close)))
                
                if position_size > 0:
                    self.sell(size=position_size, sl=stop_price)
                    self.last_short_signal = len(self.data)
                    self.trade_count += 1
                    print(f"📉 SHORT ENTRY! Size: {position_size}, Stop: {stop_price:.2f}, ATR Factor: {volatility_factor:.2f}")
                    
        else:
            # 🌙 IMPROVED EXIT STRATEGY - OPTIMIZATION
            if self.position.is_long:
                # Scale out partial profits
                if current_close >= self.position.entry_price * 1.15:  # Take partial profit at 15%
                    self.position.close(0.5)  # Close half position
                    print(f"✨ PARTIAL LONG PROFIT TAKEN! +15%")
                
                # Trailing stop and improved exit conditions
                trail_stop = current_close - (atr * 1.5)
                if trail_stop > self.position.sl:
                    self.position.sl = trail_stop
                    
                if (current_close >= bb_upper and current_rsi >= 75) or bearish_divergence or current_close < ema_fast:
                    self.position.close()
                    print(f"✨ FULL LONG EXIT! Price: {current_close:.2f}")
                    
            elif self.position.is_short:
                # Scale out partial profits
                if current_close <= self.position.entry_price * 0.85:  # Take partial profit at 15%
                    self.position.close(0.5)  # Close half position
                    print(f"✨ PARTIAL SHORT PROFIT TAKEN! +15%")
                
                # Trailing stop and improved exit conditions
                trail_stop = current_close + (atr * 1.5)
                if trail_stop < self.position.sl:
                    self.position.sl = trail_stop
                    
                if (current_close <= bb_lower and current_rsi <= 25) or bullish_divergence or current_close > ema_fast:
                    self.position.close()
                    print(f"✨ FULL SHORT EXIT! Price: {current_close:.2f}")

data = load_data()
bt = Backtest(data, VolatilityDivergence, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)