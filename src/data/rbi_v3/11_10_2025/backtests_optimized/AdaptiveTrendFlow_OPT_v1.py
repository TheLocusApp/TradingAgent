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
    # 🌙 OPTIMIZED PARAMETERS: Tighter EMAs for faster signals, higher ADX for stronger trends
    ema_fast_period = 12
    ema_slow_period = 26
    atr_period = 14
    adx_period = 14
    volume_sma_period = 20
    rsi_period = 14
    
    # 🌙 IMPROVED RISK MANAGEMENT: Slightly higher risk per trade for better returns
    risk_per_trade = 0.025
    max_drawdown_per_trade = 0.04
    portfolio_max_drawdown = 0.08
    
    # 🌙 ADDED: Dynamic position sizing based on volatility
    volatility_lookback = 20
    
    def init(self):
        close_prices = self.data.Close.astype(float)
        high_prices = self.data.High.astype(float)
        low_prices = self.data.Low.astype(float)
        volume_data = self.data.Volume.astype(float)
        
        # 🌙 CORE INDICATORS
        self.ema_fast = self.I(talib.EMA, close_prices, timeperiod=self.ema_fast_period)
        self.ema_slow = self.I(talib.EMA, close_prices, timeperiod=self.ema_slow_period)
        self.atr = self.I(talib.ATR, high_prices, low_prices, close_prices, timeperiod=self.atr_period)
        self.adx = self.I(talib.ADX, high_prices, low_prices, close_prices, timeperiod=self.adx_period)
        self.volume_sma = self.I(talib.SMA, volume_data, timeperiod=self.volume_sma_period)
        
        # 🌙 ADDED: RSI for momentum confirmation and overbought/oversold filtering
        self.rsi = self.I(talib.RSI, close_prices, timeperiod=self.rsi_period)
        
        # 🌙 ADDED: Volatility-based position sizing
        self.volatility = self.I(talib.STDDEV, close_prices, timeperiod=self.volatility_lookback)
        
        self.trailing_high = None
        self.trailing_low = None
        self.portfolio_peak = 1000000
        
    def next(self):
        if len(self.data) < max(self.ema_slow_period, self.adx_period, self.atr_period, self.rsi_period) + 1:
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
        rsi_current = self.rsi[-1]
        volatility_current = self.volatility[-1]
        
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
                trailing_stop = self.trailing_high - (1.8 * atr_current)  # 🌙 TIGHTER TRAILING STOP
                
                # 🌙 IMPROVED EXIT CONDITIONS: More responsive exits
                exit_conditions = [
                    current_close < ema_fast_current,
                    (ema_fast_previous >= ema_slow_previous and ema_fast_current < ema_slow_current),
                    adx_current < 25,  # 🌙 HIGHER ADX THRESHOLD FOR TREND STRENGTH
                    current_close < trailing_stop,
                    rsi_current > 70  # 🌙 ADDED: Exit on overbought RSI
                ]
                
                if any(exit_conditions):
                    print(f"🌙 MOON DEV: Closing LONG position - Close: {current_close:.2f}, EMA12: {ema_fast_current:.2f}, EMA26: {ema_slow_current:.2f}, ADX: {adx_current:.2f}, RSI: {rsi_current:.2f}")
                    self.position.close()
                    self.trailing_high = None
                    
            elif self.position.is_short:
                self.trailing_low = min(self.trailing_low, self.data.Low[-1])
                trailing_stop = self.trailing_low + (1.8 * atr_current)  # 🌙 TIGHTER TRAILING STOP
                
                # 🌙 IMPROVED EXIT CONDITIONS: More responsive exits
                exit_conditions = [
                    current_close > ema_fast_current,
                    (ema_fast_previous <= ema_slow_previous and ema_fast_current > ema_slow_current),
                    adx_current < 25,  # 🌙 HIGHER ADX THRESHOLD FOR TREND STRENGTH
                    current_close > trailing_stop,
                    rsi_current < 30  # 🌙 ADDED: Exit on oversold RSI
                ]
                
                if any(exit_conditions):
                    print(f"🌙 MOON DEV: Closing SHORT position - Close: {current_close:.2f}, EMA12: {ema_fast_current:.2f}, EMA26: {ema_slow_current:.2f}, ADX: {adx_current:.2f}, RSI: {rsi_current:.2f}")
                    self.position.close()
                    self.trailing_low = None
                    
        else:
            # 🌙 IMPROVED POSITION SIZING: Dynamic sizing based on volatility
            volatility_factor = max(0.5, min(2.0, volatility_current / np.mean(self.volatility[-10:])))
            adjusted_risk = self.risk_per_trade / volatility_factor
            
            risk_amount = current_equity * adjusted_risk
            max_loss_per_share = 2.0 * atr_current  # 🌙 TIGHTER STOP LOSS
            
            position_size = int(round(risk_amount / max_loss_per_share))
            
            if position_size <= 0:
                return
                
            # 🌙 IMPROVED ENTRY CONDITIONS: Stricter filters for higher quality setups
            long_conditions = [
                current_close > ema_fast_current,
                current_close > ema_slow_current,
                ema_fast_current > ema_slow_current,
                ema_fast_previous <= ema_slow_previous,  # 🌙 ADDED: EMA crossover confirmation
                adx_current > 30,  # 🌙 HIGHER ADX FOR STRONGER TRENDS
                adx_previous < adx_current,  # 🌙 ADDED: ADX rising
                current_close > previous_close,
                current_volume > volume_sma_current * 1.1,  # 🌙 HIGHER VOLUME THRESHOLD
                rsi_current > 40 and rsi_current < 65,  # 🌙 ADDED: RSI momentum filter (avoid overbought)
                volatility_current < np.mean(self.volatility[-5:]) * 1.5  # 🌙 ADDED: Avoid high volatility periods
            ]
            
            short_conditions = [
                current_close < ema_fast_current,
                current_close < ema_slow_current,
                ema_fast_current < ema_slow_current,
                ema_fast_previous >= ema_slow_previous,  # 🌙 ADDED: EMA crossover confirmation
                adx_current > 30,  # 🌙 HIGHER ADX FOR STRONGER TRENDS
                adx_previous < adx_current,  # 🌙 ADDED: ADX rising
                current_close < previous_close,
                current_volume > volume_sma_current * 1.1,  # 🌙 HIGHER VOLUME THRESHOLD
                rsi_current < 60 and rsi_current > 35,  # 🌙 ADDED: RSI momentum filter (avoid oversold)
                volatility_current < np.mean(self.volatility[-5:]) * 1.5  # 🌙 ADDED: Avoid high volatility periods
            ]
            
            if sum(long_conditions) >= 9:  # 🌙 STRICTER: Require 9 out of 10 conditions
                entry_price = current_close
                stop_loss_price = entry_price - (2.0 * atr_current)  # 🌙 TIGHTER STOP LOSS
                take_profit_price = entry_price + (4.0 * atr_current)  # 🌙 IMPROVED RISK-REWARD (2:1)
                
                # 🌙 MOON DEV SL/TP VALIDATION
                if stop_loss_price >= entry_price or take_profit_price <= entry_price:
                    print(f"🌙 MOON DEV DEBUG: Long order validation failed - SL: {stop_loss_price:.2f}, Entry: {entry_price:.2f}, TP: {take_profit_price:.2f}")
                    return
                    
                print(f"🌙 MOON DEV: Entering LONG - Close: {current_close:.2f}, EMA12: {ema_fast_current:.2f}, EMA26: {ema_slow_current:.2f}, ADX: {adx_current:.2f}, RSI: {rsi_current:.2f}, Vol: {current_volume:.0f}")
                self.buy(size=position_size, sl=stop_loss_price, tp=take_profit_price)
                self.trailing_high = self.data.High[-1]
                
            elif sum(short_conditions) >= 9:  # 🌙 STRICTER: Require 9 out of 10 conditions
                entry_price = current_close
                stop_loss_price = entry_price + (2.0 * atr_current)  # 🌙 TIGHTER STOP LOSS
                take_profit_price = entry_price - (4.0 * atr_current)  # 🌙 IMPROVED RISK-REWARD (2:1)
                
                # 🌙 MOON DEV SL/TP VALIDATION
                if take_profit_price >= entry_price or stop_loss_price <= entry_price:
                    print(f"🌙 MOON DEV DEBUG: Short order validation failed - TP: {take_profit_price:.2f}, Entry: {entry_price:.2f}, SL: {stop_loss_price:.2f}")
                    return
                    
                print(f"🌙 MOON DEV: Entering SHORT - Close: {current_close:.2f}, EMA12: {ema_fast_current:.2f}, EMA26: {ema_slow_current:.2f}, ADX: {adx_current:.2f}, RSI: {rsi_current:.2f}, Vol: {current_volume:.0f}")
                self.sell(size=position_size, sl=stop_loss_price, tp=take_profit_price)
                self.trailing_low = self.data.Low[-1]

data = load_data()
bt = Backtest(data, AdaptiveTrendFlow, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)