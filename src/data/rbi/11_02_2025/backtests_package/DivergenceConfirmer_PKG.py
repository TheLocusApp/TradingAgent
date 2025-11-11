import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import talib

class DivergenceConfirmer(Strategy):
    rsi_period = 14
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    risk_per_trade = 0.02
    max_trade_duration = 24
    
    def init(self):
        # Clean and prepare data
        self.data.df.columns = self.data.df.columns.str.strip().str.lower()
        self.data.df = self.data.df.drop(columns=[col for col in self.data.df.columns if 'unnamed' in col.lower()])
        
        # Calculate indicators using self.I() wrapper
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.macd, self.macd_signal_line, self.macd_hist = self.I(talib.MACD, self.data.Close, 
                                                                  fastperiod=self.macd_fast, 
                                                                  slowperiod=self.macd_slow, 
                                                                  signalperiod=self.macd_signal)
        
        # Calculate swing highs and lows for divergence detection
        self.swing_high = self.I(talib.MAX, self.data.High, timeperiod=5)
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=5)
        
        # Track trade entry time
        self.entry_time = None
        self.position_size = 0
        
        print("🌙 Moon Dev Divergence Confirmer Strategy Initialized! ✨")

    def next(self):
        current_bar = len(self.data) - 1
        if current_bar < 50:  # Need enough data for reliable indicators
            return
            
        # Check if we're in a trade and manage exits
        if self.position:
            self.manage_exit(current_bar)
            return
            
        # Look for new entry signals
        self.check_entries(current_bar)

    def check_entries(self, current_bar):
        price = self.data.Close[current_bar]
        rsi = self.rsi[current_bar]
        
        # Check for bullish divergence
        bullish_div = self.detect_bullish_divergence(current_bar)
        if bullish_div:
            macd_bullish = self.macd[current_bar] > self.macd_signal_line[current_bar]
            macd_hist_rising = (self.macd_hist[current_bar] > self.macd_hist[current_bar-1] and 
                              self.macd_hist[current_bar-1] > self.macd_hist[current_bar-2])
            
            if macd_bullish and macd_hist_rising:
                swing_high_break = price > self.swing_high[current_bar-1]
                if swing_high_break:
                    self.enter_long(current_bar)
        
        # Check for bearish divergence
        bearish_div = self.detect_bearish_divergence(current_bar)
        if bearish_div:
            macd_bearish = self.macd[current_bar] < self.macd_signal_line[current_bar]
            macd_hist_falling = (self.macd_hist[current_bar] < self.macd_hist[current_bar-1] and 
                               self.macd_hist[current_bar-1] < self.macd_hist[current_bar-2])
            
            if macd_bearish and macd_hist_falling:
                swing_low_break = price < self.swing_low[current_bar-1]
                if swing_low_break:
                    self.enter_short(current_bar)

    def detect_bullish_divergence(self, current_bar):
        # Look for lower lows in price but higher lows in RSI
        lookback = 20
        if current_bar < lookback:
            return False
            
        price_lows = [self.data.Low[i] for i in range(current_bar-lookback, current_bar+1)]
        rsi_lows = [self.rsi[i] for i in range(current_bar-lookback, current_bar+1)]
        
        # Find significant lows in price and RSI
        price_min_idx = np.argmin(price_lows)
        rsi_min_idx = np.argmin(rsi_lows)
        
        # Bullish divergence: price makes lower low but RSI makes higher low
        if price_min_idx > len(price_lows)//2 and rsi_min_idx < len(rsi_lows)//2:
            if price_lows[price_min_idx] < price_lows[price_min_idx-1] and rsi_lows[rsi_min_idx] > rsi_lows[rsi_min_idx-1]:
                print(f"🚀 Moon Dev Bullish Divergence Detected! Price: {price_lows[price_min_idx]:.2f}, RSI: {rsi_lows[rsi_min_idx]:.2f}")
                return True
        return False

    def detect_bearish_divergence(self, current_bar):
        # Look for higher highs in price but lower highs in RSI
        lookback = 20
        if current_bar < lookback:
            return False
            
        price_highs = [self.data.High[i] for i in range(current_bar-lookback, current_bar+1)]
        rsi_highs = [self.rsi[i] for i in range(current_bar-lookback, current_bar+1)]
        
        # Find significant highs in price and RSI
        price_max_idx = np.argmax(price_highs)
        rsi_max_idx = np.argmax(rsi_highs)
        
        # Bearish divergence: price makes higher high but RSI makes lower high
        if price_max_idx > len(price_highs)//2 and rsi_max_idx < len(rsi_highs)//2:
            if price_highs[price_max_idx] > price_highs[price_max_idx-1] and rsi_highs[rsi_max_idx] < rsi_highs[rsi_max_idx-1]:
                print(f"🌙 Moon Dev Bearish Divergence Detected! Price: {price_highs[price_max_idx]:.2f}, RSI: {rsi_highs[rsi_max_idx]:.2f}")
                return True
        return False

    def enter_long(self, current_bar):
        entry_price = self.data.Close[current_bar]
        stop_loss = self.swing_low[current_bar-1]
        risk = entry_price - stop_loss
        
        if risk <= 0:
            return
            
        # Calculate position size based on 2% risk
        risk_amount = self.equity * self.risk_per_trade
        position_size = risk_amount / risk
        position_size = int(round(position_size))
        
        if position_size > 0:
            take_profit = entry_price + (2 * risk)  # 1:2 risk-reward
            self.buy(size=position_size, sl=stop_loss, tp=take_profit)
            self.entry_time = current_bar
            print(f"✨ Moon Dev LONG Entry! Size: {position_size}, Entry: {entry_price:.2f}, SL: {stop_loss:.2f}, TP: {take_profit:.2f}")

    def enter_short(self, current_bar):
        entry_price = self.data.Close[current_bar]
        stop_loss = self.swing_high[current_bar-1]
        risk = stop_loss - entry_price
        
        if risk <= 0:
            return
            
        # Calculate position size based on 2% risk
        risk_amount = self.equity * self.risk_per_trade
        position_size = risk_amount / risk
        position_size = int(round(position_size))
        
        if position_size > 0:
            take_profit = entry_price - (2 * risk)  # 1:2 risk-reward
            self.sell(size=position_size, sl=stop_loss, tp=take_profit)
            self.entry_time = current_bar
            print(f"🌙 Moon Dev SHORT Entry! Size: {position_size}, Entry: {entry_price:.2f}, SL: {stop_loss:.2f}, TP: {take_profit:.2f}")

    def manage_exit(self, current_bar):
        # Check maximum trade duration (24 bars for hourly data)
        if self.entry_time and (current_bar - self.entry_time) >= self.max_trade_duration:
            self.position.close()
            print("⏰ Moon Dev Trade Closed - Maximum Duration Reached!")
            return
            
        # Check RSI exit conditions
        current_rsi = self.rsi[current_bar]
        
        if self.position.is_long and current_rsi >= 70:
            self.position.close()
            print(f"🎯 Moon Dev LONG Exit - RSI Overbought: {current_rsi:.2f}")
        elif self.position.is_short and current_rsi <= 30:
            self.position.close()
            print(f"🎯 Moon Dev SHORT Exit - RSI Oversold: {current_rsi:.2f}")
        
        # Check MACD reversal
        if len(self.data) > 3:
            if self.position.is_long and (self.macd_hist[current_bar] < self.macd_hist[current_bar-1] and 
                                        self.macd_hist[current_bar-1] < self.macd_hist[current_bar-2]):
                self.position.close()
                print("📉 Moon Dev LONG Exit - MACD Histogram Reversal")
            elif self.position.is_short and (self.macd_hist[current_bar] > self.macd_hist[current_bar-1] and 
                                           self.macd_hist[current_bar-1] > self.macd_hist[current_bar-2]):
                self.position.close()
                print("📈 Moon Dev SHORT Exit - MACD Histogram Reversal")

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
data['DateTime'] = pd.to_datetime(data['datetime'])
data = data.set_index('DateTime')

print("🌙 Moon Dev Backtest Starting...")
print(f"Dataset shape: {data.shape}")
print(f"Columns: {data.columns.tolist()}")

# Run backtest
bt = Backtest(data, DivergenceConfirmer, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)