import yfinance as yf
import talib
import pandas as pd
from backtesting import Backtest, Strategy

# 🌙 Data Loading via yfinance (per Moon Dev spec)
ticker = yf.Ticker("SPY")
data = ticker.history(period="2y", interval="1h")
data = data.reset_index()
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'date': 'datetime', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')
try:
    data.index = data.index.tz_localize(None)
except Exception:
    pass

class SpanRatioCrossover(Strategy):
    def init(self):
        print("🌙 Init ✨: Setting up TA-Lib indicators (EMA48, EMA200, ATR14, ADX14)")
        self.ema48 = self.I(talib.EMA, self.data.Close, timeperiod=48)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
    
    def next(self):
        # Warm-up guard to ensure enough bars for EMA200 lookback and slope calc
        if len(self.data.Close) < 206:
            if len(self.data.Close) % 25 == 0:
                print(f"🌙 Debug ✨: Warming up indicators... bars={len(self.data.Close)}")
            return

        # Check positions
        if self.position:
            # Exit logic
            if (self.data.Close[-1] < self.ema48[-1] or 
                self.data.Close[-1] < self.ema200[-1]):
                self.position.close()
                print("🚀🎯 Moon Exit ✨: Position closed")

            # Scale out logic with integer units and SL to breakeven
            entry_price = self.position.price
            risk = 1.5 * self.atr[-1]
            if self.data.Close[-1] >= entry_price + 2 * risk:
                if self.position.size >= 2:
                    units_to_close = max(1, int(self.position.size // 2))
                    self.position.close(size=units_to_close)
                    # Move stop to breakeven; support different backtesting versions
                    try:
                        self.position.modify(sl=entry_price)
                    except Exception:
                        try:
                            self.position.set_sl(entry_price)
                        except Exception as e:
                            print(f"🌙 Debug ✨: Unable to set breakeven SL due to: {e}")
                    print("🌙 Partial Moon Exit 🚀: Scaled out position")
                else:
                    # Too small to scale out by integer units; only move SL to breakeven
                    try:
                        self.position.modify(sl=entry_price)
                    except Exception:
                        try:
                            self.position.set_sl(entry_price)
                        except Exception as e:
                            print(f"🌙 Debug ✨: Unable to set breakeven SL due to: {e}")
                    print("🌙 Partial Moon Exit 🚀: Position too small to scale; moved SL to breakeven")
        else:
            # Entry logic
            cross_margin = (self.ema48[-1] - self.ema200[-1]) / self.data.Close[-1]
            ema200_slope = self.ema200[-1] - self.ema200[-6]
            
            if (self.ema48[-1] > self.ema200[-1] and
                self.data.Close[-1] > self.ema48[-1] and
                self.data.Close[-1] > self.ema200[-1] and
                ema200_slope > 0 and 
                cross_margin >= 0.001 and
                self.adx[-1] >= 18):
                
                atr_risk = 1.5 * self.atr[-1]
                if atr_risk <= 0:
                    print("🌙 Debug ✨: ATR risk non-positive, skipping entry")
                    return
                position_size = max(1, int(self.equity * 0.01 / atr_risk))
                self.buy(size=position_size, sl=self.data.Close[-1] - atr_risk)
                print(f"🌝 New Moon Entry 🚀: Buying {position_size} units at {self.data.Close[-1]} | ATR risk={atr_risk:.4f} | ADX={self.adx[-1]:.2f}")

print("🌙 Launching Backtest ✨")
bt = Backtest(data, SpanRatioCrossover, cash=1000000, commission=.002)
stats = bt.run()
print("🌙 Backtest Complete ✨ - Stats:")
print(stats)
print(stats._strategy)