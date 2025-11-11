#!/usr/bin/env python3
"""
🌙 Moon Dev's Trading Agent Configuration
Centralized configuration for trading agents
Built with love by Moon Dev 🚀
"""

from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
import json

@dataclass
class TradingConfig:
    """Configuration for trading agent"""
    
    # Model settings
    models: List[str] = field(default_factory=lambda: ["deepseek"])
    model_temperature: float = 0.7
    model_max_tokens: int = 1024
    system_prompt: str = ""  # Custom system prompt (empty = use default)
    
    # Asset settings
    asset_type: str = "crypto"  # "crypto", "stock", or "options"
    ticker: str = "BTC"  # BTC, ETH for crypto; AAPL, TSLA for stocks; SPY, QQQ for options (underlying)
    
    # Trading settings
    timeframe: str = "3m"  # 1m, 3m, 5m, 15m, 30m, 1h, 4h, 1d (default: 3m for optimal trading)
    cycle_interval: int = 60  # seconds between cycles (1 minute = 60 seconds for active trading)
    
    # Simulation settings
    use_simulation: bool = True
    initial_balance: float = 100000.0  # $100k starting capital for better position sizing
    position_size_percentage: float = 0.1  # 10% per trade
    
    # Portfolio management
    max_positions: int = 3  # Max concurrent positions
    risk_per_trade: float = 0.02  # 2% risk per trade
    monitored_assets: List[str] = field(default_factory=lambda: ["BTC", "ETH", "SPY", "QQQ"])
    
    # Agent identity (for multi-agent support)
    agent_name: str = "Agent 1"
    agent_strategy: str = ""  # Strategy description
    
    # Session settings
    save_decisions: bool = True
    decisions_dir: str = "src/data/trading_decisions"
    
    # Data provider settings
    use_live_data: bool = False  # Use live data vs example data
    
    # RL Optimization settings
    enable_rl: bool = False  # Enable RL optimization
    rl_training_trades: int = 50  # Number of trades before optimization
    rl_status: str = "inactive"  # "inactive", "training", "optimized"
    rl_optimized_prompt: str = ""  # Optimized system prompt (empty = use original)
    
    # RBI RL Optimization settings
    enable_rbi_rl: bool = False  # Enable RL optimization for RBI backtests
    rbi_rl_training_backtests: int = 10  # Number of backtests before optimization
    rbi_rl_status: str = "inactive"  # "inactive", "training", "optimized"
    
    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return {
            'models': self.models,
            'model_temperature': self.model_temperature,
            'model_max_tokens': self.model_max_tokens,
            'system_prompt': self.system_prompt,
            'asset_type': self.asset_type,
            'ticker': self.ticker,
            'timeframe': self.timeframe,
            'cycle_interval': self.cycle_interval,
            'use_simulation': self.use_simulation,
            'initial_balance': self.initial_balance,
            'position_size_percentage': self.position_size_percentage,
            'max_positions': self.max_positions,
            'risk_per_trade': self.risk_per_trade,
            'monitored_assets': self.monitored_assets,
            'agent_name': self.agent_name,
            'agent_strategy': self.agent_strategy,
            'save_decisions': self.save_decisions,
            'decisions_dir': self.decisions_dir,
            'use_live_data': self.use_live_data,
            'enable_rl': self.enable_rl,
            'rl_training_trades': self.rl_training_trades,
            'rl_status': self.rl_status,
            'rl_optimized_prompt': self.rl_optimized_prompt,
            'enable_rbi_rl': self.enable_rbi_rl,
            'rbi_rl_training_backtests': self.rbi_rl_training_backtests,
            'rbi_rl_status': self.rbi_rl_status
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TradingConfig':
        """Create config from dictionary"""
        config = cls(**data)
        config.validate()
        return config
    
    def validate(self):
        """Validate configuration"""
        # Ensure monitored_assets match asset_type
        if self.asset_type == "crypto":
            crypto_tickers = ["BTC", "ETH", "SOL", "DOGE", "XRP", "ADA", "DOT", "MATIC", "AVAX", "LINK"]
            invalid = [a for a in self.monitored_assets if a not in crypto_tickers]
            if invalid:
                raise ValueError(f"Invalid crypto tickers: {invalid}. Agent can only trade crypto OR stocks, not both.")
        elif self.asset_type == "stock":
            stock_tickers = ["SPY", "QQQ", "AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "AMD"]
            invalid = [a for a in self.monitored_assets if a not in stock_tickers]
            if invalid:
                raise ValueError(f"Invalid stock tickers: {invalid}. Agent can only trade crypto OR stocks, not both.")
        elif self.asset_type == "options":
            # Options use stock tickers as underlyings
            options_tickers = ["SPY", "QQQ", "AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "AMD", "IWM"]
            invalid = [a for a in self.monitored_assets if a not in options_tickers]
            if invalid:
                raise ValueError(f"Invalid options underlying tickers: {invalid}. Options trading supports major stocks/ETFs only.")
    
    def save(self, filepath: str):
        """Save config to JSON file"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> 'TradingConfig':
        """Load config from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def get_asset_display_name(self) -> str:
        """Get display name for asset"""
        if self.asset_type == "crypto":
            return f"{self.ticker}/USD"
        elif self.asset_type == "options":
            return f"{self.ticker} 0DTE Options"
        else:
            return self.ticker
    
    def get_cycle_display(self) -> str:
        """Get human-readable cycle interval"""
        minutes = self.cycle_interval // 60
        if minutes < 60:
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        hours = minutes // 60
        return f"{hours} hour{'s' if hours != 1 else ''}"


# Default configurations
DEFAULT_CONFIG = TradingConfig()

CRYPTO_BTC_CONFIG = TradingConfig(
    asset_type="crypto",
    ticker="BTC",
    timeframe="3m",
    cycle_interval=180
)

CRYPTO_ETH_CONFIG = TradingConfig(
    asset_type="crypto",
    ticker="ETH",
    timeframe="3m",
    cycle_interval=180
)

STOCK_AAPL_CONFIG = TradingConfig(
    asset_type="stock",
    ticker="AAPL",
    timeframe="3m",
    cycle_interval=180,
    use_live_data=True
)

STOCK_TSLA_CONFIG = TradingConfig(
    asset_type="stock",
    ticker="TSLA",
    timeframe="3m",
    cycle_interval=180,
    use_live_data=True
)

# Available models
AVAILABLE_MODELS = [
    "deepseek",
    "openai",
    "claude",
    "gemini",
    "groq",
    "xai"
]

# Available tickers
CRYPTO_TICKERS = ["BTC", "ETH", "SOL", "AVAX", "MATIC"]
STOCK_TICKERS = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META"]
OPTIONS_TICKERS = ["SPY", "QQQ", "AAPL", "TSLA", "NVDA", "IWM"]  # Underlying symbols for options

# Timeframes
TIMEFRAMES = ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d"]
