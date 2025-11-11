#!/usr/bin/env python3
"""
🌙 Swarm RL Manager
Manages persistent RL state for Swarm Consensus agents
Built with love by Moon Dev 🚀
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from termcolor import cprint

from src.agents.swarm_agent_rl import SwarmAgentRL, TradeOutcome


class SwarmRLManager:
    """Manages RL optimization state for Swarm agents"""
    
    def __init__(self):
        """Initialize Swarm RL Manager"""
        self.state_dir = Path('data/swarm_rl_state')
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.agents: Dict[str, SwarmAgentRL] = {}
        self.state_file = self.state_dir / 'rl_state.json'
        self.load_state()
        cprint("✅ Swarm RL Manager initialized", "green")
    
    def get_or_create_agent(self, swarm_name: str, agent_names: List[str], enable_rl: bool = False) -> Optional[SwarmAgentRL]:
        """
        Get or create an RL agent for a swarm
        
        Args:
            swarm_name: Name of the swarm
            agent_names: List of agent names in the swarm
            enable_rl: Whether to enable RL optimization
            
        Returns:
            SwarmAgentRL instance or None if RL disabled
        """
        if not enable_rl:
            return None
        
        # Check if agent already exists
        if swarm_name in self.agents:
            return self.agents[swarm_name]
        
        # Create new agent
        agent = SwarmAgentRL(agent_names=agent_names, enable_rl=True, rl_training_trades=50)
        self.agents[swarm_name] = agent
        
        cprint(f"✅ Created RL agent for swarm: {swarm_name}", "green")
        return agent
    
    def record_trade(self, swarm_name: str, agent_names: List[str], trade_outcome: TradeOutcome) -> Dict:
        """
        Record a trade outcome with RL optimization
        
        Args:
            swarm_name: Name of the swarm
            agent_names: List of agent names
            trade_outcome: Trade outcome to record
            
        Returns:
            RL status dictionary
        """
        # Get or create agent
        agent = self.get_or_create_agent(swarm_name, agent_names, enable_rl=True)
        
        if not agent:
            return None
        
        # Record the trade
        agent.record_trade_outcome(trade_outcome)
        
        # Get status
        status = agent.get_rl_status_display()
        
        # Save state
        self.save_state()
        
        return status
    
    def get_rl_status(self, swarm_name: str) -> Optional[Dict]:
        """
        Get RL status for a swarm
        
        Args:
            swarm_name: Name of the swarm
            
        Returns:
            RL status dictionary or None
        """
        if swarm_name not in self.agents:
            return None
        
        agent = self.agents[swarm_name]
        return agent.get_rl_status_display()
    
    def get_weights(self, swarm_name: str) -> Optional[Dict[str, float]]:
        """
        Get current agent weights for a swarm
        
        Args:
            swarm_name: Name of the swarm
            
        Returns:
            Dictionary of agent names to weights
        """
        if swarm_name not in self.agents:
            return None
        
        agent = self.agents[swarm_name]
        return agent.agent_weights
    
    def get_all_statuses(self) -> Dict[str, Dict]:
        """Get RL status for all swarms"""
        result = {}
        for swarm_name, agent in self.agents.items():
            result[swarm_name] = agent.get_rl_status_display()
        return result
    
    def save_state(self):
        """Save RL state to file"""
        try:
            state_data = {}
            for swarm_name, agent in self.agents.items():
                state_data[swarm_name] = agent.get_summary()
            
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            cprint(f"💾 Saved RL state for {len(self.agents)} swarms", "blue")
        except Exception as e:
            cprint(f"⚠️ Error saving RL state: {e}", "yellow")
    
    def load_state(self):
        """Load RL state from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)
                
                if isinstance(state_data, dict):
                    for swarm_name, summary in state_data.items():
                        try:
                            # Extract agent names from summary
                            agent_names = summary.get('agent_names', [])
                            
                            # Create new agent
                            agent = SwarmAgentRL(agent_names=agent_names, enable_rl=True, rl_training_trades=50)
                            
                            # Restore state from summary if available
                            if isinstance(summary, dict):
                                if 'trade_outcomes' in summary:
                                    agent.trade_outcomes = summary.get('trade_outcomes', [])
                                if 'rl_status' in summary:
                                    agent.rl_status = summary.get('rl_status', 'training')
                                if 'agent_weights' in summary:
                                    agent.agent_weights = summary.get('agent_weights', {})
                            
                            self.agents[swarm_name] = agent
                        except Exception as e:
                            cprint(f"⚠️ Error loading swarm {swarm_name}: {e}", "yellow")
                
                if len(self.agents) > 0:
                    cprint(f"✅ Loaded RL state for {len(self.agents)} swarms", "green")
        except Exception as e:
            cprint(f"⚠️ Error loading RL state: {e}", "yellow")
    
    def clear_swarm(self, swarm_name: str):
        """Clear RL state for a swarm"""
        if swarm_name in self.agents:
            del self.agents[swarm_name]
            self.save_state()
            cprint(f"🗑️ Cleared RL state for: {swarm_name}", "yellow")
    
    def clear_all(self):
        """Clear all RL state"""
        self.agents.clear()
        self.save_state()
        cprint(f"🗑️ Cleared all RL state", "yellow")


# Global instance
_swarm_rl_manager = None


def get_swarm_rl_manager() -> SwarmRLManager:
    """Get or create the global Swarm RL Manager instance"""
    global _swarm_rl_manager
    if _swarm_rl_manager is None:
        _swarm_rl_manager = SwarmRLManager()
    return _swarm_rl_manager
