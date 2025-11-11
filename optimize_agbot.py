"""
AGBot Strategy Optimization - TSLA 1H
Optimize parameters to maximize returns and Sharpe ratio
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
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    return df

def optimize_strategy(df):
    """Optimize strategy parameters"""
    if df is None or df.empty:
        print("❌ No data to optimize")
        return None
    
    print("\n" + "="*60)
    print("🔍 Optimizing Strategy Parameters")
    print("="*60)
    
    try:
        bt = Backtest(
            df,
            AGBotStrategy,
            cash=10000,
            commission=0.0003,
            exclusive_orders=True
        )
        
        print("⏳ Optimization in progress (this may take several minutes)...")
        print("Testing parameter combinations...")
        
        # Optimize with reduced parameter space for faster testing
        stats = bt.optimize(
            ma_length=[100, 150, 200, 250],
            key_value=[1.5, 2.0, 2.5, 3.0],
            adaptive_atr_mult=[1.0, 1.5, 2.0],
            tp1_rr_long=[0.5, 1.0, 1.5],
            tp1_percent=[25, 35, 45],
            maximize='Return [%]',
            constraint=lambda p: p.tp2_rr_long > p.tp1_rr_long,
            max_tries=200
        )
        
        print("\n" + "="*60)
        print("✨ Optimization Results - Best Parameters Found")
        print("="*60)
        
        print(f"\n📊 Performance Metrics:")
        print(f"  Return: {stats['Return [%]']:.2f}%")
        print(f"  Sharpe Ratio: {stats['Sharpe Ratio']:.2f}")
        print(f"  Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
        print(f"  Win Rate: {stats['Win Rate [%]']:.2f}%")
        print(f"  # Trades: {stats['# Trades']}")
        print(f"  Profit Factor: {stats['Profit Factor']:.2f}")
        
        print(f"\n🎯 Optimized Parameters:")
        print(f"  MA Length: {stats._strategy.ma_length}")
        print(f"  Key Value (UT Bot): {stats._strategy.key_value}")
        print(f"  Adaptive ATR Mult: {stats._strategy.adaptive_atr_mult}")
        print(f"  TP1 RR Long: {stats._strategy.tp1_rr_long}")
        print(f"  TP1 Percent: {stats._strategy.tp1_percent}")
        print(f"  TP2 RR Long: {stats._strategy.tp2_rr_long}")
        
        return stats
    
    except Exception as e:
        print(f"❌ Optimization error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def run_backtest_with_params(df, params):
    """Run backtest with specific parameters"""
    print("\n" + "="*60)
    print("🚀 Running Backtest with Optimized Parameters")
    print("="*60)
    
    try:
        bt = Backtest(
            df,
            AGBotStrategy,
            cash=10000,
            commission=0.0003,
            exclusive_orders=True
        )
        
        stats = bt.run(**params)
        
        print(f"\n📊 Results:")
        print(f"  Return: {stats['Return [%]']:.2f}%")
        print(f"  Sharpe Ratio: {stats['Sharpe Ratio']:.2f}")
        print(f"  Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
        print(f"  Win Rate: {stats['Win Rate [%]']:.2f}%")
        print(f"  # Trades: {stats['# Trades']}")
        
        return stats
    
    except Exception as e:
        print(f"❌ Backtest error: {str(e)}")
        return None

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌙 AGBot Strategy Optimization - TSLA 1H")
    print("="*60)
    
    # Fetch 1 year of data
    print("\n📍 Fetching 1 year of historical data...")
    df = fetch_data("TSLA", period_days=365)
    
    if df is not None:
        # Run optimization
        opt_stats = optimize_strategy(df)
        
        if opt_stats is not None:
            print("\n✅ Optimization complete!")
            print("\n" + "="*60)
            print("📈 Full Results")
            print("="*60)
            print(opt_stats)
    
    print("\n" + "="*60)
    print("✨ Done!")
    print("="*60)
