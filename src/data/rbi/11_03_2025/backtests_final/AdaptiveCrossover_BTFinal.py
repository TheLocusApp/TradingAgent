import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import talib

class AdaptiveCrossover(Strategy):
    # Strategy parameters
    ema_fast_period = 20
    ema_slow_period = 100
    risk_per_trade = 0.02  # 2% risk per trade
    stop_loss_pct = 0.03   # 3% stop loss
    
    def init(self):
        # Calculate EMAs using TA-Lib
        self.ema_fast = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_fast_period)
        self.ema_slow = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_slow_period)
        
        # Track crossover state
        self.crossover_state = 0  # 0: neutral, 1: long, -1: short
        self.entry_price = 0
        
        print(f"🌙 Moon Dev AdaptiveCrossover Strategy Initialized")
        print(f"✨ Fast EMA: {self.ema_fast_period}, Slow EMA: {self.ema_slow_period}")
        print(f"🚀 Risk per trade: {self.risk_per_trade*100}%, Stop loss: {self.stop_loss_pct*100}%")

    def next(self):
        current_close = self.data.Close[-1]
        current_fast_ema = self.ema_fast[-1]
        current_slow_ema = self.ema_slow[-1]
        
        # Skip if we don't have enough data for EMAs
        if np.isnan(current_fast_ema) or np.isnan(current_slow_ema):
            return
        
        # Calculate position size based on risk management
        if self.risk_per_trade > 0 and self.stop_loss_pct > 0:
            risk_amount = self.equity * self.risk_per_trade
            risk_per_share = current_close * self.stop_loss_pct
            position_size = risk_amount / risk_per_share if risk_per_share > 0 else 0
            position_size = int(round(position_size))
        else:
            position_size = 1
        
        # Ensure position size is reasonable
        max_position = int(self.equity // current_close)
        position_size = min(position_size, max_position)
        
        # LONG ENTRY: Fast EMA crosses above Slow EMA
        if (self.ema_fast[-2] <= self.ema_slow[-2] and 
            self.ema_fast[-1] > self.ema_slow[-1] and 
            not self.position.is_long):
            
            # Close any short position first
            if self.position.is_short:
                print(f"🔄 Moon Dev Signal: Closing short position at {current_close:.2f}")
                self.position.close()
            
            # Enter long position
            stop_price = current_close * (1 - self.stop_loss_pct)
            print(f"🚀 Moon Dev LONG Entry! Price: {current_close:.2f}, Stop: {stop_price:.2f}, Size: {position_size}")
            self.buy(size=position_size, sl=stop_price)
            self.crossover_state = 1
            self.entry_price = current_close
        
        # SHORT ENTRY: Fast EMA crosses below Slow EMA  
        elif (self.ema_fast[-2] >= self.ema_slow[-2] and 
              self.ema_fast[-1] < self.ema_slow[-1] and 
              not self.position.is_short):
            
            # Close any long position first
            if self.position.is_long:
                print(f"🔄 Moon Dev Signal: Closing long position at {current_close:.2f}")
                self.position.close()
            
            # Enter short position
            stop_price = current_close * (1 + self.stop_loss_pct)
            print(f"📉 Moon Dev SHORT Entry! Price: {current_close:.2f}, Stop: {stop_price:.2f}, Size: {position_size}")
            self.sell(size=position_size, sl=stop_price)
            self.crossover_state = -1
            self.entry_price = current_close
        
        # EXIT RULES: Reverse crossover closes positions
        # Exit long when fast EMA crosses below slow EMA
        elif (self.position.is_long and 
              self.ema_fast[-2] >= self.ema_slow[-2] and 
              self.ema_fast[-1] < self.ema_slow[-1]):
            
            print(f"🔚 Moon Dev LONG Exit: Fast EMA crossed below Slow EMA")
            self.position.close()
            self.crossover_state = 0
        
        # Exit short when fast EMA crosses above slow EMA
        elif (self.position.is_short and 
              self.ema_fast[-2] <= self.ema_slow[-2] and 
              self.ema_fast[-1] > self.ema_slow[-1]):
            
            print(f"🔚 Moon Dev SHORT Exit: Fast EMA crossed above Slow EMA")
            self.position.close()
            self.crossover_state = 0

# Load data
data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(data_path, parse_dates=['datetime'], index_col='datetime')

# Clean column names
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})

# Run backtest
bt = Backtest(data, AdaptiveCrossover, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)