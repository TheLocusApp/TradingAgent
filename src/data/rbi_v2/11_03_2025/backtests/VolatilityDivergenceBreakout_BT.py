import pandas as pd
import numpy as np
import yfinance as yf
from backtesting import Backtest, Strategy
import talib as ta

def load_data():
    ticker = yf.Ticker("SPY")
    data = ticker.history(period="2y", interval="1d")
    data = data.reset_index()
    data.columns = data.columns.str.strip()
    data = data.rename(columns={'Date': 'datetime'})
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    return data[['Open', 'High', 'Low', 'Close', 'Volume']]

class VolatilityDivergenceBreakout(Strategy):
    # Strategy parameters
    bb_period = 20
    bb_std = 2.0
    kc_period = 20
    kc_multiplier = 2.0
    rsi_period = 14
    atr_period = 14
    
    def init(self):
        # Calculate indicators
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        
        # Bollinger Bands
        self.bb_middle = self.I(ta.BBANDS, close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)[1]
        self.bb_upper = self.I(ta.BBANDS, close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)[0]
        self.bb_lower = self.I(ta.BBANDS, close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)[2]
        
        # ATR for Keltner Channel
        self.atr = self.I(ta.ATR, high, low, close, timeperiod=self.atr_period)
        
        # Keltner Channel
        self.kc_middle = self.I(ta.EMA, close, timeperiod=self.kc_period)
        self.kc_upper = self.I(lambda x: self.kc_middle + (self.kc_multiplier * self.atr))
        self.kc_lower = self.I(lambda x: self.kc_middle - (self.kc_multiplier * self.atr))
        
        # RSI for divergence detection
        self.rsi = self.I(ta.RSI, close, timeperiod=self.rsi_period)
        
        # Bollinger Band width for volatility expansion
        self.bb_width = self.I(lambda x: (self.bb_upper - self.bb_lower) / self.bb_middle)
        self.bb_width_avg = self.I(ta.SMA, self.bb_width, timeperiod=20)
        
        # Track swing lows for divergence detection
        self.swing_lows = []
        self.rsi_lows = []
        
    def next(self):
        current_close = self.data.Close[-1]
        current_low = self.data.Low[-1]
        current_rsi = self.rsi[-1]
        
        # Update swing lows (last 5 periods)
        if len(self.data.Close) >= 5:
            # Check if current low is a swing low (lower than previous 2 and next 2 candles)
            if (current_low < self.data.Low[-2] and current_low < self.data.Low[-3] and 
                current_low < self.data.Low[-4] and current_low < self.data.Low[-5]):
                self.swing_lows.append(current_low)
                self.rsi_lows.append(current_rsi)
                
                # Keep only last 3 swing lows
                if len(self.swing_lows) > 3:
                    self.swing_lows = self.swing_lows[-3:]
                    self.rsi_lows = self.rsi_lows[-3:]
        
        # Check for bullish divergence
        bullish_divergence = False
        if len(self.swing_lows) >= 2:
            # Price makes lower low but RSI makes higher low
            if (self.swing_lows[-1] < self.swing_lows[-2] and 
                self.rsi_lows[-1] > self.rsi_lows[-2]):
                bullish_divergence = True
        
        # Check volatility expansion (Bollinger Bands wider than average)
        volatility_expansion = self.bb_width[-1] > self.bb_width_avg[-1]
        
        # Check breakout above Keltner Channel
        kc_breakout = current_close > self.kc_upper[-1]
        
        # ENTRY CONDITIONS
        if (not self.position and 
            bullish_divergence and 
            volatility_expansion and 
            kc_breakout):
            
            # Calculate position size (risk 1% of capital)
            capital = self.equity
            risk_amount = capital * 0.01
            
            # Stop loss below recent swing low
            if len(self.swing_lows) > 0:
                stop_price = self.swing_lows[-1] - 0.01
                risk_per_share = current_close - stop_price
                
                if risk_per_share > 0:
                    position_size = risk_amount / risk_per_share
                    # Buy with calculated position size
                    self.buy(size=position_size, sl=stop_price)
        
        # EXIT CONDITIONS
        if self.position:
            # Exit if price closes below Keltner Channel midline
            if current_close < self.kc_middle[-1]:
                self.position.close()
            
            # Exit if price touches upper Bollinger Band (profit taking)
            elif current_close >= self.bb_upper[-1]:
                self.position.close()
            
            # Emergency exit if price closes below lower Keltner Channel
            elif current_close < self.kc_lower[-1]:
                self.position.close()
            
            # Trailing stop: move to breakeven after 1.5x ATR profit
            elif (current_close - self.position.entry_price) > (1.5 * self.atr[-1]):
                if self.position.sl is None or self.position.sl < self.position.entry_price:
                    self.position.sl = self.position.entry_price

# Load data and run backtest
if __name__ == "__main__":
    data = load_data()
    bt = Backtest(data, VolatilityDivergenceBreakout, cash=1000000, commission=.002)
    results = bt.run()
    print(results)
    bt.plot()