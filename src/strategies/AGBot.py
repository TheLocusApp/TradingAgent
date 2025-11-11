from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np
from datetime import time

class AGBotStrategy(Strategy):
    """
    AG Bot Trading Strategy adapted for backtesting.py
    """
    
    # Strategy parameters (optimizable)
    ma_length = 200
    key_value = 3.0
    atr_period = 1
    adaptive_atr_mult = 1.5
    
    # Risk management
    risk_per_trade = 2.5
    stoploss_type = "atr"  # "atr" or "swing"
    swing_high_bars = 10
    swing_low_bars = 10
    
    # Take profit settings
    use_takeprofit = True
    num_take_profits = 2
    second_tp_type = "atr_trailing"  # "rr" or "atr_trailing"
    tp1_rr_long = 1.0
    tp2_rr_long = 3.0
    tp1_rr_short = 1.0
    tp2_rr_short = 3.0
    tp1_percent = 30.0
    
    # Position management
    long_positions = True
    short_positions = True
    
    # Session settings
    session_start_hour = 9
    session_start_minute = 30
    session_end_hour = 16
    session_end_minute = 0
    enable_eod_close = True
    
    def init(self):
        """Initialize indicators"""
        # Cache price data
        price = self.data.Close
        high = self.data.High
        low = self.data.Low
        
        # Calculate EMA for trend filter
        self.ema = self.I(self.calculate_ema, price, self.ma_length, name='EMA')
        
        # Calculate ATR
        self.atr = self.I(self.calculate_atr, high, low, price, 14, name='ATR')
        self.smoothed_atr = self.I(self.calculate_sma, self.atr, 14, name='Smoothed_ATR')
        
        # Calculate UT Bot components
        ut_bot_results = self.I(
            self.calculate_ut_bot, 
            high, low, price, 
            self.key_value, 
            self.atr_period,
            name='UT_Bot',
            overlay=False
        )
        
        # Unpack UT Bot results (returns tuple)
        self.xATRTrailingStop = ut_bot_results
        
        # Calculate stop loss levels
        if self.stoploss_type == "atr":
            self.long_stop = self.I(
                lambda: price - (self.atr * self.adaptive_atr_mult),
                name='Long_Stop'
            )
            self.short_stop = self.I(
                lambda: price + (self.atr * self.adaptive_atr_mult),
                name='Short_Stop'
            )
        else:
            self.long_stop = self.I(
                lambda: pd.Series(low).rolling(self.swing_low_bars).min().values,
                name='Long_Stop'
            )
            self.short_stop = self.I(
                lambda: pd.Series(high).rolling(self.swing_high_bars).max().values,
                name='Short_Stop'
            )
        
        # Track position state
        self.tp1_hit = False
        self.highest_since_entry = None
        self.lowest_since_entry = None
        self.entry_price = None
        self.initial_sl = None
    
    @staticmethod
    def calculate_ema(series, period):
        """Calculate EMA"""
        return pd.Series(series).ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_sma(series, period):
        """Calculate SMA"""
        return pd.Series(series).rolling(window=period).mean()
    
    @staticmethod
    def calculate_atr(high, low, close, period):
        """Calculate ATR"""
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)
        
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr.values
    
    @staticmethod
    def calculate_ut_bot(high, low, close, key_value, atr_period):
        """Calculate UT Bot ATR Trailing Stop"""
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)
        
        # Calculate ATR for UT Bot
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=atr_period).mean()
        
        n_loss = key_value * atr
        src = close
        
        # Calculate ATR Trailing Stop
        xATRTrailingStop = pd.Series(index=close.index, dtype=float)
        xATRTrailingStop.iloc[0] = src.iloc[0]
        
        for i in range(1, len(close)):
            prev_stop = xATRTrailingStop.iloc[i-1]
            
            if pd.isna(prev_stop):
                xATRTrailingStop.iloc[i] = src.iloc[i]
                continue
            
            if src.iloc[i] > prev_stop:
                xATRTrailingStop.iloc[i] = max(prev_stop, src.iloc[i] - n_loss.iloc[i])
            elif src.iloc[i] < prev_stop:
                xATRTrailingStop.iloc[i] = min(prev_stop, src.iloc[i] + n_loss.iloc[i])
            else:
                if src.iloc[i-1] > prev_stop:
                    xATRTrailingStop.iloc[i] = src.iloc[i] - n_loss.iloc[i]
                else:
                    xATRTrailingStop.iloc[i] = src.iloc[i] + n_loss.iloc[i]
        
        return xATRTrailingStop.values
    
    def in_session(self):
        """Check if current time is within trading session"""
        current_time = self.data.index[-1].time()
        start = time(self.session_start_hour, self.session_start_minute)
        end = time(self.session_end_hour, self.session_end_minute)
        return start <= current_time <= end
    
    def is_eod(self):
        """Check if it's end of day"""
        current_time = self.data.index[-1].time()
        end = time(self.session_end_hour, self.session_end_minute)
        return current_time >= end
    
    def calculate_position_size(self, entry_price, stop_loss, is_long):
        """Calculate position size based on risk"""
        if is_long:
            risk_distance = abs(entry_price - stop_loss) / entry_price
        else:
            risk_distance = abs(stop_loss - entry_price) / entry_price
        
        if risk_distance == 0:
            return 0
        
        # Calculate position size as fraction of equity
        risk_amount = self.equity * (self.risk_per_trade / 100)
        position_value = risk_amount / risk_distance
        
        # Convert to size (fraction of equity)
        size = position_value / self.equity
        
        # Cap at 1.0 (100% of equity) if not using leverage
        return min(size, 1.0)
    
    def next(self):
        """Strategy logic executed on each bar"""
        price = self.data.Close[-1]
        
        # Check session time
        if not self.in_session():
            return
        
        # Close positions at EOD
        if self.enable_eod_close and self.is_eod() and self.position:
            self.position.close()
            return
        
        # Get current indicator values
        ema_value = self.ema[-1]
        atr_trailing = self.xATRTrailingStop[-1]
        
        # Check for valid values
        if pd.isna(ema_value) or pd.isna(atr_trailing):
            return
        
        # Trend conditions
        bullish = price > ema_value
        bearish = price < ema_value
        
        # UT Bot signals
        buy_signal = (price > atr_trailing and 
                     len(self.data.Close) > 1 and 
                     self.data.Close[-2] <= self.xATRTrailingStop[-2])
        
        sell_signal = (price < atr_trailing and 
                      len(self.data.Close) > 1 and 
                      self.data.Close[-2] >= self.xATRTrailingStop[-2])
        
        # Manage existing positions
        if self.position:
            self.manage_position()
        
        # Entry logic
        if not self.position:
            # Long entry
            if buy_signal and bullish and self.long_positions:
                stop_loss = self.long_stop[-1]
                
                if pd.isna(stop_loss):
                    return
                
                # Calculate position size
                size = self.calculate_position_size(price, stop_loss, True)
                
                if size > 0:
                    # Enter long position
                    self.buy(size=size, sl=stop_loss)
                    
                    # Store entry details
                    self.entry_price = price
                    self.initial_sl = stop_loss
                    self.tp1_hit = False
                    self.highest_since_entry = self.data.High[-1]
                    
                    # Calculate take profits
                    if self.use_takeprofit:
                        sl_distance = price - stop_loss
                        tp1 = price + (sl_distance * self.tp1_rr_long)
                        
                        if self.num_take_profits == 2 and self.second_tp_type == "rr":
                            tp2 = price + (sl_distance * self.tp2_rr_long)
                            # Note: backtesting.py doesn't support multiple TPs natively
                            # You'll need to manage this manually in manage_position
            
            # Short entry
            elif sell_signal and bearish and self.short_positions:
                stop_loss = self.short_stop[-1]
                
                if pd.isna(stop_loss):
                    return
                
                # Calculate position size
                size = self.calculate_position_size(price, stop_loss, False)
                
                if size > 0:
                    # Enter short position
                    self.sell(size=size, sl=stop_loss)
                    
                    # Store entry details
                    self.entry_price = price
                    self.initial_sl = stop_loss
                    self.tp1_hit = False
                    self.lowest_since_entry = self.data.Low[-1]
                    
                    # Calculate take profits
                    if self.use_takeprofit:
                        sl_distance = stop_loss - price
                        tp1 = price - (sl_distance * self.tp1_rr_short)
    
    def manage_position(self):
        """Manage existing position - handle TPs and trailing stops"""
        if not self.position:
            return
        
        price = self.data.Close[-1]
        high = self.data.High[-1]
        low = self.data.Low[-1]
        
        # Long position management
        if self.position.is_long:
            # Update highest high for trailing
            if self.highest_since_entry is not None:
                self.highest_since_entry = max(self.highest_since_entry, high)
            
            # Check for TP1
            if not self.tp1_hit and self.use_takeprofit and self.entry_price:
                sl_distance = self.entry_price - self.initial_sl
                tp1 = self.entry_price + (sl_distance * self.tp1_rr_long)
                
                if high >= tp1:
                    # Partially close at TP1 (close() expects fraction 0-1)
                    fraction = self.tp1_percent / 100
                    if fraction > 0:
                        self.position.close(fraction)
                        self.tp1_hit = True
            
            # Check for TP2 with trailing stop
            if (self.tp1_hit and 
                self.num_take_profits == 2 and 
                self.second_tp_type == "atr_trailing" and
                self.highest_since_entry is not None):
                
                trail_stop = self.highest_since_entry - (self.atr[-1] * self.adaptive_atr_mult)
                
                if low <= trail_stop:
                    self.position.close()
            
            # Check for TP2 with R:R
            elif (self.tp1_hit and 
                  self.num_take_profits == 2 and 
                  self.second_tp_type == "rr" and
                  self.entry_price):
                
                sl_distance = self.entry_price - self.initial_sl
                tp2 = self.entry_price + (sl_distance * self.tp2_rr_long)
                
                if high >= tp2:
                    self.position.close()
        
        # Short position management
        elif self.position.is_short:
            # Update lowest low for trailing
            if self.lowest_since_entry is not None:
                self.lowest_since_entry = min(self.lowest_since_entry, low)
            
            # Check for TP1
            if not self.tp1_hit and self.use_takeprofit and self.entry_price:
                sl_distance = self.initial_sl - self.entry_price
                tp1 = self.entry_price - (sl_distance * self.tp1_rr_short)
                
                if low <= tp1:
                    # Partially close at TP1 (close() expects fraction 0-1)
                    fraction = self.tp1_percent / 100
                    if fraction > 0:
                        self.position.close(fraction)
                        self.tp1_hit = True
            
            # Check for TP2 with trailing stop
            if (self.tp1_hit and 
                self.num_take_profits == 2 and 
                self.second_tp_type == "atr_trailing" and
                self.lowest_since_entry is not None):
                
                trail_stop = self.lowest_since_entry + (self.atr[-1] * self.adaptive_atr_mult)
                
                if high >= trail_stop:
                    self.position.close()
            
            # Check for TP2 with R:R
            elif (self.tp1_hit and 
                  self.num_take_profits == 2 and 
                  self.second_tp_type == "rr" and
                  self.entry_price):
                
                sl_distance = self.initial_sl - self.entry_price
                tp2 = self.entry_price - (sl_distance * self.tp2_rr_short)
                
                if low <= tp2:
                    self.position.close()


