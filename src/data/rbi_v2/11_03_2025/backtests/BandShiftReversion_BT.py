import pandas as pd
import yfinance as yf
import talib
from backtesting import Backtest, Strategy
import numpy as np

def load_data():
    ticker = yf.Ticker("BTC-USD")
    data = ticker.history(period="2y", interval="1h")
    data = data.reset_index()
    data.columns = data.columns.str.strip()
    data = data.rename(columns={'Date': 'datetime'})
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    return data[['Open', 'High', 'Low', 'Close', 'Volume']]

class BandShiftReversion(Strategy):
    bb_period = 20
    bb_std = 2
    atr_period = 14
    risk_per_trade = 0.02
    max_reentries = 2
    
    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        
        self.bb_upper = self.I(talib.BBANDS, close, timeperiod=self.bb_period, nbdevup=self.bb_std)[0]
        self.bb_middle = self.I(talib.BBANDS, close, timeperiod=self.bb_period, nbdevup=self.bb_std)[1]
        self.bb_lower = self.I(talib.BBANDS, close, timeperiod=self.bb_period, nbdevup=self.bb_std)[2]
        self.sma_20 = self.I(talib.SMA, close, timeperiod=20)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        
        self.reentry_count = 0
        self.entry_price = 0
        self.position_size = 0
        self.stop_loss = 0
        self.take_profit = 0
        self.breakeven_set = False

    def next(self):
        current_close = self.data.Close[-1]
        current_low = self.data.Low[-1]
        current_high = self.data.High[-1]
        current_atr = self.atr[-1]
        
        if not self.position:
            self.reentry_count = 0
            self.breakeven_set = False
            
            bandshift_condition = self.bb_lower[-1] > self.sma_20[-1]
            touch_condition = current_low <= self.bb_lower[-1]
            bullish_candle = current_close > self.data.Open[-1]
            
            if bandshift_condition and touch_condition and bullish_candle:
                risk_amount = self.equity * self.risk_per_trade
                atr_stop_distance = 2 * current_atr
                position_size = risk_amount / atr_stop_distance
                position_size = int(round(position_size))
                
                if position_size > 0:
                    self.entry_price = current_close
                    self.stop_loss = self.entry_price - atr_stop_distance
                    self.take_profit = self.entry_price + (2 * current_atr)
                    
                    print(f"🌙 MOON DEV ENTRY SIGNAL! 🚀")
                    print(f"📈 Entry Price: {self.entry_price:.2f}")
                    print(f"🛑 Stop Loss: {self.stop_loss:.2f}")
                    print(f"🎯 Take Profit: {self.take_profit:.2f}")
                    print(f"💰 Position Size: {position_size} units")
                    
                    self.buy(size=position_size)
        
        else:
            if not self.breakeven_set and current_high >= self.entry_price + current_atr:
                self.stop_loss = self.entry_price
                self.breakeven_set = True
                print(f"✨ BREAKEVEN SET! Stop moved to entry: {self.entry_price:.2f}")
            
            if current_low <= self.stop_loss:
                print(f"🛑 STOP LOSS HIT! Exiting at: {current_close:.2f}")
                self.position.close()
                self.reentry_count += 1
                
                if self.reentry_count <= self.max_reentries:
                    print(f"🔄 RE-ENTRY ATTEMPT #{self.reentry_count}")
            
            elif current_high >= self.take_profit:
                print(f"🎯 TAKE PROFIT HIT! Exiting at: {current_close:.2f}")
                self.position.close()
            
            elif current_high >= self.bb_middle[-1]:
                print(f"📊 MIDDLE BAND TOUCH! Exiting at: {current_close:.2f}")
                self.position.close()

if __name__ == "__main__":
    data = load_data()
    bt = Backtest(data, BandShiftReversion, cash=1000000, commission=.002)
    stats = bt.run()
    print(stats)
    print(stats._strategy)