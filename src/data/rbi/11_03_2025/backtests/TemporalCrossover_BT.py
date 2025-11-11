import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

class TemporalCrossover(Strategy):
    # Strategy parameters
    ema_short_period = 20
    ema_long_period = 100
    risk_per_trade = 0.02  # 2% risk per trade
    stop_loss_pct = 0.03   # 3% stop loss
    max_holding_days = 5   # 5 days maximum holding period
    
    def init(self):
        # Clean data columns
        self.data.df.columns = self.data.df.columns.str.strip().str.lower()
        
        # Calculate EMAs using talib
        self.ema_20 = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_short_period)
        self.ema_100 = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_long_period)
        
        # Calculate volume average for confirmation
        self.volume_avg = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        
        # Track entry time for time-based exits
        self.entry_time = None
        
        print("🌙 Moon Dev TemporalCrossover Strategy Initialized!")
        print(f"✨ EMA Periods: {self.ema_short_period}/{self.ema_long_period}")
        print(f"🚀 Risk Management: {self.risk_per_trade*100}% risk, {self.stop_loss_pct*100}% stop loss")

    def next(self):
        current_bar = len(self.data) - 1
        
        # Skip if we don't have enough data for EMAs
        if current_bar < self.ema_long_period:
            return
        
        # Get current values
        close = self.data.Close[-1]
        ema_20_current = self.ema_20[-1]
        ema_100_current = self.ema_100[-1]
        ema_20_prev = self.ema_20[-2]
        ema_100_prev = self.ema_100[-2]
        volume_current = self.data.Volume[-1]
        volume_avg_current = self.volume_avg[-1]
        
        # Calculate position size based on risk
        account_equity = self.equity
        risk_amount = account_equity * self.risk_per_trade
        stop_loss_distance = close * self.stop_loss_pct
        position_size = risk_amount / stop_loss_distance if stop_loss_distance > 0 else 0
        position_size = int(round(position_size))
        
        # Check for crossover signals
        bullish_crossover = (ema_20_prev <= ema_100_prev and 
                           ema_20_current > ema_100_current and 
                           close > ema_20_current)
        
        bearish_crossover = (ema_20_prev >= ema_100_prev and 
                           ema_20_current < ema_100_current and 
                           close < ema_20_current)
        
        # Volume confirmation (optional)
        volume_confirmation = volume_current > volume_avg_current
        
        # LONG ENTRY LOGIC 🌙
        if not self.position and bullish_crossover:
            if position_size > 0:
                # Calculate stop loss and take profit
                stop_price = close * (1 - self.stop_loss_pct)
                # Use reverse crossover for exit
                tp_price = None  # Let exit logic handle profit taking
                
                print(f"🚀 MOON BULL SIGNAL! Buying {position_size} shares")
                print(f"   Entry: ${close:.2f}, Stop: ${stop_price:.2f}")
                print(f"   EMA20: ${ema_20_current:.2f}, EMA100: ${ema_100_current:.2f}")
                if volume_confirmation:
                    print("   📈 Volume confirmation: YES!")
                
                self.buy(size=position_size, sl=stop_price)
                self.entry_time = current_bar
        
        # SHORT ENTRY LOGIC 🌙
        elif not self.position and bearish_crossover:
            if position_size > 0:
                # Calculate stop loss and take profit
                stop_price = close * (1 + self.stop_loss_pct)
                # Use reverse crossover for exit
                tp_price = None  # Let exit logic handle profit taking
                
                print(f"🌙 BEAR SIGNAL! Shorting {position_size} shares")
                print(f"   Entry: ${close:.2f}, Stop: ${stop_price:.2f}")
                print(f"   EMA20: ${ema_20_current:.2f}, EMA100: ${ema_100_current:.2f}")
                if volume_confirmation:
                    print("   📉 Volume confirmation: YES!")
                
                self.sell(size=position_size, sl=stop_price)
                self.entry_time = current_bar
        
        # EXIT LOGIC 🌙
        elif self.position:
            # Check for reverse crossover exit
            if self.position.is_long and bearish_crossover:
                print(f"✨ EXIT LONG: Reverse crossover detected")
                self.position.close()
                self.entry_time = None
                
            elif self.position.is_short and bullish_crossover:
                print(f"✨ EXIT SHORT: Reverse crossover detected")
                self.position.close()
                self.entry_time = None
            
            # Time-based exit (5 days maximum holding)
            elif self.entry_time and (current_bar - self.entry_time) >= (self.max_holding_days * 24):  # Assuming hourly data
                print(f"⏰ TIME EXIT: Maximum holding period reached")
                self.position.close()
                self.entry_time = None

def prepare_data(data):
    """Prepare and clean data for backtesting"""
    # Clean column names
    data.columns = data.columns.str.strip().str.lower()
    
    # Drop unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    
    # Ensure proper column mapping
    column_mapping = {
        'open': 'Open',
        'high': 'High', 
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }
    
    # Rename columns to match backtesting.py requirements
    data = data.rename(columns=column_mapping)
    
    # Ensure we have the required columns
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required_cols:
        if col not in data.columns:
            raise ValueError(f"Missing required column: {col}")
    
    return data

# Example usage (commented out for the strategy code)
if __name__ == "__main__":
    # Load your SPY hourly data
    # data = pd.read_csv('SPY_hourly.csv', index_col=0, parse_dates=True)
    # data = prepare_data(data)
    
    # Initialize backtest with $1,000,000 capital
    # bt = Backtest(data, TemporalCrossover, cash=1000000)
    
    # Run backtest
    # stats = bt.run()
    
    # Print comprehensive results
    # print("🌙 MOON DEV TEMPORAL CROSSOVER BACKTEST RESULTS 🌙")
    # print("=" * 50)
    # print(stats)
    # print("\n" + "=" * 50)
    # print("STRATEGY DETAILS:")
    # print(stats._strategy)
    pass