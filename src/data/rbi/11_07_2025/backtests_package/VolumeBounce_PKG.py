import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
import yfinance as yf

class VolumeBounce(Strategy):
    # Strategy parameters
    support_lookback = 20
    resistance_lookback = 20
    volume_lookback = 10
    risk_per_trade = 0.01
    stop_loss_ticks = 3
    rr_ratio = 1.5
    
    def init(self):
        # Clean and prepare data for TA-Lib (convert to float64)
        close_prices = self.data.Close.astype(float)
        high_prices = self.data.High.astype(float)
        low_prices = self.data.Low.astype(float)
        volume_data = self.data.Volume.astype(float)
        
        # Calculate indicators using TA-Lib
        self.support_levels = self.I(talib.MIN, low_prices, timeperiod=self.support_lookback)
        self.resistance_levels = self.I(talib.MAX, high_prices, timeperiod=self.resistance_lookback)
        self.volume_sma = self.I(talib.SMA, volume_data, timeperiod=self.volume_lookback)
        
        # Track entry price manually
        self.entry_price = None
        self.entry_stop_loss = None
        self.entry_take_profit = None
        
        print("🌙 Moon Dev VolumeBounce Strategy Initialized!")
        print(f"📊 Support Lookback: {self.support_lookback}")
        print(f"📊 Resistance Lookback: {self.resistance_lookback}")
        print(f"📊 Volume Lookback: {self.volume_lookback}")
        print(f"🛡️ Risk per Trade: {self.risk_per_trade*100}%")
        print(f"🎯 R:R Ratio: 1:{self.rr_ratio}")

    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_volume = self.data.Volume[-1]
        
        # Skip first 30 minutes of market (first 6 candles in 5-min data)
        if len(self.data) < 6:
            return
            
        # Get current support and resistance levels
        current_support = self.support_levels[-1]
        current_resistance = self.resistance_levels[-1]
        avg_volume = self.volume_sma[-1]
        
        # Skip if levels are not valid
        if np.isnan(current_support) or np.isnan(current_resistance) or np.isnan(avg_volume):
            return
            
        # Check for volume confirmation (must be above average)
        volume_confirm = current_volume > avg_volume * 1.2
        
        if not self.position:
            # LONG ENTRY LOGIC
            if self._is_near_support(current_low, current_support) and volume_confirm:
                if self._is_bullish_reversal():
                    stop_loss = current_support - (self.stop_loss_ticks * 0.01)  # Assuming $0.01 tick size
                    risk_amount = current_close - stop_loss
                    
                    if risk_amount > 0:
                        position_size = self._calculate_position_size(risk_amount)
                        take_profit = current_close + (risk_amount * self.rr_ratio)
                        
                        if position_size > 0:
                            self.buy(size=position_size, sl=stop_loss, tp=take_profit)
                            self.entry_price = current_close
                            self.entry_stop_loss = stop_loss
                            self.entry_take_profit = take_profit
                            print(f"🚀 LONG ENTRY | Price: {current_close:.2f} | Support: {current_support:.2f}")
                            print(f"🎯 SL: {stop_loss:.2f} | TP: {take_profit:.2f} | Size: {position_size}")
            
            # SHORT ENTRY LOGIC  
            elif self._is_near_resistance(current_high, current_resistance) and volume_confirm:
                if self._is_bearish_reversal():
                    stop_loss = current_resistance + (self.stop_loss_ticks * 0.01)
                    risk_amount = stop_loss - current_close
                    
                    if risk_amount > 0:
                        position_size = self._calculate_position_size(risk_amount)
                        take_profit = current_close - (risk_amount * self.rr_ratio)
                        
                        if position_size > 0:
                            self.sell(size=position_size, sl=stop_loss, tp=take_profit)
                            self.entry_price = current_close
                            self.entry_stop_loss = stop_loss
                            self.entry_take_profit = take_profit
                            print(f"📉 SHORT ENTRY | Price: {current_close:.2f} | Resistance: {current_resistance:.2f}")
                            print(f"🎯 SL: {stop_loss:.2f} | TP: {take_profit:.2f} | Size: {position_size}")
        
        else:
            # Track current position for debugging
            if self.position.is_long:
                current_pnl = (current_close - self.entry_price) / self.entry_price * 100
                if current_pnl >= 0:
                    print(f"📈 LONG Position | PnL: +{current_pnl:.2f}% | Current: {current_close:.2f}")
                else:
                    print(f"📉 LONG Position | PnL: {current_pnl:.2f}% | Current: {current_close:.2f}")
            elif self.position.is_short:
                current_pnl = (self.entry_price - current_close) / self.entry_price * 100
                if current_pnl >= 0:
                    print(f"📈 SHORT Position | PnL: +{current_pnl:.2f}% | Current: {current_close:.2f}")
                else:
                    print(f"📉 SHORT Position | PnL: {current_pnl:.2f}% | Current: {current_close:.2f}")

    def _is_near_support(self, current_low, support_level, threshold=0.001):
        """Check if price is near support level (within 0.1%)"""
        return abs(current_low - support_level) / support_level <= threshold

    def _is_near_resistance(self, current_high, resistance_level, threshold=0.001):
        """Check if price is near resistance level (within 0.1%)"""
        return abs(current_high - resistance_level) / resistance_level <= threshold

    def _is_bullish_reversal(self):
        """Detect bullish reversal candle patterns"""
        close = self.data.Close.astype(float)
        open_price = self.data.Open.astype(float)
        high = self.data.High.astype(float)
        low = self.data.Low.astype(float)
        
        # Hammer pattern (small body near top, long lower shadow)
        body = abs(close[-1] - open_price[-1])
        lower_shadow = min(open_price[-1], close[-1]) - low[-1]
        upper_shadow = high[-1] - max(open_price[-1], close[-1])
        
        is_hammer = (lower_shadow > 2 * body) and (upper_shadow < body * 0.5)
        
        # Bullish engulfing (current candle completely engulfs previous)
        if len(self.data) > 1:
            prev_close = close[-2]
            prev_open = open_price[-2]
            is_bullish_engulfing = (close[-1] > open_price[-1] and 
                                  prev_close < prev_open and
                                  open_price[-1] < prev_close and 
                                  close[-1] > prev_open)
        else:
            is_bullish_engulfing = False
            
        return is_hammer or is_bullish_engulfing

    def _is_bearish_reversal(self):
        """Detect bearish reversal candle patterns"""
        close = self.data.Close.astype(float)
        open_price = self.data.Open.astype(float)
        high = self.data.High.astype(float)
        low = self.data.Low.astype(float)
        
        # Shooting star pattern (small body near bottom, long upper shadow)
        body = abs(close[-1] - open_price[-1])
        upper_shadow = high[-1] - max(open_price[-1], close[-1])
        lower_shadow = min(open_price[-1], close[-1]) - low[-1]
        
        is_shooting_star = (upper_shadow > 2 * body) and (lower_shadow < body * 0.5)
        
        # Bearish engulfing (current candle completely engulfs previous)
        if len(self.data) > 1:
            prev_close = close[-2]
            prev_open = open_price[-2]
            is_bearish_engulfing = (close[-1] < open_price[-1] and 
                                  prev_close > prev_open and
                                  open_price[-1] > prev_close and 
                                  close[-1] < prev_open)
        else:
            is_bearish_engulfing = False
            
        return is_shooting_star or is_bearish_engulfing

    def _calculate_position_size(self, risk_amount):
        """Calculate position size based on risk management"""
        if risk_amount <= 0:
            return 0
            
        risk_dollars = self.equity * self.risk_per_trade
        position_size = risk_dollars / risk_amount
        
        # Convert to integer number of shares
        position_size = int(round(position_size))
        
        # Ensure we don't exceed available capital
        max_shares = int(self.equity // self.data.Close[-1])
        position_size = min(position_size, max_shares)
        
        return max(1, position_size)  # Minimum 1 share

# Download and prepare data
print("🌙 Downloading SPY data...")
ticker = yf.Ticker("SPY")
data = ticker.history(period="730d", interval="5m")

# Clean and prepare data
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

print(f"📊 Data loaded: {len(data)} candles")
print(f"📅 Date range: {data.index.min()} to {data.index.max()}")

# Run backtest
print("🚀 Starting Moon Dev VolumeBounce Backtest...")
bt = Backtest(data, VolumeBounce, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)