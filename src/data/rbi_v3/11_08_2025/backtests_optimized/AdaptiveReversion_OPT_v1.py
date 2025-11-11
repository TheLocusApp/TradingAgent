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
    bb_period = 18  # Tighter period for more responsive bands
    bb_std = 1.8    # Reduced deviation for more frequent signals
    rsi_period = 12 # Faster RSI for quicker momentum detection
    atr_period = 10 # Faster ATR for dynamic position sizing
    vol_period = 15 # Faster volume average
    sma_trend = 40  # Faster trend detection
    ema_fast = 8    # Added fast EMA for trend confirmation
    ema_slow = 21   # Added slow EMA for trend filter
    
    # 🌙 ENHANCED RISK MANAGEMENT
    risk_per_trade = 0.015  # Increased risk for higher returns
    max_consecutive_losses = 2  # Tighter loss control
    max_daily_trades = 3    # Prevent overtrading
    trailing_stop_atr = 1.5 # Added trailing stop
    
    def init(self):
        close = self.data.Close.astype(float)
        high = self.data.High.astype(float)
        low = self.data.Low.astype(float)
        volume = self.data.Volume.astype(float)
        
        # 🌙 OPTIMIZED INDICATORS WITH MULTIPLE TIMEFRAME CONFIRMATION
        bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)
        
        self.bb_upper = self.I(lambda x: bb_upper, self.data.Close)
        self.bb_middle = self.I(lambda x: bb_middle, self.data.Close)
        self.bb_lower = self.I(lambda x: bb_lower, self.data.Close)
        
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        self.vol_sma = self.I(talib.SMA, volume, timeperiod=self.vol_period)
        self.sma_50 = self.I(talib.SMA, close, timeperiod=self.sma_trend)
        
        # 🌙 ADDED TREND CONFIRMATION INDICATORS
        self.ema_fast = self.I(talib.EMA, close, timeperiod=self.ema_fast)
        self.ema_slow = self.I(talib.EMA, close, timeperiod=self.ema_slow)
        
        # 🌙 ADDED MOMENTUM FILTER
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, close)
        
        self.consecutive_losses = 0
        self.daily_trades = 0
        self.last_trade_day = None
        self.long_signal = False
        self.short_signal = False
        self.touched_lower_band = False
        self.touched_upper_band = False
        
    def next(self):
        if len(self.data) < max(self.bb_period, self.rsi_period, self.atr_period, self.vol_period, self.sma_trend, self.ema_slow) + 1:
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
        current_ema_fast = self.ema_fast[-1]
        current_ema_slow = self.ema_slow[-1]
        current_macd = self.macd[-1] if self.macd[-1] is not None else 0
        current_macd_signal = self.macd_signal[-1] if self.macd_signal[-1] is not None else 0
        
        hour = self.data.index[-1].hour
        current_day = self.data.index[-1].date()
        
        # 🌙 RESET DAILY TRADE COUNTER
        if self.last_trade_day != current_day:
            self.daily_trades = 0
            self.last_trade_day = current_day
            
        # 🌙 OPTIMIZED TRADING HOURS FILTER
        if hour < 9 or hour >= 16:  # Extended trading hours slightly
            return
            
        if not np.isfinite([current_close, current_rsi, current_atr, current_bb_upper, current_bb_lower, current_bb_middle, current_vol_sma, current_ema_fast, current_ema_slow]).all():
            return
            
        if self.consecutive_losses >= self.max_consecutive_losses:
            print(f"🌙 MOON DEV PAUSE: Max consecutive losses reached ({self.consecutive_losses})")
            return
            
        if self.daily_trades >= self.max_daily_trades:
            return
            
        # 🌙 IMPROVED BAND TOUCH DETECTION WITH MOMENTUM FILTERS
        if current_low <= current_bb_lower and current_rsi < 28 and current_volume > current_vol_sma * 1.2:
            # 🌙 ADDED TREND CONFIRMATION FOR LONG ENTRIES
            if current_ema_fast > current_ema_slow or current_macd > current_macd_signal:
                self.touched_lower_band = True
                print(f"🌙 MOON DEV ALERT: Lower BB touched! RSI: {current_rsi:.2f}, Volume: {current_volume:.0f} > {current_vol_sma:.0f}")
            
        if current_high >= current_bb_upper and current_rsi > 72 and current_volume > current_vol_sma * 1.2:
            # 🌙 ADDED TREND CONFIRMATION FOR SHORT ENTRIES
            if current_ema_fast < current_ema_slow or current_macd < current_macd_signal:
                self.touched_upper_band = True
                print(f"🌙 MOON DEV ALERT: Upper BB touched! RSI: {current_rsi:.2f}, Volume: {current_volume:.0f} > {current_vol_sma:.0f}")
            
        if not self.position:
            # 🌙 ENHANCED LONG ENTRY WITH MULTIPLE CONFIRMATIONS
            if self.touched_lower_band and current_close > current_bb_lower and current_rsi > 32:
                # 🌙 VOLATILITY-BASED POSITION SIZING
                volatility_factor = max(0.5, min(2.0, current_atr / current_close * 100))
                adjusted_risk = self.risk_per_trade * volatility_factor
                risk_amount = self.equity * adjusted_risk
                stop_loss_price = current_close - (1.8 * current_atr)  # Tighter stop
                
                # 🌙 SCALED TAKE PROFIT LEVELS
                position_size = risk_amount / (current_close - stop_loss_price)
                position_size = int(round(position_size))
                
                if position_size > 0:
                    # 🌙 IMPROVED TP STRATEGY WITH MULTIPLE TARGETS
                    target1 = current_bb_middle
                    target2 = current_close + (2.0 * current_atr)  # Increased reward
                    take_profit = min(target1, target2)
                    
                    self.buy(size=position_size, sl=stop_loss_price, tp=take_profit)
                    self.daily_trades += 1
                    print(f"🚀 MOON DEV LONG ENTRY: Size: {position_size}, Entry: {current_close:.2f}, SL: {stop_loss_price:.2f}, TP: {take_profit:.2f}, VolFactor: {volatility_factor:.2f}")
                    self.touched_lower_band = False
                    
            # 🌙 ENHANCED SHORT ENTRY WITH MULTIPLE CONFIRMATIONS
            elif self.touched_upper_band and current_close < current_bb_upper and current_rsi < 68:
                # 🌙 VOLATILITY-BASED POSITION SIZING
                volatility_factor = max(0.5, min(2.0, current_atr / current_close * 100))
                adjusted_risk = self.risk_per_trade * volatility_factor
                risk_amount = self.equity * adjusted_risk
                stop_loss_price = current_close + (1.8 * current_atr)  # Tighter stop
                
                position_size = risk_amount / (stop_loss_price - current_close)
                position_size = int(round(position_size))
                
                if position_size > 0:
                    # 🌙 IMPROVED TP STRATEGY WITH MULTIPLE TARGETS
                    target1 = current_bb_middle
                    target2 = current_close - (2.0 * current_atr)  # Increased reward
                    take_profit = max(target1, target2)
                    
                    if take_profit < current_close < stop_loss_price:
                        self.sell(size=position_size, sl=stop_loss_price, tp=take_profit)
                        self.daily_trades += 1
                        print(f"📉 MOON DEV SHORT ENTRY: Size: {position_size}, Entry: {current_close:.2f}, SL: {stop_loss_price:.2f}, TP: {take_profit:.2f}, VolFactor: {volatility_factor:.2f}")
                        self.touched_upper_band = False
                    else:
                        print(f"🌙 MOON DEV DEBUG: Short order validation failed - TP: {take_profit:.2f}, Entry: {current_close:.2f}, SL: {stop_loss_price:.2f}")
                    
        else:
            # 🌙 IMPROVED EXIT STRATEGY WITH TRAILING STOPS
            if self.position.is_long:
                # 🌙 DYNAMIC TRAILING STOP FOR LONGS
                trailing_stop = current_close - (self.trailing_stop_atr * current_atr)
                if trailing_stop > self.position.sl:
                    self.position.sl = trailing_stop
                    
                # 🌙 IMPROVED EXIT CONDITIONS
                if current_rsi > 75 or (current_close > current_bb_upper and current_rsi > 65):
                    self.position.close()
                    print(f"✨ MOON DEV LONG EXIT: RSI {current_rsi:.2f} or Upper BB reached")
                    
            elif self.position.is_short:
                # 🌙 DYNAMIC TRAILING STOP FOR SHORTS
                trailing_stop = current_close + (self.trailing_stop_atr * current_atr)
                if trailing_stop < self.position.sl:
                    self.position.sl = trailing_stop
                    
                # 🌙 IMPROVED EXIT CONDITIONS
                if current_rsi < 25 or (current_close < current_bb_lower and current_rsi < 35):
                    self.position.close()
                    print(f"✨ MOON DEV SHORT EXIT: RSI {current_rsi:.2f} or Lower BB reached")
                
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