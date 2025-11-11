import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import talib as ta

class TTMomentum(Strategy):
    # Strategy parameters
    bb_period = 20
    bb_std = 2
    kc_period = 20
    kc_mult = 2
    momentum_period = 12
    squeeze_lookback = 5
    
    def init(self):
        # Clean and prepare data
        self.data.df.columns = self.data.df.columns.str.strip().str.lower()
        
        # Calculate Bollinger Bands
        self.bb_middle = self.I(ta.SMA, self.data.Close, timeperiod=self.bb_period)
        self.bb_upper = self.I(ta.BBANDS, self.data.Close, timeperiod=self.bb_period, nbdevup=self.bb_std)[0]
        self.bb_lower = self.I(ta.BBANDS, self.data.Close, timeperiod=self.bb_period, nbdevdn=self.bb_std)[2]
        
        # Calculate Keltner Channel
        self.atr = self.I(ta.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.kc_period)
        self.kc_middle = self.I(ta.SMA, self.data.Close, timeperiod=self.kc_period)
        self.kc_upper = self.I(lambda x: self.kc_middle + (self.kc_mult * self.atr))
        self.kc_lower = self.I(lambda x: self.kc_middle - (self.kc_mult * self.atr))
        
        # TTM Squeeze calculation
        self.squeeze_on = self.I(lambda: (self.bb_lower > self.kc_lower) & (self.bb_upper < self.kc_upper))
        
        # Momentum histogram (simplified using MACD)
        self.macd, self.macd_signal, self.macd_hist = self.I(ta.MACD, self.data.Close, 
                                                            fastperiod=12, slowperiod=26, signalperiod=9)
        
        # Volume indicator
        self.volume_sma = self.I(ta.SMA, self.data.Volume, timeperiod=20)
        
        # Swing highs and lows for stop placement
        self.swing_high = self.I(ta.MAX, self.data.High, timeperiod=10)
        self.swing_low = self.I(ta.MIN, self.data.Low, timeperiod=10)
        
        # Track trades per day
        self.trades_today = 0
        self.current_date = None
        
        print("🌙 Moon Dev TTMomentum Strategy Initialized! 🚀")

    def next(self):
        current_time = self.data.index[-1]
        current_date = current_time.date()
        
        # Reset daily trade counter
        if self.current_date != current_date:
            self.trades_today = 0
            self.current_date = current_date
        
        # Skip if we've reached daily trade limit
        if self.trades_today >= 3:
            return
        
        # Get current values
        price = self.data.Close[-1]
        volume = self.data.Volume[-1]
        
        # Check for squeeze conditions
        squeeze_active = self.squeeze_on[-1]
        was_squeeze_active = any(self.squeeze_on[-self.squeeze_lookback:-1]) if len(self.squeeze_on) > self.squeeze_lookback else False
        
        # Momentum signals
        momentum_hist = self.macd_hist[-1]
        prev_momentum_hist = self.macd_hist[-2] if len(self.macd_hist) > 2 else 0
        
        # Volume confirmation
        volume_above_avg = volume > self.volume_sma[-1]
        
        # Risk management
        account_equity = self.equity
        risk_per_trade = account_equity * 0.02  # 2% risk per trade
        
        # LONG ENTRY CONDITIONS
        if (not self.position and 
            was_squeeze_active and not squeeze_active and  # Coming out of squeeze
            momentum_hist > 0 and prev_momentum_hist <= 0 and  # First green momentum bar
            price > self.swing_high[-2] and  # Break above recent high
            volume_above_avg):
            
            # Calculate position size
            stop_price = self.swing_low[-1]
            risk_per_share = price - stop_price
            if risk_per_share > 0:
                position_size = risk_per_trade / risk_per_share
                position_size = int(round(position_size))
                
                if position_size > 0:
                    self.buy(size=position_size, sl=stop_price)
                    self.trades_today += 1
                    print(f"🌙 MOON ENTRY! 🚀 LONG TSLA at {price:.2f}, Size: {position_size}, Stop: {stop_price:.2f}")
        
        # SHORT ENTRY CONDITIONS  
        elif (not self.position and 
              was_squeeze_active and not squeeze_active and  # Coming out of squeeze
              momentum_hist < 0 and prev_momentum_hist >= 0 and  # First red momentum bar
              price < self.swing_low[-2] and  # Break below recent low
              volume_above_avg):
            
            # Calculate position size
            stop_price = self.swing_high[-1]
            risk_per_share = stop_price - price
            if risk_per_share > 0:
                position_size = risk_per_trade / risk_per_share
                position_size = int(round(position_size))
                
                if position_size > 0:
                    self.sell(size=position_size, sl=stop_price)
                    self.trades_today += 1
                    print(f"🌙 MOON ENTRY! 📉 SHORT TSLA at {price:.2f}, Size: {position_size}, Stop: {stop_price:.2f}")
        
        # EXIT CONDITIONS for existing positions
        if self.position:
            if self.position.is_long:
                # Long exit conditions
                if (momentum_hist < 0 or  # Momentum turns red
                    price < self.swing_low[-1]):  # Price breaks below swing low
                    
                    print(f"🌙 MOON EXIT! 📊 Closing LONG at {price:.2f}")
                    self.position.close()
            
            elif self.position.is_short:
                # Short exit conditions
                if (momentum_hist > 0 or  # Momentum turns green
                    price > self.swing_high[-1]):  # Price breaks above swing high
                    
                    print(f"🌙 MOON EXIT! 📊 Closing SHORT at {price:.2f}")
                    self.position.close()

# Load and prepare data
def load_data():
    data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
    data = pd.read_csv(data_path)
    
    # Clean column names
    data.columns = data.columns.str.strip().str.lower()
    
    # Drop unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    
    # Ensure proper column mapping
    column_mapping = {
        'open': 'Open',
        'high': 'High', 
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }
    
    data = data.rename(columns=column_mapping)
    data['DateTime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('DateTime')
    
    # Ensure required columns exist
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required_cols:
        if col not in data.columns:
            raise ValueError(f"Missing required column: {col}")
    
    return data

# Run backtest
if __name__ == "__main__":
    print("🌙 Moon Dev TTMomentum Backtest Starting... 🚀")
    
    data = load_data()
    
    bt = Backtest(
        data,
        TTMomentum,
        cash=1000000,
        commission=0.001,
        exclusive_orders=True
    )
    
    stats = bt.run()
    print("🌙 MOON DEV BACKTEST COMPLETE! ✨")
    print(stats)
    print(stats._strategy)