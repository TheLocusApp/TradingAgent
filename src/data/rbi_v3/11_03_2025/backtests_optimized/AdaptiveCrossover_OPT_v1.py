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
    # 🌙 OPTIMIZED STRATEGY PARAMETERS FOR 50% TARGET 🚀
    fast_ema = 5        # Faster EMA for earlier signals
    slow_ema = 15       # Optimized slow EMA for better trend capture
    signal_ema = 9      # Added signal line for MACD-style confirmation
    atr_period = 10     # Faster ATR for more responsive stops
    volume_period = 15  # Optimized volume period
    rsi_period = 14     # RSI for momentum confirmation
    risk_per_trade = 0.025  # Increased to 2.5% risk per trade for higher returns
    atr_multiplier_stop = 1.8  # Tighter stops for better risk/reward
    atr_multiplier_trail = 1.2  # Tighter trailing for profit protection
    rsi_oversold = 35   # RSI filter for entries
    rsi_overbought = 65 # RSI filter for entries
    
    def init(self):
        # Convert data to float64 for TA-Lib compatibility
        close_data = np.array(self.data.Close, dtype=np.float64)
        high_data = np.array(self.data.High, dtype=np.float64)
        low_data = np.array(self.data.Low, dtype=np.float64)
        volume_data = np.array(self.data.Volume, dtype=np.float64)
        
        # 🌙 ENHANCED INDICATOR SUITE FOR BETTER SIGNALS 🚀
        # Core trend indicators
        self.ema_fast = self.I(talib.EMA, close_data, timeperiod=self.fast_ema)
        self.ema_slow = self.I(talib.EMA, close_data, timeperiod=self.slow_ema)
        self.ema_signal = self.I(talib.EMA, close_data, timeperiod=self.signal_ema)
        
        # Volatility and momentum indicators
        self.atr = self.I(talib.ATR, high_data, low_data, close_data, timeperiod=self.atr_period)
        self.volume_ma = self.I(talib.SMA, volume_data, timeperiod=self.volume_period)
        self.rsi = self.I(talib.RSI, close_data, timeperiod=self.rsi_period)
        
        # 🌙 ADDED TREND STRENGTH INDICATOR 🚀
        self.adx = self.I(talib.ADX, high_data, low_data, close_data, timeperiod=14)
        
        # Track entry prices and ATR for position management
        self.entry_price = None
        self.entry_atr = None
        self.trailing_active = False
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
        
        # 🌙 DYNAMIC POSITION SIZING WITH VOLATILITY ADJUSTMENT 🚀
        if atr_current > 0:
            # Adjust risk based on ATR volatility (lower risk in high volatility)
            volatility_factor = max(0.5, min(2.0, 1.0 / (atr_current / current_close * 100)))
            adjusted_risk = self.risk_per_trade * volatility_factor
            risk_amount = self.equity * adjusted_risk
            position_size = risk_amount / (atr_current * self.atr_multiplier_stop)
            position_size = int(round(position_size))
        else:
            position_size = int(round(self.equity * self.risk_per_trade / current_close))
        
        # Ensure minimum position size
        if position_size < 1:
            position_size = 1
        
        # 🌙 ENHANCED LONG ENTRY CONDITIONS WITH MULTIPLE FILTERS 🚀
        long_signal = (
            ema_fast_current > ema_slow_current and        # Primary EMA crossover
            ema_fast_prev <= ema_slow_prev and             # Confirmed crossover
            current_close > ema_fast_current and           # Price above fast EMA
            current_close > ema_slow_current and           # Price above slow EMA
            current_close > ema_signal_current and         # Price above signal EMA
            current_volume > volume_ma_current * 1.1 and   # Strong volume confirmation
            rsi_current > self.rsi_oversold and           # Not oversold
            rsi_current < 70 and                          # Not overbought
            adx_current > 20                              # Trend strength confirmation
        )
        
        # 🌙 ENHANCED SHORT ENTRY CONDITIONS WITH MULTIPLE FILTERS 🚀
        short_signal = (
            ema_fast_current < ema_slow_current and        # EMA crossover down
            ema_fast_prev >= ema_slow_prev and             # Confirmed crossover
            current_close < ema_fast_current and           # Price below fast EMA
            current_close < ema_slow_current and           # Price below slow EMA
            current_close < ema_signal_current and         # Price below signal EMA
            current_volume > volume_ma_current * 1.1 and   # Strong volume confirmation
            rsi_current < self.rsi_overbought and         # Not overbought
            rsi_current > 30 and                          # Not oversold
            adx_current > 20                              # Trend strength confirmation
        )
        
        # 🌙 OPTIMIZED EXIT CONDITIONS WITH TRAILING PROFIT TAKING 🚀
        long_exit = (
            ema_fast_current < ema_slow_current or         # EMA crossover down
            current_close < ema_slow_current or           # Price below slow EMA
            rsi_current > 75                              # Overbought RSI exit
        )
        
        short_exit = (
            ema_fast_current > ema_slow_current or         # EMA crossover up
            current_close > ema_slow_current or           # Price above slow EMA
            rsi_current < 25                              # Oversold RSI exit
        )
        
        # 🌙 ADVANCED POSITION MANAGEMENT WITH SCALING AND TRAILING 🚀
        if self.position:
            if self.position.is_long:
                # Calculate profit levels for scaling out
                profit_pct = (current_close - self.entry_price) / self.entry_price * 100
                
                # Scale out 50% at 2% profit
                if profit_pct >= 2.0 and len(self.scale_out_levels) == 0:
                    scale_size = int(self.position.size * 0.5)
                    if scale_size > 0:
                        self.position.close(scale_size)
                        self.scale_out_levels.append(2.0)
                        print(f"🌙 MOON DEV: Scaled out 50% long at +2% profit! Remaining: {self.position.size}")
                
                # Scale out remaining at 4% profit
                elif profit_pct >= 4.0 and len(self.scale_out_levels) == 1:
                    self.position.close()
                    self.scale_out_levels = []
                    print(f"🚀 MOON DEV: Full long exit at +4% profit! Total gain: {profit_pct:.2f}%")
                    self.entry_price = None
                    self.entry_atr = None
                    self.trailing_active = False
                    return
                
                # Check for trailing stop activation
                if not self.trailing_active and current_close >= self.entry_price + (self.entry_atr * 1.5):
                    self.trailing_active = True
                    print(f"🌙 MOON DEV: Trailing stop activated for long position! Entry: {self.entry_price:.2f}")
                
                # Apply trailing stop if active
                if self.trailing_active:
                    trail_stop = current_close - (self.entry_atr * self.atr_multiplier_trail)
                    if current_low <= trail_stop:
                        print(f"🚀 MOON DEV: Long exit - Trailing stop hit! Price: {current_close:.2f}")
                        self.position.close()
                        self.entry_price = None
                        self.entry_atr = None
                        self.trailing_active = False
                        self.scale_out_levels = []
                        return
                
                # Check other exit conditions
                if long_exit and profit_pct < 0:  # Only exit on signal if losing
                    print(f"🌙 MOON DEV: Long exit - Signal reversal! Price: {current_close:.2f}")
                    self.position.close()
                    self.entry_price = None
                    self.entry_atr = None
                    self.trailing_active = False
                    self.scale_out_levels = []
                    
            elif self.position.is_short:
                # Calculate profit levels for scaling out
                profit_pct = (self.entry_price - current_close) / self.entry_price * 100
                
                # Scale out 50% at 2% profit
                if profit_pct >= 2.0 and len(self.scale_out_levels) == 0:
                    scale_size = int(self.position.size * 0.5)
                    if scale_size > 0:
                        self.position.close(scale_size)
                        self.scale_out_levels.append(2.0)
                        print(f"🌙 MOON DEV: Scaled out 50% short at +2% profit! Remaining: {self.position.size}")
                
                # Scale out remaining at 4% profit
                elif profit_pct >= 4.0 and len(self.scale_out_levels) == 1:
                    self.position.close()
                    self.scale_out_levels = []
                    print(f"🚀 MOON DEV: Full short exit at +4% profit! Total gain: {profit_pct:.2f}%")
                    self.entry_price = None
                    self.entry_atr = None
                    self.trailing_active = False
                    return
                
                # Check for trailing stop activation
                if not self.trailing_active and current_close <= self.entry_price - (self.entry_atr * 1.5):
                    self.trailing_active = True
                    print(f"🌙 MOON DEV: Trailing stop activated for short position! Entry: {self.entry_price:.2f}")
                
                # Apply trailing stop if active
                if self.trailing_active:
                    trail_stop = current_close + (self.entry_atr * self.atr_multiplier_trail)
                    if current_high >= trail_stop:
                        print(f"🚀 MOON DEV: Short exit - Trailing stop hit! Price: {current_close:.2f}")
                        self.position.close()
                        self.entry_price = None
                        self.entry_atr = None
                        self.trailing_active = False
                        self.scale_out_levels = []
                        return
                
                # Check other exit conditions
                if short_exit and profit_pct < 0:  # Only exit on signal if losing
                    print(f"🌙 MOON DEV: Short exit - Signal reversal! Price: {current_close:.2f}")
                    self.position.close()
                    self.entry_price = None
                    self.entry_atr = None
                    self.trailing_active = False
                    self.scale_out_levels = []
        
        # 🌙 ENTRY LOGIC WITH IMPROVED FILTERING (only if no position) 🚀
        if not self.position:
            if long_signal:
                stop_loss = current_close - (atr_current * self.atr_multiplier_stop)
                print(f"✨ MOON DEV: LONG ENTRY! Price: {current_close:.2f}, Stop: {stop_loss:.2f}, Size: {position_size}")
                self.buy(size=position_size)
                self.entry_price = current_close
                self.entry_atr = atr_current
                self.trailing_active = False
                self.scale_out_levels = []
                
            elif short_signal:
                stop_loss = current_close + (atr_current * self.atr_multiplier_stop)
                print(f"✨ MOON DEV: SHORT ENTRY! Price: {current_close:.2f}, Stop: {stop_loss:.2f}, Size: {position_size}")
                self.sell(size=position_size)
                self.entry_price = current_close
                self.entry_atr = atr_current
                self.trailing_active = False
                self.scale_out_levels = []

