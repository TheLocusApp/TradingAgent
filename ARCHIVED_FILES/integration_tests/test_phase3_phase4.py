#!/usr/bin/env python3
"""
Test Phase 3 & 4 Implementation
Verifies Swarm RL and Market Intel RL integration
"""

import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.agents.swarm_agent_rl import SwarmAgentRL, ConsensusResult, TradeOutcome
from src.agents.market_intel_agent_rl import MarketIntelAgentRL, AnalysisType, AnalysisResult, AnalysisOutcome


# ============================================================
# PHASE 3: SWARM AGENT RL TESTS
# ============================================================

def test_swarm_initialization():
    """Test Swarm Agent initialization"""
    print("\n✅ Test 1: Swarm Initialization")
    
    agents = ["Agent1", "Agent2", "Agent3"]
    
    # Test disabled
    swarm_disabled = SwarmAgentRL(agents, enable_rl=False)
    assert swarm_disabled.enable_rl == False, "enable_rl should be False"
    assert swarm_disabled.rl_status == "inactive", "rl_status should be inactive"
    print("   ✓ Disabled mode works correctly")
    
    # Test enabled
    swarm_enabled = SwarmAgentRL(agents, enable_rl=True, rl_training_trades=10)
    assert swarm_enabled.enable_rl == True, "enable_rl should be True"
    assert swarm_enabled.rl_status == "training", "rl_status should be training"
    assert len(swarm_enabled.agent_weights) == 3, "Should have 3 agents"
    print("   ✓ Enabled mode works correctly")
    print("   ✓ Equal weights initialized")


def test_swarm_consensus():
    """Test consensus calculation"""
    print("\n✅ Test 2: Swarm Consensus")
    
    agents = ["Agent1", "Agent2", "Agent3"]
    swarm = SwarmAgentRL(agents, enable_rl=True)
    
    # All agents agree on BUY
    decisions = {
        "Agent1": ("BUY", 80.0),
        "Agent2": ("BUY", 90.0),
        "Agent3": ("BUY", 70.0)
    }
    
    result = swarm.calculate_consensus(decisions)
    assert result.consensus_signal == "BUY", "Consensus should be BUY"
    assert result.confidence > 0, "Confidence should be positive"
    assert len(result.contributing_agents) == 3, "All agents should contribute"
    print("   ✓ Consensus calculated correctly")
    print(f"   ✓ Signal: {result.consensus_signal}, Confidence: {result.confidence:.1f}%")


def test_swarm_weight_update():
    """Test weight updates based on trade outcomes"""
    print("\n✅ Test 3: Swarm Weight Update")
    
    agents = ["Agent1", "Agent2", "Agent3"]
    swarm = SwarmAgentRL(agents, enable_rl=True, rl_training_trades=3)
    
    # Initial weights
    initial_weights = dict(swarm.agent_weights)
    print(f"   ✓ Initial weights: {initial_weights}")
    
    # Winning trade
    trade = TradeOutcome(
        consensus_signal="BUY",
        entry_price=100.0,
        exit_price=110.0,
        pnl=10.0,
        pnl_pct=10.0,
        contributing_agents=["Agent1", "Agent2"]
    )
    swarm.record_trade_outcome(trade)
    
    # Weights should have changed
    new_weights = dict(swarm.agent_weights)
    assert new_weights != initial_weights, "Weights should change after trade"
    assert new_weights["Agent1"] > initial_weights["Agent1"], "Agent1 should be rewarded"
    assert new_weights["Agent2"] > initial_weights["Agent2"], "Agent2 should be rewarded"
    print("   ✓ Weights updated after winning trade")


def test_swarm_optimization_trigger():
    """Test optimization trigger"""
    print("\n✅ Test 4: Swarm Optimization Trigger")
    
    agents = ["Agent1", "Agent2"]
    swarm = SwarmAgentRL(agents, enable_rl=True, rl_training_trades=2)
    
    # Record trades
    for i in range(2):
        trade = TradeOutcome(
            consensus_signal="BUY",
            entry_price=100.0,
            exit_price=105.0 + i,
            pnl=5.0 + i,
            pnl_pct=5.0 + i,
            contributing_agents=["Agent1"]
        )
        swarm.record_trade_outcome(trade)
    
    assert swarm.rl_status == "optimized", "Should be optimized after 2 trades"
    print("   ✓ Optimization triggered automatically")


def test_swarm_status_display():
    """Test swarm status display"""
    print("\n✅ Test 5: Swarm Status Display")
    
    agents = ["Agent1", "Agent2"]
    swarm = SwarmAgentRL(agents, enable_rl=True, rl_training_trades=5)
    
    # Training status
    status = swarm.get_rl_status_display()
    assert status['status'] == 'training', "Status should be training"
    assert '🔄' in status['label'], "Label should have refresh emoji"
    assert status['color'] == '#f59e0b', "Color should be yellow"
    print("   ✓ Training status display correct")
    
    # Add trades
    for i in range(5):
        trade = TradeOutcome(
            consensus_signal="BUY",
            entry_price=100.0,
            exit_price=105.0,
            pnl=5.0,
            pnl_pct=5.0,
            contributing_agents=["Agent1"]
        )
        swarm.record_trade_outcome(trade)
    
    # Optimized status
    status = swarm.get_rl_status_display()
    assert status['status'] == 'optimized', "Status should be optimized"
    assert '✨' in status['label'], "Label should have sparkle emoji"
    assert status['color'] == '#10b981', "Color should be green"
    print("   ✓ Optimized status display correct")


