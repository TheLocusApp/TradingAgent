"""
Direct test of optimizer - bypass Flask
Tests if the optimizer works at all
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.strategy_optimizer import optimize_strategy
import time

print("\n" + "="*70)
print("🧪 Direct Optimizer Test")
print("="*70)

print("\n⏱️  Starting optimization...")
start_time = time.time()

try:
    # Test with realistic settings
    # For swing trade (1h, 4h, 1d), need at least 2x the max MA length
    # Max MA length is 200, so need at least 400 bars
    result = optimize_strategy(
        symbol='TSLA',
        trade_type='swing',
        max_bars=2000  # Realistic for swing trade
    )
    
    elapsed = time.time() - start_time
    
    print(f"\n✅ Optimization complete in {elapsed:.1f} seconds")
    print(f"\nResults:")
    print(f"  Symbol: {result.get('symbol')}")
    print(f"  Trade Type: {result.get('trade_type')}")
    print(f"  Best Combinations: {len(result.get('best_combinations', []))}")
    
    if result.get('best_combinations'):
        best = result['best_combinations'][0]
        print(f"\n🏆 Best Combination:")
        print(f"  Timeframe: {best['timeframe']}")
        print(f"  Sharpe: {best['sharpe']:.2f}")
        print(f"  Return: {best['return']:.2f}%")
        print(f"  Trades: {best['trades']}")
    
except Exception as e:
    elapsed = time.time() - start_time
    print(f"\n❌ Error after {elapsed:.1f} seconds:")
    print(f"  {type(e).__name__}: {e}")
    
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()

print("\n" + "="*70)
