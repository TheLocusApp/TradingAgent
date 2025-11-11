import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import talib

class GapReversion(Strategy):
    gap_threshold = 0.02
    max_gap_size = 0.10
    risk_per_trade = 0.02
    rsi_period = 14
    volume_lookback = 20
    
    def init(self):
        # Calculate previous day's close (shifted by 1 period)
        self.prev_close = self.I(lambda x: pd.Series(x).shift(1), self.data.Close)
        
        # Calculate gap percentage
        self.gap_pct = self.I(lambda: (self.data.Open - self.prev_close) / self.prev_close)
        
        # Calculate RSI
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        
        # Calculate volume average
        self.volume_avg = self.I(talib.SMA, self.data.Volume, timeperiod=self.volume_lookback)
        
        # Track entry time for time-based exits
        self.entry_time = None
        
    def next(self):
        current_idx = len(self.data) - 1
        
        # Skip if we don't have enough data
        if current_idx < 2:
            return
            
        # Check if we have an open position
        if self.position:
            self.manage_position(current_idx)
            return
            
        # Check for valid gap
        gap_size = abs(self.gap_pct[current_idx])
        
        # Filter gap size
        if gap_size < self.gap_threshold or gap_size > self.max_gap_size:
            return
            
        # Check volume confirmation
        if self.data.Volume[current_idx] < self.volume_avg[current_idx]:
            return
            
        # Gap-up scenario (potential short)
        if self.gap_pct[current_idx] > 0:
            self.handle_gap_up(current_idx)
            
        # Gap-down scenario (potential long)  
        elif self.gap_pct[current_idx] < 0:
            self.handle_gap_down(current_idx)
            
    def handle_gap_up(self, idx):
        """Handle gap-up scenario for short entry"""
        # Check RSI overbought condition
        if self.rsi[idx] > 70:
            # Calculate risk management
            entry_price = self.data.Close[idx]
            prev_close = self.prev_close[idx]
            gap_fill_target = prev_close  # Target is previous close
            stop_loss = self.data.High[idx] * 1.02  # 2% above gap-up high
            
            risk_per_share = stop_loss - entry_price
            reward_per_share = entry_price - gap_fill_target
            
            # Check risk-reward ratio
            if reward_per_share / risk_per_share >= 2 and risk_per_share > 0:
                # Calculate position size
                account_equity = self.equity
                risk_amount = account_equity * self.risk_per_trade
                position_size = risk_amount / risk_per_share
                position_size = int(round(position_size))
                
                if position_size > 0:
                    print(f"🌙 MOON DEV GAP REVERSION: SHORT ENTRY 🚀")
                    print(f"   Gap-up detected: {self.gap_pct[idx]:.2%}")
                    print(f"   Entry: {entry_price:.2f}, Target: {gap_fill_target:.2f}")
                    print(f"   Stop: {stop_loss:.2f}, R/R: {reward_per_share/risk_per_share:.2f}")
                    print(f"   Position size: {position_size} shares")
                    
                    self.sell(size=position_size, sl=stop_loss)
                    self.entry_time = idx
                    
    def handle_gap_down(self, idx):
        """Handle gap-down scenario for long entry"""
        # Check RSI oversold condition
        if self.rsi[idx] < 30:
            # Calculate risk management
            entry_price = self.data.Close[idx]
            prev_close = self.prev_close[idx]
            gap_fill_target = prev_close  # Target is previous close
            stop_loss = self.data.Low[idx] * 0.98  # 2% below gap-down low
            
            risk_per_share = entry_price - stop_loss
            reward_per_share = gap_fill_target - entry_price
            
            # Check risk-reward ratio
            if reward_per_share / risk_per_share >= 2 and risk_per_share > 0:
                # Calculate position size
                account_equity = self.equity
                risk_amount = account_equity * self.risk_per_trade
                position_size = risk_amount / risk_per_share
                position_size = int(round(position_size))
                
                if position_size > 0:
                    print(f"🌙 MOON DEV GAP REVERSION: LONG ENTRY 🚀")
                    print(f"   Gap-down detected: {self.gap_pct[idx]:.2%}")
                    print(f"   Entry: {entry_price:.2f}, Target: {gap_fill_target:.2f}")
                    print(f"   Stop: {stop_loss:.2f}, R/R: {reward_per_share/risk_per_share:.2f}")
                    print(f"   Position size: {position_size} shares")
                    
                    self.buy(size=position_size, sl=stop_loss)
                    self.entry_time = idx
                    
    def manage_position(self, current_idx):
        """Manage open positions including partial profits and time-based exits"""
        if not self.entry_time:
            return
            
        # Check time-based exit (3 days maximum hold)
        days_in_trade = current_idx - self.entry_time
        if days_in_trade >= 12:  # Assuming 4 periods per day for daily data
            if self.position.is_long:
                print(f"🌙 MOON DEV: Time exit - LONG closed after 3 days 📅")
                self.position.close()
            elif self.position.is_short:
                print(f"🌙 MOON DEV: Time exit - SHORT closed after 3 days 📅")
                self.position.close()
            return
            
        # Check for partial profit taking at 50% gap fill
        entry_price = self.position.entry_price
        prev_close = self.prev_close[self.entry_time]
        gap_size = abs(entry_price - prev_close)
        
        if self.position.is_long:
            current_progress = (self.data.Close[current_idx] - entry_price) / gap_size
            if current_progress >= 0.5 and self.position.size > 100:
                # Close half position
                close_size = int(self.position.size * 0.5)
                print(f"🌙 MOON DEV: Partial profit taken - 50% gap fill achieved! 🎯")
                self.position.close(portion=0.5)
                
        elif self.position.is_short:
            current_progress = (entry_price - self.data.Close[current_idx]) / gap_size
            if current_progress >= 0.5 and self.position.size > 100:
                # Close half position
                close_size = int(self.position.size * 0.5)
                print(f"🌙 MOON DEV: Partial profit taken - 50% gap fill achieved! 🎯")
                self.position.close(portion=0.5)

# Load and prepare data
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path)

# Clean column names and remove unnamed columns
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

# Ensure data is sorted
data = data.sort_index()

print("🌙 MOON DEV: Starting Gap Reversion Backtest 🚀")
print(f"Data loaded: {len(data)} periods")
print(f"Date range: {data.index[0]} to {data.index[-1]}")

# Run backtest
bt = Backtest(data, GapReversion, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)