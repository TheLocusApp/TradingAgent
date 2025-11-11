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
    slow_ema = 15       # Adjusted for better trend capture
    trend_ema = 50      # NEW: Trend filter to avoid choppy markets
    atr_period = 10     # More responsive ATR
    volume_period = 15  # Adjusted volume period
    rsi_period = 14     # NEW: RSI for momentum confirmation
    risk_per_trade = 0.025  # Increased to 2.5% risk per trade
    atr_multiplier_stop = 1.8    # Tighter stops for better R:R
    atr_multiplier_trail = 1.2   # Tighter trailing for profit capture
    rsi_oversold = 30   # RSI filter levels
    rsi_overbought = 70
    
    def init(self):
        # Convert data to float64 for TA-Lib compatibility
        close_data = np.array(self.data.Close, dtype=np.float64)
        high_data = np.array(self.data.High, dtype=np.float64)
        low_data = np.array(self.data.Low, dtype=np.float64)
        volume_data = np.array(self.data.Volume, dtype=np.float64)
        
        # 🌙 ENHANCED INDICATOR SUITE FOR BETTER SIGNALS ✨
        self.ema_fast = self.I(talib.EMA, close_data, timeperiod=self.fast_ema)
        self.ema_slow = self.I(talib.EMA, close_data, timeperiod=self.slow_ema)
        self.ema_trend = self.I(talib.EMA, close_data, timeperiod=self.trend_ema)  # Trend filter
        self.atr = self.I(talib.ATR, high_data, low_data, close_data, timeperiod=self.atr_period)
        self.volume_ma = self.I(talib.SMA, volume_data, timeperiod=self.volume_period)
        self.rsi = self.I(talib.RSI, close_data, timeperiod=self.rsi_period)  # Momentum filter
        
        # Track entry prices and ATR for position management
        self.entry_price = None
        self.entry_atr = None
        self.trailing_active = False
        
    def next(self):
        current_close = self.data.Close[-1]
        current_volume = self.data.Volume[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        
        # Skip if we don't have enough data for indicators
        min_bars = max(self.fast_ema, self.slow_ema, self.trend_ema, self.atr_period, self.volume_period, self.rsi_period) + 1
        if len(self.data) < min_bars:
            return
            
        # Get current indicator values
        ema_fast_current = self.ema_fast[-1] if self.ema_fast[-1] is not None else 0
        ema_slow_current = self.ema_slow[-1] if self.ema_slow[-1] is not None else 0
        ema_trend_current = self.ema_trend[-1] if self.ema_trend[-1] is not None else 0
        ema_fast_prev = self.ema_fast[-2] if len(self.ema_fast) > 1 and self.ema_fast[-2] is not None else 0
        ema_slow_prev = self.ema_slow[-2] if len(self.ema_slow) > 1 and self.ema_slow[-2] is not None else 0
        atr_current = self.atr[-1] if self.atr[-1] is not None else 0
        volume_ma_current = self.volume_ma[-1] if self.volume_ma[-1] is not None else 0
        rsi_current = self.rsi[-1] if self.rsi[-1] is not None else 50
        
        # 🌙 DYNAMIC POSITION SIZING WITH VOLATILITY ADJUSTMENT 🚀
        if atr_current > 0:
            # Scale position size based on volatility (smaller in high vol)
            vol_adjustment = max(0.5, min(1.5, 1.0 / (atr_current / current_close * 100)))
            risk_amount = self.equity * self.risk_per_trade * vol_adjustment
            position_size = risk_amount / (atr_current * self.atr_multiplier_stop)
            position_size = int(round(position_size))
        else:
            position_size = int(round(self.equity * self.risk_per_trade / current_close))
        
        # Ensure minimum position size
        if position_size < 1:
            position_size = 1
        
        # 🌙 ENHANCED LONG ENTRY CONDITIONS WITH MULTIPLE FILTERS ✨
        long_signal = (
            ema_fast_current > ema_slow_current and      # EMA crossover
            ema_fast_prev <= ema_slow_prev and           # Confirmed crossover
            current_close > ema_fast_current and          # Price above fast EMA
            current_close > ema_slow_current and          # Price above slow EMA
            current_close > ema_trend_current and         # NEW: Above trend EMA (bullish trend)
            rsi_current > 40 and rsi_current < 80 and     # NEW: RSI in favorable zone
            current_volume > volume_ma_current * 1.1      # STRONGER volume confirmation
        )
        
        # 🌙 ENHANCED SHORT ENTRY CONDITIONS WITH MULTIPLE FILTERS ✨
        short_signal = (
            ema_fast_current < ema_slow_current and      # EMA crossover
            ema_fast_prev >= ema_slow_prev and           # Confirmed crossover
            current_close < ema_fast_current and          # Price below fast EMA
            current_close < ema_slow_current and          # Price below slow EMA
            current_close < ema_trend_current and         # NEW: Below trend EMA (bearish trend)
            rsi_current < 60 and rsi_current > 20 and     # NEW: RSI in favorable zone
            current_volume > volume_ma_current * 1.1      # STRONGER volume confirmation
        )
        
        # 🌙 OPTIMIZED EXIT CONDITIONS WITH PROFIT TARGETS 🎯
        long_exit = (
            ema_fast_current < ema_slow_current or        # EMA crossover down
            current_close < ema_slow_current or           # Price below slow EMA
            rsi_current > 85                              # NEW: Overbought RSI exit
        )
        
        short_exit = (
            ema_fast_current > ema_slow_current or        # EMA crossover up
            current_close > ema_slow_current or           # Price above slow EMA
            rsi_current < 15                              # NEW: Oversold RSI exit
        )
        
        # 🌙 ENHANCED POSITION MANAGEMENT WITH SCALED EXITS 🚀
        if self.position:
            if self.position.is_long:
                # Check for profit targets (scale out)
                profit_pct = (current_close - self.entry_price) / self.entry_price
                
                # Scale out at 2% profit (25% of position)
                if profit_pct >= 0.02 and self.position.size > position_size * 0.75:
                    close_size = int(self.position.size * 0.25)
                    print(f"🎯 MOON DEV: Long partial profit taken! Size: {close_size}")
                    self.position.close(portion=0.25)
                
                # Check for trailing stop activation (earlier)
                if not self.trailing_active and current_close >= self.entry_price + (self.entry_atr * 0.5):
                    self.trailing_active = True
                    print(f"🌙 MOON DEV: Trailing stop activated for long position! Entry: {self.entry_price:.2f}")
                
                # Apply tighter trailing stop if active
                if self.trailing_active:
                    trail_stop = current_close - (self.entry_atr * self.atr_multiplier_trail)
                    if current_low <= trail_stop:
                        print(f"🚀 MOON DEV: Long exit - Trailing stop hit! Price: {current_close:.2f}")
                        self.position.close()
                        self.entry_price = None
                        self.entry_atr = None
                        self.trailing_active = False
                        return
                
                # Check other exit conditions
                if long_exit:
                    print(f"🌙 MOON DEV: Long exit - Signal reversal! Price: {current_close:.2f}")
                    self.position.close()
                    self.entry_price = None
                    self.entry_atr = None
                    self.trailing_active = False
                    
            elif self.position.is_short:
                # Check for profit targets (scale out)
                profit_pct = (self.entry_price - current_close) / self.entry_price
                
                # Scale out at 2% profit (25% of position)
                if profit_pct >= 0.02 and self.position.size > position_size * 0.75:
                    close_size = int(self.position.size * 0.25)
                    print(f"🎯 MOON DEV: Short partial profit taken! Size: {close_size}")
                    self.position.close(portion=0.25)
                
                # Check for trailing stop activation (earlier)
                if not self.trailing_active and current_close <= self.entry_price - (self.entry_atr * 0.5):
                    self.trailing_active = True
                    print(f"🌙 MOON DEV: Trailing stop activated for short position! Entry: {self.entry_price:.2f}")
                
                # Apply tighter trailing stop if active
                if self.trailing_active:
                    trail_stop = current_close + (self.entry_atr * self.atr_multiplier_trail)
                    if current_high >= trail_stop:
                        print(f"🚀 MOON DEV: Short exit - Trailing stop hit! Price: {current_close:.2f}")
                        self.position.close()
                        self.entry_price = None
                        self.entry_atr = None
                        self.trailing_active = False
                        return
                
                # Check other exit conditions
                if short_exit:
                    print(f"🌙 MOON DEV: Short exit - Signal reversal! Price: {current_close:.2f}")
                    self.position.close()
                    self.entry_price = None
                    self.entry_atr = None
                    self.trailing_active = False
        
        # 🌙 ENHANCED ENTRY LOGIC WITH BETTER TIMING ✨
        if not self.position:
            if long_signal:
                stop_loss = current_close - (atr_current * self.atr_multiplier_stop)
                risk_reward = (current_close - stop_loss) / current_close
                
                # Only enter if risk:reward is favorable
                if risk_reward <= 0.03:  # Max 3% risk per trade
                    print(f"✨ MOON DEV: LONG ENTRY! Price: {current_close:.2f}, Stop: {stop_loss:.2f}, Size: {position_size}, RSI: {rsi_current:.1f}")
                    self.buy(size=position_size)
                    self.entry_price = current_close
                    self.entry_atr = atr_current
                    self.trailing_active = False
                
            elif short_signal:
                stop_loss = current_close + (atr_current * self.atr_multiplier_stop)
                risk_reward = (stop_loss - current_close) / current_close
                
                # Only enter if risk:reward is favorable
                if risk_reward <= 0.03:  # Max 3% risk per trade
                    print(f"✨ MOON DEV: SHORT ENTRY! Price: {current_close:.2f}, Stop: {stop_loss:.2f}, Size: {position_size}, RSI: {rsi_current:.1f}")
                    self.sell(size=position_size)
                    self.entry_price = current_close
                    self.entry_atr = atr_current
                    self.trailing_active = False

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
    
    print("\n✅ Optimized backtest execution successful! Strategy enhanced for 50% target!")