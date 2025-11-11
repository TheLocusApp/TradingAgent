import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import talib

class TeslaGapFill(Strategy):
    gap_threshold = 0.015  # 1.5% minimum gap
    rsi_period = 14
    sma_period = 20
    max_holding_days = 5
    risk_per_trade = 0.02  # 2% risk per trade
    
    def init(self):
        # Clean and prepare data
        self.data.df.columns = self.data.df.columns.str.strip().str.lower()
        
        # Calculate indicators
        self.sma = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_period)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.prev_close = self.I(self.calculate_prev_close)
        
        # Calculate gap percentage
        self.gap_pct = self.I(self.calculate_gap_percentage)
        
        # Track entry days for time-based exit
        self.entry_day = None
        
    def calculate_prev_close(self):
        """Calculate previous day's close"""
        return pd.Series(self.data.Close).shift(1)
    
    def calculate_gap_percentage(self):
        """Calculate gap percentage from previous close"""
        gap = (self.data.Open - self.prev_close) / self.prev_close
        return gap * 100  # Return as percentage
    
    def next(self):
        current_bar = len(self.data) - 1
        
        # Skip if we don't have enough data
        if current_bar < max(self.sma_period, self.rsi_period) + 1:
            return
            
        # Check if we're in a position
        if self.position:
            self.manage_position(current_bar)
        else:
            self.check_entry_signals(current_bar)
    
    def check_entry_signals(self, current_bar):
        """Check for gap entry signals"""
        gap_size = abs(self.gap_pct[current_bar])
        
        # Check if gap meets minimum threshold
        if gap_size < self.gap_threshold * 100:  # Convert to percentage
            return
            
        is_gap_down = self.gap_pct[current_bar] < 0
        volume_spike = self.data.Volume[current_bar] > self.data.Volume[current_bar-1] * 1.5
        rsi_value = self.rsi[current_bar]
        
        # Gap Down (Buy) Signal
        if is_gap_down:
            if (rsi_value < 30 and  # Oversold
                volume_spike and
                self.data.Close[current_bar] > self.data.Low[current_bar] and  # Some recovery from lows
                self.data.Close[current_bar] > self.sma[current_bar]):  # Above SMA for trend context
                
                self.enter_long_position(current_bar)
                
        # Gap Up (Short) Signal  
        else:
            if (rsi_value > 70 and  # Overbought
                volume_spike and
                self.data.Close[current_bar] < self.data.High[current_bar] and  # Some rejection from highs
                self.data.Close[current_bar] < self.sma[current_bar]):  # Below SMA for trend context
                
                self.enter_short_position(current_bar)
    
    def enter_long_position(self, current_bar):
        """Enter long position for gap down fill"""
        gap_size_pct = abs(self.gap_pct[current_bar]) / 100
        target_price = self.prev_close[current_bar]  # Gap fill target
        stop_price = self.data.Low[current_bar]  # Below gap day low
        
        risk_per_share = self.data.Close[current_bar] - stop_price
        if risk_per_share <= 0:
            return
            
        # Calculate position size with 2% risk
        risk_amount = self.equity * self.risk_per_trade
        position_size = risk_amount / risk_per_share
        position_size = int(round(position_size))
        
        if position_size > 0:
            print(f"🌙 MOON DEV GAP DOWN ENTRY! 🚀")
            print(f"   Gap: {self.gap_pct[current_bar]:.2f}% | Entry: ${self.data.Close[current_bar]:.2f}")
            print(f"   Target: ${target_price:.2f} | Stop: ${stop_price:.2f}")
            print(f"   Position Size: {position_size} shares")
            
            self.buy(size=position_size, sl=stop_price, tp=target_price)
            self.entry_day = current_bar
    
    def enter_short_position(self, current_bar):
        """Enter short position for gap up fill"""
        gap_size_pct = abs(self.gap_pct[current_bar]) / 100
        target_price = self.prev_close[current_bar]  # Gap fill target
        stop_price = self.data.High[current_bar]  # Above gap day high
        
        risk_per_share = stop_price - self.data.Close[current_bar]
        if risk_per_share <= 0:
            return
            
        # Calculate position size with 2% risk
        risk_amount = self.equity * self.risk_per_trade
        position_size = risk_amount / risk_per_share
        position_size = int(round(position_size))
        
        if position_size > 0:
            print(f"🌙 MOON DEV GAP UP ENTRY! 📉")
            print(f"   Gap: {self.gap_pct[current_bar]:.2f}% | Entry: ${self.data.Close[current_bar]:.2f}")
            print(f"   Target: ${target_price:.2f} | Stop: ${stop_price:.2f}")
            print(f"   Position Size: {position_size} shares")
            
            self.sell(size=position_size, sl=stop_price, tp=target_price)
            self.entry_day = current_bar
    
    def manage_position(self, current_bar):
        """Manage open positions"""
        if not self.entry_day:
            return
            
        # Time-based exit (max holding period)
        days_held = current_bar - self.entry_day
        if days_held >= self.max_holding_days:
            if self.position.is_long:
                print(f"🌙 TIME EXIT LONG 📅 | Held {days_held} days")
                self.position.close()
            else:
                print(f"🌙 TIME EXIT SHORT 📅 | Held {days_held} days")
                self.position.close()
            return
        
        # Check for trend failure exit
        gap_size = abs(self.gap_pct[self.entry_day]) / 100
        entry_price = self.position.entry_price
        
        if self.position.is_long:
            # Exit if price moves against by more than gap size
            if self.data.Close[current_bar] < entry_price * (1 - gap_size):
                print(f"🌙 TREND FAILURE EXIT LONG 🛑 | Loss exceeded gap size")
                self.position.close()
        else:
            # Exit if price moves against by more than gap size
            if self.data.Close[current_bar] > entry_price * (1 + gap_size):
                print(f"🌙 TREND FAILURE EXIT SHORT 🛑 | Loss exceeded gap size")
                self.position.close()

# Load and prepare data
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path)

# Clean column names and drop unnamed columns
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Ensure proper column mapping
column_mapping = {
    'open': 'Open',
    'high': 'High', 
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}
data = data.rename(columns=column_mapping)

# Convert datetime and set index
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

print("🌙 MOON DEV TESLA GAP FILL BACKTEST STARTING... 🚀")
print(f"Data shape: {data.shape}")
print(f"Date range: {data.index.min()} to {data.index.max()}")

# Run backtest
bt = Backtest(data, TeslaGapFill, cash=1000000)
stats = bt.run()
print(stats)
print(stats._strategy)