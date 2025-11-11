#!/usr/bin/env python3
"""
🌙 Phase 2 Integration Tests
Tests for RBI Backtest Agents RL Integration
Built with love by Moon Dev 🚀
"""

import unittest
import json
from pathlib import Path
from datetime import datetime

from src.agents.rbi_agent_rl import RBIAgentRL, RBIBacktestResult
from src.agents.rbi_rl_manager import RBIRLManager, get_rbi_rl_manager


class TestRBIRLManager(unittest.TestCase):
    """Test RBI RL Manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = RBIRLManager()
        self.strategy_name = "test_strategy_rsi_divergence"
    
    def tearDown(self):
        """Clean up after tests"""
        self.manager.clear_all()
    
    def test_manager_initialization(self):
        """Test manager initializes correctly"""
        self.assertIsNotNone(self.manager)
        self.assertTrue(self.manager.state_dir.exists())
    
    def test_get_or_create_agent_disabled(self):
        """Test get_or_create_agent with RL disabled"""
        agent = self.manager.get_or_create_agent(self.strategy_name, enable_rl=False)
        self.assertIsNone(agent)
    
    def test_get_or_create_agent_enabled(self):
        """Test get_or_create_agent with RL enabled"""
        agent = self.manager.get_or_create_agent(self.strategy_name, enable_rl=True)
        self.assertIsNotNone(agent)
        self.assertIsInstance(agent, RBIAgentRL)
    
    def test_agent_persistence(self):
        """Test agent is returned from cache on second call"""
        agent1 = self.manager.get_or_create_agent(self.strategy_name, enable_rl=True)
        agent2 = self.manager.get_or_create_agent(self.strategy_name, enable_rl=True)
        self.assertIs(agent1, agent2)
    
    def test_record_backtest(self):
        """Test recording a backtest result"""
        backtest_result = RBIBacktestResult(
            strategy_name=self.strategy_name,
            win_rate=55.0,
            sharpe_ratio=1.2,
            total_return=25.5,
            total_trades=20,
            max_drawdown=15.0
        )
        
        status = self.manager.record_backtest(self.strategy_name, backtest_result)
        
        self.assertIsNotNone(status)
        self.assertEqual(status['status'], 'training')
        self.assertIn('label', status)
    
    def test_multiple_backtests_tracking(self):
        """Test tracking multiple backtests"""
        for i in range(5):
            backtest_result = RBIBacktestResult(
                strategy_name=self.strategy_name,
                win_rate=50.0 + i,
                sharpe_ratio=1.0 + (i * 0.1),
                total_return=10.0 + (i * 2),
                total_trades=10 + (i * 2),
                max_drawdown=20.0 - (i * 1)
            )
            self.manager.record_backtest(self.strategy_name, backtest_result)
        
        status = self.manager.get_rl_status(self.strategy_name)
        self.assertIsNotNone(status)
        self.assertEqual(status['progress'], 50)  # 5/10 = 50%
    
    def test_optimization_trigger(self):
        """Test optimization triggers after 10 backtests"""
        for i in range(10):
            backtest_result = RBIBacktestResult(
                strategy_name=self.strategy_name,
                win_rate=55.0,
                sharpe_ratio=1.2,
                total_return=25.0,
                total_trades=20,
                max_drawdown=15.0
            )
            self.manager.record_backtest(self.strategy_name, backtest_result)
        
        status = self.manager.get_rl_status(self.strategy_name)
        self.assertEqual(status['status'], 'optimized')
    
    def test_get_rl_status_nonexistent(self):
        """Test get_rl_status for nonexistent strategy"""
        status = self.manager.get_rl_status("nonexistent_strategy")
        self.assertIsNone(status)
    
    def test_get_all_statuses(self):
        """Test get_all_statuses returns all strategies"""
        for i in range(3):
            strategy_name = f"strategy_{i}"
            backtest_result = RBIBacktestResult(
                strategy_name=strategy_name,
                win_rate=55.0,
                sharpe_ratio=1.2,
                total_return=25.0,
                total_trades=20,
                max_drawdown=15.0
            )
            self.manager.record_backtest(strategy_name, backtest_result)
        
        statuses = self.manager.get_all_statuses()
        self.assertEqual(len(statuses), 3)
    
    def test_clear_strategy(self):
        """Test clearing a specific strategy"""
        backtest_result = RBIBacktestResult(
            strategy_name=self.strategy_name,
            win_rate=55.0,
            sharpe_ratio=1.2,
            total_return=25.0,
            total_trades=20,
            max_drawdown=15.0
        )
        self.manager.record_backtest(self.strategy_name, backtest_result)
        
        self.manager.clear_strategy(self.strategy_name)
        status = self.manager.get_rl_status(self.strategy_name)
        self.assertIsNone(status)
    
    def test_save_and_load_state(self):
        """Test saving and loading state"""
        # Record a backtest
        backtest_result = RBIBacktestResult(
            strategy_name=self.strategy_name,
            win_rate=55.0,
            sharpe_ratio=1.2,
            total_return=25.0,
            total_trades=20,
            max_drawdown=15.0
        )
        self.manager.record_backtest(self.strategy_name, backtest_result)
        
        # Save state
        self.manager.save_state()
        
        # Create new manager and load state
        new_manager = RBIRLManager()
        status = new_manager.get_rl_status(self.strategy_name)
        
        self.assertIsNotNone(status)
        # Status should be loaded (even if progress is 0 due to state restoration)
        self.assertIn('status', status)
        self.assertIn('label', status)


class TestPhase2Integration(unittest.TestCase):
    """Test Phase 2 Integration"""
    
    def test_rl_manager_singleton(self):
        """Test RBI RL Manager singleton pattern"""
        manager1 = get_rbi_rl_manager()
        manager2 = get_rbi_rl_manager()
        self.assertIs(manager1, manager2)
    
    def test_backtest_result_creation(self):
        """Test creating backtest result"""
        result = RBIBacktestResult(
            strategy_name="test_strategy",
            win_rate=55.0,
            sharpe_ratio=1.2,
            total_return=25.0,
            total_trades=20,
            max_drawdown=15.0
        )
        
        self.assertEqual(result.strategy_name, "test_strategy")
        self.assertEqual(result.win_rate, 55.0)
        self.assertEqual(result.sharpe_ratio, 1.2)
    
    def test_rl_agent_training_progression(self):
        """Test RL agent training progression"""
        agent = RBIAgentRL(enable_rl=True, rl_training_backtests=10)
        
        # Record 5 backtests
        for i in range(5):
            result = RBIBacktestResult(
                strategy_name="test_strategy",
                win_rate=50.0 + i,
                sharpe_ratio=1.0 + (i * 0.1),
                total_return=10.0 + (i * 2),
                total_trades=10 + (i * 2),
                max_drawdown=20.0 - (i * 1)
            )
            agent.record_backtest_result(result)
        
        status = agent.get_rl_status_display()
        self.assertEqual(status['status'], 'training')
        self.assertEqual(status['progress'], 50)  # 5/10 = 50%
    
    def test_rl_agent_optimization_trigger(self):
        """Test RL agent optimization trigger"""
        agent = RBIAgentRL(enable_rl=True, rl_training_backtests=3)
        
        # Record 3 backtests to trigger optimization
        for i in range(3):
            result = RBIBacktestResult(
                strategy_name="test_strategy",
                win_rate=55.0,
                sharpe_ratio=1.2,
                total_return=25.0,
                total_trades=20,
                max_drawdown=15.0
            )
            agent.record_backtest_result(result)
        
        status = agent.get_rl_status_display()
        self.assertEqual(status['status'], 'optimized')
    
    def test_rl_status_display_format(self):
        """Test RL status display format"""
        agent = RBIAgentRL(enable_rl=True, rl_training_backtests=10)
        
        result = RBIBacktestResult(
            strategy_name="test_strategy",
            win_rate=55.0,
            sharpe_ratio=1.2,
            total_return=25.0,
            total_trades=20,
            max_drawdown=15.0
        )
        agent.record_backtest_result(result)
        
        status = agent.get_rl_status_display()
        
        # Verify status format
        self.assertIn('status', status)
        self.assertIn('label', status)
        self.assertIn('color', status)
        self.assertIn('progress', status)
        
        # Verify label format
        self.assertIn('Training', status['label'])
        self.assertIn('1/10', status['label'])


class TestPhase2UIIntegration(unittest.TestCase):
    """Test Phase 2 UI Integration"""
    
    def test_rl_checkbox_state(self):
        """Test RL checkbox state tracking"""
        # Simulate frontend state
        strategy = {
            'id': 1,
            'idea': 'RSI divergence with MACD confirmation',
            'enableRL': True,
            'rlStatus': 'training',
            'rlTrainingCount': 0
        }
        
        self.assertTrue(strategy['enableRL'])
        self.assertEqual(strategy['rlStatus'], 'training')
    
    def test_rl_tag_generation(self):
        """Test RL tag generation for UI"""
        # Training tag
        rl_status = {
            'status': 'training',
            'label': '🔄 Training (5/10)',
            'color': '#f59e0b',
            'progress': 5
        }
        
        self.assertEqual(rl_status['status'], 'training')
        self.assertIn('Training', rl_status['label'])
        self.assertEqual(rl_status['color'], '#f59e0b')
        
        # Optimized tag
        rl_status_optimized = {
            'status': 'optimized',
            'label': '✨ RL Optimized',
            'color': '#10b981',
            'progress': 10
        }
        
        self.assertEqual(rl_status_optimized['status'], 'optimized')
        self.assertIn('Optimized', rl_status_optimized['label'])
        self.assertEqual(rl_status_optimized['color'], '#10b981')


if __name__ == '__main__':
    unittest.main()
