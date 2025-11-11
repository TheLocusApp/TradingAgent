"""
Full optimization test - verify all timeframes produce correct results
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.strategy_optimizer import optimize_strategy
import json

def main():
    print("\n" + "="*70)
    print("🚀 Full Strategy Optimization Test")
    print("="*70)
    
    # Run optimization for swing trade (1h, 4h, 1d)
    result = optimize_strategy('TSLA', 'swing')
    
    if result:
        print(f"\n✅ Optimization completed!")
        
        # Show results for each timeframe
        for timeframe in ['1h', '4h', '1d']:
            if timeframe in result:
                combos = result[timeframe]
                if combos:
                    best = combos[0]
                    print(f"\n📊 {timeframe.upper()} Timeframe:")
                    print(f"   #1 Result:")
                    print(f"      MA Length: {best['ma_length']}")
                    print(f"      Key Value: {best['key_value']}")
                    print(f"      ATR Mult: {best['adaptive_atr_mult']}")
                    print(f"      TP1 RR: {best['tp1_rr_long']}")
                    print(f"      TP1 %: {best['tp1_percent']}")
                    print(f"      Return: {best['return']:.2f}%")
                    print(f"      Sharpe: {best['sharpe']:.2f}")
                    print(f"      Trades: {best['trades']}")
                    
                    # Compare with initial test expectations
                    if timeframe == '1h':
                        print(f"\n      Expected (initial test): Return=43.19%, Sharpe=1.62, Trades=67")
                        if abs(best['return'] - 43.19) < 1 and best['trades'] > 60:
                            print(f"      ✅ MATCH!")
                        else:
                            print(f"      ⚠️  Different")
    else:
        print(f"❌ Optimization failed")

if __name__ == "__main__":
    main()
