import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
import yfinance as yf

def load_data():
    ticker = yf.Ticker("SPY")
    data = ticker.history(period="2y", interval="1h")
    data.columns = data.columns.str.strip()
    required = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in data.columns for col in required):
        raise ValueError(f"Missing required columns. Got: {list(data.columns)}")
    return data

class AdaptiveReversion(Strategy):
    bb_period = 20
    bb_std = 2
    rsi_period = 14
    atr_period = 14
    volume_ma_period = 20
    max_risk_per_trade = 0.02
    atr_stop_multiplier = 2
    max_bars_hold = 5
    vix_threshold = 25
    
    def init(self):
        close = self.data.Close.astype(float)
        high = self.data.High.astype(float)
        low = self.data.Low.astype(float)
        volume = self.data.Volume.astype(float)
        
        self.bb_upper = self.I(talib.BBANDS, close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)[0]
        self.bb_lower = self.I(talib.BBANDS, close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)[2]
        self.sma_20 = self.I(talib.SMA, close, timeperiod=self.bb_period)
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        self.volume_ma = self.I(talib.SMA, volume, timeperiod=self.volume_ma_period)
        
        self.consecutive_losses = 0
        self.trade_count = 0
        self.entry_bar = None
        
    def next(self):
        if len(self.data) < max(self.bb_period, self.rsi_period, self.atr_period) + 1:
            return
            
        current_price = self.data.Close[-1]
        current_rsi = self.rsi[-1]
        current_volume = self.data.Volume[-1]
        current_atr = self.atr[-1]
        bb_upper = self.bb_upper[-1]
        bb_lower = self.bb_lower[-1]
        volume_ma = self.volume_ma[-1]
        sma_20 = self.sma_20[-1]
        
        if self.position:
            self.manage_position(current_price, current_rsi, sma_20)
        else:
            if self.consecutive_losses >= 3:
                print(f"🌙 MOON DEV: Skipping trade - 3 consecutive losses reached")
                return
                
            self.check_entries(current_price, current_rsi, current_volume, volume_ma, 
                             bb_upper, bb_lower, current_atr, sma_20)
    
    def check_entries(self, price, rsi, volume, volume_ma, bb_upper, bb_lower, atr, sma_20):
        if volume < volume_ma:
            return
            
        position_size = self.calculate_position_size(atr, price)
        if position_size <= 0:
            return
            
        if price <= bb_lower and rsi < 30:
            print(f"🌙 MOON DEV: LONG SIGNAL - Price: {price:.2f}, RSI: {rsi:.2f}")
            stop_loss = price - (atr * self.atr_stop_multiplier)
            take_profit = sma_20
            
            if stop_loss >= price or take_profit <= price:
                print(f"🌙 MOON DEV: Long order validation failed - SL: {stop_loss:.2f}, Entry: {price:.2f}, TP: {take_profit:.2f}")
                return
                
            self.buy(size=position_size, sl=stop_loss, tp=take_profit)
            self.entry_bar = len(self.data)
            
        elif price >= bb_upper and rsi > 70:
            print(f"🌙 MOON DEV: SHORT SIGNAL - Price: {price:.2f}, RSI: {rsi:.2f}")
            stop_loss = price + (atr * self.atr_stop_multiplier)
            take_profit = sma_20
            
            if take_profit >= price or stop_loss <= price:
                print(f"🌙 MOON DEV: Short order validation failed - TP: {take_profit:.2f}, Entry: {price:.2f}, SL: {stop_loss:.2f}")
                return
                
            self.sell(size=position_size, sl=stop_loss, tp=take_profit)
            self.entry_bar = len(self.data)
    
    def manage_position(self, price, rsi, sma_20):
        if self.entry_bar and (len(self.data) - self.entry_bar) >= self.max_bars_hold:
            print(f"🌙 MOON DEV: Time-based exit after {self.max_bars_hold} bars")
            self.position.close()
            self.entry_bar = None
            return
            
        if self.position.is_long:
            if rsi > 45 or abs(price - sma_20) < 0.01:
                print(f"🌙 MOON DEV: Long exit - RSI: {rsi:.2f}, Price near SMA")
                self.position.close()
                self.entry_bar = None
        elif self.position.is_short:
            if rsi < 55 or abs(price - sma_20) < 0.01:
                print(f"🌙 MOON DEV: Short exit - RSI: {rsi:.2f}, Price near SMA")
                self.position.close()
                self.entry_bar = None
    
    def calculate_position_size(self, atr, price):
        risk_amount = self.equity * self.max_risk_per_trade
        risk_per_share = atr * self.atr_stop_multiplier
        
        if risk_per_share <= 0:
            return 0
            
        raw_size = risk_amount / risk_per_share
        position_size = int(round(raw_size))
        
        max_shares = int(self.equity * 0.1 / price)
        position_size = min(position_size, max_shares)
        
        return max(1, position_size)
    
    def notify_trade(self, trade):
        if trade.is_closed:
            self.trade_count += 1
            if trade.pnl < 0:
                self.consecutive_losses += 1
                print(f"🌙 MOON DEV: Trade LOSS - PnL: {trade.pnl:.2f}, Consecutive losses: {self.consecutive_losses}")
            else:
                self.consecutive_losses = 0
                print(f"🌙 MOON DEV: Trade WIN - PnL: {trade.pnl:.2f}, Consecutive losses reset")

data = load_data()
bt = Backtest(data, AdaptiveReversion, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)