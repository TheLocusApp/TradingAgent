import yfinance as yf
import pandas as pd
import talib
from backtesting import Backtest, Strategy
import numpy as np

class DynamicCrossover(Strategy):
    # Strategy parameters
    sma_period = 20
    risk_per_trade = 0.03  # 3% risk per trade
    stop_loss_pct = 0.02   # 2% stop loss
    
    def init(self):
        # Calculate 20-period SMA using TA-Lib
        self.sma_20 = self.I(talib.SMA, self.data.Close.astype(float), timeperiod=self.sma_period)
        
        # Track previous day's position relative to SMA
        self.prev_close_above_sma = None
        
        print("🌙 Moon Dev DynamicCrossover Strategy Initialized!")
        print(f"📊 SMA Period: {self.sma_period}")
        print(f"💰 Risk per Trade: {self.risk_per_trade*100}%")
        print(f"🛑 Stop Loss: {self.stop_loss_pct*100}%")
    
    def next(self):
        current_index = len(self.data) - 1
        
        # Need at least 2 days of data for comparison
        if current_index < 1:
            return
            
        # Get current and previous values
        current_close = self.data.Close[-1]
        current_sma = self.sma_20[-1]
        prev_close = self.data.Close[-2]
        prev_sma = self.sma_20[-2]
        
        # Calculate position size based on risk management
        position_size = self.risk_per_trade  # Use 3% of equity
        
        # 🌙 LONG ENTRY: Price closes above SMA and previous close was below SMA
        if (not self.position.is_long and 
            current_close > current_sma and 
            prev_close <= prev_sma):
            
            # Calculate stop loss and take profit
            entry_price = self.data.Open[-1] if len(self.data.Open) > current_index else current_close
            stop_loss_price = entry_price * (1 - self.stop_loss_pct)
            
            print(f"🚀 LONG SIGNAL DETECTED! Entry: ${entry_price:.2f}, SMA: ${current_sma:.2f}")
            print(f"🛑 Stop Loss: ${stop_loss_price:.2f}")
            
            # Enter long position
            self.buy(size=position_size, sl=stop_loss_price)
            
        # 🌙 SHORT ENTRY: Price closes below SMA and previous close was above SMA
        elif (not self.position.is_short and 
              current_close < current_sma and 
              prev_close >= prev_sma):
            
            # Calculate stop loss and take profit
            entry_price = self.data.Open[-1] if len(self.data.Open) > current_index else current_close
            stop_loss_price = entry_price * (1 + self.stop_loss_pct)
            
            print(f"📉 SHORT SIGNAL DETECTED! Entry: ${entry_price:.2f}, SMA: ${current_sma:.2f}")
            print(f"🛑 Stop Loss: ${stop_loss_price:.2f}")
            
            # Enter short position
            self.sell(size=position_size, sl=stop_loss_price)
        
        # 🌙 LONG EXIT: Price closes below SMA while in long position
        elif (self.position.is_long and 
              current_close < current_sma):
            
            print(f"🔴 EXIT LONG: Price ${current_close:.2f} closed below SMA ${current_sma:.2f}")
            self.position.close()
            
        # 🌙 SHORT EXIT: Price closes above SMA while in short position
        elif (self.position.is_short and 
              current_close > current_sma):
            
            print(f"🟢 EXIT SHORT: Price ${current_close:.2f} closed above SMA ${current_sma:.2f}")
            self.position.close()

# Fetch SPY data using yfinance
print("🌙 Fetching SPY data from Yahoo Finance...")
ticker = yf.Ticker("SPY")
data = ticker.history(period="2y", interval="1d")
data.index.name = 'datetime'

print(f"📊 Data columns: {list(data.columns)}")
print(f"📈 Data shape: {data.shape}")
print(f"📅 Date range: {data.index[0]} to {data.index[-1]}")

# Verify we have the required columns
required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
if all(col in data.columns for col in required_columns):
    print("✅ All required columns present!")
else:
    print("❌ Missing required columns!")
    missing = [col for col in required_columns if col not in data.columns]
    print(f"Missing: {missing}")

# Initialize backtest with $1,000,000 capital
print("🚀 Initializing Backtest with $1,000,000...")
bt = Backtest(data, DynamicCrossover, cash=1000000)

# Run backtest
print("🌙 Running DynamicCrossover Backtest...")
stats = bt.run()
print(stats)