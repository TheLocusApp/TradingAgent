#!/usr/bin/env python3
"""
🌙 Phase 3 & 4 Integration Tests
Tests for Swarm Consensus and Market Intel Agents RL Integration
Built with love by Moon Dev 🚀
"""

import unittest
from pathlib import Path

from src.agents.swarm_agent_rl import SwarmAgentRL, TradeOutcome
from src.agents.swarm_rl_manager import SwarmRLManager, get_swarm_rl_manager

from src.agents.market_intel_agent_rl import MarketIntelAgentRL, AnalysisType, AnalysisResult
from src.agents.market_intel_rl_manager import MarketIntelRLManager, get_market_intel_rl_manager


class TestSwarmRLManager(unittest.TestCase):
    """Test Swarm RL Manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = SwarmRLManager()
        self.swarm_name = "test_swarm_consensus"
        self.agent_names = ["Agent1", "Agent2", "Agent3"]
    
    def tearDown(self):
        """Clean up after tests"""
        self.manager.clear_all()
    
    def test_manager_initialization(self):
        """Test manager initializes correctly"""
        self.assertIsNotNone(self.manager)
        self.assertTrue(self.manager.state_dir.exists())
    
    def test_get_or_create_agent_disabled(self):
        """Test get_or_create_agent with RL disabled"""
        agent = self.manager.get_or_create_agent(self.swarm_name, self.agent_names, enable_rl=False)
        self.assertIsNone(agent)
    
    def test_get_or_create_agent_enabled(self):
        """Test get_or_create_agent with RL enabled"""
        agent = self.manager.get_or_create_agent(self.swarm_name, self.agent_names, enable_rl=True)
        self.assertIsNotNone(agent)
        self.assertIsInstance(agent, SwarmAgentRL)
    
    def test_agent_persistence(self):
        """Test agent is returned from cache on second call"""
        agent1 = self.manager.get_or_create_agent(self.swarm_name, self.agent_names, enable_rl=True)
        agent2 = self.manager.get_or_create_agent(self.swarm_name, self.agent_names, enable_rl=True)
        self.assertIs(agent1, agent2)
    
    def test_record_trade(self):
        """Test recording a trade outcome"""
        trade_outcome = TradeOutcome(
            consensus_signal='BUY',
            entry_price=100.0,
            exit_price=110.0,
            pnl=1000.0,
            pnl_pct=10.0,
            contributing_agents=['Agent1', 'Agent2']
        )
        
        status = self.manager.record_trade(self.swarm_name, self.agent_names, trade_outcome)
        
        self.assertIsNotNone(status)
        self.assertEqual(status['status'], 'training')
        self.assertIn('label', status)
    
    def test_multiple_trades_tracking(self):
        """Test tracking multiple trades"""
        for i in range(5):
            trade_outcome = TradeOutcome(
                consensus_signal='BUY',
                entry_price=100.0,
                exit_price=110.0 + (i * 2),
                pnl=1000.0 + (i * 100),
                pnl_pct=10.0 + (i * 1),
                contributing_agents=['Agent1', 'Agent2']
            )
            self.manager.record_trade(self.swarm_name, self.agent_names, trade_outcome)
        
        status = self.manager.get_rl_status(self.swarm_name)
        self.assertIsNotNone(status)
        self.assertEqual(status['progress'], 10)  # 5/50 = 10%
    
    def test_get_weights(self):
        """Test getting agent weights"""
        # Record some trades first
        for i in range(3):
            trade_outcome = TradeOutcome(
                consensus_signal='BUY',
                entry_price=100.0,
                exit_price=110.0,
                pnl=1000.0,
                pnl_pct=10.0,
                contributing_agents=['Agent1', 'Agent2']
            )
            self.manager.record_trade(self.swarm_name, self.agent_names, trade_outcome)
        
        weights = self.manager.get_weights(self.swarm_name)
        self.assertIsNotNone(weights)
        self.assertIn('Agent1', weights)
        self.assertIn('Agent2', weights)
        self.assertIn('Agent3', weights)
    
    def test_clear_swarm(self):
        """Test clearing a specific swarm"""
        trade_outcome = TradeOutcome(
            consensus_signal='BUY',
            entry_price=100.0,
            exit_price=110.0,
            pnl=1000.0,
            pnl_pct=10.0,
            contributing_agents=['Agent1', 'Agent2']
        )
        self.manager.record_trade(self.swarm_name, self.agent_names, trade_outcome)
        
        self.manager.clear_swarm(self.swarm_name)
        status = self.manager.get_rl_status(self.swarm_name)
        self.assertIsNone(status)


class TestMarketIntelRLManager(unittest.TestCase):
    """Test Market Intel RL Manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = MarketIntelRLManager()
        self.agent_name = "test_chart_analyzer"
        self.analysis_type = AnalysisType.CHART
    
    def tearDown(self):
        """Clean up after tests"""
        self.manager.clear_all()
    
    def test_manager_initialization(self):
        """Test manager initializes correctly"""
        self.assertIsNotNone(self.manager)
        self.assertTrue(self.manager.state_dir.exists())
    
    def test_get_or_create_agent_disabled(self):
        """Test get_or_create_agent with RL disabled"""
        agent = self.manager.get_or_create_agent(self.agent_name, self.analysis_type, enable_rl=False)
        self.assertIsNone(agent)
    
    def test_get_or_create_agent_enabled(self):
        """Test get_or_create_agent with RL enabled"""
        agent = self.manager.get_or_create_agent(self.agent_name, self.analysis_type, enable_rl=True)
        self.assertIsNotNone(agent)
        self.assertIsInstance(agent, MarketIntelAgentRL)
        self.manager.clear_all()
    
    def test_agent_persistence(self):
        """Test agent is returned from cache on second call"""
        agent1 = self.manager.get_or_create_agent(self.agent_name, self.analysis_type, enable_rl=True)
        agent2 = self.manager.get_or_create_agent(self.agent_name, self.analysis_type, enable_rl=True)
        self.assertIs(agent1, agent2)
    
    def test_record_analysis(self):
        """Test recording an analysis result"""
        analysis_result = AnalysisResult(
            analysis_type=AnalysisType.CHART,
            signal='BUY',
            confidence=0.85,
            accuracy=0.0,
            reasoning='Strong bullish divergence detected'
        )
        
        status = self.manager.record_analysis(self.agent_name, self.analysis_type, analysis_result)
        
        self.assertIsNotNone(status)
        self.assertEqual(status['status'], 'training')
        self.assertIn('label', status)
    
    def test_multiple_analyses_tracking(self):
        """Test tracking multiple analyses"""
        for i in range(5):
            analysis_result = AnalysisResult(
                analysis_type=AnalysisType.CHART,
                signal='BUY' if i % 2 == 0 else 'SELL',
                confidence=0.75 + (i * 0.02),
                accuracy=0.0,
                reasoning=f'Analysis {i}'
            )
            self.manager.record_analysis(self.agent_name, self.analysis_type, analysis_result)
        
        status = self.manager.get_rl_status(self.agent_name)
        self.assertIsNotNone(status)
        self.assertEqual(status['progress'], 10)  # 5/50 = 10%
    
    def test_record_outcome(self):
        """Test recording an outcome"""
        # Record an analysis first
        analysis_result = AnalysisResult(
            analysis_type=AnalysisType.CHART,
            signal='BUY',
            confidence=0.85,
            accuracy=0.0,
            reasoning='Strong bullish divergence'
        )
        self.manager.record_analysis(self.agent_name, self.analysis_type, analysis_result)
        
        # Record outcome
        status = self.manager.record_outcome(self.agent_name, outcome=True, confidence=0.85)
        
        self.assertIsNotNone(status)
        self.assertIn('status', status)
    
    def test_get_metrics(self):
        """Test getting performance metrics"""
        # Record some analyses
        for i in range(3):
            analysis_result = AnalysisResult(
                analysis_type=AnalysisType.CHART,
                signal='BUY',
                confidence=0.85,
                accuracy=0.0,
                reasoning=f'Analysis {i}'
            )
            self.manager.record_analysis(self.agent_name, self.analysis_type, analysis_result)
        
        metrics = self.manager.get_metrics(self.agent_name)
        self.assertIsNotNone(metrics)
        self.assertIn('accuracy', metrics)
        self.assertIn('precision', metrics)
    
    def test_get_suggestions(self):
        """Test getting optimization suggestions"""
        # Record some analyses
        for i in range(5):
            analysis_result = AnalysisResult(
                analysis_type=AnalysisType.CHART,
                signal='BUY' if i % 2 == 0 else 'SELL',
                confidence=0.75,
                accuracy=0.0,
                reasoning=f'Analysis {i}'
            )
            self.manager.record_analysis(self.agent_name, self.analysis_type, analysis_result)
        
        suggestions = self.manager.get_suggestions(self.agent_name)
        self.assertIsNotNone(suggestions)
        self.assertIsInstance(suggestions, str)


