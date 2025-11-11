import yfinance as yf
import pandas as pd
import talib
from backtesting import Backtest, Strategy
import numpy as np

# Fetch data using yfinance
ticker = yf.Ticker("TSLA")
data = ticker.history(period="1y", interval="1h")
data.index.name = 'datetime'

# Clean and prepare data
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High', 
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

class VolatilityBreakout(Strategy):
    bb_period = 20
    bb_std = 2
    rsi_period = 14
    volume_lookback = 20
    
    def init(self):
        print("🌙 Moon Dev Volatility Breakout Strategy Initializing...")
        
        # Bollinger Bands
        self.bb_middle = self.I(talib.SMA, self.data.Close, timeperiod=self.bb_period)
        bb_bands = self.I(talib.BBANDS, self.data.Close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)
        self.bb_upper = bb_bands[0]
        self.bb_lower = bb_bands[2]
        
        # Band width for squeeze detection
        self.bb_width = self.I(lambda: (self.bb_upper - self.bb_lower) / self.bb_middle)
        
        # Volume indicator
        self.volume_sma = self.I(talib.SMA, self.data.Volume, timeperiod=self.volume_lookback)
        
        # RSI for momentum filter
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        
        print("✨ Indicators loaded successfully!")
        
    def next(self):
        current_idx = len(self.data) - 1
        
        # Skip if we don't have enough data
        if current_idx < max(self.bb_period, self.rsi_period, self.volume_lookback):
            return
            
        # Calculate band width percentile for squeeze detection
        lookback_period = 50
        if current_idx >= lookback_period:
            recent_bb_width = self.bb_width[current_idx-lookback_period:current_idx]
            bb_width_percentile = np.percentile(recent_bb_width, 30)
            
            squeeze_condition = self.bb_width[current_idx] <= bb_width_percentile
            volume_condition = self.data.Volume[current_idx] > self.volume_sma[current_idx]
            
            # Long entry conditions
            if (squeeze_condition and 
                self.data.Close[current_idx-1] > self.bb_upper[current_idx-1] and
                volume_condition and
                self.rsi[current_idx] > 50 and
                not self.position):
                
                print(f"🚀 LONG SIGNAL DETECTED! | Price: {self.data.Close[current_idx]:.2f} | RSI: {self.rsi[current_idx]:.1f}")
                stop_loss = self.bb_lower[current_idx]
                risk = self.data.Close[current_idx] - stop_loss
                if risk > 0:
                    size = min(1000000 / risk * 0.01, 1000000 / self.data.Close[current_idx])
                    self.buy(size=size, sl=stop_loss)
                    print(f"🌙 ENTERED LONG | Size: {size:.2f} | Stop: {stop_loss:.2f}")
            
            # Short entry conditions  
            elif (squeeze_condition and
                  self.data.Close[current_idx-1] < self.bb_lower[current_idx-1] and
                  volume_condition and
                  self.rsi[current_idx] < 50 and
                  not self.position):
                  
                print(f"📉 SHORT SIGNAL DETECTED! | Price: {self.data.Close[current_idx]:.2f} | RSI: {self.rsi[current_idx]:.1f}")
                stop_loss = self.bb_upper[current_idx]
                risk = stop_loss - self.data.Close[current_idx]
                if risk > 0:
                    size = min(1000000 / risk * 0.01, 1000000 / self.data.Close[current_idx])
                    self.sell(size=size, sl=stop_loss)
                    print(f"🌙 ENTERED SHORT | Size: {size:.2f} | Stop: {stop_loss:.2f}")
        
        # Exit logic for long positions
        if self.position and self.position.is_long:
            # Take profit at opposite band or use trailing stop
            if self.data.Close[current_idx] >= self.bb_lower[current_idx] and self.data.Close[current_idx-1] < self.bb_lower[current_idx-1]:
                print(f"💰 LONG PROFIT TAKEN | Price: {self.data.Close[current_idx]:.2f}")
                self.position.close()
            # Trailing stop based on middle band
            elif self.data.Close[current_idx] < self.bb_middle[current_idx]:
                print(f"🛑 LONG TRAILING STOP | Price: {self.data.Close[current_idx]:.2f}")
                self.position.close()
        
        # Exit logic for short positions
        elif self.position and self.position.is_short:
            # Take profit at opposite band or use trailing stop
            if self.data.Close[current_idx] <= self.bb_upper[current_idx] and self.data.Close[current_idx-1] > self.bb_upper[current_idx-1]:
                print(f"💰 SHORT PROFIT TAKEN | Price: {self.data.Close[current_idx]:.2f}")
                self.position.close()
            # Trailing stop based on middle band
            elif self.data.Close[current_idx] > self.bb_middle[current_idx]:
                print(f"🛑 SHORT TRAILING STOP | Price: {self.data.Close[current_idx]:.2f}")
                self.position.close()

print("🌙 MOON DEV VOLATILITY BREAKOUT BACKTEST STARTING...")
bt = Backtest(data, VolatilityBreakout, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)