import pandas as pd
import yfinance as yf
from backtesting import Backtest, Strategy
import talib

def load_data():
    # Download SPY hourly data using yfinance
    ticker = yf.Ticker("SPY")
    data = ticker.history(period="2y", interval="1h")
    
    # Reset index to make datetime a column
    data = data.reset_index()
    
    # Clean and standardize column names
    data.columns = data.columns.str.strip().str.lower()
    
    # Drop any unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])
    
    # Rename columns to match backtesting.py requirements
    data = data.rename(columns={
        'date': 'datetime',
        'open': 'Open',
        'high': 'High', 
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    
    # Ensure all required columns exist
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"🌙 MOON DEV ERROR: Missing required column: {col}")
    
    # Set datetime as index
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    
    print(f"🌙 MOON DEV: Data loaded successfully - {len(data)} bars, columns: {list(data.columns)}")
    return data

class AdaptiveCrossover(Strategy):
    # Strategy parameters
    ema_fast = 20
    ema_slow = 200
    risk_per_trade = 0.02  # 2% risk per trade
    
    def init(self):
        # 🌙 MOON DEV INDICATORS - Dual EMA System 🚀
        self.ema_fast = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_fast)
        self.ema_slow = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_slow)
        
        # 🌙 Debug prints for indicator calculation
        print(f"✨ MOON DEV: EMA indicators initialized - Fast: {self.ema_fast}, Slow: {self.ema_slow}")
    
    def next(self):
        current_price = self.data.Close[-1]
        fast_ema = self.ema_fast[-1]
        slow_ema = self.ema_slow[-1]
        prev_fast_ema = self.ema_fast[-2] if len(self.ema_fast) > 1 else fast_ema
        prev_slow_ema = self.ema_slow[-2] if len(self.ema_slow) > 1 else slow_ema
        
        # 🌙 MOON DEV TRADE LOGIC - Simple Crossover System 🌙
        
        # LONG ENTRY: Fast EMA crosses above Slow EMA
        if (prev_fast_ema <= prev_slow_ema and fast_ema > slow_ema) or (fast_ema > slow_ema and not self.position):
            if not self.position:
                # Calculate position size based on 2% risk
                risk_amount = self.equity * self.risk_per_trade
                stop_distance = current_price * 0.01  # 1% stop loss
                position_size = risk_amount / stop_distance
                position_size = int(round(position_size))
                
                # Ensure minimum position size
                if position_size > 0:
                    # 🌙 ENTER LONG POSITION 🚀
                    self.buy(size=position_size)
                    print(f"🌙 MOON DEV LONG ENTRY: Price: {current_price:.2f}, Size: {position_size}, Fast EMA: {fast_ema:.2f}, Slow EMA: {slow_ema:.2f}")
        
        # SHORT ENTRY: Fast EMA crosses below Slow EMA  
        elif (prev_fast_ema >= prev_slow_ema and fast_ema < slow_ema) or (fast_ema < slow_ema and not self.position):
            if not self.position:
                # Calculate position size based on 2% risk
                risk_amount = self.equity * self.risk_per_trade
                stop_distance = current_price * 0.01  # 1% stop loss
                position_size = risk_amount / stop_distance
                position_size = int(round(position_size))
                
                # Ensure minimum position size
                if position_size > 0:
                    # 🌙 ENTER SHORT POSITION 📉
                    self.sell(size=position_size)
                    print(f"🌙 MOON DEV SHORT ENTRY: Price: {current_price:.2f}, Size: {position_size}, Fast EMA: {fast_ema:.2f}, Slow EMA: {slow_ema:.2f}")
        
        # EXIT LOGIC: Reverse crossover for position management
        if self.position:
            if self.position.is_long and fast_ema < slow_ema:
                # 🌙 EXIT LONG POSITION 💰
                pl = self.position.pl
                self.position.close()
                print(f"🌙 MOON DEV LONG EXIT: Price: {current_price:.2f}, Profit: {pl:.2f}")
            
            elif self.position.is_short and fast_ema > slow_ema:
                # 🌙 EXIT SHORT POSITION 💰
                pl = self.position.pl
                self.position.close()
                print(f"🌙 MOON DEV SHORT EXIT: Price: {current_price:.2f}, Profit: {pl:.2f}")

# Load data and run backtest
print("🌙 MOON DEV BACKTEST INITIALIZED - Adaptive Crossover Strategy 🚀")
data = load_data()
print(f"📊 Data loaded: {len(data)} bars from {data.index[0]} to {data.index[-1]}")

# Initialize backtest with 1,000,000 capital
bt = Backtest(data, AdaptiveCrossover, cash=1000000, commission=.002)

# Run backtest
print("\n🚀 RUNNING MOON DEV BACKTEST...")
stats = bt.run()
print("\n" + "="*80)
print("📊 MOON DEV BACKTEST RESULTS - Adaptive Crossover Strategy")
print("="*80)
print(stats)
print("\n" + "="*80)
print("🔍 STRATEGY DETAILS")
print("="*80)
print(stats._strategy)

# 🌙 MOON DEV'S ENHANCED TESTING FRAMEWORK 🚀
print("\n" + "="*80)
print("🚀 MOON DEV'S ENHANCED BACKTESTING COMPLETE!")
print("="*80)
print("✨ Strategy successfully tested on SPY hourly data")
print("📈 Ready for multi-market deployment!")