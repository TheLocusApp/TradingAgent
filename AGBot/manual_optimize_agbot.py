"""
AGBot Strategy Manual Optimization - TSLA 1H
Manually test parameter combinations to find best performers
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

def fetch_data(symbol, period_days):
    """Fetch OHLCV data from yfinance"""
    print(f"📊 Fetching {symbol} data for {period_days} days...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days)
    
    df = yf.download(
        symbol, 
        start=start_date, 
        end=end_date, 
        interval='1h',
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
    return df

def test_parameters(df, ma_length, key_value, adaptive_atr_mult, tp1_rr_long, tp1_percent):
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
        
        bt = Backtest(
            df,
            TestStrategy,
            cash=10000,
            commission=0.0003,
            exclusive_orders=True
        )
        
        stats = bt.run()
        
        return {
            'ma_length': ma_length,
            'key_value': key_value,
            'adaptive_atr_mult': adaptive_atr_mult,
            'tp1_rr_long': tp1_rr_long,
            'tp1_percent': tp1_percent,
            'return': stats['Return [%]'],
            'sharpe': stats['Sharpe Ratio'],
            'max_dd': stats['Max. Drawdown [%]'],
            'win_rate': stats['Win Rate [%]'],
            'trades': stats['# Trades'],
            'profit_factor': stats['Profit Factor']
        }
    except Exception as e:
        return None

def optimize_strategy(df):
    """Manually optimize strategy parameters"""
    print("\n" + "="*60)
    print("🔍 Manual Parameter Optimization")
    print("="*60)
    
    # Parameter ranges
    ma_lengths = [100, 150, 200, 250]
    key_values = [1.5, 2.0, 2.5, 3.0]
    adaptive_atr_mults = [1.0, 1.5, 2.0]
    tp1_rr_longs = [0.5, 1.0, 1.5]
    tp1_percents = [25, 35, 45]
    
    total_combinations = len(ma_lengths) * len(key_values) * len(adaptive_atr_mults) * len(tp1_rr_longs) * len(tp1_percents)
    print(f"\n⏳ Testing {total_combinations} parameter combinations...")
    print("This may take 5-10 minutes...\n")
    
    results = []
    tested = 0
    
    for ma_length in ma_lengths:
        for key_value in key_values:
            for adaptive_atr_mult in adaptive_atr_mults:
                for tp1_rr_long in tp1_rr_longs:
                    for tp1_percent in tp1_percents:
                        result = test_parameters(
                            df, ma_length, key_value, adaptive_atr_mult, tp1_rr_long, tp1_percent
                        )
                        
                        if result is not None:
                            results.append(result)
                        
                        tested += 1
                        if tested % 20 == 0:
                            print(f"  Progress: {tested}/{total_combinations} ({100*tested/total_combinations:.1f}%)")
    
    if not results:
        print("❌ No valid results found")
        return None
    
    # Convert to DataFrame for analysis
    results_df = pd.DataFrame(results)
    
    # Sort by return
    results_df = results_df.sort_values('return', ascending=False)
    
    print("\n" + "="*60)
    print("🏆 Top 10 Parameter Combinations (by Return)")
    print("="*60)
    
    for idx, row in results_df.head(10).iterrows():
        print(f"\n#{idx+1}")
        print(f"  Return: {row['return']:.2f}%")
        print(f"  Sharpe: {row['sharpe']:.2f}")
        print(f"  Max DD: {row['max_dd']:.2f}%")
        print(f"  Win Rate: {row['win_rate']:.2f}%")
        print(f"  Trades: {int(row['trades'])}")
        print(f"  Parameters:")
        print(f"    MA Length: {int(row['ma_length'])}")
        print(f"    Key Value: {row['key_value']:.1f}")
        print(f"    ATR Mult: {row['adaptive_atr_mult']:.1f}")
        print(f"    TP1 RR: {row['tp1_rr_long']:.1f}")
        print(f"    TP1 %: {int(row['tp1_percent'])}")
    
    # Also show best by Sharpe ratio
    results_df_sharpe = results_df.sort_values('sharpe', ascending=False)
    
    print("\n" + "="*60)
    print("⭐ Top 5 Parameter Combinations (by Sharpe Ratio)")
    print("="*60)
    
    for idx, (_, row) in enumerate(results_df_sharpe.head(5).iterrows(), 1):
        print(f"\n#{idx}")
        print(f"  Sharpe: {row['sharpe']:.2f}")
        print(f"  Return: {row['return']:.2f}%")
        print(f"  Max DD: {row['max_dd']:.2f}%")
        print(f"  Win Rate: {row['win_rate']:.2f}%")
        print(f"  Trades: {int(row['trades'])}")
        print(f"  Parameters:")
        print(f"    MA Length: {int(row['ma_length'])}")
        print(f"    Key Value: {row['key_value']:.1f}")
        print(f"    ATR Mult: {row['adaptive_atr_mult']:.1f}")
        print(f"    TP1 RR: {row['tp1_rr_long']:.1f}")
        print(f"    TP1 %: {int(row['tp1_percent'])}")
    
    # Save results to CSV
    results_df.to_csv('agbot_optimization_results.csv', index=False)
    print(f"\n✅ Results saved to agbot_optimization_results.csv")
    
    return results_df

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌙 AGBot Strategy Manual Optimization - TSLA 1H")
    print("="*60)
    
    # Fetch 1 year of data
    df = fetch_data("TSLA", period_days=365)
    
    if df is not None:
        results_df = optimize_strategy(df)
        
        if results_df is not None:
            print("\n" + "="*60)
            print("✨ Optimization Complete!")
            print("="*60)
    
    print("\nDone!")
