import pandas as pd
import yfinance as yf
import talib
import numpy as np
from backtesting import Backtest, Strategy

def load_data():
    ticker = yf.Ticker("SPY")
    data = ticker.history(period="2y", interval="1h")
    
    data = data.reset_index()
    data.columns = data.columns.str.strip().str.lower()
    
    # Clean and rename columns properly
    data = data.rename(columns={
        'date': 'datetime',
        'open': 'Open',
        'high': 'High', 
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    
    # Drop any unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    
    print(f"🌙 MOON DEV DATA LOADED: {len(data)} rows, columns: {list(data.columns)}")
    return data

class AdaptiveReversion(Strategy):
    # 🌙 OPTIMIZED PARAMETERS FOR HIGHER RETURNS
    bb_period = 18  # Tighter bands for more responsive signals
    bb_std = 1.8    # Reduced deviation for earlier entries
    rsi_period = 12 # More responsive RSI
    atr_period = 10 # Faster ATR for dynamic sizing
    vol_period = 15 # Quicker volume analysis
    sma_trend = 34  # Better trend filter
    risk_per_trade = 0.015  # Increased risk for higher returns
    max_consecutive_losses = 2  # Tighter loss control
    
    # 🌙 NEW OPTIMIZATION PARAMETERS
    rsi_oversold = 28  # More aggressive oversold level
    rsi_overbought = 72 # More aggressive overbought level
    atr_multiplier_sl = 1.5  # Tighter stops for better R:R
    atr_multiplier_tp = 2.0  # Better profit targets
    min_volume_ratio = 1.3   # Stronger volume confirmation
    
    def init(self):
        close = self.data.Close.astype(float)
        high = self.data.High.astype(float)
        low = self.data.Low.astype(float)
        volume = self.data.Volume.astype(float)
        
        # 🌙 IMPROVED: Calculate all Bollinger Bands components at once
        bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)
        
        self.bb_upper = self.I(lambda x: bb_upper, self.data.Close)
        self.bb_middle = self.I(lambda x: bb_middle, self.data.Close)
        self.bb_lower = self.I(lambda x: bb_lower, self.data.Close)
        
        # 🌙 ADDED: Momentum and trend confirmation indicators
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        self.vol_sma = self.I(talib.SMA, volume, timeperiod=self.vol_period)
        self.sma_50 = self.I(talib.SMA, close, timeperiod=self.sma_trend)
        
        # 🌙 ADDED: Complementary indicators for better signal quality
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, close, fastperiod=12, slowperiod=26, signalperiod=9)
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=14)
        
        self.consecutive_losses = 0
        self.long_signal = False
        self.short_signal = False
        self.touched_lower_band = False
        self.touched_upper_band = False
        
    def next(self):
        if len(self.data) < max(self.bb_period, self.rsi_period, self.atr_period, self.vol_period, self.sma_trend) + 1:
            return
            
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_volume = self.data.Volume[-1]
        current_rsi = self.rsi[-1]
        current_atr = self.atr[-1]
        current_bb_upper = self.bb_upper[-1]
        current_bb_lower = self.bb_lower[-1]
        current_bb_middle = self.bb_middle[-1]
        current_vol_sma = self.vol_sma[-1]
        current_macd = self.macd[-1] if self.macd[-1] is not None else 0
        current_macd_signal = self.macd_signal[-1] if self.macd_signal[-1] is not None else 0
        current_adx = self.adx[-1] if self.adx[-1] is not None else 0
        
        hour = self.data.index[-1].hour
        
        # 🌙 IMPROVED: Focus on high-probability trading hours
        if hour < 9 or hour >= 16:  # Extended to capture more opportunities
            return
            
        if not np.isfinite([current_close, current_rsi, current_atr, current_bb_upper, current_bb_lower, current_bb_middle, current_vol_sma]).all():
            return
            
        if self.consecutive_losses >= self.max_consecutive_losses:
            print(f"🌙 MOON DEV PAUSE: Max consecutive losses reached ({self.consecutive_losses})")
            return
        
        # 🌙 ADDED: Market regime filter - only trade in trending markets
        if current_adx < 20:  # Avoid choppy markets
            return
            
        volume_ratio = current_volume / current_vol_sma
        
        # 🌙 IMPROVED: More aggressive band touch detection with volume confirmation
        if current_low <= current_bb_lower and current_rsi < self.rsi_oversold and volume_ratio > self.min_volume_ratio:
            self.touched_lower_band = True
            print(f"🌙 MOON DEV ALERT: Lower BB touched! RSI: {current_rsi:.2f}, Volume Ratio: {volume_ratio:.2f}")
            
        if current_high >= current_bb_upper and current_rsi > self.rsi_overbought and volume_ratio > self.min_volume_ratio:
            self.touched_upper_band = True
            print(f"🌙 MOON DEV ALERT: Upper BB touched! RSI: {current_rsi:.2f}, Volume Ratio: {volume_ratio:.2f}")
            
        if not self.position:
            # 🌙 IMPROVED: Long entry with momentum confirmation
            if (self.touched_lower_band and 
                current_close > current_bb_lower and 
                current_rsi > self.rsi_oversold and
                current_macd > current_macd_signal):  # MACD momentum confirmation
                
                # 🌙 IMPROVED: Dynamic position sizing based on ATR volatility
                risk_amount = self.equity * self.risk_per_trade
                stop_loss_price = current_close - (self.atr_multiplier_sl * current_atr)
                position_size = risk_amount / (current_close - stop_loss_price)
                position_size = int(round(position_size))
                
                if position_size > 0:
                    # 🌙 IMPROVED: Better profit targeting with ATR scaling
                    target1 = current_bb_middle
                    target2 = current_close + (self.atr_multiplier_tp * current_atr)
                    take_profit = min(target1, target2)
                    
                    self.buy(size=position_size, sl=stop_loss_price, tp=take_profit)
                    print(f"🚀 MOON DEV LONG ENTRY: Size: {position_size}, Entry: {current_close:.2f}, SL: {stop_loss_price:.2f}, TP: {take_profit:.2f}, R:R: {(take_profit-current_close)/(current_close-stop_loss_price):.2f}")
                    self.touched_lower_band = False
                    
            # 🌙 IMPROVED: Short entry with momentum confirmation  
            elif (self.touched_upper_band and 
                  current_close < current_bb_upper and 
                  current_rsi < self.rsi_overbought and
                  current_macd < current_macd_signal):  # MACD momentum confirmation
                
                risk_amount = self.equity * self.risk_per_trade
                stop_loss_price = current_close + (self.atr_multiplier_sl * current_atr)
                position_size = risk_amount / (stop_loss_price - current_close)
                position_size = int(round(position_size))
                
                if position_size > 0:
                    target1 = current_bb_middle
                    target2 = current_close - (self.atr_multiplier_tp * current_atr)
                    take_profit = max(target1, target2)
                    
                    # FIXED: Ensure proper order for short positions - TP < Entry < SL
                    if take_profit < current_close < stop_loss_price:
                        self.sell(size=position_size, sl=stop_loss_price, tp=take_profit)
                        print(f"📉 MOON DEV SHORT ENTRY: Size: {position_size}, Entry: {current_close:.2f}, SL: {stop_loss_price:.2f}, TP: {take_profit:.2f}, R:R: {(current_close-take_profit)/(stop_loss_price-current_close):.2f}")
                        self.touched_upper_band = False
                    else:
                        print(f"🌙 MOON DEV DEBUG: Short order validation failed - TP: {take_profit:.2f}, Entry: {current_close:.2f}, SL: {stop_loss_price:.2f}")
                    
        else:
            # 🌙 IMPROVED: Dynamic exit conditions with trend following
            if self.position.is_long:
                # Take partial profits at first target, trail rest
                if current_close >= self.position.tp and not hasattr(self.position, 'partial_taken'):
                    # Scale out 50% at first target
                    size_to_close = int(self.position.size * 0.5)
                    if size_to_close > 0:
                        self.position.close(size_to_close)
                        print(f"✨ MOON DEV PARTIAL PROFIT: Closed {size_to_close} shares at {current_close:.2f}")
                        self.position.partial_taken = True
                        # Trail remaining position
                        new_sl = current_close - (current_atr * 1.0)
                        if new_sl > self.position.sl:
                            self.position.sl = new_sl
                            print(f"🌙 MOON DEV TRAILING SL: New SL at {new_sl:.2f}")
                
                # Emergency exit if trend reverses
                elif current_rsi > 75 or current_macd < current_macd_signal:
                    self.position.close()
                    print(f"✨ MOON DEV LONG EXIT: RSI: {current_rsi:.2f}, MACD turned bearish")
                    
            elif self.position.is_short:
                # Take partial profits at first target, trail rest
                if current_close <= self.position.tp and not hasattr(self.position, 'partial_taken'):
                    # Scale out 50% at first target
                    size_to_close = int(self.position.size * 0.5)
                    if size_to_close > 0:
                        self.position.close(size_to_close)
                        print(f"✨ MOON DEV PARTIAL PROFIT: Closed {size_to_close} shares at {current_close:.2f}")
                        self.position.partial_taken = True
                        # Trail remaining position
                        new_sl = current_close + (current_atr * 1.0)
                        if new_sl < self.position.sl:
                            self.position.sl = new_sl
                            print(f"🌙 MOON DEV TRAILING SL: New SL at {new_sl:.2f}")
                
                # Emergency exit if trend reverses
                elif current_rsi < 25 or current_macd > current_macd_signal:
                    self.position.close()
                    print(f"✨ MOON DEV SHORT EXIT: RSI: {current_rsi:.2f}, MACD turned bullish")
                
    def notify_trade(self, trade):
        if trade.is_closed:
            if trade.pnl < 0:
                self.consecutive_losses += 1
                print(f"🔴 MOON DEV LOSS: -${abs(trade.pnl):.2f}, Consecutive losses: {self.consecutive_losses}")
            else:
                self.consecutive_losses = 0
                print(f"🟢 MOON DEV WIN: +${trade.pnl:.2f}, Reset consecutive losses")

data = load_data()
bt = Backtest(data, AdaptiveReversion, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)