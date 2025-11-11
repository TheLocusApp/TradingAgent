#!/usr/bin/env python3
"""
🌙 RBI RL Manager
Manages persistent RL state for RBI backtest strategies
Built with love by Moon Dev 🚀
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from termcolor import cprint

from src.agents.rbi_agent_rl import RBIAgentRL, RBIBacktestResult


class RBIRLManager:
    """Manages RL optimization state for RBI backtesting strategies"""
    
    def __init__(self):
        """Initialize RBI RL Manager"""
        self.state_dir = Path('data/rbi_rl_state')
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.agents: Dict[str, RBIAgentRL] = {}
        self.state_file = self.state_dir / 'rl_state.json'
        self.load_state()
        cprint("✅ RBI RL Manager initialized", "green")
    
    def get_or_create_agent(self, strategy_name: str, enable_rl: bool = False) -> Optional[RBIAgentRL]:
        """
        Get or create an RL agent for a strategy
        
        Args:
            strategy_name: Name of the strategy
            enable_rl: Whether to enable RL optimization
            
        Returns:
            RBIAgentRL instance or None if RL disabled
        """
        if not enable_rl:
            return None
        
        # Check if agent already exists
        if strategy_name in self.agents:
            return self.agents[strategy_name]
        
        # Create new agent
        agent = RBIAgentRL(enable_rl=True, rl_training_backtests=10)
        self.agents[strategy_name] = agent
        
        cprint(f"✅ Created RL agent for: {strategy_name}", "green")
        return agent
    
    def record_backtest(self, strategy_name: str, backtest_result: RBIBacktestResult) -> Dict:
        """
        Record a backtest result with RL optimization
        
        Args:
            strategy_name: Name of the strategy
            backtest_result: Backtest result to record
            
        Returns:
            RL status dictionary
        """
        # Get or create agent
        agent = self.get_or_create_agent(strategy_name, enable_rl=True)
        
        if not agent:
            return None
        
        # Record the result
        agent.record_backtest_result(backtest_result)
        
        # Get status
        status = agent.get_rl_status_display()
        
        # Save state
        self.save_state()
        
        return status
    
    def get_rl_status(self, strategy_name: str) -> Optional[Dict]:
        """
        Get RL status for a strategy
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            RL status dictionary or None
        """
        if strategy_name not in self.agents:
            return None
        
        agent = self.agents[strategy_name]
        return agent.get_rl_status_display()
    
    def get_all_statuses(self) -> Dict[str, Dict]:
        """Get RL status for all strategies"""
        result = {}
        for strategy_name, agent in self.agents.items():
            result[strategy_name] = agent.get_rl_status_display()
        return result
    
    def save_state(self):
        """Save RL state to file"""
        try:
            state_data = {}
            for strategy_name, agent in self.agents.items():
                state_data[strategy_name] = agent.get_summary()
            
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            cprint(f"💾 Saved RL state for {len(self.agents)} strategies", "blue")
        except Exception as e:
            cprint(f"⚠️ Error saving RL state: {e}", "yellow")
    
    def load_state(self):
        """Load RL state from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)
                
                if isinstance(state_data, dict):
                    for strategy_name, summary in state_data.items():
                        try:
                            # Create new agent
                            agent = RBIAgentRL(enable_rl=True, rl_training_backtests=10)
                            
                            # Restore state from summary if available
                            if isinstance(summary, dict):
                                # Restore backtest results
                                if 'backtest_results' in summary:
                                    agent.backtest_results = summary.get('backtest_results', [])
                                if 'rl_status' in summary:
                                    agent.rl_status = summary.get('rl_status', 'training')
                            
                            self.agents[strategy_name] = agent
                        except Exception as e:
                            cprint(f"⚠️ Error loading strategy {strategy_name}: {e}", "yellow")
                
                if len(self.agents) > 0:
                    cprint(f"✅ Loaded RL state for {len(self.agents)} strategies", "green")
        except Exception as e:
            cprint(f"⚠️ Error loading RL state: {e}", "yellow")
    
    def clear_strategy(self, strategy_name: str):
        """Clear RL state for a strategy"""
        if strategy_name in self.agents:
            del self.agents[strategy_name]
            self.save_state()
            cprint(f"🗑️ Cleared RL state for: {strategy_name}", "yellow")
    
    def clear_all(self):
        """Clear all RL state"""
        self.agents.clear()
        self.save_state()
        cprint(f"🗑️ Cleared all RL state", "yellow")


# Global instance
_rbi_rl_manager = None


def get_rbi_rl_manager() -> RBIRLManager:
    """Get or create the global RBI RL Manager instance"""
    global _rbi_rl_manager
    if _rbi_rl_manager is None:
        _rbi_rl_manager = RBIRLManager()
    return _rbi_rl_manager
