from backtesting import Backtest, Strategy
import talib
import pandas as pd
import numpy as np

class AGBotTrailingStop(Strategy):
    def init(self):
        print("🌙 Initializing strategy and cleaning data...")
        self.data.columns = self.data.columns.str.strip().str.lower()
        self.data = self.data.drop(columns=[col for col in self.data.columns if 'unnamed' in col.lower()])
        self.data = self.data.rename(columns={
            'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'
        })

        print("✨ Computing indicators using talib...")
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.atr1 = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=1)
        self.ema1 = self.I(talib.EMA, self.data.Close, timeperiod=1)
        self.atr14 = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.sma_atr14 = self.I(talib.SMA, self.atr14, timeperiod=14)

    def next(self):
        print("🌙 Evaluating conditions for the next step...")
        time = self.data.index[-1]
        current_time = time.time()
        start_time = pd.to_datetime('09:30:00').time()
        end_time = pd.to_datetime('16:00:00').time()

        if not (start_time <= current_time <= end_time):
            print("✨ Outside trading hours, skipping...")
            return

        price = self.data.Close[-1]
        trailing_stop_long = self.data.Close[-1] - self.atr1[-1] * 3
        trailing_stop_short = self.data.Close[-1] + self.atr1[-1] * 3

        if price > self.ema200[-1]:
            print("✨ Price is above EMA200, checking for long entry...")
            if self.data.Close[-2] < trailing_stop_long and price > trailing_stop_long and \
               self.ema1[-2] < trailing_stop_long and self.ema1[-1] > trailing_stop_long:
                print("🌙 Bullish conditions met, entering long...")
                stop_loss_dist = self.atr14[-1] * 1.5 * (self.atr14[-1] / self.sma_atr14[-1])
                position_size = (0.025 * self.equity) / stop_loss_dist
                position_size = int(round(position_size))
                self.buy(size=position_size, sl=price - stop_loss_dist)

        elif price < self.ema200[-1]:
            print("✨ Price is below EMA200, checking for short entry...")
            if trailing_stop_short < self.data.Close[-2] and trailing_stop_short > price and \
               trailing_stop_short < self.ema1[-2] and trailing_stop_short > self.ema1[-1]:
                print("🌙 Bearish conditions met, entering short...")
                stop_loss_dist = self.atr14[-1] * 1.5 * (self.atr14[-1] / self.sma_atr14[-1])
                position_size = (0.025 * self.equity) / stop_loss_dist
                position_size = int(round(position_size))
                self.sell(size=position_size, sl=price + stop_loss_dist)

        # End of day close
        if current_time >= end_time:
            print("✨ End of day, closing positions...")
            self.position.close()

# Load data
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv', parse_dates=['datetime'], index_col='datetime')

# Run backtest
bt = Backtest(data, AGBotTrailingStop, cash=1_000_000, commission=0.0003, trade_on_close=True)
stats = bt.run()
print(stats)