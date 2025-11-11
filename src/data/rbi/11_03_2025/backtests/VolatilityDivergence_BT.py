import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
import yfinance as yf

class VolatilityDivergence(Strategy):
    # Strategy parameters
    bb_period = 20
    bb_std = 2
    rsi_period = 14
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    atr_period = 14
    risk_per_trade = 0.01
    max_risk = 0.02
    max_daily_dd = 0.05
    
    def init(self):
        # Clean data and ensure float64 for TA-Lib
        close_data = self.data.Close.astype(float)
        high_data = self.data.High.astype(float)
        low_data = self.data.Low.astype(float)
        volume_data = self.data.Volume.astype(float)
        
        # Calculate indicators using self.I() wrapper
        self.bb_upper = self.I(talib.BBANDS, close_data, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std, matype=0)[0]
        self.bb_middle = self.I(talib.BBANDS, close_data, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std, matype=0)[1]
        self.bb_lower = self.I(talib.BBANDS, close_data, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std, matype=0)[2]
        self.bb_width = self.I(lambda x: (self.bb_upper - self.bb_lower) / self.bb_middle)
        self.bb_width_avg = self.I(talib.SMA, self.bb_width, timeperiod=20)
        
        self.rsi = self.I(talib.RSI, close_data, timeperiod=self.rsi_period)
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, close_data, fastperiod=self.macd_fast, slowperiod=self.macd_slow, signalperiod=self.macd_signal)
        self.atr = self.I(talib.ATR, high_data, low_data, close_data, timeperiod=self.atr_period)
        
        # Track variables for divergence detection
        self.price_highs = []
        self.price_lows = []
        self.rsi_highs = []
        self.rsi_lows = []
        self.macd_hist_highs = []
        self.macd_hist_lows = []
        
        # Risk management tracking
        self.entry_price = None
        self.consecutive_losses = 0
        self.last_trade_day = None
        
        print("🌙 Moon Dev Volatility Divergence Strategy Initialized! ✨")

    def next(self):
        current_idx = len(self.data) - 1
        if current_idx < max(self.bb_period, self.rsi_period, self.macd_slow, self.atr_period):
            return
            
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_time = self.data.index[-1]
        
        # Update swing points for divergence detection
        self.update_swing_points(current_high, current_low, self.rsi[-1], self.macd_hist[-1])
        
        # Check if we should avoid trading (first/last hour)
        if self.should_avoid_trading(current_time):
            return
            
        # Check risk management conditions
        if not self.check_risk_management():
            return
            
        # Check volatility filter
        if not self.check_volatility_filter():
            return
            
        # Main trading logic
        if not self.position:
            self.check_entries(current_close, current_time)
        else:
            self.check_exits(current_close)

    def update_swing_points(self, high, low, rsi, macd_hist):
        # Update price highs/lows (5-period lookback)
        lookback = 5
        
        if len(self.data.Close) > lookback:
            # Price highs
            if high == max([self.data.High[-i] for i in range(1, lookback+1)]):
                self.price_highs.append((len(self.data)-1, high))
                if len(self.price_highs) > 10:
                    self.price_highs.pop(0)
            
            # Price lows
            if low == min([self.data.Low[-i] for i in range(1, lookback+1)]):
                self.price_lows.append((len(self.data)-1, low))
                if len(self.price_lows) > 10:
                    self.price_lows.pop(0)
            
            # RSI highs/lows
            if len(self.rsi) > lookback:
                if rsi == max([self.rsi[-i] for i in range(1, lookback+1)]):
                    self.rsi_highs.append((len(self.data)-1, rsi))
                    if len(self.rsi_highs) > 10:
                        self.rsi_highs.pop(0)
                
                if rsi == min([self.rsi[-i] for i in range(1, lookback+1)]):
                    self.rsi_lows.append((len(self.data)-1, rsi))
                    if len(self.rsi_lows) > 10:
                        self.rsi_lows.pop(0)
            
            # MACD histogram highs/lows
            if len(self.macd_hist) > lookback:
                if macd_hist == max([self.macd_hist[-i] for i in range(1, lookback+1)]):
                    self.macd_hist_highs.append((len(self.data)-1, macd_hist))
                    if len(self.macd_hist_highs) > 10:
                        self.macd_hist_highs.pop(0)
                
                if macd_hist == min([self.macd_hist[-i] for i in range(1, lookback+1)]):
                    self.macd_hist_lows.append((len(self.data)-1, macd_hist))
                    if len(self.macd_hist_lows) > 10:
                        self.macd_hist_lows.pop(0)

    def should_avoid_trading(self, current_time):
        # Avoid first and last hour of trading session
        hour = current_time.hour
        if hour in [9, 15]:  # Assuming 9AM-4PM trading hours
            return True
        return False

    def check_risk_management(self):
        # Check maximum daily drawdown
        if self.equity < 1000000 * (1 - self.max_daily_dd):
            print("🚨 Moon Dev Alert: Maximum daily drawdown reached! No new trades today. 🌙")
            return False
            
        # Check consecutive losses
        if self.consecutive_losses >= 3:
            print("🚨 Moon Dev Alert: 3 consecutive losses! Cooling off period activated. 🌙")
            return False
            
        return True

    def check_volatility_filter(self):
        # Trade only during high volatility periods
        if self.bb_width[-1] > self.bb_width_avg[-1]:
            return True
        return False

    def detect_bullish_divergence(self):
        if len(self.price_lows) >= 2 and len(self.rsi_lows) >= 2 and len(self.macd_hist_lows) >= 2:
            # Check price making lower low but RSI making higher low
            price_low1, price_low2 = self.price_lows[-2][1], self.price_lows[-1][1]
            rsi_low1, rsi_low2 = self.rsi_lows[-2][1], self.rsi_lows[-1][1]
            macd_low1, macd_low2 = self.macd_hist_lows[-2][1], self.macd_hist_lows[-1][1]
            
            if (price_low2 < price_low1 and 
                rsi_low2 > rsi_low1 and 
                macd_low2 > macd_low1):
                return True
        return False

    def detect_bearish_divergence(self):
        if len(self.price_highs) >= 2 and len(self.rsi_highs) >= 2 and len(self.macd_hist_highs) >= 2:
            # Check price making higher high but RSI making lower high
            price_high1, price_high2 = self.price_highs[-2][1], self.price_highs[-1][1]
            rsi_high1, rsi_high2 = self.rsi_highs[-2][1], self.rsi_highs[-1][1]
            macd_high1, macd_high2 = self.macd_hist_highs[-2][1], self.macd_hist_highs[-1][1]
            
            if (price_high2 > price_high1 and 
                rsi_high2 < rsi_high1 and 
                macd_high2 < macd_high1):
                return True
        return False

    def check_entries(self, current_close, current_time):
        # Long entry conditions
        long_conditions = (
            current_close <= self.bb_lower[-1] and
            self.detect_bullish_divergence() and
            self.macd_hist[-1] > self.macd_hist[-2] and  # MACD histogram improving
            self.bb_width[-1] > self.bb_width_avg[-1]    # Volatility expansion
        )
        
        # Short entry conditions
        short_conditions = (
            current_close >= self.bb_upper[-1] and
            self.detect_bearish_divergence() and
            self.macd_hist[-1] < self.macd_hist[-2] and  # MACD histogram deteriorating
            self.bb_width[-1] > self.bb_width_avg[-1]    # Volatility expansion
        )
        
        if long_conditions:
            self.enter_long(current_close, current_time)
        elif short_conditions:
            self.enter_short(current_close, current_time)

    def enter_long(self, current_close, current_time):
        # Calculate position size based on ATR risk
        atr_value = self.atr[-1]
        stop_distance = 2 * atr_value
        risk_amount = min(self.risk_per_trade * self.equity, self.max_risk * self.equity)
        
        position_size = risk_amount / stop_distance
        position_size = int(round(position_size))
        
        if position_size > 0:
            stop_price = current_close - stop_distance
            target_price = current_close + (2 * stop_distance)  # 2:1 reward:risk
            
            self.buy(size=position_size, sl=stop_price, tp=target_price)
            self.entry_price = current_close
            print(f"🌙 MOON DEV LONG SIGNAL! 🚀 | Entry: {current_close:.2f} | Size: {position_size} | SL: {stop_price:.2f} | TP: {target_price:.2f}")

    def enter_short(self, current_close, current_time):
        # Calculate position size based on ATR risk
        atr_value = self.atr[-1]
        stop_distance = 2 * atr_value
        risk_amount = min(self.risk_per_trade * self.equity, self.max_risk * self.equity)
        
        position_size = risk_amount / stop_distance
        position_size = int(round(position_size))
        
        if position_size > 0:
            stop_price = current_close + stop_distance
            target_price = current_close - (2 * stop_distance)  # 2:1 reward:risk
            
            self.sell(size=position_size, sl=stop_price, tp=target_price)
            self.entry_price = current_close
            print(f"🌙 MOON DEV SHORT SIGNAL! 📉 | Entry: {current_close:.2f} | Size: {position_size} | SL: {stop_price:.2f} | TP: {target_price:.2f}")

    def check_exits(self, current_close):
        if self.position.is_long:
            # Long exit conditions
            exit_conditions = (
                current_close >= self.bb_middle[-1] or
                self.rsi[-1] >= 70 or
                self.detect_bearish_divergence()
            )
            
            if exit_conditions:
                self.position.close()
                print(f"🌙 MOON DEV LONG EXIT! ✅ | Exit: {current_close:.2f} | P/L: {self.position.pl:.2f}")
                
        elif self.position.is_short:
            # Short exit conditions
            exit_conditions = (
                current_close <= self.bb_middle[-1] or
                self.rsi[-1] <= 30 or
                self.detect_bullish_divergence()
            )
            
            if exit_conditions:
                self.position.close()
                print(f"🌙 MOON DEV SHORT EXIT! ✅ | Exit: {current_close:.2f} | P/L: {self.position.pl:.2f}")

# Download data and run backtest
ticker = yf.Ticker("SPY")
data = ticker.history(period="730d", interval="1h")

# Reset index and clean columns
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

# Run backtest
bt = Backtest(data, VolatilityDivergence, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)