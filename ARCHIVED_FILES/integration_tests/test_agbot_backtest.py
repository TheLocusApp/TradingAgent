"""
AGBot Strategy Backtest - TSLA 1H
Test with 1 week of data first, then optimize
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
    # Columns are in format (OHLCV, Ticker)
    if isinstance(df.columns, pd.MultiIndex):
        # Get level 0 (OHLCV names)
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

def run_backtest(df, params=None):
    """Run backtest with optional parameters"""
    if df is None or df.empty:
        print("❌ No data to backtest")
        return None
    
    print("\n" + "="*60)
    print("🚀 Running Backtest")
    print("="*60)
    
    try:
        bt = Backtest(
            df,
            AGBotStrategy,
            cash=10000,
            commission=0.0003,  # 0.03% for stocks
            exclusive_orders=True
        )
        
        if params:
            print(f"📋 Parameters: {params}")
            stats = bt.run(**params)
        else:
            print("📋 Using default parameters")
            stats = bt.run()
        
        print("\n" + "="*60)
        print("📈 Backtest Results")
        print("="*60)
        print(stats)
        
        return stats, bt
    
    except Exception as e:
        print(f"❌ Backtest error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

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
        
        print("⏳ This may take a few minutes...")
        
        stats, heatmap = bt.optimize(
            ma_length=[50, 100, 150, 200, 250, 300],
            key_value=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
            adaptive_atr_mult=[0.5, 1.0, 1.5, 2.0, 2.5],
            tp1_rr_long=[0.5, 1.0, 1.5, 2.0],
            tp1_percent=[20, 30, 40, 50],
            maximize='Equity Final [$]',
            constraint=lambda p: p.tp2_rr_long > p.tp1_rr_long,
            max_tries=100  # Limit to prevent excessive runtime
        )
        
        print("\n" + "="*60)
        print("✨ Optimization Results")
        print("="*60)
        print(stats)
        
        print("\n" + "="*60)
        print("🔥 Best Parameters")
        print("="*60)
        print(f"MA Length: {stats._strategy.ma_length}")
        print(f"Key Value: {stats._strategy.key_value}")
        print(f"Adaptive ATR Mult: {stats._strategy.adaptive_atr_mult}")
        print(f"TP1 RR Long: {stats._strategy.tp1_rr_long}")
        print(f"TP1 Percent: {stats._strategy.tp1_percent}")
        
        return stats, heatmap, bt
    
    except Exception as e:
        print(f"❌ Optimization error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None, None

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌙 AGBot Strategy Backtest - TSLA 1H")
    print("="*60)
    
    # Step 1: Test with 1 week of data
    print("\n📍 PHASE 1: Testing with 1 week of data")
    df_week = fetch_data("TSLA", period_days=7)
    
    if df_week is not None:
        stats_week, bt_week = run_backtest(df_week)
        
        if stats_week is not None:
            print("\n✅ Strategy generated trades on 1-week data!")
            print(f"Total Trades: {stats_week['# Trades']}")
            print(f"Win Rate: {stats_week['Win Rate [%]']:.2f}%")
            print(f"Return: {stats_week['Return [%]']:.2f}%")
            
            # Step 2: Fetch full year data
            print("\n📍 PHASE 2: Fetching 1 year of data for optimization")
            df_year = fetch_data("TSLA", period_days=365)
            
            if df_year is not None:
                # Run default backtest on full year
                stats_year, bt_year = run_backtest(df_year)
                
                if stats_year is not None:
                    print(f"\n✅ Full year backtest complete!")
                    print(f"Total Trades: {stats_year['# Trades']}")
                    print(f"Win Rate: {stats_year['Win Rate [%]']:.2f}%")
                    print(f"Return: {stats_year['Return [%]']:.2f}%")
                    
                    # Step 3: Optimize parameters
                    print("\n📍 PHASE 3: Optimizing parameters on full year data")
                    opt_stats, opt_heatmap, opt_bt = optimize_strategy(df_year)
                    
                    if opt_stats is not None:
                        print("\n✅ Optimization complete!")
                        print(f"Final Equity: ${opt_stats['Equity Final [$]']:.2f}")
                        print(f"Return: {opt_stats['Return [%]']:.2f}%")
                        print(f"Sharpe Ratio: {opt_stats['Sharpe Ratio']:.2f}")
                        print(f"Max Drawdown: {opt_stats['Max. Drawdown [%]']:.2f}%")
        else:
            print("\n⚠️  No trades generated on 1-week data. Strategy may need adjustment.")
    
    print("\n" + "="*60)
    print("✨ Backtest Complete!")
    print("="*60)
