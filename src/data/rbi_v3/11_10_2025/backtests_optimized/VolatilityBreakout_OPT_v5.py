import yfinance as yf
import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

def load_data():
    ticker = yf.Ticker("SPY")
    data = ticker.history(period="2y", interval="1h")
    data.columns = data.columns.str.strip()
    required = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in data.columns for col in required):
        raise ValueError(f"Missing required columns. Got: {list(data.columns)}")
    return data

class VolatilityBreakout(Strategy):
    # 🌙 OPTIMIZED PARAMETERS FOR HIGHER RETURNS
    bb_period = 14  # Reduced for faster signal detection
    bb_std = 1.8    # Tighter bands for earlier breakouts
    rsi_period = 10  # Faster RSI for momentum confirmation
    volume_multiplier = 1.5  # Higher volume requirement for stronger signals
    risk_per_trade = 0.03    # Increased risk for higher returns
    
    # 🌙 ADDED OPTIMIZATION PARAMETERS
    atr_multiplier_sl = 1.5  # Tighter stops using ATR
    atr_multiplier_tp = 2.5  # Better risk-reward ratio
    min_bb_width = 0.02      # Filter low volatility periods
    trend_filter_period = 50  # EMA trend filter
    
    def init(self):
        close = self.data.Close.astype(float)
        high = self.data.High.astype(float)
        low = self.data.Low.astype(float)
        volume = self.data.Volume.astype(float)
        
        # 🌙 CORE INDICATORS
        bb_bands = self.I(talib.BBANDS, close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)
        self.bb_upper = bb_bands[0]
        self.bb_middle = bb_bands[1]
        self.bb_lower = bb_bands[2]
        self.volume_sma = self.I(talib.SMA, volume, timeperiod=20)
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=14)
        
        # 🌙 ADDED OPTIMIZATION INDICATORS
        self.bb_width = self.I(lambda: (self.bb_upper - self.bb_lower) / self.bb_middle)
        self.ema_fast = self.I(talib.EMA, close, timeperiod=20)   # Fast trend
        self.ema_slow = self.I(talib.EMA, close, timeperiod=50)   # Slow trend
        self.macd, self.macd_signal, _ = self.I(talib.MACD, close, fastperiod=12, slowperiod=26, signalperiod=9)
        
        self.breakout_signal = 0
        self.position_count = 0

    def next(self):
        if len(self.data) < 51:  # Increased for trend filter
            return
            
        current_close = self.data.Close[-1]
        current_volume = self.data.Volume[-1]
        bb_upper = self.bb_upper[-1]
        bb_lower = self.bb_lower[-1]
        bb_middle = self.bb_middle[-1]
        volume_sma = self.volume_sma[-1]
        rsi = self.rsi[-1]
        atr = self.atr[-1]
        bb_width = self.bb_width[-1]
        ema_fast = self.ema_fast[-1]
        ema_slow = self.ema_slow[-1]
        macd = self.macd[-1] if self.macd is not None else 0
        macd_signal = self.macd_signal[-1] if self.macd_signal is not None else 0
        
        # 🌙 IMPROVED MARKET REGIME FILTERS
        avg_bb_width = np.mean(self.bb_width[-10:-1]) if len(self.bb_width) > 10 else bb_width
        is_squeeze = bb_width < avg_bb_width * 0.6  # Tighter squeeze condition
        volume_confirmed = current_volume > volume_sma * self.volume_multiplier
        is_uptrend = ema_fast > ema_slow  # Trend filter
        is_downtrend = ema_fast < ema_slow
        macd_bullish = macd > macd_signal  # Momentum confirmation
        macd_bearish = macd < macd_signal
        
        # 🌙 MINIMUM VOLATILITY FILTER
        if bb_width < self.min_bb_width:
            return  # Skip low volatility periods
        
        if not self.position:
            # 🌙 IMPROVED ENTRY CONDITIONS WITH MULTIPLE CONFIRMATIONS
            if is_squeeze and volume_confirmed:
                # LONG SETUP: Breakout + Trend + Momentum + RSI filter
                if (current_close > bb_upper and rsi < 65 and 
                    is_uptrend and macd_bullish):
                    self.breakout_signal = 1
                    print(f"🌙 MOON DEV: OPTIMIZED LONG BREAKOUT - Close: {current_close:.2f}, BB Upper: {bb_upper:.2f}, Volume: {current_volume:.0f}, RSI: {rsi:.1f}")
                    
                # SHORT SETUP: Breakdown + Trend + Momentum + RSI filter  
                elif (current_close < bb_lower and rsi > 35 and 
                      is_downtrend and macd_bearish):
                    self.breakout_signal = -1
                    print(f"🌙 MOON DEV: OPTIMIZED SHORT BREAKOUT - Close: {current_close:.2f}, BB Lower: {bb_lower:.2f}, Volume: {current_volume:.0f}, RSI: {rsi:.1f}")
            
            elif self.breakout_signal != 0:
                entry_price = self.data.Open[-1]
                risk_amount = self.equity * self.risk_per_trade
                
                if self.breakout_signal == 1:
                    # 🌙 IMPROVED ATR-BASED STOP LOSS & TAKE PROFIT
                    stop_loss_price = entry_price - (self.atr_multiplier_sl * atr)
                    take_profit_price = entry_price + (self.atr_multiplier_tp * atr)
                    
                    # 🌙 VALIDATE LONG ORDER: SL < Entry < TP
                    if stop_loss_price >= entry_price or take_profit_price <= entry_price:
                        print(f"🌙 MOON DEV: Long order validation failed - SL: {stop_loss_price:.2f}, Entry: {entry_price:.2f}, TP: {take_profit_price:.2f}")
                        self.breakout_signal = 0
                        return
                    
                    risk_per_share = entry_price - stop_loss_price
                    if risk_per_share > 0:
                        position_size = int(round(risk_amount / risk_per_share))
                        max_position_size = int(self.equity * 0.15 / entry_price)  # Increased position limit
                        position_size = min(position_size, max_position_size)
                        
                        if position_size > 0:
                            self.buy(size=position_size, sl=stop_loss_price, tp=take_profit_price)
                            print(f"🚀 MOON DEV: ENTERED OPTIMIZED LONG - Size: {position_size}, Entry: {entry_price:.2f}, SL: {stop_loss_price:.2f}, TP: {take_profit_price:.2f}, R:R: {((take_profit_price-entry_price)/(entry_price-stop_loss_price)):.2f}")
                            self.breakout_signal = 0
                
                elif self.breakout_signal == -1:
                    # 🌙 IMPROVED ATR-BASED STOP LOSS & TAKE PROFIT
                    take_profit_price = entry_price - (self.atr_multiplier_tp * atr)
                    stop_loss_price = entry_price + (self.atr_multiplier_sl * atr)
                    
                    # 🌙 VALIDATE SHORT ORDER: TP < Entry < SL
                    if take_profit_price >= entry_price or stop_loss_price <= entry_price:
                        print(f"🌙 MOON DEV: Short order validation failed - TP: {take_profit_price:.2f}, Entry: {entry_price:.2f}, SL: {stop_loss_price:.2f}")
                        self.breakout_signal = 0
                        return
                    
                    risk_per_share = stop_loss_price - entry_price
                    if risk_per_share > 0:
                        position_size = int(round(risk_amount / risk_per_share))
                        max_position_size = int(self.equity * 0.15 / entry_price)  # Increased position limit
                        position_size = min(position_size, max_position_size)
                        
                        if position_size > 0:
                            self.sell(size=position_size, sl=stop_loss_price, tp=take_profit_price)
                            print(f"🌙 MOON DEV: ENTERED OPTIMIZED SHORT - Size: {position_size}, Entry: {entry_price:.2f}, SL: {stop_loss_price:.2f}, TP: {take_profit_price:.2f}, R:R: {((entry_price-take_profit_price)/(stop_loss_price-entry_price)):.2f}")
                            self.breakout_signal = 0
        
        else:
            # 🌙 IMPROVED EXIT MONITORING
            if self.position.is_long:
                if current_close <= self.position.sl or current_close >= self.position.tp:
                    print(f"✨ MOON DEV: LONG EXIT - Price: {current_close:.2f}, P&L: {self.position.pl:.2f}, P&L%: {(self.position.pl/self.position.size/self.position.entry_price)*100:.2f}%")
            
            elif self.position.is_short:
                if current_close >= self.position.sl or current_close <= self.position.tp:
                    print(f"✨ MOON DEV: SHORT EXIT - Price: {current_close:.2f}, P&L: {self.position.pl:.2f}, P&L%: {(self.position.pl/self.position.size/self.position.entry_price)*100:.2f}%")

data = load_data()
bt = Backtest(data, VolatilityBreakout, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)