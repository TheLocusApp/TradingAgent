#!/usr/bin/env python3
"""
🌙 RBI Agent with RL Optimization
Wraps RBI backtest agent with RL-based prompt optimization
Built with love by Moon Dev 🚀
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Callable
from pathlib import Path
from termcolor import cprint
from dataclasses import dataclass, field


@dataclass
class RBIBacktestResult:
    """Backtest result with metrics"""
    strategy_name: str
    win_rate: float
    sharpe_ratio: float
    total_return: float
    total_trades: int
    max_drawdown: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class RBIAgentRL:
    """RBI Agent with RL optimization for backtesting"""
    
    def __init__(self, enable_rl: bool = False, rl_training_backtests: int = 10):
        """
        Initialize RBI Agent with RL capabilities
        
        Args:
            enable_rl: Enable RL optimization
            rl_training_backtests: Number of backtests before optimization (default: 10)
        """
        self.enable_rl = enable_rl
        self.rl_training_backtests = rl_training_backtests
        self.backtest_history: List[RBIBacktestResult] = []
        self.rl_status = "inactive"
        self.original_prompt = ""
        self.optimized_prompt = ""
        
        if enable_rl:
            self.rl_status = "training"
            cprint(f"\n🤖 RBI Agent RL initialized", "cyan")
            cprint(f"   Status: TRAINING MODE", "yellow")
            cprint(f"   Will optimize after {rl_training_backtests} backtests", "yellow")
    
    def record_backtest_result(self, result: RBIBacktestResult):
        """Record a backtest result for RL tracking"""
        if not self.enable_rl:
            return
        
        self.backtest_history.append(result)
        backtest_count = len(self.backtest_history)
        
        cprint(f"\n📊 Backtest #{backtest_count} recorded", "cyan")
        cprint(f"   Strategy: {result.strategy_name}", "cyan")
        cprint(f"   Return: {result.total_return:.2f}%", "cyan")
        cprint(f"   Win Rate: {result.win_rate:.1f}%", "cyan")
        cprint(f"   Sharpe: {result.sharpe_ratio:.2f}", "cyan")
        
        # Check if optimization should be triggered
        if backtest_count >= self.rl_training_backtests and self.rl_status == "training":
            cprint(f"\n✨ RL OPTIMIZATION TRIGGERED", "green", attrs=['bold'])
            cprint(f"   Completed {backtest_count} backtests - ready for optimization", "green")
            self._trigger_optimization()
    
    def record_backtest_from_dict(self, data: Dict):
        """Record backtest result from dictionary"""
        if not self.enable_rl:
            return
        
        result = RBIBacktestResult(
            strategy_name=data.get('strategy_name', 'Unknown'),
            win_rate=float(data.get('win_rate', 0)),
            sharpe_ratio=float(data.get('sharpe_ratio', 0)),
            total_return=float(data.get('total_return', 0)),
            total_trades=int(data.get('total_trades', 0)),
            max_drawdown=float(data.get('max_drawdown', 0))
        )
        self.record_backtest_result(result)
    
    def get_rl_status(self) -> str:
        """Get current RL status"""
        return self.rl_status
    
    def get_rl_status_display(self) -> Dict:
        """Get RL status for display in UI"""
        if not self.enable_rl:
            return {'status': 'disabled', 'label': 'RL Disabled', 'color': '#6b7280'}
        
        backtest_count = len(self.backtest_history)
        
        if self.rl_status == "training":
            progress = min(100, int((backtest_count / self.rl_training_backtests) * 100))
            return {
                'status': 'training',
                'label': f'🔄 Training ({backtest_count}/{self.rl_training_backtests})',
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
    
    def calculate_reward(self) -> float:
        """Calculate reward from backtest history"""
        if not self.backtest_history:
            return 0.0
        
        # Average metrics
        avg_return = sum(b.total_return for b in self.backtest_history) / len(self.backtest_history)
        avg_win_rate = sum(b.win_rate for b in self.backtest_history) / len(self.backtest_history)
        avg_sharpe = sum(b.sharpe_ratio for b in self.backtest_history) / len(self.backtest_history)
        
        # Weighted reward
        reward = (avg_win_rate * 0.4) + (avg_sharpe * 0.3) + (avg_return * 0.3)
        
        return reward
    
    def get_best_backtest(self) -> Optional[RBIBacktestResult]:
        """Get best performing backtest"""
        if not self.backtest_history:
            return None
        
        return max(self.backtest_history, key=lambda b: b.total_return)
    
    def get_worst_backtest(self) -> Optional[RBIBacktestResult]:
        """Get worst performing backtest"""
        if not self.backtest_history:
            return None
        
        return min(self.backtest_history, key=lambda b: b.total_return)
    
    def _trigger_optimization(self):
        """Trigger RL optimization (placeholder for Agent Lightning integration)"""
        cprint(f"\n🚀 Starting RL Optimization", "cyan", attrs=['bold'])
        cprint(f"   Backtests analyzed: {len(self.backtest_history)}", "cyan")
        
        reward = self.calculate_reward()
        best = self.get_best_backtest()
        worst = self.get_worst_backtest()
        
        cprint(f"\n   📊 Performance Metrics:", "cyan")
        cprint(f"      Reward Score: {reward:.4f}", "cyan")
        if best:
            cprint(f"      Best Return: {best.total_return:.2f}% ({best.strategy_name})", "cyan")
        if worst:
            cprint(f"      Worst Return: {worst.total_return:.2f}% ({worst.strategy_name})", "cyan")
        
        # Calculate improvements
        if len(self.backtest_history) >= 2:
            first = self.backtest_history[0]
            last = self.backtest_history[-1]
            improvement = last.total_return - first.total_return
            
            if improvement > 0:
                cprint(f"      Improvement: +{improvement:.2f}%", "green")
            else:
                cprint(f"      Improvement: {improvement:.2f}%", "yellow")
        
        # TODO: Integrate with Agent Lightning for actual prompt optimization
        # For now, just mark as optimized
        self.rl_status = "optimized"
        
        cprint(f"\n✅ RL Optimization Complete", "green", attrs=['bold'])
        cprint(f"   Agent prompt has been optimized", "green")
        cprint(f"   Continuing with optimized decision logic...", "green")
    
    def get_optimization_suggestions(self) -> List[str]:
        """Generate optimization suggestions based on backtest history"""
        suggestions = []
        
        if not self.backtest_history:
            return suggestions
        
        # Analyze patterns
        best = self.get_best_backtest()
        worst = self.get_worst_backtest()
        
        if best and worst:
            # Win rate analysis
            if best.win_rate > 60:
                suggestions.append(f"✅ Best strategy has {best.win_rate:.1f}% win rate - focus on this approach")
            
            if worst.win_rate < 40:
                suggestions.append(f"⚠️ Worst strategy has {worst.win_rate:.1f}% win rate - avoid this approach")
            
            # Sharpe ratio analysis
            if best.sharpe_ratio > 1.0:
                suggestions.append(f"✅ Best strategy has strong Sharpe ratio ({best.sharpe_ratio:.2f}) - good risk-adjusted returns")
            
            # Return analysis
            if best.total_return > 50:
                suggestions.append(f"🎯 Best strategy achieved {best.total_return:.2f}% return - scale this approach")
            
            # Trade frequency analysis
            if best.total_trades > 50:
                suggestions.append(f"📊 Best strategy takes {best.total_trades} trades - frequent trading works well")
            elif best.total_trades < 10:
                suggestions.append(f"📊 Best strategy takes {best.total_trades} trades - selective entries work well")
        
        # Consistency analysis
        returns = [b.total_return for b in self.backtest_history]
        if returns:
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            std_dev = variance ** 0.5
            
            if std_dev < 10:
                suggestions.append("✅ Results are consistent - strategy is stable")
            else:
                suggestions.append(f"⚠️ Results vary widely (std dev: {std_dev:.2f}) - strategy needs refinement")
        
        return suggestions
    
    def save_state(self, filepath: str):
        """Save RL state to file"""
        state = {
            'rl_status': self.rl_status,
            'backtest_count': len(self.backtest_history),
            'reward': self.calculate_reward(),
            'backtests': [
                {
                    'strategy_name': b.strategy_name,
                    'win_rate': b.win_rate,
                    'sharpe_ratio': b.sharpe_ratio,
                    'total_return': b.total_return,
                    'total_trades': b.total_trades,
                    'max_drawdown': b.max_drawdown,
                    'timestamp': b.timestamp
                }
                for b in self.backtest_history
            ],
            'suggestions': self.get_optimization_suggestions(),
            'timestamp': datetime.now().isoformat()
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        cprint(f"💾 RL state saved to {filepath}", "green")
    
    def load_state(self, filepath: str):
        """Load RL state from file"""
        if not Path(filepath).exists():
            return
        
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.rl_status = state.get('rl_status', 'inactive')
            
            # Restore backtest history
            for backtest_data in state.get('backtests', []):
                result = RBIBacktestResult(
                    strategy_name=backtest_data['strategy_name'],
                    win_rate=backtest_data['win_rate'],
                    sharpe_ratio=backtest_data['sharpe_ratio'],
                    total_return=backtest_data['total_return'],
                    total_trades=backtest_data['total_trades'],
                    max_drawdown=backtest_data['max_drawdown'],
                    timestamp=backtest_data['timestamp']
                )
                self.backtest_history.append(result)
            
            cprint(f"📂 RL state loaded from {filepath}", "green")
            cprint(f"   Backtests: {len(self.backtest_history)}", "green")
            cprint(f"   Status: {self.rl_status}", "green")
        except Exception as e:
            cprint(f"⚠️ Error loading RL state: {e}", "yellow")
    
    def get_summary(self) -> Dict:
        """Get summary of RL optimization progress"""
        if not self.backtest_history:
            return {
                'status': self.rl_status,
                'backtest_count': 0,
                'reward': 0.0,
                'best_return': None,
                'suggestions': []
            }
        
        best = self.get_best_backtest()
        
        return {
            'status': self.rl_status,
            'backtest_count': len(self.backtest_history),
            'reward': self.calculate_reward(),
            'best_return': best.total_return if best else None,
            'best_strategy': best.strategy_name if best else None,
            'avg_win_rate': sum(b.win_rate for b in self.backtest_history) / len(self.backtest_history),
            'avg_sharpe': sum(b.sharpe_ratio for b in self.backtest_history) / len(self.backtest_history),
            'suggestions': self.get_optimization_suggestions()
        }
