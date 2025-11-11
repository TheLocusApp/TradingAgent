#!/usr/bin/env python3
"""
🌙 Market Intel RL Manager
Manages persistent RL state for Market Intel agents
Built with love by Moon Dev 🚀
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from termcolor import cprint

from src.agents.market_intel_agent_rl import MarketIntelAgentRL, AnalysisType, AnalysisResult


class MarketIntelRLManager:
    """Manages RL optimization state for Market Intel agents"""
    
    def __init__(self):
        """Initialize Market Intel RL Manager"""
        self.state_dir = Path('data/market_intel_rl_state')
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.agents: Dict[str, MarketIntelAgentRL] = {}
        self.state_file = self.state_dir / 'rl_state.json'
        self.load_state()
        cprint("✅ Market Intel RL Manager initialized", "green")
    
    def get_or_create_agent(self, agent_name: str, analysis_type: AnalysisType, enable_rl: bool = False) -> Optional[MarketIntelAgentRL]:
        """
        Get or create an RL agent for market intel
        
        Args:
            agent_name: Name of the agent
            analysis_type: Type of analysis (CHART, SENTIMENT, WHALE_ALERT, LIQUIDATION)
            enable_rl: Whether to enable RL optimization
            
        Returns:
            MarketIntelAgentRL instance or None if RL disabled
        """
        if not enable_rl:
            return None
        
        # Check if agent already exists
        if agent_name in self.agents:
            return self.agents[agent_name]
        
        # Create new agent
        agent = MarketIntelAgentRL(agent_type=analysis_type, enable_rl=True, rl_training_analyses=50)
        self.agents[agent_name] = agent
        
        cprint(f"✅ Created RL agent for: {agent_name} ({analysis_type.name})", "green")
        return agent
    
    def record_analysis(self, agent_name: str, analysis_type: AnalysisType, analysis_result: AnalysisResult) -> Dict:
        """
        Record an analysis result with RL optimization
        
        Args:
            agent_name: Name of the agent
            analysis_type: Type of analysis
            analysis_result: Analysis result to record
            
        Returns:
            RL status dictionary
        """
        # Get or create agent
        agent = self.get_or_create_agent(agent_name, analysis_type, enable_rl=True)
        
        if not agent:
            return None
        
        # Record the analysis
        agent.record_analysis(analysis_result)
        
        # Get status
        status = agent.get_rl_status_display()
        
        # Save state
        self.save_state()
        
        return status
    
    def record_outcome(self, agent_name: str, outcome: bool, confidence: float = 0.5):
        """
        Record an outcome for a previous analysis
        
        Args:
            agent_name: Name of the agent
            outcome: Whether the analysis was correct
            confidence: Confidence level of the analysis
        """
        if agent_name not in self.agents:
            return None
        
        agent = self.agents[agent_name]
        agent.record_outcome(outcome, confidence)
        
        # Save state
        self.save_state()
        
        return agent.get_rl_status_display()
    
    def get_rl_status(self, agent_name: str) -> Optional[Dict]:
        """
        Get RL status for an agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            RL status dictionary or None
        """
        if agent_name not in self.agents:
            return None
        
        agent = self.agents[agent_name]
        return agent.get_rl_status_display()
    
    def get_metrics(self, agent_name: str) -> Optional[Dict]:
        """
        Get performance metrics for an agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Metrics dictionary or None
        """
        if agent_name not in self.agents:
            return None
        
        agent = self.agents[agent_name]
        return agent.get_metrics()
    
    def get_suggestions(self, agent_name: str) -> Optional[str]:
        """
        Get optimization suggestions for an agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Suggestions string or None
        """
        if agent_name not in self.agents:
            return None
        
        agent = self.agents[agent_name]
        return agent.get_optimization_suggestions()
    
    def get_all_statuses(self) -> Dict[str, Dict]:
        """Get RL status for all agents"""
        result = {}
        for agent_name, agent in self.agents.items():
            result[agent_name] = agent.get_rl_status_display()
        return result
    
    def save_state(self):
        """Save RL state to file"""
        try:
            state_data = {}
            for agent_name, agent in self.agents.items():
                state_data[agent_name] = agent.get_summary()
            
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            cprint(f"💾 Saved RL state for {len(self.agents)} agents", "blue")
        except Exception as e:
            cprint(f"⚠️ Error saving RL state: {e}", "yellow")
    
    def load_state(self):
        """Load RL state from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)
                
                if isinstance(state_data, dict):
                    for agent_name, summary in state_data.items():
                        try:
                            # Extract analysis type from summary
                            analysis_type_str = summary.get('analysis_type', 'CHART')
                            analysis_type = AnalysisType[analysis_type_str]
                            
                            # Create new agent
                            agent = MarketIntelAgentRL(analysis_type=analysis_type, enable_rl=True, rl_training_analyses=50)
                            
                            # Restore state from summary if available
                            if isinstance(summary, dict):
                                if 'analyses' in summary:
                                    agent.analyses = summary.get('analyses', [])
                                if 'rl_status' in summary:
                                    agent.rl_status = summary.get('rl_status', 'training')
                                if 'metrics' in summary:
                                    agent.metrics = summary.get('metrics', {})
                            
                            self.agents[agent_name] = agent
                        except Exception as e:
                            cprint(f"⚠️ Error loading agent {agent_name}: {e}", "yellow")
                
                if len(self.agents) > 0:
                    cprint(f"✅ Loaded RL state for {len(self.agents)} agents", "green")
        except Exception as e:
            cprint(f"⚠️ Error loading RL state: {e}", "yellow")
    
    def clear_agent(self, agent_name: str):
        """Clear RL state for an agent"""
        if agent_name in self.agents:
            del self.agents[agent_name]
            self.save_state()
            cprint(f"🗑️ Cleared RL state for: {agent_name}", "yellow")
    
    def clear_all(self):
        """Clear all RL state"""
        self.agents.clear()
        self.save_state()
        cprint(f"🗑️ Cleared all RL state", "yellow")


# Global instances by type
_market_intel_rl_managers = {}


def get_market_intel_rl_manager(analysis_type: str = "general") -> MarketIntelRLManager:
    """Get or create a Market Intel RL Manager instance"""
    global _market_intel_rl_managers
    if analysis_type not in _market_intel_rl_managers:
        _market_intel_rl_managers[analysis_type] = MarketIntelRLManager()
    return _market_intel_rl_managers[analysis_type]
