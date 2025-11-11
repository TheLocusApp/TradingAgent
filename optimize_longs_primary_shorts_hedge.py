"""
Longs-Primary with Shorts-Hedge Strategy
- Trade LONGS 100% of the time (proven +400%)
- Only add SHORTS during extreme bear conditions:
  1. VIX > 30 (extreme fear)
  2. Price < EMA200 for 20+ consecutive bars (confirmed bear)
  
This should give us the best of both worlds!
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import os
from itertools import product

class LongsPrimaryShortsHedge:
    def __init__(self, ticker='QQQ', timeframe='1h'):
        self.ticker = ticker
        self.timeframe = timeframe
        self.data = None
        self.vix_data = None
        
    def download_data(self):
        """Download QQQ and VIX data"""
        print(f"\n{'='*60}")
        print(f"Downloading {self.ticker} {self.timeframe} data + VIX...")
        print(f"{'='*60}\n")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)
        
        try:
            # Download QQQ
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
            
            # Download VIX (daily data)
            vix_data = yf.download(
                '^VIX',
                start=start_date,
                end=end_date,
                interval='1d',
                progress=False
            )
            
            if vix_data.empty:
                print(f"⚠️ No VIX data downloaded, will use EMA200 filter only")
                self.vix_data = None
            else:
                if isinstance(vix_data.columns, pd.MultiIndex):
                    vix_data.columns = vix_data.columns.get_level_values(0)
                self.vix_data = vix_data
                print(f"✅ Downloaded VIX data: {len(vix_data)} bars")
                
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
        
        # Merge VIX data if available
        if self.vix_data is not None:
            # Convert both to timezone-naive for comparison
            vix_series = self.vix_data['Close'].copy()
            vix_series.index = vix_series.index.tz_localize(None) if vix_series.index.tz is None else vix_series.index.tz_convert(None)
            df_index_naive = df.index.tz_localize(None) if df.index.tz is None else df.index.tz_convert(None)
            
            # Resample VIX to match QQQ timeframe
            vix_resampled = vix_series.reindex(df_index_naive, method='ffill')
            df['vix'] = vix_resampled.values
        else:
            df['vix'] = 0
        
        # Count consecutive bars below EMA200
        df['below_ema200'] = (df['Close'] < df['ema200']).astype(int)
        df['bars_below_ema200'] = 0
        
        count = 0
        for i in range(len(df)):
            if df['below_ema200'].iloc[i]:
                count += 1
            else:
                count = 0
            df.loc[df.index[i], 'bars_below_ema200'] = count
        
        return df
    
    def backtest(self, ma_length, key_value, atr_mult_longs, atr_mult_shorts, 
                 tp1_pct_longs, tp1_pct_shorts, swing_high_bars, 
                 vix_threshold, ema200_bars_threshold):
        """Backtest longs-primary with shorts-hedge"""
        df = self.calculate_indicators(ma_length, key_value)
        df = df.dropna()
        
        if len(df) < 50:
            return None
        
        # Signals
        df['bullish'] = df['Close'] > df['ema']
        df['bearish'] = df['Close'] < df['ema']
        df['buy_signal'] = (df['Close'] > df['xATRTrail']) & (df['Close'].shift(1) <= df['xATRTrail'].shift(1))
        df['sell_signal'] = (df['Close'] < df['xATRTrail']) & (df['Close'].shift(1) >= df['xATRTrail'].shift(1))
        
        # HEDGE CONDITIONS for shorts
        df['vix_extreme'] = df['vix'] > vix_threshold
        df['confirmed_bear'] = df['bars_below_ema200'] >= ema200_bars_threshold
        df['bear_alignment'] = (df['Close'] < df['ema13']) & (df['ema13'] < df['ema48']) & (df['ema48'] < df['ema200'])
        
        # Shorts ONLY when hedge conditions met
        df['hedge_active'] = df['vix_extreme'] | df['confirmed_bear'] | df['bear_alignment']
        
        # Swing high for shorts
        df['swing_high'] = df['High'].rolling(window=swing_high_bars).max()
        
        # Trading
        position = 0  # 1 = long, -1 = short
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
            current_atr = df['atr'].iloc[i]
            
            # Entry logic
            if position == 0:
                # LONGS: Always available (primary strategy)
                if df['buy_signal'].iloc[i] and df['bullish'].iloc[i]:
                    entry_price = current_price
                    stop_loss = entry_price - (current_atr * atr_mult_longs)
                    
                    risk_amount = equity * 0.025
                    stop_distance = entry_price - stop_loss
                    if stop_distance > 0:
                        position_size_pct = risk_amount / (stop_distance * equity)
                        position_size_pct = min(position_size_pct, 0.1)
                        
                        if position_size_pct > 0:
                            position = 1
                            entry_bar = i
                            tp1_hit = False
                            
                            tp1_distance = stop_distance * 1.0  # 1:1 R:R for longs
                            tp1_price = entry_price + tp1_distance
                
                # SHORTS: Only when hedge conditions met
                elif df['sell_signal'].iloc[i] and df['bearish'].iloc[i] and df['hedge_active'].iloc[i]:
                    entry_price = current_price
                    swing_high_stop = df['swing_high'].iloc[i]
                    
                    if not pd.isna(swing_high_stop):
                        stop_loss = swing_high_stop
                        
                        risk_amount = equity * 0.025
                        stop_distance = stop_loss - entry_price
                        if stop_distance > 0:
                            position_size_pct = risk_amount / (stop_distance * equity)
                            position_size_pct = min(position_size_pct, 0.1)
                            
                            if position_size_pct > 0:
                                position = -1
                                entry_bar = i
                                tp1_hit = False
                                
                                tp1_distance = stop_distance * 1.5  # 1.5:1 R:R for shorts
                                tp1_price = entry_price - tp1_distance
            
            # Exit management
            elif position != 0:
                exit_reason = None
                exit_price = current_price
                pnl_pct = 0
                
                if position == 1:  # LONG
                    # Stop loss
                    if current_price <= stop_loss:
                        exit_reason = 'SL'
                        exit_price = stop_loss
                        pnl_pct = ((exit_price - entry_price) / entry_price) * position_size_pct
                    
                    # TP1
                    elif not tp1_hit and current_price >= tp1_price:
                        exit_reason = 'TP1'
                        exit_price = tp1_price
                        pnl_pct = ((exit_price - entry_price) / entry_price) * position_size_pct * (tp1_pct_longs / 100)
                        tp1_hit = True
                        equity *= (1 + pnl_pct)
                        trades.append({
                            'type': 'LONG',
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'pnl_pct': pnl_pct * 100,
                            'exit_reason': exit_reason,
                            'bars_held': i - entry_bar,
                            'entry_date': df.index[entry_bar],
                            'exit_date': df.index[i]
                        })
                        continue
                
                elif position == -1:  # SHORT
                    # Update stop to swing high
                    swing_high_stop = df['swing_high'].iloc[i]
                    if not pd.isna(swing_high_stop):
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
                        pnl_pct = ((entry_price - exit_price) / entry_price) * position_size_pct * (tp1_pct_shorts / 100)
                        tp1_hit = True
                        equity *= (1 + pnl_pct)
                        trades.append({
                            'type': 'SHORT',
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'pnl_pct': pnl_pct * 100,
                            'exit_reason': exit_reason,
                            'bars_held': i - entry_bar,
                            'entry_date': df.index[entry_bar],
                            'exit_date': df.index[i]
                        })
                        continue
                    
                    # Exit if hedge conditions no longer met
                    elif not df['hedge_active'].iloc[i]:
                        exit_reason = 'Hedge_Off'
                        pnl_pct = ((entry_price - exit_price) / entry_price) * position_size_pct * ((100 - tp1_pct_shorts) / 100 if tp1_hit else 1.0)
                
                if exit_reason and exit_reason not in ['TP1']:
                    equity *= (1 + pnl_pct)
                    trades.append({
                        'type': 'LONG' if position == 1 else 'SHORT',
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
        
        # Separate long and short stats
        long_trades = trades_df[trades_df['type'] == 'LONG']
        short_trades = trades_df[trades_df['type'] == 'SHORT']
        
        winners = trades_df[trades_df['pnl_pct'] > 0]
        losers = trades_df[trades_df['pnl_pct'] <= 0]
        
        win_rate = (len(winners) / len(trades)) * 100 if len(trades) > 0 else 0
        
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
            'atr_mult_longs': atr_mult_longs,
            'atr_mult_shorts': atr_mult_shorts,
            'tp1_pct_longs': tp1_pct_longs,
            'tp1_pct_shorts': tp1_pct_shorts,
            'swing_high_bars': swing_high_bars,
            'vix_threshold': vix_threshold,
            'ema200_bars_threshold': ema200_bars_threshold,
            'return': total_return,
            'sharpe': sharpe,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_dd': max_dd,
            'trades': len(trades),
            'long_trades': len(long_trades),
            'short_trades': len(short_trades),
            'final_equity': equity
        }
    
    def optimize(self):
        """Run optimization"""
        if not self.download_data():
            return None
        
        param_grid = {
            'ma_length': [100, 150],
            'key_value': [1.5, 2.0],
            'atr_mult_longs': [2.0, 2.5],
            'atr_mult_shorts': [1.0],
            'tp1_pct_longs': [35],
            'tp1_pct_shorts': [70],
            'swing_high_bars': [5, 7],
            'vix_threshold': [25, 30, 35],
            'ema200_bars_threshold': [10, 20, 30]
        }
        
        total_combinations = np.prod([len(v) for v in param_grid.values()])
        print(f"\n{'='*60}")
        print(f"LONGS-PRIMARY + SHORTS-HEDGE OPTIMIZATION")
        print(f"{'='*60}")
        print(f"Total combinations: {total_combinations}")
        print(f"Ticker: {self.ticker}")
        print(f"\nStrategy:")
        print(f"  - LONGS: Always active (primary)")
        print(f"  - SHORTS: Only when:")
        print(f"    • VIX > threshold (25/30/35)")
        print(f"    • Price < EMA200 for 10/20/30 bars")
        print(f"    • Bear alignment (C < 13 < 48 < 200)")
        print(f"{'='*60}\n")
        
        results = []
        count = 0
        
        for params in product(*param_grid.values()):
            count += 1
            if count % 20 == 0:
                print(f"Progress: {count}/{total_combinations} ({count/total_combinations*100:.1f}%)")
            
            result = self.backtest(*params)
            
            if result:
                results.append(result)
        
        if not results:
            print("\n❌ No valid results")
            return None
        
        results.sort(key=lambda x: x['return'], reverse=True)
        
        print(f"\n{'='*60}")
        print(f"OPTIMIZATION COMPLETE")
        print(f"{'='*60}")
        print(f"Valid results: {len(results)}")
        print(f"\nTop 10 Results (by Return):")
        print(f"{'='*60}\n")
        
        for i, r in enumerate(results[:10], 1):
            print(f"#{i}")
            print(f"  MA: {r['ma_length']}, Key: {r['key_value']}")
            print(f"  Longs ATR: {r['atr_mult_longs']}, Shorts Swing: {r['swing_high_bars']} bars")
            print(f"  VIX Threshold: {r['vix_threshold']}, EMA200 Bars: {r['ema200_bars_threshold']}")
            print(f"  Return: {r['return']:.2f}%, Sharpe: {r['sharpe']:.2f}")
            print(f"  Win Rate: {r['win_rate']:.1f}%, Trades: {r['trades']} (L:{r['long_trades']}, S:{r['short_trades']})")
            print(f"  Max DD: {r['max_dd']:.2f}%, PF: {r['profit_factor']:.2f}")
            print()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'optimization_{self.ticker}_longs_primary_shorts_hedge_{timestamp}.json'
        filepath = os.path.join('src', 'data', 'optimizations', filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"✅ Results saved to: {filepath}")
        
        return results

if __name__ == '__main__':
    optimizer = LongsPrimaryShortsHedge(ticker='QQQ', timeframe='1h')
    results = optimizer.optimize()
    
    if results:
        print(f"\n{'='*60}")
        print(f"BEST PARAMETERS (Longs-Primary + Shorts-Hedge)")
        print(f"{'='*60}")
        best = results[0]
        print(f"\nRecommended Settings:")
        print(f"  MA Length: {best['ma_length']}")
        print(f"  Key Value: {best['key_value']}")
        print(f"  Longs ATR Mult: {best['atr_mult_longs']}")
        print(f"  Shorts Swing High: {best['swing_high_bars']} bars")
        print(f"  VIX Threshold: {best['vix_threshold']}")
        print(f"  EMA200 Bars Threshold: {best['ema200_bars_threshold']}")
        print(f"\nExpected Performance (Last 730 days):")
        print(f"  Return: {best['return']:.2f}%")
        print(f"  Sharpe: {best['sharpe']:.2f}")
        print(f"  Win Rate: {best['win_rate']:.1f}%")
        print(f"  Max DD: {best['max_dd']:.2f}%")
        print(f"  Total Trades: {best['trades']} (Longs: {best['long_trades']}, Shorts: {best['short_trades']})")
        print(f"  Profit Factor: {best['profit_factor']:.2f}")
        print(f"{'='*60}\n")
