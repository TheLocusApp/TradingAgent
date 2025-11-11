import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
import yfinance as yf

class DualWaveCrossover(Strategy):
    # Strategy parameters
    fast_ema_period = 13
    slow_ema_period = 48
    atr_period = 14
    risk_per_trade = 0.02  # 2% risk per trade
    
    def init(self):
        # Clean and prepare data for TA-Lib (convert to float64)
        close_prices = self.data.Close.astype(float)
        high_prices = self.data.High.astype(float)
        low_prices = self.data.Low.astype(float)
        
        # Calculate EMAs using TA-Lib
        self.fast_ema = self.I(talib.EMA, close_prices, timeperiod=self.fast_ema_period)
        self.slow_ema = self.I(talib.EMA, close_prices, timeperiod=self.slow_ema_period)
        
        # Calculate ATR for stop loss
        self.atr = self.I(talib.ATR, high_prices, low_prices, close_prices, timeperiod=self.atr_period)
        
        # Track entry price manually
        self.entry_price = None
        
        print(f"🌙 Moon Dev: DualWave Crossover Strategy Initialized")
        print(f"✨ Fast EMA: {self.fast_ema_period}, Slow EMA: {self.slow_ema_period}")
        print(f"🚀 ATR Period: {self.atr_period}, Risk per Trade: {self.risk_per_trade*100}%")

    def next(self):
        # Skip if we don't have enough data for indicators
        if len(self.data) < self.slow_ema_period + 1:
            return
            
        current_bar = len(self.data) - 1
        current_close = self.data.Close[-1]
        current_atr = self.atr[-1]
        
        # Calculate position size based on risk management
        if current_atr > 0:
            risk_amount = self.equity * self.risk_per_trade
            position_size = risk_amount / (current_atr * 2.5)  # Using 2.5 ATR for stop
            position_size = int(round(position_size))
        else:
            position_size = int(self.equity * 0.02 / current_close)  # Fallback calculation
        
        # Ensure reasonable position size
        max_position = int(self.equity * 0.1 / current_close)  # Max 10% of equity
        position_size = min(position_size, max_position)
        
        # Entry and Exit Logic
        if not self.position:
            # No position - look for entries
            if (self.fast_ema[-2] <= self.slow_ema[-2] and 
                self.fast_ema[-1] > self.slow_ema[-1] and 
                current_close > self.fast_ema[-1] and 
                current_close > self.slow_ema[-1]):
                # 🌙 LONG ENTRY: Fast EMA crosses above Slow EMA
                stop_price = current_close - (current_atr * 2.5)
                target_price = current_close + (current_atr * 5)  # 2:1 reward ratio
                
                if position_size > 0:
                    self.buy(size=position_size, sl=stop_price, tp=target_price)
                    self.entry_price = current_close
                    print(f"🌙 MOON ENTRY LONG 🟢 | Bar: {current_bar} | Price: {current_close:.2f} | Size: {position_size}")
                    print(f"   🛡️  SL: {stop_price:.2f} | 🎯 TP: {target_price:.2f} | ATR: {current_atr:.2f}")
                    
            elif (self.fast_ema[-2] >= self.slow_ema[-2] and 
                  self.fast_ema[-1] < self.slow_ema[-1] and 
                  current_close < self.fast_ema[-1] and 
                  current_close < self.slow_ema[-1]):
                # 🌙 SHORT ENTRY: Fast EMA crosses below Slow EMA
                stop_price = current_close + (current_atr * 2.5)
                target_price = current_close - (current_atr * 5)  # 2:1 reward ratio
                
                if position_size > 0:
                    self.sell(size=position_size, sl=stop_price, tp=target_price)
                    self.entry_price = current_close
                    print(f"🌙 MOON ENTRY SHORT 🔴 | Bar: {current_bar} | Price: {current_close:.2f} | Size: {position_size}")
                    print(f"   🛡️  SL: {stop_price:.2f} | 🎯 TP: {target_price:.2f} | ATR: {current_atr:.2f}")
        
        else:
            # We have a position - look for exits
            if self.position.is_long:
                # Exit long when fast EMA crosses below slow EMA
                if (self.fast_ema[-2] >= self.slow_ema[-2] and 
                    self.fast_ema[-1] < self.slow_ema[-1]):
                    self.position.close()
                    print(f"🌙 MOON EXIT LONG 🔄 | Bar: {current_bar} | Price: {current_close:.2f} | PnL: {self.position.pl:.2f}")
                    
            elif self.position.is_short:
                # Exit short when fast EMA crosses above slow EMA
                if (self.fast_ema[-2] <= self.slow_ema[-2] and 
                    self.fast_ema[-1] > self.slow_ema[-1]):
                    self.position.close()
                    print(f"🌙 MOON EXIT SHORT 🔄 | Bar: {current_bar} | Price: {current_close:.2f} | PnL: {self.position.pl:.2f}")

# Download SPY data using yfinance
print("🌙 DOWNLOADING SPY DATA...")
ticker = yf.Ticker("SPY")
data = ticker.history(period="730d", interval="1h")  # Max 730 days for hourly data

# Clean and prepare data
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

print(f"🌙 DATA DOWNLOADED: {len(data)} bars | From {data.index[0]} to {data.index[-1]}")

# Run backtest
print("🚀 STARTING MOON DEV BACKTEST...")
bt = Backtest(data, DualWaveCrossover, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)