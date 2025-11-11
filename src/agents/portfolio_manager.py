#!/usr/bin/env python3
"""
🏦 Portfolio Manager Agent
Dynamic capital allocation, risk management, and rebalancing
Built with love by Moon Dev 🚀
"""

import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from termcolor import cprint
import json
from pathlib import Path


class PortfolioManager:
    """
    Manages portfolio-level capital allocation and risk
    
    Features:
    - Kelly Criterion-based position sizing
    - Dynamic rebalancing based on Sharpe ratios
    - Portfolio-wide risk limits
    - Correlation-based diversification
    """
    
    def __init__(self, total_capital: float = 100000.0, max_portfolio_risk: float = 0.06):
        """
        Initialize portfolio manager
        
        Args:
            total_capital: Total portfolio capital
            max_portfolio_risk: Maximum portfolio drawdown allowed (default 6%)
        """
        self.total_capital = total_capital
        self.max_portfolio_risk = max_portfolio_risk
        self.max_agent_risk = 0.03  # Max 3% drawdown per agent
        self.max_daily_loss = 0.02  # Max 2% daily loss
        
        # Allocation tracking
        self.agent_allocations: Dict[str, float] = {}  # {agent_id: capital_allocated}
        self.agent_performance: Dict[str, Dict] = {}  # {agent_id: {sharpe, return, drawdown, trades}}
        self.rebalance_frequency = 7  # Rebalance every 7 days
        self.last_rebalance = datetime.now()
        
        # Risk tracking
        self.daily_pnl = 0.0
        self.daily_start_capital = total_capital
        self.peak_capital = total_capital
        self.current_drawdown = 0.0
        
        # State persistence
        self.state_file = Path(__file__).parent.parent / "data" / "portfolio_manager_state.json"
        self._load_state()
        
        cprint("✅ Portfolio Manager initialized", "green")
        cprint(f"   Total Capital: ${total_capital:,.2f}", "cyan")
        cprint(f"   Max Portfolio Risk: {max_portfolio_risk*100:.1f}%", "cyan")
    
    def _load_state(self):
        """Load saved state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.agent_allocations = state.get('agent_allocations', {})
                    self.agent_performance = state.get('agent_performance', {})
                    self.last_rebalance = datetime.fromisoformat(state.get('last_rebalance', datetime.now().isoformat()))
                    self.peak_capital = state.get('peak_capital', self.total_capital)
                    cprint(f"📊 Loaded portfolio state: {len(self.agent_allocations)} agents", "green")
            except Exception as e:
                cprint(f"⚠️ Error loading portfolio state: {e}", "yellow")
    
    def _save_state(self):
        """Save current state"""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            state = {
                'agent_allocations': self.agent_allocations,
                'agent_performance': self.agent_performance,
                'last_rebalance': self.last_rebalance.isoformat(),
                'peak_capital': self.peak_capital,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            cprint(f"⚠️ Error saving portfolio state: {e}", "yellow")
    
    def calculate_kelly_fraction(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Calculate Kelly Criterion optimal bet size
        
        Formula: f = (p*b - q) / b
        where:
            p = win probability
            q = loss probability (1-p)
            b = win/loss ratio
        
        Args:
            win_rate: Win rate (0-1)
            avg_win: Average win size
            avg_loss: Average loss size (positive number)
            
        Returns:
            Optimal fraction of capital to allocate (0-1)
        """
        if win_rate <= 0 or win_rate >= 1 or avg_win <= 0 or avg_loss <= 0:
            return 0.10  # Default 10% if invalid inputs
        
        p = win_rate
        q = 1 - win_rate
        b = avg_win / avg_loss  # Win/loss ratio
        
        kelly = (p * b - q) / b
        
        # Apply fractional Kelly (use 50% of full Kelly for safety)
        fractional_kelly = kelly * 0.5
        
        # Clamp between 5% and 30%
        return max(0.05, min(0.30, fractional_kelly))
    
    def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe ratio
        
        Args:
            returns: List of returns
            risk_free_rate: Annual risk-free rate (default 2%)
            
        Returns:
            Sharpe ratio
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        excess_returns = returns_array - (risk_free_rate / 252)  # Daily risk-free rate
        
        if np.std(excess_returns) == 0:
            return 0.0
        
        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)  # Annualized
        return sharpe
    
    def update_agent_performance(self, agent_id: str, stats: Dict):
        """
        Update agent performance metrics
        
        Args:
            agent_id: Agent identifier
            stats: Performance stats dict with keys: pnl_pct, win_rate, sharpe_ratio, max_drawdown, total_trades
        """
        self.agent_performance[agent_id] = {
            'return_pct': stats.get('pnl_pct', 0.0),
            'win_rate': stats.get('win_rate', 0.0),
            'sharpe_ratio': stats.get('sharpe_ratio', 0.0),
            'max_drawdown': stats.get('max_drawdown', 0.0),
            'total_trades': stats.get('total_trades', 0),
            'last_updated': datetime.now().isoformat()
        }
        self._save_state()
    
    def allocate_capital(self, agent_stats: Dict[str, Dict]) -> Dict[str, float]:
        """
        Allocate capital across agents using Kelly Criterion and Sharpe ratios
        
        Args:
            agent_stats: Dict of {agent_id: {pnl_pct, win_rate, sharpe_ratio, max_drawdown, total_trades}}
            
        Returns:
            Dict of {agent_id: allocated_capital}
        """
        allocations = {}
        
        # Filter agents with sufficient trades and positive Sharpe
        qualified_agents = {
            agent_id: stats for agent_id, stats in agent_stats.items()
            if stats.get('total_trades', 0) >= 10 and stats.get('sharpe_ratio', 0) > 0.5
        }
        
        if not qualified_agents:
            # Equal allocation if no qualified agents
            equal_allocation = self.total_capital / max(len(agent_stats), 1)
            return {agent_id: equal_allocation for agent_id in agent_stats.keys()}
        
        # Calculate Kelly fractions for each agent
        kelly_fractions = {}
        for agent_id, stats in qualified_agents.items():
            win_rate = stats.get('win_rate', 50.0) / 100.0
            # Estimate avg win/loss from Sharpe and return
            avg_return = stats.get('pnl_pct', 0.0) / max(stats.get('total_trades', 1), 1)
            avg_win = abs(avg_return) * 1.5 if avg_return > 0 else 1.0
            avg_loss = abs(avg_return) * 0.5 if avg_return > 0 else 1.0
            
            kelly = self.calculate_kelly_fraction(win_rate, avg_win, avg_loss)
            kelly_fractions[agent_id] = kelly
        
        # Weight by Sharpe ratio (favor higher Sharpe agents)
        sharpe_weights = {}
        total_sharpe = sum(max(stats.get('sharpe_ratio', 0), 0.1) for stats in qualified_agents.values())
        
        for agent_id, stats in qualified_agents.items():
            sharpe = max(stats.get('sharpe_ratio', 0), 0.1)
            sharpe_weights[agent_id] = sharpe / total_sharpe
        
        # Combine Kelly and Sharpe weighting (70% Kelly, 30% Sharpe)
        for agent_id in qualified_agents.keys():
            kelly_allocation = kelly_fractions[agent_id] * self.total_capital
            sharpe_allocation = sharpe_weights[agent_id] * self.total_capital
            
            # Weighted average
            allocations[agent_id] = kelly_allocation * 0.7 + sharpe_allocation * 0.3
        
        # Normalize to total capital
        total_allocated = sum(allocations.values())
        if total_allocated > 0:
            scale_factor = self.total_capital / total_allocated
            allocations = {agent_id: alloc * scale_factor for agent_id, alloc in allocations.items()}
        
        # Apply minimum and maximum constraints
        for agent_id in allocations.keys():
            allocations[agent_id] = max(5000, min(allocations[agent_id], self.total_capital * 0.40))  # Min $5k, max 40%
        
        self.agent_allocations = allocations
        self._save_state()
        
        return allocations
    
    def should_rebalance(self) -> bool:
        """Check if it's time to rebalance"""
        days_since_rebalance = (datetime.now() - self.last_rebalance).days
        return days_since_rebalance >= self.rebalance_frequency
    
    def rebalance_portfolio(self, agent_stats: Dict[str, Dict]) -> Dict[str, float]:
        """
        Rebalance portfolio allocations
        
        Args:
            agent_stats: Current agent statistics
            
        Returns:
            New allocations
        """
        cprint("\n🔄 Rebalancing Portfolio...", "cyan")
        
        # Calculate new allocations
        new_allocations = self.allocate_capital(agent_stats)
        
        # Log changes
        for agent_id, new_alloc in new_allocations.items():
            old_alloc = self.agent_allocations.get(agent_id, 0)
            change = new_alloc - old_alloc
            change_pct = (change / old_alloc * 100) if old_alloc > 0 else 0
            
            if abs(change) > 1000:  # Only log significant changes
                cprint(f"  {agent_id}: ${old_alloc:,.0f} → ${new_alloc:,.0f} ({change_pct:+.1f}%)", "yellow")
        
        self.last_rebalance = datetime.now()
        self._save_state()
        
        return new_allocations
    
    def check_risk_limits(self, current_portfolio_value: float, agent_stats: Dict[str, Dict]) -> Dict[str, bool]:
        """
        Check if agents should be paused due to risk limits
        
        Args:
            current_portfolio_value: Current total portfolio value
            agent_stats: Current agent statistics
            
        Returns:
            Dict of {agent_id: should_pause}
        """
        pause_decisions = {}
        
        # Update portfolio metrics
        self.current_drawdown = (self.peak_capital - current_portfolio_value) / self.peak_capital
        if current_portfolio_value > self.peak_capital:
            self.peak_capital = current_portfolio_value
            self.current_drawdown = 0.0
        
        # Check portfolio-wide drawdown
        if self.current_drawdown >= self.max_portfolio_risk:
            cprint(f"\n🚨 PORTFOLIO RISK LIMIT HIT: {self.current_drawdown*100:.2f}% drawdown", "red")
            cprint(f"   Pausing ALL agents until drawdown recovers", "red")
            return {agent_id: True for agent_id in agent_stats.keys()}
        
        # Check daily loss limit
        daily_loss_pct = (self.daily_start_capital - current_portfolio_value) / self.daily_start_capital
        if daily_loss_pct >= self.max_daily_loss:
            cprint(f"\n🚨 DAILY LOSS LIMIT HIT: {daily_loss_pct*100:.2f}%", "red")
            cprint(f"   Pausing ALL agents for rest of day", "red")
            return {agent_id: True for agent_id in agent_stats.keys()}
        
        # Check individual agent drawdowns
        for agent_id, stats in agent_stats.items():
            agent_dd = abs(stats.get('max_drawdown', 0))
            if agent_dd >= self.max_agent_risk:
                pause_decisions[agent_id] = True
                cprint(f"⚠️ Agent {agent_id} paused: {agent_dd*100:.2f}% drawdown", "yellow")
            else:
                pause_decisions[agent_id] = False
        
        return pause_decisions
    
    def get_portfolio_summary(self, agent_stats: Dict[str, Dict]) -> Dict:
        """
        Get portfolio-level summary statistics
        
        Args:
            agent_stats: Current agent statistics
            
        Returns:
            Portfolio summary dict
        """
        total_value = sum(stats.get('balance', 0) for stats in agent_stats.values())
        total_pnl = total_value - self.total_capital
        total_pnl_pct = (total_pnl / self.total_capital) * 100
        
        # Calculate portfolio Sharpe (weighted average)
        portfolio_sharpe = 0.0
        total_capital_allocated = sum(self.agent_allocations.values())
        
        if total_capital_allocated > 0:
            for agent_id, stats in agent_stats.items():
                allocation = self.agent_allocations.get(agent_id, 0)
                weight = allocation / total_capital_allocated
                agent_sharpe = stats.get('sharpe_ratio', 0)
                portfolio_sharpe += weight * agent_sharpe
        
        # Find best/worst performers
        best_agent = max(agent_stats.items(), key=lambda x: x[1].get('pnl_pct', 0), default=(None, {}))
        worst_agent = min(agent_stats.items(), key=lambda x: x[1].get('pnl_pct', 0), default=(None, {}))
        
        return {
            'total_capital': self.total_capital,
            'current_value': total_value,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'portfolio_sharpe': portfolio_sharpe,
            'current_drawdown': self.current_drawdown,
            'peak_capital': self.peak_capital,
            'num_agents': len(agent_stats),
            'num_active_agents': sum(1 for stats in agent_stats.values() if stats.get('running', False)),
            'best_performer': {
                'agent_id': best_agent[0],
                'pnl_pct': best_agent[1].get('pnl_pct', 0)
            } if best_agent[0] else None,
            'worst_performer': {
                'agent_id': worst_agent[0],
                'pnl_pct': worst_agent[1].get('pnl_pct', 0)
            } if worst_agent[0] else None,
            'allocations': self.agent_allocations,
            'days_until_rebalance': self.rebalance_frequency - (datetime.now() - self.last_rebalance).days
        }


# Global portfolio manager instance
_portfolio_manager = None

def get_portfolio_manager(total_capital: float = 100000.0) -> PortfolioManager:
    """Get or create global portfolio manager instance"""
    global _portfolio_manager
    if _portfolio_manager is None:
        _portfolio_manager = PortfolioManager(total_capital)
    return _portfolio_manager
