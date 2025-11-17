"""
Run RBI Agent for AGBot Strategy Optimization
Uses AI to analyze, backtest, and optimize the AGBot strategy
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents.rbi_agent import RBIAgent
from datetime import datetime

def main():
    print("\n" + "="*70)
    print("🌙 AGBot Strategy Optimization via RBI Agent")
    print("="*70)
    
    # Initialize RBI Agent
    print("\n📍 Initializing RBI Agent...")
    rbi = RBIAgent()
    
    # Strategy description
    strategy_description = """
AGBot Strategy Optimization - TSLA 4H Timeframe

CURRENT ISSUE:
The AGBot strategy generates +43% return on TSLA 1H but with only +0.64% average trade.
This is too small - commissions and slippage eliminate profits.

OPTIMIZATION GOAL:
Improve the strategy to generate 1-2% average trade size while maintaining good Sharpe ratio.

KEY CHANGES TO TEST:
1. Move from 1H to 4H timeframe (fewer, higher-quality trades)
2. Increase TP1 RR from 0.5 to 1.0-2.0 (let winners run more)
3. Reduce TP1 Percent from 45 to 20-30 (take smaller partial profits)
4. Optimize MA length and Key Value for 4H

PARAMETERS TO TEST:
- ma_length: [50, 100, 150, 200]
- key_value: [1.5, 2.0, 2.5, 3.0]
- adaptive_atr_mult: [1.0, 1.5, 2.0, 2.5]
- tp1_rr_long: [1.0, 1.5, 2.0, 2.5]
- tp1_percent: [20, 25, 30]
- tp2_rr_long: [3.0, 4.0, 5.0]

OPTIMIZATION CRITERIA:
1. Primary: Average trade size >= 1.0%
2. Secondary: Sharpe ratio >= 1.5
3. Tertiary: Win rate >= 60%
4. Constraint: Max drawdown <= 15%

BACKTEST SETTINGS:
- Asset: TSLA
- Timeframe: 4H
- Period: 1 year
- Initial Capital: $10,000
- Commission: 0.03%

STRATEGY FILE:
src/strategies/AGBot.py

EXPECTED OUTCOME:
A set of optimized parameters that generate larger, more sustainable trades
with better risk-reward ratios and lower commission impact.
"""
    
    print("\n" + "="*70)
    print("📊 Strategy Optimization Request")
    print("="*70)
    print(strategy_description)
    
    # Run RBI phases
    print("\n" + "="*70)
    print("🚀 Starting RBI Optimization Pipeline")
    print("="*70)
    
    print("\n📍 Phase 1: Research & Analysis")
    print("-" * 70)
    research_result = rbi.research(strategy_description)
    print(research_result)
    
    print("\n📍 Phase 2: Backtest Generation")
    print("-" * 70)
    backtest_code = rbi.backtest(research_result)
    print("✅ Backtest code generated")
    print(f"Lines: {len(backtest_code.split(chr(10)))}")
    
    print("\n📍 Phase 3: Package Optimization")
    print("-" * 70)
    packaged_code = rbi.package(backtest_code)
    print("✅ Code packaged and optimized")
    
    print("\n📍 Phase 4: Debug & Validation")
    print("-" * 70)
    final_code = rbi.debug(packaged_code)
    print("✅ Code debugged and validated")
    
    print("\n" + "="*70)
    print("✨ RBI Optimization Complete!")
    print("="*70)
    
    print("\n📁 Output Files:")
    print("  - Research: src/data/rbi/MM_DD_YYYY/research/")
    print("  - Backtest: src/data/rbi/MM_DD_YYYY/backtests/")
    print("  - Final: src/data/rbi/MM_DD_YYYY/backtests_final/")
    
    print("\n🎯 Next Steps:")
    print("  1. Review generated backtest code")
    print("  2. Run optimization on TSLA 4H data")
    print("  3. Compare results with 1H strategy")
    print("  4. Deploy best parameters to paper trading")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