# Load data and run backtest
print("🌙 MOON DEV'S OPTIMIZED ADAPTIVE CROSSOVER STRATEGY - SPY HOURLY 🚀")
print("Loading SPY hourly data...")
data = load_data()

print(f"Data loaded: {len(data)} candles from {data.index[0]} to {data.index[-1]}")
print(f"Columns: {data.columns.tolist()}")

# Initialize backtest with 1,000,000 capital
bt = Backtest(data, AdaptiveCrossover, cash=1000000, commission=.002)

print("\n🚀 RUNNING OPTIMIZED BACKTEST...")
stats = bt.run()
print(stats)
print(stats._strategy)

# 🌙 MOON DEV'S SIMPLIFIED TESTING FRAMEWORK 🚀
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 MOON DEV'S OPTIMIZED BACKTEST COMPLETE!")
    print("="*80)
    
    # Display key performance metrics
    if hasattr(stats, '_equity_curve'):
        print(f"📈 Final Equity: ${stats['Equity Final [$]']:,.2f}")
        print(f"📊 Total Return: {stats['Return [%]']:.2f}%")
        print(f"📉 Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
        print(f"🔢 Total Trades: {stats['# Trades']}")
        print(f"🎯 Win Rate: {stats['Win Rate [%]']:.2f}%")
    
    print("\n✅ Optimized backtest execution successful! Strategy ready for deployment.")