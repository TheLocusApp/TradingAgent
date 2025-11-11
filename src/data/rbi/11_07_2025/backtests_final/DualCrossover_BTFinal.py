import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import talib
import yfinance as yf

class DualCrossover(Strategy):
    ema_fast_period = 8
    ema_slow_period = 13
    risk_per_trade = 1.0
    
    def init(self):
        close_prices = self.data.Close.astype(float)
        
        self.ema_fast = self.I(talib.EMA, close_prices, timeperiod=self.ema_fast_period)
        self.ema_slow = self.I(talib.EMA, close_prices, timeperiod=self.ema_slow_period)
        
        self.entry_price = None
        
    def calculate_position_size(self, entry_price, stop_loss_price):
        risk_distance = abs(entry_price - stop_loss_price) / entry_price
        
        if risk_distance == 0:
            return 0.01
            
        risk_amount = self.equity * (self.risk_per_trade / 100)
        position_value = risk_amount / risk_distance
        size = position_value / self.equity
        
        size = max(0.01, min(size, 0.5))
        return size
        
    def next(self):
        current_price = self.data.Close[-1]
        current_fast_ema = self.ema_fast[-1]
        current_slow_ema = self.ema_slow[-1]
        prev_fast_ema = self.ema_fast[-2] if len(self.ema_fast) > 1 else current_fast_ema
        prev_slow_ema = self.ema_slow[-2] if len(self.ema_slow) > 1 else current_slow_ema
        
        if not self.position:
            crossover_signal = None
            
            if (prev_fast_ema <= prev_slow_ema and 
                current_fast_ema > current_slow_ema):
                crossover_signal = "bullish"
                print(f"🌙 MOON DEV ALERT: BULLISH CROSSOVER DETECTED! | Fast EMA: {current_fast_ema:.2f} > Slow EMA: {current_slow_ema:.2f}")
                
            elif (prev_fast_ema >= prev_slow_ema and 
                  current_fast_ema < current_slow_ema):
                crossover_signal = "bearish"
                print(f"🌙 MOON DEV ALERT: BEARISH CROSSOVER DETECTED! | Fast EMA: {current_fast_ema:.2f} < Slow EMA: {current_slow_ema:.2f}")
            
            if crossover_signal == "bullish":
                entry_price = current_price
                stop_loss = entry_price * 0.99
                take_profit = entry_price * 1.02
                
                if stop_loss < entry_price < take_profit:
                    size = self.calculate_position_size(entry_price, stop_loss)
                    self.buy(size=size, sl=stop_loss, tp=take_profit)
                    self.entry_price = entry_price
                    print(f"🚀 MOON DEV LONG ENTRY | Price: {entry_price:.2f} | Size: {size:.2%} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}")
                    
            elif crossover_signal == "bearish":
                entry_price = current_price
                stop_loss = entry_price * 1.01
                take_profit = entry_price * 0.98
                
                if take_profit < entry_price < stop_loss:
                    size = self.calculate_position_size(entry_price, stop_loss)
                    self.sell(size=size, sl=stop_loss, tp=take_profit)
                    self.entry_price = entry_price
                    print(f"📉 MOON DEV SHORT ENTRY | Price: {entry_price:.2f} | Size: {size:.2%} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}")
                    
        else:
            if self.position.is_long:
                if (prev_fast_ema >= prev_slow_ema and 
                    current_fast_ema < current_slow_ema):
                    self.position.close()
                    print(f"✨ MOON DEV LONG EXIT | Bearish crossover detected | Price: {current_price:.2f} | P&L: {self.position.pl:.2f}")
                    
            elif self.position.is_short:
                if (prev_fast_ema <= prev_slow_ema and 
                    current_fast_ema > current_slow_ema):
                    self.position.close()
                    print(f"✨ MOON DEV SHORT EXIT | Bullish crossover detected | Price: {current_price:.2f} | P&L: {self.position.pl:.2f}")

ticker = yf.Ticker("QQQ")
data = ticker.history(period="60d", interval="1h")

data = data.reset_index()
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

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

bt = Backtest(data, DualCrossover, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)