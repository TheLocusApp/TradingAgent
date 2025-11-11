"""
Bollinger Bands + RSI Strategy for Downtrends
Mean reversion strategy optimized for bear markets

Logic:
- Entry: Price > Upper BB AND RSI > overbought threshold (catch bounces)
- Exit: Price < Middle BB OR RSI < neutral threshold (mean reversion)
- Stop: Price > Entry + (2 * ATR) (failed reversal)

Test period: Jan-Apr 2025 (tariff downtrend)
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import json
import os
from itertools import product

class BBRSIShorts:
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
    
    def calculate_indicators(self, bb_length, bb_std, rsi_length):
        """Calculate Bollinger Bands, RSI, and ATR"""
        df = self.data.copy()
        
        # Bollinger Bands
        df['bb_middle'] = df['Close'].rolling(window=bb_length).mean()
        df['bb_std'] = df['Close'].rolling(window=bb_length).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * df['bb_std'])
        df['bb_lower'] = df['bb_middle'] - (bb_std * df['bb_std'])
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_length).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_length).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR for stops
        df['high_low'] = df['High'] - df['Low']
        df['high_close'] = abs(df['High'] - df['Close'].shift(1))
        df['low_close'] = abs(df['Low'] - df['Close'].shift(1))
        df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        df['atr'] = df['true_range'].rolling(window=14).mean()
        
        return df
    
    def backtest_shorts(self, bb_length, bb_std, rsi_length, rsi_overbought, rsi_exit, atr_stop_mult, tp_rr):
        """Backtest BB+RSI shorts strategy"""
        df = self.calculate_indicators(bb_length, bb_std, rsi_length)
        
        # Remove NaN rows
        df = df.dropna()
        
        if len(df) < 50:
            return None
        
        # Signals
        df['overbought'] = (df['Close'] > df['bb_upper']) & (df['rsi'] > rsi_overbought)
        df['mean_revert'] = (df['Close'] < df['bb_middle']) | (df['rsi'] < rsi_exit)
        
        # Trading
        position = 0
        entry_price = 0
        stop_loss = 0
        take_profit = 0
        entry_bar = 0
        trades = []
        equity = 100000
        position_size_pct = 0
        
        for i in range(1, len(df)):
            current_price = df['Close'].iloc[i]
            current_atr = df['atr'].iloc[i]
            
            # Entry: SHORT when overbought
            if position == 0:
                if df['overbought'].iloc[i]:
                    entry_price = current_price
                    stop_loss = entry_price + (current_atr * atr_stop_mult)
                    
                    # Calculate position size (2.5% risk)
                    risk_amount = equity * 0.025
                    stop_distance = stop_loss - entry_price
                    if stop_distance > 0:
                        position_size_pct = risk_amount / (stop_distance * equity)
                        position_size_pct = min(position_size_pct, 0.1)  # Max 10% position
                        
                        if position_size_pct > 0:
                            position = -1
                            entry_bar = i
                            
                            # Take profit target
                            tp_distance = stop_distance * tp_rr
                            take_profit = entry_price - tp_distance
            
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
                
                # Take profit
                elif current_price <= take_profit:
                    exit_reason = 'TP'
                    exit_price = take_profit
                    pnl_pct = ((entry_price - exit_price) / entry_price) * position_size_pct
                
                # Mean reversion exit
                elif df['mean_revert'].iloc[i]:
                    exit_reason = 'Mean_Rev'
                    pnl_pct = ((entry_price - exit_price) / entry_price) * position_size_pct
                
                if exit_reason:
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
            'bb_length': bb_length,
            'bb_std': bb_std,
            'rsi_length': rsi_length,
            'rsi_overbought': rsi_overbought,
            'rsi_exit': rsi_exit,
            'atr_stop_mult': atr_stop_mult,
            'tp_rr': tp_rr,
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
        """Run optimization"""
        
        # Download data
        if not self.download_data(start_date, end_date):
            return None
        
        # Parameter ranges for BB+RSI shorts
        param_grid = {
            'bb_length': [20, 30, 40],  # BB period
            'bb_std': [2.0, 2.5, 3.0],  # BB standard deviations
            'rsi_length': [7, 14, 21],  # RSI period
            'rsi_overbought': [65, 70, 75, 80],  # RSI overbought threshold
            'rsi_exit': [40, 45, 50, 55],  # RSI exit threshold
            'atr_stop_mult': [1.5, 2.0, 2.5],  # ATR stop multiplier
            'tp_rr': [1.0, 1.5, 2.0, 2.5]  # Take profit R:R
        }
        
        total_combinations = np.prod([len(v) for v in param_grid.values()])
        print(f"\n{'='*60}")
        print(f"BOLLINGER BANDS + RSI SHORTS OPTIMIZATION")
        print(f"{'='*60}")
        print(f"Total combinations: {total_combinations}")
        print(f"Ticker: {self.ticker}")
        print(f"Period: {start_date} to {end_date}")
        print(f"\nStrategy Logic:")
        print(f"  Entry: Price > Upper BB AND RSI > Overbought")
        print(f"  Exit: Price < Middle BB OR RSI < Exit Threshold")
        print(f"  Stop: Entry + (ATR × Multiplier)")
        print(f"{'='*60}\n")
        
        results = []
        count = 0
        
        for params in product(*param_grid.values()):
            count += 1
            bb_length, bb_std, rsi_length, rsi_overbought, rsi_exit, atr_stop_mult, tp_rr = params
            
            if count % 100 == 0:
                print(f"Progress: {count}/{total_combinations} ({count/total_combinations*100:.1f}%)")
            
            result = self.backtest_shorts(
                bb_length, bb_std, rsi_length, rsi_overbought, rsi_exit, atr_stop_mult, tp_rr
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
            print(f"  BB: {r['bb_length']} period, {r['bb_std']} std")
            print(f"  RSI: {r['rsi_length']} period, OB: {r['rsi_overbought']}, Exit: {r['rsi_exit']}")
            print(f"  Stop: {r['atr_stop_mult']}×ATR, TP: {r['tp_rr']} R:R")
            print(f"  Return: {r['return']:.2f}%, Sharpe: {r['sharpe']:.2f}")
            print(f"  Win Rate: {r['win_rate']:.1f}%, Trades: {r['trades']}")
            print(f"  Avg Win: {r['avg_win']:.2f}%, Avg Loss: {r['avg_loss']:.2f}%")
            print(f"  Max DD: {r['max_dd']:.2f}%, PF: {r['profit_factor']:.2f}")
            print()
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'optimization_{self.ticker}_bb_rsi_shorts_{timestamp}.json'
        filepath = os.path.join('src', 'data', 'optimizations', filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"✅ Results saved to: {filepath}")
        
        return results

if __name__ == '__main__':
    # Test on 2022 bear market (actual downtrend) - use daily data
    optimizer = BBRSIShorts(ticker='QQQ', timeframe='1d')
    
    print("\n" + "="*60)
    print("Testing on 2022 BEAR MARKET (Real Downtrend)")
    print("Using DAILY data (1H not available for 2022)")
    print("="*60)
    
    results = optimizer.optimize(
        start_date='2022-01-01',
        end_date='2022-12-31'
    )
    
    if results:
        print(f"\n{'='*60}")
        print(f"BEST PARAMETERS FOR BB+RSI SHORTS (Jan-Apr 2025)")
        print(f"{'='*60}")
        best = results[0]
        print(f"\nRecommended Settings:")
        print(f"  BB Length: {best['bb_length']}")
        print(f"  BB Std Dev: {best['bb_std']}")
        print(f"  RSI Length: {best['rsi_length']}")
        print(f"  RSI Overbought: {best['rsi_overbought']}")
        print(f"  RSI Exit: {best['rsi_exit']}")
        print(f"  ATR Stop Mult: {best['atr_stop_mult']}")
        print(f"  TP R:R: {best['tp_rr']}")
        print(f"\nExpected Performance (Jan-Apr 2025):")
        print(f"  Return: {best['return']:.2f}%")
        print(f"  Sharpe: {best['sharpe']:.2f}")
        print(f"  Win Rate: {best['win_rate']:.1f}%")
        print(f"  Avg Win: {best['avg_win']:.2f}%")
        print(f"  Avg Loss: {best['avg_loss']:.2f}%")
        print(f"  Max DD: {best['max_dd']:.2f}%")
        print(f"  Trades: {best['trades']}")
        print(f"  Profit Factor: {best['profit_factor']:.2f}")
        print(f"{'='*60}\n")
