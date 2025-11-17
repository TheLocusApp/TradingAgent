"""
Test 4H optimization with adjusted MA lengths
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.strategy_optimizer import StrategyOptimizer

def test_4h():
    """Test 4H optimization"""
    print("\n" + "="*70)
    print("🚀 Testing 4H Optimization with Adjusted MA Lengths")
    print("="*70)
    
    optimizer = StrategyOptimizer()
    
    # Test 4H timeframe
    print("\n📊 Fetching 4H TSLA data...")
    df = optimizer.fetch_data('TSLA', '4h')
    
    if df is not None:
        print(f"✅ Fetched {len(df)} candles")
        
        # Get parameter ranges for 4H
        param_ranges = optimizer.get_parameter_ranges('swing', '4h')
        print(f"\n📋 Parameter Ranges for 4H:")
        print(f"   MA Lengths: {param_ranges['ma_length']}")
        print(f"   Key Values: {param_ranges['key_value']}")
        print(f"   ATR Mults: {param_ranges['adaptive_atr_mult']}")
        print(f"   TP1 RRs: {param_ranges['tp1_rr_long']}")
        print(f"   TP1 %s: {param_ranges['tp1_percent']}")
        
        # Calculate combinations
        total = 1
        for values in param_ranges.values():
            total *= len(values)
        print(f"\n   Total Combinations: {total}")
        
        # Check data requirement
        max_ma = max(param_ranges['ma_length'])
        min_required = max_ma * 2
        print(f"\n📊 Data Check:")
        print(f"   Max MA Length: {max_ma}")
        print(f"   Min Required Bars: {min_required}")
        print(f"   Available Bars: {len(df)}")
        
        if len(df) >= min_required:
            print(f"   ✅ PASS: Sufficient data for optimization!")
        else:
            print(f"   ❌ FAIL: Not enough data")
    else:
        print(f"❌ Failed to fetch data")

if __name__ == "__main__":
    test_4h()
