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
    # 🌙 MOON DEV OPTIMIZATION: Fine-tuned parameters for better risk-adjusted returns
    ema_fast_period = 15      # Faster EMA for quicker trend detection
    ema_slow_period = 45      # Adjusted slow EMA for better trend filtering
    atr_period = 10           # Shorter ATR for more responsive volatility measurement
    adx_period = 12           # Shorter ADX for faster trend strength detection
    volume_sma_period = 15    # Adjusted volume filter period
    rsi_period = 14           # 🌙 NEW: RSI for momentum confirmation
    risk_per_trade = 0.025    # 🌙 INCREASED: Slightly higher risk per trade (2.5%)
    max_drawdown_per_trade = 0.04  # 🌙 TIGHTER: Reduced max loss per trade
    portfolio_max_drawdown = 0.08   # 🌙 TIGHTER: Reduced portfolio drawdown limit
    
    def init(self):
        close_prices = self.data.Close.astype(float)
        high_prices = self.data.High.astype(float)
        low_prices = self.data.Low.astype(float)
        volume_data = self.data.Volume.astype(float)
        
        # 🌙 MOON DEV: Core trend indicators
        self.ema_fast = self.I(talib.EMA, close_prices, timeperiod=self.ema_fast_period)
        self.ema_slow = self.I(talib.EMA, close_prices, timeperiod=self.ema_slow_period)
        self.atr = self.I(talib.ATR, high_prices, low_prices, close_prices, timeperiod=self.atr_period)
        self.adx = self.I(talib.ADX, high_prices, low_prices, close_prices, timeperiod=self.adx_period)
        self.volume_sma = self.I(talib.SMA, volume_data, timeperiod=self.volume_sma_period)
        
        # 🌙 MOON DEV OPTIMIZATION: Added momentum and volatility filters
        self.rsi = self.I(talib.RSI, close_prices, timeperiod=self.rsi_period)  # Momentum filter
        self.volatility_ratio = self.I(self.calculate_volatility_ratio, high_prices, low_prices)  # Volatility filter
        
        self.trailing_high = None
        self.trailing_low = None
        self.portfolio_peak = 1000000
        
    def calculate_volatility_ratio(self, high, low):
        """🌙 MOON DEV: Calculate volatility ratio to avoid choppy markets"""
        true_range = talib.TRANGE(high, low, self.data.Close.astype(float))
        volatility_sma = talib.SMA(true_range, timeperiod=20)
        current_tr = true_range[-1] if len(true_range) > 0 else 0
        vol_sma = volatility_sma[-1] if len(volatility_sma) > 0 and not np.isnan(volatility_sma[-1]) else current_tr
        return current_tr / vol_sma if vol_sma > 0 else 1.0
        
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
        volatility_ratio = self.volatility_ratio[-1]
        
        current_equity = self.equity
        if current_equity > self.portfolio_peak:
            self.portfolio_peak = current_equity
            
        portfolio_drawdown = (self.portfolio_peak - current_equity) / self.portfolio_peak
        
        if portfolio_drawdown > self.portfolio_max_drawdown:
            print(f"🌙 MOON DEV: Portfolio drawdown {portfolio_drawdown:.2%} exceeds maximum {self.portfolio_max_drawdown:.2%} - skipping trades")
            return
            
        # 🌙 MOON DEV OPTIMIZATION: Dynamic position sizing based on volatility
        volatility_factor = max(0.5, min(2.0, 1.0 / volatility_ratio))  # Reduce size in high volatility
        adjusted_risk = self.risk_per_trade * volatility_factor
        
        if self.position:
            if self.position.is_long:
                self.trailing_high = max(self.trailing_high, self.data.High[-1])
                # 🌙 MOON DEV OPTIMIZATION: Dynamic trailing stop based on ATR and trend strength
                trailing_atr_multiplier = 1.5 if adx_current > 35 else 2.0  # Tighter stops in strong trends
                trailing_stop = self.trailing_high - (trailing_atr_multiplier * atr_current)
                
                exit_conditions = [
                    current_close < ema_fast_current,
                    (ema_fast_previous >= ema_slow_previous and ema_fast_current < ema_slow_current),
                    adx_current < 22,  # 🌙 TIGHTER: Increased ADX exit threshold
                    current_close < trailing_stop,
                    rsi_current > 75   # 🌙 NEW: Exit on overbought RSI
                ]
                
                if any(exit_conditions):
                    print(f"🌙 MOON DEV: Closing LONG position - Close: {current_close:.2f}, EMA15: {ema_fast_current:.2f}, EMA45: {ema_slow_current:.2f}, ADX: {adx_current:.2f}, RSI: {rsi_current:.2f}")
                    self.position.close()
                    self.trailing_high = None
                    
            elif self.position.is_short:
                self.trailing_low = min(self.trailing_low, self.data.Low[-1])
                # 🌙 MOON DEV OPTIMIZATION: Dynamic trailing stop for shorts
                trailing_atr_multiplier = 1.5 if adx_current > 35 else 2.0
                trailing_stop = self.trailing_low + (trailing_atr_multiplier * atr_current)
                
                exit_conditions = [
                    current_close > ema_fast_current,
                    (ema_fast_previous <= ema_slow_previous and ema_fast_current > ema_slow_current),
                    adx_current < 22,  # 🌙 TIGHTER: Increased ADX exit threshold
                    current_close > trailing_stop,
                    rsi_current < 25   # 🌙 NEW: Exit on oversold RSI
                ]
                
                if any(exit_conditions):
                    print(f"🌙 MOON DEV: Closing SHORT position - Close: {current_close:.2f}, EMA15: {ema_fast_current:.2f}, EMA45: {ema_slow_current:.2f}, ADX: {adx_current:.2f}, RSI: {rsi_current:.2f}")
                    self.position.close()
                    self.trailing_low = None
                    
        else:
            risk_amount = current_equity * adjusted_risk
            max_loss_per_share = 2.0 * atr_current  # 🌙 TIGHTER: Reduced ATR multiplier for better R:R
            position_size = int(round(risk_amount / max_loss_per_share))
            
            if position_size <= 0:
                return
                
            # 🌙 MOON DEV OPTIMIZATION: Enhanced entry conditions with multiple filters
            long_conditions = [
                current_close > ema_fast_current,
                current_close > ema_slow_current,
                ema_fast_current > ema_slow_current,
                ema_fast_previous <= ema_slow_previous or ema_fast_current > ema_slow_current * 1.01,  # 🌙 NEW: Strong trend confirmation
                adx_current > 28,  # 🌙 HIGHER: Stronger trend requirement
                adx_current > adx_previous,  # 🌙 NEW: ADX increasing
                current_close > previous_close,
                current_volume > volume_sma_current * 1.1,  # 🌙 HIGHER: Stronger volume requirement
                rsi_current > 45 and rsi_current < 70,  # 🌙 NEW: RSI in favorable zone
                volatility_ratio < 2.0  # 🌙 NEW: Avoid extreme volatility
            ]
            
            short_conditions = [
                current_close < ema_fast_current,
                current_close < ema_slow_current,
                ema_fast_current < ema_slow_current,
                ema_fast_previous >= ema_slow_previous or ema_fast_current < ema_slow_current * 0.99,  # 🌙 NEW: Strong trend confirmation
                adx_current > 28,  # 🌙 HIGHER: Stronger trend requirement
                adx_current > adx_previous,  # 🌙 NEW: ADX increasing
                current_close < previous_close,
                current_volume > volume_sma_current * 1.1,  # 🌙 HIGHER: Stronger volume requirement
                rsi_current < 55 and rsi_current > 30,  # 🌙 NEW: RSI in favorable zone
                volatility_ratio < 2.0  # 🌙 NEW: Avoid extreme volatility
            ]
            
            if sum(long_conditions) >= 9:  # 🌙 OPTIMIZATION: Require 9/10 conditions for higher quality
                entry_price = current_close
                # 🌙 MOON DEV OPTIMIZATION: Dynamic SL/TP based on trend strength
                sl_multiplier = 1.8 if adx_current > 35 else 2.0
                tp_multiplier = 4.0 if adx_current > 35 else 3.5
                
                stop_loss_price = entry_price - (sl_multiplier * atr_current)
                take_profit_price = entry_price + (tp_multiplier * atr_current)
                
                # 🌙 MOON DEV: Critical SL/TP validation
                if stop_loss_price >= entry_price or take_profit_price <= entry_price:
                    print(f"🌙 MOON DEV DEBUG: Long order validation failed - SL: {stop_loss_price:.2f}, Entry: {entry_price:.2f}, TP: {take_profit_price:.2f}")
                    return
                    
                print(f"🌙 MOON DEV: Entering LONG - Close: {current_close:.2f}, EMA15: {ema_fast_current:.2f}, EMA45: {ema_slow_current:.2f}, ADX: {adx_current:.2f}, RSI: {rsi_current:.2f}, VolRatio: {volatility_ratio:.2f}")
                self.buy(size=position_size, sl=stop_loss_price, tp=take_profit_price)
                self.trailing_high = self.data.High[-1]
                
            elif sum(short_conditions) >= 9:  # 🌙 OPTIMIZATION: Require 9/10 conditions for higher quality
                entry_price = current_close
                # 🌙 MOON DEV OPTIMIZATION: Dynamic SL/TP for shorts
                sl_multiplier = 1.8 if adx_current > 35 else 2.0
                tp_multiplier = 4.0 if adx_current > 35 else 3.5
                
                take_profit_price = entry_price - (tp_multiplier * atr_current)
                stop_loss_price = entry_price + (sl_multiplier * atr_current)
                
                # 🌙 MOON DEV: Critical SL/TP validation for shorts
                if take_profit_price >= entry_price or stop_loss_price <= entry_price:
                    print(f"🌙 MOON DEV DEBUG: Short order validation failed - TP: {take_profit_price:.2f}, Entry: {entry_price:.2f}, SL: {stop_loss_price:.2f}")
                    return
                    
                print(f"🌙 MOON DEV: Entering SHORT - Close: {current_close:.2f}, EMA15: {ema_fast_current:.2f}, EMA45: {ema_slow_current:.2f}, ADX: {adx_current:.2f}, RSI: {rsi_current:.2f}, VolRatio: {volatility_ratio:.2f}")
                self.sell(size=position_size, sl=stop_loss_price, tp=take_profit_price)
                self.trailing_low = self.data.Low[-1]

data = load_data()
bt = Backtest(data, AdaptiveTrendFlow, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)