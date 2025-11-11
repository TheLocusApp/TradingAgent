#!/usr/bin/env python3
"""
🌙 Moon Dev's Universal Trading Agent
Supports multiple models, crypto & stocks, configurable tickers
Built with love by Moon Dev 🚀
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from termcolor import cprint
from dotenv import load_dotenv

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import configuration
from src.config.trading_config import TradingConfig, AVAILABLE_MODELS

# Import model factory
from src.models import model_factory

# Import data providers
from src.data_providers.tastytrade_provider import TastytradeProvider
from src.data_providers.comprehensive_market_data import ComprehensiveMarketDataProvider
from src.data_providers.polygon_options_provider import PolygonOptionsProvider
from src.data_providers.tastytrade_dxlink_provider import TastytradeDXLinkProvider


class UniversalTradingAgent:
    """Universal trading agent supporting multiple models and assets"""
    
    def __init__(self, config: TradingConfig):
        """Initialize agent with configuration"""
        self.config = config
        self.models = {}
        self.data_provider = None
        self.comprehensive_provider = ComprehensiveMarketDataProvider()
        self.options_provider = None
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_decisions = []
        self.start_time = datetime.now()
        self.invocation_count = 0
        
        # Portfolio management
        self.capital = config.initial_balance
        self.free_capital = config.initial_balance
        self.positions = {}  # {asset: {size, entry_price, current_price, pnl, pnl_pct}}
        self.trade_history = []
        
        # Initialize models
        self._initialize_models()
        
        # Initialize data provider
        if config.asset_type == "stock" and config.use_live_data:
            self._initialize_stock_provider()
        elif config.asset_type == "options":
            self._initialize_options_provider()
        
        # Session file
        decisions_dir = Path(config.decisions_dir)
        decisions_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = decisions_dir / f"session_{self.session_id}.json"
        
        cprint(f"\n✨ Universal Trading Agent Ready!", "green", attrs=['bold'])
        cprint(f"   Asset: {config.get_asset_display_name()}", "cyan")
        cprint(f"   Models: {', '.join(config.models)}", "cyan")
        cprint(f"   Timeframe: {config.timeframe}", "cyan")
        cprint(f"   Cycle: {config.get_cycle_display()}", "cyan")
    
    def _initialize_models(self):
        """Initialize AI models"""
        cprint(f"\n🤖 Initializing {len(self.config.models)} model(s)...", "cyan")
        
        for model_name in self.config.models:
            if model_name not in AVAILABLE_MODELS:
                cprint(f"⚠️ Unknown model: {model_name}", "yellow")
                continue
            
            try:
                model = model_factory.get_model(model_name)
                if model:
                    self.models[model_name] = model
                    cprint(f"✅ {model_name}: {model.model_name}", "green")
                else:
                    cprint(f"⚠️ {model_name}: Not available (skipping)", "yellow")
            except Exception as e:
                cprint(f"⚠️ {model_name}: {str(e)[:80]} (skipping)", "yellow")
        
        # Ensure we have at least one model
        if not self.models:
            cprint(f"\n❌ ERROR: No models could be initialized!", "red", attrs=['bold'])
            cprint(f"   Please check your API keys in .env", "red")
            raise RuntimeError("No AI models available. Check API keys.")
    
    def _initialize_stock_provider(self):
        """Initialize Tastytrade provider for stocks"""
        try:
            cprint("\n📈 Connecting to Tastytrade...", "cyan")
            self.data_provider = TastytradeProvider()
        except Exception as e:
            cprint(f"❌ Failed to connect to Tastytrade: {e}", "red")
            cprint("   Falling back to example data", "yellow")
    
    def _initialize_options_provider(self):
        """Initialize options provider - try Tastytrade DXLink first, then Polygon"""
        # Try Tastytrade DXLink first (REAL-TIME OPTION QUOTES)
        try:
            cprint("\n📊 Connecting to Tastytrade DXLink for options data...", "cyan")
            self.options_provider = TastytradeDXLinkProvider()
            cprint("✅ Tastytrade DXLink options provider initialized (REAL-TIME QUOTES)", "green")
            return
        except Exception as e:
            cprint(f"⚠️ Tastytrade DXLink not available: {e}", "yellow")
        
        # Fallback to Polygon
        try:
            cprint("\n📊 Connecting to Polygon/Massive for options data...", "cyan")
            self.options_provider = PolygonOptionsProvider()
            cprint("✅ Polygon options provider initialized (with fallback data)", "green")
        except Exception as e:
            cprint(f"❌ Failed to initialize options provider: {e}", "red")
            raise RuntimeError("Options trading requires either Tastytrade credentials or POLYGON_API_KEY")
    
    def get_market_state(self) -> Dict:
        """Get current market state with comprehensive data (for first monitored asset)"""
        try:
            # Use first monitored asset (or fallback to ticker)
            symbol = self.config.monitored_assets[0] if self.config.monitored_assets else self.config.ticker
            
            # Use comprehensive provider for all assets
            return self.comprehensive_provider.get_comprehensive_data(
                symbol=symbol,
                timeframe=self.config.timeframe
            )
        except Exception as e:
            cprint(f"⚠️ Error getting market state: {e}", "yellow")
            return self._get_example_market_state()
    
    def get_market_state_for_symbol(self, symbol: str) -> Dict:
        """Get current market state for a specific symbol"""
        try:
            # Use comprehensive provider for this specific symbol
            return self.comprehensive_provider.get_comprehensive_data(
                symbol=symbol,
                timeframe=self.config.timeframe
            )
        except Exception as e:
            cprint(f"⚠️ Error getting market state for {symbol}: {e}", "yellow")
            return self._get_example_market_state()
    
    def get_options_data(self, symbol: str = None) -> Optional[Dict]:
        """Get 0DTE ATM options data for the specified underlying
        
        Args:
            symbol: Underlying symbol (e.g., SPY, QQQ). If None, uses config.ticker
        """
        if not self.options_provider:
            cprint("❌ No options provider initialized", "red")
            return None
        
        # Use provided symbol or fall back to first monitored asset or ticker
        underlying = symbol or (self.config.monitored_assets[0] if self.config.monitored_assets else self.config.ticker)
        
        try:
            cprint(f"📊 Calling options_provider.get_0dte_atm_options({underlying})...", "cyan")
            result = self.options_provider.get_0dte_atm_options(underlying)
            if result:
                cprint(f"✅ Options data received for {underlying}", "green")
            else:
                cprint(f"⚠️ Options provider returned None for {underlying}", "yellow")
            return result
        except Exception as e:
            cprint(f"❌ EXCEPTION getting options data for {underlying}: {e}", "red")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_example_market_state(self) -> Dict:
        """Return example market state (fallback)"""
        return {
            'symbol': self.config.ticker,
            'asset_type': self.config.asset_type,
            'current_price': 113793.5 if self.config.ticker == "BTC" else 2500.0,
            'current_ema20': 113767.331,
            'current_ema50': 113500.0,
            'current_macd': -50.596,
            'current_rsi7': 53.606,
            'current_rsi14': 50.0,
            'mid_prices': [113854.5, 113844.0, 113648.5],
            'ema20_series': [],
            'macd_series': [],
            'rsi7_series': [],
            'rsi14_series': [],
            'volume_series': [],
            'context_ema20': 0,
            'context_ema50': 0,
            'context_atr3': 0,
            'context_atr14': 0,
            'context_volume': 0,
            'context_avg_volume': 0,
            'context_macd_series': [],
            'context_rsi14_series': [],
            'open_interest_latest': 0,
            'open_interest_avg': 0,
            'funding_rate': 0,
            'has_oi_data': False,
            'current_time': datetime.now().isoformat()
        }
    
    def update_account_from_engine(self, trading_engine, current_prices: Dict[str, float] = None):
        """Update account information from trading engine with current prices"""
        # Update account value with current prices
        if current_prices:
            self.capital = trading_engine.get_account_value(current_prices)
        else:
            self.capital = trading_engine.get_account_value()
        self.free_capital = trading_engine.balance
        
        # Convert trading engine positions to agent format
        self.positions = {}
        for symbol, pos in trading_engine.positions.items():
            # Get current price from provided prices, or use entry price as fallback
            current_price = current_prices.get(symbol, pos['entry_price']) if current_prices else pos['entry_price']
            
            entry_value = pos['entry_value']
            current_value = pos['qty'] * current_price
            pnl = current_value - entry_value
            pnl_pct = (pnl / entry_value * 100) if entry_value > 0 else 0
            
            self.positions[symbol] = {
                'size': entry_value,
                'entry_price': pos['entry_price'],
                'current_price': current_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'qty': pos['qty']
            }
    
    def make_decision(self, market_state: Dict) -> Dict:
        """Make trading decision using configured models"""
        decisions = {}
        
        for model_name, model in self.models.items():
            cprint(f"\n🤖 Querying {model_name}...", "cyan")
            
            try:
                # Build prompt
                prompt = self._build_prompt(market_state)
                
                # Get response
                response = model.generate_response(
                    system_prompt=self._get_system_prompt(),
                    user_content=prompt,
                    temperature=self.config.model_temperature,
                    max_tokens=self.config.model_max_tokens
                )
                
                if response:
                    signal, confidence, reasoning = self._parse_response(response.content)
                    decisions[model_name] = {
                        'signal': signal,
                        'confidence': confidence,
                        'reasoning': reasoning,
                        'raw_response': response.content,
                        'prompt': prompt,  # Save the user prompt
                        'system_prompt': self._get_system_prompt()  # Save system prompt
                    }
                    cprint(f"✅ {model_name}: {signal} ({confidence}%)", "green")
                
            except Exception as e:
                cprint(f"❌ Error with {model_name}: {e}", "red")
        
        # Aggregate decision
        final_decision = self._aggregate_decisions(decisions)
        final_decision['timestamp'] = datetime.now().isoformat()
        final_decision['market_state'] = market_state
        final_decision['individual_decisions'] = decisions
        
        # Save decision
        if self.config.save_decisions:
            self._save_decision(final_decision)
        
        return final_decision
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for models"""
        # Use custom system prompt if provided
        if self.config.system_prompt and self.config.system_prompt.strip():
            return self.config.system_prompt
        
        # Otherwise use default
        asset_name = self.config.get_asset_display_name()
        
        # Options-specific system prompt
        if self.config.asset_type == "options":
            return f"""You are an expert options trading AI specializing in 0DTE (zero days to expiration) day trading.

Your role is to analyze real-time market data for {asset_name} and make options trading decisions.

OPTIONS TRADING CONTEXT:
- You are trading 0DTE ATM (at-the-money) options on {self.config.ticker}
- You will be provided with both CALL and PUT option prices
- You must decide whether to BUY a CALL, BUY a PUT, SELL existing positions, or HOLD
- Options expire TODAY - this is pure day trading with high theta decay
- Each contract controls 100 shares of the underlying
- Maximum risk is limited to the premium paid

OBJECTIVE: Capture intraday momentum and volatility moves while managing theta decay.

TRADING RULES:
- When you signal BUY, you MUST specify "BUY CALL" or "BUY PUT" in your reasoning
- Example reasoning: "BUY CALL to capture upside" or "BUY PUT for downside protection"
- SELL to close existing option positions and lock in profits/losses
- HOLD when conditions don't warrant action or theta decay risk is too high
- Consider: underlying price momentum, volatility, time decay, and proximity to key levels
- Options lose value rapidly as expiration approaches - be decisive
- ONLY buy calls or puts - do NOT suggest spreads, straddles, or selling options

KEY FACTORS FOR 0DTE OPTIONS:
- Strong directional momentum = favorable for buying
- High volatility = higher premiums but more opportunity
- Time decay accelerates in final hours - exit before close
- ATM options have highest gamma (fastest price movement)

Provide your response in this format:
SIGNAL: [BUY/SELL/HOLD]
CONFIDENCE: [0-100]%
REASONING: [your analysis - if BUY, specify CALL or PUT]
"""
        
        # Default prompt for stocks/crypto
        return f"""You are an expert trading AI with deep knowledge of technical analysis, risk management, and market dynamics.

Your role is to analyze real-time market data for {asset_name} and make trading decisions.

OBJECTIVE: Maximize risk-adjusted returns while managing position sizing and drawdown.

TRADING RULES:
- You can BUY to open new positions or add to existing positions (scale in)
- You can SELL to close positions or reduce position size (scale out)
- Use HOLD when conditions don't warrant action or when waiting for better entry/exit
- Consider position sizing - you don't need to use all capital at once
- Check "Current live positions & performance" section to see existing positions and available capital
- Manage risk by scaling in/out based on conviction and market conditions

Provide your response in this format:
SIGNAL: [BUY/SELL/HOLD]
CONFIDENCE: [0-100]%
REASONING: [your analysis]
"""
    
    def _build_regime_context(self, symbol: str, current_price: float) -> str:
        """Build market regime context section (contextual, not prescriptive)"""
        try:
            from src.agents.regime_detector import get_regime_detector
            from src.agents.vix_compass import get_vix_compass
            
            detector = get_regime_detector()
            regime_data = detector.detect_regime(symbol)
            rec = detector.get_strategy_recommendation(regime_data)
            
            # Get VIX compass reading
            vix_compass = get_vix_compass()
            vix_context = vix_compass.get_agent_context()
            
            # Build contextual guidance (not commands)
            context = f"""=== MARKET REGIME CONTEXT ===
Current Regime: {regime_data['regime']} (Confidence: {regime_data['confidence']:.0f}%)
{rec.get('context', 'Normal market conditions')}

Technical Environment:
  - ADX: {regime_data['adx']:.1f} (Trend strength indicator)
  - VIX: {regime_data['vix']:.1f} (Market volatility index)
  - Trend Direction: {regime_data['trend_direction']}
  - Price vs EMA20: {regime_data['price_vs_ema20']:.2f}%
  - Price vs EMA50: {regime_data['price_vs_ema50']:.2f}%

{vix_context}"""
            
            # Add market observations as context, not recommendations
            if 'risk_considerations' in rec and rec['risk_considerations']:
                context += "\nMarket Observations:"
                for consideration in rec['risk_considerations']:
                    context += f"\n  - {consideration}"
            
            context += "\n\nNote: Evaluate all trading approaches based on your analysis of current conditions. No specific strategy is recommended."
            
            return context
            
        except Exception as e:
            # Fail gracefully - don't break agent if regime detection fails
            return f"=== MARKET REGIME CONTEXT ===\nRegime detection temporarily unavailable. Proceed with normal analysis."
    
    def _build_risk_guidance(self, current_price: float, market_state: Dict) -> str:
        """Build risk management guidance section (suggestions, not rules)"""
        try:
            from src.agents.advanced_risk_manager import get_risk_manager
            from src.agents.regime_detector import get_regime_detector
            
            # Get regime for risk context
            detector = get_regime_detector()
            regime_data = detector.detect_regime(self.config.ticker)
            
            # Get risk guidance
            rm = get_risk_manager()
            atr = market_state.get('atr', current_price * 0.02)
            
            guidance = rm.get_risk_guidance(
                balance=self.capital,
                entry_price=current_price,
                direction='LONG',  # Default, agent will decide
                confidence=70,  # Default, will be updated with actual
                win_rate=self._calculate_win_rate(),
                atr=atr,
                regime_info=regime_data
            )
            
            # Build guidance section (suggestions, not commands)
            risk_context = f"""=== RISK MANAGEMENT GUIDANCE ===
The Risk Manager has analyzed current conditions and provides the following SUGGESTIONS:

Suggested Stop Loss: ${guidance['suggested_stop_loss']:,.2f} ({abs((guidance['suggested_stop_loss']-current_price)/current_price)*100:.1f}% from entry)
  Reasoning: {guidance['reasoning']}

Suggested Position Size: ${guidance['suggested_position_size_dollars']:,.0f} ({guidance['suggested_position_size_dollars']/self.capital*100:.1f}% of capital)
  Risk per trade: ${guidance['risk_dollars']:,.0f} ({guidance['risk_pct']:.2f}% of capital)

{guidance['override_guidance']}

Note: These are SUGGESTIONS based on current market conditions and your historical performance. You have full autonomy to override if you see a better setup or have additional context."""
            
            return risk_context
            
        except Exception as e:
            # Fail gracefully
            return f"=== RISK MANAGEMENT GUIDANCE ===\nRisk guidance temporarily unavailable. Use your judgment for position sizing and stops."
    
    def _calculate_win_rate(self) -> float:
        """Calculate historical win rate for this agent"""
        if not self.trade_history:
            return 0.50  # Default 50% if no history
        
        winning_trades = sum(1 for t in self.trade_history if t.get('pnl', 0) > 0)
        return winning_trades / len(self.trade_history) if self.trade_history else 0.50
    
    def _build_prompt(self, market_state: Dict) -> str:
        """Build comprehensive prompt with regime and risk context"""
        self.invocation_count += 1
        minutes_elapsed = int((datetime.now() - self.start_time).total_seconds() / 60)
        
        symbol = market_state.get('symbol', 'UNKNOWN')
        current_price = market_state.get('current_price', 0)
        
        # Get regime context
        regime_section = self._build_regime_context(symbol, current_price)
        
        # Get risk guidance
        risk_section = self._build_risk_guidance(current_price, market_state)
        
        # Determine interval display text
        interval_text = self.config.timeframe
        if self.config.timeframe == '3m':
            interval_text = "3‑minute intervals"
        elif self.config.timeframe == '5m':
            interval_text = "5‑minute intervals"
        elif self.config.timeframe == '15m':
            interval_text = "15‑minute intervals"
        elif self.config.timeframe == '1h':
            interval_text = "1‑hour intervals"
        
        # Build comprehensive prompt
        prompt = f"""It has been {minutes_elapsed} minutes since you started trading. The current time is {datetime.now()} and you've been invoked {self.invocation_count} times. Below, we are providing you with a variety of state data, price data, and predictive signals so you can discover alpha. Below that is your current account information, value, performance, positions, etc.

ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST → NEWEST

Timeframes note: Unless stated otherwise in a section title, intraday series are provided at {interval_text}.

{regime_section}

{risk_section}

CURRENT MARKET STATE

ALL {symbol} DATA
current_price = {current_price:.2f}, current_ema20 = {market_state.get('current_ema20', 0):.2f}, current_macd = {market_state.get('current_macd', 0):.3f}, current_rsi (7 period) = {market_state.get('current_rsi7', 0):.2f}
"""
        
        # Add options data if trading options
        if self.config.asset_type == "options":
            options_data = self.get_options_data(symbol)
            if options_data:
                prompt += f"""
0DTE ATM OPTIONS DATA (Expiration: {options_data['expiration']}):
Underlying Price: ${options_data['underlying_price']:.2f}
ATM Strike: ${options_data['atm_strike']:.2f}

CALL Option ({options_data['call']['ticker']}):
  - Bid: ${options_data['call']['bid']:.2f}
  - Ask: ${options_data['call']['ask']:.2f}
  - Mid: ${options_data['call']['mid']:.2f}
  - Last: ${options_data['call']['last']:.2f}

PUT Option ({options_data['put']['ticker']}):
  - Bid: ${options_data['put']['bid']:.2f}
  - Ask: ${options_data['put']['ask']:.2f}
  - Mid: ${options_data['put']['mid']:.2f}
  - Last: ${options_data['put']['last']:.2f}

Note: When you signal BUY, specify "BUY CALL" or "BUY PUT" in your reasoning based on your directional bias.
"""

        
        # Add OI and funding if available
        if market_state.get('has_oi_data'):
            prompt += f"""In addition, here is the latest {symbol} open interest and funding rate for perps (the instrument you are trading):
Open Interest: Latest: {market_state.get('open_interest_latest', 0):.2f} Average: {market_state.get('open_interest_avg', 0):.2f}
Funding Rate: {market_state.get('funding_rate', 0):.2e}
"""
        
        # Add intraday series
        prompt += f"""Intraday series ({interval_text}, oldest → latest):
Mid prices: {self._format_series(market_state.get('mid_prices', []))}
EMA indicators (20‑period): {self._format_series(market_state.get('ema20_series', []))}
MACD indicators: {self._format_series(market_state.get('macd_series', []))}
RSI indicators (7‑Period): {self._format_series(market_state.get('rsi7_series', []))}
RSI indicators (14‑Period): {self._format_series(market_state.get('rsi14_series', []))}
"""
        
        # Add longer-term context (4-hour timeframe) - always include
        prompt += f"""Longer‑term context (4‑hour timeframe):
20‑Period EMA: {market_state.get('context_ema20', 0):.3f} vs. 50‑Period EMA: {market_state.get('context_ema50', 0):.3f}
3‑Period ATR: {market_state.get('context_atr3', 0):.3f} vs. 14‑Period ATR: {market_state.get('context_atr14', 0):.3f}
Current Volume: {market_state.get('context_volume', 0):.3f} vs. Average Volume: {market_state.get('context_avg_volume', 0):.3f}
MACD indicators: {self._format_series(market_state.get('context_macd_series', []))}
RSI indicators (14‑Period): {self._format_series(market_state.get('context_rsi14_series', []))}
"""
        
        # Add account information section
        total_return_pct = ((self.capital - self.config.initial_balance) / self.config.initial_balance) * 100
        prompt += f"""
HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE
Current Total Return (percent): {total_return_pct:.2f}%
Available Cash: {self.free_capital:.2f}
Current Account Value: {self.capital:.2f}
Current live positions & performance: {self._format_positions()}
"""
        
        return prompt
    
    def _format_series(self, series: List) -> str:
        """Format series data for prompt"""
        if not series:
            return "[]"
        return "[" + ", ".join([f"{x:.3f}" if isinstance(x, (int, float)) else str(x) for x in series]) + "]"
    
    def _format_positions(self) -> str:
        """Format current positions for prompt"""
        if not self.positions:
            return "No open positions"
        
        lines = []
        for asset, pos in self.positions.items():
            pnl_sign = "+" if pos['pnl'] >= 0 else ""
            lines.append(f"- {asset}: ${pos['size']:,.2f} @ ${pos['entry_price']:.2f} | Current: ${pos['current_price']:.2f} | PnL: {pnl_sign}${pos['pnl']:.2f} ({pnl_sign}{pos['pnl_pct']:.2f}%)")
        return "\n".join(lines)
    
    def get_portfolio_status(self) -> Dict:
        """Get current portfolio status"""
        return {
            'capital': self.capital,
            'free_capital': self.free_capital,
            'allocated_capital': self.capital - self.free_capital,
            'positions': self.positions,
            'position_count': len(self.positions),
            'max_positions': self.config.max_positions,
            'total_pnl': sum(pos['pnl'] for pos in self.positions.values()),
            'total_pnl_pct': ((self.capital - self.config.initial_balance) / self.config.initial_balance) * 100
        }
    
    def _parse_response(self, response: str) -> tuple:
        """Parse model response"""
        signal = "HOLD"
        confidence = 50
        reasoning = ""
        
        lines = response.split('\n')
        reasoning_started = False
        reasoning_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            
            if line_stripped.startswith('SIGNAL:'):
                signal = line_stripped.replace('SIGNAL:', '').strip().upper()
                if 'BUY' in signal:
                    signal = 'BUY'
                elif 'SELL' in signal:
                    signal = 'SELL'
                else:
                    signal = 'HOLD'
                reasoning_started = False
            elif line_stripped.startswith('CONFIDENCE:'):
                try:
                    confidence = int(line_stripped.replace('CONFIDENCE:', '').replace('%', '').strip())
                except:
                    confidence = 50
                reasoning_started = False
            elif line_stripped.startswith('REASONING:'):
                reasoning_started = True
                # Get reasoning from same line if present
                reasoning_text = line_stripped.replace('REASONING:', '').strip()
                if reasoning_text:
                    reasoning_lines.append(reasoning_text)
            elif reasoning_started and line_stripped:
                # Continue capturing reasoning lines until we hit another section or empty line
                if not any(line_stripped.startswith(prefix) for prefix in ['SIGNAL:', 'CONFIDENCE:', 'RISK:', 'NEXT:']):
                    reasoning_lines.append(line_stripped)
        
        # Join all reasoning lines
        reasoning = ' '.join(reasoning_lines)
        
        return signal, confidence, reasoning
    
    def _aggregate_decisions(self, decisions: Dict) -> Dict:
        """Aggregate decisions from multiple models"""
        if not decisions:
            return {'signal': 'HOLD', 'confidence': 0, 'reasoning': 'No models available', 'models_used': []}
        
        # Simple majority vote
        signals = [d['signal'] for d in decisions.values()]
        confidences = [d['confidence'] for d in decisions.values()]
        model_names = list(decisions.keys())
        
        # Most common signal
        signal_counts = {}
        for sig in signals:
            signal_counts[sig] = signal_counts.get(sig, 0) + 1
        
        final_signal = max(signal_counts, key=signal_counts.get)
        avg_confidence = sum(confidences) / len(confidences)
        
        # Get prompt and response from first model (they're all the same prompt)
        first_decision = list(decisions.values())[0]
        
        # Build reasoning - use actual reasoning from model, not just model name
        if len(model_names) == 1:
            # Use the actual reasoning from the single model
            reasoning_text = first_decision.get('reasoning', model_names[0].upper())
        else:
            # For multiple models, aggregate their reasoning
            reasoning_parts = [f"{name.upper()}: {decisions[name].get('reasoning', 'N/A')}" for name in model_names]
            reasoning_text = " | ".join(reasoning_parts)
        
        return {
            'signal': final_signal,
            'confidence': int(avg_confidence),
            'reasoning': reasoning_text,
            'model_count': len(decisions),
            'models_used': model_names,
            'prompt': first_decision.get('prompt', ''),
            'response': first_decision.get('raw_response', ''),
            'system_prompt': first_decision.get('system_prompt', '')
        }
    
    def _save_decision(self, decision: Dict):
        """Save decision to session file"""
        try:
            save_data = {k: v for k, v in decision.items() if k != 'market_state'}
            self.session_decisions.append(save_data)
            
            with open(self.session_file, 'w') as f:
                json.dump({
                    'session_id': self.session_id,
                    'config': self.config.to_dict(),
                    'session_start': self.start_time.isoformat(),
                    'decisions_count': len(self.session_decisions),
                    'decisions': self.session_decisions
                }, f, indent=2)
            
            cprint(f"💾 Saved to {self.session_file.name} ({len(self.session_decisions)} total)", "blue")
        except Exception as e:
            cprint(f"⚠️ Error saving: {e}", "yellow")
    
    def run_continuous(self):
        """Run continuous trading"""
        cprint(f"\n🚀 Starting continuous mode...", "green", attrs=['bold'])
        cprint(f"⏱️  Interval: {self.config.get_cycle_display()}", "yellow")
        cprint(f"📁 Session: {self.session_file.name}\n", "yellow")
        
        cycle = 0
        try:
            while True:
                cycle += 1
                cprint(f"\n{'='*70}", "magenta")
                cprint(f"🔄 CYCLE #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "magenta", attrs=['bold'])
                cprint(f"{'='*70}", "magenta")
                
                market_state = self.get_market_state()
                decision = self.make_decision(market_state)
                
                cprint(f"\n📊 Final Decision: {decision['signal']} ({decision['confidence']}%)", "cyan", attrs=['bold'])
                cprint(f"💭 {decision['reasoning']}", "white")
                
                cprint(f"\n⏳ Waiting {self.config.cycle_interval}s...", "yellow")
                time.sleep(self.config.cycle_interval)
                
        except KeyboardInterrupt:
            cprint(f"\n\n{'='*70}", "red")
            cprint(f"👋 Stopped after {cycle} cycles", "red", attrs=['bold'])
            cprint(f"📁 All decisions in: {self.session_file}", "red")
            cprint(f"{'='*70}", "red")


def main():
    """Main entry point"""
    # Example: Create config and run
    config = TradingConfig(
        models=["deepseek"],
        asset_type="crypto",
        ticker="BTC",
        timeframe="3m",
        cycle_interval=180
    )
    
    agent = UniversalTradingAgent(config)
    agent.run_continuous()


if __name__ == "__main__":
    main()
