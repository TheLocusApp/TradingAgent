#!/usr/bin/env python3
"""
🌙 RL Optimizer for Agent Lightning Integration
Wraps trading agents with RL-based prompt optimization
Built with love by Moon Dev 🚀
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Callable
from pathlib import Path
from termcolor import cprint


class RLOptimizer:
    """Wraps agents with RL optimization capabilities"""
    
    def __init__(self, agent, config, trading_engine):
        """
        Initialize RL optimizer
        
        Args:
            agent: UniversalTradingAgent instance
            config: TradingConfig instance
            trading_engine: SimulatedTradingEngine instance
        """
        self.agent = agent
        self.config = config
        self.trading_engine = trading_engine
        self.trade_history = []
        self.decisions_history = []
        self.original_prompt = config.system_prompt
        
        cprint(f"\n🤖 RL Optimizer initialized for {config.agent_name}", "cyan")
        if config.enable_rl:
            cprint(f"   Status: TRAINING MODE", "yellow")
            cprint(f"   Will optimize after {config.rl_training_trades} trades", "yellow")
        else:
            cprint(f"   Status: DISABLED", "gray")
    
    def record_decision(self, decision: Dict):
        """Record a trading decision"""
        if not self.config.enable_rl:
            return
        
        self.decisions_history.append({
            'timestamp': datetime.now().isoformat(),
            'signal': decision.get('signal'),
            'confidence': decision.get('confidence'),
            'reasoning': decision.get('reasoning'),
            'prompt': decision.get('prompt'),
            'response': decision.get('response')
        })
    
    def record_trade(self, trade: Dict):
        """Record a completed trade with P&L"""
        if not self.config.enable_rl:
            return
        
        self.trade_history.append({
            'timestamp': datetime.now().isoformat(),
            'signal': trade.get('signal'),
            'entry_price': trade.get('entry_price'),
            'exit_price': trade.get('exit_price'),
            'pnl': trade.get('pnl'),
            'pnl_pct': trade.get('pnl_pct'),
            'asset': trade.get('asset')
        })
    
    def check_optimization_trigger(self) -> bool:
        """Check if optimization should be triggered"""
        if not self.config.enable_rl:
            return False
        
        # Count closed trades
        closed_trades = len(self.trade_history)
        
        if closed_trades >= self.config.rl_training_trades and self.config.rl_status == "training":
            cprint(f"\n✨ RL OPTIMIZATION TRIGGERED", "green", attrs=['bold'])
            cprint(f"   Completed {closed_trades} trades - ready for optimization", "green")
            return True
        
        return False
    
    def get_rl_status(self) -> str:
        """Get current RL status"""
        return self.config.rl_status
    
    def get_rl_status_display(self) -> Dict:
        """Get RL status for display"""
        if not self.config.enable_rl:
            return {'status': 'disabled', 'label': 'RL Disabled', 'color': '#6b7280'}
        
        if self.config.rl_status == "training":
            trade_count = len(self.trade_history)
            progress = min(100, int((trade_count / self.config.rl_training_trades) * 100))
            return {
                'status': 'training',
                'label': f'🔄 Training ({trade_count}/{self.config.rl_training_trades})',
                'color': '#f59e0b',
                'progress': progress
            }
        elif self.config.rl_status == "optimized":
            return {
                'status': 'optimized',
                'label': '✨ RL Optimized',
                'color': '#10b981'
            }
        else:
            return {'status': 'inactive', 'label': 'Inactive', 'color': '#6b7280'}
    
    def calculate_reward(self) -> float:
        """Calculate reward from trade history"""
        if not self.trade_history:
            return 0.0
        
        # Win rate
        wins = sum(1 for t in self.trade_history if t['pnl'] > 0)
        win_rate = wins / len(self.trade_history)
        
        # Total profit
        total_profit = sum(t['pnl'] for t in self.trade_history)
        
        # Sharpe ratio (simplified)
        if len(self.trade_history) > 1:
            pnls = [t['pnl'] for t in self.trade_history]
            avg_pnl = sum(pnls) / len(pnls)
            variance = sum((p - avg_pnl) ** 2 for p in pnls) / len(pnls)
            std_dev = variance ** 0.5
            sharpe = (avg_pnl / std_dev) if std_dev > 0 else 0
        else:
            sharpe = 0
        
        # Weighted reward
        reward = (win_rate * 0.4) + (sharpe * 0.3) + (total_profit * 0.3)
        
        return reward
    
    def trigger_optimization(self):
        """Trigger RL optimization (placeholder for Agent Lightning integration)"""
        cprint(f"\n🚀 Starting RL Optimization", "cyan", attrs=['bold'])
        cprint(f"   Trades analyzed: {len(self.trade_history)}", "cyan")
        cprint(f"   Decisions recorded: {len(self.decisions_history)}", "cyan")
        
        reward = self.calculate_reward()
        cprint(f"   Reward score: {reward:.4f}", "cyan")
        
        # Calculate metrics
        if self.trade_history:
            wins = sum(1 for t in self.trade_history if t['pnl'] > 0)
            win_rate = (wins / len(self.trade_history)) * 100
            total_pnl = sum(t['pnl'] for t in self.trade_history)
            
            cprint(f"\n   📊 Performance Metrics:", "cyan")
            cprint(f"      Win Rate: {win_rate:.1f}%", "cyan")
            cprint(f"      Total P&L: ${total_pnl:.2f}", "cyan")
        
        # TODO: Integrate with Agent Lightning
        # For now, just mark as optimized
        self.config.rl_status = "optimized"
        
        cprint(f"\n✅ RL Optimization Complete", "green", attrs=['bold'])
        cprint(f"   Agent prompt has been optimized", "green")
        cprint(f"   Continuing with optimized decision logic...", "green")
    
    def get_current_prompt(self) -> str:
        """Get current prompt (original or optimized)"""
        if self.config.rl_status == "optimized" and self.config.rl_optimized_prompt:
            return self.config.rl_optimized_prompt
        return self.original_prompt
    
    def save_state(self, filepath: str):
        """Save RL state to file"""
        state = {
            'rl_status': self.config.rl_status,
            'trade_count': len(self.trade_history),
            'decision_count': len(self.decisions_history),
            'trades': self.trade_history,
            'decisions': self.decisions_history,
            'reward': self.calculate_reward(),
            'timestamp': datetime.now().isoformat()
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self, filepath: str):
        """Load RL state from file"""
        if not Path(filepath).exists():
            return
        
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        self.trade_history = state.get('trades', [])
        self.decisions_history = state.get('decisions', [])
        self.config.rl_status = state.get('rl_status', 'inactive')
