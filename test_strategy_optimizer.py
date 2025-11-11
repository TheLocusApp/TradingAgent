"""
Quick test of Strategy Optimizer
Tests the optimizer on a single timeframe with limited parameters
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.strategy_optimizer import StrategyOptimizer
import pandas as pd

def test_single_timeframe():
    """Test optimization on a single timeframe"""
    print("\n" + "="*70)
    print("🧪 Strategy Optimizer - Quick Test")
    print("="*70)
    
    optimizer = StrategyOptimizer()
    
    # Test on TSLA 1H for quick verification
    print("\n📍 Testing: TSLA 1H (limited parameters for speed)")
    
    # Fetch data
    df = optimizer.fetch_data('TSLA', '1h', max_bars=500)
    
    if df is None or len(df) < 100:
        print("❌ Failed to fetch data")
        return False
    
    print(f"✅ Data fetched: {len(df)} candles")
    
    # Test a few parameter combinations manually
    print("\n🔍 Testing parameter combinations...")
    
    test_params = [
        {'ma_length': 100, 'key_value': 1.0, 'adaptive_atr_mult': 1.5, 'tp1_rr_long': 1.0, 'tp1_percent': 20},
        {'ma_length': 150, 'key_value': 2.0, 'adaptive_atr_mult': 2.0, 'tp1_rr_long': 1.5, 'tp1_percent': 25},
        {'ma_length': 200, 'key_value': 2.5, 'adaptive_atr_mult': 2.5, 'tp1_rr_long': 2.0, 'tp1_percent': 30},
    ]
    
    results = []
    for i, params in enumerate(test_params, 1):
        result = optimizer.test_parameters(df, '1h', **params)
        if result:
            results.append(result)
            print(f"\n  Test {i}:")
            print(f"    MA: {result['ma_length']}, Key: {result['key_value']}, ATR: {result['adaptive_atr_mult']}")
            print(f"    Sharpe: {result['sharpe']:.2f}, Return: {result['return']:.2f}%, Trades: {result['trades']}")
    
    if not results:
        print("❌ No valid results")
        return False
    
    print(f"\n✅ Generated {len(results)} valid results")
    
    # Sort by Sharpe
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('sharpe', ascending=False)
    
    print("\n" + "="*70)
    print("📊 Results (sorted by Sharpe Ratio)")
    print("="*70)
    print(results_df[['ma_length', 'key_value', 'adaptive_atr_mult', 'tp1_rr_long', 'tp1_percent', 'sharpe', 'return', 'trades']])
    
    return True

def test_full_optimization():
    """Test full optimization workflow"""
    print("\n" + "="*70)
    print("🚀 Full Optimization Test - TSLA Swing Trade")
    print("="*70)
    print("\n⚠️  This will test 1h, 4h, 1d timeframes")
    print("   Estimated time: 10-15 minutes")
    print("   Press Ctrl+C to cancel\n")
    
    try:
        from src.agents.strategy_optimizer import optimize_strategy
        
        result = optimize_strategy('TSLA', 'swing')
        
        print("\n" + "="*70)
        print("✅ Optimization Complete!")
        print("="*70)
        
        best = result['best_combinations'][0]
        print(f"\n🏆 Best Combination:")
        print(f"   Timeframe: {best['timeframe']}")
        print(f"   MA Length: {best['ma_length']}")
        print(f"   Key Value: {best['key_value']}")
        print(f"   ATR Mult: {best['adaptive_atr_mult']}")
        print(f"   TP1 RR: {best['tp1_rr_long']}")
        print(f"   TP1 %: {best['tp1_percent']}")
        print(f"\n   Sharpe: {best['sharpe']:.2f}")
        print(f"   Return: {best['return']:.2f}%")
        print(f"   Win Rate: {best['win_rate']:.2f}%")
        print(f"   Trades: {best['trades']}")
        
        print(f"\n📊 Top 10 Combinations:")
        best_df = pd.DataFrame(result['best_combinations'])
        print(best_df[['timeframe', 'ma_length', 'key_value', 'sharpe', 'return', 'trades']].head(10))
        
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️  Optimization cancelled by user")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Strategy Optimizer')
    parser.add_argument('--quick', action='store_true', help='Run quick test only')
    parser.add_argument('--full', action='store_true', help='Run full optimization')
    args = parser.parse_args()
    
    if args.full:
        success = test_full_optimization()
    else:
        # Default: quick test
        success = test_single_timeframe()
        
        if success:
            print("\n" + "="*70)
            print("✅ Quick test passed!")
            print("="*70)
            print("\nTo run full optimization on all timeframes:")
            print("  python test_strategy_optimizer.py --full")
    
    sys.exit(0 if success else 1)
