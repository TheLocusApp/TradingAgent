#!/usr/bin/env python3
"""
🌙 Moon Dev's Deepseek Bitcoin Trading Agent 🌙

Real-time Bitcoin trading using Deepseek Chat v3.1 for decision-making.
Analyzes market state, indicators, and account information to generate trading signals.

The model receives raw market data and decides strategy independently.
Includes simulation mode with P&L tracking and memory across trading cycles.

Usage:
    python src/agents/deepseek_btc_trader.py

Configuration:
    - Model: deepseek-chat (v3.1)
    - Asset: Bitcoin (BTC)
    - Data: Market state, indicators, account info
    - Output: BUY, SELL, or HOLD with reasoning
    - Simulation: Full P&L tracking, win rate, trade history

Built with love by Moon Dev 🚀
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from termcolor import cprint, colored
from dotenv import load_dotenv

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import ONLY Deepseek model directly to avoid initializing all models
from src.models.deepseek_model import DeepSeekModel

# ============================================================================
# CONFIGURATION
# ============================================================================

# Model settings
MODEL_TYPE = "deepseek"
MODEL_NAME = "deepseek-chat"  # v3.1
TEMPERATURE = 0.7  # Balanced between reasoning and consistency
MAX_TOKENS = 1024

# Trading settings
POSITION_SIZE_PERCENTAGE = 0.9  # 90% of account
STOP_LOSS_PERCENTAGE = 2.0  # 2% stop loss
TAKE_PROFIT_PERCENTAGE = 5.0  # 5% take profit

# Execution settings
SLEEP_BETWEEN_CYCLES = 180  # Seconds between trading cycles (180s = 3-minute candles)
SAVE_DECISIONS = True
DECISIONS_DIR = Path(project_root) / "src" / "data" / "deepseek_btc_decisions"
SESSION_FILE = None  # Will be set when continuous mode starts

# ============================================================================
# SYSTEM PROMPT (with objective and memory context)
# ============================================================================

def get_system_prompt(trading_stats: Optional[Dict] = None) -> str:
    """Generate system prompt with dynamic trading context"""
    
    base_prompt = """You are an expert Bitcoin trading AI powered by Deepseek.

Your role is to analyze real-time market data and make trading decisions on 3-MINUTE CANDLES.

OBJECTIVE: Maximize risk-adjusted returns on 3-minute timeframe.

DECISION FRAMEWORK:
1. Analyze the current market state (price, indicators, open interest, funding)
2. Review the 3-minute candle price action and technical indicators (RSI, MACD, EMA)
3. Consider longer-term context (4-hour timeframe for trend confirmation)
4. Evaluate account status and risk metrics
5. Generate a trading signal: BUY, SELL, or HOLD

TIMEFRAME FOCUS: You are analyzing 3-minute candles. Look for:
- Quick reversals and momentum shifts
- RSI(7) for short-term overbought/oversold conditions
- MACD crossovers for momentum changes
- EMA(20) as dynamic support/resistance
- Volume confirmation on 3-minute bars

SIGNAL DEFINITIONS:
- BUY: Strong bullish signals, recommend opening/increasing long position
- SELL: Bearish signals or risk management, recommend closing position
- HOLD: Neutral/unclear signals, maintain current position

RESPONSE FORMAT:
Provide your response in exactly this format:

SIGNAL: [BUY/SELL/HOLD]
CONFIDENCE: [0-100]%
REASONING: [2-3 sentences explaining your decision]
RISK_LEVEL: [LOW/MEDIUM/HIGH]
NEXT_LEVELS: Entry/Exit levels if applicable

Be concise, data-driven, and focus on actionable insights."""

    # Add trading memory/context if available
    if trading_stats:
        memory_context = f"""

TRADING MEMORY & PERFORMANCE:
- Time Running: {trading_stats.get('time_running_minutes', 0)} minutes
- Total Invocations: {trading_stats.get('total_invocations', 0)}
- Trades Executed: {trading_stats.get('total_trades', 0)}
- Win Rate: {trading_stats.get('win_rate', 0):.1f}%
- Total P&L: ${trading_stats.get('total_pnl', 0):,.2f}
- Account Balance: ${trading_stats.get('account_balance', 0):,.2f}
- Max Drawdown: {trading_stats.get('max_drawdown', 0):.2f}%

