import yfinance as yf
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import talib

def load_data():
    ticker = yf.Ticker("SPY")
    data = ticker.history(period="2y", interval="1d")
    data.columns = data.columns.str.strip()
    required = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in data.columns for col in required):
        raise ValueError(f"Missing required columns. Got: {list(data.columns)}")
    return data

class AdaptiveTrendFlow(Strategy):
    ema_fast_period = 20
    ema_slow_period = 50
    atr_period = 14
    adx_period = 14
    volume_sma_period = 20
    risk_per_trade = 0.02
    max_drawdown_per_trade = 0.05
    portfolio_max_drawdown = 0.10
    
    def init(self):
        close_prices = self.data.Close.astype(float)
        high_prices = self.data.High.astype(float)
        low_prices = self.data.Low.astype(float)
        volume_data = self.data.Volume.astype(float)
        
        self.ema_fast = self.I(talib.EMA, close_prices, timeperiod=self.ema_fast_period)
        self.ema_slow = self.I(talib.EMA, close_prices, timeperiod=self.ema_slow_period)
        self.atr = self.I(talib.ATR, high_prices, low_prices, close_prices, timeperiod=self.atr_period)
        self.adx = self.I(talib.ADX, high_prices, low_prices, close_prices, timeperiod=self.adx_period)
        self.volume_sma = self.I(talib.SMA, volume_data, timeperiod=self.volume_sma_period)
        
        self.trailing_high = None
        self.trailing_low = None
        self.portfolio_peak = 1000000
        
    def next(self):
        if len(self.data) < max(self.ema_slow_period, self.adx_period, self.atr_period) + 1:
            return
            
        current_close = self.data.Close[-1]
        previous_close = self.data.Close[-2]
        current_volume = self.data.Volume[-1]
        
        ema_fast_current = self.ema_fast[-1]
        ema_slow_current = self.ema_slow[-1]
        ema_fast_previous = self.ema_fast[-2]
        ema_slow_previous = self.ema_slow[-2]
        
        adx_current = self.adx[-1]
        adx_previous = self.adx[-2]
        atr_current = self.atr[-1]
        volume_sma_current = self.volume_sma[-1]
        
        current_equity = self.equity
        if current_equity > self.portfolio_peak:
            self.portfolio_peak = current_equity
            
        portfolio_drawdown = (self.portfolio_peak - current_equity) / self.portfolio_peak
        
        if portfolio_drawdown > self.portfolio_max_drawdown:
            print(f"🌙 MOON DEV: Portfolio drawdown {portfolio_drawdown:.2%} exceeds maximum {self.portfolio_max_drawdown:.2%} - skipping trades")
            return
            
        if self.position:
            if self.position.is_long:
                self.trailing_high = max(self.trailing_high, self.data.High[-1])
                trailing_stop = self.trailing_high - (2 * atr_current)
                
                exit_conditions = [
                    current_close < ema_fast_current,
                    ema_fast_current < ema_slow_current and ema_fast_previous >= ema_slow_previous,
                    adx_current < 20,
                    current_close < trailing_stop
                ]
                
                if any(exit_conditions):
                    print(f"🌙 MOON DEV: Closing LONG position - Close: {current_close:.2f}, EMA20: {ema_fast_current:.2f}, EMA50: {ema_slow_current:.2f}, ADX: {adx_current:.2f}")
                    self.position.close()
                    self.trailing_high = None
                    
            elif self.position.is_short:
                self.trailing_low = min(self.trailing_low, self.data.Low[-1])
                trailing_stop = self.trailing_low + (2 * atr_current)
                
                exit_conditions = [
                    current_close > ema_fast_current,
                    ema_fast_current > ema_slow_current and ema_fast_previous <= ema_slow_previous,
                    adx_current < 20,
                    current_close > trailing_stop
                ]
                
                if any(exit_conditions):
                    print(f"🌙 MOON DEV: Closing SHORT position - Close: {current_close:.2f}, EMA20: {ema_fast_current:.2f}, EMA50: {ema_slow_current:.2f}, ADX: {adx_current:.2f}")
                    self.position.close()
                    self.trailing_low = None
                    
        else:
            risk_amount = current_equity * self.risk_per_trade
            max_loss_per_share = 2.5 * atr_current
            position_size = int(round(risk_amount / max_loss_per_share))
            
            if position_size <= 0:
                return
                
            long_conditions = [
                current_close > ema_fast_current,
                current_close > ema_slow_current,
                ema_fast_current > ema_slow_current,
                adx_current > 25,
                current_close > previous_close,
                current_volume > volume_sma_current
            ]
            
            short_conditions = [
                current_close < ema_fast_current,
                current_close < ema_slow_current,
                ema_fast_current < ema_slow_current,
                adx_current > 25,
                current_close < previous_close,
                current_volume > volume_sma_current
            ]
            
            if all(long_conditions):
                entry_price = current_close
                stop_loss_price = entry_price - (2.5 * atr_current)
                take_profit_price = entry_price + (5 * atr_current)
                
                if stop_loss_price >= entry_price or take_profit_price <= entry_price:
                    print(f"🌙 MOON DEV DEBUG: Long order validation failed - SL: {stop_loss_price:.2f}, Entry: {entry_price:.2f}, TP: {take_profit_price:.2f}")
                    return
                    
                print(f"🌙 MOON DEV: Entering LONG - Close: {current_close:.2f}, EMA20: {ema_fast_current:.2f}, EMA50: {ema_slow_current:.2f}, ADX: {adx_current:.2f}, Volume: {current_volume:.0f}")
                self.buy(size=position_size, sl=stop_loss_price, tp=take_profit_price)
                self.trailing_high = self.data.High[-1]
                
            elif all(short_conditions):
                entry_price = current_close
                stop_loss_price = entry_price + (2.5 * atr_current)
                take_profit_price = entry_price - (5 * atr_current)
                
                if take_profit_price >= entry_price or stop_loss_price <= entry_price:
                    print(f"🌙 MOON DEV DEBUG: Short order validation failed - TP: {take_profit_price:.2f}, Entry: {entry_price:.2f}, SL: {stop_loss_price:.2f}")
                    return
                    
                print(f"🌙 MOON DEV: Entering SHORT - Close: {current_close:.2f}, EMA20: {ema_fast_current:.2f}, EMA50: {ema_slow_current:.2f}, ADX: {adx_current:.2f}, Volume: {current_volume:.0f}")
                self.sell(size=position_size, sl=stop_loss_price, tp=take_profit_price)
                self.trailing_low = self.data.Low[-1]

data = load_data()
bt = Backtest(data, AdaptiveTrendFlow, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)