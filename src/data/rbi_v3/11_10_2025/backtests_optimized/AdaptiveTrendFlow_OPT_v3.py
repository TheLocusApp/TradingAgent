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
    # 🌙 MOON DEV OPTIMIZED PARAMETERS
    ema_fast_period = 15  # Tighter EMA for faster trend detection
    ema_slow_period = 45  # Adjusted for better trend filtering
    atr_period = 10  # Shorter ATR for more responsive volatility
    adx_period = 12  # Faster ADX for quicker trend strength assessment
    volume_sma_period = 15  # Tighter volume filter
    rsi_period = 14  # NEW: RSI for momentum confirmation
    risk_per_trade = 0.025  # Increased risk slightly for higher returns
    max_drawdown_per_trade = 0.04  # Tighter per-trade risk
    portfolio_max_drawdown = 0.08  # Tighter portfolio risk
    
    def init(self):
        close_prices = self.data.Close.astype(float)
        high_prices = self.data.High.astype(float)
        low_prices = self.data.Low.astype(float)
        volume_data = self.data.Volume.astype(float)
        
        # 🌙 CORE TREND INDICATORS
        self.ema_fast = self.I(talib.EMA, close_prices, timeperiod=self.ema_fast_period)
        self.ema_slow = self.I(talib.EMA, close_prices, timeperiod=self.ema_slow_period)
        self.atr = self.I(talib.ATR, high_prices, low_prices, close_prices, timeperiod=self.atr_period)
        self.adx = self.I(talib.ADX, high_prices, low_prices, close_prices, timeperiod=self.adx_period)
        self.volume_sma = self.I(talib.SMA, volume_data, timeperiod=self.volume_sma_period)
        
        # 🌙 NEW: MOMENTUM & VOLATILITY FILTERS
        self.rsi = self.I(talib.RSI, close_prices, timeperiod=self.rsi_period)
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, close_prices, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )
        
        self.trailing_high = None
        self.trailing_low = None
        self.portfolio_peak = 1000000
        
    def next(self):
        if len(self.data) < max(self.ema_slow_period, self.adx_period, self.atr_period, 20) + 1:
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
        
        # 🌙 NEW: MOMENTUM & VOLATILITY READINGS
        rsi_current = self.rsi[-1]
        rsi_previous = self.rsi[-2]
        bb_upper_current = self.bb_upper[-1]
        bb_lower_current = self.bb_lower[-1]
        
        current_equity = self.equity
        if current_equity > self.portfolio_peak:
            self.portfolio_peak = current_equity
            
        portfolio_drawdown = (self.portfolio_peak - current_equity) / self.portfolio_peak
        
        if portfolio_drawdown > self.portfolio_max_drawdown:
            print(f"🌙 MOON DEV: Portfolio drawdown {portfolio_drawdown:.2%} exceeds maximum {self.portfolio_max_drawdown:.2%} - skipping trades")
            return
            
        # 🌙 DYNAMIC POSITION SIZING BASED ON VOLATILITY
        volatility_factor = max(0.5, min(2.0, atr_current / current_close * 100))  # Normalize ATR
        adjusted_risk = self.risk_per_trade / volatility_factor
        risk_amount = current_equity * adjusted_risk
        
        if self.position:
            if self.position.is_long:
                self.trailing_high = max(self.trailing_high, self.data.High[-1])
                # 🌙 DYNAMIC TRAILING STOP: Tighter in high volatility
                trailing_stop_atr_multiplier = 1.8 if volatility_factor > 1.5 else 2.2
                trailing_stop = self.trailing_high - (trailing_stop_atr_multiplier * atr_current)
                
                exit_conditions = [
                    current_close < ema_fast_current,
                    (ema_fast_previous >= ema_slow_previous and ema_fast_current < ema_slow_current),
                    adx_current < 22,  # Tighter ADX filter
                    current_close < trailing_stop,
                    rsi_current > 75,  # NEW: Exit overbought conditions
                    current_close > bb_upper_current  # NEW: Exit at upper Bollinger Band
                ]
                
                if any(exit_conditions):
                    print(f"🌙 MOON DEV: Closing LONG position - Close: {current_close:.2f}, EMA15: {ema_fast_current:.2f}, EMA45: {ema_slow_current:.2f}, ADX: {adx_current:.2f}, RSI: {rsi_current:.2f}")
                    self.position.close()
                    self.trailing_high = None
                    
            elif self.position.is_short:
                self.trailing_low = min(self.trailing_low, self.data.Low[-1])
                # 🌙 DYNAMIC TRAILING STOP: Tighter in high volatility
                trailing_stop_atr_multiplier = 1.8 if volatility_factor > 1.5 else 2.2
                trailing_stop = self.trailing_low + (trailing_stop_atr_multiplier * atr_current)
                
                exit_conditions = [
                    current_close > ema_fast_current,
                    (ema_fast_previous <= ema_slow_previous and ema_fast_current > ema_slow_current),
                    adx_current < 22,  # Tighter ADX filter
                    current_close > trailing_stop,
                    rsi_current < 25,  # NEW: Exit oversold conditions
                    current_close < bb_lower_current  # NEW: Exit at lower Bollinger Band
                ]
                
                if any(exit_conditions):
                    print(f"🌙 MOON DEV: Closing SHORT position - Close: {current_close:.2f}, EMA15: {ema_fast_current:.2f}, EMA45: {ema_slow_current:.2f}, ADX: {adx_current:.2f}, RSI: {rsi_current:.2f}")
                    self.position.close()
                    self.trailing_low = None
                    
        else:
            max_loss_per_share = 2.2 * atr_current  # Tighter initial stop
            position_size = int(round(risk_amount / max_loss_per_share))
            
            if position_size <= 0:
                return
                
            # 🌙 OPTIMIZED LONG CONDITIONS WITH MOMENTUM FILTERS
            long_conditions = [
                current_close > ema_fast_current,
                current_close > ema_slow_current,
                ema_fast_current > ema_slow_current,
                ema_fast_current > ema_fast_previous,  # NEW: EMA accelerating
                adx_current > 28,  # Higher ADX threshold for stronger trends
                adx_current > adx_previous,  # NEW: ADX increasing
                current_close > previous_close,
                current_volume > volume_sma_current * 1.1,  # Stronger volume requirement
                rsi_current > 45 and rsi_current < 70,  # NEW: RSI in optimal zone
                rsi_current > rsi_previous,  # NEW: RSI momentum up
                current_close < bb_upper_current  # NEW: Not at extreme overbought
            ]
            
            # 🌙 OPTIMIZED SHORT CONDITIONS WITH MOMENTUM FILTERS
            short_conditions = [
                current_close < ema_fast_current,
                current_close < ema_slow_current,
                ema_fast_current < ema_slow_current,
                ema_fast_current < ema_fast_previous,  # NEW: EMA accelerating down
                adx_current > 28,  # Higher ADX threshold for stronger trends
                adx_current > adx_previous,  # NEW: ADX increasing
                current_close < previous_close,
                current_volume > volume_sma_current * 1.1,  # Stronger volume requirement
                rsi_current < 55 and rsi_current > 30,  # NEW: RSI in optimal zone
                rsi_current < rsi_previous,  # NEW: RSI momentum down
                current_close > bb_lower_current  # NEW: Not at extreme oversold
            ]
            
            # 🌙 COUNT VALID CONDITIONS FOR CONFIDENCE SCORING
            long_score = sum(long_conditions)
            short_score = sum(short_conditions)
            
            if long_score >= 9:  # Require 9/11 conditions for higher quality
                entry_price = current_close
                stop_loss_price = entry_price - (2.2 * atr_current)  # Tighter SL
                take_profit_price = entry_price + (4.5 * atr_current)  # Better R:R
                
                # 🌙 CRITICAL: VALIDATE LONG ORDER PRICING
                if stop_loss_price >= entry_price or take_profit_price <= entry_price:
                    print(f"🌙 MOON DEV DEBUG: Long order validation failed - SL: {stop_loss_price:.2f}, Entry: {entry_price:.2f}, TP: {take_profit_price:.2f}")
                    return
                    
                print(f"🌙 MOON DEV: Entering LONG - Close: {current_close:.2f}, EMA15: {ema_fast_current:.2f}, EMA45: {ema_slow_current:.2f}, ADX: {adx_current:.2f}, RSI: {rsi_current:.2f}, Score: {long_score}/11")
                self.buy(size=position_size, sl=stop_loss_price, tp=take_profit_price)
                self.trailing_high = self.data.High[-1]
                
            elif short_score >= 9:  # Require 9/11 conditions for higher quality
                entry_price = current_close
                take_profit_price = entry_price - (4.5 * atr_current)  # SUBTRACT for TP (below entry)
                stop_loss_price = entry_price + (2.2 * atr_current)    # ADD for SL (above entry)
                
                # 🌙 CRITICAL: VALIDATE SHORT ORDER PRICING
                if take_profit_price >= entry_price or stop_loss_price <= entry_price:
                    print(f"🌙 MOON DEV DEBUG: Short order validation failed - TP: {take_profit_price:.2f}, Entry: {entry_price:.2f}, SL: {stop_loss_price:.2f}")
                    return
                    
                print(f"🌙 MOON DEV: Entering SHORT - Close: {current_close:.2f}, EMA15: {ema_fast_current:.2f}, EMA45: {ema_slow_current:.2f}, ADX: {adx_current:.2f}, RSI: {rsi_current:.2f}, Score: {short_score}/11")
                self.sell(size=position_size, sl=stop_loss_price, tp=take_profit_price)
                self.trailing_low = self.data.Low[-1]

data = load_data()
bt = Backtest(data, AdaptiveTrendFlow, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)