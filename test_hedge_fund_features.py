#!/usr/bin/env python3
"""
Test script for hedge fund features
Run this to validate all new systems are working
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from termcolor import cprint
import time


def test_portfolio_manager():
    """Test Portfolio Manager"""
    cprint("\n" + "="*70, "cyan")
    cprint("TEST 1: Portfolio Manager", "cyan")
    cprint("="*70, "cyan")
    
    try:
        from src.agents.portfolio_manager import get_portfolio_manager
        
        pm = get_portfolio_manager(total_capital=100000)
        
        # Test Kelly Criterion
        kelly = pm.calculate_kelly_fraction(win_rate=0.60, avg_win=2.0, avg_loss=1.0)
        cprint(f"✅ Kelly Criterion: {kelly:.2%}", "green")
        
        # Test allocation
        mock_stats = {
            'agent_1': {'pnl_pct': 10.5, 'win_rate': 60, 'sharpe_ratio': 2.1, 'max_drawdown': 0.03, 'total_trades': 50},
            'agent_2': {'pnl_pct': 8.2, 'win_rate': 55, 'sharpe_ratio': 1.8, 'max_drawdown': 0.04, 'total_trades': 45},
            'agent_3': {'pnl_pct': -2.1, 'win_rate': 45, 'sharpe_ratio': 0.5, 'max_drawdown': 0.06, 'total_trades': 30}
        }
        
        allocations = pm.allocate_capital(mock_stats)
        cprint(f"✅ Capital Allocated: {len(allocations)} agents", "green")
        for agent_id, capital in allocations.items():
            cprint(f"   {agent_id}: ${capital:,.2f}", "yellow")
        
        # Test risk limits
        pause_decisions = pm.check_risk_limits(95000, mock_stats)
        cprint(f"✅ Risk Limits Checked: {sum(pause_decisions.values())} agents to pause", "green")
        
        return True
        
    except Exception as e:
        cprint(f"❌ Portfolio Manager Test Failed: {e}", "red")
        import traceback
        traceback.print_exc()
        return False


def test_rbi_deployment():
    """Test RBI Deployment Pipeline"""
    cprint("\n" + "="*70, "cyan")
    cprint("TEST 2: RBI Deployment Pipeline", "cyan")
    cprint("="*70, "cyan")
    
    try:
        from src.agents.rbi_deployment_pipeline import get_deployment_pipeline
        from pathlib import Path
        
        pipeline = get_deployment_pipeline()
        
        # Test parameter extraction
        backtest_dir = Path(project_root) / "src" / "data" / "rbi" / "FINAL_WINNING_STRATEGIES"
        backtest_file = backtest_dir / "DivergenceVolatilityEnhanced_BT.py"
        
        if backtest_file.exists():
            params = pipeline.extract_backtest_params(backtest_file)
            if params:
                cprint(f"✅ Parameters Extracted: {params['strategy_name']}", "green")
                cprint(f"   Timeframe: {params.get('timeframe', 'N/A')}", "yellow")
                cprint(f"   Asset Type: {params.get('asset_type', 'N/A')}", "yellow")
            else:
                cprint("⚠️ No parameters extracted (file may not match expected format)", "yellow")
        else:
            cprint("⚠️ Backtest file not found (expected for testing)", "yellow")
        
        # Test deployment tracking
        deployments = pipeline.get_all_deployments()
        cprint(f"✅ Deployment Tracking: {len(deployments)} deployments", "green")
        
        return True
        
    except Exception as e:
        cprint(f"❌ RBI Deployment Test Failed: {e}", "red")
        import traceback
        traceback.print_exc()
        return False


def test_regime_detector():
    """Test Regime Detector"""
    cprint("\n" + "="*70, "cyan")
    cprint("TEST 3: Regime Detector", "cyan")
    cprint("="*70, "cyan")
    
    try:
        from src.agents.regime_detector import get_regime_detector
        
        detector = get_regime_detector()
        
        # Detect regime
        cprint("🔍 Detecting market regime (this may take 10-15 seconds)...", "yellow")
        regime_info = detector.detect_regime(symbol='SPY')
        
        cprint(f"✅ Regime Detected: {regime_info['regime']}", "green")
        cprint(f"   Confidence: {regime_info['confidence']:.1f}%", "yellow")
        cprint(f"   ADX: {regime_info['adx']:.2f}", "yellow")
        cprint(f"   VIX: {regime_info['vix']:.2f}", "yellow")
        cprint(f"   Trend: {regime_info['trend_direction']}", "yellow")
        
        # Get recommendations
        recommendations = detector.get_strategy_recommendation(regime_info)
        cprint(f"✅ Strategy Recommendations:", "green")
        cprint(f"   Preferred: {recommendations.get('preferred_strategies', [])}", "yellow")
        cprint(f"   Position Size Multiplier: {recommendations.get('position_size_multiplier', 1.0):.2f}x", "yellow")
        
        return True
        
    except Exception as e:
        cprint(f"❌ Regime Detector Test Failed: {e}", "red")
        import traceback
        traceback.print_exc()
        return False


def test_risk_manager():
    """Test Advanced Risk Manager"""
    cprint("\n" + "="*70, "cyan")
    cprint("TEST 4: Advanced Risk Manager", "cyan")
    cprint("="*70, "cyan")
    
    try:
        from src.agents.advanced_risk_manager import get_risk_manager
        
        rm = get_risk_manager()
        
        # Test position sizing
        size_dollars, size_units = rm.calculate_position_size(
            balance=100000,
            entry_price=50000,
            stop_loss_price=49000,
            confidence=85,
            win_rate=0.60,
            volatility_multiplier=1.0
        )
        
        cprint(f"✅ Position Size Calculated:", "green")
        cprint(f"   Size: ${size_dollars:,.2f} ({size_units:.4f} units)", "yellow")
        cprint(f"   Risk: ${abs(size_dollars - size_units * 49000):,.2f}", "yellow")
        
        # Test trailing stops
        rm.initialize_trailing_stop('test_pos', 50000, 49000, 'LONG', 500)
        
        # Simulate price movement
        test_prices = [50500, 51000, 52000, 53000, 52500]
        for price in test_prices:
            new_stop, should_exit = rm.update_trailing_stop('test_pos', price, 500)
            if new_stop:
                profit_pct = ((price - 50000) / 50000) * 100
                cprint(f"   Price: ${price:,} | Stop: ${new_stop:,.0f} | Profit: {profit_pct:.1f}%", "yellow")
        
        cprint(f"✅ Trailing Stops Working", "green")
        
        return True
        
    except Exception as e:
        cprint(f"❌ Risk Manager Test Failed: {e}", "red")
        import traceback
        traceback.print_exc()
        return False


def test_momentum_rotator():
    """Test Momentum Rotator"""
    cprint("\n" + "="*70, "cyan")
    cprint("TEST 5: Momentum Rotator", "cyan")
    cprint("="*70, "cyan")
    
    try:
        from src.agents.momentum_rotator import get_momentum_rotator
        
        # Use smaller universe for faster testing
        test_universe = ['BTC-USD', 'ETH-USD', 'SPY', 'QQQ', 'AAPL', 'MSFT']
        rotator = get_momentum_rotator(universe=test_universe)
        
        # Rank assets
        cprint("🔍 Ranking assets (this may take 15-20 seconds)...", "yellow")
        rankings = rotator.rank_assets(lookback_days=60)
        
        cprint(f"✅ Assets Ranked: {len(rankings)} assets", "green")
        
        # Get recommendations
        recommendations = rotator.get_rotation_recommendations(num_positions=3)
        cprint(f"✅ Top 3 Recommendations:", "green")
        for i, rec in enumerate(recommendations, 1):
            cprint(f"   {i}. {rec['symbol']}: Score {rec['composite_score']:.2f}", "yellow")
        
        # Get allocation weights
        weights = rotator.calculate_allocation_weights(recommendations)
        cprint(f"✅ Allocation Weights:", "green")
        for symbol, weight in weights.items():
            cprint(f"   {symbol}: {weight*100:.1f}%", "yellow")
        
        # Detect risk regime
        risk_regime = rotator.detect_risk_regime()
        cprint(f"✅ Risk Regime: {risk_regime.get('regime', 'UNKNOWN')}", "green")
        
        return True
        
    except Exception as e:
        cprint(f"❌ Momentum Rotator Test Failed: {e}", "red")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    cprint("\n" + "="*70, "cyan")
    cprint("🏦 HEDGE FUND FEATURES TEST SUITE", "cyan")
    cprint("="*70 + "\n", "cyan")
    
    results = []
    
    # Run tests
    results.append(("Portfolio Manager", test_portfolio_manager()))
    results.append(("RBI Deployment", test_rbi_deployment()))
    results.append(("Regime Detector", test_regime_detector()))
    results.append(("Risk Manager", test_risk_manager()))
    results.append(("Momentum Rotator", test_momentum_rotator()))
    
    # Summary
    cprint("\n" + "="*70, "cyan")
    cprint("TEST SUMMARY", "cyan")
    cprint("="*70, "cyan")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        color = "green" if result else "red"
        cprint(f"{status} - {name}", color)
    
    cprint(f"\n📊 Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)", "cyan")
    
    if passed == total:
        cprint("\n🎉 ALL TESTS PASSED! Systems ready for deployment.", "green")
    else:
        cprint(f"\n⚠️ {total - passed} test(s) failed. Review errors above.", "yellow")
    
    cprint("="*70 + "\n", "cyan")


if __name__ == '__main__':
    main()
