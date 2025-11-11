from backtesting import Backtest, Strategy
import talib
import pandas as pd
import numpy as np
import os

# Load and prepare data
data_file_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'rbi', 'BTC-USD-15m.csv')
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
        atr_value = self.atr[-1] if self.atr[-1] > 0 else 1

        if self.position:
            # Exit on RSI overbought (> 70)
            if self.rsi[-1] > 70:
                self.position.close()
                print(f"✨ RSI Overbought Exit 🌙: Closing position at {self.data.Open[-1]}")
        else:
            # Entry: RSI crosses above 30 AND price above SMA200
            if (self.rsi[-2] < 30 and self.rsi[-1] > 30) and (self.data.Close[-1] > self.sma200[-1]):
                # Risk 1% of equity per trade
                risk_amount = 0.01 * self.equity
                position_size = risk_amount / (2.5 * atr_value) if atr_value > 0 else 0
                position_size = max(int(position_size), 0)
                if position_size > 0:
                    self.buy(size=position_size)
                    print(f"🌙 New Long Position 🚀: Buying at next open with size {position_size}")
                else:
                    print("🌙 Skipped trade due to zero position size (ATR too small) ✨")

bt = Backtest(data, ContrarianSeventyThirty, cash=1_000_000, commission=0.0002)
stats = bt.run()
print(stats)