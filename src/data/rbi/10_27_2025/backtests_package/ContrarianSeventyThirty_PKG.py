from backtesting import Backtest, Strategy
import talib
import pandas as pd
import numpy as np

# Load and prepare data
data_file_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(data_file_path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)

class ContrarianSeventyThirty(Strategy):
    def init(self):
        print("🌙 Initializing indicators with TA-Lib ✨")
        # Initialize indicators using talib and wrap with self.I
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.sma200 = self.I(talib.SMA, self.data.Close, timeperiod=200)

    def next(self):
        price = self.data.Close[-1]
        atr_value = self.atr[-1]

        if self.position:
            stop_loss_price = self.position.entry_price - 2.5 * atr_value
            if self.data.Low[-1] <= stop_loss_price:
                self.position.close()
                print(f"🌙 Protective Stop Loss Triggered 🚀: Closing position at {self.data.Open[-1]}")
            elif len(self.trades) > 0 and (self.rsi[-2] < 70 and self.rsi[-1] > 70):
                self.position.close()
                print(f"✨ RSI Overbought Exit 🌙: Closing position at {self.data.Open[-1]}")
            elif len(self.trades) > 0 and getattr(self.trades[-1], 'is_open', False) and self.trades[-1].duration >= 60:
                self.position.close()
                print(f"🌙 Time Stop 🚀: Closing position at {self.data.Open[-1]}")
        else:
            # Bullish RSI crossover above 30 and price above SMA200 (REPLACED backtesting.lib.crossover)
            if (self.rsi[-2] < 30 and self.rsi[-1] > 30) and (self.data.Close[-1] > self.sma200[-1]):
                risk_per_share = 2.5 * atr_value
                equity = self.broker.cash
                position_size = int((0.01 * equity) / risk_per_share) if risk_per_share > 0 else 0
                if position_size > 0:
                    self.buy(size=position_size)
                    print(f"🌙 New Long Position 🚀: Buying at next open with size {position_size}")
                else:
                    print("🌙 Skipped trade due to zero position size (ATR too small) ✨")

bt = Backtest(data, ContrarianSeventyThirty, cash=1_000_000, commission=0.0002)
stats = bt.run()
print(stats)