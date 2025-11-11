import yfinance as yf
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

def load_data():
    ticker = yf.Ticker("SPY")
    data = ticker.history(period="2y", interval="1h")  # 1-hour data
    if 'Date' in data.columns:
        data = data.rename(columns={'Date': 'datetime'})
    elif 'Datetime' in data.columns:
        data = data.rename(columns={'Datetime': 'datetime'})
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    return data[['Open', 'High', 'Low', 'Close', 'Volume']]

class HourlyExponentialCrossover(Strategy):
    def init(self):
        self.ema20 = self.I(talib.EMA, self.data.Close, timeperiod=20)
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=50)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
    def next(self):
        position_size = 1_000_000
        price = self.data.Close[-1]
        ema20 = self.ema20[-1]
        ema50 = self.ema50[-1]
        ema50_slope = self.ema50[-1] - self.ema50[-2]
        
        if crossover(self.ema20, self.ema50) and price > ema20 and price > ema50 and ema50_slope > 0:
            stop_loss = price - 2 * self.atr[-1]
            if price - stop_loss > 0:
                self.buy(size=position_size)
                print(f"🌙 Long Entry Triggered 🚀 | Price: {price} | EMA20: {ema20} | EMA50: {ema50} ")

        elif crossover(self.ema50, self.ema20) and price < ema20 and price < ema50 and ema50_slope < 0:
            stop_loss = price + 2 * self.atr[-1]
            if stop_loss - price > 0:
                self.sell(size=position_size)
                print(f"🌙 Short Entry Triggered 🚀 | Price: {price} | EMA20: {ema20} | EMA50: {ema50} ")

data = load_data()

bt = Backtest(data, HourlyExponentialCrossover, cash=10_000_000, commission=.002)

stats = bt.run()
print(stats)