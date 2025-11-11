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
    bb_period = 20
    bb_std = 2
    rsi_period = 14
    atr_period = 14
    vol_period = 20
    sma_trend = 50
    risk_per_trade = 0.01
    max_consecutive_losses = 3
    
    def init(self):
        close = self.data.Close.astype(float)
        high = self.data.High.astype(float)
        low = self.data.Low.astype(float)
        volume = self.data.Volume.astype(float)
        
        # Calculate all Bollinger Bands components at once
        bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)
        
        self.bb_upper = self.I(lambda x: bb_upper, self.data.Close)
        self.bb_middle = self.I(lambda x: bb_middle, self.data.Close)
        self.bb_lower = self.I(lambda x: bb_lower, self.data.Close)
        
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        self.vol_sma = self.I(talib.SMA, volume, timeperiod=self.vol_period)
        self.sma_50 = self.I(talib.SMA, close, timeperiod=self.sma_trend)
        
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
        
        hour = self.data.index[-1].hour
        
        if hour < 9 or hour >= 15:
            return
            
        if not np.isfinite([current_close, current_rsi, current_atr, current_bb_upper, current_bb_lower, current_bb_middle, current_vol_sma]).all():
            return
            
        if self.consecutive_losses >= self.max_consecutive_losses:
            print(f"🌙 MOON DEV PAUSE: Max consecutive losses reached ({self.consecutive_losses})")
            return
            
        if current_low <= current_bb_lower and current_rsi < 30 and current_volume > current_vol_sma:
            self.touched_lower_band = True
            print(f"🌙 MOON DEV ALERT: Lower BB touched! RSI: {current_rsi:.2f}, Volume: {current_volume:.0f} > {current_vol_sma:.0f}")
            
        if current_high >= current_bb_upper and current_rsi > 70 and current_volume > current_vol_sma:
            self.touched_upper_band = True
            print(f"🌙 MOON DEV ALERT: Upper BB touched! RSI: {current_rsi:.2f}, Volume: {current_volume:.0f} > {current_vol_sma:.0f}")
            
        if not self.position:
            if self.touched_lower_band and current_close > current_bb_lower and current_rsi > 30:
                risk_amount = self.equity * self.risk_per_trade
                stop_loss_price = current_close - (2 * current_atr)
                position_size = risk_amount / (current_close - stop_loss_price)
                position_size = int(round(position_size))
                
                if position_size > 0:
                    target1 = current_bb_middle
                    target2 = current_close + (1.5 * current_atr)
                    take_profit = min(target1, target2)
                    
                    self.buy(size=position_size, sl=stop_loss_price, tp=take_profit)
                    print(f"🚀 MOON DEV LONG ENTRY: Size: {position_size}, Entry: {current_close:.2f}, SL: {stop_loss_price:.2f}, TP: {take_profit:.2f}")
                    self.touched_lower_band = False
                    
            elif self.touched_upper_band and current_close < current_bb_upper and current_rsi < 70:
                risk_amount = self.equity * self.risk_per_trade
                stop_loss_price = current_close + (2 * current_atr)
                position_size = risk_amount / (stop_loss_price - current_close)
                position_size = int(round(position_size))
                
                if position_size > 0:
                    target1 = current_bb_middle
                    target2 = current_close - (1.5 * current_atr)
                    take_profit = max(target1, target2)
                    
                    # FIXED: Ensure proper order for short positions - TP < Entry < SL
                    if take_profit < current_close < stop_loss_price:
                        self.sell(size=position_size, sl=stop_loss_price, tp=take_profit)
                        print(f"📉 MOON DEV SHORT ENTRY: Size: {position_size}, Entry: {current_close:.2f}, SL: {stop_loss_price:.2f}, TP: {take_profit:.2f}")
                        self.touched_upper_band = False
                    else:
                        print(f"🌙 MOON DEV DEBUG: Short order validation failed - TP: {take_profit:.2f}, Entry: {current_close:.2f}, SL: {stop_loss_price:.2f}")
                    
        else:
            if self.position.is_long and current_rsi > 70:
                self.position.close()
                print(f"✨ MOON DEV LONG EXIT: RSI overbought at {current_rsi:.2f}")
                
            elif self.position.is_short and current_rsi < 30:
                self.position.close()
                print(f"✨ MOON DEV SHORT EXIT: RSI oversold at {current_rsi:.2f}")
                
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