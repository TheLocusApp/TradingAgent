"""
Test AGBot with exact TradingView parameters
Verify if we can replicate the 2,802% return
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

def fetch_data(symbol, period_days, interval='1h'):
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

def test_parameters(df, params_name, **params):
    """Test strategy with specific parameters"""
    try:
        class TestStrategy(AGBotStrategy):
            pass
        
        # Set all parameters
        for key, value in params.items():
            setattr(TestStrategy, key, value)
        
        bt = Backtest(
            df,
            TestStrategy,
            cash=5000,  # TradingView uses $5000
            commission=0.0003,  # 0.03%
            exclusive_orders=True
        )
        
        stats = bt.run()
        
        return {
            'name': params_name,
            'return': stats['Return [%]'],
            'sharpe': stats['Sharpe Ratio'],
            'max_dd': stats['Max. Drawdown [%]'],
            'win_rate': stats['Win Rate [%]'],
            'trades': stats['# Trades'],
            'avg_trade': stats['Avg. Trade [%]'],
            'profit_factor': stats['Profit Factor'],
            'equity_final': stats['Equity Final [$]']
        }
    except Exception as e:
        print(f"❌ Error testing {params_name}: {str(e)}")
        return None

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🌙 AGBot - Testing TradingView Parameters")
    print("="*70)
    
    # Fetch 1 year of 1H data
    df = fetch_data("TSLA", period_days=365, interval='1h')
    
    if df is not None:
        print("\n" + "="*70)
        print("🧪 Testing Parameter Sets")
        print("="*70)
        
        # TradingView parameters (from your screenshots)
        tradingview_params = {
            'ma_length': 100,
            'key_value': 3,
            'atr_period': 20,
            'adaptive_atr_mult': 4,
            'tp1_rr_long': 3,
            'tp2_rr_long': 6,
            'tp1_percent': 5,
            'tp1_rr_short': 4,
            'tp2_rr_short': 6,
            'risk_per_trade': 10
        }
        
        # Our best 4H parameters (adapted to 1H)
        our_4h_params = {
            'ma_length': 150,
            'key_value': 2.5,
            'adaptive_atr_mult': 2.5,
            'tp1_rr_long': 2.5,
            'tp1_percent': 20,
            'tp2_rr_long': 4.0
        }
        
        # Our best 1H parameters
        our_1h_params = {
            'ma_length': 250,
            'key_value': 1.5,
            'adaptive_atr_mult': 2.0,
            'tp1_rr_long': 0.5,
            'tp1_percent': 45,
            'tp2_rr_long': 3.0
        }
        
        results = []
        
        print("\n1️⃣ Testing TradingView Parameters...")
        result = test_parameters(df, "TradingView", **tradingview_params)
        if result:
            results.append(result)
            print(f"   Return: {result['return']:.2f}%")
            print(f"   Sharpe: {result['sharpe']:.2f}")
            print(f"   Avg Trade: {result['avg_trade']:.2f}%")
        
        print("\n2️⃣ Testing Our 4H Parameters (on 1H)...")
        result = test_parameters(df, "Our 4H Params", **our_4h_params)
        if result:
            results.append(result)
            print(f"   Return: {result['return']:.2f}%")
            print(f"   Sharpe: {result['sharpe']:.2f}")
            print(f"   Avg Trade: {result['avg_trade']:.2f}%")
        
        print("\n3️⃣ Testing Our 1H Parameters...")
        result = test_parameters(df, "Our 1H Params", **our_1h_params)
        if result:
            results.append(result)
            print(f"   Return: {result['return']:.2f}%")
            print(f"   Sharpe: {result['sharpe']:.2f}")
            print(f"   Avg Trade: {result['avg_trade']:.2f}%")
        
        # Summary
        print("\n" + "="*70)
        print("📊 Summary Comparison")
        print("="*70)
        
        results_df = pd.DataFrame(results)
        print("\n" + results_df.to_string(index=False))
        
        print("\n" + "="*70)
        print("🎯 Analysis")
        print("="*70)
        
        tv_result = results[0] if results else None
        if tv_result:
            print(f"\nTradingView Parameters on 1H TSLA (1 year):")
            print(f"  Return: {tv_result['return']:.2f}%")
            print(f"  Sharpe: {tv_result['sharpe']:.2f}")
            print(f"  Win Rate: {tv_result['win_rate']:.2f}%")
            print(f"  Avg Trade: {tv_result['avg_trade']:.2f}%")
            print(f"  Trades: {int(tv_result['trades'])}")
            print(f"  Max DD: {tv_result['max_dd']:.2f}%")
            
            if tv_result['return'] > 100:
                print(f"\n✅ EXCELLENT - Parameters are working well!")
            elif tv_result['return'] > 20:
                print(f"\n✅ GOOD - Solid performance")
            else:
                print(f"\n⚠️ UNDERPERFORMING - Need to investigate")
    
    print("\nDone!")
