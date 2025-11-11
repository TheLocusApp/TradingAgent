import pandas as pd
import numpy as np
import yfinance as yf
import talib
from backtesting import Backtest, Strategy

def load_data():
    print("🌙 Loading data with yfinance... ✨")
    df = yf.download("SPY", period="2y", interval="1h", auto_adjust=False, progress=False)
    df = df.dropna()
    df.index = pd.to_datetime(df.index)
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    print(f"🌙 Data loaded: {len(df)} rows from {df.index.min()} to {df.index.max()} 🌌")
    return df

class HourlyExponentialCrossover(Strategy):
    def init(self):
        print("🌙 Initializing indicators with TA-Lib... ✨")
        self.ema20 = self.I(talib.EMA, self.data.Close, timeperiod=20)
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=50)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        print("🌙 Indicators ready: EMA20, EMA50, ATR 🌠")

    def next(self):
        # Guard against NaNs during warm-up
        if (
            np.isnan(self.ema20[-1]) or np.isnan(self.ema20[-2]) or
            np.isnan(self.ema50[-1]) or np.isnan(self.ema50[-2]) or
            np.isnan(self.atr[-1])
        ):
            return

        # Enforce unit-based sizing as a positive whole number
        position_size = int(1_000_000)
        if position_size <= 0:
            print("🌙⚠️ Position size invalid; must be a positive whole number for unit-based sizing.")
            return

        price = float(self.data.Close[-1])
        ema20_now = float(self.ema20[-1])
        ema50_now = float(self.ema50[-1])
        ema50_prev = float(self.ema50[-2])
        ema50_slope = ema50_now - ema50_prev

        # Manual crossover detection (no backtesting.lib)
        bullish_cross = (self.ema20[-2] < self.ema50[-2]) and (self.ema20[-1] > self.ema50[-1])
        bearish_cross = (self.ema20[-2] > self.ema50[-2]) and (self.ema20[-1] < self.ema50[-1])

        if bullish_cross and price > ema20_now and price > ema50_now and ema50_slope > 0:
            stop_loss = price - 2 * float(self.atr[-1])  # Price level
            if price - stop_loss > 0:
                self.buy(size=position_size, sl=stop_loss)
                print(f"🌙 Long Entry Triggered 🚀 | Size: {position_size} | Price: {price:.2f} | SL: {stop_loss:.2f} | EMA20: {ema20_now:.2f} | EMA50: {ema50_now:.2f} | Slope: {ema50_slope:.6f}")

        elif bearish