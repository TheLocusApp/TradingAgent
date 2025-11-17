"""
AGBot SHORTS OPTIMIZED - Simplified Backtest
Tests the strategy logic on QQQ 1H data (2 years)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover


def crossunder(a, b):
    """Detect crossunder"""
    return crossover(b, a)


class AGBotShortsOptimized(Strategy):
    """AGBot with longs (META exact) + shorts (swing high optimized)"""
    
    # Parameters
    risk_per_trade_pct = 2.5
    ma_length = 100
    key_value = 2.0
    atr_period_ut = 1
    atr_period = 14
    swing_high_bars = 10
    swing_low_bars = 10
    adaptive_atr_mult = 2.0
    tp1_rr_long = 1.0
    tp2_rr_long = 3.0
    tp1_percent = 35.0
    use_tp = True
    num_tps = 2
    second_tp_type = "atr_trailing"
    
    # Shorts
    use_ema_filter_shorts = True
    use_regime_shorts = True
    use_swing_high_shorts = True
    swing_high_bars_shorts = 5
    tp1_rr_short = 1.5
    tp2_rr_short = 3.0
    tp1_percent_shorts = 70.0
    bull_market_risk_reduction = 0.5
    
    trading_mode = "both"
    
    def init(self):
        """Initialize indicators"""
        # Simple EMA
        self.ema = self.I(lambda x: pd.Series(x).ewm(span=self.ma_length).mean(), self.data.Close)
        
        # Simple ATR
        def calc_atr():
            high = np.asarray(self.data.High)
            low = np.asarray(self.data.Low)
            close = np.asarray(self.data.Close)
            
            tr = np.zeros(len(close))
            for i in range(len(close)):
                if i == 0:
                    tr[i] = high[i] - low[i]
                else:
                    tr[i] = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
            
            atr = pd.Series(tr).rolling(self.atr_period).mean()
            return atr.values
        
        self.atr = self.I(calc_atr)
        
        # Simple trailing stop (UT Bot approximation)
        def calc_trail():
            close = np.asarray(self.data.Close)
            atr = np.asarray(self.atr)
            trail = np.zeros(len(close))
            
            for i in range(len(close)):
                if i == 0:
                    trail[i] = close[i]
                else:
                    n_loss = self.key_value * atr[i] if not np.isnan(atr[i]) else 0
                    if close[i] > trail[i-1]:
                        trail[i] = max(trail[i-1], close[i] - n_loss)
                    elif close[i] < trail[i-1]:
                        trail[i] = min(trail[i-1], close[i] + n_loss)
                    else:
                        trail[i] = trail[i-1]
            
            return trail
        
        self.trail = self.I(calc_trail)
        
        # Regime (SMA 50/200)
        self.sma50 = self.I(lambda x: pd.Series(x).rolling(50).mean(), self.data.Close)
        self.sma200 = self.I(lambda x: pd.Series(x).rolling(200).mean(), self.data.Close)
        
        # EMA Ribbon
        self.ema13 = self.I(lambda x: pd.Series(x).ewm(span=13).mean(), self.data.Close)
        self.ema48 = self.I(lambda x: pd.Series(x).ewm(span=48).mean(), self.data.Close)
        self.ema200 = self.I(lambda x: pd.Series(x).ewm(span=200).mean(), self.data.Close)
        
        # Signals
        def calc_buy_sig():
            return crossover(np.asarray(self.data.Close), np.asarray(self.trail))
        
        def calc_sell_sig():
            return crossunder(np.asarray(self.data.Close), np.asarray(self.trail))
        
        self.buy_sig = self.I(calc_buy_sig)
        self.sell_sig = self.I(calc_sell_sig)
        
        # Tracking
        self.entry_price = None
        self.initial_sl = None
        self.tp1_hit = False
        self.hi_since = None
        self.lo_since = None
    
    def next(self):
        """Execute strategy on each bar"""
        if self.position:
            self._manage_position()
            return
        
        # Determine stops
        long_stop = self.data.Close[-1] - self.atr[-1] * self.adaptive_atr_mult if not np.isnan(self.atr[-1]) else self.data.Close[-1] - 1
        short_stop = self.data.Close[-1] + self.atr[-1] * self.adaptive_atr_mult if not np.isnan(self.atr[-1]) else self.data.Close[-1] + 1
        
        # Trend
        bullish = self.data.Close[-1] > self.ema[-1]
        bearish = self.data.Close[-1] < self.ema[-1]
        
        # Regime
        is_bull_regime = self.sma50[-1] > self.sma200[-1] if not np.isnan(self.sma50[-1]) and not np.isnan(self.sma200[-1]) else True
        
        # EMA alignment (for shorts)
        bear_alignment = (self.data.Close[-1] < self.ema13[-1] and 
                         self.ema13[-1] < self.ema48[-1] and 
                         self.ema48[-1] < self.ema200[-1]) if (not np.isnan(self.ema13[-1]) and not np.isnan(self.ema48[-1]) and not np.isnan(self.ema200[-1])) else True
        
        allow_longs = self.trading_mode in ["longs_only", "both"]
        allow_shorts = self.trading_mode in ["shorts_only", "both"]
        
        # LONG ENTRY (100% META - NO FILTERS!)
        if allow_longs and self.buy_sig[-1] and bullish:
            qty_l = self._calc_qty_long(self.data.Close[-1], long_stop)
            if qty_l > 0:
                self.buy(size=qty_l)
                self.entry_price = self.data.Close[-1]
                self.initial_sl = long_stop
                self.tp1_hit = False
                self.hi_since = self.data.High[-1]
                self.lo_since = None
        
        # SHORT ENTRY (with regime-aware filters)
        elif allow_shorts and self.sell_sig[-1] and bearish and bear_alignment:
            qty_s = self._calc_qty_short(self.data.Close[-1], short_stop, is_bull_regime)
            if qty_s > 0:
                self.sell(size=qty_s)
                self.entry_price = self.data.Close[-1]
                self.initial_sl = short_stop
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
        
        # LONG management
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
                else:
                    if self.hi_since:
                        trail_stop = self.hi_since - self.atr[-1] * self.adaptive_atr_mult if not np.isnan(self.atr[-1]) else self.hi_since - 1
                        if self.data.Low[-1] <= trail_stop:
                            self.position.close()
            
            # SL
            if self.data.Low[-1] <= self.initial_sl:
                self.position.close()
        
        # SHORT management
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
                else:
                    if self.lo_since:
                        trail_stop = self.lo_since + self.atr[-1] * self.adaptive_atr_mult if not np.isnan(self.atr[-1]) else self.lo_since + 1
                        if self.data.High[-1] >= trail_stop:
                            self.position.close()
            
            # SL
            if self.data.High[-1] >= self.initial_sl:
                self.position.close()
    
    def _calc_qty_long(self, price, stop):
        """Calculate position size for long"""
        if price <= stop:
            return 0.0
        
        equity = self.equity
        risk_amt = equity * (self.risk_per_trade_pct / 100.0)
        dist = price - stop
        
        if dist <= 0:
            return 0.0
        
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
    
    # Fetch data
    print("\n📊 Fetching QQQ 1H data (2 years)...")
    ticker = "QQQ"
    data = yf.download(ticker, period="2y", interval="1h", progress=False)
    
    # Clean data
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data.columns = data.columns.str.strip()
    
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
    print("BACKTEST RESULTS - QQQ 1H (2 Years)")
    print("=" * 80)
    print(f"\n💰 RETURNS:")
    print(f"   Total Return:           {stats['Return [%]']:.2f}%")
    print(f"   Annual Return:          {stats['Return (Ann.) [%]']:.2f}%")
    
    print(f"\n📊 RISK METRICS:")
    print(f"   Sharpe Ratio:           {stats['Sharpe Ratio']:.2f}")
    print(f"   Max Drawdown:           {stats['Max. Drawdown [%]']:.2f}%")
    print(f"   Profit Factor:          {stats['Profit Factor']:.2f}")
    
    print(f"\n🎯 TRADE STATISTICS:")
    print(f"   Total Trades:           {stats['# Trades']:.0f}")
    print(f"   Win Rate:               {stats['Win Rate [%]']:.2f}%")
    print(f"   Avg Trade:              {stats['Avg. Trade [%]']:.2f}%")
    print(f"   Best Trade:             {stats['Best Trade [%]']:.2f}%")
    print(f"   Worst Trade:            {stats['Worst Trade [%]']:.2f}%")
    print(f"   Consecutive Wins:       {stats['Consecutive Wins']:.0f}")
    print(f"   Consecutive Losses:     {stats['Consecutive Losses']:.0f}")
    
    print(f"\n💵 CAPITAL:")
    print(f"   Starting Equity:        ${stats['Start']:.2f}")
    print(f"   Final Equity:           ${stats['_equity_final']:.2f}")
    print(f"   Period:                 {stats['Start']} to {stats['End']}")
    
    print("\n" + "=" * 80)
    
    # Plot
    print("\n📈 Generating chart...")
    bt.plot(filename='agbot_shorts_optimized_backtest.html', open_browser=False)
    print("   Chart saved to: agbot_shorts_optimized_backtest.html")
    
    return stats


if __name__ == "__main__":
    stats = run_backtest()
