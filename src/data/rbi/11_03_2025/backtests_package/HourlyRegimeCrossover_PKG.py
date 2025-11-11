import yfinance as yf
import pandas as pd
import talib
from backtesting import Backtest, Strategy

print("🌙 Moon Dev Package AI: Booting up... Ensuring zero use of backtesting.lib! ✨")

# Download data
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

# Set datetime as index
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

print(f"🌙 Data prepared: {len(data)} bars with columns {list(data.columns)}")

class HourlyRegimeCrossover(Strategy):
    k = 2.5  # ATR multiplier

    def init(self):
        print("🌙✨ Init: Registering TA-Lib indicators via self.I()")
        self.ema48 = self.I(talib.EMA, self.data.Close, timeperiod=48)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        print("🌙✨ Indicators ready: EMA48, EMA200, ATR(14), ADX(14), Volume SMA(20)")

    def next(self):
        # Position sizing (simple example leveraging ATR)
        denom = (self.data.Close[-1] - self.k * self.atr[-1])
        position_size = int(round(1000000 / denom)) if denom != 0 else 0

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

            if filters_ok:
                print(f"🌙 Buying size={position_size} @ {self.data.Close[-1]:.2f} | ATR={self.atr[-1]:.2f}")
                self.buy(size=position_size)
                entry_price = self.data.Close[-1]
                initial_stop = entry_price - self.k * self.atr[-1]
                self.position.set_stop_loss(initial_stop)
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
print(stats._strategy)