class TestPhase3Integration(unittest.TestCase):
    """Test Phase 3 Integration (Swarm)"""
    
    def test_swarm_rl_manager_singleton(self):
        """Test Swarm RL Manager singleton pattern"""
        manager1 = get_swarm_rl_manager()
        manager2 = get_swarm_rl_manager()
        self.assertIs(manager1, manager2)
    
    def test_swarm_weight_optimization(self):
        """Test swarm agent weight optimization"""
        manager = SwarmRLManager()
        swarm_name = "test_swarm"
        agent_names = ["Agent1", "Agent2", "Agent3"]
        
        # Record trades with different outcomes
        for i in range(10):
            trade_outcome = TradeOutcome(
                consensus_signal='BUY',
                entry_price=100.0,
                exit_price=110.0 + (i * 0.5),
                pnl=1000.0 + (i * 50),
                pnl_pct=10.0 + (i * 0.5),
                contributing_agents=['Agent1', 'Agent2']
            )
            manager.record_trade(swarm_name, agent_names, trade_outcome)
        
        weights = manager.get_weights(swarm_name)
        
        # Verify weights sum to 1.0
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=2)
        
        manager.clear_all()
    
    def test_swarm_optimization_trigger(self):
        """Test swarm optimization triggers after 50 trades"""
        manager = SwarmRLManager()
        swarm_name = "test_swarm"
        agent_names = ["Agent1", "Agent2", "Agent3"]
        
        # Record 50 trades
        for i in range(50):
            trade_outcome = TradeOutcome(
                consensus_signal='BUY',
                entry_price=100.0,
                exit_price=110.0,
                pnl=1000.0,
                pnl_pct=10.0,
                contributing_agents=['Agent1', 'Agent2']
            )
            manager.record_trade(swarm_name, agent_names, trade_outcome)
        
        status = manager.get_rl_status(swarm_name)
        self.assertEqual(status['status'], 'optimized')
        
        manager.clear_all()


