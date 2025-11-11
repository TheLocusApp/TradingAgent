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
    # 🌙 MOON DEV ULTRA-OPTIMIZED PARAMETERS FOR 50% TARGET
    ema_fast_period = 12  # Faster EMA for quicker trend detection
    ema_slow_period = 36  # Optimized trend filter
    atr_period = 8  # More responsive volatility measurement
    adx_period = 10  # Faster trend strength assessment
    volume_sma_period = 12  # Tighter volume momentum
    rsi_period = 10  # More responsive momentum
    macd_fast = 8  # NEW: MACD for momentum confirmation
    macd_slow = 21  # NEW: MACD slow line
    macd_signal = 9  # NEW: MACD signal line
    risk_per_trade = 0.03  # Increased risk for higher returns
    max_drawdown_per_trade = 0.035  # Balanced risk management
    portfolio_max_drawdown = 0.10  # Allow more room for aggressive strategy
    
    def init(self):
        close_prices = self.data.Close.astype(float)
        high_prices = self.data.High.astype(float)
        low_prices = self.data.Low.astype(float)
        volume_data = self.data.Volume.astype(float)
        
        # 🌙 CORE TREND INDICATORS - OPTIMIZED
        self.ema_fast = self.I(talib.EMA, close_prices, timeperiod=self.ema_fast_period)
        self.ema_slow = self.I(talib.EMA, close_prices, timeperiod=self.ema_slow_period)
        self.atr = self.I(talib.ATR, high_prices, low_prices, close_prices, timeperiod=self.atr_period)
        self.adx = self.I(talib.ADX, high_prices, low_prices, close_prices, timeperiod=self.adx_period)
        self.volume_sma = self.I(talib.SMA, volume_data, timeperiod=self.volume_sma_period)
        
        # 🌙 ENHANCED MOMENTUM & VOLATILITY FILTERS
        self.rsi = self.I(talib.RSI, close_prices, timeperiod=self.rsi_period)
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, close_prices, timeperiod=18, nbdevup=1.8, nbdevdn=1.8, matype=0  # Tighter bands
        )
        
        # 🌙 NEW: MACD FOR MOMENTUM CONFIRMATION
        self.macd, self.macd_signal, self.macd_hist = self.I(
            talib.MACD, close_prices, 
            fastperiod=self.macd_fast, 
            slowperiod=self.macd_slow, 
            signalperiod=self.macd_signal
        )
        
        self.trailing_high = None
        self.trailing_low = None
        self.portfolio_peak = 1000000
        
    def next(self):
        if len(self.data) < max(self.ema_slow_period, self.adx_period, self.atr_period, 20, self.macd_slow) + 1:
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
        
        # 🌙 ENHANCED MOMENTUM & VOLATILITY READINGS
        rsi_current = self.rsi[-1]
        rsi_previous = self.rsi[-2]
        bb_upper_current = self.bb_upper[-1]
        bb_lower_current = self.bb_lower[-1]
        
        # 🌙 NEW: MACD MOMENTUM CONFIRMATION
        macd_current = self.macd[-1]
        macd_previous = self.macd[-2]
        macd_signal_current = self.macd_signal[-1]
        macd_hist_current = self.macd_hist[-1]
        
        current_equity = self.equity
        if current_equity > self.portfolio_peak:
            self.portfolio_peak = current_equity
            
        portfolio_drawdown = (self.portfolio_peak - current_equity) / self.portfolio_peak
        
        if portfolio_drawdown > self.portfolio_max_drawdown:
            print(f"🌙 MOON DEV: Portfolio drawdown {portfolio_drawdown:.2%} exceeds maximum {self.portfolio_max_drawdown:.2%} - skipping trades")
            return
            
        # 🌙 DYNAMIC POSITION SIZING WITH VOLATILITY ADJUSTMENT
        volatility_factor = max(0.4, min(2.5, atr_current / current_close * 100))
        adjusted_risk = self.risk_per_trade / volatility_factor
        risk_amount = current_equity * adjusted_risk
        
        if self.position:
            if self.position.is_long:
                self.trailing_high = max(self.trailing_high, self.data.High[-1])
                # 🌙 AGGRESSIVE TRAILING STOP FOR HIGHER RETURNS
                trailing_stop_atr_multiplier = 1.5 if volatility_factor > 1.8 else 2.0
                trailing_stop = self.trailing_high - (trailing_stop_atr_multiplier * atr_current)
                
                exit_conditions = [
                    current_close < ema_fast_current,
                    (ema_fast_previous >= ema_slow_previous and ema_fast_current < ema_slow_current),
                    adx_current < 25,  # Slightly relaxed for more trades
                    current_close < trailing_stop,
                    rsi_current > 78,  # Tighter overbought exit
                    current_close > bb_upper_current * 0.998,  # Exit near upper band
                    macd_current < macd_signal_current and macd_previous >= macd_signal_current  # NEW: MACD crossover down
                ]
                
                if any(exit_conditions):
                    print(f"🌙 MOON DEV: Closing LONG position - Close: {current_close:.2f}, EMA12: {ema_fast_current:.2f}, EMA36: {ema_slow_current:.2f}, ADX: {adx_current:.2f}, RSI: {rsi_current:.2f}")
                    self.position.close()
                    self.trailing_high = None
                    
            elif self.position.is_short:
                self.trailing_low = min(self.trailing_low, self.data.Low[-1])
                # 🌙 AGGRESSIVE TRAILING STOP FOR HIGHER RETURNS
                trailing_stop_atr_multiplier = 1.5 if volatility_factor > 1.8 else 2.0
                trailing_stop = self.trailing_low + (trailing_stop_atr_multiplier * atr_current)
                
                exit_conditions = [
                    current_close > ema_fast_current,
                    (ema_fast_previous <= ema_slow_previous and ema_fast_current > ema_slow_current),
                    adx_current < 25,  # Slightly relaxed for more trades
                    current_close > trailing_stop,
                    rsi_current < 22,  # Tighter oversold exit
                    current_close < bb_lower_current * 1.002,  # Exit near lower band
                    macd_current > macd_signal_current and macd_previous <= macd_signal_current  # NEW: MACD crossover up
                ]
                
                if any(exit_conditions):
                    print(f"🌙 MOON DEV: Closing SHORT position - Close: {current_close:.2f}, EMA12: {ema_fast_current:.2f}, EMA36: {ema_slow_current:.2f}, ADX: {adx_current:.2f}, RSI: {rsi_current:.2f}")
                    self.position.close()
                    self.trailing_low = None
                    
        else:
            max_loss_per_share = 2.0 * atr_current  # Tighter initial stop for better R:R
            position_size = int(round(risk_amount / max_loss_per_share))
            
            if position_size <= 0:
                return
                
            # 🌙 ULTRA-OPTIMIZED LONG CONDITIONS WITH MULTIPLE CONFIRMATION
            long_conditions = [
                current_close > ema_fast_current,
                current_close > ema_slow_current,
                ema_fast_current > ema_slow_current,
                ema_fast_current > ema_fast_previous,  # EMA accelerating up
                adx_current > 26,  # Strong trend requirement
                adx_current > adx_previous,  # ADX increasing
                current_close > previous_close,  # Price momentum up
                current_volume > volume_sma_current * 1.15,  # Strong volume confirmation
                rsi_current > 48 and rsi_current < 72,  # Optimal RSI zone
                rsi_current > rsi_previous,  # RSI momentum up
                current_close < bb_upper_current * 0.99,  # Not at extreme overbought
                macd_current > macd_signal_current,  # NEW: MACD bullish
                macd_current > macd_previous,  # NEW: MACD accelerating
                macd_hist_current > 0  # NEW: Positive MACD histogram
            ]
            
            # 🌙 ULTRA-OPTIMIZED SHORT CONDITIONS WITH MULTIPLE CONFIRMATION
            short_conditions = [
                current_close < ema_fast_current,
                current_close < ema_slow_current,
                ema_fast_current < ema_slow_current,
                ema_fast_current < ema_fast_previous,  # EMA accelerating down
                adx_current > 26,  # Strong trend requirement
                adx_current > adx_previous,  # ADX increasing
                current_close < previous_close,  # Price momentum down
                current_volume > volume_sma_current * 1.15,  # Strong volume confirmation
                rsi_current < 52 and rsi_current > 28,  # Optimal RSI zone
                rsi_current < rsi_previous,  # RSI momentum down
                current_close > bb_lower_current * 1.01,  # Not at extreme oversold
                macd_current < macd_signal_current,  # NEW: MACD bearish
                macd_current < macd_previous,  # NEW: MACD accelerating down
                macd_hist_current < 0  # NEW: Negative MACD histogram
            ]
            
            # 🌙 CONFIDENCE-BASED ENTRY WITH HIGHER STANDARDS
            long_score = sum(long_conditions)
            short_score = sum(short_conditions)
            
            if long_score >= 11:  # Require 11/14 conditions for high-quality setups
                entry_price = current_close
                stop_loss_price = entry_price - (2.0 * atr_current)  # Tighter SL for better R:R
                take_profit_price = entry_price + (5.0 * atr_current)  # Improved profit target
                
                # 🌙 CRITICAL: VALIDATE LONG ORDER PRICING
                if stop_loss_price >= entry_price or take_profit_price <= entry_price:
                    print(f"🌙 MOON DEV DEBUG: Long order validation failed - SL: {stop_loss_price:.2f}, Entry: {entry_price:.2f}, TP: {take_profit_price:.2f}")
                    return
                    
                print(f"🌙 MOON DEV: Entering LONG - Close: {current_close:.2f}, EMA12: {ema_fast_current:.2f}, EMA36: {ema_slow_current:.2f}, ADX: {adx_current:.2f}, RSI: {rsi_current:.2f}, MACD: {macd_current:.4f}, Score: {long_score}/14")
                self.buy(size=position_size, sl=stop_loss_price, tp=take_profit_price)
                self.trailing_high = self.data.High[-1]
                
            elif short_score >= 11:  # Require 11/14 conditions for high-quality setups
                entry_price = current_close
                take_profit_price = entry_price - (5.0 * atr_current)  # SUBTRACT for TP (below entry)
                stop_loss_price = entry_price + (2.0 * atr_current)    # ADD for SL (above entry)
                
                # 🌙 CRITICAL: VALIDATE SHORT ORDER PRICING
                if take_profit_price >= entry_price or stop_loss_price <= entry_price:
                    print(f"🌙 MOON DEV DEBUG: Short order validation failed - TP: {take_profit_price:.2f}, Entry: {entry_price:.2f}, SL: {stop_loss_price:.2f}")
                    return
                    
                print(f"🌙 MOON DEV: Entering SHORT - Close: {current_close:.2f}, EMA12: {ema_fast_current:.2f}, EMA36: {ema_slow_current:.2f}, ADX: {adx_current:.2f}, RSI: {rsi_current:.2f}, MACD: {macd_current:.4f}, Score: {short_score}/14")
                self.sell(size=position_size, sl=stop_loss_price, tp=take_profit_price)
                self.trailing_low = self.data.Low[-1]

data = load_data()
bt = Backtest(data, AdaptiveTrendFlow, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)