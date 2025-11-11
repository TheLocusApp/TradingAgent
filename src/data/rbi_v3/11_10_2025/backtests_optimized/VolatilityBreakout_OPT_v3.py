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
    rsi_period = 14
    volume_multiplier = 1.5  # 🌙 INCREASED: Tighter volume filter for stronger signals
    risk_per_trade = 0.03    # 🌙 INCREASED: Slightly higher risk for better returns
    atr_multiplier_sl = 1.5  # 🌙 ADDED: ATR-based stop loss for better risk management
    atr_multiplier_tp = 2.5  # 🌙 ADDED: ATR-based take profit for better reward
    min_bb_width = 0.02      # 🌙 ADDED: Filter out low volatility periods
    
    def init(self):
        close = self.data.Close.astype(float)
        high = self.data.High.astype(float)
        low = self.data.Low.astype(float)
        volume = self.data.Volume.astype(float)
        
        # 🌙 IMPROVED: Added multiple timeframe indicators
        bb_bands = self.I(talib.BBANDS, close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)
        self.bb_upper = bb_bands[0]
        self.bb_middle = bb_bands[1]
        self.bb_lower = bb_bands[2]
        
        self.volume_sma = self.I(talib.SMA, volume, timeperiod=20)
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=14)
        
        # 🌙 ADDED: Trend filter using EMA
        self.ema_fast = self.I(talib.EMA, close, timeperiod=20)
        self.ema_slow = self.I(talib.EMA, close, timeperiod=50)
        
        self.bb_width = self.I(lambda: (self.bb_upper - self.bb_lower) / self.bb_middle)
        self.breakout_signal = 0
        self.position_count = 0

    def next(self):
        if len(self.data) < 51:  # 🌙 INCREASED: Wait for more data for better indicators
            return
            
        current_close = self.data.Close[-1]
        current_volume = self.data.Volume[-1]
        bb_upper = self.bb_upper[-1]
        bb_lower = self.bb_lower[-1]
        bb_middle = self.bb_middle[-1]
        volume_sma = self.volume_sma[-1]
        rsi = self.rsi[-1]
        atr = self.atr[-1]
        bb_width = self.bb_width[-1]
        ema_fast = self.ema_fast[-1]
        ema_slow = self.ema_slow[-1]
        
        avg_bb_width = np.mean(self.bb_width[-20:-1]) if len(self.bb_width) > 20 else bb_width
        
        # 🌙 IMPROVED: Stronger squeeze condition with minimum width filter
        is_squeeze = bb_width < avg_bb_width * 0.6 and bb_width > self.min_bb_width
        volume_confirmed = current_volume > volume_sma * self.volume_multiplier
        
        # 🌙 ADDED: Trend filter - only trade with trend
        trend_up = ema_fast > ema_slow
        trend_down = ema_fast < ema_slow
        
        if not self.position:
            if is_squeeze and volume_confirmed:
                # 🌙 IMPROVED: Added trend alignment and tighter RSI filters
                if current_close > bb_upper and rsi < 65 and trend_up:  # 🌙 TIGHTER: RSI 65 instead of 70
                    self.breakout_signal = 1
                    print(f"🌙 MOON DEV: LONG BREAKOUT SIGNAL - Close: {current_close:.2f}, BB Upper: {bb_upper:.2f}, Volume: {current_volume:.0f}")
                    
                elif current_close < bb_lower and rsi > 35 and trend_down:  # 🌙 TIGHTER: RSI 35 instead of 30
                    self.breakout_signal = -1
                    print(f"🌙 MOON DEV: SHORT BREAKOUT SIGNAL - Close: {current_close:.2f}, BB Lower: {bb_lower:.2f}, Volume: {current_volume:.0f}")
            
            elif self.breakout_signal != 0:
                entry_price = self.data.Open[-1]
                risk_amount = self.equity * self.risk_per_trade
                
                if self.breakout_signal == 1:
                    # 🌙 IMPROVED: ATR-based stop loss instead of BB lower
                    stop_loss_price = entry_price - (self.atr_multiplier_sl * atr)
                    take_profit_price = entry_price + (self.atr_multiplier_tp * atr)
                    
                    # 🌙 VALIDATION: Critical SL/TP ordering check
                    if stop_loss_price >= entry_price or take_profit_price <= entry_price:
                        print(f"🌙 MOON DEV: Long order validation failed - SL: {stop_loss_price:.2f}, Entry: {entry_price:.2f}, TP: {take_profit_price:.2f}")
                        self.breakout_signal = 0
                        return
                    
                    risk_per_share = entry_price - stop_loss_price
                    if risk_per_share > 0:
                        position_size = int(round(risk_amount / risk_per_share))
                        max_position_size = int(self.equity * 0.15 / entry_price)  # 🌙 INCREASED: Slightly higher position limit
                        position_size = min(position_size, max_position_size)
                        
                        if position_size > 0:
                            self.buy(size=position_size, sl=stop_loss_price, tp=take_profit_price)
                            print(f"🚀 MOON DEV: ENTERED LONG - Size: {position_size}, Entry: {entry_price:.2f}, SL: {stop_loss_price:.2f}, TP: {take_profit_price:.2f}, R:R: {self.atr_multiplier_tp/self.atr_multiplier_sl:.2f}")
                            self.breakout_signal = 0
                
                elif self.breakout_signal == -1:
                    # 🌙 IMPROVED: ATR-based stop loss instead of BB upper
                    take_profit_price = entry_price - (self.atr_multiplier_tp * atr)  # 🌙 CORRECT: TP BELOW entry for shorts
                    stop_loss_price = entry_price + (self.atr_multiplier_sl * atr)    # 🌙 CORRECT: SL ABOVE entry for shorts
                    
                    # 🌙 VALIDATION: Critical SL/TP ordering check
                    if take_profit_price >= entry_price or stop_loss_price <= entry_price:
                        print(f"🌙 MOON DEV: Short order validation failed - TP: {take_profit_price:.2f}, Entry: {entry_price:.2f}, SL: {stop_loss_price:.2f}")
                        self.breakout_signal = 0
                        return
                    
                    risk_per_share = stop_loss_price - entry_price
                    if risk_per_share > 0:
                        position_size = int(round(risk_amount / risk_per_share))
                        max_position_size = int(self.equity * 0.15 / entry_price)  # 🌙 INCREASED: Slightly higher position limit
                        position_size = min(position_size, max_position_size)
                        
                        if position_size > 0:
                            self.sell(size=position_size, sl=stop_loss_price, tp=take_profit_price)
                            print(f"🌙 MOON DEV: ENTERED SHORT - Size: {position_size}, Entry: {entry_price:.2f}, SL: {stop_loss_price:.2f}, TP: {take_profit_price:.2f}, R:R: {self.atr_multiplier_tp/self.atr_multiplier_sl:.2f}")
                            self.breakout_signal = 0
        
        else:
            # 🌙 IMPROVED: Let backtesting.py handle exits automatically via SL/TP
            if self.position.is_long:
                if current_close <= self.position.sl or current_close >= self.position.tp:
                    print(f"✨ MOON DEV: LONG EXIT - Price: {current_close:.2f}, P&L: {self.position.pl:.2f}")
            
            elif self.position.is_short:
                if current_close >= self.position.sl or current_close <= self.position.tp:
                    print(f"✨ MOON DEV: SHORT EXIT - Price: {current_close:.2f}, P&L: {self.position.pl:.2f}")

data = load_data()
bt = Backtest(data, VolatilityBreakout, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)