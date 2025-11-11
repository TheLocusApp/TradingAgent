"""
Simple test strategy to verify backtesting.py works
This should DEFINITELY generate trades
"""
import pandas as pd
import numpy as np
import yfinance as yf
from backtesting import Backtest, Strategy
import talib

def load_data():
    ticker = yf.Ticker("SPY")
    data = ticker.history(period="2y", interval="1d")
    data = data.reset_index()
    data.columns = data.columns.str.strip().str.lower()
    data = data.rename(columns={
        'date': 'datetime',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    return data[['Open', 'High', 'Low', 'Close', 'Volume']]

class SimpleSMAStrategy(Strategy):
    """
    ULTRA SIMPLE: Buy when price > 20 SMA, sell when price < 20 SMA
    This WILL generate trades if the system works
    """
    sma_period = 20
    
    def init(self):
        close = np.array(self.data.Close, dtype=np.float64)
        self.sma = self.I(talib.SMA, close, timeperiod=self.sma_period)
        print(f"🌙 Simple SMA Strategy Initialized!")
        print(f"📊 SMA Period: {self.sma_period}")
    
    def next(self):
        # Skip warmup period
        if len(self.data) < self.sma_period:
            return
        
        price = self.data.Close[-1]
        sma = self.sma[-1]
        
        # SIMPLE LOGIC: Buy if above SMA, sell if below
        if not self.position:
            if price > sma:
                print(f"🟢 BUY: Price {price:.2f} > SMA {sma:.2f}")
                self.buy(size=0.95)  # Use 95% of equity
        else:
            if price < sma:
                print(f"🔴 SELL: Price {price:.2f} < SMA {sma:.2f}")
                self.position.close()

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 TESTING SIMPLE SMA STRATEGY")
    print("="*80)
    
    data = load_data()
    print(f"📊 Data loaded: {len(data)} bars")
    print(f"📅 Date range: {data.index[0]} to {data.index[-1]}")
    
    bt = Backtest(data, SimpleSMAStrategy, cash=1000000, commission=0.002)
    stats = bt.run()
    
    print("\n" + "="*80)
    print("📊 RESULTS")
    print("="*80)
    print(stats)
    
    print("\n" + "="*80)
    print(f"✅ Trades: {stats['# Trades']}")
    print(f"📈 Return: {stats['Return [%]']:.2f}%")
    print("="*80)
