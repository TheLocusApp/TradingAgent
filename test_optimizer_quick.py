"""
Quick test of optimizer with fixed data fetching
Tests just the best parameters from initial test
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.strategy_optimizer import StrategyOptimizer

def test_best_params():
    """Test the best parameters from initial optimization"""
    print("\n" + "="*70)
    print("🚀 Testing Best Parameters from Initial Optimization")
    print("="*70)
    
    optimizer = StrategyOptimizer()
    
    # Fetch 1H data
    print("\n📊 Fetching 1H TSLA data...")
    df = optimizer.fetch_data('TSLA', '1h')
    
    if df is None:
        print("❌ Failed to fetch data")
        return
    
    print(f"✅ Fetched {len(df)} candles")
    
    # Test the best parameters from initial test
    best_params = {
        'ma_length': 250,
        'key_value': 1.5,
        'adaptive_atr_mult': 2.0,
        'tp1_rr_long': 0.5,
        'tp1_percent': 45
    }
    
    print(f"\n🔍 Testing best parameters from initial test:")
    print(f"   MA Length: {best_params['ma_length']}")
    print(f"   Key Value: {best_params['key_value']}")
    print(f"   ATR Mult: {best_params['adaptive_atr_mult']}")
    print(f"   TP1 RR: {best_params['tp1_rr_long']}")
    print(f"   TP1 %: {best_params['tp1_percent']}")
    
    result = optimizer.test_parameters(df, '1h', **best_params)
    
    if result:
        print(f"\n✅ Test completed!")
        print(f"   Return: {result['return']:.2f}%")
        print(f"   Sharpe: {result['sharpe']:.2f}")
        print(f"   Win Rate: {result['win_rate']:.2f}%")
        print(f"   Trades: {result['trades']}")
        print(f"   Max DD: {result['max_dd']:.2f}%")
        
        # Compare with initial test
        print(f"\n📋 Comparison with initial test:")
        print(f"   Initial: Return=43.19%, Sharpe=1.62, Trades=67")
        print(f"   Current: Return={result['return']:.2f}%, Sharpe={result['sharpe']:.2f}, Trades={result['trades']}")
        
        if abs(result['return'] - 43.19) < 1 and result['trades'] > 60:
            print(f"   ✅ PASS: Results match initial test!")
        else:
            print(f"   ⚠️  Results differ - may need further investigation")
    else:
        print(f"❌ Test failed")

if __name__ == "__main__":
    test_best_params()
