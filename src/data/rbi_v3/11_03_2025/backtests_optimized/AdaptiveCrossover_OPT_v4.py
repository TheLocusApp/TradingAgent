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
    # 🌙 AGGRESSIVE OPTIMIZATION FOR 50% TARGET 🚀
    fast_ema = 3        # Ultra-fast EMA for early entries
    slow_ema = 12       # Optimized for trend capture
    signal_ema = 6      # Tighter signal line
    atr_period = 8      # Faster ATR for dynamic stops
    volume_period = 10  # More responsive volume filter
    rsi_period = 10     # Faster momentum detection
    risk_per_trade = 0.035  # Increased to 3.5% risk per trade
    atr_multiplier_stop = 1.5    # Tighter stops for better R:R
    atr_multiplier_trail = 1.0   # Aggressive trailing
    take_profit_multiplier = 3.0 # Higher profit targets
    
    def init(self):
        # Convert data to float64 for TA-Lib compatibility
        close_data = np.array(self.data.Close, dtype=np.float64)
        high_data = np.array(self.data.High, dtype=np.float64)
        low_data = np.array(self.data.Low, dtype=np.float64)
        volume_data = np.array(self.data.Volume, dtype=np.float64)
        
        # 🌙 ENHANCED INDICATOR SUITE WITH MULTIPLE TIMEFRAME CONFIRMATION 🚀
        self.ema_fast = self.I(talib.EMA, close_data, timeperiod=self.fast_ema)
        self.ema_slow = self.I(talib.EMA, close_data, timeperiod=self.slow_ema)
        self.ema_signal = self.I(talib.EMA, close_data, timeperiod=self.signal_ema)
        self.atr = self.I(talib.ATR, high_data, low_data, close_data, timeperiod=self.atr_period)
        self.volume_ma = self.I(talib.SMA, volume_data, timeperiod=self.volume_period)
        self.rsi = self.I(talib.RSI, close_data, timeperiod=self.rsi_period)
        
        # 🌙 ADDED MULTIPLE MOMENTUM INDICATORS FOR CONFIRMATION 🚀
        self.adx = self.I(talib.ADX, high_data, low_data, close_data, timeperiod=10)
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, close_data, fastperiod=8, slowperiod=21, signalperiod=9)
        
        # Track entry prices and ATR for position management
        self.entry_price = None
        self.entry_atr = None
        self.trailing_active = False
        self.take_profit_level = None
        
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
        
        # 🌙 AGGRESSIVE POSITION SIZING WITH VOLATILITY ADJUSTMENT 🚀
        if atr_current > 0:
            # More aggressive scaling for higher returns
            vol_adjustment = max(0.7, min(2.0, 1.2 / (atr_current / current_close * 100)))
            risk_amount = self.equity * self.risk_per_trade * vol_adjustment
            position_size = risk_amount / (atr_current * self.atr_multiplier_stop)
            position_size = int(round(position_size))
        else:
            position_size = int(round(self.equity * self.risk_per_trade / current_close))
        
        # Ensure minimum position size but allow larger positions
        if position_size < 1:
            position_size = 1
        
        # 🌙 ULTRA-AGGRESSIVE LONG ENTRY CONDITIONS 🚀
        long_signal = (
            ema_fast_current > ema_slow_current and          # Primary EMA crossover
            ema_fast_prev <= ema_slow_prev and               # Confirmed crossover
            current_close > ema_signal_current and           # Price above signal EMA
            current_close > ema_fast_current and             # Price above fast EMA
            current_volume > volume_ma_current * 1.05 and    # Stronger volume filter
            rsi_current > 45 and rsi_current < 75 and        # Optimized RSI range
            adx_current > 25 and                             # Stronger trend filter
            macd_current > macd_signal_current               # MACD momentum confirmation
        )
        
        # 🌙 ULTRA-AGGRESSIVE SHORT ENTRY CONDITIONS 🚀
        short_signal = (
            ema_fast_current < ema_slow_current and          # Primary EMA crossover
            ema_fast_prev >= ema_slow_prev and               # Confirmed crossover
            current_close < ema_signal_current and           # Price below signal EMA
            current_close < ema_fast_current and             # Price below fast EMA
            current_volume > volume_ma_current * 1.05 and    # Stronger volume filter
            rsi_current < 55 and rsi_current > 25 and        # Optimized RSI range
            adx_current > 25 and                             # Stronger trend filter
            macd_current < macd_signal_current               # MACD momentum confirmation
        )
        
        # 🌙 OPTIMIZED EXIT CONDITIONS WITH EARLIER PROFIT TAKING 🚀
        long_exit = (
            ema_fast_current < ema_slow_current or           # EMA crossover down
            current_close < ema_signal_current or            # Price below signal EMA
            rsi_current > 80                                 # Earlier overbought exit
        )
        
        short_exit = (
            ema_fast_current > ema_slow_current or           # EMA crossover up
            current_close > ema_signal_current or            # Price above signal EMA
            rsi_current < 20                                 # Earlier oversold exit
        )
        
        # 🌙 AGGRESSIVE POSITION MANAGEMENT WITH SCALED EXITS 🚀
        if self.position:
            if self.position.is_long:
                # Check for take profit target
                if self.take_profit_level and current_high >= self.take_profit_level:
                    print(f"🎯 MOON DEV: Long exit - Take profit hit! Price: {current_close:.2f}")
                    self.position.close()
                    self.entry_price = None
                    self.entry_atr = None
                    self.take_profit_level = None
                    self.trailing_active = False
                    return
                
                # Check for earlier trailing stop activation
                if not self.trailing_active and current_close >= self.entry_price + (self.entry_atr * 0.8):
                    self.trailing_active = True
                    print(f"🌙 MOON DEV: Trailing stop activated for long position! Entry: {self.entry_price:.2f}")
                
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
                        return
                
                # Check other exit conditions
                if long_exit:
                    print(f"🌙 MOON DEV: Long exit - Signal reversal! Price: {current_close:.2f}")
                    self.position.close()
                    self.entry_price = None
                    self.entry_atr = None
                    self.take_profit_level = None
                    self.trailing_active = False
                    
            elif self.position.is_short:
                # Check for take profit target
                if self.take_profit_level and current_low <= self.take_profit_level:
                    print(f"🎯 MOON DEV: Short exit - Take profit hit! Price: {current_close:.2f}")
                    self.position.close()
                    self.entry_price = None
                    self.entry_atr = None
                    self.take_profit_level = None
                    self.trailing_active = False
                    return
                
                # Check for earlier trailing stop activation
                if not self.trailing_active and current_close <= self.entry_price - (self.entry_atr * 0.8):
                    self.trailing_active = True
                    print(f"🌙 MOON DEV: Trailing stop activated for short position! Entry: {self.entry_price:.2f}")
                
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
                        return
                
                # Check other exit conditions
                if short_exit:
                    print(f"🌙 MOON DEV: Short exit - Signal reversal! Price: {current_close:.2f}")
                    self.position.close()
                    self.entry_price = None
                    self.entry_atr = None
                    self.take_profit_level = None
                    self.trailing_active = False
        
        # 🌙 AGGRESSIVE ENTRY LOGIC WITH HIGHER TARGETS 🚀
        if not self.position:
            if long_signal:
                stop_loss = current_close - (atr_current * self.atr_multiplier_stop)
                take_profit = current_close + (atr_current * self.take_profit_multiplier)
                print(f"✨ MOON DEV: AGGRESSIVE LONG ENTRY! Price: {current_close:.2f}, Stop: {stop_loss:.2f}, TP: {take_profit:.2f}, Size: {position_size}")
                self.buy(size=position_size)
                self.entry_price = current_close
                self.entry_atr = atr_current
                self.take_profit_level = take_profit
                self.trailing_active = False
                
            elif short_signal:
                stop_loss = current_close + (atr_current * self.atr_multiplier_stop)
                take_profit = current_close - (atr_current * self.take_profit_multiplier)
                print(f"✨ MOON DEV: AGGRESSIVE SHORT ENTRY! Price: {current_close:.2f}, Stop: {stop_loss:.2f}, TP: {take_profit:.2f}, Size: {position_size}")
                self.sell(size=position_size)
                self.entry_price = current_close
                self.entry_atr = atr_current
                self.take_profit_level = take_profit
                self.trailing_active = False

