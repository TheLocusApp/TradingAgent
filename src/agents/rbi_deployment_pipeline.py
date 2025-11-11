#!/usr/bin/env python3
"""
🚀 RBI Strategy Deployment Pipeline
One-click deployment from backtest to live trading
Built with love by Moon Dev 🚀
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple
from termcolor import cprint
import re

from src.config.trading_config import TradingConfig


class RBIDeploymentPipeline:
    """
    Manages deployment of RBI backtested strategies to live trading
    
    Features:
    - Extract parameters from backtest files
    - Create live trading agent configs
    - Paper trading validation period
    - Performance monitoring and auto-promotion
    """
    
    def __init__(self):
        """Initialize deployment pipeline"""
        self.deployments_dir = Path(__file__).parent.parent / "data" / "rbi_deployments"
        self.deployments_dir.mkdir(parents=True, exist_ok=True)
        self.deployments_file = self.deployments_dir / "deployments.json"
        
        self.deployments: Dict[str, Dict] = {}
        self._load_deployments()
        
        cprint("✅ RBI Deployment Pipeline initialized", "green")
    
    def _load_deployments(self):
        """Load existing deployments"""
        if self.deployments_file.exists():
            try:
                with open(self.deployments_file, 'r') as f:
                    self.deployments = json.load(f)
                cprint(f"📊 Loaded {len(self.deployments)} existing deployments", "green")
            except Exception as e:
                cprint(f"⚠️ Error loading deployments: {e}", "yellow")
    
    def _save_deployments(self):
        """Save deployments to file"""
        try:
            with open(self.deployments_file, 'w') as f:
                json.dump(self.deployments, f, indent=2)
        except Exception as e:
            cprint(f"⚠️ Error saving deployments: {e}", "yellow")
    
    def extract_backtest_params(self, backtest_file: Path) -> Optional[Dict]:
        """
        Extract trading parameters from backtest file
        
        Args:
            backtest_file: Path to backtest .py file
            
        Returns:
            Dict of extracted parameters or None if failed
        """
        try:
            with open(backtest_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            params = {
                'strategy_name': backtest_file.stem.replace('_BT', '').replace('_BTFinal', '').replace('_WORKING', ''),
                'file_path': str(backtest_file),
                'extracted_at': datetime.now().isoformat()
            }
            
            # Extract key parameters using regex
            # Look for common parameter patterns
            
            # Position sizing
            position_size_match = re.search(r'self\.position_size\s*=\s*([\d.]+)', content)
            if position_size_match:
                params['position_size_pct'] = float(position_size_match.group(1)) * 100
            
            # Stop loss
            stop_loss_match = re.search(r'stop_loss\s*=\s*([\d.]+)', content)
            if stop_loss_match:
                params['stop_loss_pct'] = float(stop_loss_match.group(1)) * 100
            
            # Take profit
            take_profit_match = re.search(r'take_profit\s*=\s*([\d.]+)', content)
            if take_profit_match:
                params['take_profit_pct'] = float(take_profit_match.group(1)) * 100
            
            # Timeframe (look for comments or variable names)
            if '1h' in content.lower() or 'hourly' in content.lower():
                params['timeframe'] = '1h'
            elif '4h' in content.lower():
                params['timeframe'] = '4h'
            elif '1d' in content.lower() or 'daily' in content.lower():
                params['timeframe'] = '1d'
            else:
                params['timeframe'] = '15m'  # Default
            
            # Asset type (infer from strategy name or content)
            if 'option' in params['strategy_name'].lower():
                params['asset_type'] = 'options'
            elif any(ticker in content for ticker in ['BTC', 'ETH', 'SOL']):
                params['asset_type'] = 'crypto'
            else:
                params['asset_type'] = 'stock'
            
            # Strategy description (extract from docstring if present)
            docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
            if docstring_match:
                params['description'] = docstring_match.group(1).strip()[:200]  # First 200 chars
            
            return params
            
        except Exception as e:
            cprint(f"❌ Error extracting parameters from {backtest_file}: {e}", "red")
            return None
    
    def create_agent_config_from_backtest(self, backtest_params: Dict, 
                                          initial_balance: float = 100000.0) -> TradingConfig:
        """
        Create TradingConfig from backtest parameters
        
        Args:
            backtest_params: Extracted backtest parameters
            initial_balance: Starting capital for live agent
            
        Returns:
            TradingConfig instance
        """
        config = TradingConfig(
            agent_name=f"RBI_{backtest_params['strategy_name']}",
            agent_strategy=backtest_params.get('description', f"Deployed from {backtest_params['strategy_name']} backtest"),
            asset_type=backtest_params.get('asset_type', 'crypto'),
            timeframe=backtest_params.get('timeframe', '15m'),
            initial_balance=initial_balance,
            position_size_percentage=backtest_params.get('position_size_pct', 10.0) / 100.0,
            risk_per_trade=backtest_params.get('stop_loss_pct', 2.0) / 100.0,
            models=['deepseek'],  # Default to DeepSeek for cost efficiency
            cycle_interval=self._timeframe_to_seconds(backtest_params.get('timeframe', '15m')),
            use_simulation=True,
            save_decisions=True
        )
        
        # Set appropriate tickers based on asset type
        if config.asset_type == 'crypto':
            config.monitored_assets = ['BTC', 'ETH', 'SOL']
            config.ticker = 'BTC'
        elif config.asset_type == 'stock':
            config.monitored_assets = ['SPY', 'QQQ', 'AAPL', 'TSLA']
            config.ticker = 'SPY'
        elif config.asset_type == 'options':
            config.monitored_assets = ['SPY', 'QQQ']
            config.ticker = 'SPY'
        
        return config
    
    def _timeframe_to_seconds(self, timeframe: str) -> int:
        """Convert timeframe string to seconds"""
        timeframe_map = {
            '1m': 60,
            '3m': 180,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }
        return timeframe_map.get(timeframe, 900)  # Default 15m
    
    def deploy_strategy(self, backtest_file: Path, backtest_results: Dict,
                       initial_balance: float = 100000.0,
                       paper_trading_days: int = 14) -> Optional[Dict]:
        """
        Deploy a backtest strategy to live trading
        
        Args:
            backtest_file: Path to backtest file
            backtest_results: Backtest performance results
            initial_balance: Starting capital
            paper_trading_days: Days of paper trading before live (default 14)
            
        Returns:
            Deployment info dict or None if failed
        """
        cprint(f"\n🚀 Deploying strategy: {backtest_file.name}", "cyan")
        
        # Extract parameters
        params = self.extract_backtest_params(backtest_file)
        if not params:
            cprint("❌ Failed to extract parameters", "red")
            return None
        
        # Create agent config
        config = self.create_agent_config_from_backtest(params, initial_balance)
        
        # Create deployment record
        deployment_id = f"rbi_{params['strategy_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        deployment = {
            'deployment_id': deployment_id,
            'strategy_name': params['strategy_name'],
            'backtest_file': str(backtest_file),
            'backtest_results': backtest_results,
            'config': config.to_dict(),
            'status': 'paper_trading',  # paper_trading, live, paused, failed
            'deployed_at': datetime.now().isoformat(),
            'paper_trading_until': (datetime.now().timestamp() + paper_trading_days * 86400),
            'live_performance': {
                'trades': 0,
                'pnl': 0.0,
                'pnl_pct': 0.0,
                'win_rate': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0
            },
            'validation_status': {
                'backtest_vs_live_deviation': 0.0,  # % deviation from expected
                'meets_expectations': True,
                'issues': []
            }
        }
        
        self.deployments[deployment_id] = deployment
        self._save_deployments()
        
        cprint(f"✅ Strategy deployed as: {deployment_id}", "green")
        cprint(f"   Status: Paper Trading ({paper_trading_days} days)", "yellow")
        cprint(f"   Backtest Sharpe: {backtest_results.get('sharpe_ratio', 0):.2f}", "cyan")
        cprint(f"   Backtest Return: {backtest_results.get('total_return', 0):.2f}%", "cyan")
        
        return deployment
    
    def update_deployment_performance(self, deployment_id: str, live_stats: Dict):
        """
        Update deployment with live performance data
        
        Args:
            deployment_id: Deployment identifier
            live_stats: Live performance statistics
        """
        if deployment_id not in self.deployments:
            cprint(f"⚠️ Deployment {deployment_id} not found", "yellow")
            return
        
        deployment = self.deployments[deployment_id]
        deployment['live_performance'] = live_stats
        deployment['last_updated'] = datetime.now().isoformat()
        
        # Check if paper trading period is over
        if deployment['status'] == 'paper_trading':
            if datetime.now().timestamp() >= deployment['paper_trading_until']:
                # Validate performance before promoting to live
                validation = self._validate_deployment(deployment)
                
                if validation['meets_expectations']:
                    deployment['status'] = 'live'
                    cprint(f"🎉 {deployment_id} promoted to LIVE trading!", "green")
                else:
                    deployment['status'] = 'failed'
                    cprint(f"❌ {deployment_id} failed validation:", "red")
                    for issue in validation['issues']:
                        cprint(f"   - {issue}", "red")
                
                deployment['validation_status'] = validation
        
        self._save_deployments()
    
    def _validate_deployment(self, deployment: Dict) -> Dict:
        """
        Validate deployment performance against backtest expectations
        
        Args:
            deployment: Deployment dict
            
        Returns:
            Validation result dict
        """
        backtest_results = deployment['backtest_results']
        live_performance = deployment['live_performance']
        
        issues = []
        
        # Check if we have enough trades
        if live_performance['trades'] < 20:
            issues.append(f"Insufficient trades: {live_performance['trades']} < 20")
        
        # Check Sharpe ratio deviation
        backtest_sharpe = backtest_results.get('sharpe_ratio', 0)
        live_sharpe = live_performance.get('sharpe_ratio', 0)
        sharpe_deviation = abs(live_sharpe - backtest_sharpe) / max(abs(backtest_sharpe), 0.1)
        
        if sharpe_deviation > 0.5:  # More than 50% deviation
            issues.append(f"Sharpe deviation too high: {sharpe_deviation*100:.1f}%")
        
        # Check if returns are positive
        if live_performance.get('pnl_pct', 0) < -5:
            issues.append(f"Negative returns: {live_performance['pnl_pct']:.2f}%")
        
        # Check drawdown
        if live_performance.get('max_drawdown', 0) > 0.10:  # More than 10%
            issues.append(f"Excessive drawdown: {live_performance['max_drawdown']*100:.1f}%")
        
        return {
            'meets_expectations': len(issues) == 0,
            'issues': issues,
            'sharpe_deviation': sharpe_deviation,
            'validated_at': datetime.now().isoformat()
        }
    
    def get_deployment_status(self, deployment_id: str) -> Optional[Dict]:
        """Get deployment status"""
        return self.deployments.get(deployment_id)
    
    def get_all_deployments(self) -> Dict[str, Dict]:
        """Get all deployments"""
        return self.deployments
    
    def pause_deployment(self, deployment_id: str, reason: str = "Manual pause"):
        """Pause a deployment"""
        if deployment_id in self.deployments:
            self.deployments[deployment_id]['status'] = 'paused'
            self.deployments[deployment_id]['pause_reason'] = reason
            self.deployments[deployment_id]['paused_at'] = datetime.now().isoformat()
            self._save_deployments()
            cprint(f"⏸️ Deployment {deployment_id} paused: {reason}", "yellow")
    
    def resume_deployment(self, deployment_id: str):
        """Resume a paused deployment"""
        if deployment_id in self.deployments:
            old_status = self.deployments[deployment_id].get('status_before_pause', 'live')
            self.deployments[deployment_id]['status'] = old_status
            self.deployments[deployment_id]['resumed_at'] = datetime.now().isoformat()
            self._save_deployments()
            cprint(f"▶️ Deployment {deployment_id} resumed", "green")


# Global deployment pipeline instance
_deployment_pipeline = None

def get_deployment_pipeline() -> RBIDeploymentPipeline:
    """Get or create global deployment pipeline instance"""
    global _deployment_pipeline
    if _deployment_pipeline is None:
        _deployment_pipeline = RBIDeploymentPipeline()
    return _deployment_pipeline