class TestPhase4Integration(unittest.TestCase):
    """Test Phase 4 Integration (Market Intel)"""
    
    def test_market_intel_rl_manager_singleton(self):
        """Test Market Intel RL Manager singleton pattern"""
        manager1 = get_market_intel_rl_manager()
        manager2 = get_market_intel_rl_manager()
        self.assertIs(manager1, manager2)
    
    def test_market_intel_accuracy_tracking(self):
        """Test market intel accuracy tracking"""
        manager = MarketIntelRLManager()
        agent_name = "test_analyzer"
        
        # Record analyses with outcomes
        for i in range(10):
            analysis_result = AnalysisResult(
                analysis_type=AnalysisType.CHART,
                signal='BUY' if i % 2 == 0 else 'SELL',
                confidence=0.85,
                accuracy=0.0,
                reasoning=f'Analysis {i}'
            )
            manager.record_analysis(agent_name, AnalysisType.CHART, analysis_result)
            
            # Record outcome (correct if i is even)
            manager.record_outcome(agent_name, outcome=(i % 2 == 0), confidence=0.85)
        
        metrics = manager.get_metrics(agent_name)
        
        # Verify metrics exist
        self.assertIn('accuracy', metrics)
        self.assertIn('precision', metrics)
        self.assertIn('recall', metrics)
        
        manager.clear_all()
    
    def test_market_intel_optimization_trigger(self):
        """Test market intel optimization triggers after 50 analyses"""
        manager = MarketIntelRLManager()
        agent_name = "test_analyzer"
        
        # Record 50 analyses
        for i in range(50):
            analysis_result = AnalysisResult(
                analysis_type=AnalysisType.CHART,
                signal='BUY',
                confidence=0.85,
                accuracy=0.0,
                reasoning=f'Analysis {i}'
            )
            manager.record_analysis(agent_name, AnalysisType.CHART, analysis_result)
        
        status = manager.get_rl_status(agent_name)
        self.assertEqual(status['status'], 'optimized')
        
        manager.clear_all()
    
    def test_multiple_analysis_types(self):
        """Test multiple analysis types"""
        manager = MarketIntelRLManager()
        
        analysis_types = [
            ("chart_analyzer", AnalysisType.CHART),
            ("sentiment_analyzer", AnalysisType.SENTIMENT)
        ]
        
        for agent_name, analysis_type in analysis_types:
            analysis_result = AnalysisResult(
                analysis_type=analysis_type,
                signal='BUY',
                confidence=0.85,
                accuracy=0.0,
                reasoning='Test analysis'
            )
            manager.record_analysis(agent_name, analysis_type, analysis_result)
        
        statuses = manager.get_all_statuses()
        self.assertEqual(len(statuses), 3)
        
        manager.clear_all()


if __name__ == '__main__':
    unittest.main()
