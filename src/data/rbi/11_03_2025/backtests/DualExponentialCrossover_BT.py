import pandas as pd
from backtesting import Backtest, Strategy
import talib
from pathlib import Path

data_path = Path(__file__).resolve().parents[2] / 'SPY-60m.csv'
data = pd.read_csv(data_path, parse_dates=['datetime'], index_col='datetime')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)

class DualExponentialCrossover(Strategy):
    def init(self):
        self.ema48 = self.I(talib.EMA, self.data.Close, timeperiod=48)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.atr14 = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
    
    def next(self):
        close = self.data.Close[-1]
        ema48_now, ema48_prev = self.ema48[-1], self.ema48[-2]
        ema200_now, ema200_prev = self.ema200[-1], self.ema200[-2]
        atr_value = self.atr14[-1]
        
        # Long Entry Conditions
        if (ema48_prev < ema200_prev and ema48_now > ema200_now and
            ema200_now - ema200_prev > 0 and close > ema48_now > ema200_now and
            (ema48_now - ema200_now) >= 0.0005 * close):
            sl = max(self.data.Low[-10:]) if (ema200_now - 1 * atr_value) < min(self.data.Low[-10:]) else (ema200_now - 1 * atr_value)
            size = self.equity * 0.01 / (close - sl)  # Risk 1% of equity
            size = int(round(size))
            
            print(f"🌕 Long signal detected! Moons Ahead 🚀 | Close: {close} | EMA48: {ema48_now:.2f} | EMA200: {ema200_now:.2f}")
            self.buy(sl=sl, size=size)
        
        # Hard Exit Condition for Long
        elif self.position.is_long and ema48_now < ema200_now:
            print(f"🌘 Exit Long | Close: {close} | EMA48: {ema48_now:.2f} crossed below EMA200: {ema200_now:.2f}")
            self.position.close()

        # Additional exit conditions
        elif self.position.is_long and close < self.ema48[-1]:
            print(f"🌗 Trailing Exit | Close: {close} | Below EMA48: {ema48_now:.2f}")
            self.position.close()
        
bt = Backtest(data, DualExponentialCrossover, cash=1_000_000, commission=.002, exclusive_orders=True)
stats = bt.run()
print(stats)