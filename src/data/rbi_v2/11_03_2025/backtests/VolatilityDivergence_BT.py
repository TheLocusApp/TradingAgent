import pandas as pd
import yfinance as yf
import pandas_ta as ta
from backtesting import Backtest, Strategy
import numpy as np

def fetch_data(ticker="SPY"):
    ticker_obj = yf.Ticker(ticker)
    data = ticker_obj.history(period="730d", interval="1h")
    data = data.reset_index()
    
    if 'Date' in data.columns:
        data = data.rename(columns={'Date': 'datetime'})
    elif 'Datetime' in data.columns:
        data = data.rename(columns={'Datetime': 'datetime'})
    
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    return data[['Open', 'High', 'Low', 'Close', 'Volume']]

class VolatilityDivergence(Strategy):
    bb_length = 20
    bb_std = 2
    rsi_length = 14
    atr_length = 14
    bb_width_period = 50
    volatility_threshold = 1.2
    
    def init(self):
        # Calculate indicators
        self.bb = self.I(ta.bbands, self.data.Close, length=self.bb_length, std=self.bb_std)
        self.rsi = self.I(ta.rsi, self.data.Close, length=self.rsi_length)
        self.atr = self.I(ta.atr, self.data.High, self.data.Low, self.data.Close, length=self.atr_length)
        self.sma20 = self.I(ta.sma, self.data.Close, length=20)
        
        # Calculate Bollinger Band width
        self.bb_width = self.I(lambda: (self.bb[2] - self.bb[0]) / self.bb[1])
        self.bb_width_avg = self.I(ta.sma, self.bb_width, length=self.bb_width_period)
        
        # Store previous values for divergence detection
        self.price_lows = []
        self.price_highs = []
        self.rsi_lows = []
        self.rsi_highs = []
        
    def next(self):
        if len(self.data) < 100:
            return
            
        current_idx = len(self.data) - 1
        
        # Update price and RSI extremes
        if len(self.data.Close) >= 3:
            # Check for price lows
            if (self.data.Low[-3] > self.data.Low[-2] < self.data.Low[-1]):
                self.price_lows.append((current_idx - 1, self.data.Low[-2]))
                self.rsi_lows.append((current_idx - 1, self.rsi[-2]))
            
            # Check for price highs
            if (self.data.High[-3] < self.data.High[-2] > self.data.High[-1]):
                self.price_highs.append((current_idx - 1, self.data.High[-2]))
                self.rsi_highs.append((current_idx - 1, self.rsi[-2]))
        
        # Keep only recent extremes (last 20)
        if len(self.price_lows) > 20:
            self.price_lows = self.price_lows[-20:]
            self.rsi_lows = self.rsi_lows[-20:]
        if len(self.price_highs) > 20:
            self.price_highs = self.price_highs[-20:]
            self.rsi_highs = self.rsi_highs[-20:]
        
        # Check volatility condition
        if self.bb_width[-1] < self.bb_width_avg[-1] * self.volatility_threshold:
            return
            
        # Check if we have enough data for divergence
        if len(self.price_lows) < 2 or len(self.price_highs) < 2:
            return
            
        current_price = self.data.Close[-1]
        current_rsi = self.rsi[-1]
        current_volume = self.data.Volume[-1]
        avg_volume = np.mean(self.data.Volume[-20:])
        
        # Check for long setup
        if not self.position and len(self.price_lows) >= 2:
            latest_low_idx, latest_low_price = self.price_lows[-1]
            prev_low_idx, prev_low_price = self.price_lows[-2]
            
            latest_low_rsi = self.rsi_lows[-1][1]
            prev_low_rsi = self.rsi_lows[-2][1]
            
            # Bullish divergence: lower price low, higher RSI low
            price_divergence = latest_low_price < prev_low_price
            rsi_divergence = latest_low_rsi > prev_low_rsi
            
            # Near lower Bollinger Band
            near_lower_band = current_price <= self.bb[0][-1] * 1.02
            
            # Volume confirmation
            volume_confirmation = current_volume > avg_volume * 1.1
            
            # SMA confirmation
            sma_confirmation = current_price > self.sma20[-1]
            
            if (price_divergence and rsi_divergence and near_lower_band and 
                volume_confirmation and sma_confirmation):
                
                # Calculate position size with 2% risk
                stop_loss = latest_low_price - (self.atr[-1] * 1.5)
                risk_per_share = current_price - stop_loss
                if risk_per_share > 0:
                    position_size = (1000000 * 0.02) / risk_per_share
                    position_size = min(position_size, 1000000 / current_price)
                    
                    # Take profit at previous swing high or upper Bollinger Band
                    take_profit = min(self.price_highs[-1][1] if self.price_highs else current_price * 1.03, 
                                    self.bb[2][-1])
                    
                    if take_profit / current_price >= 1.02:  # Minimum 1:2 risk-reward
                        self.buy(size=position_size, sl=stop_loss, tp=take_profit)
        
        # Check for short setup
        elif not self.position and len(self.price_highs) >= 2:
            latest_high_idx, latest_high_price = self.price_highs[-1]
            prev_high_idx, prev_high_price = self.price_highs[-2]
            
            latest_high_rsi = self.rsi_highs[-1][1]
            prev_high_rsi = self.rsi_highs[-2][1]
            
            # Bearish divergence: higher price high, lower RSI high
            price_divergence = latest_high_price > prev_high_price
            rsi_divergence = latest_high_rsi < prev_high_rsi
            
            # Near upper Bollinger Band
            near_upper_band = current_price >= self.bb[2][-1] * 0.98
            
            # Volume confirmation
            volume_confirmation = current_volume > avg_volume * 1.1
            
            # SMA confirmation
            sma_confirmation = current_price < self.sma20[-1]
            
            if (price_divergence and rsi_divergence and near_upper_band and 
                volume_confirmation and sma_confirmation):
                
                # Calculate position size with 2% risk
                stop_loss = latest_high_price + (self.atr[-1] * 1.5)
                risk_per_share = stop_loss - current_price
                if risk_per_share > 0:
                    position_size = (1000000 * 0.02) / risk_per_share
                    position_size = min(position_size, 1000000 / current_price)
                    
                    # Take profit at previous swing low or lower Bollinger Band
                    take_profit = max(self.price_lows[-1][1] if self.price_lows else current_price * 0.97, 
                                    self.bb[0][-1])
                    
                    if current_price / take_profit >= 1.02:  # Minimum 1:2 risk-reward
                        self.sell(size=position_size, sl=stop_loss, tp=take_profit)

# Fetch data and run backtest
if __name__ == "__main__":
    data = fetch_data("SPY")
    bt = Backtest(data, VolatilityDivergence, cash=1000000, commission=.002)
    results = bt.run()
    print(results)
    bt.plot()