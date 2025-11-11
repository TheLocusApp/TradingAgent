from backtesting import Backtest, Strategy
import talib as ta
import yfinance as yf
import pandas as pd
import numpy as np

class HourlyEMACrossover(Strategy):
    fast_ema_period = 13
    slow_ema_period = 48
    trend_filter_ema_period = 200
    atr_period = 14
    adx_threshold = 20
    risk_per_trade = 0.0075
    
    def init(self):
        self.fast_ema = self.I(ta.EMA, self.data.Close.astype(float), timeperiod=self.fast_ema_period)
        self.slow_ema = self.I(ta.EMA, self.data.Close.astype(float), timeperiod=self.slow_ema_period)
        self.trend_filter_ema = self.I(ta.EMA, self.data.Close.astype(float), timeperiod=self.trend_filter_ema_period)
        self.atr = self.I(ta.ATR, self.data.High.astype(float), self.data.Low.astype(float), self.data.Close.astype(float), timeperiod=self.atr_period)
        self.adx = self.I(ta.ADX, self.data.High.astype(float), self.data.Low.astype(float), self.data.Close.astype(float), timeperiod=self.atr_period)
   
    def next(self):
        if not self.position:
            if (self.fast_ema[-2] < self.slow_ema[-2] and self.fast_ema[-1] > self.slow_ema[-1] and 
                self.data.Close[-1] > self.trend_filter_ema[-1] and self.adx[-1] > self.adx_threshold):
                stop_price = self.data.Close[-1] - 2.0 * self.atr[-1]
                size = self.calculate_size(self.data.Close[-1], stop_price)
                self.buy(sl=stop_price, tp=None, size=size)
        
        elif self.position.is_long:
            stop_price = max(self.slow_ema[-1] - 0.5 * self.atr[-1], self.data.Close[-1] - 2.0 * self.atr[-1])
            self.sell(sl=stop_price, tp=None, size=self.position.size)
    
    def calculate_size(self, entry_price, stop_price):
        account_risk = self.equity * self.risk_per_trade
        position_risk = entry_price - stop_price
        position_size = int(round(account_risk / position_risk))
        return position_size

# Download SPY data
ticker = yf.Ticker("SPY")
data = ticker.history(period="10y", interval="1h")

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

# Run backtest
bt = Backtest(data, HourlyEMACrossover, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)