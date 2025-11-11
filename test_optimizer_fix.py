"""
Test script to verify optimizer produces same results as initial test
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.strategy_optimizer import StrategyOptimizer

def test_optimizer():
    """Test that optimizer now uses 1 year of data"""
    print("\n" + "="*70)
    print("🔍 Testing Strategy Optimizer Fix")
    print("="*70)
    
    optimizer = StrategyOptimizer()
    
    # Test 1H timeframe with TSLA
    print("\n📊 Fetching 1H TSLA data (should be 365 days)...")
    df = optimizer.fetch_data('TSLA', '1h')
    
    if df is not None:
        print(f"\n✅ Data fetched successfully!")
        print(f"   Rows: {len(df)}")
        print(f"   Date range: {df.index[0]} to {df.index[-1]}")
        
        # Calculate expected bars for 1H
        days = (df.index[-1] - df.index[0]).days
        expected_bars = days * 24  # Roughly 24 bars per day
        print(f"   Days covered: {days}")
        print(f"   Expected bars: ~{expected_bars}")
        
        # Compare with initial test expectations
        print(f"\n📋 Comparison with initial test:")
        print(f"   Initial test: 1,738 hourly candles (365 days)")
        print(f"   Current test: {len(df)} hourly candles ({days} days)")
        
        if len(df) > 1500:
            print(f"   ✅ PASS: Sufficient data for optimization")
        else:
            print(f"   ❌ FAIL: Not enough data")
            
    else:
        print(f"❌ Failed to fetch data")

if __name__ == "__main__":
    test_optimizer()
