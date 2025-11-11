import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
import yfinance as yf

class VolatilityDivergence(Strategy):
    # Strategy parameters
    keltner_period = 20
    keltner_multiplier = 2.0
    bollinger_period = 20
    bollinger_std = 2.0
    rsi_period = 14
    atr_period = 14
    risk_per_trade = 1.0  # 1% risk per trade
    
    def init(self):
        # Convert all data to float64 for TA-Lib compatibility
        close_prices = self.data.Close.astype(float)
        high_prices = self.data.High.astype(float)
        low_prices = self.data.Low.astype(float)
        volume_data = self.data.Volume.astype(float)
        
        # Calculate Keltner Channel
        self.ema = self.I(talib.EMA, close_prices, timeperiod=self.keltner_period)
        self.atr = self.I(talib.ATR, high_prices, low_prices, close_prices, timeperiod=self.atr_period)
        
        # Keltner Channel Upper and Lower bands
        def keltner_upper_func(ema, atr):
            return ema + (self.keltner_multiplier * atr)
        
        def keltner_lower_func(ema, atr):
            return ema - (self.keltner_multiplier * atr)
        
        self.keltner_upper = self.I(keltner_upper_func, self.ema, self.atr)
        self.keltner_lower = self.I(keltner_lower_func, self.ema, self.atr)
        
        # Calculate Bollinger Bands
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, close_prices, 
            timeperiod=self.bollinger_period, 
            nbdevup=self.bollinger_std, 
            nbdevdn=self.bollinger_std
        )
        
        # Calculate RSI for divergence detection
        self.rsi = self.I(talib.RSI, close_prices, timeperiod=self.rsi_period)
        
        # Track previous values for divergence detection
        self.price_lows = []
        self.rsi_lows = []
        self.divergence_detected = False
        
        # Track entry price manually
        self.entry_price = None
        
        print("🌙 MOON DEV: VolatilityDivergence Strategy Initialized")

    def calculate_position_size(self, entry_price, stop_loss_price):
        """Calculate position size based on risk percentage"""
        risk_distance = abs(entry_price - stop_loss_price) / entry_price
        
        if risk_distance == 0:
            return 0.01  # Minimum position size
            
        risk_amount = self.equity * (self.risk_per_trade / 100)
        position_value = risk_amount / risk_distance
        size = position_value / self.equity
        
        # Ensure size is between 0.01 and 0.5 (1% to 50% of equity)
        size = max(0.01, min(size, 0.5))
        
        print(f"🌙 MOON DEV: Position size calculated: {size:.4f} ({size*100:.2f}% of equity)")
        return size

    def detect_bullish_divergence(self):
        """Detect bullish divergence between price and RSI"""
        if len(self.data.Close) < 5:
            return False
            
        current_low = self.data.Low[-1]
        current_rsi = self.rsi[-1]
        
        # Store recent lows
        self.price_lows.append(current_low)
        self.rsi_lows.append(current_rsi)
        
        # Keep only last 10 values
        if len(self.price_lows) > 10:
            self.price_lows.pop(0)
            self.rsi_lows.pop(0)
        
        if len(self.price_lows) >= 5:
            # Find two consecutive lower price lows
            price_lower_lows = False
            rsi_higher_lows = False
            
            for i in range(2, len(self.price_lows)):
                if (self.price_lows[i] < self.price_lows[i-1] < self.price_lows[i-2] and
                    self.rsi_lows[i] > self.rsi_lows[i-1] > self.rsi_lows[i-2]):
                    price_lower_lows = True
                    rsi_higher_lows = True
                    break
            
            if price_lower_lows and rsi_higher_lows:
                print("🌙 MOON DEV: 🎯 Bullish divergence detected!")
                return True
        
        return False

    def check_bollinger_expansion(self):
        """Check if Bollinger Bands are expanding"""
        if len(self.bb_upper) < 3:
            return False
            
        current_width = self.bb_upper[-1] - self.bb_lower[-1]
        previous_width = self.bb_upper[-2] - self.bb_lower[-2]
        earlier_width = self.bb_upper[-3] - self.bb_lower[-3]
        
        # Check if bands are expanding over last 3 periods
        expansion = (current_width > previous_width > earlier_width)
        
        if expansion:
            print("🌙 MOON DEV: 📈 Bollinger Bands expanding - volatility increasing")
        
        return expansion

    def check_keltner_breakout(self):
        """Check if price breaks above upper Keltner Channel"""
        current_close = self.data.Close[-1]
        current_keltner_upper = self.keltner_upper[-1]
        
        breakout = current_close > current_keltner_upper
        
        if breakout:
            print(f"🌙 MOON DEV: 🚀 Keltner Channel breakout! Close: {current_close:.2f} > Upper: {current_keltner_upper:.2f}")
        
        return breakout

    def next(self):
        current_close = self.data.Close[-1]
        current_low = self.data.Low[-1]
        
        # Exit logic
        if self.position:
            if self.position.is_long:
                # Exit when price closes below Keltner Channel middle line (EMA)
                if current_close < self.ema[-1]:
                    print(f"🌙 MOON DEV: 📉 Exit signal - Close {current_close:.2f} below EMA {self.ema[-1]:.2f}")
                    self.position.close()
                    self.entry_price = None
                    return
                
                # Check if we should trail stop loss
                if self.entry_price:
                    # Use ATR-based trailing stop
                    trailing_stop = current_close - (2 * self.atr[-1])
                    if trailing_stop > self.entry_price:
                        self.entry_price = trailing_stop
                        print(f"🌙 MOON DEV: 🔄 Trailing stop updated to {trailing_stop:.2f}")
        
        # Entry logic - only if no current position
        if not self.position:
            # Check all three entry conditions
            divergence = self.detect_bullish_divergence()
            bollinger_expanding = self.check_bollinger_expansion()
            keltner_breakout = self.check_keltner_breakout()
            
            if divergence and bollinger_expanding and keltner_breakout:
                print("🌙 MOON DEV: 🎯 ALL ENTRY CONDITIONS MET! Preparing long entry...")
                
                entry_price = current_close
                
                # Calculate stop loss using recent swing low or ATR
                recent_lows = [self.data.Low[-i] for i in range(1, min(6, len(self.data.Low)))]
                swing_low = min(recent_lows) if recent_lows else current_low
                atr_stop = current_close - (2 * self.atr[-1])
                
                # Use the more conservative stop loss
                stop_loss_price = min(swing_low, atr_stop)
                
                # Validate stop loss is below entry price
                if stop_loss_price >= entry_price:
                    stop_loss_price = entry_price - (1 * self.atr[-1])
                    print(f"🌙 MOON DEV: ⚠️ Adjusted stop loss to ATR-based: {stop_loss_price:.2f}")
                
                # Calculate take profit (3:1 reward ratio)
                take_profit_price = entry_price + (3 * (entry_price - stop_loss_price))
                
                # Validate order parameters for long position
                if stop_loss_price < entry_price < take_profit_price:
                    size = self.calculate_position_size(entry_price, stop_loss_price)
                    
                    if size > 0:
                        print(f"🌙 MOON DEV: 🚀 ENTERING LONG | Entry: {entry_price:.2f} | SL: {stop_loss_price:.2f} | TP: {take_profit_price:.2f}")
                        self.buy(size=size, sl=stop_loss_price, tp=take_profit_price)
                        self.entry_price = entry_price
                    else:
                        print("🌙 MOON DEV: ❌ Position size too small, skipping trade")
                else:
                    print(f"🌙 MOON DEV: ❌ Order validation failed | SL: {stop_loss_price:.2f} | Entry: {entry_price:.2f} | TP: {take_profit_price:.2f}")

# Download data using yfinance
def download_data(ticker="SPY", period="730d", interval="1h"):
    print(f"🌙 MOON DEV: Downloading {ticker} data...")
    ticker_obj = yf.Ticker(ticker)
    data = ticker_obj.history(period=period, interval=interval)
    
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
    
    print(f"🌙 MOON DEV: Data downloaded - {len(data)} bars from {data.index[0]} to {data.index[-1]}")
    return data

# Execute backtest
if __name__ == "__main__":
    # Download data
    data = download_data(ticker="SPY", period="730d", interval="1h")
    
    # Run backtest
    bt = Backtest(data, VolatilityDivergence, cash=1000000, commission=.002)
    stats = bt.run()
    
    print(stats)
    print(stats._strategy)