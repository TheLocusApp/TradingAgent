from backtesting import Backtest, Strategy
from backtesting.test import GOOG
import talib
import pandas as pd

class ContrarianSeventyThirty(Strategy):
    def init(self):
        print("🌙 Initializing strategy...")
        # Clean data
        self.data.columns = self.data.columns.str.strip().str.lower()
        self.data = self.data.drop(columns=[col for col in self.data.columns if 'unnamed' in col.lower()])

        # Calculate indicators
        self.rsi = self.I(talib.RSI, self.data.close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.high, self.data.low, self.data.close, timeperiod=14)

        # Calculate SMA200 for optional trend filter
        self.sma200 = self.I(talib.SMA, self.data.close, timeperiod=200)

    def next(self):
        price = self.data.close[-1]
        atr_value = self.atr[-1]
        rsi_value = self.rsi[-1]
        rsi_prev = self.rsi[-2] if len(self.rsi) > 1 else None
        entry_price = price

        # Entry condition
        if not self.position and rsi_value < 30 and (rsi_prev is None or rsi_prev >= 30):
            risk_per_share = 2.5 * atr_value
            shares = int((0.01 * self.equity) / risk_per_share)
            if shares > 0:
                self.buy(size=shares)
                self.entry_price = entry_price
                self.stop_loss_price = self.entry_price - risk_per_share
                print(f"🌙 🚀 Buy Signal: RSI < 30 at {price}. Buying {shares} shares.")

        # Exit conditions
        if self.position:
            if rsi_value > 70:
                self.position.close()
                print(f"🌙 ✨ Sell Signal: RSI > 70 at {price}. Exiting position.")
            elif price <= self.stop_loss_price:
                self.position.close()
                print(f"🌙 🔥 Stop Loss Triggered at {price}. Exiting position.")

bt = Backtest(GOOG, ContrarianSeventyThirty, cash=1_000_000, commission=0.0002)
stats = bt.run()
print(stats)