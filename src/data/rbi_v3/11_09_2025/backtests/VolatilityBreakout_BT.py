import yfinance as yf
import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

def load_data():
    ticker = yf.Ticker("SPY")
    data = ticker.history(period="1y", interval="1h")
    data.columns = data.columns.str.strip()
    required = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in data.columns for col in required):
        raise ValueError(f"Missing required columns. Got: {list(data.columns)}")
    return data

class VolatilityBreakout(Strategy):
    bb_period = 20
    bb_std = 2
    rsi_period = 14
    squeeze_threshold = 0.02
    volume_threshold = 1.2
    risk_per_trade = 0.01
    
    def init(self):
        close_prices = self.data.Close.astype(float)
        high_prices = self.data.High.astype(float)
        low_prices = self.data.Low.astype(float)
        volume_data = self.data.Volume.astype(float)
        
        self.bb_upper = self.I(talib.BBANDS, close_prices, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)[0]
        self.bb_middle = self.I(talib.BBANDS, close_prices, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)[1]
        self.bb_lower = self.I(talib.BBANDS, close_prices, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)[2]
        
        self.bb_width = self.I(lambda: (self.bb_upper - self.bb_lower) / self.bb_middle)
        
        self.volume_sma = self.I(talib.SMA, volume_data, timeperiod=20)
        self.rsi = self.I(talib.RSI, close_prices, timeperiod=self.rsi_period)
        
        self.squeeze_signal = self.I(lambda: self.bb_width < self.squeeze_threshold)
        self.volume_signal = self.I(lambda: volume_data > (self.volume_sma * self.volume_threshold))
        
        self.breakout_high = self.I(lambda: high_prices > self.bb_upper)
        self.breakout_low = self.I(lambda: low_prices < self.bb_lower)
        
        self.squeeze_count = 0

    def next(self):
        if len(self.data) < 21:
            return
            
        current_price = self.data.Close[-1]
        bb_middle = self.bb_middle[-1]
        bb_upper = self.bb_upper[-1]
        bb_lower = self.bb_lower[-1]
        bb_width = self.bb_width[-1]
        volume = self.data.Volume[-1]
        volume_sma = self.volume_sma[-1]
        rsi = self.rsi[-1]
        
        if bb_width < self.squeeze_threshold:
            self.squeeze_count += 1
        else:
            self.squeeze_count = 0
        
        if not self.position:
            if (self.squeeze_count >= 4 and 
                volume > (volume_sma * self.volume_threshold)):
                
                if (self.breakout_high[-2] and 
                    self.data.Open[-1] > bb_upper):
                    
                    entry_price = self.data.Open[-1]
                    stop_loss_price = min(entry_price * 0.98, bb_lower)
                    take_profit_price = bb_middle
                    
                    if stop_loss_price >= entry_price or take_profit_price <= entry_price:
                        print(f"🌙 MOON DEV DEBUG: Long order validation failed - SL: {stop_loss_price}, Entry: {entry_price}, TP: {take_profit_price}")
                        return
                    
                    risk_amount = self.equity * self.risk_per_trade
                    risk_per_share = entry_price - stop_loss_price
                    
                    if risk_per_share > 0:
                        position_size = int(round(risk_amount / risk_per_share))
                        if position_size > 0:
                            print(f"🌙 MOON DEV: LONG ENTRY - Price: {entry_price:.2f}, SL: {stop_loss_price:.2f}, TP: {take_profit_price:.2f}, Size: {position_size}")
                            self.buy(size=position_size, sl=stop_loss_price, tp=take_profit_price)
                
                elif (self.breakout_low[-2] and 
                      self.data.Open[-1] < bb_lower):
                    
                    entry_price = self.data.Open[-1]
                    stop_loss_price = max(entry_price * 1.02, bb_upper)
                    take_profit_price = bb_middle
                    
                    if take_profit_price >= entry_price or stop_loss_price <= entry_price:
                        print(f"🌙 MOON DEV DEBUG: Short order validation failed - TP: {take_profit_price}, Entry: {entry_price}, SL: {stop_loss_price}")
                        return
                    
                    risk_amount = self.equity * self.risk_per_trade
                    risk_per_share = stop_loss_price - entry_price
                    
                    if risk_per_share > 0:
                        position_size = int(round(risk_amount / risk_per_share))
                        if position_size > 0:
                            print(f"🌙 MOON DEV: SHORT ENTRY - Price: {entry_price:.2f}, SL: {stop_loss_price:.2f}, TP: {take_profit_price:.2f}, Size: {position_size}")
                            self.sell(size=position_size, sl=stop_loss_price, tp=take_profit_price)
        
        else:
            if self.position.is_long:
                if rsi >= 70:
                    print(f"🌙 MOON DEV: LONG EXIT - RSI overbought at {rsi:.1f}")
                    self.position.close()
            elif self.position.is_short:
                if rsi <= 30:
                    print(f"🌙 MOON DEV: SHORT EXIT - RSI oversold at {rsi:.1f}")
                    self.position.close()

data = load_data()
bt = Backtest(data, VolatilityBreakout, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)