def test_swarm_contributions():
    """Test agent contribution analysis"""
    print("\n✅ Test 6: Swarm Contributions")
    
    agents = ["Agent1", "Agent2", "Agent3"]
    swarm = SwarmAgentRL(agents, enable_rl=True)
    
    # Record trades
    trades = [
        TradeOutcome("BUY", 100, 110, 10, 10.0, ["Agent1", "Agent2"]),
        TradeOutcome("BUY", 100, 95, -5, -5.0, ["Agent1", "Agent3"]),
        TradeOutcome("SELL", 100, 90, 10, 10.0, ["Agent2", "Agent3"]),
    ]
    
    for trade in trades:
        swarm.record_trade_outcome(trade)
    
    contributions = swarm.get_agent_contributions()
    assert "Agent1" in contributions, "Agent1 should have contributions"
    assert contributions["Agent1"]["trades"] == 2, "Agent1 should have 2 trades"
    print("   ✓ Agent contributions calculated correctly")


def test_swarm_summary():
    """Test swarm summary"""
    print("\n✅ Test 7: Swarm Summary")
    
    agents = ["Agent1", "Agent2"]
    swarm = SwarmAgentRL(agents, enable_rl=True)
    
    # Empty summary
    summary = swarm.get_summary()
    assert summary['trade_count'] == 0, "Should have 0 trades"
    print("   ✓ Empty summary correct")
    
    # Add trades
    for i in range(3):
        trade = TradeOutcome(
            consensus_signal="BUY",
            entry_price=100.0,
            exit_price=105.0,
            pnl=5.0,
            pnl_pct=5.0,
            contributing_agents=["Agent1"]
        )
        swarm.record_trade_outcome(trade)
    
    summary = swarm.get_summary()
    assert summary['trade_count'] == 3, "Should have 3 trades"
    assert 'metrics' in summary, "Should have metrics"
    assert 'agent_weights' in summary, "Should have agent weights"
    print("   ✓ Summary with trades correct")


# ============================================================
# PHASE 4: MARKET INTEL AGENT RL TESTS
# ============================================================

def test_market_intel_initialization():
    """Test Market Intel Agent initialization"""
    print("\n✅ Test 8: Market Intel Initialization")
    
    # Test disabled
    agent_disabled = MarketIntelAgentRL(AnalysisType.CHART, enable_rl=False)
    assert agent_disabled.enable_rl == False, "enable_rl should be False"
    assert agent_disabled.rl_status == "inactive", "rl_status should be inactive"
    print("   ✓ Disabled mode works correctly")
    
    # Test enabled
    agent_enabled = MarketIntelAgentRL(AnalysisType.CHART, enable_rl=True, rl_training_analyses=10)
    assert agent_enabled.enable_rl == True, "enable_rl should be True"
    assert agent_enabled.rl_status == "training", "rl_status should be training"
    assert agent_enabled.agent_type == AnalysisType.CHART, "Type should be CHART"
    print("   ✓ Enabled mode works correctly")


def test_market_intel_record_analysis():
    """Test recording analysis results"""
    print("\n✅ Test 9: Market Intel Record Analysis")
    
    agent = MarketIntelAgentRL(AnalysisType.CHART, enable_rl=True)
    
    result = AnalysisResult(
        analysis_type=AnalysisType.CHART,
        signal="BUY",
        confidence=75.0,
        accuracy=0.0,
        reasoning="Bullish pattern detected"
    )
    
    agent.record_analysis(result)
    assert len(agent.analysis_history) == 1, "Should have 1 analysis"
    print("   ✓ Analysis recorded correctly")


def test_market_intel_record_outcome():
    """Test recording analysis outcomes"""
    print("\n✅ Test 10: Market Intel Record Outcome")
    
    agent = MarketIntelAgentRL(AnalysisType.SENTIMENT, enable_rl=True, rl_training_analyses=2)
    
    # Record outcomes
    for i in range(2):
        outcome = AnalysisOutcome(
            analysis_type=AnalysisType.SENTIMENT,
            signal="BUY",
            was_correct=True,
            accuracy_score=85.0
        )
        agent.record_outcome(outcome)
    
    assert len(agent.outcome_history) == 2, "Should have 2 outcomes"
    assert agent.rl_status == "optimized", "Should be optimized after 2 analyses"
    print("   ✓ Outcomes recorded and optimization triggered")


