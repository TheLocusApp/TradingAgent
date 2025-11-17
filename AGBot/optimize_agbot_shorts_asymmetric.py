"""
AGBot SHORTS Optimization - Asymmetric Parameters
Optimized for downtrend physics (fast, violent moves)

Key differences from longs:
- Tighter stops (0.5-1.0x ATR vs 2.0x)
- Faster exits (0.3-0.75 R:R vs 1.0+)
- Higher trim % (80-95% vs 35%)
- Shorter holds (2-6 hours vs 12+)

Test period: Jan 2025 - Apr 2025 (tariff downtrend)
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import os
from itertools import product

class AGBotShortsAsymmetric:
    def __init__(self, ticker='QQQ', timeframe='1h'):
        self.ticker = ticker
        self.timeframe = timeframe
        self.data = None
        
    def download_data(self, start_date, end_date):
        """Download data for specific period"""
        print(f"\n{'='*60}")
        print(f"Downloading {self.ticker} {self.timeframe} data...")
        print(f"Period: {start_date} to {end_date}")
        print(f"{'='*60}\n")
        
        try:
            data = yf.download(
                self.ticker,
                start=start_date,
                end=end_date,
                interval=self.timeframe,
                progress=False
            )
            
            if data.empty:
                print(f"❌ No data downloaded for {self.ticker}")
                return False
            
            # Flatten multi-level columns if present
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
                
            self.data = data
            print(f"✅ Downloaded {len(data)} bars")
            print(f"   Date range: {data.index[0]} to {data.index[-1]}")
            return True
            
        except Exception as e:
            print(f"❌ Error downloading data: {e}")
            return False
    
    def calculate_indicators(self, ma_length, key_value, atr_period=14):
        """Calculate EMA, ATR, and UT Bot trailing stop"""
        df = self.data.copy()
        
        # EMA
        df['ema'] = df['Close'].ewm(span=ma_length, adjust=False).mean()
        
        # ATR for UT Bot
        df['high_low'] = df['High'] - df['Low']
        df['high_close'] = abs(df['High'] - df['Close'].shift(1))
        df['low_close'] = abs(df['Low'] - df['Close'].shift(1))
        df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        df['atr_ut'] = df['true_range'].rolling(window=1).mean()
        
        # ATR for stops
        df['atr'] = df['true_range'].rolling(window=atr_period).mean()
        
        # UT Bot trailing stop
        nLoss = key_value * df['atr_ut']
        df['xATRTrail'] = 0.0
        
        for i in range(1, len(df)):
            prev_trail = df['xATRTrail'].iloc[i-1]
            curr_close = df['Close'].iloc[i]
            curr_loss = nLoss.iloc[i]
            
            if pd.isna(prev_trail) or prev_trail == 0:
                df.loc[df.index[i], 'xATRTrail'] = curr_close
            elif curr_close > prev_trail:
                df.loc[df.index[i], 'xATRTrail'] = max(prev_trail, curr_close - curr_loss)
            elif curr_close < prev_trail:
                df.loc[df.index[i], 'xATRTrail'] = min(prev_trail, curr_close + curr_loss)
            else:
                prev_close = df['Close'].iloc[i-1]
                if prev_close > prev_trail:
                    df.loc[df.index[i], 'xATRTrail'] = curr_close - curr_loss
                else:
                    df.loc[df.index[i], 'xATRTrail'] = curr_close + curr_loss
        
        return df
    
    def backtest_shorts(self, ma_length, key_value, atr_mult, tp1_rr, tp1_percent, max_hold_hours):
        """Backtest SHORTS ONLY with asymmetric parameters"""
        df = self.calculate_indicators(ma_length, key_value)
        
        # Signals
        df['bearish'] = df['Close'] < df['ema']
        df['sell_signal'] = (df['Close'] < df['xATRTrail']) & (df['Close'].shift(1) >= df['xATRTrail'].shift(1))
        
        # Trading
        position = 0
        entry_price = 0
        stop_loss = 0
        tp1_price = 0
        entry_bar = 0
        trades = []
        equity = 100000
        position_size_pct = 0
        
        for i in range(1, len(df)):
            current_price = df['Close'].iloc[i]
            current_atr = df['atr'].iloc[i]
            bars_held = i - entry_bar if position != 0 else 0
            max_hold_bars = max_hold_hours  # 1H timeframe = 1 bar per hour
            
            # Entry: SHORT only
            if position == 0:
                if df['sell_signal'].iloc[i] and df['bearish'].iloc[i]:
                    entry_price = current_price
                    stop_loss = entry_price + (current_atr * atr_mult)
                    
                    # Calculate position size (2.5% risk)
                    risk_amount = equity * 0.025
                    stop_distance = stop_loss - entry_price
                    if stop_distance > 0:
                        position_size_pct = risk_amount / (stop_distance * equity)
                        position_size_pct = min(position_size_pct, 0.1)  # Max 10% position
                        
                        if position_size_pct > 0:
                            position = -1
                            entry_bar = i
                            
                            # TP1 for shorts (ASYMMETRIC - faster exits)
                            tp1_distance = (entry_price - stop_loss) * tp1_rr
                            tp1_price = entry_price - tp1_distance
            
            # Exit management
            elif position == -1:
                exit_reason = None
                exit_price = current_price
                pnl_pct = 0
                
                # Stop loss
                if current_price >= stop_loss:
                    exit_reason = 'SL'
                    exit_price = stop_loss
                    pnl_pct = ((entry_price - exit_price) / entry_price) * position_size_pct
                
                # TP1 (close 80-95% immediately)
                elif current_price <= tp1_price:
                    exit_reason = 'TP1'
                    exit_price = tp1_price
                    pnl_pct = ((entry_price - exit_price) / entry_price) * position_size_pct * (tp1_percent / 100)
                
                # Max hold time (ASYMMETRIC - shorter holds)
                elif bars_held >= max_hold_bars:
                    exit_reason = 'Time'
                    pnl_pct = ((entry_price - exit_price) / entry_price) * position_size_pct
                
                if exit_reason:
                    equity *= (1 + pnl_pct)
                    
                    trades.append({
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl_pct': pnl_pct * 100,
                        'exit_reason': exit_reason,
                        'bars_held': bars_held,
                        'entry_date': df.index[entry_bar],
                        'exit_date': df.index[i]
                    })
                    
                    position = 0
                    entry_price = 0
                    stop_loss = 0
        
        # Calculate metrics
        if len(trades) == 0:
            return None
        
        trades_df = pd.DataFrame(trades)
        total_return = ((equity - 100000) / 100000) * 100
        
        winners = trades_df[trades_df['pnl_pct'] > 0]
        losers = trades_df[trades_df['pnl_pct'] <= 0]
        
        win_rate = (len(winners) / len(trades)) * 100 if len(trades) > 0 else 0
        avg_win = winners['pnl_pct'].mean() if len(winners) > 0 else 0
        avg_loss = losers['pnl_pct'].mean() if len(losers) > 0 else 0
        
        profit_factor = abs(winners['pnl_pct'].sum() / losers['pnl_pct'].sum()) if len(losers) > 0 and losers['pnl_pct'].sum() != 0 else 0
        
        # Sharpe ratio
        returns = trades_df['pnl_pct'].values
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
        
        # Max drawdown
        cumulative = (1 + trades_df['pnl_pct'] / 100).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = ((cumulative - running_max) / running_max) * 100
        max_dd = drawdown.min()
        
        return {
            'ma_length': ma_length,
            'key_value': key_value,
            'atr_mult': atr_mult,
            'tp1_rr': tp1_rr,
            'tp1_percent': tp1_percent,
            'max_hold_hours': max_hold_hours,
            'return': total_return,
            'sharpe': sharpe,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_dd': max_dd,
            'trades': len(trades),
            'final_equity': equity
        }
    
    def optimize(self, start_date, end_date):
        """Run optimization with asymmetric parameters"""
        
        # Download data
        if not self.download_data(start_date, end_date):
            return None
        
        # ASYMMETRIC parameter ranges for SHORTS
        param_grid = {
            'ma_length': [50, 75, 100, 150],  # Faster MA for quicker response
            'key_value': [0.5, 1.0, 1.5],  # Tighter trailing
            'atr_mult': [0.5, 0.75, 1.0],  # MUCH tighter stops
            'tp1_rr': [0.3, 0.5, 0.75],  # Faster exits
            'tp1_percent': [80, 90, 95],  # Lock almost everything
            'max_hold_hours': [2, 4, 6]  # Shorter duration
        }
        
        total_combinations = np.prod([len(v) for v in param_grid.values()])
        print(f"\n{'='*60}")
        print(f"ASYMMETRIC SHORTS OPTIMIZATION")
        print(f"{'='*60}")
        print(f"Total combinations: {total_combinations}")
        print(f"Ticker: {self.ticker}")
        print(f"Period: {start_date} to {end_date}")
        print(f"\nKey differences from longs:")
        print(f"  - ATR Mult: 0.5-1.0 (vs 2.0 for longs)")
        print(f"  - TP1 R:R: 0.3-0.75 (vs 1.0+ for longs)")
        print(f"  - TP1%: 80-95% (vs 35% for longs)")
        print(f"  - Max Hold: 2-6h (vs 12h for longs)")
        print(f"{'='*60}\n")
        
        results = []
        count = 0
        
        for params in product(*param_grid.values()):
            count += 1
            ma_length, key_value, atr_mult, tp1_rr, tp1_percent, max_hold_hours = params
            
            if count % 50 == 0:
                print(f"Progress: {count}/{total_combinations} ({count/total_combinations*100:.1f}%)")
            
            result = self.backtest_shorts(
                ma_length, key_value, atr_mult, tp1_rr, tp1_percent, max_hold_hours
            )
            
            if result:
                results.append(result)
        
        if not results:
            print("\n❌ No valid results generated")
            return None
        
        # Sort by Sharpe ratio
        results.sort(key=lambda x: x['sharpe'], reverse=True)
        
        print(f"\n{'='*60}")
        print(f"OPTIMIZATION COMPLETE")
        print(f"{'='*60}")
        print(f"Valid results: {len(results)}")
        print(f"\nTop 10 Results (by Sharpe):")
        print(f"{'='*60}\n")
        
        for i, r in enumerate(results[:10], 1):
            print(f"#{i}")
            print(f"  MA: {r['ma_length']}, Key: {r['key_value']}, ATR: {r['atr_mult']}")
            print(f"  TP1 R:R: {r['tp1_rr']}, TP1%: {r['tp1_percent']}%, Hold: {r['max_hold_hours']}h")
            print(f"  Return: {r['return']:.2f}%, Sharpe: {r['sharpe']:.2f}")
            print(f"  Win Rate: {r['win_rate']:.1f}%, Trades: {r['trades']}")
            print(f"  Max DD: {r['max_dd']:.2f}%, PF: {r['profit_factor']:.2f}")
            print()
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'optimization_{self.ticker}_shorts_asymmetric_{timestamp}.json'
        filepath = os.path.join('src', 'data', 'optimizations', filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"✅ Results saved to: {filepath}")
        
        return results

if __name__ == '__main__':
    # Test on Jan-Apr 2025 tariff downtrend
    optimizer = AGBotShortsAsymmetric(ticker='QQQ', timeframe='1h')
    
    # Jan 2025 - Apr 2025 (tariff downtrend period)
    results = optimizer.optimize(
        start_date='2025-01-01',
        end_date='2025-04-30'
    )
    
    if results:
        print(f"\n{'='*60}")
        print(f"BEST PARAMETERS FOR SHORTS (Jan-Apr 2025 Tariff Downtrend)")
        print(f"{'='*60}")
        best = results[0]
        print(f"\nRecommended Settings:")
        print(f"  MA Length: {best['ma_length']}")
        print(f"  Key Value: {best['key_value']}")
        print(f"  ATR Mult: {best['atr_mult']} (vs 2.0 for longs)")
        print(f"  TP1 R:R: {best['tp1_rr']} (vs 1.0 for longs)")
        print(f"  TP1 Close %: {best['tp1_percent']}% (vs 35% for longs)")
        print(f"  Max Hold: {best['max_hold_hours']} hours (vs 12 for longs)")
        print(f"\nExpected Performance (Jan-Apr 2025):")
        print(f"  Return: {best['return']:.2f}%")
        print(f"  Sharpe: {best['sharpe']:.2f}")
        print(f"  Win Rate: {best['win_rate']:.1f}%")
        print(f"  Max DD: {best['max_dd']:.2f}%")
        print(f"  Trades: {best['trades']}")
        print(f"  Profit Factor: {best['profit_factor']:.2f}")
        print(f"{'='*60}\n")
