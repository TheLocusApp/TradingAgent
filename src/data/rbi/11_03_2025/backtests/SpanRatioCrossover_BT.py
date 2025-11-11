import yfinance as yf
import talib
import pandas as pd
from backtesting import Backtest, Strategy

# Download data
ticker = yf.Ticker("SPY")
data = ticker.history(period="2y", interval="1h")
data = data.reset_index()
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'date': 'datetime',
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

class SpanRatioCrossover(Strategy):
    def init(self):
        self.ema48 = self.I(talib.EMA, self.data.Close, timeperiod=48)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
    
    def next(self):
        # Check positions
        if self.position:
            # Exit logic
            if (self.data.Close[-1] < self.ema48[-1] or 
                self.data.Close[-1] < self.ema200[-1]):
                self.position.close()
                print("🚀🎯 Moon Exit ✨: Position closed")

            # Scale out logic
            entry_price = self.position.price
            risk = 1.5 * self.atr[-1]
            if self.data.Close[-1] >= entry_price + 2 * risk:
                self.position.close(size=self.position.size / 2)
                self.position.modify(stop=entry_price)
                print("🌙 Partial Moon Exit 🚀: Scaled out position")
        else:
            # Entry logic
            cross_margin = (self.ema48[-1] - self.ema200[-1]) / self.data.Close[-1]
            ema200_slope = self.ema200[-1] - self.ema200[-6]
            
            if (self.ema48[-1] > self.ema200[-1] and
                self.data.Close[-1] > self.ema48[-1] and
                self.data.Close[-1] > self.ema200[-1] and
                ema200_slope > 0 and 
                cross_margin >= 0.001 and
                self.adx[-1] >= 18):
                
                atr_risk = 1.5 * self.atr[-1]
                position_size = int(self.equity * 0.01 / atr_risk)
                self.buy(size=position_size, sl=self.data.Close[-1] - atr_risk)
                print(f"🌝 New Moon Entry 🚀: Buying {position_size} units at {self.data.Close[-1]}")

bt = Backtest(data, SpanRatioCrossover, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)