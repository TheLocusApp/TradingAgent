import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import talib
import yfinance as yf

class DivergenceConfirm(Strategy):
    # Strategy parameters
    rsi_period = 14
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    risk_per_trade = 0.02
    rsi_overbought = 70
    rsi_oversold = 30
    
    def init(self):
        # Calculate indicators using self.I() wrapper
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.macd, self.macd_signal_line, self.macd_hist = self.I(
            talib.MACD, self.data.Close, 
            fastperiod=self.macd_fast, 
            slowperiod=self.macd_slow, 
            signalperiod=self.macd_signal
        )
        
        # Calculate swing highs/lows for divergence detection
        self.swing_high = self.I(talib.MAX, self.data.High, timeperiod=5)
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=5)
        
        # Track previous values for divergence detection
        self.price_highs = []
        self.price_lows = []
        self.rsi_highs = []
        self.rsi_lows = []
        
        print("🌙 Moon Dev DivergenceConfirm Strategy Initialized!")
        print(f"✨ RSI Period: {self.rsi_period}")
        print(f"✨ MACD Settings: {self.macd_fast},{self.macd_slow},{self.macd_signal}")
        print(f"✨ Risk per Trade: {self.risk_per_trade*100}%")

    def next(self):
        current_bar = len(self.data) - 1
        if current_bar < 20:  # Need enough data for reliable signals
            return
            
        # Get current values
        current_close = self.data.Close[-1]
        current_rsi = self.rsi[-1] if self.rsi[-1] is not None else 50
        current_macd = self.macd[-1] if self.macd[-1] is not None else 0
        current_macd_signal = self.macd_signal_line[-1] if self.macd_signal_line[-1] is not None else 0
        current_macd_hist = self.macd_hist[-1] if self.macd_hist[-1] is not None else 0
        
        # Update swing detection arrays
        self._update_swing_points(current_bar)
        
        # Check for existing positions
        if not self.position:
            self._check_entries(current_bar)
        else:
            self._manage_exits(current_bar)

    def _update_swing_points(self, current_bar):
        # Update price swing highs
        if len(self.price_highs) < 2:
            self.price_highs.append((current_bar, self.data.High[-1]))
            self.price_lows.append((current_bar, self.data.Low[-1]))
            self.rsi_highs.append((current_bar, self.rsi[-1] if self.rsi[-1] is not None else 50))
            self.rsi_lows.append((current_bar, self.rsi[-1] if self.rsi[-1] is not None else 50))
        else:
            # Keep only last 3 swing points for divergence detection
            if len(self.price_highs) > 3:
                self.price_highs.pop(0)
                self.price_lows.pop(0)
                self.rsi_highs.pop(0)
                self.rsi_lows.pop(0)
            
            # Add new swing points when detected
            if len(self.swing_high) > 0 and self.swing_high[-1] == self.data.High[-1]:
                self.price_highs.append((current_bar, self.data.High[-1]))
                self.rsi_highs.append((current_bar, self.rsi[-1] if self.rsi[-1] is not None else 50))
                
            if len(self.swing_low) > 0 and self.swing_low[-1] == self.data.Low[-1]:
                self.price_lows.append((current_bar, self.data.Low[-1]))
                self.rsi_lows.append((current_bar, self.rsi[-1] if self.rsi[-1] is not None else 50))

    def _check_entries(self, current_bar):
        # Check for bullish divergence (long entry)
        if self._detect_bullish_divergence():
            if self._macd_bullish_confirmation():
                self._enter_long(current_bar)
        
        # Check for bearish divergence (short entry)
        elif self._detect_bearish_divergence():
            if self._macd_bearish_confirmation():
                self._enter_short(current_bar)

    def _detect_bullish_divergence(self):
        if len(self.price_lows) < 2 or len(self.rsi_lows) < 2:
            return False
            
        # Price makes lower low, RSI makes higher low
        price_low1, price_low2 = self.price_lows[-2][1], self.price_lows[-1][1]
        rsi_low1, rsi_low2 = self.rsi_lows[-2][1], self.rsi_lows[-1][1]
        
        bullish_div = (price_low2 < price_low1) and (rsi_low2 > rsi_low1)
        
        if bullish_div:
            print(f"🚀 BULLISH DIVERGENCE DETECTED! Price: {price_low2:.2f} < {price_low1:.2f}, RSI: {rsi_low2:.1f} > {rsi_low1:.1f}")
        
        return bullish_div

    def _detect_bearish_divergence(self):
        if len(self.price_highs) < 2 or len(self.rsi_highs) < 2:
            return False
            
        # Price makes higher high, RSI makes lower high
        price_high1, price_high2 = self.price_highs[-2][1], self.price_highs[-1][1]
        rsi_high1, rsi_high2 = self.rsi_highs[-2][1], self.rsi_highs[-1][1]
        
        bearish_div = (price_high2 > price_high1) and (rsi_high2 < rsi_high1)
        
        if bearish_div:
            print(f"📉 BEARISH DIVERGENCE DETECTED! Price: {price_high2:.2f} > {price_high1:.2f}, RSI: {rsi_high2:.1f} < {rsi_high1:.1f}")
        
        return bearish_div

    def _macd_bullish_confirmation(self):
        if len(self.macd) < 2 or len(self.macd_signal_line) < 2:
            return False
            
        current_macd = self.macd[-1] if self.macd[-1] is not None else 0
        current_macd_signal = self.macd_signal_line[-1] if self.macd_signal_line[-1] is not None else 0
        current_macd_hist = self.macd_hist[-1] if self.macd_hist[-1] is not None else 0
        prev_macd_hist = self.macd_hist[-2] if len(self.macd_hist) > 1 and self.macd_hist[-2] is not None else 0
        
        # MACD line crosses above signal line OR histogram turns positive
        prev_macd = self.macd[-2] if self.macd[-2] is not None else 0
        prev_macd_signal = self.macd_signal_line[-2] if self.macd_signal_line[-2] is not None else 0
        
        macd_cross = (current_macd > current_macd_signal) and (prev_macd <= prev_macd_signal)
        hist_turn = (current_macd_hist > 0) and (prev_macd_hist <= 0)
        
        confirmation = macd_cross or hist_turn
        
        if confirmation:
            print(f"✅ MACD BULLISH CONFIRMATION: Cross={macd_cross}, Histogram={hist_turn}")
        
        return confirmation

    def _macd_bearish_confirmation(self):
        if len(self.macd) < 2 or len(self.macd_signal_line) < 2:
            return False
            
        current_macd = self.macd[-1] if self.macd[-1] is not None else 0
        current_macd_signal = self.macd_signal_line[-1] if self.macd_signal_line[-1] is not None else 0
        current_macd_hist = self.macd_hist[-1] if self.macd_hist[-1] is not None else 0
        prev_macd_hist = self.macd_hist[-2] if len(self.macd_hist) > 1 and self.macd_hist[-2] is not None else 0
        
        # MACD line crosses below signal line OR histogram turns negative
        prev_macd = self.macd[-2] if self.macd[-2] is not None else 0
        prev_macd_signal = self.macd_signal_line[-2] if self.macd_signal_line[-2] is not None else 0
        
        macd_cross = (current_macd < current_macd_signal) and (prev_macd >= prev_macd_signal)
        hist_turn = (current_macd_hist < 0) and (prev_macd_hist >= 0)
        
        confirmation = macd_cross or hist_turn
        
        if confirmation:
            print(f"✅ MACD BEARISH CONFIRMATION: Cross={macd_cross}, Histogram={hist_turn}")
        
        return confirmation

    def _enter_long(self, current_bar):
        if len(self.price_lows) < 2:
            print("❌ Not enough price lows for long entry")
            return
            
        entry_price = self.data.Close[-1]
        stop_loss = min(self.price_lows[-2][1], self.price_lows[-1][1])
        risk_per_share = entry_price - stop_loss
        
        if risk_per_share <= 0:
            print("❌ Invalid stop loss for long entry")
            return
            
        # Calculate position size with 2% risk
        risk_amount = self.equity * self.risk_per_trade
        position_size = risk_amount / risk_per_share
        position_size = int(round(position_size))
        
        if position_size > 0:
            take_profit = entry_price + (2 * risk_per_share)  # 2:1 reward:risk
            
            print(f"🌙 ENTERING LONG: {position_size} shares at ${entry_price:.2f}")
            print(f"🛡️  Stop Loss: ${stop_loss:.2f}")
            print(f"🎯 Take Profit: ${take_profit:.2f}")
            
            self.buy(size=position_size, sl=stop_loss, tp=take_profit)

    def _enter_short(self, current_bar):
        if len(self.price_highs) < 2:
            print("❌ Not enough price highs for short entry")
            return
            
        entry_price = self.data.Close[-1]
        stop_loss = max(self.price_highs[-2][1], self.price_highs[-1][1])
        risk_per_share = stop_loss - entry_price
        
        if risk_per_share <= 0:
            print("❌ Invalid stop loss for short entry")
            return
            
        # Calculate position size with 2% risk
        risk_amount = self.equity * self.risk_per_trade
        position_size = risk_amount / risk_per_share
        position_size = int(round(position_size))
        
        if position_size > 0:
            take_profit = entry_price - (2 * risk_per_share)  # 2:1 reward:risk
            
            print(f"🌙 ENTERING SHORT: {position_size} shares at ${entry_price:.2f}")
            print(f"🛡️  Stop Loss: ${stop_loss:.2f}")
            print(f"🎯 Take Profit: ${take_profit:.2f}")
            
            self.sell(size=position_size, sl=stop_loss, tp=take_profit)

    def _manage_exits(self, current_bar):
        if len(self.rsi) == 0:
            return
            
        current_rsi = self.rsi[-1] if self.rsi[-1] is not None else 50
        
        if self.position.is_long:
            # Exit long if RSI becomes overbought
            if current_rsi >= self.rsi_overbought:
                print(f"📊 EXIT LONG: RSI overbought at {current_rsi:.1f}")
                self.position.close()
                
        elif self.position.is_short:
            # Exit short if RSI becomes oversold
            if current_rsi <= self.rsi_oversold:
                print(f"📊 EXIT SHORT: RSI oversold at {current_rsi:.1f}")
                self.position.close()

