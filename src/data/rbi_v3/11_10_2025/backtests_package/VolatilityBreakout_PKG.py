import yfinance as yf
import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

def load_data():
    ticker = yf.Ticker("SPY")
    data = ticker.history(period="2y", interval="1h")
    data.columns = data.columns.str.strip()
    required = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in data.columns for col in required):
        raise ValueError(f"Missing required columns. Got: {list(data.columns)}")
    return data

class VolatilityBreakout(Strategy):
    bb_period = 20
    bb_std = 2
    sma_period = 50
    squeeze_threshold = 0.02
    volume_spike_threshold = 1.5
    max_trade_hours = 8
    risk_per_trade = 0.02
    
    def init(self):
        close = self.data.Close.astype(float)
        volume = self.data.Volume.astype(float)
        
        self.bb_upper = self.I(talib.BBANDS, close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)[0]
        self.bb_middle = self.I(talib.BBANDS, close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)[1]
        self.bb_lower = self.I(talib.BBANDS, close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)[2]
        
        self.sma_50 = self.I(talib.SMA, close, timeperiod=self.sma_period)
        self.volume_sma = self.I(talib.SMA, volume, timeperiod=20)
        
        self.squeeze_count = self.I(self.calculate_squeeze_count)
        self.entry_time = None
        self.breakeven_stop = None
        
    def calculate_squeeze_count(self):
        bb_width = (self.bb_upper - self.bb_lower) / self.bb_middle
        squeeze_condition = bb_width < self.squeeze_threshold
        squeeze_count = np.zeros_like(self.data.Close)
        count = 0
        for i in range(len(squeeze_count)):
            if squeeze_condition[i]:
                count += 1
            else:
                count = 0
            squeeze_count[i] = count
        return squeeze_count
    
    def next(self):
        if len(self.data) < 50:
            return
            
        current_idx = len(self.data) - 1
        current_time = self.data.index[-1]
        
        if self.position:
            hours_in_trade = (current_time - self.entry_time).total_seconds() / 3600
            if hours_in_trade >= self.max_trade_hours:
                print(f"🌙 MOON DEV: Time-based exit after {hours_in_trade:.1f} hours")
                self.position.close()
                return
                
            if self.breakeven_stop is None and self.data.Close[-1] >= self.entry_price + self.bb_width_at_entry:
                self.breakeven_stop = self.entry_price
                print(f"🌙 MOON DEV: Moving to breakeven at {self.breakeven_stop:.2f}")
            
            if self.breakeven_stop and self.data.Low[-1] <= self.breakeven_stop:
                print(f"🌙 MOON DEV: Breakeven stop hit at {self.breakeven_stop:.2f}")
                self.position.close()
                return
                
            return
        
        if not self.is_trading_hours():
            return
            
        bb_width = (self.bb_upper[-1] - self.bb_lower[-1]) / self.bb_middle[-1]
        volume_spike = self.data.Volume[-1] > self.volume_sma[-1] * self.volume_spike_threshold
        price_above_bb = self.data.Close[-1] > self.bb_upper[-1]
        squeeze_valid = self.squeeze_count[-1] >= 3
        
        sma_slope = self.sma_50[-1] > self.sma_50[-2]
        
        gap_condition = abs(self.data.Open[-1] - self.data.Close[-2]) / self.data.Close[-2] <= 0.005
        
        if (squeeze_valid and price_above_bb and volume_spike and sma_slope and gap_condition):
            print(f"🌙 MOON DEV: Volatility Breakout Signal Detected!")
            print(f"  BB Width: {bb_width:.4f}, Volume Spike: {self.data.Volume[-1]/self.volume_sma[-1]:.2f}x")
            print(f"  Squeeze Count: {self.squeeze_count[-1]}, SMA Slope: {'Up' if sma_slope else 'Down'}")
            
            entry_price = self.data.Open[-1]
            stop_loss = self.bb_middle[-1]
            bb_width_value = self.bb_upper[-1] - self.bb_lower[-1]
            take_profit = entry_price + (2 * bb_width_value)
            
            risk_per_share = entry_price - stop_loss
            if risk_per_share <= 0:
                print(f"🌙 MOON DEV: Invalid risk calculation - skipping trade")
                return
                
            risk_amount = self.equity * self.risk_per_trade
            position_size = risk_amount / risk_per_share
            position_size = int(round(position_size))
            
            if position_size <= 0:
                print(f"🌙 MOON DEV: Position size too small - skipping trade")
                return
            
            print(f"🌙 MOON DEV: Entering LONG at {entry_price:.2f}")
            print(f"  SL: {stop_loss:.2f}, TP: {take_profit:.2f}, Size: {position_size} shares")
            
            if stop_loss >= entry_price or take_profit <= entry_price:
                print(f"🌙 MOON DEV: Order validation failed - SL: {stop_loss:.2f}, Entry: {entry_price:.2f}, TP: {take_profit:.2f}")
                return
                
            self.buy(size=position_size, sl=stop_loss, tp=take_profit)
            self.entry_time = current_time
            self.entry_price = entry_price
            self.bb_width_at_entry = bb_width_value
            self.breakeven_stop = None
    
    def is_trading_hours(self):
        current_time = self.data.index[-1]
        hour = current_time.hour
        minute = current_time.minute
        
        est_hour = hour - 5
        if current_time.dst():
            est_hour = hour - 4
            
        time_value = est_hour + minute / 60.0
        
        return 9.5 <= time_value <= 15.5

data = load_data()
bt = Backtest(data, VolatilityBreakout, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)