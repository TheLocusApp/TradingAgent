import pandas as pd
import numpy as np
import yfinance as yf
from backtesting import Backtest, Strategy
import talib

def load_data():
    print("🌙 MOON DEV: Loading market data from Yahoo Finance...")
    ticker = yf.Ticker("SPY")
    data = ticker.history(period="2y", interval="1h")
    data = data.reset_index()
    
    # Clean and standardize column names
    data.columns = data.columns.str.strip().str.lower()
    print(f"🌙 MOON DEV: Columns found: {list(data.columns)}")
    
    # Handle column renaming properly
    if 'date' in data.columns:
        data = data.rename(columns={'date': 'datetime'})
    elif 'index' in data.columns:
        data = data.rename(columns={'index': 'datetime'})
    
    # Drop any unnamed columns
    unnamed_cols = [col for col in data.columns if 'unnamed' in col.lower()]
    if unnamed_cols:
        print(f"🌙 MOON DEV: Dropping unnamed columns: {unnamed_cols}")
        data = data.drop(columns=unnamed_cols)
    
    # Ensure datetime column exists and process it
    if 'datetime' in data.columns:
        data['datetime'] = pd.to_datetime(data['datetime'])
        data = data.set_index('datetime')
    else:
        print("🌙 MOON DEV WARNING: No datetime column found, using index as datetime")
        data.index = pd.to_datetime(data.index)
    
    # Standardize column names for backtesting
    column_mapping = {
        'open': 'Open', 'high': 'High', 'low': 'Low', 
        'close': 'Close', 'volume': 'Volume'
    }
    
    for old_col, new_col in column_mapping.items():
        if old_col in data.columns:
            data = data.rename(columns={old_col: new_col})
    
    print(f"🌙 MOON DEV: Final columns: {list(data.columns)}")
    print(f"🌙 MOON DEV: Data shape: {data.shape}")
    
    return data[['Open', 'High', 'Low', 'Close', 'Volume']]

class DualHorizonCrossover(Strategy):
    ema_fast_period = 20
    ema_slow_period = 200
    risk_per_trade = 0.02
    stop_loss_pct = 0.03
    
    def init(self):
        close = self.data.Close
        self.ema_fast = self.I(talib.EMA, close, timeperiod=self.ema_fast_period)
        self.ema_slow = self.I(talib.EMA, close, timeperiod=self.ema_slow_period)
        self.position_size = 0
        print("🌙 MOON DEV: Strategy initialized with Dual Horizon Crossover")
        
    def next(self):
        current_close = self.data.Close[-1]
        ema_fast_current = self.ema_fast[-1]
        ema_slow_current = self.ema_slow[-1]
        ema_fast_prev = self.ema_fast[-2] if len(self.ema_fast) > 1 else ema_fast_current
        ema_slow_prev = self.ema_slow[-2] if len(self.ema_slow) > 1 else ema_slow_current
        
        if not self.position:
            # Long entry condition
            if (ema_fast_prev <= ema_slow_prev and 
                ema_fast_current > ema_slow_current and 
                current_close > ema_fast_current and 
                current_close > ema_slow_current):
                
                risk_amount = self.equity * self.risk_per_trade
                stop_price = current_close * (1 - self.stop_loss_pct)
                risk_per_share = current_close - stop_price
                
                if risk_per_share > 0:
                    position_size = risk_amount / risk_per_share
                    position_size = int(round(position_size))
                    
                    if position_size > 0:
                        self.buy(size=position_size, sl=stop_price)
                        print(f"🌙 MOON DEV LONG ENTRY! 🚀 | Price: {current_close:.2f} | Size: {position_size} | Stop: {stop_price:.2f}")
                    else:
                        print(f"🌙 MOON DEV: Position size too small: {position_size}")
                else:
                    print("🌙 MOON DEV: Risk per share calculation error")
                
            # Short entry condition  
            elif (ema_fast_prev >= ema_slow_prev and 
                  ema_fast_current < ema_slow_current and 
                  current_close < ema_fast_current and 
                  current_close < ema_slow_current):
                
                risk_amount = self.equity * self.risk_per_trade
                stop_price = current_close * (1 + self.stop_loss_pct)
                risk_per_share = stop_price - current_close
                
                if risk_per_share > 0:
                    position_size = risk_amount / risk_per_share
                    position_size = int(round(position_size))
                    
                    if position_size > 0:
                        self.sell(size=position_size, sl=stop_price)
                        print(f"🌙 MOON DEV SHORT ENTRY! 📉 | Price: {current_close:.2f} | Size: {position_size} | Stop: {stop_price:.2f}")
                    else:
                        print(f"🌙 MOON DEV: Position size too small: {position_size}")
                else:
                    print("🌙 MOON DEV: Risk per share calculation error")
        
        else:
            # Exit conditions for existing positions
            if self.position.is_long:
                if ema_fast_current < ema_slow_current:
                    self.position.close()
                    print(f"🌙 MOON DEV LONG EXIT! ✅ | Crossunder detected | Price: {current_close:.2f}")
                    
            elif self.position.is_short:
                if ema_fast_current > ema_slow_current:
                    self.position.close()
                    print(f"🌙 MOON DEV SHORT EXIT! ✅ | Crossover detected | Price: {current_close:.2f}")

if __name__ == "__main__":
    print("🌙 MOON DEV: Starting Dual Horizon Crossover Backtest")
    data = load_data()
    bt = Backtest(data, DualHorizonCrossover, cash=1000000, commission=.002)
    stats = bt.run()
    print("🌙 MOON DEV: Backtest Complete!")
    print(stats)
    print(stats._strategy)