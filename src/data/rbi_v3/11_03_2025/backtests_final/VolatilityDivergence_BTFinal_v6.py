import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
import yfinance as yf

def load_data():
    print("🌙 MOON DEV: Fetching BTC-USD data from yfinance...")
    ticker = yf.Ticker("BTC-USD")
    data = ticker.history(period="2y", interval="1h")
    
    data = data.reset_index()
    data.columns = data.columns.str.strip().str.lower()
    
    # Clean any unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    
    # Standardize column names
    data = data.rename(columns={
        'date': 'datetime',
        'open': 'Open',
        'high': 'High', 
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    
    print(f"🌙 MOON DEV: Data loaded successfully! Shape: {data.shape}")
    print(f"🌙 MOON DEV: Columns: {list(data.columns)}")
    print(f"🌙 MOON DEV: Data range: {data.index.min()} to {data.index.max()}")
    return data

class VolatilityDivergence(Strategy):
    rsi_period = 14
    bb_period = 20
    bb_std = 2
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    risk_per_trade = 0.02
    
    def init(self):
        close = self.data.Close.astype(float)
        high = self.data.High.astype(float)
        low = self.data.Low.astype(float)
        volume = self.data.Volume.astype(float)
        
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(talib.BBANDS, close, 
                                                              timeperiod=self.bb_period, 
                                                              nbdevup=self.bb_std, 
                                                              nbdevdn=self.bb_std)
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, close, 
                                                            fastperiod=self.macd_fast,
                                                            slowperiod=self.macd_slow, 
                                                            signalperiod=self.macd_signal)
        
        # Calculate BB width using proper indicator wrapping
        def calculate_bb_width():
            bb_upper_array = np.array(self.bb_upper)
            bb_lower_array = np.array(self.bb_lower) 
            bb_middle_array = np.array(self.bb_middle)
            return (bb_upper_array - bb_lower_array) / bb_middle_array
            
        self.bb_width = self.I(calculate_bb_width)
        self.bb_width_avg = self.I(lambda x: talib.SMA(x, timeperiod=20), self.bb_width)
        
        self.volume_sma = self.I(talib.SMA, volume, timeperiod=20)
        
        self.swing_highs = self.I(talib.MAX, high, timeperiod=5)
        self.swing_lows = self.I(talib.MIN, low, timeperiod=5)
        
        self.rsi_lows = self.I(talib.MIN, self.rsi, timeperiod=5)
        self.rsi_highs = self.I(talib.MAX, self.rsi, timeperiod=5)
        
        print("🌙 MOON DEV: Indicators initialized successfully!")
        
    def next(self):
        if len(self.data) < 30:
            return
            
        current_close = self.data.Close[-1]
        current_rsi = self.rsi[-1] if len(self.rsi) > 0 else 50
        current_volume = self.data.Volume[-1]
        current_macd_hist = self.macd_hist[-1] if len(self.macd_hist) > 0 else 0
        
        bb_upper = self.bb_upper[-1] if len(self.bb_upper) > 0 else current_close * 1.1
        bb_lower = self.bb_lower[-1] if len(self.bb_lower) > 0 else current_close * 0.9
        bb_middle = self.bb_middle[-1] if len(self.bb_middle) > 0 else current_close
        
        bb_width = self.bb_width[-1] if len(self.bb_width) > 0 else 0.1
        bb_width_avg = self.bb_width_avg[-1] if len(self.bb_width_avg) > 0 else 0.1
        
        volume_sma = self.volume_sma[-1] if len(self.volume_sma) > 0 else current_volume
        
        swing_low = self.swing_lows[-1] if len(self.swing_lows) > 0 else current_close
        swing_high = self.swing_highs[-1] if len(self.swing_highs) > 0 else current_close
        prev_swing_low = self.swing_lows[-2] if len(self.swing_lows) > 2 else swing_low
        prev_swing_high = self.swing_highs[-2] if len(self.swing_highs) > 2 else swing_high
        
        rsi_low = self.rsi_lows[-1] if len(self.rsi_lows) > 0 else current_rsi
        rsi_high = self.rsi_highs[-1] if len(self.rsi_highs) > 0 else current_rsi
        prev_rsi_low = self.rsi_lows[-2] if len(self.rsi_lows) > 2 else rsi_low
        prev_rsi_high = self.rsi_highs[-2] if len(self.rsi_highs) > 2 else rsi_high
        
        prev_macd_hist = self.macd_hist[-2] if len(self.macd_hist) > 2 else current_macd_hist
        
        high_volatility = bb_width > bb_width_avg
        volume_confirmation = current_volume > volume_sma
        
        bullish_divergence = (swing_low < prev_swing_low and 
                            rsi_low > prev_rsi_low and 
                            current_macd_hist > prev_macd_hist)
        
        bearish_divergence = (swing_high > prev_swing_high and 
                            rsi_high < prev_rsi_high and 
                            current_macd_hist < prev_macd_hist)
        
        price_touched_lower_band = self.data.Low[-1] <= bb_lower or (len(self.data.Low) > 2 and self.data.Low[-2] <= bb_lower)
        price_touched_upper_band = self.data.High[-1] >= bb_upper or (len(self.data.High) > 2 and self.data.High[-2] >= bb_upper)
        
        price_back_inside_long = current_close > bb_lower
        price_back_inside_short = current_close < bb_upper
        
        if not self.position:
            if (bullish_divergence and price_touched_lower_band and 
                high_volatility and volume_confirmation and price_back_inside_long):
                
                risk_amount = self.equity * self.risk_per_trade
                stop_loss = swing_low * 0.98
                risk_per_share = current_close - stop_loss
                
                if risk_per_share > 0:
                    position_size = int(round(risk_amount / risk_per_share))
                    max_position_size = int(self.equity * 0.03 / current_close)
                    position_size = min(position_size, max_position_size)
                    
                    if position_size > 0:
                        self.buy(size=position_size, sl=stop_loss)
                        print(f"🌙 MOON DEV LONG ENTRY: {current_close:.2f} | Size: {position_size} | SL: {stop_loss:.2f}")
                        print(f"🌙 MOON DEV: Bullish divergence confirmed! RSI: {current_rsi:.2f}, BB Width: {bb_width:.4f}")
                        print(f"🌙 MOON DEV: Conditions - Divergence: {bullish_divergence}, BB Touch: {price_touched_lower_band}, Vol: {high_volatility}, Vol Conf: {volume_confirmation}")
                        
            elif (bearish_divergence and price_touched_upper_band and 
                  high_volatility and volume_confirmation and price_back_inside_short):
                
                risk_amount = self.equity * self.risk_per_trade
                stop_loss = swing_high * 1.02
                risk_per_share = stop_loss - current_close
                
                if risk_per_share > 0:
                    position_size = int(round(risk_amount / risk_per_share))
                    max_position_size = int(self.equity * 0.03 / current_close)
                    position_size = min(position_size, max_position_size)
                    
                    if position_size > 0:
                        self.sell(size=position_size, sl=stop_loss)
                        print(f"🌙 MOON DEV SHORT ENTRY: {current_close:.2f} | Size: {position_size} | SL: {stop_loss:.2f}")
                        print(f"🌙 MOON DEV: Bearish divergence confirmed! RSI: {current_rsi:.2f}, BB Width: {bb_width:.4f}")
                        print(f"🌙 MOON DEV: Conditions - Divergence: {bearish_divergence}, BB Touch: {price_touched_upper_band}, Vol: {high_volatility}, Vol Conf: {volume_confirmation}")
        
        else:
            if self.position.is_long:
                macd_current = self.macd[-1] if len(self.macd) > 0 else 0
                macd_prev = self.macd[-2] if len(self.macd) > 1 else 0
                macd_signal_current = self.macd_signal[-1] if len(self.macd_signal) > 0 else 0
                macd_signal_prev = self.macd_signal[-2] if len(self.macd_signal) > 1 else 0
                
                macd_bearish_cross = (macd_prev >= macd_signal_prev and macd_current < macd_signal_current)
                exit_condition = (
                    current_close >= bb_middle or
                    current_rsi >= 70 or
                    macd_bearish_cross or
                    current_close <= swing_low
                )
                
                if exit_condition:
                    print(f"✨ MOON DEV LONG EXIT: {current_close:.2f} | P&L: {self.position.pl:.2f}")
                    self.position.close()
                    
            elif self.position.is_short:
                macd_current = self.macd[-1] if len(self.macd) > 0 else 0
                macd_prev = self.macd[-2] if len(self.macd) > 1 else 0
                macd_signal_current = self.macd_signal[-1] if len(self.macd_signal) > 0 else 0
                macd_signal_prev = self.macd_signal[-2] if len(self.macd_signal) > 1 else 0
                
                macd_bullish_cross = (macd_prev <= macd_signal_prev and macd_current > macd_signal_current)
                exit_condition = (
                    current_close <= bb_middle or
                    current_rsi <= 30 or
                    macd_bullish_cross or
                    current_close >= swing_high
                )
                
                if exit_condition:
                    print(f"✨ MOON DEV SHORT EXIT: {current_close:.2f} | P&L: {self.position.pl:.2f}")
                    self.position.close()

data = load_data()
bt = Backtest(data, VolatilityDivergence, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)