Use this context to inform your decisions. Avoid repeating losing patterns."""
        return base_prompt + memory_context
    
    return base_prompt

# ============================================================================
# DEEPSEEK BTC TRADER CLASS
# ============================================================================

class DeepseekBTCTrader:
    """Bitcoin trading agent powered by Deepseek Chat v3.1"""

    def __init__(self, use_simulation: bool = True, initial_balance: float = 10000.0, session_id: Optional[str] = None):
        """
        Initialize the trading agent
        
        Args:
            use_simulation: Enable simulation mode with P&L tracking
            initial_balance: Starting account balance for simulation
            session_id: Optional session ID for grouping decisions in one file
        """
        cprint("\n" + "="*70, "cyan")
        cprint("🌙 Moon Dev's Deepseek Bitcoin Trading Agent 🌙", "cyan", attrs=['bold'])
        cprint("="*70, "cyan")

        # Load environment
        load_dotenv()

        # Initialize ONLY Deepseek model (avoid initializing all models)
        cprint("\n🤖 Initializing Deepseek Chat v3.1 (direct import)...", "cyan")
        try:
            api_key = os.getenv("DEEPSEEK_KEY")
            if not api_key:
                cprint("❌ DEEPSEEK_KEY not found in environment!", "red")
                sys.exit(1)
            
            self.model = DeepSeekModel(api_key)
            cprint(f"✅ Model initialized: {self.model.model_name}", "green")
        except Exception as e:
            cprint(f"❌ Failed to initialize Deepseek model: {e}", "red")
            sys.exit(1)

        # Create decisions directory
        if SAVE_DECISIONS:
            DECISIONS_DIR.mkdir(parents=True, exist_ok=True)
            cprint(f"📁 Decisions will be saved to: {DECISIONS_DIR}", "yellow")

        # Session-based file logging
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = DECISIONS_DIR / f"session_{self.session_id}.json"
        self.session_decisions = []  # In-memory buffer

        # Trading state
        self.last_signal = None
        self.last_decision_time = None
        self.decision_count = 0
        self.start_time = datetime.now()

        # Simulation mode
        self.use_simulation = use_simulation
        self.trades: List[Dict] = []  # Trade history
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.current_position = None  # {'entry_price': X, 'quantity': Y, 'entry_time': Z}
        self.position_entry_price = None
        
        if use_simulation:
            cprint(f"\n💰 SIMULATION MODE ENABLED", "yellow", attrs=['bold'])
            cprint(f"   Initial Balance: ${initial_balance:,.2f}", "yellow")
        
        cprint("\n✨ Agent ready for trading!", "green", attrs=['bold'])

    def format_market_data(self, market_state: Dict) -> str:
        """
        Format market data into a readable prompt for the model.

        Args:
            market_state: Dict containing all market data

        Returns:
            Formatted string for the model
        """
        formatted = f"""
CURRENT MARKET STATE FOR BITCOIN
═══════════════════════════════════════════════════════════

CURRENT SNAPSHOT:
  Price: ${market_state.get('current_price', 0):,.2f}
  EMA(20): ${market_state.get('current_ema20', 0):,.2f}
  MACD: {market_state.get('current_macd', 0):.3f}
  RSI(7): {market_state.get('current_rsi_7', 0):.2f}

PERPETUALS MARKET:
  Open Interest: ${market_state.get('open_interest_latest', 0):,.2f}
    (Average: ${market_state.get('open_interest_avg', 0):,.2f})
  Funding Rate: {market_state.get('funding_rate', 0):.2e}

INTRADAY SERIES (oldest → latest):
"""
        # Add intraday data
        if 'mid_prices' in market_state:
            formatted += f"\n  Mid Prices: {market_state['mid_prices']}"
        if 'ema_20' in market_state:
            formatted += f"\n  EMA(20): {market_state['ema_20']}"
        if 'macd' in market_state:
            formatted += f"\n  MACD: {market_state['macd']}"
        if 'rsi_7' in market_state:
            formatted += f"\n  RSI(7): {market_state['rsi_7']}"
        if 'rsi_14' in market_state:
            formatted += f"\n  RSI(14): {market_state['rsi_14']}"

        # Add longer-term context
        formatted += f"""

