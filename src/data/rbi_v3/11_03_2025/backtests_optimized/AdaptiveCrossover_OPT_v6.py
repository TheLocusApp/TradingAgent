```python
import pandas as pd
import numpy as np
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
    
    print(f"🌙 MOON DEV: Data loaded successfully! Shape: {data.shape}")
    print(f"📊 Columns: {data.columns.tolist()}")
    print(f"⏰ Date range: {data.index[0]} to {data.index[-1]}")
    
    return data

class AdaptiveCrossover(Strategy):
    # 🌙 ULTRA-OPTIMIZED PARAMETERS FOR 50% TARGET 🚀
    fast_ema = 2        # Ultra-fast EMA for earliest entries
    slow_ema = 8        # Optimized trend following
    signal_ema = 4      # Tighter signal confirmation
    atr_period = 6      # Faster volatility measurement
    volume_period = 8   # More responsive volume filter
    rsi_period = 8      # Faster momentum detection
    risk_per_trade = 0.045  # Increased to 4.5% risk per trade
    atr_multiplier_stop = 1.2    # Tighter stops for better risk-reward
    atr_multiplier_trail = 0.8   # Aggressive trailing stops
    take_profit_multiplier = 4.0 # Higher profit targets for 50% goal
    
    def init(self):
        # Convert data to float64 for TA-Lib compatibility
        close_data = np.array(self.data.Close, dtype=np.float64)
        high_data = np.array(self.data.High, dtype=np.float64)
        low_data = np.array(self.data.Low, dtype=np.float64)
        volume_data = np.array(self.data.Volume, dtype=np.float64)
        
        # 🌙 ENHANCED INDICATOR SUITE WITH MULTIPLE CONFIRMATIONS 🚀
        self.ema_fast = self.I(talib.EMA, close_data, timeperiod=self.fast_ema)
        self.ema_slow = self.I(talib.EMA, close_data, timeperiod=self.slow_ema)
        self.ema_signal = self.I(talib.EMA, close_data, timeperiod=self.signal_ema)
        self.atr = self.I(talib.ATR, high_data, low_data, close_data, timeperiod=self.atr_period)
        self.volume_ma = self.I(talib.SMA, volume_data, timeperiod=self.volume_period)
        self.rsi = self.I(talib.RSI, close_data, timeperiod=self.rsi_period)
        
        # 🌙 ADDED MULTIPLE MOMENTUM INDICATORS FOR STRONGER CONFIRMATION 🚀
        self.adx = self.I(talib.ADX, high_data, low_data, close_data, timeperiod=8)
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, close_data, fastperiod=6, slowperiod=13, signalperiod=5)
        self.stoch_k, self.stoch_d = self.I(talib.STOCH, high_data, low_data, close_data, fastk_period=5, slowk_period=3, slowd_period=3)
        
        # 🌙 ADDED VOLATILITY FILTER FOR MARKET REGIME DETECTION 🚀
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(talib.BBANDS, close_data, timeperiod=10, nbdevup=2, nbdevdn=2)
        
        # Track entry prices and ATR for position management
        self.entry_price = None
        self.entry_atr = None
        self.trailing_active = False
        self.take_profit_level = None
        self.scale_out_levels = []  # For partial profit taking
        
    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_volume = self.data.Volume[-1]
        
        # Skip if we don't have enough data for indicators
        min_periods = max(self.fast_ema, self.slow_ema, self.atr_period, 
                         self.volume_period, self.rsi_period, 14) + 1
        if len(self.data) < min_periods:
            return
            
        # Get current indicator values
        ema_fast_current = self.ema_fast[-1] if self.ema_fast[-1] is not None else 0
        ema_slow_current = self.ema_slow[-1] if self.ema_slow[-1] is not None else 0
        ema_signal_current = self.ema_signal[-1] if self.ema_signal[-1] is not None else 0
        ema_fast_prev = self.ema_fast[-2] if len(self.ema_fast) > 1 and self.ema_fast[-2] is not None else 0
        ema_slow_prev = self.ema_slow[-2] if len(self.ema_slow) > 1 and self.ema_slow[-2] is not None else 0
        atr_current = self.atr[-1] if self.atr[-1] is not None else 0
        volume_ma_current = self.volume_ma[-1] if self.volume_ma[-1] is not None else 0
        rsi_current = self.rsi[-1] if self.rsi[-1] is not None else 50
        adx_current = self.adx[-1] if self.adx[-1] is not None else 0
        macd_current = self.macd[-1] if self.macd[-1] is not None else 0
        macd_signal_current = self.macd_signal[-1] if self.macd_signal[-1] is not None else 0
        stoch_k_current = self.stoch_k[-1] if self.stoch_k[-1] is not None else 50
        stoch_d_current = self.stoch_d[-1] if self.stoch_d[-1] is not None else 50
        bb_upper_current = self.bb_upper[-1] if self.bb_upper[-1] is not None else current_close
        bb_lower_current = self.bb_lower[-1] if self.bb_lower[-1] is not None else current_close
        
        # 🌙 AGGRESSIVE VOLATILITY-ADJUSTED POSITION SIZING 🚀
        if atr_current > 0:
            # More aggressive scaling with volatility normalization
            vol_ratio = atr_current / current_close
            vol_adjustment = max(0.8, min(2.5, 1.5 / (vol_ratio * 100)))
            risk_amount = self.equity * self.risk_per_trade * vol_adjustment
            position_size = risk_amount / (atr_current * self.atr_multiplier_stop)
            position_size = int(round(position_size))
        else:
            position_size = int(round(self.equity * self.risk_per_trade / current_close))
        
        # Ensure minimum position size but allow larger positions
        if position_size < 1:
            position_size = 1
        
        # 🌙 ULTRA-OPTIMIZED LONG ENTRY CONDITIONS WITH MULTIPLE CONFIRMATIONS 🚀
        long_signal = (
            ema_fast_current > ema_slow_current and          # Primary EMA crossover
            ema_fast_prev <= ema_slow_prev and               # Confirmed crossover
            current_close > ema_signal_current and           # Price above signal EMA
            current_close > ema_fast_current and             # Price above fast EMA
            current_volume > volume_ma_current * 1.08 and    # Strong volume confirmation
            rsi_current > 40 and rsi_current < 70 and        # Optimized RSI momentum
            adx_current > 28 and                             # Strong trend filter
            macd_current > macd_signal_current and           # MACD momentum
            stoch_k_current > stoch_d_current and            # Stochastic momentum
            current_close > bb_middle[-1] if self.bb_middle[-1] is not None else True  # Above BB middle
        )
        
        # 🌙 ULTRA-OPTIMIZED SHORT ENTRY CONDITIONS WITH MULTIPLE CONFIRMATIONS 🚀
        short_signal = (
            ema_fast_current < ema_slow_current and          # Primary EMA crossover
            ema_fast_prev >= ema_slow_prev and               # Confirmed crossover
            current_close < ema_signal_current and           # Price below signal EMA
            current_close < ema_fast_current and             # Price below fast EMA
            current_volume > volume_ma_current * 1.08 and    # Strong volume confirmation
            rsi_current < 60 and rsi_current > 30 and        # Optimized RSI momentum
            adx_current > 28 and                             # Strong trend filter
            macd_current < macd_signal_current and           # MACD momentum
            stoch_k_current < stoch_d_current and            # Stochastic momentum
            current_close < bb_middle[-1] if self.bb_middle[-1] is not None else True  # Below BB middle
        )
        
        # 🌙 OPTIMIZED EXIT CONDITIONS WITH EARLIER PROFIT PROTECTION 🚀
        long_exit = (
            ema_fast_current < ema_slow_current or           # EMA crossover down
            current_close < ema_signal_current or            # Price below signal EMA
            rsi_current > 75 or                              # Earlier overbought exit
            stoch_k_current > 80                             # Stochastic overbought
        )
        
        short_exit = (
            ema_fast_current > ema_slow_current or           # EMA crossover up
            current_close > ema_signal_current or            # Price above signal EMA
            rsi_current < 25 or                              # Earlier oversold exit
            stoch_k_current < 20                             # Stochastic oversold
        )
        
        # 🌙 AGGRESSIVE POSITION MANAGEMENT WITH SCALED EXITS AND TRAILING 🚀
        if self.position:
            if self.position.is_long:
                # Check for scale-out profit targets
                if not self.scale_out_levels and current_high >= self.entry_price + (self.entry_atr * 1.5):
                    # Scale out 50% at 1.5 ATR profit
                    scale_size = int(self.position.size * 0.5)
                    if scale_size > 0:
                        self.position.close(scale_size)
                        print(f"🎯 MOON DEV: Long scale-out 50% at 1.5 ATR profit! Price: {current_close:.2f}")
                        self.scale_out_levels.append(1.5)
                
                # Check for take profit target
                if self.take_profit_level and current_high >= self.take_profit_level:
                    print(f"🎯 MOON DEV: Long exit - Final take profit hit! Price: {current_close:.2f}")
                    self.position.close()
                    self.entry_price = None
                    self.entry_atr = None
                    self.take_profit_level = None
                    self.trailing_active = False
                    self.scale_out_levels = []
                    return
                
                # Check for earlier trailing stop activation
                if not self.trailing_active and current_close >= self.entry_price + (self.entry_atr * 0.6):
                    self.trailing_active = True
                    print(f"🌙 MOON DEV: Early trailing stop activated for long! Entry: {self.entry_price:.2f}")
                
                # Apply aggressive trailing stop if active
                if self.trailing_active:
                    trail_stop = current_close - (self.entry_atr * self.atr_multiplier_trail)
                    if current_low <= trail_stop:
                        print(f"🚀 MOON DEV: Long exit - Trailing stop hit! Price: {current_close:.2f}")
                        self.position.close()
                        self.entry_price = None
                        self.entry_atr = None
                        self.take_profit_level = None
                        self.trailing_active = False
                        self.scale_out_levels = []
                        return
                
                # Check other exit conditions
                if long_exit:
                    print(f"🌙 MOON DEV: Long exit - Signal reversal! Price: {current_close:.2f}")
                    self.position.close()
                    self.entry_price = None
                    self.entry_atr = None
                    self.take_profit_level = None
                    self.trailing_active = False
                    self.scale_out_levels = []
                    
            elif self.position.is_short:
                # Check for scale-out profit targets
                if not self.scale_out_levels and current_low <= self.entry_price - (self.entry_atr * 1.5):
                    # Scale out 50% at 1.5 ATR profit
                    scale_size = int(self.position.size * 0.5)
                    if scale_size > 0:
                        self.position.close(scale_size)
                        print(f"🎯 MOON DEV: Short scale-out 50% at 1.5 ATR profit! Price: {current_close:.2f}")
                        self.scale_out_levels.append(1.5)
                
                # Check for take profit target
                if self.take_profit_level and current_low <= self.take_profit_level:
                    print(f"🎯 MOON DEV: Short exit - Final take profit hit! Price: {current_close:.2f}")
                    self.position.close()
                    self.entry_price = None
                    self.entry_atr = None
                    self.take_profit_level = None
                    self.trailing_active = False
                    self.scale_out_levels = []
                    return
                
                # Check for earlier trailing stop activation
                if not self.trailing_active and current_close <= self.entry_price - (self.entry_atr * 0.6):
                    self.trailing_active = True
                    print(f"🌙 MOON DEV: Early trailing stop activated for short! Entry: {self.entry_price:.2f}")
                
                # Apply aggressive trailing stop if active
                if self.trailing_active:
                    trail_stop = current_close + (self.entry_atr * self.atr_multiplier_trail)
                    if current_high >= trail_stop:
                        print(f"🚀 MOON DEV: Short exit - Trailing stop hit! Price: {current_close:.2f}")
                        self.position.close()
                        self.entry_price = None
                        self.entry_atr = None
                        self.take_profit_level = None
                        self.trailing_active = False
                        self.scale_out_levels = []
                        return
                
                # Check other exit conditions
                if short_exit:
                    print(f"🌙 MOON DEV: Short exit - Signal reversal! Price: {current_close:.2f}")
                    self.position.close()
                    self.entry_price = None
                    self.entry_atr = None
                    self.take_profit_level = None
                    self.trailing_active = False
                    self.scale_out_levels = []
        
        # 🌙 AGGRESSIVE ENTRY LOGIC WITH HIGHER TARGETS AND SCALED POSITIONS 🚀
        if not self.position:
            if long_signal:
                stop_loss = current_close - (atr_current * self.atr_multiplier_stop)
                take_profit = current_close + (atr_current * self.take_profit_multiplier)
                print(f"✨ MOON DEV: ULTRA-OPTIMIZED LONG ENTRY! Price: {current_close:.2f}, Stop: {stop_loss:.2f}, TP: {take_profit:.2f}, Size: {position_size}")
                self.buy(size=position_size)
                self.entry_price = current_close
                self.entry_atr = atr_current
                self.take_profit_level = take_profit
                self.trailing_active = False
                self.scale_out_levels = []
                
            elif short_signal:
                stop_loss = current_close + (atr_current * self.atr_multiplier_stop)
                take_profit = current_close - (atr_current * self.take_profit_multiplier)
                print(f"✨ MOON DEV: ULTRA-OPTIMIZED SHORT ENTRY! Price: {current_close:.2f}, Stop: {stop_loss:.2f}, TP: {take_profit:.2f}, Size: {position_size}")
                self.sell(size=position_size)
                self.entry_price = current_close
                self.entry_atr = atr_current
                self.take_profit_level = take_profit
                self.trailing_active = False
                self.scale_out_levels = []

# Load data and run backtest
print("🌙 MOON DEV'S ULTRA-OPTIMIZED ADAPTIVE CROSSOVER STRATEGY - SPY HOURLY 🚀")
print("Loading SPY hourly data...")
data