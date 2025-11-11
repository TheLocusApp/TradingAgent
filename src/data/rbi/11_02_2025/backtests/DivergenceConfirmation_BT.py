import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import talib

class DivergenceConfirmation(Strategy):
    # Strategy parameters
    rsi_period = 14
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    risk_per_trade = 0.02
    max_positions = 3
    
    def init(self):
        # Clean and prepare data
        self.data.df.columns = self.data.df.columns.str.strip().str.lower()
        self.data.df = self.data.df.drop(columns=[col for col in self.data.df.columns if 'unnamed' in col.lower()])
        
        # Calculate indicators using self.I() wrapper
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.macd, self.macd_signal_line, self.macd_hist = self.I(
            lambda close: talib.MACD(close, fastperiod=self.macd_fast, 
                                   slowperiod=self.macd_slow, 
                                   signalperiod=self.macd_signal),
            self.data.Close
        )
        
        # Store swing highs/lows for divergence detection
        self.swing_highs = self.I(talib.MAX, self.data.High, timeperiod=5)
        self.swing_lows = self.I(talib.MIN, self.data.Low, timeperiod=5)
        
        # Track active positions
        self.active_positions = 0
        self.last_swing_low = None
        self.last_swing_high = None
        
        print("🌙 Moon Dev Divergence Strategy Initialized! ✨")

    def next(self):
        current_idx = len(self.data) - 1
        
        # Need enough data for reliable signals
        if current_idx < 30:
            return
            
        # Check if we have maximum positions
        if self.active_positions >= self.max_positions:
            return
            
        current_close = self.data.Close[-1]
        current_rsi = self.rsi[-1]
        current_macd = self.macd[-1] if self.macd[-1] is not None else 0
        current_macd_signal = self.macd_signal_line[-1] if self.macd_signal_line[-1] is not None else 0
        current_macd_hist = self.macd_hist[-1] if self.macd_hist[-1] is not None else 0
        
        # Update swing points
        self._update_swing_points(current_idx)
        
        # Check for long entry (Bullish Divergence)
        if self._bullish_divergence(current_idx) and self._macd_bullish_confirmation(current_idx):
            self._enter_long(current_close, current_idx)
            
        # Check for short entry (Bearish Divergence)
        elif self._bearish_divergence(current_idx) and self._macd_bearish_confirmation(current_idx):
            self._enter_short(current_close, current_idx)
            
        # Check exits for existing positions
        self._check_exits(current_idx, current_rsi, current_macd_hist)

    def _update_swing_points(self, current_idx):
        """Update swing high and low points for divergence detection"""
        if current_idx >= 10:
            # Look for swing lows (price making lower lows)
            if (self.data.Low[-5] < self.data.Low[-6] and 
                self.data.Low[-5] < self.data.Low[-4] and
                self.data.Low[-5] < self.data.Low[-7]):
                self.last_swing_low = (current_idx - 5, self.data.Low[-5])
                
            # Look for swing highs (price making higher highs)
            if (self.data.High[-5] > self.data.High[-6] and 
                self.data.High[-5] > self.data.High[-4] and
                self.data.High[-5] > self.data.High[-7]):
                self.last_swing_high = (current_idx - 5, self.data.High[-5])

    def _bullish_divergence(self, current_idx):
        """Check for bullish divergence: price lower low, RSI higher low"""
        if (self.last_swing_low is None or current_idx - self.last_swing_low[0] < 3 or
            current_idx < 15):
            return False
            
        # Price made lower low
        price_lower_low = self.data.Low[-1] < self.last_swing_low[1]
        
        # RSI made higher low
        current_rsi_low = min(self.rsi[-5:])
        previous_rsi_low = min(self.rsi[self.last_swing_low[0]-2:self.last_swing_low[0]+2])
        rsi_higher_low = current_rsi_low > previous_rsi_low
        
        if price_lower_low and rsi_higher_low:
            print(f"🚀 BULLISH DIVERGENCE DETECTED! Price: {self.data.Low[-1]:.2f} < {self.last_swing_low[1]:.2f}, RSI: {current_rsi_low:.2f} > {previous_rsi_low:.2f}")
            return True
        return False

    def _bearish_divergence(self, current_idx):
        """Check for bearish divergence: price higher high, RSI lower high"""
        if (self.last_swing_high is None or current_idx - self.last_swing_high[0] < 3 or
            current_idx < 15):
            return False
            
        # Price made higher high
        price_higher_high = self.data.High[-1] > self.last_swing_high[1]
        
        # RSI made lower high
        current_rsi_high = max(self.rsi[-5:])
        previous_rsi_high = max(self.rsi[self.last_swing_high[0]-2:self.last_swing_high[0]+2])
        rsi_lower_high = current_rsi_high < previous_rsi_high
        
        if price_higher_high and rsi_lower_high:
            print(f"📉 BEARISH DIVERGENCE DETECTED! Price: {self.data.High[-1]:.2f} > {self.last_swing_high[1]:.2f}, RSI: {current_rsi_high:.2f} < {previous_rsi_high:.2f}")
            return True
        return False

    def _macd_bullish_confirmation(self, current_idx):
        """MACD confirmation for bullish signals"""
        if current_idx < 2:
            return False
            
        macd_hist_positive = self.macd_hist[-1] > 0 and self.macd_hist[-2] > 0
        macd_rising = self.macd_hist[-1] > self.macd_hist[-2]
        macd_above_signal = self.macd[-1] > self.macd_signal_line[-1]
        
        bullish_confirmation = (macd_hist_positive and macd_rising) or macd_above_signal
        
        if bullish_confirmation:
            print("✨ MACD Bullish Confirmation - Green light for LONG! 🟢")
            
        return bullish_confirmation

    def _macd_bearish_confirmation(self, current_idx):
        """MACD confirmation for bearish signals"""
        if current_idx < 2:
            return False
            
        macd_hist_negative = self.macd_hist[-1] < 0 and self.macd_hist[-2] < 0
        macd_falling = self.macd_hist[-1] < self.macd_hist[-2]
        macd_below_signal = self.macd[-1] < self.macd_signal_line[-1]
        
        bearish_confirmation = (macd_hist_negative and macd_falling) or macd_below_signal
        
        if bearish_confirmation:
            print("✨ MACD Bearish Confirmation - Red light for SHORT! 🔴")
            
        return bearish_confirmation

    def _enter_long(self, current_close, current_idx):
        """Execute long entry with proper risk management"""
        if self.last_swing_low is None:
            return
            
        stop_loss_price = self.last_swing_low[1]
        risk_per_share = current_close - stop_loss_price
        
        if risk_per_share <= 0:
            print("❌ Invalid stop loss for long position")
            return
            
        # Calculate position size based on 2% risk
        risk_amount = self.equity * self.risk_per_trade
        position_size = risk_amount / risk_per_share
        
        # Ensure position size is integer
        position_size = int(round(position_size))
        
        if position_size > 0:
            # Calculate take profit for 1:2 risk-reward
            take_profit_price = current_close + (2 * risk_per_share)
            
            print(f"🌙 MOON DEV LONG ENTRY! 🚀")
            print(f"   Entry: {current_close:.2f}, Stop: {stop_loss_price:.2f}, Target: {take_profit_price:.2f}")
            print(f"   Position Size: {position_size} shares, Risk: ${risk_amount:.2f}")
            
            self.buy(size=position_size, sl=stop_loss_price, tp=take_profit_price)
            self.active_positions += 1

    def _enter_short(self, current_close, current_idx):
        """Execute short entry with proper risk management"""
        if self.last_swing_high is None:
            return
            
        stop_loss_price = self.last_swing_high[1]
        risk_per_share = stop_loss_price - current_close
        
        if risk_per_share <= 0:
            print("❌ Invalid stop loss for short position")
            return
            
        # Calculate position size based on 2% risk
        risk_amount = self.equity * self.risk_per_trade
        position_size = risk_amount / risk_per_share
        
        # Ensure position size is integer
        position_size = int(round(position_size))
        
        if position_size > 0:
            # Calculate take profit for 1:2 risk-reward
            take_profit_price = current_close - (2 * risk_per_share)
            
            print(f"🌙 MOON DEV SHORT ENTRY! 📉")
            print(f"   Entry: {current_close:.2f}, Stop: {stop_loss_price:.2f}, Target: {take_profit_price:.2f}")
            print(f"   Position Size: {position_size} shares, Risk: ${risk_amount:.2f}")
            
            self.sell(size=position_size, sl=stop_loss_price, tp=take_profit_price)
            self.active_positions += 1

    def _check_exits(self, current_idx, current_rsi, current_macd_hist):
        """Check exit conditions for existing positions"""
        for trade in self.trades:
            if trade.is_long:
                # Long exit conditions
                rsi_exit = current_rsi >= 70
                macd_exit = (current_idx >= 2 and 
                            self.macd_hist[-1] < 0 and 
                            self.macd_hist[-2] < 0)
                
                if rsi_exit or macd_exit:
                    reason = "RSI Overbought" if rsi_exit else "MACD Turned Negative"
                    print(f"🌙 LONG EXIT SIGNAL! {reason} - RSI: {current_rsi:.2f}")
                    trade.close()
                    self.active_positions = max(0, self.active_positions - 1)
                    
            elif trade.is_short:
                # Short exit conditions
                rsi_exit = current_rsi <= 30
                macd_exit = (current_idx >= 2 and 
                            self.macd_hist[-1] > 0 and 
                            self.macd_hist[-2] > 0)
                
                if rsi_exit or macd_exit:
                    reason = "RSI Oversold" if rsi_exit else "MACD Turned Positive"
                    print(f"🌙 SHORT EXIT SIGNAL! {reason} - RSI: {current_rsi:.2f}")
                    trade.close()
                    self.active_positions = max(0, self.active_positions - 1)

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

# Rename columns to match backtesting.py requirements
data = data.rename(columns=column_mapping)

# Convert datetime column if present
if 'datetime' in data.columns:
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')

print("🌙 Loading BTC Data for Divergence Strategy Backtest...")
print(f"📊 Data shape: {data.shape}")
print(f"📈 Columns: {data.columns.tolist()}")

# Run backtest
bt = Backtest(data, DivergenceConfirmation, cash=1000000, commission=.002)

print("🚀 Starting Moon Dev Divergence Backtest...")
stats = bt.run()
print(stats)
print(stats._strategy)