LONGER-TERM CONTEXT (4-hour timeframe):
  EMA(20): ${market_state.get('ema_20_4h', 0):,.2f}
  EMA(50): ${market_state.get('ema_50_4h', 0):,.2f}
  ATR(3): {market_state.get('atr_3_4h', 0):.2f}
  ATR(14): {market_state.get('atr_14_4h', 0):.2f}
  Current Volume: {market_state.get('volume_current_4h', 0):.2f}
  Average Volume: {market_state.get('volume_avg_4h', 0):.2f}
  MACD(4h): {market_state.get('macd_4h', [])}
  RSI(14, 4h): {market_state.get('rsi_14_4h', [])}

ACCOUNT INFORMATION:
  Time Running: {market_state.get('time_running_minutes', 0)} minutes
  Current Time: {market_state.get('current_time', 'N/A')}
  Invocations: {market_state.get('invocations', 0)}
  Account Balance: ${market_state.get('account_balance', 0):,.2f}
  Current Position: {market_state.get('current_position', 'None')}
  Position P&L: {market_state.get('position_pnl', 'N/A')}
"""
        return formatted

    def parse_signal(self, response: str) -> Tuple[str, int, str, str, str]:
        """
        Parse the model's response into structured signal data.

        Args:
            response: Raw response from Deepseek model

        Returns:
            Tuple of (signal, confidence, reasoning, risk_level, next_levels)
        """
        try:
            lines = response.strip().split('\n')
            signal = "HOLD"
            confidence = 0
            reasoning = ""
            risk_level = "MEDIUM"
            next_levels = ""

            for line in lines:
                line = line.strip()
                if line.startswith('SIGNAL:'):
                    signal = line.replace('SIGNAL:', '').strip().upper()
                    # Normalize to BUY/SELL/HOLD
                    if 'BUY' in signal:
                        signal = 'BUY'
                    elif 'SELL' in signal:
                        signal = 'SELL'
                    else:
                        signal = 'HOLD'
                elif line.startswith('CONFIDENCE:'):
                    try:
                        conf_str = line.replace('CONFIDENCE:', '').strip().replace('%', '')
                        confidence = int(float(conf_str))
                    except:
                        confidence = 50
                elif line.startswith('REASONING:'):
                    reasoning = line.replace('REASONING:', '').strip()
                elif line.startswith('RISK_LEVEL:'):
                    risk_level = line.replace('RISK_LEVEL:', '').strip()
                elif line.startswith('NEXT_LEVELS:'):
                    next_levels = line.replace('NEXT_LEVELS:', '').strip()

            return signal, confidence, reasoning, risk_level, next_levels

        except Exception as e:
            cprint(f"⚠️ Error parsing signal: {e}", "yellow")
            return "HOLD", 0, "Parse error", "MEDIUM", ""

    def get_trading_stats(self) -> Dict:
        """Get current trading statistics for memory context"""
        time_running = (datetime.now() - self.start_time).total_seconds() / 60
        
        if not self.trades:
            win_rate = 0.0
            total_pnl = 0.0
            max_drawdown = 0.0
        else:
            winning_trades = sum(1 for t in self.trades if t.get('pnl', 0) > 0)
            win_rate = (winning_trades / len(self.trades)) * 100
            total_pnl = sum(t.get('pnl', 0) for t in self.trades)
            
            # Calculate max drawdown
            balance_history = [self.initial_balance]
            for trade in self.trades:
                balance_history.append(balance_history[-1] + trade.get('pnl', 0))
            
            peak = balance_history[0]
            max_drawdown = 0.0
            for balance in balance_history:
                if balance < peak:
                    drawdown = ((peak - balance) / peak) * 100
                    max_drawdown = max(max_drawdown, drawdown)
                peak = max(peak, balance)
        
        return {
            'time_running_minutes': int(time_running),
            'total_invocations': self.decision_count,
            'total_trades': len(self.trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'account_balance': self.current_balance,
            'max_drawdown': max_drawdown
        }

    def execute_simulation_trade(self, signal: str, market_state: Dict) -> Optional[Dict]:
        """
        Execute a simulated trade based on signal.
        
        Args:
            signal: BUY, SELL, or HOLD
            market_state: Current market data
            
        Returns:
            Trade record if executed, None otherwise
        """
        if not self.use_simulation:
            return None
        
        current_price = market_state.get('current_price', 0)
        
        if signal == 'BUY' and not self.current_position:
            # Open long position
            position_size = (self.current_balance * POSITION_SIZE_PERCENTAGE) / current_price
            self.current_position = {
                'entry_price': current_price,
                'quantity': position_size,
                'entry_time': datetime.now(),
                'type': 'long'
            }
            self.position_entry_price = current_price
            
            cprint(f"\n💚 SIMULATION: BUY executed", "green", attrs=['bold'])
            cprint(f"   Entry Price: ${current_price:,.2f}", "green")
            cprint(f"   Position Size: {position_size:.4f} BTC", "green")
            
            return {
                'type': 'entry',
                'signal': 'BUY',
                'entry_price': current_price,
                'quantity': position_size,
                'timestamp': datetime.now().isoformat()
            }
        
        elif signal == 'SELL' and self.current_position:
            # Close long position
            exit_price = current_price
            quantity = self.current_position['quantity']
            entry_price = self.current_position['entry_price']
            
            pnl = (exit_price - entry_price) * quantity
            pnl_percent = ((exit_price - entry_price) / entry_price) * 100
            
            self.current_balance += pnl
            
            trade_record = {
                'entry_price': entry_price,
                'exit_price': exit_price,
                'quantity': quantity,
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'entry_time': self.current_position['entry_time'].isoformat(),
                'exit_time': datetime.now().isoformat(),
                'type': 'long'
            }
            
            self.trades.append(trade_record)
            self.current_position = None
            
            color = 'green' if pnl > 0 else 'red'
            cprint(f"\n❤️ SIMULATION: SELL executed", color, attrs=['bold'])
            cprint(f"   Exit Price: ${exit_price:,.2f}", color)
            cprint(f"   P&L: ${pnl:,.2f} ({pnl_percent:+.2f}%)", color)
            cprint(f"   New Balance: ${self.current_balance:,.2f}", color)
            
            return trade_record
        
        return None

    def make_decision(self, market_state: Dict) -> Dict:
        """
        Analyze market data and make a trading decision.

        Args:
            market_state: Dict containing all market data

        Returns:
            Dict with signal, confidence, reasoning, etc.
        """
        try:
            cprint("\n" + "─"*70, "cyan")
            cprint(f"🤖 Analyzing market data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "cyan", attrs=['bold'])
            cprint("─"*70, "cyan")

            # Format market data for model
            formatted_data = self.format_market_data(market_state)

            cprint("\n📊 Sending to Deepseek Chat v3.1...", "yellow")

            # Get dynamic system prompt with trading memory
            trading_stats = self.get_trading_stats()
            system_prompt = get_system_prompt(trading_stats)

            # Query the model
            response = self.model.generate_response(
                system_prompt=system_prompt,
                user_content=formatted_data,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS
            )

            # Extract text from response
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)

            cprint("✅ Response received from Deepseek", "green")

            # Parse the signal
            signal, confidence, reasoning, risk_level, next_levels = self.parse_signal(response_text)

            # Create decision record
            decision = {
                'timestamp': datetime.now().isoformat(),
                'signal': signal,
                'confidence': confidence,
                'reasoning': reasoning,
                'risk_level': risk_level,
                'next_levels': next_levels,
                'market_state': market_state,
                'raw_response': response_text
            }

            # Display decision
            self._display_decision(decision)

            # Execute simulation trade if enabled
            if self.use_simulation:
                trade_result = self.execute_simulation_trade(signal, market_state)
                decision['simulation_trade'] = trade_result

            # Save decision if enabled
            if SAVE_DECISIONS:
                self._save_decision(decision)

            self.last_signal = signal
            self.last_decision_time = datetime.now()
            self.decision_count += 1

            return decision

        except Exception as e:
            cprint(f"❌ Error making decision: {e}", "red")
            import traceback
            traceback.print_exc()
            return {
                'timestamp': datetime.now().isoformat(),
                'signal': 'HOLD',
                'confidence': 0,
                'reasoning': f'Error: {str(e)}',
                'risk_level': 'HIGH',
                'next_levels': '',
                'error': str(e)
            }

    def _display_decision(self, decision: Dict):
        """Display the trading decision in a formatted way"""
        signal = decision['signal']
        confidence = decision['confidence']
        reasoning = decision['reasoning']
        risk_level = decision['risk_level']

        # Color code by signal
        if signal == 'BUY':
            signal_color = 'green'
            signal_emoji = '🟢'
        elif signal == 'SELL':
            signal_color = 'red'
            signal_emoji = '🔴'
        else:
            signal_color = 'yellow'
            signal_emoji = '🟡'

        cprint("\n" + "="*70, signal_color)
        cprint(f"{signal_emoji} TRADING SIGNAL: {signal}", signal_color, attrs=['bold'])
        cprint("="*70, signal_color)

        cprint(f"\n📊 Confidence: {confidence}%", "white")
        cprint(f"⚠️  Risk Level: {risk_level}", "white")
        cprint(f"\n💭 Reasoning:", "cyan")
        cprint(f"   {reasoning}", "white")

        if decision.get('next_levels'):
            cprint(f"\n🎯 Next Levels:", "cyan")
            cprint(f"   {decision['next_levels']}", "white")

        cprint("\n" + "="*70 + "\n", signal_color)

    def display_trading_stats(self):
        """Display current trading statistics"""
        stats = self.get_trading_stats()
        
        cprint("\n" + "="*70, "cyan")
        cprint("📊 TRADING STATISTICS", "cyan", attrs=['bold'])
        cprint("="*70, "cyan")
        
        cprint(f"\n⏱️  Time Running: {stats['time_running_minutes']} minutes", "white")
        cprint(f"🔄 Total Invocations: {stats['total_invocations']}", "white")
        cprint(f"📈 Total Trades: {stats['total_trades']}", "white")
        
        if stats['total_trades'] > 0:
            cprint(f"✅ Win Rate: {stats['win_rate']:.1f}%", "green" if stats['win_rate'] >= 50 else "red")
            cprint(f"💰 Total P&L: ${stats['total_pnl']:,.2f}", "green" if stats['total_pnl'] >= 0 else "red")
            cprint(f"📉 Max Drawdown: {stats['max_drawdown']:.2f}%", "yellow")
        
        cprint(f"💵 Account Balance: ${stats['account_balance']:,.2f}", "cyan", attrs=['bold'])
        
        if self.current_position:
            entry_price = self.current_position['entry_price']
            current_price = self.current_position.get('current_price', entry_price)
            unrealized_pnl = (current_price - entry_price) * self.current_position['quantity']
            unrealized_pnl_pct = ((current_price - entry_price) / entry_price) * 100
            
            color = 'green' if unrealized_pnl > 0 else 'red'
            cprint(f"\n📍 Open Position:", color, attrs=['bold'])
            cprint(f"   Entry: ${entry_price:,.2f}", color)
            cprint(f"   Unrealized P&L: ${unrealized_pnl:,.2f} ({unrealized_pnl_pct:+.2f}%)", color)
        
        cprint("\n" + "="*70 + "\n", "cyan")

    def _save_decision(self, decision: Dict):
        """Save decision to session file (one file per continuous run)"""
        try:
            # Remove market_state from saved file (too large)
            save_data = {k: v for k, v in decision.items() if k != 'market_state'}
            
            # Add to in-memory buffer
            self.session_decisions.append(save_data)
            
            # Write all decisions to session file
            with open(self.session_file, 'w') as f:
                json.dump({
                    'session_id': self.session_id,
                    'session_start': self.start_time.isoformat(),
                    'decisions_count': len(self.session_decisions),
                    'decisions': self.session_decisions
                }, f, indent=2)

            cprint(f"💾 Decision saved to session: {self.session_file.name} ({len(self.session_decisions)} total)", "blue")

        except Exception as e:
            cprint(f"⚠️ Error saving decision: {e}", "yellow")

    def run_once(self, market_state: Dict) -> Dict:
        """
        Run a single trading cycle.

        Args:
            market_state: Dict containing all market data

        Returns:
            Trading decision
        """
        return self.make_decision(market_state)

    def run_continuous(self, market_state_provider=None):
        """
        Run continuous trading cycles.

        Args:
            market_state_provider: Optional function that returns market_state dict
        """
        cprint("\n🚀 Starting continuous trading mode (3-minute candles)...", "green", attrs=['bold'])
        cprint(f"⏱️  Cycle interval: {SLEEP_BETWEEN_CYCLES} seconds (3-minute candles)", "yellow")
        cprint(f"💰 Simulation Mode: {'ENABLED' if self.use_simulation else 'DISABLED'}", "yellow")
        cprint(f"📁 Session file: {self.session_file.name}\n", "yellow")

        cycle = 0
        try:
            while True:
                cycle += 1
                cprint(f"\n{'='*70}", "magenta")
                cprint(f"🔄 CYCLE #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "magenta", attrs=['bold'])
                cprint(f"{'='*70}", "magenta")

                # Get market state
                if market_state_provider:
                    market_state = market_state_provider()
                else:
                    cprint("⚠️ No market state provider - using example data", "yellow")
                    market_state = self._get_example_market_state()

                # Make decision
                decision = self.make_decision(market_state)

                # Display stats every 5 cycles
                if cycle % 5 == 0:
                    self.display_trading_stats()

                # Sleep before next cycle
                cprint(f"\n⏳ Waiting {SLEEP_BETWEEN_CYCLES}s for next 3-minute candle...", "yellow")
                time.sleep(SLEEP_BETWEEN_CYCLES)

        except KeyboardInterrupt:
            cprint(f"\n\n{'='*70}", "red")
            cprint(f"👋 Trading stopped after {cycle} cycles", "red", attrs=['bold'])
            cprint(f"📁 All decisions saved to: {self.session_file}", "red")
            cprint(f"{'='*70}", "red")
            
            # Display final stats
            self.display_trading_stats()

    def _get_example_market_state(self) -> Dict:
        """Return example market state for testing"""
        return {
            'current_price': 113793.5,
            'current_ema20': 113767.331,
            'current_macd': -50.596,
            'current_rsi_7': 53.606,
            'open_interest_latest': 29998.08,
            'open_interest_avg': 29903.69,
            'funding_rate': 1.25e-05,
            'mid_prices': [113854.5, 113844.0, 113648.5, 113728.5, 113600.0, 113566.5, 113659.5, 113690.0, 113724.5, 113793.5],
            'ema_20': [113877.996, 113872.949, 113847.811, 113839.638, 113815.863, 113791.21, 113776.333, 113769.92, 113767.261, 113767.331],
            'macd': [-3.038, -7.259, -27.715, -31.22, -47.332, -62.048, -66.648, -63.59, -57.836, -50.596],
            'rsi_7': [41.42, 39.092, 18.709, 43.188, 30.961, 29.115, 39.121, 47.346, 50.805, 53.606],
            'rsi_14': [45.753, 44.66, 31.289, 44.064, 35.968, 34.653, 40.218, 45.004, 47.04, 48.653],
            'ema_20_4h': 113270.82,
            'ema_50_4h': 111844.96,
            'atr_3_4h': 392.748,
            'atr_14_4h': 563.173,
            'volume_current_4h': 29.931,
            'volume_avg_4h': 4682.793,
            'macd_4h': [889.972, 961.709, 1082.258, 1206.811, 1325.662, 1391.865, 1399.553, 1374.151, 1277.883, 1172.022],
            'rsi_14_4h': [69.947, 68.424, 72.327, 74.258, 75.761, 74.188, 70.412, 68.365, 60.885, 59.065],
            'time_running_minutes': 8223,
            'current_time': datetime.now().isoformat(),
            'invocations': 3239,
            'account_balance': 10000.0,
            'current_position': None,
            'position_pnl': None
        }


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    import sys
    
    # Check for command line arguments
    use_continuous = '--continuous' in sys.argv
    use_simulation = '--no-sim' not in sys.argv
    
    # Initialize agent with simulation enabled
    agent = DeepseekBTCTrader(use_simulation=use_simulation, initial_balance=10000.0)

    if use_continuous:
        # Run continuous trading mode (3-minute candles)
        cprint("\n📝 Running in CONTINUOUS mode (3-minute candles)...", "yellow", attrs=['bold'])
        cprint("   Press Ctrl+C to stop", "yellow")
        cprint("   All decisions will be saved to ONE session file\n", "yellow")
        agent.run_continuous()
    else:
        # Run single decision with example data
        cprint("\n📝 Running SINGLE DECISION with example market data...", "yellow", attrs=['bold'])
        cprint("   Analyzing 3-minute candle data\n", "yellow")
        market_state = agent._get_example_market_state()

        # Make a single decision
        decision = agent.run_once(market_state)

        cprint("\n✅ Example decision complete!", "green", attrs=['bold'])
        cprint(f"Signal: {decision['signal']}", "cyan")
        cprint(f"Confidence: {decision['confidence']}%", "cyan")
        
        # Display stats
        agent.display_trading_stats()
        
        cprint("\n💡 Commands:", "blue")
        cprint("   Continuous mode (3-min candles): python src/agents/deepseek_btc_trader.py --continuous", "blue")
        cprint("   Continuous without simulation: python src/agents/deepseek_btc_trader.py --continuous --no-sim", "blue")


if __name__ == "__main__":
    main()
