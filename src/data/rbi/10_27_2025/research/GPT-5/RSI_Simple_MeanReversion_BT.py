from backtesting import Backtest, Strategy
import talib
import pandas as pd

# Load and prepare data
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)

class RSI_Simple_MeanReversion(Strategy):
    def init(self):
        # Using talib for indicators and wrapping them in self.I() ✨
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)

    def next(self):
        if self.position:
            entry_price = self.position.price
            stop_loss = entry_price * 0.97
            time_in_position = len(self.trades)
            
            if time_in_position >= 10:
                print("🌙 Time Stop! Exiting after 10 bars. 🚀")
                self.position.close()
            elif self.data.Close[-1] < stop_loss:
                print("🌙 Stop Loss hit! Exiting. 🚀")
                self.position.close()
            elif self.rsi[-1] > 70:
                print("🌙 Take Profit! RSI above 70. 🚀")
                self.position.close()

        else:
            if self.rsi[-1] < 30 and self.data.Close[-1] > self.ema200[-1]:
                risk = self.data.Close[-1] * 0.03
                position_size = 10000 * 0.02 / risk
                position_size = int(round(position_size))  # Ensure position size is a whole number
                print(f"🌙 Buy Signal! RSI below 30, entering with size {position_size}. ✨")
                self.buy(size=position_size)

bt = Backtest(data, RSI_Simple_MeanReversion, cash=10000, commission=0.001, exclusive_orders=True)
stats = bt.run()
print(stats)