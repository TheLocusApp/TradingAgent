"""
AGBot Strategy Optimization - TSLA 4H Timeframe
Optimized for larger average trade size (target: 1-2% per trade)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from backtesting import Backtest
from src.strategies.AGBot import AGBotStrategy
import warnings
warnings.filterwarnings('ignore')

def fetch_data(symbol, period_days, interval='4h'):
    """Fetch OHLCV data from yfinance"""
    print(f"📊 Fetching {symbol} data ({interval}) for {period_days} days...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days)
    
    df = yf.download(
        symbol, 
        start=start_date, 
        end=end_date, 
        interval=interval,
        progress=False
    )
    
    if df.empty:
        print(f"❌ No data fetched for {symbol}")
        return None
    
    # Handle MultiIndex columns from yfinance
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Select only required columns
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    df = df[required_cols]
    
    # Remove any NaN rows
    df = df.dropna()
    
    if df.empty:
        print(f"❌ No valid data after cleaning")
        return None
    
    print(f"✅ Fetched {len(df)} candles")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    return df

def test_parameters(df, ma_length, key_value, adaptive_atr_mult, tp1_rr_long, tp1_percent, tp2_rr_long):
    """Test a specific parameter combination"""
    try:
        class TestStrategy(AGBotStrategy):
            pass
        
        # Set parameters
        TestStrategy.ma_length = ma_length
        TestStrategy.key_value = key_value
        TestStrategy.adaptive_atr_mult = adaptive_atr_mult
        TestStrategy.tp1_rr_long = tp1_rr_long
        TestStrategy.tp1_percent = tp1_percent
        TestStrategy.tp2_rr_long = tp2_rr_long
        
        bt = Backtest(
            df,
            TestStrategy,
            cash=10000,
            commission=0.0003,
            exclusive_orders=True
        )
        
        stats = bt.run()
        
        # Calculate average trade size
        avg_trade = stats['Avg. Trade [%]'] if stats['# Trades'] > 0 else 0
        
        return {
            'ma_length': ma_length,
            'key_value': key_value,
            'adaptive_atr_mult': adaptive_atr_mult,
            'tp1_rr_long': tp1_rr_long,
            'tp1_percent': tp1_percent,
            'tp2_rr_long': tp2_rr_long,
            'return': stats['Return [%]'],
            'sharpe': stats['Sharpe Ratio'],
            'max_dd': stats['Max. Drawdown [%]'],
            'win_rate': stats['Win Rate [%]'],
            'trades': stats['# Trades'],
            'avg_trade': avg_trade,
            'profit_factor': stats['Profit Factor']
        }
    except Exception as e:
        return None

def optimize_strategy(df):
    """Optimize strategy parameters for 4H timeframe"""
    print("\n" + "="*70)
    print("🔍 AGBot Strategy Optimization - TSLA 4H")
    print("="*70)
    print("Goal: Find parameters that generate 1-2% average trade size")
    
    # Parameter ranges (optimized for 4H)
    ma_lengths = [50, 100, 150, 200]
    key_values = [1.5, 2.0, 2.5, 3.0]
    adaptive_atr_mults = [1.0, 1.5, 2.0, 2.5]
    tp1_rr_longs = [1.0, 1.5, 2.0, 2.5]  # INCREASED from 0.5
    tp1_percents = [20, 25, 30]  # REDUCED from 45
    tp2_rr_longs = [3.0, 4.0, 5.0]
    
    total_combinations = (len(ma_lengths) * len(key_values) * len(adaptive_atr_mults) * 
                         len(tp1_rr_longs) * len(tp1_percents) * len(tp2_rr_longs))
    print(f"\n⏳ Testing {total_combinations} parameter combinations...")
    print("This will take 10-15 minutes...\n")
    
    results = []
    tested = 0
    
    for ma_length in ma_lengths:
        for key_value in key_values:
            for adaptive_atr_mult in adaptive_atr_mults:
                for tp1_rr_long in tp1_rr_longs:
                    for tp1_percent in tp1_percents:
                        for tp2_rr_long in tp2_rr_longs:
                            result = test_parameters(
                                df, ma_length, key_value, adaptive_atr_mult, 
                                tp1_rr_long, tp1_percent, tp2_rr_long
                            )
                            
                            if result is not None:
                                results.append(result)
                            
                            tested += 1
                            if tested % 100 == 0:
                                pct = 100 * tested / total_combinations
                                print(f"  Progress: {tested}/{total_combinations} ({pct:.1f}%)")
    
    if not results:
        print("❌ No valid results found")
        return None
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    # Filter for viable strategies (avg trade >= 1.0%)
    viable = results_df[results_df['avg_trade'] >= 1.0]
    
    print("\n" + "="*70)
    print("📊 Optimization Results")
    print("="*70)
    print(f"\nTotal combinations tested: {len(results_df)}")
    print(f"Viable strategies (avg trade >= 1.0%): {len(viable)}")
    
    if len(viable) == 0:
        print("\n⚠️  No strategies found with avg trade >= 1.0%")
        print("Showing best by average trade size:\n")
        results_df = results_df.sort_values('avg_trade', ascending=False)
    else:
        print("\n✅ Found viable strategies!\n")
        viable = viable.sort_values('avg_trade', ascending=False)
        results_df = viable
    
    # Show top 10
    print("🏆 Top 10 Parameter Combinations")
    print("-" * 70)
    
    for idx, (_, row) in enumerate(results_df.head(10).iterrows(), 1):
        print(f"\n#{idx}")
        print(f"  Avg Trade: {row['avg_trade']:.2f}% ⭐")
        print(f"  Return: {row['return']:.2f}%")
        print(f"  Sharpe: {row['sharpe']:.2f}")
        print(f"  Max DD: {row['max_dd']:.2f}%")
        print(f"  Win Rate: {row['win_rate']:.2f}%")
        print(f"  Trades: {int(row['trades'])}")
        print(f"  Parameters:")
        print(f"    MA: {int(row['ma_length'])}, Key: {row['key_value']:.1f}, ATR: {row['adaptive_atr_mult']:.1f}")
        print(f"    TP1 RR: {row['tp1_rr_long']:.1f}, TP1%: {int(row['tp1_percent'])}, TP2 RR: {row['tp2_rr_long']:.1f}")
    
    # Save results
    results_df.to_csv('agbot_4h_optimization_results.csv', index=False)
    print(f"\n✅ Full results saved to agbot_4h_optimization_results.csv")
    
    return results_df

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🌙 AGBot Strategy Optimization - TSLA 4H")
    print("="*70)
    print("Objective: Find parameters for 1-2% average trade size")
    
    # Fetch 1 year of 4H data
    df = fetch_data("TSLA", period_days=365, interval='4h')
    
    if df is not None:
        results_df = optimize_strategy(df)
        
        if results_df is not None:
            print("\n" + "="*70)
            print("✨ Optimization Complete!")
            print("="*70)
    
    print("\nDone!")
