#!/usr/bin/env python3
"""
Test RBI Agent RL Implementation
Verifies that RBI RL optimizer integrates correctly
"""

import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.agents.rbi_agent_rl import RBIAgentRL, RBIBacktestResult
from src.config.trading_config import TradingConfig


def test_rbi_rl_initialization():
    """Test RBI RL agent initialization"""
    print("\n✅ Test 1: RBI RL Initialization")
    
    # Test disabled
    agent_disabled = RBIAgentRL(enable_rl=False)
    assert agent_disabled.enable_rl == False, "enable_rl should be False"
    assert agent_disabled.rl_status == "inactive", "rl_status should be inactive"
    print("   ✓ Disabled mode works correctly")
    
    # Test enabled
    agent_enabled = RBIAgentRL(enable_rl=True, rl_training_backtests=10)
    assert agent_enabled.enable_rl == True, "enable_rl should be True"
    assert agent_enabled.rl_status == "training", "rl_status should be training"
    assert agent_enabled.rl_training_backtests == 10, "rl_training_backtests should be 10"
    print("   ✓ Enabled mode works correctly")
    print("   ✓ Training status initialized")


def test_rbi_backtest_result():
    """Test RBI backtest result creation"""
    print("\n✅ Test 2: RBI Backtest Result")
    
    result = RBIBacktestResult(
        strategy_name="TestStrategy",
        win_rate=55.5,
        sharpe_ratio=1.2,
        total_return=25.5,
        total_trades=50,
        max_drawdown=10.5
    )
    
    assert result.strategy_name == "TestStrategy", "strategy_name should match"
    assert result.win_rate == 55.5, "win_rate should match"
    assert result.sharpe_ratio == 1.2, "sharpe_ratio should match"
    assert result.total_return == 25.5, "total_return should match"
    assert result.total_trades == 50, "total_trades should match"
    assert result.max_drawdown == 10.5, "max_drawdown should match"
    print("   ✓ Backtest result created correctly")


def test_record_backtest_result():
    """Test recording backtest results"""
    print("\n✅ Test 3: Record Backtest Results")
    
    agent = RBIAgentRL(enable_rl=True, rl_training_backtests=3)
    
    # Record first backtest
    result1 = RBIBacktestResult(
        strategy_name="Strategy1",
        win_rate=50.0,
        sharpe_ratio=1.0,
        total_return=20.0,
        total_trades=40,
        max_drawdown=15.0
    )
    agent.record_backtest_result(result1)
    assert len(agent.backtest_history) == 1, "Should have 1 backtest"
    print("   ✓ First backtest recorded")
    
    # Record second backtest
    result2 = RBIBacktestResult(
        strategy_name="Strategy2",
        win_rate=55.0,
        sharpe_ratio=1.2,
        total_return=25.0,
        total_trades=45,
        max_drawdown=12.0
    )
    agent.record_backtest_result(result2)
    assert len(agent.backtest_history) == 2, "Should have 2 backtests"
    print("   ✓ Second backtest recorded")
    
    # Record third backtest (should trigger optimization)
    result3 = RBIBacktestResult(
        strategy_name="Strategy3",
        win_rate=60.0,
        sharpe_ratio=1.5,
        total_return=30.0,
        total_trades=50,
        max_drawdown=10.0
    )
    agent.record_backtest_result(result3)
    assert len(agent.backtest_history) == 3, "Should have 3 backtests"
    assert agent.rl_status == "optimized", "Should be optimized after 3 backtests"
    print("   ✓ Third backtest recorded")
    print("   ✓ Optimization triggered automatically")


