import yfinance as yf
import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

print("🌙 Moon Dev Package AI: Booting up... Ensuring zero use of backtesting.lib! ✨")

# Download data via yfinance (CRITICAL REQUIREMENT)
print("🌙 Fetching SPY hourly data via yfinance...")
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

# Set datetime as index and ensure timezone-naive for backtesting compatibility
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')
if getattr(data.index, 'tz', None) is not None:
    data.index = data.index.tz_localize(None)

print(f"🌙 Data prepared: {len(data)} bars with columns {list(data.columns)}")

class HourlyRegimeCrossover(Strategy):
    k = 2.5  # ATR multiplier

    def init(self):
        print("🌙✨ Init: Registering TA-Lib indicators via self.I()")
        # 🚨 CRITICAL: TA-Lib requires float64 dtype - add .astype(float) to all data columns
        self.ema48 = self.I(talib.EMA, self.data.Close.astype(float), timeperiod=48)
        self.ema200 = self.I(talib.EMA, self.data.Close.astype(float), timeperiod=200)
        self.atr = self.I(talib.ATR, self.data.High.astype(float), self.data.Low.astype(float), self.data.Close.astype(float), timeperiod=14)
        self.adx = self.I(talib.ADX, self.data.High.astype(float), self.data.Low.astype(float), self.data.Close.astype(float), timeperiod=14)
        self.vol_sma = self.I(talib.SMA, self.data.Volume.astype(float), timeperiod=20)
        print("🌙✨ Indicators ready: EMA48, EMA200, ATR(14), ADX(14), Volume SMA(20)")

    def next(self):
        # Ensure enough data to avoid index errors and NaNs
        if len(self.data.Close) < 6:
            return
        last_vals = [self.ema48[-1], self.ema200[-1], self.atr[-1], self.adx[-1], self.vol_sma[-1],
                     self.ema48[-2], self.ema200[-2], self.ema200[-5]]
        if any(pd.isna(v) for v in last_vals):
            return

        # Position sizing (units, positive whole numbers only)
        denom = (self.data.Close[-1] - self.k * self.atr[-1])
        if pd.isna(denom) or denom <= 0:
            position_size = 0
        else:
            position_size = int(max(round(1000000 / denom), 0))  # units, non-negative whole number

        # Manual crossover detection (no backtesting.lib!)
        bull_cross = (self.ema48[-2] < self.ema200[-2] and self.ema48[-1] > self.ema200[-1])
        bear_cross = (self.ema200[-2] < self.ema48[-2] and self.ema200[-1] > self.ema48[-1])

        if bull_cross:  # Long Signal
            filters_ok = (
                self.data.Close[-1] > max(self.ema48[-1], self.ema200[-1]) and
                self.ema200[-1] > self.ema200[-5] and
                self.adx[-1] > 18 and
                self.data.Volume[-1] > self.vol_sma[-1]
            )
            print(f"🌙✨ Bullish crossover detected at {self.data.index[-1]} | Filters OK: {filters_ok}")

            if filters_ok and position_size > 0:
                entry_price = self.data.Close[-1]
                initial_stop = entry_price - self.k * self.atr[-1]  # price level, not distance
                print(f"🌙 Buying size={position_size} @ {entry_price:.2f} | ATR={self.atr[-1]:.2f} | SL={initial_stop:.2f}")
                self.buy(size=position_size, sl=initial_stop)
                print(f"🌙 Stop-loss set @ {initial_stop:.2f}")

        elif bear_cross:  # Exit Long
            if self.position:
                print(f"🌙✨ Bearish crossover detected at {self.data.index[-1]} — closing long position.")
                self.position.close()

bt = Backtest(data, HourlyRegimeCrossover, cash=1000000, commission=.002)
print("🌙 Launching backtest... ✨")
stats = bt.run()
print("🌙 Backtest complete! ✨")
print(stats)
try:
    print(stats._strategy)
except Exception as e:
    print(f"🌙 Debug: Could not print strategy instance ({e})")