#!/usr/bin/env python3
"""
🌙 Swarm Agent with RL Optimization
Learns optimal agent voting weights via RL
Built with love by Moon Dev 🚀
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from termcolor import cprint
from dataclasses import dataclass, field


@dataclass
class AgentDecision:
    """Individual agent decision"""
    agent_name: str
    signal: str  # BUY, SELL, HOLD
    confidence: float
    reasoning: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ConsensusResult:
    """Consensus decision result"""
    consensus_signal: str
    confidence: float
    contributing_agents: List[str]
    weights_used: Dict[str, float]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TradeOutcome:
    """Trade outcome for weight learning"""
    consensus_signal: str
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    contributing_agents: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class SwarmAgentRL:
    """Swarm consensus with RL-optimized voting weights"""
    
    def __init__(self, agent_names: List[str], enable_rl: bool = False, rl_training_trades: int = 50):
        """
        Initialize Swarm Agent with RL capabilities
        
        Args:
            agent_names: List of agent names in swarm
            enable_rl: Enable RL weight optimization
            rl_training_trades: Number of trades before optimization
        """
        self.agent_names = agent_names
        self.enable_rl = enable_rl
        self.rl_training_trades = rl_training_trades
        
        # Initialize equal weights
        self.agent_weights = {agent: 1.0 for agent in agent_names}
        self._normalize_weights()
        
        # RL tracking
        self.decision_history: List[ConsensusResult] = []
        self.trade_outcomes: List[TradeOutcome] = []
        self.rl_status = "inactive"
        
        if enable_rl:
            self.rl_status = "training"
            cprint(f"\n🤖 Swarm Agent RL initialized", "cyan")
            cprint(f"   Agents: {len(agent_names)}", "cyan")
            cprint(f"   Status: TRAINING MODE", "yellow")
            cprint(f"   Will optimize after {rl_training_trades} trades", "yellow")
            cprint(f"   Initial weights: Equal (1/{len(agent_names)} each)", "cyan")
    
    def _normalize_weights(self):
        """Normalize weights to sum to 1.0"""
        total = sum(self.agent_weights.values())
        if total > 0:
            self.agent_weights = {k: v / total for k, v in self.agent_weights.items()}
    
    def record_decision(self, agent_name: str, signal: str, confidence: float, reasoning: str = ""):
        """Record individual agent decision"""
        if agent_name not in self.agent_weights:
            cprint(f"⚠️ Unknown agent: {agent_name}", "yellow")
            return
        
        decision = AgentDecision(
            agent_name=agent_name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )
        
        if self.enable_rl:
            # Store for consensus calculation
            pass
    
    def calculate_consensus(self, decisions: Dict[str, Tuple[str, float]]) -> ConsensusResult:
        """
        Calculate weighted consensus from agent decisions
        
        Args:
            decisions: Dict of {agent_name: (signal, confidence)}
        
        Returns:
            ConsensusResult with consensus signal and contributing agents
        """
        weighted_votes = {}
        contributing_agents = []
        
        for agent_name, (signal, confidence) in decisions.items():
            if agent_name not in self.agent_weights:
                continue
            
            weight = self.agent_weights[agent_name]
            weighted_vote = weight * (confidence / 100.0)
            
            if signal not in weighted_votes:
                weighted_votes[signal] = 0.0
            weighted_votes[signal] += weighted_vote
            
            if weighted_vote > 0:
                contributing_agents.append(agent_name)
        
        # Get consensus signal (highest weighted vote)
        if not weighted_votes:
            consensus_signal = "HOLD"
            confidence = 0.0
        else:
            consensus_signal = max(weighted_votes, key=weighted_votes.get)
            confidence = min(100.0, weighted_votes[consensus_signal] * 100.0)
        
        result = ConsensusResult(
            consensus_signal=consensus_signal,
            confidence=confidence,
            contributing_agents=contributing_agents,
            weights_used=dict(self.agent_weights)
        )
        
        if self.enable_rl:
            self.decision_history.append(result)
        
        return result
    
    def record_trade_outcome(self, trade: TradeOutcome):
        """Record trade outcome for weight learning"""
        if not self.enable_rl:
            return
        
        self.trade_outcomes.append(trade)
        
        cprint(f"\n📊 Trade #{len(self.trade_outcomes)} recorded", "cyan")
        cprint(f"   Signal: {trade.consensus_signal}", "cyan")
        cprint(f"   P&L: {trade.pnl_pct:.2f}%", "cyan")
        cprint(f"   Contributing Agents: {', '.join(trade.contributing_agents)}", "cyan")
        
        # Update weights based on outcome
        self._update_weights(trade)
        
        # Check if optimization should be triggered
        if len(self.trade_outcomes) >= self.rl_training_trades and self.rl_status == "training":
            cprint(f"\n✨ RL OPTIMIZATION TRIGGERED", "green", attrs=['bold'])
            cprint(f"   Completed {len(self.trade_outcomes)} trades - ready for optimization", "green")
            self._trigger_optimization()
    
    def _update_weights(self, trade: TradeOutcome):
        """Update agent weights based on trade outcome"""
        if not trade.contributing_agents:
            return
        
        # Reward good trades, penalize bad trades
        adjustment_factor = 1.0 + (trade.pnl_pct / 100.0) * 0.1  # 10% adjustment per 100% P&L
        adjustment_factor = max(0.5, min(1.5, adjustment_factor))  # Clamp between 0.5 and 1.5
        
        for agent in trade.contributing_agents:
            if agent in self.agent_weights:
                self.agent_weights[agent] *= adjustment_factor
        
        # Penalize agents not in consensus
        for agent in self.agent_names:
            if agent not in trade.contributing_agents:
                self.agent_weights[agent] *= 0.95  # 5% penalty
        
        # Normalize
        self._normalize_weights()
    
    def _trigger_optimization(self):
        """Trigger RL optimization"""
        cprint(f"\n🚀 Starting RL Optimization", "cyan", attrs=['bold'])
        cprint(f"   Trades analyzed: {len(self.trade_outcomes)}", "cyan")
        
        # Calculate metrics
        metrics = self._calculate_metrics()
        
        cprint(f"\n   📊 Performance Metrics:", "cyan")
        cprint(f"      Win Rate: {metrics['win_rate']:.1f}%", "cyan")
        cprint(f"      Avg P&L: {metrics['avg_pnl_pct']:.2f}%", "cyan")
        cprint(f"      Total P&L: {metrics['total_pnl_pct']:.2f}%", "cyan")
        cprint(f"      Sharpe Ratio: {metrics['sharpe_ratio']:.2f}", "cyan")
        
        # Analyze agent contributions
        cprint(f"\n   🤖 Agent Weights:", "cyan")
        for agent, weight in sorted(self.agent_weights.items(), key=lambda x: x[1], reverse=True):
            pct = weight * 100
            bar = "█" * int(pct / 5)
            cprint(f"      {agent}: {weight:.3f} ({pct:.1f}%) {bar}", "cyan")
        
        self.rl_status = "optimized"
        
        cprint(f"\n✅ RL Optimization Complete", "green", attrs=['bold'])
        cprint(f"   Agent weights have been optimized", "green")
        cprint(f"   Continuing with optimized weights...", "green")
    
    def _calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if not self.trade_outcomes:
            return {
                'win_rate': 0.0,
                'avg_pnl_pct': 0.0,
                'total_pnl_pct': 0.0,
                'sharpe_ratio': 0.0
            }
        
        pnl_list = [t.pnl_pct for t in self.trade_outcomes]
        wins = sum(1 for p in pnl_list if p > 0)
        win_rate = (wins / len(pnl_list)) * 100 if pnl_list else 0
        
        avg_pnl = sum(pnl_list) / len(pnl_list) if pnl_list else 0
        total_pnl = sum(pnl_list)
        
        # Calculate Sharpe ratio
        if len(pnl_list) > 1:
            variance = sum((p - avg_pnl) ** 2 for p in pnl_list) / len(pnl_list)
            std_dev = variance ** 0.5
            sharpe = (avg_pnl / std_dev) if std_dev > 0 else 0
        else:
            sharpe = 0.0
        
        return {
            'win_rate': win_rate,
            'avg_pnl_pct': avg_pnl,
            'total_pnl_pct': total_pnl,
            'sharpe_ratio': sharpe
        }
    
    def get_rl_status(self) -> str:
        """Get current RL status"""
        return self.rl_status
    
    def get_rl_status_display(self) -> Dict:
        """Get RL status for display in UI"""
        if not self.enable_rl:
            return {'status': 'disabled', 'label': 'RL Disabled', 'color': '#6b7280'}
        
        trade_count = len(self.trade_outcomes)
        
        if self.rl_status == "training":
            progress = min(100, int((trade_count / self.rl_training_trades) * 100))
            return {
                'status': 'training',
                'label': f'🔄 Training ({trade_count}/{self.rl_training_trades})',
                'color': '#f59e0b',
                'progress': progress
            }
        elif self.rl_status == "optimized":
            return {
                'status': 'optimized',
                'label': '✨ RL Optimized',
                'color': '#10b981'
            }
        else:
            return {'status': 'inactive', 'label': 'Inactive', 'color': '#6b7280'}
    
    def get_agent_contributions(self) -> Dict[str, Dict]:
        """Get agent contribution analysis"""
        contributions = {agent: {'trades': 0, 'wins': 0, 'pnl': 0.0} for agent in self.agent_names}
        
        for trade in self.trade_outcomes:
            for agent in trade.contributing_agents:
                if agent in contributions:
                    contributions[agent]['trades'] += 1
                    if trade.pnl_pct > 0:
                        contributions[agent]['wins'] += 1
                    contributions[agent]['pnl'] += trade.pnl_pct
        
        # Calculate win rates
        for agent in contributions:
            if contributions[agent]['trades'] > 0:
                contributions[agent]['win_rate'] = (contributions[agent]['wins'] / contributions[agent]['trades']) * 100
            else:
                contributions[agent]['win_rate'] = 0.0
        
        return contributions
    
    def get_summary(self) -> Dict:
        """Get summary of swarm RL optimization"""
        if not self.trade_outcomes:
            return {
                'status': self.rl_status,
                'trade_count': 0,
                'metrics': {},
                'agent_weights': dict(self.agent_weights),
                'contributions': {}
            }
        
        metrics = self._calculate_metrics()
        contributions = self.get_agent_contributions()
        
        return {
            'status': self.rl_status,
            'trade_count': len(self.trade_outcomes),
            'metrics': metrics,
            'agent_weights': dict(self.agent_weights),
            'contributions': contributions
        }
    
    def save_state(self, filepath: str):
        """Save swarm RL state to file"""
        state = {
            'rl_status': self.rl_status,
            'agent_names': self.agent_names,
            'agent_weights': self.agent_weights,
            'trade_count': len(self.trade_outcomes),
            'metrics': self._calculate_metrics(),
            'contributions': self.get_agent_contributions(),
            'timestamp': datetime.now().isoformat()
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        cprint(f"💾 Swarm RL state saved to {filepath}", "green")
    
    def load_state(self, filepath: str):
        """Load swarm RL state from file"""
        if not Path(filepath).exists():
            return
        
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.rl_status = state.get('rl_status', 'inactive')
            self.agent_weights = state.get('agent_weights', {agent: 1.0 for agent in self.agent_names})
            self._normalize_weights()
            
            cprint(f"📂 Swarm RL state loaded from {filepath}", "green")
            cprint(f"   Status: {self.rl_status}", "green")
            cprint(f"   Agents: {len(self.agent_names)}", "green")
        except Exception as e:
            cprint(f"⚠️ Error loading swarm RL state: {e}", "yellow")