# Load and prepare data using yfinance
def load_data():
    print("🌙 Fetching SPY data from yfinance...")
    
    # Fetch SPY data for the last 2 years with daily intervals
    ticker = yf.Ticker("SPY")
    data = ticker.history(period="2y", interval="1d")
    
    # Ensure we have data
    if data.empty:
        print("❌ No data fetched from yfinance!")
        return None
    
    # Clean and prepare data
    data = data.dropna()
    
    print("✨ SPY data fetched successfully from yfinance!")
    print(f"📈 Data shape: {data.shape}")
    print(f"📅 Date range: {data.index.min()} to {data.index.max()}")
    print(f"💰 Price range: ${data['Low'].min():.2f} - ${data['High'].max():.2f}")
    
    return data

# Run backtest
if __name__ == "__main__":
    # Load data
    data = load_data()
    
    if data is not None:
        # Initialize backtest with $1,000,000 capital
        bt = Backtest(data, DivergenceConfirm, cash=1000000, commission=.002)
        
        print("🚀 Starting Moon Dev DivergenceConfirm Backtest...")
        print("✨ Strategy: RSI Divergence + MACD Confirmation")
        print("💰 Initial Capital: $1,000,000")
        print("📊 Data Source: yfinance (SPY Daily)")
        
        # Run backtest
        stats = bt.run()
        
        # Print full statistics
        print("\n" + "="*80)
        print("🌙 MOON DEV BACKTEST RESULTS - DIVERGENCE CONFIRM STRATEGY")
        print("="*80)
        print(stats)
        print("\n" + "="*80)
        print("📊 STRATEGY DETAILS")
        print("="*80)
        print(stats._strategy)
    else:
        print("❌ Failed to load data. Backtest aborted.")