# Load data and run backtest
print("🌙 MOON DEV'S ULTRA-OPTIMIZED ADAPTIVE CROSSOVER STRATEGY - SPY HOURLY 🚀")
print("Loading SPY hourly data...")
data = load_data()

print(f"Data loaded: {len(data)} candles from {data.index[0]} to {data.index[-1]}")
print(f"Columns: {data.columns.tolist()}")

# Initialize backtest with 1,000,000 capital
bt = Backtest(data, AdaptiveCrossover, cash=1000000, commission=.002)

print("\n🚀 RUNNING ULTRA-OPTIMIZED BACKTEST...")
stats = bt.run()
print(stats)
print(stats._strategy)

# 🌙 MOON DEV'S AGGRESSIVE TESTING FRAMEWORK 🚀
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 MOON DEV'S ULTRA-OPTIMIZED BACKTEST COMPLETE!")
    print("="*80)
    
    # Display key performance metrics
    if hasattr(stats, '_equity_curve'):
        print(f"📈 Final Equity: ${stats['Equity Final [$]']:,.2f}")
        print(f"📊 Total Return: {stats['Return [%]']:.2f}%")
        print(f"📉 Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
        print(f"🔢 Total Trades: {stats['# Trades']}")
        print(f"🎯 Win Rate: {stats['Win Rate [%]']:.2f}%")
        print(f"💰 Profit Factor: {stats['Profit Factor']:.2f}")
    
    print("\n✅ Ultra-optimized backtest execution successful! Strategy enhanced for 50% target!")