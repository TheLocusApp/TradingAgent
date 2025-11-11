import yfinance as yf
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# Download data
ticker = yf.Ticker("SPY")
data = ticker.history(period="2y", interval="1h")

# Reset index and clean columns
data = data.reset_index()
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Rename columns to match backtesting.py requirements
data = data.rename(columns={
    'date': 'datetime',
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# Set datetime as index
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

class HourlyRegimeCrossover(Strategy):
    k = 2.5  # ATR multiplier

    def init(self):
        self.ema48 = self.I(talib.EMA, self.data.Close, timeperiod=48)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)

    def next(self):
        position_size = int(round(1000000 / (self.data.Close[-1] - self.k * self.atr[-1])))

        if crossover(self.ema48, self.ema200):  # Long Signal
            if (self.data.Close[-1] > max(self.ema48[-1], self.ema200[-1]) and
                    self.ema200[-1] > self.ema200[-5] and
                    self.adx[-1] > 18 and
                    self.data.Volume[-1] > self.vol_sma[-1]):
                
                self.buy(size=position_size)
                entry_price = self.data.Close[-1]
                initial_stop = entry_price - self.k * self.atr[-1]
                self.position.set_stop_loss(initial_stop)
                
        elif crossover(self.ema200, self.ema48):  # Exit Long
            self.position.close()

bt = Backtest(data, HourlyRegimeCrossover, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)