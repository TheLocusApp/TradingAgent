"""
AGBot SHORTS OPTIMIZED - Final Backtest
Simplified approach: pre-calculate all indicators
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
    atr_period = 14
    swing_high_bars_shorts = 5
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
    tp1_rr_short = 1.5
    tp2_rr_short = 3.0
    tp1_percent_shorts = 70.0
    bull_market_risk_reduction = 0.5
    
    trading_mode = "both"
    
    def init(self):
        """Initialize - all indicators pre-calculated"""
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
        
        # Get current values from data columns
        close = self.data.Close[-1]
        high = self.data.High[-1]
        low = self.data.Low[-1]
        ema = self.data.ema[-1]
        atr = self.data.atr[-1]
        trail = self.data.trail[-1]
        sma50 = self.data.sma50[-1]
        sma200 = self.data.sma200[-1]
        ema13 = self.data.ema13[-1]
        ema48 = self.data.ema48[-1]
        ema200 = self.data.ema200[-1]
        buy_sig = self.data.buy_sig[-1]
        sell_sig = self.data.sell_sig[-1]
        
        # Determine stops
        long_stop = close - atr * self.adaptive_atr_mult if not np.isnan(atr) else close - 1
        short_stop = close + atr * self.adaptive_atr_mult if not np.isnan(atr) else close + 1
        
        # Trend
        bullish = close > ema
        bearish = close < ema
        
        # Regime
        is_bull_regime = sma50 > sma200 if not np.isnan(sma50) and not np.isnan(sma200) else True
        
        # EMA alignment (for shorts)
        bear_alignment = (close < ema13 and 
                         ema13 < ema48 and 
                         ema48 < ema200) if (not np.isnan(ema13) and not np.isnan(ema48) and not np.isnan(ema200)) else True
        
        allow_longs = self.trading_mode in ["longs_only", "both"]
        allow_shorts = self.trading_mode in ["shorts_only", "both"]
        
        # LONG ENTRY (100% META - NO FILTERS!)
        if allow_longs and buy_sig and bullish:
            qty_l = self._calc_qty_long(close, long_stop)
            if qty_l > 0:
                self.buy(size=qty_l)
                self.entry_price = close
                self.initial_sl = long_stop
                self.tp1_hit = False
                self.hi_since = high
                self.lo_since = None
        
        # SHORT ENTRY (with regime-aware filters)
        elif allow_shorts and sell_sig and bearish and bear_alignment:
            qty_s = self._calc_qty_short(close, short_stop, is_bull_regime)
            if qty_s > 0:
                self.sell(size=qty_s)
                self.entry_price = close
                self.initial_sl = short_stop
                self.tp1_hit = False
                self.lo_since = low
                self.hi_since = None
    
    def _manage_position(self):
        """Manage open positions"""
        if not self.position:
            return
        
        # Get current values
        high = self.data.High[-1]
        low = self.data.Low[-1]
        atr = self.data.atr[-1]
        
        # Update extremes
        if self.position.is_long:
            self.hi_since = max(self.hi_since or high, high)
        else:
            self.lo_since = min(self.lo_since or low, low)
        
        # LONG management
        if self.position.is_long and self.entry_price and self.initial_sl:
            sl_dist = self.entry_price - self.initial_sl
            
            # TP1
            if self.use_tp and not self.tp1_hit:
                tp1_long = self.entry_price + sl_dist * self.tp1_rr_long
                if high >= tp1_long:
                    self.tp1_hit = True
            
            # TP2 or SL
            if self.tp1_hit:
                if self.second_tp_type == "rr":
                    tp2_long = self.entry_price + sl_dist * self.tp2_rr_long
                    if high >= tp2_long:
                        self.position.close()
                else:
                    if self.hi_since:
                        trail_stop = self.hi_since - atr * self.adaptive_atr_mult if not np.isnan(atr) else self.hi_since - 1
                        if low <= trail_stop:
                            self.position.close()
            
            # SL
            if low <= self.initial_sl:
                self.position.close()
        
        # SHORT management
        elif self.position.is_short and self.entry_price and self.initial_sl:
            sl_dist = self.initial_sl - self.entry_price
            
            # TP1
            if self.use_tp and not self.tp1_hit:
                tp1_short = self.entry_price - sl_dist * self.tp1_rr_short
                if low <= tp1_short:
                    self.tp1_hit = True
            
            # TP2 or SL
            if self.tp1_hit:
                if self.second_tp_type == "rr":
                    tp2_short = self.entry_price - sl_dist * self.tp2_rr_short
                    if low <= tp2_short:
                        self.position.close()
                else:
                    if self.lo_since:
                        trail_stop = self.lo_since + atr * self.adaptive_atr_mult if not np.isnan(atr) else self.lo_since + 1
                        if high >= trail_stop:
                            self.position.close()
            
            # SL
            if high >= self.initial_sl:
                self.position.close()
    
    def _calc_qty_long(self, price, stop):
        """Calculate position size for long"""
        if price <= stop or np.isnan(price) or np.isnan(stop):
            return 0.0
        
        equity = self.equity
        risk_amt = equity * (self.risk_per_trade_pct / 100.0)
        dist = price - stop
        
        if dist <= 0:
            return 0.0
        
        # Use percentage of equity instead of absolute quantity
        qty_pct = min(0.95, risk_amt / (dist * price))  # Cap at 95% of equity
        return max(0.01, qty_pct)  # Min 1% of equity
    
    def _calc_qty_short(self, price, stop, is_bull_regime):
        """Calculate position size for short"""
        if stop <= price or np.isnan(price) or np.isnan(stop):
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
        
        # Use percentage of equity instead of absolute quantity
        qty_pct = min(0.95, risk_amt / (dist * price))  # Cap at 95% of equity
        return max(0.01, qty_pct)  # Min 1% of equity


def calculate_indicators(data):
    """Pre-calculate all indicators"""
    close = data['Close'].values
    high = data['High'].values
    low = data['Low'].values
    
    # EMA
    ema = pd.Series(close).ewm(span=100).mean().values
    
    # ATR
    tr = np.zeros(len(close))
    for i in range(len(close)):
        if i == 0:
            tr[i] = high[i] - low[i]
        else:
            tr[i] = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
    
    atr = pd.Series(tr).rolling(14).mean().values
    
    # Trailing stop
    trail = np.zeros(len(close))
    key_value = 2.0
    for i in range(len(close)):
        if i == 0:
            trail[i] = close[i]
        else:
            n_loss = key_value * atr[i] if not np.isnan(atr[i]) else 0
            if close[i] > trail[i-1]:
                trail[i] = max(trail[i-1], close[i] - n_loss)
            elif close[i] < trail[i-1]:
                trail[i] = min(trail[i-1], close[i] + n_loss)
            else:
                trail[i] = trail[i-1]
    
    # Regime
    sma50 = pd.Series(close).rolling(50).mean().values
    sma200 = pd.Series(close).rolling(200).mean().values
    
    # EMA Ribbon
    ema13 = pd.Series(close).ewm(span=13).mean().values
    ema48 = pd.Series(close).ewm(span=48).mean().values
    ema200 = pd.Series(close).ewm(span=200).mean().values
    
    # Signals
    buy_sig = crossover(close, trail).astype(float)
    sell_sig = crossunder(close, trail).astype(float)
    
    # Add to dataframe
    data['ema'] = ema
    data['atr'] = atr
    data['trail'] = trail
    data['sma50'] = sma50
    data['sma200'] = sma200
    data['ema13'] = ema13
    data['ema48'] = ema48
    data['ema200'] = ema200
    data['buy_sig'] = buy_sig
    data['sell_sig'] = sell_sig
    
    return data


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
    
    # Calculate indicators
    print("\n⚙️  Calculating indicators...")
    data = calculate_indicators(data)
    
    # Run backtest
    print("   Running backtest...")
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
    if 'Consecutive Wins' in stats:
        print(f"   Consecutive Wins:       {stats['Consecutive Wins']:.0f}")
    if 'Consecutive Losses' in stats:
        print(f"   Consecutive Losses:     {stats['Consecutive Losses']:.0f}")
    
    print(f"\n💵 CAPITAL:")
    if 'Start' in stats:
        print(f"   Starting Equity:        ${stats['Start']:.2f}")
    if 'End' in stats:
        print(f"   Ending Date:            {stats['End']}")
    
    print("\n" + "=" * 80)
    
    # Plot
    print("\n📈 Generating chart...")
    bt.plot(filename='agbot_shorts_optimized_backtest.html', open_browser=False)
    print("   Chart saved to: agbot_shorts_optimized_backtest.html")
    
    return stats


if __name__ == "__main__":
    stats = run_backtest()
