"""
CONSISTENCY CHECK: Test same parameters with both strategies
This will reveal if the issue is:
1. Different strategy implementations (AGBot vs AGBotGeneric)
2. Different data handling
3. Different backtesting setup
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from datetime import datetime
import yfinance as yf
from backtesting import Backtest
from src.strategies.AGBot import AGBotStrategy
from src.strategies.AGBotGeneric import AGBotGeneric
import warnings
warnings.filterwarnings('ignore')

print("\n" + "="*70)
print("🔍 CONSISTENCY CHECK: AGBot vs AGBotGeneric")
print("="*70)

# Fetch exact same data as early test
start_date = "2024-04-26"
end_date = "2025-11-06"

print(f"\n📊 Fetching TSLA 4H data...")
print(f"   Period: {start_date} to {end_date}")

df = yf.download("TSLA", start=start_date, end=end_date, interval='4h', progress=False)

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

print(f"✅ Fetched {len(df)} candles")
print(f"   Date range: {df.index[0]} to {df.index[-1]}")

# EXACT parameters from early test
params = {
    'ma_length': 150,
    'key_value': 2.5,
    'adaptive_atr_mult': 2.5,
    'tp1_rr_long': 2.5,
    'tp1_percent': 20,
    'tp2_rr_long': 4.0
}

print(f"\n📋 Testing Parameters:")
for k, v in params.items():
    print(f"   {k}: {v}")

# Test 1: Original AGBotStrategy
print(f"\n{'='*70}")
print("TEST 1: Original AGBotStrategy")
print(f"{'='*70}")

try:
    class TestStrategy1(AGBotStrategy):
        pass
    
    for key, value in params.items():
        setattr(TestStrategy1, key, value)
    
    bt1 = Backtest(df, TestStrategy1, cash=5000, commission=0.0003, exclusive_orders=True)
    stats1 = bt1.run()
    
    print(f"✅ Return: {stats1['Return [%]']:.2f}%")
    print(f"   Sharpe: {stats1['Sharpe Ratio']:.2f}")
    print(f"   Trades: {int(stats1['# Trades'])}")
    print(f"   Avg Trade: {stats1['Avg. Trade [%]']:.2f}%")
    print(f"   Win Rate: {stats1['Win Rate [%]']:.2f}%")
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {str(e)[:100]}")
    stats1 = None

# Test 2: New AGBotGeneric
print(f"\n{'='*70}")
print("TEST 2: New AGBotGeneric")
print(f"{'='*70}")

try:
    class TestStrategy2(AGBotGeneric):
        pass
    
    for key, value in params.items():
        setattr(TestStrategy2, key, value)
    
    bt2 = Backtest(df, TestStrategy2, cash=5000, commission=0.0003, exclusive_orders=True)
    stats2 = bt2.run()
    
    print(f"✅ Return: {stats2['Return [%]']:.2f}%")
    print(f"   Sharpe: {stats2['Sharpe Ratio']:.2f}")
    print(f"   Trades: {int(stats2['# Trades'])}")
    print(f"   Avg Trade: {stats2['Avg. Trade [%]']:.2f}%")
    print(f"   Win Rate: {stats2['Win Rate [%]']:.2f}%")
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {str(e)[:100]}")
    stats2 = None

# COMPARISON
print(f"\n{'='*70}")
print("🔍 COMPARISON")
print(f"{'='*70}")

if stats1 is not None and stats2 is not None:
    print(f"\n{'Metric':<20} {'AGBotStrategy':<20} {'AGBotGeneric':<20} {'Match?':<10}")
    print("-" * 70)
    
    metrics = [
        ('Return [%]', 'Return [%]'),
        ('Sharpe Ratio', 'Sharpe Ratio'),
        ('# Trades', '# Trades'),
        ('Avg. Trade [%]', 'Avg. Trade [%]'),
        ('Win Rate [%]', 'Win Rate [%]'),
    ]
    
    for metric_name, stat_key in metrics:
        val1 = stats1[stat_key]
        val2 = stats2[stat_key]
        match = "✅ YES" if abs(val1 - val2) < 0.01 else "❌ NO"
        print(f"{metric_name:<20} {val1:<20.2f} {val2:<20.2f} {match:<10}")
    
    if abs(stats1['Return [%]'] - stats2['Return [%]']) > 0.1:
        print(f"\n🚨 CRITICAL: Return differs by {abs(stats1['Return [%]'] - stats2['Return [%]']):.2f}%")
        print("   This explains the inconsistency!")
else:
    print("❌ Could not compare - one or both tests failed")

print(f"\n{'='*70}")
