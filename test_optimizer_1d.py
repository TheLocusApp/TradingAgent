"""
Test 1D optimization with adaptive MA lengths
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.strategy_optimizer import StrategyOptimizer

def test_1d():
    """Test 1D optimization"""
    print("\n" + "="*70)
    print("🚀 Testing 1D Optimization with Adaptive MA Lengths")
    print("="*70)
    
    optimizer = StrategyOptimizer()
    
    # Test 1D timeframe
    print("\n📊 Fetching 1D TSLA data...")
    df = optimizer.fetch_data('TSLA', '1d')
    
    if df is not None:
        print(f"✅ Fetched {len(df)} candles")
        
        # Get parameter ranges for 1D
        param_ranges = optimizer.get_parameter_ranges('swing', '1d')
        print(f"\n📋 Parameter Ranges for 1D (initial):")
        print(f"   MA Lengths: {param_ranges['ma_length']}")
        
        # Simulate what optimizer will do
        max_ma = max(param_ranges['ma_length'])
        min_bars_needed = max_ma * 2
        
        print(f"\n📊 Data Check:")
        print(f"   Max MA Length: {max_ma}")
        print(f"   Min Required Bars: {min_bars_needed}")
        print(f"   Available Bars: {len(df)}")
        
        if len(df) < min_bars_needed:
            print(f"\n   ⚠️  Adjusting MA lengths to fit available data...")
            available_ma_lengths = [ma for ma in param_ranges['ma_length'] if ma * 2 <= len(df)]
            if not available_ma_lengths:
                available_ma_lengths = [min(param_ranges['ma_length'])]
            print(f"   ✅ Using MA lengths: {available_ma_lengths}")
            
            # Calculate new combinations
            total = 1
            for key, values in param_ranges.items():
                if key == 'ma_length':
                    total *= len(available_ma_lengths)
                else:
                    total *= len(values)
            print(f"   Total Combinations: {total}")
        else:
            print(f"   ✅ All MA lengths fit!")
    else:
        print(f"❌ Failed to fetch data")

if __name__ == "__main__":
    test_1d()
