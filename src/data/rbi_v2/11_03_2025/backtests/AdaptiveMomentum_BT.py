import pandas as pd
import yfinance as yf
from backtesting import Backtest, Strategy
import talib

def load_data():
    ticker = yf.Ticker("SPY")
    data = ticker.history(period="2y", interval="1h")
    data = data.reset_index()
    data.columns = data.columns.str.strip()
    data = data.rename(columns={'Datetime': 'datetime'})
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    return data[['Open', 'High', 'Low', 'Close', 'Volume']]

class AdaptiveMomentum(Strategy):
    ema_fast_period = 20
    ema_slow_period = 200
    stop_loss_pct = 0.02
    trailing_stop_pct = 0.02
    
    def init(self):
        self.ema_fast = self.I(talib.EMA, self.data.Close, self.ema_fast_period)
        self.ema_slow = self.I(talib.EMA, self.data.Close, self.ema_slow_period)
        self.position_size = 1000000
        
    def next(self):
        current_price = self.data.Close[-1]
        
        if len(self.ema_fast) < 2 or len(self.ema_slow) < 2:
            return
            
        ema_fast_current = self.ema_fast[-1]
        ema_fast_prev = self.ema_fast[-2]
        ema_slow_current = self.ema_slow[-1]
        ema_slow_prev = self.ema_slow[-2]
        
        if not self.position:
            if (ema_fast_prev <= ema_slow_prev and 
                ema_fast_current > ema_slow_current):
                self.buy(size=1)
                
            elif (ema_fast_prev >= ema_slow_prev and 
                  ema_fast_current < ema_slow_current):
                self.sell(size=1)
                
        else:
            if self.position.is_long:
                if (ema_fast_prev >= ema_slow_prev and 
                    ema_fast_current < ema_slow_current):
                    self.position.close()
                    
            elif self.position.is_short:
                if (ema_fast_prev <= ema_slow_prev and 
                    ema_fast_current > ema_slow_current):
                    self.position.close()

if __name__ == "__main__":
    data = load_data()
    bt = Backtest(data, AdaptiveMomentum, cash=1000000, commission=.002)
    results = bt.run()
    print(results)
    bt.plot()