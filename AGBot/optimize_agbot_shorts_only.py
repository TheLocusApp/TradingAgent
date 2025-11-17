"""
AGBot Shorts-Only Parameter Optimization
Finds best parameters specifically for SHORT positions
Tests on QQQ 1H timeframe
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from itertools import product
import sys

class AGBotShortsOptimizer:
    def __init__(self, ticker='QQQ', timeframe='1h', max_bars=5000):
        self.ticker = ticker
        self.timeframe = timeframe
        self.max_bars = max_bars
        self.data = None
        self.results = []
        
    def download_data(self):
        """Download historical data"""
        print(f"📥 Downloading {self.ticker} {self.timeframe} data...")
        
        # yfinance 1H limit: 730 days max
        # Download in chunks and combine
        end_date = datetime.now()
        all_data = []
        
        # Download 730 days at a time, going back 5 years
        for chunk in range(5):
            chunk_end = end_date - timedelta(days=730*chunk)
            chunk_start = chunk_end - timedelta(days=730)
            
            print(f"   Chunk {chunk+1}/5: {chunk_start.date()} to {chunk_end.date()}")
            
            try:
                chunk_data = yf.download(
                    self.ticker,
                    start=chunk_start,
                    end=chunk_end,
                    interval=self.timeframe,
                    progress=False
                )
                
                if len(chunk_data) > 0:
                    all_data.append(chunk_data)
            except Exception as e:
                print(f"   ⚠️ Chunk {chunk+1} failed: {str(e)[:50]}")
                continue
        
        if all_data:
            self.data = pd.concat(all_data).drop_duplicates().sort_index()
        else:
            print("❌ No data downloaded!")
            return None
        
        # Keep only last max_bars
        if len(self.data) > self.max_bars:
            self.data = self.data.iloc[-self.max_bars:]
        
        print(f"✅ Downloaded {len(self.data)} bars")
        return self.data
    
    def calculate_indicators(self, ma_length, atr_period_ut, atr_period, key_value):
        """Calculate all indicators"""
        df = self.data.copy()
        
        # EMA
        df['ema'] = df['Close'].ewm(span=ma_length, adjust=False).mean()
        
        # ATR for UT Bot
        df['tr_ut'] = np.maximum(
            df['High'] - df['Low'],
            np.maximum(
                np.abs(df['High'] - df['Close'].shift(1)),
                np.abs(df['Low'] - df['Close'].shift(1))
            )
        )
        df['atr_ut'] = df['tr_ut'].rolling(window=atr_period_ut).mean()
        
        # ATR for SL/Trail
        df['tr'] = np.maximum(
            df['High'] - df['Low'],
            np.maximum(
                np.abs(df['High'] - df['Close'].shift(1)),
                np.abs(df['Low'] - df['Close'].shift(1))
            )
        )
        df['atr'] = df['tr'].rolling(window=atr_period).mean()
        
        # UT Bot ATR Trailing Stop
        n_loss = key_value * df['atr_ut']
        
        xATRTrail = [np.nan]
        for i in range(1, len(df)):
            if np.isnan(xATRTrail[i-1]):
                xATRTrail.append(df['Close'].iloc[i])
            else:
                if df['Close'].iloc[i] > xATRTrail[i-1]:
                    xATRTrail.append(max(xATRTrail[i-1], df['Close'].iloc[i] - n_loss.iloc[i]))
                elif df['Close'].iloc[i] < xATRTrail[i-1]:
                    xATRTrail.append(min(xATRTrail[i-1], df['Close'].iloc[i] + n_loss.iloc[i]))
                else:
                    if df['Close'].iloc[i-1] > xATRTrail[i-1]:
                        xATRTrail.append(df['Close'].iloc[i] - n_loss.iloc[i])
                    else:
                        xATRTrail.append(df['Close'].iloc[i] + n_loss.iloc[i])
        
        df['ut_trail'] = xATRTrail
        
        # Signals
        df['bearish'] = df['Close'] < df['ema']
        df['sell_signal'] = (df['Close'] < df['ut_trail']) & (df['Close'].shift(1) >= df['ut_trail'].shift(1))
        
        return df
    
    def backtest_shorts(self, df, adaptive_atr_mult, tp1_rr_short, tp1_percent, risk_pct=2.5):
        """Backtest SHORT positions only"""
        
        trades = []
        position = None
        equity = 100000
        
        for i in range(1, len(df)):
            current_price = df['Close'].iloc[i]
            atr = df['atr'].iloc[i]
            
            # Entry: SHORT signal
            if position is None and df['sell_signal'].iloc[i] and df['bearish'].iloc[i]:
                # Short stop (above entry)
                short_stop = current_price + atr * adaptive_atr_mult
                
                # Risk calculation
                risk_amount = equity * (risk_pct / 100.0)
                stop_distance = short_stop - current_price
                
                if stop_distance > 0:
                    qty = risk_amount / (stop_distance * df['Close'].iloc[i])
                    
                    if qty > 0:
                        position = {
                            'entry_price': current_price,
                            'entry_bar': i,
                            'stop': short_stop,
                            'qty': qty,
                            'risk': risk_amount,
                            'tp1_hit': False,
                            'highest_price': current_price,
                        }
            
            # Management: SHORT position
            if position is not None:
                position['highest_price'] = max(position['highest_price'], current_price)
                
                # TP1 calculation (SHORT: price goes DOWN)
                stop_distance = position['stop'] - position['entry_price']
                tp1_short = position['entry_price'] - (stop_distance * tp1_rr_short)
                
                # TP1 hit
                if not position['tp1_hit'] and current_price <= tp1_short:
                    # Close tp1_percent of position
                    close_qty = position['qty'] * (tp1_percent / 100.0)
                    close_price = current_price
                    pnl = (position['entry_price'] - close_price) * close_qty
                    
                    trades.append({
                        'entry_price': position['entry_price'],
                        'entry_bar': position['entry_bar'],
                        'tp1_price': close_price,
                        'tp1_bar': i,
                        'tp1_pnl': pnl,
                        'type': 'SHORT_TP1',
                        'bars_held': i - position['entry_bar'],
                    })
                    
                    position['qty'] -= close_qty
                    position['tp1_hit'] = True
                    equity += pnl
                
                # Stop loss hit
                if current_price >= position['stop']:
                    pnl = (position['entry_price'] - position['stop']) * position['qty']
                    
                    trades.append({
                        'entry_price': position['entry_price'],
                        'entry_bar': position['entry_bar'],
                        'exit_price': position['stop'],
                        'exit_bar': i,
                        'pnl': pnl,
                        'type': 'SHORT_SL',
                        'bars_held': i - position['entry_bar'],
                    })
                    
                    equity += pnl
                    position = None
                
                # TP2: ATR trailing (if TP1 hit)
                elif position['tp1_hit'] and position['qty'] > 0:
                    trail_stop = position['highest_price'] + atr * adaptive_atr_mult
                    if current_price >= trail_stop:
                        pnl = (position['entry_price'] - trail_stop) * position['qty']
                        
                        trades.append({
                            'entry_price': position['entry_price'],
                            'entry_bar': position['entry_bar'],
                            'tp2_price': trail_stop,
                            'tp2_bar': i,
                            'tp2_pnl': pnl,
                            'type': 'SHORT_TP2',
                            'bars_held': i - position['entry_bar'],
                        })
                        
                        equity += pnl
                        position = None
        
        # Close any open position at end
        if position is not None:
            close_price = df['Close'].iloc[-1]
            pnl = (position['entry_price'] - close_price) * position['qty']
            equity += pnl
            trades.append({
                'entry_price': position['entry_price'],
                'entry_bar': position['entry_bar'],
                'exit_price': close_price,
                'exit_bar': len(df) - 1,
                'pnl': pnl,
                'type': 'SHORT_EOD',
                'bars_held': len(df) - 1 - position['entry_bar'],
            })
        
        return trades, equity
    
    def calculate_metrics(self, trades, initial_equity=100000):
        """Calculate performance metrics"""
        if not trades:
            return None
        
        trades_df = pd.DataFrame(trades)
        
        # Total return
        total_pnl = trades_df['pnl'].sum() if 'pnl' in trades_df.columns else 0
        total_pnl += trades_df['tp1_pnl'].sum() if 'tp1_pnl' in trades_df.columns else 0
        total_pnl += trades_df['tp2_pnl'].sum() if 'tp2_pnl' in trades_df.columns else 0
        
        final_equity = initial_equity + total_pnl
        total_return = (total_pnl / initial_equity) * 100
        
        # Win rate
        winning_trades = len(trades_df[trades_df['pnl'] > 0]) if 'pnl' in trades_df.columns else 0
        total_trades = len(trades_df)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Avg trade
        avg_trade = total_pnl / total_trades if total_trades > 0 else 0
        
        # Profit factor
        wins = trades_df[trades_df['pnl'] > 0]['pnl'].sum() if 'pnl' in trades_df.columns else 0
        losses = abs(trades_df[trades_df['pnl'] < 0]['pnl'].sum()) if 'pnl' in trades_df.columns else 1
        profit_factor = wins / losses if losses > 0 else 0
        
        # Sharpe ratio (simplified)
        if 'pnl' in trades_df.columns:
            returns = trades_df['pnl'] / initial_equity
            sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        else:
            sharpe = 0
        
        return {
            'total_return': total_return,
            'final_equity': final_equity,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_trade': avg_trade,
            'profit_factor': profit_factor,
            'sharpe': sharpe,
        }
    
    def optimize(self):
        """Run optimization"""
        if self.data is None or len(self.data) == 0:
            print("❌ No data available for optimization!")
            return []
        
        # Parameter ranges - OPTIMIZED FOR SHORTS
        ma_lengths = [100, 150, 200, 250]
        key_values = [1.0, 1.5, 2.0, 2.5]
        atr_mult_values = [0.5, 0.75, 1.0, 1.25, 1.5]  # Tighter for shorts
        tp1_rr_shorts = [0.25, 0.5, 0.75, 1.0]  # Lower for faster exits
        tp1_percents = [30, 40, 50, 60, 70]  # Higher trim % for shorts
        
        total_combos = (len(ma_lengths) * len(key_values) * len(atr_mult_values) * 
                       len(tp1_rr_shorts) * len(tp1_percents))
        
        print(f"\n🔍 Testing {total_combos} parameter combinations for SHORTS...")
        print(f"   MA: {ma_lengths}")
        print(f"   Key: {key_values}")
        print(f"   ATR Mult: {atr_mult_values} (tighter for shorts)")
        print(f"   TP1 R:R: {tp1_rr_shorts} (lower for faster exits)")
        print(f"   TP1 %: {tp1_percents} (higher trim for shorts)\n")
        
        combo_count = 0
        best_sharpe = -999
        best_params = None
        
        for ma_len, key_val, atr_mult, tp1_rr, tp1_pct in product(
            ma_lengths, key_values, atr_mult_values, tp1_rr_shorts, tp1_percents
        ):
            combo_count += 1
            
            if combo_count % 100 == 0:
                print(f"   Progress: {combo_count}/{total_combos} ({combo_count/total_combos*100:.1f}%)")
            
            try:
                # Calculate indicators
                df = self.calculate_indicators(ma_len, 1, 14, key_val)
                
                # Backtest
                trades, equity = self.backtest_shorts(df, atr_mult, tp1_rr, tp1_pct)
                
                # Metrics
                metrics = self.calculate_metrics(trades, 100000)
                
                if metrics and metrics['total_trades'] >= 10:  # At least 10 trades
                    metrics['ma_length'] = ma_len
                    metrics['key_value'] = key_val
                    metrics['adaptive_atr_mult'] = atr_mult
                    metrics['tp1_rr_short'] = tp1_rr
                    metrics['tp1_percent'] = tp1_pct
                    
                    self.results.append(metrics)
                    
                    if metrics['sharpe'] > best_sharpe:
                        best_sharpe = metrics['sharpe']
                        best_params = metrics
            
            except Exception as e:
                continue
        
        print(f"\n✅ Optimization complete! Tested {combo_count} combinations")
        return self.results
    
    def save_results(self, filename=None):
        """Save results to JSON"""
        if filename is None:
            filename = f"optimization_QQQ_shorts_only_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Sort by Sharpe ratio
        sorted_results = sorted(self.results, key=lambda x: x['sharpe'], reverse=True)
        
        output = {
            'ticker': self.ticker,
            'timeframe': '1h',
            'optimization_type': 'shorts_only',
            'timestamp': datetime.now().isoformat(),
            'total_combinations_tested': len(self.results),
            'best_results': sorted_results[:10],
        }
        
        filepath = f"src/data/optimizations/{filename}"
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n💾 Results saved to {filepath}")
        
        # Print top 5
        print("\n🏆 TOP 5 PARAMETER SETS FOR SHORTS:\n")
        for i, result in enumerate(sorted_results[:5], 1):
            print(f"{i}. MA={result['ma_length']}, Key={result['key_value']}, ATR Mult={result['adaptive_atr_mult']}")
            print(f"   TP1 R:R={result['tp1_rr_short']}, TP1%={result['tp1_percent']}")
            print(f"   Return: {result['total_return']:.2f}% | Sharpe: {result['sharpe']:.2f} | Win%: {result['win_rate']:.1f}%")
            print(f"   Trades: {result['total_trades']} | Profit Factor: {result['profit_factor']:.2f}\n")
        
        return filepath


if __name__ == "__main__":
    print("=" * 70)
    print("AGBot SHORTS-ONLY Optimization")
    print("=" * 70)
    
    optimizer = AGBotShortsOptimizer(ticker='QQQ', timeframe='1h')
    
    # Download data
    data = optimizer.download_data()
    
    if data is None or len(data) == 0:
        print("\n❌ Failed to download data. Trying alternative approach...")
        print("   Note: yfinance has a 730-day limit for 1H data")
        print("   Consider using a different data source or timeframe")
        sys.exit(1)
    
    # Run optimization
    results = optimizer.optimize()
    
    if results:
        # Save results
        optimizer.save_results()
        print("\n✨ Done! Use the best parameters in your Pine Script.")
    else:
        print("\n❌ Optimization failed - no valid results generated")