def test_market_intel_metrics():
    """Test market intel metrics calculation"""
    print("\n✅ Test 11: Market Intel Metrics")
    
    agent = MarketIntelAgentRL(AnalysisType.WHALE_ALERT, enable_rl=True)
    
    # Record outcomes
    outcomes = [
        AnalysisOutcome(AnalysisType.WHALE_ALERT, "ALERT", True, 90.0),
        AnalysisOutcome(AnalysisType.WHALE_ALERT, "ALERT", True, 85.0),
        AnalysisOutcome(AnalysisType.WHALE_ALERT, "ALERT", False, 40.0),
        AnalysisOutcome(AnalysisType.WHALE_ALERT, "ALERT", True, 95.0),
    ]
    
    for outcome in outcomes:
        agent.record_outcome(outcome)
    
    metrics = agent._calculate_metrics()
    assert 'accuracy' in metrics, "Should have accuracy"
    assert 'precision' in metrics, "Should have precision"
    assert 'recall' in metrics, "Should have recall"
    assert 'f1_score' in metrics, "Should have f1_score"
    assert metrics['accuracy'] == 75.0, "Accuracy should be 75% (3/4 correct)"
    print("   ✓ Metrics calculated correctly")
    print(f"   ✓ Accuracy: {metrics['accuracy']:.1f}%")


def test_market_intel_signal_accuracy():
    """Test signal accuracy analysis"""
    print("\n✅ Test 12: Market Intel Signal Accuracy")
    
    agent = MarketIntelAgentRL(AnalysisType.CHART, enable_rl=True)
    
    # Record mixed outcomes
    outcomes = [
        AnalysisOutcome(AnalysisType.CHART, "BUY", True, 90.0),
        AnalysisOutcome(AnalysisType.CHART, "BUY", True, 85.0),
        AnalysisOutcome(AnalysisType.CHART, "SELL", False, 40.0),
        AnalysisOutcome(AnalysisType.CHART, "SELL", False, 35.0),
    ]
    
    for outcome in outcomes:
        agent.record_outcome(outcome)
    
    signal_accuracy = agent.get_signal_accuracy()
    assert "BUY" in signal_accuracy, "Should have BUY accuracy"
    assert "SELL" in signal_accuracy, "Should have SELL accuracy"
    assert signal_accuracy["BUY"] == 100.0, "BUY should be 100% accurate"
    assert signal_accuracy["SELL"] == 0.0, "SELL should be 0% accurate"
    print("   ✓ Signal accuracy calculated correctly")


def test_market_intel_status_display():
    """Test market intel status display"""
    print("\n✅ Test 13: Market Intel Status Display")
    
    agent = MarketIntelAgentRL(AnalysisType.LIQUIDATION, enable_rl=True, rl_training_analyses=5)
    
    # Training status
    status = agent.get_rl_status_display()
    assert status['status'] == 'training', "Status should be training"
    assert '🔄' in status['label'], "Label should have refresh emoji"
    print("   ✓ Training status display correct")
    
    # Add outcomes
    for i in range(5):
        outcome = AnalysisOutcome(
            AnalysisType.LIQUIDATION,
            "ALERT",
            True,
            80.0
        )
        agent.record_outcome(outcome)
    
    # Optimized status
    status = agent.get_rl_status_display()
    assert status['status'] == 'optimized', "Status should be optimized"
    assert '✨' in status['label'], "Label should have sparkle emoji"
    print("   ✓ Optimized status display correct")


def test_market_intel_summary():
    """Test market intel summary"""
    print("\n✅ Test 14: Market Intel Summary")
    
    agent = MarketIntelAgentRL(AnalysisType.SENTIMENT, enable_rl=True)
    
    # Empty summary
    summary = agent.get_summary()
    assert summary['analysis_count'] == 0, "Should have 0 analyses"
    print("   ✓ Empty summary correct")
    
    # Add outcomes
    for i in range(3):
        outcome = AnalysisOutcome(
            AnalysisType.SENTIMENT,
            "BUY",
            True,
            85.0
        )
        agent.record_outcome(outcome)
    
    summary = agent.get_summary()
    assert summary['analysis_count'] == 3, "Should have 3 analyses"
    assert 'metrics' in summary, "Should have metrics"
    assert 'signal_accuracy' in summary, "Should have signal accuracy"
    print("   ✓ Summary with analyses correct")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 Phase 3 & 4 Test Suite")
    print("="*60)
    
    try:
        # Phase 3 Tests
        print("\n" + "="*60)
        print("PHASE 3: SWARM AGENT RL")
        print("="*60)
        test_swarm_initialization()
        test_swarm_consensus()
        test_swarm_weight_update()
        test_swarm_optimization_trigger()
        test_swarm_status_display()
        test_swarm_contributions()
        test_swarm_summary()
        
        # Phase 4 Tests
        print("\n" + "="*60)
        print("PHASE 4: MARKET INTEL AGENT RL")
        print("="*60)
        test_market_intel_initialization()
        test_market_intel_record_analysis()
        test_market_intel_record_outcome()
        test_market_intel_metrics()
        test_market_intel_signal_accuracy()
        test_market_intel_status_display()
        test_market_intel_summary()
        
        print("\n" + "="*60)
        print("✅ ALL 14 TESTS PASSED")
        print("="*60 + "\n")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n⚠️ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
