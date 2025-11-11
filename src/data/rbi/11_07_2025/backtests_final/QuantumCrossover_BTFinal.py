import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
import yfinance as yf

class QuantumCrossover(Strategy):
    # Strategy parameters
    ema_fast_period = 8
    ema_slow_period = 13
    risk_per_trade = 1.5  # 1.5% risk per trade
    stop_loss_pct = 0.8   # 0.8% stop loss
    
    def init(self):
        # Convert data to float64 for TA-Lib compatibility
        close_prices = self.data.Close.astype(float)
        high_prices = self.data.High.astype(float)
        low_prices = self.data.Low.astype(float)
        volume_data = self.data.Volume.astype(float)
        
        # Calculate EMAs using TA-Lib
        self.ema_fast = self.I(talib.EMA, close_prices, timeperiod=self.ema_fast_period)
        self.ema_slow = self.I(talib.EMA, close_prices, timeperiod=self.ema_slow_period)
        
        # Calculate RSI for additional filtering
        self.rsi = self.I(talib.RSI, close_prices, timeperiod=14)
        
        # Track entry price manually
        self.entry_price = None
        
        print("🌙 QuantumCrossover Strategy Initialized")
        print(f"✨ Fast EMA: {self.ema_fast_period}, Slow EMA: {self.ema_slow_period}")
        print(f"🚀 Risk per trade: {self.risk_per_trade}%, Stop loss: {self.stop_loss_pct}%")

    def calculate_position_size(self, entry_price, stop_loss_price):
        """Calculate position size based on risk percentage"""
        # Calculate risk distance as percentage
        risk_distance = abs(entry_price - stop_loss_price) / entry_price
        
        # Calculate risk amount in dollars
        risk_amount = self.equity * (self.risk_per_trade / 100)
        
        # Calculate position value needed
        position_value = risk_amount / risk_distance
        
        # Convert to fraction of equity (0 to 1)
        size = position_value / self.equity
        
        # Ensure it's between 0.01 and 0.5 (max 50% of equity per trade)
        size = max(0.01, min(size, 0.5))
        
        return size

    def next(self):
        current_price = self.data.Close[-1]
        current_time = self.data.index[-1]
        
        # Skip if we don't have enough data for indicators
        if (pd.isna(self.ema_fast[-1]) or pd.isna(self.ema_slow[-1]) or 
            pd.isna(self.ema_fast[-2]) or pd.isna(self.ema_slow[-2])):
            return
        
        # Check if we're in market hours (9:30 AM - 4:00 PM ET)
        hour = current_time.hour
        minute = current_time.minute
        market_hours = ((hour == 9 and minute >= 30) or 
                       (hour > 9 and hour < 16) or 
                       (hour == 16 and minute == 0))
        
        if not market_hours:
            return
        
        # Get current and previous EMA values
        ema_fast_current = self.ema_fast[-1]
        ema_fast_prev = self.ema_fast[-2]
        ema_slow_current = self.ema_slow[-1]
        ema_slow_prev = self.ema_slow[-2]
        
        # Check for EMA crossovers
        fast_above_slow_current = ema_fast_current > ema_slow_current
        fast_above_slow_prev = ema_fast_prev > ema_slow_prev
        fast_below_slow_current = ema_fast_current < ema_slow_current
        fast_below_slow_prev = ema_fast_prev < ema_slow_prev
        
        # Check price position relative to EMAs
        price_above_both_emas = current_price > ema_fast_current and current_price > ema_slow_current
        price_below_both_emas = current_price < ema_fast_current and current_price < ema_slow_current
        
        # Get RSI for filtering
        rsi_current = self.rsi[-1] if not pd.isna(self.rsi[-1]) else 50
        
        if not self.position:
            # LONG ENTRY: Fast EMA crosses above Slow EMA + price above both EMAs
            if (not fast_above_slow_prev and fast_above_slow_current and 
                price_above_both_emas and rsi_current < 70):
                
                entry_price = current_price
                stop_loss = entry_price * (1 - self.stop_loss_pct / 100)
                take_profit = entry_price * (1 + (self.stop_loss_pct * 1.5) / 100)  # 1.5:1 reward ratio
                
                # Validate long order conditions
                if stop_loss < entry_price < take_profit:
                    size = self.calculate_position_size(entry_price, stop_loss)
                    self.buy(size=size, sl=stop_loss, tp=take_profit)
                    self.entry_price = entry_price
                    print(f"🌙 LONG ENTRY | Price: {entry_price:.2f} | Size: {size:.2%} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}")
            
            # SHORT ENTRY: Fast EMA crosses below Slow EMA + price below both EMAs
            elif (not fast_below_slow_prev and fast_below_slow_current and 
                  price_below_both_emas and rsi_current > 30):
                
                entry_price = current_price
                stop_loss = entry_price * (1 + self.stop_loss_pct / 100)
                take_profit = entry_price * (1 - (self.stop_loss_pct * 1.5) / 100)  # 1.5:1 reward ratio
                
                # Validate short order conditions
                if take_profit < entry_price < stop_loss:
                    size = self.calculate_position_size(entry_price, stop_loss)
                    self.sell(size=size, sl=stop_loss, tp=take_profit)
                    self.entry_price = entry_price
                    print(f"🌙 SHORT ENTRY | Price: {entry_price:.2f} | Size: {size:.2%} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}")
        
        else:
            # EXIT LOGIC for existing positions
            if self.position.is_long:
                # Exit long when fast EMA crosses below slow EMA
                if fast_below_slow_current and not fast_below_slow_prev:
                    self.position.close()
                    print(f"🌙 LONG EXIT | EMA Crossover | Price: {current_price:.2f} | P/L: {self.position.pl:.2f}")
                
                # Alternative exit: RSI overbought
                elif rsi_current > 80:
                    self.position.close()
                    print(f"🌙 LONG EXIT | RSI Overbought | Price: {current_price:.2f} | P/L: {self.position.pl:.2f}")
            
            elif self.position.is_short:
                # Exit short when fast EMA crosses above slow EMA
                if fast_above_slow_current and not fast_above_slow_prev:
                    self.position.close()
                    print(f"🌙 SHORT EXIT | EMA Crossover | Price: {current_price:.2f} | P/L: {self.position.pl:.2f}")
                
                # Alternative exit: RSI oversold
                elif rsi_current < 20:
                    self.position.close()
                    print(f"🌙 SHORT EXIT | RSI Oversold | Price: {current_price:.2f} | P/L: {self.position.pl:.2f}")

# Download QQQ data using yfinance
print("🌙 Downloading QQQ data...")
ticker = yf.Ticker("QQQ")

# Use 1-hour data instead of 5-minute due to yfinance limitations
data = ticker.history(period="730d", interval="1h")

# Reset index and clean columns
data = data.reset_index()
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Rename columns to match backtesting.py requirements
data = data.rename(columns={
    'datetime': 'datetime',
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# Set datetime as index
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

print(f"🌙 Data loaded: {len(data)} candles from {data.index[0]} to {data.index[-1]}")

# Run backtest
print("🌙 Starting QuantumCrossover Backtest...")
bt = Backtest(data, QuantumCrossover, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)