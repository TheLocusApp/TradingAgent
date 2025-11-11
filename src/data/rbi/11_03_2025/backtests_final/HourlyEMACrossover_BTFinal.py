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
    debug = True

    def init(self):
        if self.debug:
            print("🌙 Moon Dev Init: Booting indicators... ✨")
            print(f"🌙 Settings -> fast_ema: {self.fast_ema_period}, slow_ema: {self.slow_ema_period}, trend_filter_ema: {self.trend_filter_ema_period}, ATR: {self.atr_period}, ADX thr: {self.adx_threshold}, risk: {self.risk_per_trade}")

        # Track entry and stop manually due to API limitations
        self.entry_price = None
        self.stop_price = None

        # TA-Lib requires float64
        self.fast_ema = self.I(ta.EMA, self.data.Close.astype(float), timeperiod=self.fast_ema_period)
        self.slow_ema = self.I(ta.EMA, self.data.Close.astype(float), timeperiod=self.slow_ema_period)
        self.trend_filter_ema = self.I(ta.EMA, self.data.Close.astype(float), timeperiod=self.trend_filter_ema_period)
        self.atr = self.I(ta.ATR, self.data.High.astype(float), self.data.Low.astype(float), self.data.Close.astype(float), timeperiod=self.atr_period)
        self.adx = self.I(ta.ADX, self.data.High.astype(float), self.data.Low.astype(float), self.data.Close.astype(float), timeperiod=self.atr_period)

    def next(self):
        # Ensure we have at least 2 data points for crossover logic
        if len(self.fast_ema) < 2 or len(self.slow_ema) < 2 or len(self.trend_filter_ema) < 2 or len(self.atr) < 1 or len(self.adx) < 1:
            return

        price = float(self.data.Close[-1])
        atr_val = float(self.atr[-1]) if not np.isnan(self.atr[-1]) else None
        adx_val = float(self.adx[-1]) if not np.isnan(self.adx[-1]) else None

        # Entry: Bullish crossover, price above 200 EMA, ADX above threshold
        if not self.position:
            bullish_cross = (self.fast_ema[-2] < self.slow_ema[-2] and self.fast_ema[-1] > self.slow_ema[-1])
            trend_ok = price > float(self.trend_filter_ema[-1]) if not np.isnan(self.trend_filter_ema[-1]) else False
            adx_ok = adx_val is not None and adx_val > self.adx_threshold
            if bullish_cross and trend_ok and adx_ok and atr_val is not None and atr_val > 0:
                stop_price = price - 2.0 * atr_val
                size = self.calculate_size(price, stop_price)
                if size > 0:
                    if self.debug:
                        print(f"🌙 Entry Signal ✨ | Time: {self.data.index[-1]} | Price: {price:.2f}")
                        print(f"   - Bullish Crossover: True | Trend OK: {trend_ok} | ADX: {adx_val:.2f} > {self.adx_threshold}")
                        print(f"   - Stop: {stop_price:.2f} | ATR: {atr_val:.4f} | Size: {size}")
                    # Place buy without SL/TP (manual management below)
                    self.buy(size=size)
                    # Track entry and initial stop manually
                    self.entry_price = price
                    self.stop_price = stop_price

        # Manage long position: trail stop manually
        elif self.position.is_long and atr_val is not None and atr_val > 0:
            ema_stop = float(self.slow_ema[-1]) - 0.5 * atr_val if not np.isnan(self.slow_ema[-1]) else -np.inf
            vol_stop = price - 2.0 * atr_val
            current_sl = self.stop_price if self.stop_price is not None else -np.inf
            new_sl = max(current_sl, ema_stop, vol_stop)

            # Update trailing stop if tightened
            if np.isfinite(new_sl) and (self.stop_price is None or new_sl > self.stop_price):
                if self.debug:
                    old_sl_str = f"{self.stop_price:.2f}" if self.stop_price is not None and np.isfinite(self.stop_price) else "None"
                    print(f"🌙 Trail Stop Update ✨ | Time: {self.data.index[-1]} | Price: {price:.2f}")
                    print(f"   - Old SL: {old_sl_str} -> New SL: {new_sl:.2f}")
                    print(f"   - EMA Stop: {ema_stop:.2f} | Vol Stop: {vol_stop:.2f} | ATR: {atr_val:.4f}")
                self.stop_price = new_sl

            # If price breaches stop, close position
            if self.stop_price is not None and np.isfinite(self.stop_price) and price <= self.stop_price:
                if self.debug:
                    print(f"🌙 Stop Hit 🚨 | Time: {self.data.index[-1]} | Price: {price:.2f} <= SL: {self.stop_price:.2f} | Closing position.")
                self.position.close()
                self.entry_price = None
                self.stop_price = None

    def calculate_size(self, entry_price, stop_price):
        position_risk = max(entry_price - stop_price, 0)
        if position_risk <= 0 or not np.isfinite(position_risk):
            if self.debug:
                print(f"🌙 Size Calc ⚠️ Invalid risk. Entry: {entry_price}, Stop: {stop_price}")
            return 0
        account_risk = float(self.equity) * float(self.risk_per_trade)
        position_size = int(np.floor(account_risk / position_risk))
        position_size = max(position_size, 1)
        if self.debug:
            print(f"🌙 Size Calc ✨ | Equity: {self.equity:.2f} | Risk/Trade: {self.risk_per_trade}")
            print(f"   - Entry: {entry_price:.4f} | Stop: {stop_price:.4f} | Risk/Unit: {position_risk:.4f}")
            print(f"   - Account Risk: {account_risk:.2f} | Size: {position_size}")
        return position_size

# Download SPY data via yfinance
print("🌙 Moon Dev Data: Downloading SPY 1h data... ✨")
ticker = yf.Ticker("SPY")
# yfinance hourly data limit: max 730 days
data = ticker.history(period="730d", interval="1h")

# Reset index and clean columns
data = data.reset_index()
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Rename columns to match backtesting.py requirements
data = data.rename(columns={
    'date': 'datetime',
    'datetime': 'datetime',
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# Set datetime as index
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

# Ensure tz-naive index if needed
if getattr(data.index, 'tz', None) is not None:
    data.index = data.index.tz_localize(None)

print(f"🌙 Moon Dev Data: {len(data)} bars loaded ✨")

# Run backtest
bt = Backtest(data, HourlyEMACrossover, cash=1000000, commission=.002)
print("🌙 Moon Dev Backtest: Running... ✨")
stats = bt.run()
print("🌙 Moon Dev Backtest: Complete! ✨")
print(stats)
try:
    print(stats._strategy)
except Exception as e:
    print(f"🌙 Debug: Could not print strategy instance ({e})")