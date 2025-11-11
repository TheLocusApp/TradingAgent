import pandas as pd
import talib
from backtesting import Backtest, Strategy
import numpy as np

class DualHorizon(Strategy):
    ema_fast_period = 48
    ema_slow_period = 200
    risk_per_trade = 0.02
    trailing_stop_pct = 0.03
    
    def init(self):
        print("🌙 Moon Dev's DualHorizon Strategy Initializing...")
        
        self.ema_fast = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_fast_period)
        self.ema_slow = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_slow_period)
        
        self.crossover_above = self.I(lambda x, y: x > y, self.ema_fast, self.ema_slow)
        self.crossover_below = self.I(lambda x, y: x < y, self.ema_fast, self.ema_slow)
        
        self.position_size = 0
        self.trailing_stop = 0
        
    def next(self):
        current_close = self.data.Close[-1]
        current_fast_ema = self.ema_fast[-1]
        current_slow_ema = self.ema_slow[-1]
        
        if len(self.data) < max(self.ema_fast_period, self.ema_slow_period) + 1:
            return
            
        risk_amount = self.equity * self.risk_per_trade
        
        if not self.position:
            if (self.crossover_above[-1] and not self.crossover_above[-2] and
                current_close > current_fast_ema and current_close > current_slow_ema):
                
                stop_loss_price = current_close * (1 - 0.03)
                position_size = int(round(risk_amount / (current_close - stop_loss_price)))
                
                if position_size > 0:
                    print(f"🚀 MOON BULLISH CROSSOVER DETECTED! Long Entry at {current_close:.2f}")
                    self.buy(size=position_size, sl=stop_loss_price)
                    self.trailing_stop = stop_loss_price
                    
            elif (self.crossover_below[-1] and not self.crossover_below[-2] and
                  current_close < current_fast_ema and current_close < current_slow_ema):
                  
                stop_loss_price = current_close * (1 + 0.03)
                position_size = int(round(risk_amount / (stop_loss_price - current_close)))
                
                if position_size > 0:
                    print(f"🌑 BEARISH CROSSOVER DETECTED! Short Entry at {current_close:.2f}")
                    self.sell(size=position_size, sl=stop_loss_price)
                    self.trailing_stop = stop_loss_price
                    
        else:
            if self.position.is_long:
                new_trailing_stop = current_close * (1 - self.trailing_stop_pct)
                if new_trailing_stop > self.trailing_stop:
                    self.trailing_stop = new_trailing_stop
                    self.position.sl = self.trailing_stop
                    print(f"✨ Updating long trailing stop to {self.trailing_stop:.2f}")
                    
                if self.crossover_below[-1] and not self.crossover_below[-2]:
                    print(f"🌙 Reverse signal - Closing long position at {current_close:.2f}")
                    self.position.close()
                    
            elif self.position.is_short:
                new_trailing_stop = current_close * (1 + self.trailing_stop_pct)
                if new_trailing_stop < self.trailing_stop:
                    self.trailing_stop = new_trailing_stop
                    self.position.sl = self.trailing_stop
                    print(f"✨ Updating short trailing stop to {self.trailing_stop:.2f}")
                    
                if self.crossover_above[-1] and not self.crossover_above[-2]:
                    print(f"🌙 Reverse signal - Closing short position at {current_close:.2f}")
                    self.position.close()

from pathlib import Path
data_path = Path(__file__).parent.parent / 'data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(data_path, parse_dates=['datetime'], index_col='datetime')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
bt = Backtest(data, DualHorizon, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)