def test_rl_status_display():
    """Test RL status display"""
    print("\n✅ Test 4: RL Status Display")
    
    agent = RBIAgentRL(enable_rl=True, rl_training_backtests=10)
    
    # Check training status
    status = agent.get_rl_status_display()
    assert status['status'] == 'training', "Status should be training"
    assert '🔄' in status['label'], "Label should have refresh emoji"
    assert '0/10' in status['label'], "Label should show progress"
    assert status['color'] == '#f59e0b', "Color should be yellow"
    print("   ✓ Training status display correct")
    
    # Add some backtests
    for i in range(5):
        result = RBIBacktestResult(
            strategy_name=f"Strategy{i}",
            win_rate=50.0 + i,
            sharpe_ratio=1.0 + i * 0.1,
            total_return=20.0 + i * 5,
            total_trades=40 + i * 5,
            max_drawdown=15.0 - i
        )
        agent.record_backtest_result(result)
    
    status = agent.get_rl_status_display()
    assert '5/10' in status['label'], "Label should show 5/10"
    assert status['progress'] == 50, "Progress should be 50%"
    print("   ✓ Progress display correct (5/10)")
    
    # Complete training
    for i in range(5, 10):
        result = RBIBacktestResult(
            strategy_name=f"Strategy{i}",
            win_rate=50.0 + i,
            sharpe_ratio=1.0 + i * 0.1,
            total_return=20.0 + i * 5,
            total_trades=40 + i * 5,
            max_drawdown=15.0 - i
        )
        agent.record_backtest_result(result)
    
    status = agent.get_rl_status_display()
    assert status['status'] == 'optimized', "Status should be optimized"
    assert '✨' in status['label'], "Label should have sparkle emoji"
    assert status['color'] == '#10b981', "Color should be green"
    print("   ✓ Optimized status display correct")


def test_reward_calculation():
    """Test reward calculation"""
    print("\n✅ Test 5: Reward Calculation")
    
    agent = RBIAgentRL(enable_rl=True)
    
    # Add backtests
    results = [
        RBIBacktestResult("S1", 50.0, 1.0, 20.0, 40, 15.0),
        RBIBacktestResult("S2", 55.0, 1.2, 25.0, 45, 12.0),
        RBIBacktestResult("S3", 60.0, 1.5, 30.0, 50, 10.0),
    ]
    
    for result in results:
        agent.record_backtest_result(result)
    
    reward = agent.calculate_reward()
    assert reward > 0, "Reward should be positive"
    assert isinstance(reward, float), "Reward should be float"
    print(f"   ✓ Reward calculated: {reward:.4f}")
    
    # Verify formula: (win_rate * 0.4) + (sharpe * 0.3) + (return * 0.3)
    avg_win_rate = (50.0 + 55.0 + 60.0) / 3  # 55.0
    avg_sharpe = (1.0 + 1.2 + 1.5) / 3  # 1.233
    avg_return = (20.0 + 25.0 + 30.0) / 3  # 25.0
    expected_reward = (avg_win_rate * 0.4) + (avg_sharpe * 0.3) + (avg_return * 0.3)
    
    assert abs(reward - expected_reward) < 0.01, "Reward calculation should match formula"
    print(f"   ✓ Reward formula verified: {expected_reward:.4f}")


def test_best_worst_backtest():
    """Test getting best and worst backtests"""
    print("\n✅ Test 6: Best/Worst Backtest")
    
    agent = RBIAgentRL(enable_rl=True)
    
    results = [
        RBIBacktestResult("S1", 50.0, 1.0, 20.0, 40, 15.0),
        RBIBacktestResult("S2", 55.0, 1.2, 25.0, 45, 12.0),
        RBIBacktestResult("S3", 60.0, 1.5, 30.0, 50, 10.0),
        RBIBacktestResult("S4", 45.0, 0.8, 15.0, 35, 20.0),
    ]
    
    for result in results:
        agent.record_backtest_result(result)
    
    best = agent.get_best_backtest()
    assert best.strategy_name == "S3", "Best should be S3 (30% return)"
    assert best.total_return == 30.0, "Best return should be 30%"
    print(f"   ✓ Best backtest: {best.strategy_name} ({best.total_return:.1f}%)")
    
    worst = agent.get_worst_backtest()
    assert worst.strategy_name == "S4", "Worst should be S4 (15% return)"
    assert worst.total_return == 15.0, "Worst return should be 15%"
    print(f"   ✓ Worst backtest: {worst.strategy_name} ({worst.total_return:.1f}%)")


def test_optimization_suggestions():
    """Test optimization suggestions"""
    print("\n✅ Test 7: Optimization Suggestions")
    
    agent = RBIAgentRL(enable_rl=True)
    
    results = [
        RBIBacktestResult("S1", 65.0, 1.5, 60.0, 100, 10.0),
        RBIBacktestResult("S2", 35.0, 0.5, 5.0, 20, 25.0),
        RBIBacktestResult("S3", 55.0, 1.2, 30.0, 50, 15.0),
    ]
    
    for result in results:
        agent.record_backtest_result(result)
    
    suggestions = agent.get_optimization_suggestions()
    assert len(suggestions) > 0, "Should have suggestions"
    assert any('65' in s for s in suggestions), "Should mention best win rate"
    assert any('35' in s for s in suggestions), "Should mention worst win rate"
    print(f"   ✓ Generated {len(suggestions)} suggestions")
    for suggestion in suggestions:
        print(f"      • {suggestion}")


