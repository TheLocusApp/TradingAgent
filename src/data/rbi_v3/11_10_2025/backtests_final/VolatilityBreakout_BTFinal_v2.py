import yfinance as yf
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import talib

def load_data():
    ticker = yf.Ticker("SPY")
    data = ticker.history(period="2y", interval="1h")
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()], errors='ignore')
    data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
    data.index = pd.to_datetime(data.index)
    required = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in data.columns for col in required):
        raise ValueError(f"Missing required columns. Got: {list(data.columns)}")
    return data

class VolatilityBreakout(Strategy):
    bb_period = 20
    bb_std = 2
    rsi_period = 14
    atr_period = 14
    squeeze_threshold = 0.02
    risk_per_trade = 0.02
    
    def init(self):
        close = self.data.Close.astype(float)
        high = self.data.High.astype(float)
        low = self.data.Low.astype(float)
        volume = self.data.Volume.astype(float)
        
        bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)
        self.bb_upper = self.I(lambda: bb_upper)
        self.bb_middle = self.I(lambda: bb_middle)
        self.bb_lower = self.I(lambda: bb_lower)
        
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        self.volume_sma = self.I(talib.SMA, volume, timeperiod=20)
        
        self.squeeze_condition = self.I(self.calculate_squeeze)
        self.trailing_high = 0
        self.trailing_low = float('inf')
        
    def calculate_squeeze(self):
        if len(self.data.Close) < 1:
            return np.array([False])
        bb_width = (self.bb_upper - self.bb_lower) / self.data.Close
        squeeze = bb_width < self.squeeze_threshold
        return squeeze
        
    def next(self):
        if len(self.data) < 21:
            return
            
        current_close = float(self.data.Close[-1])
        current_high = float(self.data.High[-1])
        current_low = float(self.data.Low[-1])
        current_volume = float(self.data.Volume[-1])
        current_time = self.data.index[-1]
        
        if hasattr(current_time, 'hour') and current_time.hour >= 15:
            return
            
        if not self.position:
            self.trailing_high = current_high
            self.trailing_low = current_low
            
            squeeze_cond = bool(self.squeeze_condition[-1]) if len(self.squeeze_condition) > 0 else False
            bb_upper_val = float(self.bb_upper[-1]) if len(self.bb_upper) > 0 else 0
            bb_lower_val = float(self.bb_lower[-1]) if len(self.bb_lower) > 0 else 0
            volume_sma_val = float(self.volume_sma[-1]) if len(self.volume_sma) > 0 else 0
            rsi_val = float(self.rsi[-1]) if len(self.rsi) > 0 else 50
            atr_val = float(self.atr[-1]) if len(self.atr) > 0 else 0.01
            
            if squeeze_cond:
                if (current_close > bb_upper_val and 
                    current_volume > volume_sma_val and 
                    50 < rsi_val < 80):
                    
                    entry_price = current_close
                    atr_val = float(self.atr[-1]) if len(self.atr) > 0 else 0.01
                    
                    # 🌙 MOON DEV DEBUG: Calculate SL/TP correctly for LONG
                    stop_loss_price = entry_price - (2.0 * atr_val)     # SL BELOW entry
                    take_profit_price = entry_price + (3.0 * atr_val)   # TP ABOVE entry
                    
                    # Validate: SL < Entry < TP
                    if stop_loss_price >= entry_price or take_profit_price <= entry_price:
                        print(f"🌙 MOON DEV DEBUG: Long order validation failed - SL: {stop_loss_price:.2f}, Entry: {entry_price:.2f}, TP: {take_profit_price:.2f}")
                        return
                    
                    risk_amount = entry_price - stop_loss_price
                    
                    if risk_amount <= 0:
                        print(f"🌙 MOON DEV DEBUG: Invalid risk calculation for long - Entry: {entry_price:.2f}, SL: {stop_loss_price:.2f}")
                        return
                    
                    position_size = int(round((self.equity * self.risk_per_trade) / risk_amount))
                    
                    if position_size > 0:
                        print(f"🌙 MOON DEV LONG ENTRY: Price: {entry_price:.2f}, Size: {position_size}, RSI: {rsi_val:.1f}, SL: {stop_loss_price:.2f}, TP: {take_profit_price:.2f}")
                        self.buy(size=position_size, sl=stop_loss_price, tp=take_profit_price)
                        self.trailing_high = entry_price
                    else:
                        print(f"🌙 MOON DEV DEBUG: Invalid position size for long: {position_size}")
                
                elif (current_close < bb_lower_val and 
                      current_volume > volume_sma_val and 
                      20 < rsi_val < 50):
                    
                    entry_price = current_close
                    atr_val = float(self.atr[-1]) if len(self.atr) > 0 else 0.01
                    
                    # 🌙 MOON DEV DEBUG: Calculate SL/TP correctly for SHORT
                    take_profit_price = entry_price - (3.0 * atr_val)   # TP BELOW entry
                    stop_loss_price = entry_price + (2.0 * atr_val)     # SL ABOVE entry
                    
                    # Validate: TP < Entry < SL
                    if take_profit_price >= entry_price or stop_loss_price <= entry_price:
                        print(f"🌙 MOON DEV DEBUG: Short order validation failed - TP: {take_profit_price:.2f}, Entry: {entry_price:.2f}, SL: {stop_loss_price:.2f}")
                        return
                    
                    risk_amount = stop_loss_price - entry_price
                    
                    if risk_amount <= 0:
                        print(f"🌙 MOON DEV DEBUG: Invalid risk calculation for short - Entry: {entry_price:.2f}, SL: {stop_loss_price:.2f}")
                        return
                    
                    position_size = int(round((self.equity * self.risk_per_trade) / risk_amount))
                    
                    if position_size > 0:
                        print(f"🌙 MOON DEV SHORT ENTRY: Price: {entry_price:.2f}, Size: {position_size}, RSI: {rsi_val:.1f}, SL: {stop_loss_price:.2f}, TP: {take_profit_price:.2f}")
                        self.sell(size=position_size, sl=stop_loss_price, tp=take_profit_price)
                        self.trailing_low = entry_price
                    else:
                        print(f"🌙 MOON DEV DEBUG: Invalid position size for short: {position_size}")
        
        else:
            bb_middle_val = float(self.bb_middle[-1]) if len(self.bb_middle) > 0 else 0
            rsi_val = float(self.rsi[-1]) if len(self.rsi) > 0 else 50
            atr_val = float(self.atr[-1]) if len(self.atr) > 0 else 0.01
            
            if self.position.is_long:
                self.trailing_high = max(self.trailing_high, current_high)
                
                exit_condition_1 = current_close < bb_middle_val
                exit_condition_2 = rsi_val < 40
                exit_condition_3 = current_close < (self.trailing_high - (1.5 * atr_val))
                
                if exit_condition_1 or exit_condition_2 or exit_condition_3:
                    print(f"🌙 MOON DEV LONG EXIT: Price: {current_close:.2f}, Reason: {'BB Middle' if exit_condition_1 else 'RSI' if exit_condition_2 else 'Trailing Stop'}")
                    self.position.close()
                    
            elif self.position.is_short:
                self.trailing_low = min(self.trailing_low, current_low)
                
                exit_condition_1 = current_close > bb_middle_val
                exit_condition_2 = rsi_val > 60
                exit_condition_3 = current_close > (self.trailing_low + (1.5 * atr_val))
                
                if exit_condition_1 or exit_condition_2 or exit_condition_3:
                    print(f"🌙 MOON DEV SHORT EXIT: Price: {current_close:.2f}, Reason: {'BB Middle' if exit_condition_1 else 'RSI' if exit_condition_2 else 'Trailing Stop'}")
                    self.position.close()

data = load_data()
bt = Backtest(data, VolatilityBreakout, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)