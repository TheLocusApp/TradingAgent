"""
Optimize Shorts Strategy with Swing High Stops in Downtrends
Tests: swing high bars, TP ratios, position sizing in bull markets
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from itertools import product
import json

class ShortSwingHighOptimizer:
    def __init__(self, ticker="QQQ", capital=10000, risk_pct=2.5):
        self.ticker = ticker
        self.capital = capital
        self.risk_pct = risk_pct
        self.df = None
        
    def download_data(self, start_date="2022-01-01", end_date=None):
        """Download OHLCV data"""
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        print(f"Downloading {self.ticker} from {start_date} to {end_date}...")
        self.df = yf.download(self.ticker, start=start_date, end=end_date, progress=False)
        # Keep only the columns we need
        self.df = self.df[['Open', 'High', 'Low', 'Close', 'Volume']]
        self.df.columns = ['open', 'high', 'low', 'close', 'volume']
        print(f"Downloaded {len(self.df)} bars")
        return self.df
    
    def calculate_indicators(self):
        """Calculate all indicators"""
        df = self.df.copy()
        
        # EMA
        df['ema100'] = df['close'].ewm(span=100).mean()
        df['ema13'] = df['close'].ewm(span=13).mean()
        df['ema48'] = df['close'].ewm(span=48).mean()
        df['ema200'] = df['close'].ewm(span=200).mean()
        
        # ATR
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                np.abs(df['high'] - df['close'].shift(1)),
                np.abs(df['low'] - df['close'].shift(1))
            )
        )
        df['atr14'] = df['tr'].rolling(14).mean()
        df['atr1'] = df['tr'].rolling(1).mean()
        
        # UT Bot trailing stop
        df['nLoss'] = 2.0 * df['atr1']
        df['xATRTrail'] = self._ut_bot_trail(df)
        
        # Signals
        df['bullish'] = df['close'] > df['ema100']
        df['bearish'] = df['close'] < df['ema100']
        df['buySignal'] = (df['close'] > df['xATRTrail']) & (df['close'].shift(1) <= df['xATRTrail'].shift(1))
        df['sellSignal'] = (df['close'] < df['xATRTrail']) & (df['close'].shift(1) >= df['xATRTrail'].shift(1))
        
        # Regime
        df['sma50'] = df['close'].rolling(50).mean()
        df['sma200'] = df['close'].rolling(200).mean()
        df['isBullRegime'] = df['sma50'] > df['sma200']
        df['isBearRegime'] = df['sma50'] < df['sma200']
        
        # EMA Filter
        df['bearAlignment'] = (df['close'] < df['ema13']) & (df['ema13'] < df['ema48']) & (df['ema48'] < df['ema200'])
        
        self.df = df
        return df
    
    def _ut_bot_trail(self, df):
        """Calculate UT Bot trailing stop"""
        trail = [df['close'].iloc[0]]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > trail[-1]:
                trail.append(max(trail[-1], df['close'].iloc[i] - df['nLoss'].iloc[i]))
            elif df['close'].iloc[i] < trail[-1]:
                trail.append(min(trail[-1], df['close'].iloc[i] + df['nLoss'].iloc[i]))
            else:
                trail.append(trail[-1])
        return pd.Series(trail, index=df.index)
    
    def backtest_shorts(self, swing_high_bars=5, tp1_rr=1.5, tp1_pct=70, bull_risk_reduction=0.5):
        """Backtest shorts with swing high stops"""
        df = self.df.copy()
        
        # Swing high for shorts (highest high in last N bars)
        df['shortStopSwing'] = df['high'].rolling(swing_high_bars).max()
        
        trades = []
        position = None
        
        for i in range(swing_high_bars, len(df)):
            if position is None:
                # Entry: sellSignal + bearish (NO strict bearAlignment filter - too restrictive)
                # Instead: Only require price below EMA200 (confirmed downtrend)
                if df['sellSignal'].iloc[i] and df['bearish'].iloc[i] and df['close'].iloc[i] < df['ema200'].iloc[i]:
                    entry_price = df['close'].iloc[i]
                    # Swing high stop should be ABOVE entry (for shorts, stop is above)
                    stop_price = df['shortStopSwing'].iloc[i]
                    
                    # For shorts: stop must be ABOVE entry price (to exit if price goes up)
                    if stop_price > entry_price:
                        # Calculate position size
                        risk_amt = self.capital * (self.risk_pct / 100)
                        
                        # Reduce risk in bull markets
                        if not df['isBearRegime'].iloc[i]:
                            risk_amt *= bull_risk_reduction
                        
                        stop_dist = stop_price - entry_price  # This is positive for shorts
                        if stop_dist > 0:
                            qty = risk_amt / stop_dist
                            
                            position = {
                                'entry_idx': i,
                                'entry_price': entry_price,
                                'stop_price': stop_price,
                                'qty': qty,
                                'risk_amt': risk_amt,
                                'regime': 'BEAR' if df['isBearRegime'].iloc[i] else 'BULL',
                                'tp1_hit': False,
                                'lo_since': df['low'].iloc[i]
                            }
            
            else:
                # Position management
                position['lo_since'] = min(position['lo_since'], df['low'].iloc[i])
                
                # Stop loss hit (price goes ABOVE stop for shorts)
                if df['high'].iloc[i] >= position['stop_price']:
                    loss = position['risk_amt']
                    trades.append({
                        'entry_idx': position['entry_idx'],
                        'entry_date': df.index[position['entry_idx']],
                        'entry_price': position['entry_price'],
                        'exit_idx': i,
                        'exit_date': df.index[i],
                        'exit_price': position['stop_price'],
                        'qty': position['qty'],
                        'pnl': -loss,
                        'pnl_pct': -self.risk_pct,
                        'regime': position['regime'],
                        'bars_held': i - position['entry_idx'],
                        'exit_reason': 'SL'
                    })
                    position = None
                
                # TP1
                elif not position['tp1_hit']:
                    sl_dist = position['stop_price'] - position['entry_price']
                    tp1_price = position['entry_price'] - sl_dist * tp1_rr
                    
                    if df['low'].iloc[i] <= tp1_price:
                        close_qty = position['qty'] * (tp1_pct / 100)
                        profit = (position['entry_price'] - tp1_price) * close_qty
                        
                        trades.append({
                            'entry_idx': position['entry_idx'],
                            'entry_date': df.index[position['entry_idx']],
                            'entry_price': position['entry_price'],
                            'exit_idx': i,
                            'exit_date': df.index[i],
                            'exit_price': tp1_price,
                            'qty': close_qty,
                            'pnl': profit,
                            'pnl_pct': (profit / (position['risk_amt'] * tp1_pct / 100)) * 100 if position['risk_amt'] > 0 else 0,
                            'regime': position['regime'],
                            'bars_held': i - position['entry_idx'],
                            'exit_reason': 'TP1'
                        })
                        
                        position['qty'] -= close_qty
                        position['tp1_hit'] = True
                        
                        if position['qty'] <= 0:
                            position = None
        
        return trades
    
    def calculate_stats(self, trades):
        """Calculate performance statistics"""
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_pnl': 0,
                'profit_factor': 0,
                'avg_bars_held': 0
            }
        
        df_trades = pd.DataFrame(trades)
        
        winning = df_trades[df_trades['pnl'] > 0]
        losing = df_trades[df_trades['pnl'] <= 0]
        
        total_pnl = df_trades['pnl'].sum()
        gross_profit = winning['pnl'].sum() if len(winning) > 0 else 0
        gross_loss = abs(losing['pnl'].sum()) if len(losing) > 0 else 0
        
        return {
            'total_trades': len(df_trades),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': (len(winning) / len(df_trades) * 100) if len(df_trades) > 0 else 0,
            'total_pnl': total_pnl,
            'avg_pnl': df_trades['pnl'].mean(),
            'profit_factor': gross_profit / gross_loss if gross_loss > 0 else 0,
            'avg_bars_held': df_trades['bars_held'].mean(),
            'bear_trades': len(df_trades[df_trades['regime'] == 'BEAR']),
            'bull_trades': len(df_trades[df_trades['regime'] == 'BULL']),
            'bear_win_rate': (len(df_trades[(df_trades['regime'] == 'BEAR') & (df_trades['pnl'] > 0)]) / 
                            len(df_trades[df_trades['regime'] == 'BEAR']) * 100) if len(df_trades[df_trades['regime'] == 'BEAR']) > 0 else 0,
            'bull_win_rate': (len(df_trades[(df_trades['regime'] == 'BULL') & (df_trades['pnl'] > 0)]) / 
                            len(df_trades[df_trades['regime'] == 'BULL']) * 100) if len(df_trades[df_trades['regime'] == 'BULL']) > 0 else 0
        }
    
    def optimize(self):
        """Run optimization across parameter space"""
        swing_bars_range = [3, 5, 7, 10]
        tp1_rr_range = [0.5, 1.0, 1.5, 2.0]
        tp1_pct_range = [50, 70, 80]
        bull_reduction_range = [0.25, 0.5, 0.75]
        
        results = []
        total_combos = len(swing_bars_range) * len(tp1_rr_range) * len(tp1_pct_range) * len(bull_reduction_range)
        combo_num = 0
        
        print(f"\nOptimizing {total_combos} parameter combinations...")
        print(f"Total bars available: {len(self.df)}")
        print(f"Sell signals: {self.df['sellSignal'].sum()}")
        print(f"Bear alignment bars: {self.df['bearAlignment'].sum()}")
        
        for swing_bars, tp1_rr, tp1_pct, bull_reduction in product(
            swing_bars_range, tp1_rr_range, tp1_pct_range, bull_reduction_range
        ):
            combo_num += 1
            trades = self.backtest_shorts(swing_bars, tp1_rr, tp1_pct, bull_reduction)
            stats = self.calculate_stats(trades)
            
            results.append({
                'swing_high_bars': swing_bars,
                'tp1_rr': tp1_rr,
                'tp1_pct': tp1_pct,
                'bull_risk_reduction': bull_reduction,
                **stats
            })
            
            if combo_num % 10 == 0:
                print(f"  {combo_num}/{total_combos} combinations tested...")
        
        df_results = pd.DataFrame(results)
        
        print(f"\nTotal combinations with trades: {len(df_results[df_results['total_trades'] > 0])}")
        print(f"Combinations with 5+ trades: {len(df_results[df_results['total_trades'] >= 5])}")
        
        # Filter for minimum trades (relax if needed)
        if len(df_results[df_results['total_trades'] >= 5]) > 0:
            df_results = df_results[df_results['total_trades'] >= 5]
        else:
            print("No combinations with 5+ trades. Showing all results...")
            df_results = df_results[df_results['total_trades'] > 0]
        
        # Sort by profit factor, then win rate
        df_results = df_results.sort_values(
            by=['profit_factor', 'win_rate', 'total_pnl'],
            ascending=[False, False, False]
        )
        
        return df_results
    
    def save_results(self, df_results, filename="shorts_optimization_results.csv"):
        """Save optimization results"""
        df_results.to_csv(filename, index=False)
        print(f"\nResults saved to {filename}")
        
        # Print top 10
        print("\n" + "="*120)
        print("TOP 10 PARAMETER COMBINATIONS")
        print("="*120)
        print(df_results.head(10).to_string())
        
        return df_results.head(10)

# =============== MAIN ===============
if __name__ == "__main__":
    optimizer = ShortSwingHighOptimizer(ticker="QQQ", capital=10000, risk_pct=2.5)
    
    # Download data (2022 bear market + 2025 data)
    optimizer.download_data(start_date="2022-01-01", end_date="2025-11-09")
    
    # Calculate indicators
    optimizer.calculate_indicators()
    
    # Run optimization
    results = optimizer.optimize()
    
    # Save results
    top_10 = optimizer.save_results(results)
    
    print("\n" + "="*120)
    print("OPTIMIZATION COMPLETE")
    print("="*120)
    print("\nKey Insights:")
    print(f"  - Best Swing High Bars: {results.iloc[0]['swing_high_bars']}")
    print(f"  - Best TP1 R:R: {results.iloc[0]['tp1_rr']}")
    print(f"  - Best TP1 Close %: {results.iloc[0]['tp1_pct']}")
    print(f"  - Best Bull Risk Reduction: {results.iloc[0]['bull_risk_reduction']}")
    print(f"  - Profit Factor: {results.iloc[0]['profit_factor']:.2f}")
    print(f"  - Win Rate: {results.iloc[0]['win_rate']:.1f}%")
    print(f"  - Total Trades: {results.iloc[0]['total_trades']}")
    print(f"  - Bear Market Win Rate: {results.iloc[0]['bear_win_rate']:.1f}%")
    print(f"  - Bull Market Win Rate: {results.iloc[0]['bull_win_rate']:.1f}%")