def test_rbi_config_fields():
    """Test RBI RL config fields"""
    print("\n✅ Test 8: RBI Config Fields")
    
    config = TradingConfig(
        agent_name="RBI Test",
        asset_type="crypto",
        ticker="BTC",
        monitored_assets=["BTC", "ETH"],
        enable_rbi_rl=True,
        rbi_rl_training_backtests=10
    )
    
    assert config.enable_rbi_rl == True, "enable_rbi_rl should be True"
    assert config.rbi_rl_training_backtests == 10, "rbi_rl_training_backtests should be 10"
    assert config.rbi_rl_status == "inactive", "rbi_rl_status should be inactive"
    print("   ✓ RBI RL config fields initialized")
    
    # Test serialization
    config_dict = config.to_dict()
    assert 'enable_rbi_rl' in config_dict, "enable_rbi_rl should be in dict"
    assert config_dict['enable_rbi_rl'] == True, "enable_rbi_rl should be True in dict"
    print("   ✓ Config serializes correctly")
    
    # Test deserialization
    config2 = TradingConfig.from_dict(config_dict)
    assert config2.enable_rbi_rl == True, "enable_rbi_rl should be True after deserialization"
    print("   ✓ Config deserializes correctly")


def test_record_from_dict():
    """Test recording backtest from dictionary"""
    print("\n✅ Test 9: Record from Dictionary")
    
    agent = RBIAgentRL(enable_rl=True)
    
    backtest_data = {
        'strategy_name': 'TestStrategy',
        'win_rate': 55.5,
        'sharpe_ratio': 1.2,
        'total_return': 25.5,
        'total_trades': 50,
        'max_drawdown': 10.5
    }
    
    agent.record_backtest_from_dict(backtest_data)
    assert len(agent.backtest_history) == 1, "Should have 1 backtest"
    
    result = agent.backtest_history[0]
    assert result.strategy_name == 'TestStrategy', "strategy_name should match"
    assert result.win_rate == 55.5, "win_rate should match"
    print("   ✓ Backtest recorded from dictionary")


def test_summary():
    """Test getting summary"""
    print("\n✅ Test 10: Summary")
    
    agent = RBIAgentRL(enable_rl=True)
    
    # Empty summary
    summary = agent.get_summary()
    assert summary['backtest_count'] == 0, "Should have 0 backtests"
    assert summary['reward'] == 0.0, "Reward should be 0"
    print("   ✓ Empty summary correct")
    
    # Add backtests
    results = [
        RBIBacktestResult("S1", 50.0, 1.0, 20.0, 40, 15.0),
        RBIBacktestResult("S2", 55.0, 1.2, 25.0, 45, 12.0),
        RBIBacktestResult("S3", 60.0, 1.5, 30.0, 50, 10.0),
    ]
    
    for result in results:
        agent.record_backtest_result(result)
    
    summary = agent.get_summary()
    assert summary['backtest_count'] == 3, "Should have 3 backtests"
    assert summary['best_return'] == 30.0, "Best return should be 30%"
    assert summary['best_strategy'] == "S3", "Best strategy should be S3"
    assert 'avg_win_rate' in summary, "Should have avg_win_rate"
    assert 'avg_sharpe' in summary, "Should have avg_sharpe"
    print("   ✓ Summary with backtests correct")
    print(f"      Backtests: {summary['backtest_count']}")
    print(f"      Best Return: {summary['best_return']:.1f}%")
    print(f"      Avg Win Rate: {summary['avg_win_rate']:.1f}%")
    print(f"      Avg Sharpe: {summary['avg_sharpe']:.2f}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 RBI Agent RL Test Suite")
    print("="*60)
    
    try:
        test_rbi_rl_initialization()
        test_rbi_backtest_result()
        test_record_backtest_result()
        test_rl_status_display()
        test_reward_calculation()
        test_best_worst_backtest()
        test_optimization_suggestions()
        test_rbi_config_fields()
        test_record_from_dict()
        test_summary()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60 + "\n")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n⚠️ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
