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
    data = data.rename(columns={'date': 'datetime'})
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    
    vix_ticker = yf.Ticker("^VIX")
    vix_data = vix_ticker.history(period="2y", interval="1d")
    vix_data = vix_data.reset_index()
    vix_data.columns = vix_data.columns.str.strip().str.lower()
    vix_data = vix_data.rename(columns={'date': 'datetime', 'close': 'VIX'})
    vix_data['datetime'] = pd.to_datetime(vix_data['datetime'])
    vix_data = vix_data.set_index('datetime')
    vix_data = vix_data[['VIX']]
    
    data = data.join(vix_data, how='left')
    data['VIX'] = data['VIX'].ffill()
    
    data = data.rename(columns={
        'open': 'Open', 'high': 'High', 'low': 'Low', 
        'close': 'Close', 'volume': 'Volume'
    })
    
    return data[['Open', 'High', 'Low', 'Close', 'Volume', 'VIX']]

class VolatilityDivergence(Strategy):
    rsi_period = 14
    atr_period = 14
    vix_lookback = 5
    divergence_lookback = 7
    
    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        vix = self.data.VIX
        
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        self.swing_high = self.I(talib.MAX, high, timeperiod=10)
        self.swing_low = self.I(talib.MIN, low, timeperiod=10)
        
        def vix_shift_func(vix_array):
            shifted_vix = np.full_like(vix_array, np.nan)
            for i in range(len(vix_array)):
                if i >= self.vix_lookback:
                    shifted_vix[i] = vix_array[i - self.vix_lookback]
                else:
                    shifted_vix[i] = vix_array[0]
            return shifted_vix
        
        self.vix_shifted = self.I(vix_shift_func, vix)
        
        def vix_increasing_func():
            return vix > self.vix_shifted
        
        self.vix_increasing = self.I(vix_increasing_func)
        
        self.position_count = 0
        self.max_positions = 3
        
    def next(self):
        current_price = self.data.Close[-1]
        current_rsi = self.rsi[-1]
        current_atr = self.atr[-1]
        current_vix = self.data.VIX[-1]
        
        if len(self.data) < 20:
            return
            
        if self.position:
            self.manage_position(current_price, current_atr, current_vix)
        else:
            self.check_entry(current_price, current_rsi, current_atr, current_vix)
    
    def check_entry(self, price, rsi, atr, vix):
        if self.position_count >= self.max_positions:
            return
            
        if vix > 45:
            print("🌙 Moon Dev Alert: VIX too high for entry - skipping trade")
            return
            
        if not self.vix_increasing[-1]:
            return
            
        bullish_divergence = self.detect_bullish_divergence()
        
        if bullish_divergence and self.vix_increasing[-1]:
            swing_high_break = price > self.swing_high[-2]
            
            if swing_high_break:
                entry_price = price
                stop_loss = entry_price - (2 * atr)
                take_profit = entry_price + (3 * atr)
                
                risk_per_trade = 0.01
                risk_amount = self.equity * risk_per_trade
                risk_per_share = entry_price - stop_loss
                
                if risk_per_share > 0:
                    position_size = risk_amount / risk_per_share
                    position_size = int(round(position_size))
                    
                    if position_size > 0:
                        self.buy(size=position_size, sl=stop_loss, tp=take_profit)
                        self.position_count += 1
                        print(f"🚀 Moon Dev LONG Entry! Price: {entry_price:.2f}, SL: {stop_loss:.2f}, TP: {take_profit:.2f}")
                        print(f"✨ Position Size: {position_size} shares, RSI: {rsi:.1f}, VIX: {vix:.1f}")
    
    def detect_bullish_divergence(self):
        if len(self.data.Close) < self.divergence_lookback + 5:
            return False
            
        price_lows = []
        rsi_lows = []
        
        for i in range(1, self.divergence_lookback + 1):
            if len(self.data.Close) >= i + 1:
                price_low = self.data.Low[-i]
                rsi_low = self.rsi[-i]
                
                if len(price_lows) == 0 or price_low < price_lows[-1]:
                    price_lows.append(price_low)
                    rsi_lows.append(rsi_low)
        
        if len(price_lows) >= 2:
            price_lower_low = price_lows[-1] < price_lows[-2]
            rsi_higher_low = rsi_lows[-1] > rsi_lows[-2]
            
            return price_lower_low and rsi_higher_low
        
        return False
    
    def manage_position(self, price, atr, vix):
        if vix > 50:
            print("🌪️ Moon Dev Emergency Exit! VIX spike detected")
            self.position.close()
            self.position_count = max(0, self.position_count - 1)

if __name__ == "__main__":
    data = load_data()
    data.columns = data.columns.str.strip()
    
    print("🌙 Moon Dev Backtest Starting...")
    print(f"📊 Data loaded: {len(data)} periods")
    print(f"📈 First date: {data.index[0]}")
    print(f"📉 Last date: {data.index[-1]}")
    
    bt = Backtest(data, VolatilityDivergence, cash=1000000, commission=.002)
    
    stats = bt.run()
    print(stats)
    print(stats._strategy)