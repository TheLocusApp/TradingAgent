"""
AGBot SHORTS OPTIMIZED Backtest
Converts Pine Script strategy to backtesting.py
Tests on QQQ 1H timeframe (2 years of data)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import talib


def crossunder(a, b):
    """Detect crossunder"""
    return crossover(b, a)


class AGBotShortsOptimized(Strategy):
    """
    AGBot strategy with:
    - Longs: 100% META (exact clone, no filters)
    - Shorts: Swing High stops + EMA filter + regime-based sizing
    """
    
    # ===== PARAMETERS =====
    # Capital
    risk_per_trade_pct = 2.5
    
    # Session (9:30 AM - 4:00 PM EST)
    sess_start_hour = 9
    sess_start_minute = 30
    sess_end_hour = 16
    sess_end_minute = 0
    enable_eod_close = True
    
    # Indicators (META EXACT)
    ma_length = 100
    key_value = 2.0
    atr_period_ut = 1
    atr_period = 14
    
    # Longs (META EXACT - NO CHANGES)
    stoploss_type = "atr"  # "atr" or "swing"
    swing_high_bars = 10
    swing_low_bars = 10
    adaptive_atr_mult = 2.0
    tp1_rr_long = 1.0
    tp2_rr_long = 3.0
    tp1_percent = 35.0
    
    # Take Profit
    use_tp = True
    num_tps = 2
    second_tp_type = "atr_trailing"  # "rr" or "atr_trailing"
    
    # Shorts Optimization
    use_ema_filter_shorts = True
    use_regime_shorts = True
    use_swing_high_shorts = True
    swing_high_bars_shorts = 5
    tp1_rr_short = 1.5
    tp2_rr_short = 3.0
    tp1_percent_shorts = 70.0
    bull_market_risk_reduction = 0.5
    
    # Trading mode
    trading_mode = "both"  # "longs_only", "shorts_only", "both"
    
    def init(self):
        """Initialize indicators"""
        # Pre-calculate all indicators on full data
        close = np.asarray(self.data.Close, dtype=float)
        high = np.asarray(self.data.High, dtype=float)
        low = np.asarray(self.data.Low, dtype=float)
        
        # EMA
        ema_val = talib.EMA(close, self.ma_length)
        self.ema_val = self.I(pd.Series, ema_val, name="ema")
        
        # ATR
        atr14 = talib.ATR(high, low, close, self.atr_period)
        self.atr14 = self.I(pd.Series, atr14, name="atr14")
        
        # UT Bot ATR Trailing Stop
        true_range_ut = np.zeros(len(close))
        for i in range(len(close)):
            if i == 0:
                tr = high[i] - low[i]
            else:
                tr = max(
                    high[i] - low[i],
                    abs(high[i] - close[i-1]),
                    abs(low[i] - close[i-1])
                )
            true_range_ut[i] = tr
        
        atr_ut = talib.SMA(true_range_ut, self.atr_period_ut)
        n_loss = self.key_value * atr_ut
        
        trail = np.zeros(len(close))
        for i in range(len(close)):
            if i == 0:
                trail[i] = close[i]
            else:
                if close[i] > trail[i-1]:
                    trail[i] = max(trail[i-1], close[i] - n_loss[i])
                elif close[i] < trail[i-1]:
                    trail[i] = min(trail[i-1], close[i] + n_loss[i])
                else:
                    if close[i-1] > trail[i-1]:
                        trail[i] = close[i] - n_loss[i]
                    else:
                        trail[i] = close[i] + n_loss[i]
        
        self.ut_trail = self.I(pd.Series, trail, name="ut_trail")
        
        # Swing stops
        long_stop_swing = talib.LOWEST(low, self.swing_low_bars)
        self.long_stop_swing = self.I(pd.Series, long_stop_swing, name="long_stop_swing")
        
        short_stop_swing = talib.HIGHEST(high, self.swing_high_bars_shorts)
        self.short_stop_swing = self.I(pd.Series, short_stop_swing, name="short_stop_swing")
        
        # Regime detection (SMA 50/200)
        sma50 = talib.SMA(close, 50)
        self.sma50 = self.I(pd.Series, sma50, name="sma50")
        
        sma200 = talib.SMA(close, 200)
        self.sma200 = self.I(pd.Series, sma200, name="sma200")
        
        # EMA Ribbon (for shorts)
        ema13 = talib.EMA(close, 13)
        self.ema13 = self.I(pd.Series, ema13, name="ema13")
        
        ema48 = talib.EMA(close, 48)
        self.ema48 = self.I(pd.Series, ema48, name="ema48")
        
        ema200 = talib.EMA(close, 200)
        self.ema200 = self.I(pd.Series, ema200, name="ema200")
        
        # Signals
        buy_signal = crossover(close, trail)
        self.buy_signal = self.I(pd.Series, buy_signal.astype(float), name="buy_signal")
        
        sell_signal = crossunder(close, trail)
        self.sell_signal = self.I(pd.Series, sell_signal.astype(float), name="sell_signal")
        
        # Tracking
        self.entry_price = None
        self.initial_sl = None
        self.tp1_hit = False
        self.hi_since = None
        self.lo_since = None
    
    def next(self):
        """Execute strategy logic on each bar"""
        # Skip if we have a position
        if self.position:
            self._manage_position()
            return
        
        # Check if in session
        if not self._in_session():
            return
        
        # Determine stops
        long_stop_chosen = self.long_stop_swing[-1] if self.stoploss_type == "swing" else (self.data.Close[-1] - self.atr14[-1] * self.adaptive_atr_mult)
        short_stop_chosen = self.short_stop_swing[-1] if (self.use_swing_high_shorts and self.use_regime_shorts) else (self.data.Close[-1] + self.atr14[-1] * self.adaptive_atr_mult)
        
        # Trend
        bullish = self.data.Close[-1] > self.ema_val[-1]
        bearish = self.data.Close[-1] < self.ema_val[-1]
        
        # Regime
        is_bull_regime = self.sma50[-1] > self.sma200[-1] if self.use_regime_shorts else True
        is_bear_regime = self.sma50[-1] < self.sma200[-1] if self.use_regime_shorts else False
        
        # EMA alignment (for shorts)
        bear_alignment = (self.data.Close[-1] < self.ema13[-1] and 
                         self.ema13[-1] < self.ema48[-1] and 
                         self.ema48[-1] < self.ema200[-1]) if self.use_ema_filter_shorts else True
        
        allow_longs = self.trading_mode in ["longs_only", "both"]
        allow_shorts = self.trading_mode in ["shorts_only", "both"]
        
        # LONG ENTRY (100% META - NO FILTERS!)
        if allow_longs and self.buy_signal[-1] and bullish and not np.isnan(long_stop_chosen):
            qty_l = self._calc_qty_long(self.data.Close[-1], long_stop_chosen)
            if qty_l > 0:
                self.buy(size=qty_l)
                self.entry_price = self.data.Close[-1]
                self.initial_sl = long_stop_chosen
                self.tp1_hit = False
                self.hi_since = self.data.High[-1]
                self.lo_since = None
        
        # SHORT ENTRY (with regime-aware filters)
        elif allow_shorts and self.sell_signal[-1] and bearish and bear_alignment and not np.isnan(short_stop_chosen):
            qty_s = self._calc_qty_short(self.data.Close[-1], short_stop_chosen, is_bull_regime)
            if qty_s > 0:
                self.sell(size=qty_s)
                self.entry_price = self.data.Close[-1]
                self.initial_sl = short_stop_chosen
                self.tp1_hit = False
                self.lo_since = self.data.Low[-1]
                self.hi_since = None
    
    def _manage_position(self):
        """Manage open positions"""
        if not self.position:
            return
        
        # Update extremes
        if self.position.is_long:
            self.hi_since = max(self.hi_since or self.data.High[-1], self.data.High[-1])
        else:
            self.lo_since = min(self.lo_since or self.data.Low[-1], self.data.Low[-1])
        
        # Calculate SL distance
        if self.position.is_long and self.entry_price and self.initial_sl:
            sl_dist = self.entry_price - self.initial_sl
            
            # TP1
            if self.use_tp and not self.tp1_hit:
                tp1_long = self.entry_price + sl_dist * self.tp1_rr_long
                if self.data.High[-1] >= tp1_long:
                    self.position.close(qty_percent=self.tp1_percent / 100.0)
                    self.tp1_hit = True
            
            # TP2
            if self.use_tp and self.num_tps == 2 and self.tp1_hit:
                if self.second_tp_type == "rr":
                    tp2_long = self.entry_price + sl_dist * self.tp2_rr_long
                    if self.data.High[-1] >= tp2_long:
                        self.position.close()
                else:  # atr_trailing
                    if self.hi_since:
                        trail_stop_l = self.hi_since - self.atr14[-1] * self.adaptive_atr_mult
                        if self.data.Low[-1] <= trail_stop_l:
                            self.position.close()
            
            # SL
            if self.data.Low[-1] <= self.initial_sl:
                self.position.close()
        
        elif self.position.is_short and self.entry_price and self.initial_sl:
            sl_dist = self.initial_sl - self.entry_price
            
            # TP1
            if self.use_tp and not self.tp1_hit:
                tp1_short = self.entry_price - sl_dist * self.tp1_rr_short
                if self.data.Low[-1] <= tp1_short:
                    self.position.close(qty_percent=self.tp1_percent_shorts / 100.0)
                    self.tp1_hit = True
            
            # TP2
            if self.use_tp and self.num_tps == 2 and self.tp1_hit:
                if self.second_tp_type == "rr":
                    tp2_short = self.entry_price - sl_dist * self.tp2_rr_short
                    if self.data.Low[-1] <= tp2_short:
                        self.position.close()
                else:  # atr_trailing
                    if self.lo_since:
                        trail_stop_s = self.lo_since + self.atr14[-1] * self.adaptive_atr_mult
                        if self.data.High[-1] >= trail_stop_s:
                            self.position.close()
            
            # SL
            if self.data.High[-1] >= self.initial_sl:
                self.position.close()
    
    def _in_session(self):
        """Check if current bar is in trading session"""
        # Simplified: assume all bars are in session for backtest
        # In live trading, would check actual time
        return True
    
    def _calc_qty_long(self, price, stop):
        """Calculate position size for long"""
        if price <= stop:
            return 0.0
        
        equity = self.equity
        risk_amt = equity * (self.risk_per_trade_pct / 100.0)
        dist = price - stop
        
        if dist <= 0:
            return 0.0
        
        # Position size = risk / (distance * point value)
        # For stocks: point value = 1
        qty = risk_amt / dist
        return max(0, qty)
    
    def _calc_qty_short(self, price, stop, is_bull_regime):
        """Calculate position size for short"""
        if stop <= price:
            return 0.0
        
        equity = self.equity
        
        # Reduce risk in bull markets
        if self.use_regime_shorts and is_bull_regime:
            risk_amt = equity * (self.risk_per_trade_pct / 100.0) * self.bull_market_risk_reduction
        else:
            risk_amt = equity * (self.risk_per_trade_pct / 100.0)
        
        dist = stop - price
        
        if dist <= 0:
            return 0.0
        
        qty = risk_amt / dist
        return max(0, qty)


def run_backtest():
    """Run the backtest"""
    print("=" * 80)
    print("AGBot SHORTS OPTIMIZED - Backtest")
    print("=" * 80)
    
    # Fetch data (QQQ 1H, 2 years)
    print("\n📊 Fetching QQQ 1H data (2 years)...")
    ticker = "QQQ"
    data = yf.download(ticker, period="2y", interval="1h", progress=False)
    
    # Clean data - handle MultiIndex
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data.columns = data.columns.str.strip()
    
    # Ensure required columns
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required_cols:
        if col not in data.columns:
            raise ValueError(f"Missing required column: {col}")
    
    print(f"   Loaded {len(data)} bars")
    print(f"   Date range: {data.index[0]} to {data.index[-1]}")
    
    # Run backtest
    print("\n⚙️  Running backtest...")
    bt = Backtest(data, AGBotShortsOptimized, 
                  cash=10000, 
                  commission=0.0,
                  exclusive_orders=True)
    
    stats = bt.run()
    
    # Display results
    print("\n" + "=" * 80)
    print("BACKTEST RESULTS")
    print("=" * 80)
    print(f"\nTotal Return:           {stats['Return [%]']:.2f}%")
    print(f"Annual Return:          {stats['Return (Ann.) [%]']:.2f}%")
    print(f"Sharpe Ratio:           {stats['Sharpe Ratio']:.2f}")
    print(f"Max Drawdown:           {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate:               {stats['Win Rate [%]']:.2f}%")
    print(f"Profit Factor:          {stats['Profit Factor']:.2f}")
    print(f"Trades:                 {stats['# Trades']:.0f}")
    print(f"Avg Trade:              {stats['Avg. Trade [%]']:.2f}%")
    print(f"Best Trade:             {stats['Best Trade [%]']:.2f}%")
    print(f"Worst Trade:            {stats['Worst Trade [%]']:.2f}%")
    print(f"Consecutive Wins:       {stats['Consecutive Wins']:.0f}")
    print(f"Consecutive Losses:     {stats['Consecutive Losses']:.0f}")
    print(f"Equity Final:           ${stats['_equity_final']:.2f}")
    print(f"Start:                  {stats['Start']}")
    print(f"End:                    {stats['End']}")
    
    print("\n" + "=" * 80)
    
    # Plot
    print("\n📈 Generating chart...")
    bt.plot(filename='agbot_shorts_optimized_backtest.html', open_browser=False)
    print("   Chart saved to: agbot_shorts_optimized_backtest.html")
    
    return stats


if __name__ == "__main__":
    stats = run_backtest()
