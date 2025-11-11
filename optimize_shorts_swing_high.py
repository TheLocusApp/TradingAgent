"""
Optimize Shorts with Swing High Stops
Test different swing high lookback periods and other parameters
to maximize shorts performance with the new stop loss approach
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import os
from itertools import product

class AGBotShortsSwingHigh:
    def __init__(self, ticker='QQQ', timeframe='1h'):
        self.ticker = ticker
        self.timeframe = timeframe
        self.data = None
        
    def download_data(self):
        """Download last 730 days of 1H data"""
        print(f"\n{'='*60}")
        print(f"Downloading {self.ticker} {self.timeframe} data...")
        print(f"{'='*60}\n")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)
        
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
        """Calculate indicators"""
        df = self.data.copy()
        
        # Main EMA
        df['ema'] = df['Close'].ewm(span=ma_length, adjust=False).mean()
        
        # EMA RIBBON
        df['ema13'] = df['Close'].ewm(span=13, adjust=False).mean()
        df['ema48'] = df['Close'].ewm(span=48, adjust=False).mean()
        df['ema200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        # ATR
        df['high_low'] = df['High'] - df['Low']
        df['high_close'] = abs(df['High'] - df['Close'].shift(1))
        df['low_close'] = abs(df['Low'] - df['Close'].shift(1))
        df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        df['atr_ut'] = df['true_range'].rolling(window=1).mean()
        df['atr'] = df['true_range'].rolling(window=atr_period).mean()
        
        # UT Bot
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
    
    def backtest_shorts(self, ma_length, key_value, swing_high_bars, tp1_rr, tp1_percent, use_ema_filter):
        """Backtest shorts with swing high stops"""
        df = self.calculate_indicators(ma_length, key_value)
        df = df.dropna()
        
        if len(df) < 50:
            return None
        
        # Bear alignment filter
        df['bear_alignment'] = (df['Close'] < df['ema13']) & (df['ema13'] < df['ema48']) & (df['ema48'] < df['ema200'])
        
        # Signals
        df['bearish'] = df['Close'] < df['ema']
        df['sell_signal'] = (df['Close'] < df['xATRTrail']) & (df['Close'].shift(1) >= df['xATRTrail'].shift(1))
        
        # Apply EMA filter if enabled
        if use_ema_filter:
            df['short_signal'] = df['sell_signal'] & df['bear_alignment'] & df['bearish']
        else:
            df['short_signal'] = df['sell_signal'] & df['bearish']
        
        # Swing high stop
        df['swing_high'] = df['High'].rolling(window=swing_high_bars).max()
        
        # Trading
        position = 0
        entry_price = 0
        stop_loss = 0
        tp1_price = 0
        entry_bar = 0
        trades = []
        equity = 100000
        position_size_pct = 0
        tp1_hit = False
        
        for i in range(1, len(df)):
            current_price = df['Close'].iloc[i]
            swing_high_stop = df['swing_high'].iloc[i]
            
            # Entry
            if position == 0:
                if df['short_signal'].iloc[i] and not pd.isna(swing_high_stop):
                    entry_price = current_price
                    stop_loss = swing_high_stop
                    
                    # Position sizing
                    risk_amount = equity * 0.025
                    stop_distance = stop_loss - entry_price
                    if stop_distance > 0:
                        position_size_pct = risk_amount / (stop_distance * equity)
                        position_size_pct = min(position_size_pct, 0.1)
                        
                        if position_size_pct > 0:
                            position = -1
                            entry_bar = i
                            tp1_hit = False
                            
                            # TP1
                            tp1_distance = stop_distance * tp1_rr
                            tp1_price = entry_price - tp1_distance
            
            # Exit management
            elif position == -1:
                exit_reason = None
                exit_price = current_price
                pnl_pct = 0
                
                # Update stop to swing high
                stop_loss = swing_high_stop
                
                # Stop loss
                if current_price >= stop_loss:
                    exit_reason = 'SL'
                    exit_price = stop_loss
                    pnl_pct = ((entry_price - exit_price) / entry_price) * position_size_pct
                
                # TP1
                elif not tp1_hit and current_price <= tp1_price:
                    exit_reason = 'TP1'
                    exit_price = tp1_price
                    pnl_pct = ((entry_price - exit_price) / entry_price) * position_size_pct * (tp1_percent / 100)
                    tp1_hit = True
                    equity *= (1 + pnl_pct)
                    trades.append({
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl_pct': pnl_pct * 100,
                        'exit_reason': exit_reason,
                        'bars_held': i - entry_bar,
                        'entry_date': df.index[entry_bar],
                        'exit_date': df.index[i]
                    })
                    continue
                
                # Exit if EMA filter enabled and bear alignment breaks
                elif use_ema_filter and not df['bear_alignment'].iloc[i]:
                    exit_reason = 'Bear_Broken'
                    pnl_pct = ((entry_price - exit_price) / entry_price) * position_size_pct * ((100 - tp1_percent) / 100 if tp1_hit else 1.0)
                
                if exit_reason and exit_reason != 'TP1':
                    equity *= (1 + pnl_pct)
                    trades.append({
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl_pct': pnl_pct * 100,
                        'exit_reason': exit_reason,
                        'bars_held': i - entry_bar,
                        'entry_date': df.index[entry_bar],
                        'exit_date': df.index[i]
                    })
                    position = 0
        
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
        
        returns = trades_df['pnl_pct'].values
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
        
        cumulative = (1 + trades_df['pnl_pct'] / 100).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = ((cumulative - running_max) / running_max) * 100
        max_dd = drawdown.min()
        
        return {
            'ma_length': ma_length,
            'key_value': key_value,
            'swing_high_bars': swing_high_bars,
            'tp1_rr': tp1_rr,
            'tp1_percent': tp1_percent,
            'use_ema_filter': use_ema_filter,
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
    
    def optimize(self):
        """Run optimization"""
        if not self.download_data():
            return None
        
        param_grid = {
            'ma_length': [50, 100, 150],
            'key_value': [1.0, 1.5, 2.0],
            'swing_high_bars': [3, 5, 7, 10],
            'tp1_rr': [0.5, 1.0, 1.5],
            'tp1_percent': [35, 50, 70],
            'use_ema_filter': [True, False]
        }
        
        total_combinations = np.prod([len(v) for v in param_grid.values()])
        print(f"\n{'='*60}")
        print(f"SHORTS SWING HIGH OPTIMIZATION")
        print(f"{'='*60}")
        print(f"Total combinations: {total_combinations}")
        print(f"Ticker: {self.ticker}")
        print(f"\nTesting:")
        print(f"  - Swing High Bars: 3, 5, 7, 10")
        print(f"  - EMA Filter: ON/OFF")
        print(f"  - TP1 levels: 35%, 50%, 70%")
        print(f"{'='*60}\n")
        
        results = []
        count = 0
        
        for params in product(*param_grid.values()):
            count += 1
            ma_length, key_value, swing_high_bars, tp1_rr, tp1_percent, use_ema_filter = params
            
            if count % 50 == 0:
                print(f"Progress: {count}/{total_combinations} ({count/total_combinations*100:.1f}%)")
            
            result = self.backtest_shorts(
                ma_length, key_value, swing_high_bars, tp1_rr, tp1_percent, use_ema_filter
            )
            
            if result:
                results.append(result)
        
        if not results:
            print("\n❌ No valid results")
            return None
        
        results.sort(key=lambda x: x['sharpe'], reverse=True)
        
        print(f"\n{'='*60}")
        print(f"OPTIMIZATION COMPLETE")
        print(f"{'='*60}")
        print(f"Valid results: {len(results)}")
        print(f"\nTop 10 Results (by Sharpe):")
        print(f"{'='*60}\n")
        
        for i, r in enumerate(results[:10], 1):
            print(f"#{i}")
            print(f"  MA: {r['ma_length']}, Key: {r['key_value']}, Swing High: {r['swing_high_bars']} bars")
            print(f"  TP1 R:R: {r['tp1_rr']}, TP1%: {r['tp1_percent']}%, EMA Filter: {r['use_ema_filter']}")
            print(f"  Return: {r['return']:.2f}%, Sharpe: {r['sharpe']:.2f}")
            print(f"  Win Rate: {r['win_rate']:.1f}%, Trades: {r['trades']}")
            print(f"  Max DD: {r['max_dd']:.2f}%, PF: {r['profit_factor']:.2f}")
            print()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'optimization_{self.ticker}_shorts_swing_high_{timestamp}.json'
        filepath = os.path.join('src', 'data', 'optimizations', filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"✅ Results saved to: {filepath}")
        
        return results

if __name__ == '__main__':
    optimizer = AGBotShortsSwingHigh(ticker='QQQ', timeframe='1h')
    results = optimizer.optimize()
    
    if results:
        print(f"\n{'='*60}")
        print(f"BEST PARAMETERS FOR SHORTS (Swing High)")
        print(f"{'='*60}")
        best = results[0]
        print(f"\nRecommended Settings:")
        print(f"  MA Length: {best['ma_length']}")
        print(f"  Key Value: {best['key_value']}")
        print(f"  Swing High Bars: {best['swing_high_bars']}")
        print(f"  TP1 R:R: {best['tp1_rr']}")
        print(f"  TP1 Close %: {best['tp1_percent']}%")
        print(f"  EMA Filter: {best['use_ema_filter']}")
        print(f"\nExpected Performance (Last 730 days):")
        print(f"  Return: {best['return']:.2f}%")
        print(f"  Sharpe: {best['sharpe']:.2f}")
        print(f"  Win Rate: {best['win_rate']:.1f}%")
        print(f"  Max DD: {best['max_dd']:.2f}%")
        print(f"  Trades: {best['trades']}")
        print(f"  Profit Factor: {best['profit_factor']:.2f}")
        print(f"{'='*60}\n")
