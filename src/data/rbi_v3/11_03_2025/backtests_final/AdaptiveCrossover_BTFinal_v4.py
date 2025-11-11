import pandas as pd
import numpy as np
import yfinance as yf
from backtesting import Backtest, Strategy
import talib

def load_data():
    # Download SPY data using yfinance
    ticker = yf.Ticker("SPY")
    data = ticker.history(period="2y", interval="1d")
    
    # Reset index to make datetime a column
    data = data.reset_index()
    
    # Clean and rename columns properly
    data.columns = data.columns.str.strip().str.lower()
    data = data.rename(columns={
        'date': 'datetime',
        'open': 'Open',
        'high': 'High', 
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    
    # Drop any unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    
    # Set datetime as index
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    
    print("🌙 MOON DEV: Data loaded successfully! 📊")
    print(f"📈 Data shape: {data.shape}, Columns: {list(data.columns)}")
    print(f"📅 Date range: {data.index.min()} to {data.index.max()}")
    
    return data

class AdaptiveCrossover(Strategy):
    # Strategy parameters
    fast_ema_period = 20
    slow_ema_period = 50
    atr_period = 14
    volume_lookback = 20
    risk_per_trade = 0.02
    max_daily_dd = 0.05
    trailing_stop_pct = 0.02
    atr_multiplier = 2
    min_ema_distance = 0.005
    
    def init(self):
        # Convert data to proper float64 type for TA-Lib
        close_data = np.array(self.data.Close, dtype=np.float64)
        volume_data = np.array(self.data.Volume, dtype=np.float64)
        high_data = np.array(self.data.High, dtype=np.float64)
        low_data = np.array(self.data.Low, dtype=np.float64)
        
        # Calculate indicators using self.I() wrapper with proper data types
        self.fast_ema = self.I(talib.EMA, close_data, timeperiod=self.fast_ema_period)
        self.slow_ema = self.I(talib.EMA, close_data, timeperiod=self.slow_ema_period)
        self.volume_avg = self.I(talib.SMA, volume_data, timeperiod=self.volume_lookback)
        self.atr = self.I(talib.ATR, high_data, low_data, close_data, timeperiod=self.atr_period)
        
        # Track highest/lowest close for trailing stops
        self.highest_close = None
        self.lowest_close = None
        
        # Track portfolio peak for drawdown protection
        self.portfolio_peak = 1000000  # Starting equity
        
        print("🌙 MOON DEV: AdaptiveCrossover Strategy Initialized! 🚀")
        print(f"📊 Fast EMA: {self.fast_ema_period}, Slow EMA: {self.slow_ema_period}")
        print(f"🎯 Risk per trade: {self.risk_per_trade*100}%, Max DD: {self.max_daily_dd*100}%")

    def next(self):
        current_bar = len(self.data) - 1
        if current_bar < max(self.slow_ema_period, self.volume_lookback, self.atr_period):
            return
            
        # Get current values
        close = self.data.Close[-1]
        volume = self.data.Volume[-1]
        fast_ema = self.fast_ema[-1]
        slow_ema = self.slow_ema[-1]
        volume_avg = self.volume_avg[-1]
        atr = self.atr[-1]
        
        # Previous values for crossover detection
        prev_fast_ema = self.fast_ema[-2] if len(self.fast_ema) > 1 else fast_ema
        prev_slow_ema = self.slow_ema[-2] if len(self.slow_ema) > 1 else slow_ema
        
        # Calculate EMA distance percentage
        ema_distance = abs(fast_ema - slow_ema) / slow_ema
        
        # Update portfolio peak
        current_equity = self.equity
        if current_equity > self.portfolio_peak:
            self.portfolio_peak = current_equity
        
        # Check drawdown protection
        current_dd = (self.portfolio_peak - current_equity) / self.portfolio_peak
        if current_dd > 0.03:
            print(f"⚠️ MOON DEV: Portfolio down {current_dd*100:.1f}% from peak - No new entries!")
            return
        
        # Check if we have a position
        if not self.position:
            # No position - check for entries
            
            # Volume confirmation
            volume_ok = volume > volume_avg
            
            # EMA distance confirmation
            ema_distance_ok = ema_distance > self.min_ema_distance
            
            # Check for LONG entry
            long_signal = (prev_fast_ema <= prev_slow_ema and 
                          fast_ema > slow_ema and 
                          close > fast_ema and 
                          close > slow_ema)
            
            # Check for SHORT entry  
            short_signal = (prev_fast_ema >= prev_slow_ema and 
                           fast_ema < slow_ema and 
                           close < fast_ema and 
                           close < slow_ema)
            
            if long_signal and volume_ok and ema_distance_ok:
                # Calculate position size based on risk
                risk_amount = current_equity * self.risk_per_trade
                stop_loss_price = close - (atr * self.atr_multiplier)
                risk_per_share = close - stop_loss_price
                
                if risk_per_share > 0:
                    position_size = risk_amount / risk_per_share
                    position_size = int(round(position_size))
                    
                    if position_size > 0:
                        print(f"🌙 MOON DEV: LONG ENTRY SIGNAL! 🟢")
                        print(f"📈 Price: {close:.2f}, Fast EMA: {fast_ema:.2f}, Slow EMA: {slow_ema:.2f}")
                        print(f"💰 Position size: {position_size} shares")
                        print(f"🎯 Stop Loss: {stop_loss_price:.2f}")
                        self.buy(size=position_size, sl=stop_loss_price)
                        self.highest_close = close
                        
            elif short_signal and volume_ok and ema_distance_ok:
                # Calculate position size based on risk
                risk_amount = current_equity * self.risk_per_trade
                stop_loss_price = close + (atr * self.atr_multiplier)
                risk_per_share = stop_loss_price - close
                
                if risk_per_share > 0:
                    position_size = risk_amount / risk_per_share
                    position_size = int(round(position_size))
                    
                    if position_size > 0:
                        print(f"🌙 MOON DEV: SHORT ENTRY SIGNAL! 🔴")
                        print(f"📉 Price: {close:.2f}, Fast EMA: {fast_ema:.2f}, Slow EMA: {slow_ema:.2f}")
                        print(f"💰 Position size: {position_size} shares")
                        print(f"🎯 Stop Loss: {stop_loss_price:.2f}")
                        self.sell(size=position_size, sl=stop_loss_price)
                        self.lowest_close = close
                        
        else:
            # We have a position - manage exits
            if self.position.is_long:
                # Update highest close for trailing stop
                if close > self.highest_close:
                    self.highest_close = close
                
                # Calculate exit conditions
                trailing_stop_price = self.highest_close * (1 - self.trailing_stop_pct)
                ema_cross_exit = fast_ema < slow_ema
                
                if close <= trailing_stop_price or ema_cross_exit:
                    print(f"🌙 MOON DEV: LONG EXIT! 🟡")
                    print(f"📊 Exit reason: {'EMA Cross' if ema_cross_exit else 'Trailing Stop'}")
                    print(f"💰 P&L: ${self.position.pl:.2f}")
                    self.position.close()
                    
            elif self.position.is_short:
                # Update lowest close for trailing stop
                if close < self.lowest_close:
                    self.lowest_close = close
                
                # Calculate exit conditions
                trailing_stop_price = self.lowest_close * (1 + self.trailing_stop_pct)
                ema_cross_exit = fast_ema > slow_ema
                
                if close >= trailing_stop_price or ema_cross_exit:
                    print(f"🌙 MOON DEV: SHORT EXIT! 🟡")
                    print(f"📊 Exit reason: {'EMA Cross' if ema_cross_exit else 'Trailing Stop'}")
                    print(f"💰 P&L: ${self.position.pl:.2f}")
                    self.position.close()

# Load data and run backtest
data = load_data()
bt = Backtest(data, AdaptiveCrossover, cash=1000000, commission=.002)

print("🚀 MOON DEV: Starting AdaptiveCrossover Backtest...")
stats = bt.run()
print(stats)
print(stats._strategy)

# 🌙 MOON DEV'S BACKTEST COMPLETE! 🚀
print("\n" + "="*80)
print("🌙 MOON DEV: AdaptiveCrossover Backtest Complete!")
print("="*80)