# Example usage
if __name__ == "__main__":
    # Load your data
    # Data should be a pandas DataFrame with columns: Open, High, Low, Close, Volume
    # and a DatetimeIndex
    
    # Example: Create sample data
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='1H')
    np.random.seed(42)
    
    close_prices = 100 + np.cumsum(np.random.randn(len(dates)) * 0.5)
    
    df = pd.DataFrame({
        'Open': close_prices + np.random.randn(len(dates)) * 0.1,
        'High': close_prices + np.abs(np.random.randn(len(dates))) * 0.5,
        'Low': close_prices - np.abs(np.random.randn(len(dates))) * 0.5,
        'Close': close_prices,
        'Volume': np.random.randint(1000, 10000, len(dates))
    }, index=dates)
    
    # Run backtest
    bt = Backtest(
        df, 
        AGBotStrategy,
        cash=10000,
        commission=0.0003,  # 0.03%
        exclusive_orders=True
    )
    
    # Run with default parameters
    stats = bt.run()
    print(stats)
    
    # Plot results
    bt.plot()
    
    # Optimize parameters (optional)
    # stats, heatmap = bt.optimize(
    #     key_value=range(2, 5),
    #     ma_length=[100, 200, 300],
    #     tp1_rr_long=[0.5, 1.0, 1.5, 2.0],
    #     maximize='Equity Final [$]',
    #     constraint=lambda p: p.tp2_rr_long > p.tp1_rr_long
    # )
    # print(stats)