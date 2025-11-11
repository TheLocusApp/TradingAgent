"""
🎮 Simulated Trading Engine
Tracks simulated trades, positions, and performance for agent comparison
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import math


class SimulatedTradingEngine:
    """Manages simulated trading for an agent"""
    
    def __init__(self, agent_id: str, agent_name: str, initial_balance: float = 10000.0, force_fresh_start: bool = False, asset_type: str = "crypto"):
        """Initialize simulated trading engine
        
        Args:
            agent_id: Unique agent identifier
            agent_name: Human-readable agent name
            initial_balance: Starting capital
            force_fresh_start: If True, ignore existing state and start fresh
            asset_type: Type of asset (crypto, stock, options)
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.asset_type = asset_type
        self.positions: Dict[str, dict] = {}  # {symbol: {qty, entry_price, entry_time, entry_value, option_type, strike, expiration}}
        self.trades_history: List[dict] = []
        self.pnl_history: List[dict] = []
        self.decisions_log: List[dict] = []
        
        # Performance tracking
        self.peak_value = initial_balance
        self.max_drawdown = 0.0
        
        # Create data directory
        self.data_dir = Path(__file__).parent.parent / "data" / "simulated_trades"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.data_dir / f"{agent_id}_state.json"
        
        # Load existing state if available (unless force_fresh_start)
        if force_fresh_start:
            print(f" Starting fresh for {agent_id} - ignoring old state")
            if self.state_file.exists():
                self.state_file.unlink()  # Delete old state file
        else:
            self._load_state()
        
    def _load_state(self):
        """Load saved state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    
                    # Check if initial_balance changed (user updated config)
                    saved_initial_balance = state.get('initial_balance', self.initial_balance)
                    if saved_initial_balance != self.initial_balance:
                        print(f" Initial balance changed from ${saved_initial_balance:,.2f} to ${self.initial_balance:,.2f}")
                        print(f"   Starting fresh with new balance...")
                        # Don't load old state if balance changed - start fresh
                        return
                    
                    self.balance = state.get('balance', self.initial_balance)
                    self.positions = state.get('positions', {})
                    self.trades_history = state.get('trades_history', [])
                    self.pnl_history = state.get('pnl_history', [])
                    self.decisions_log = state.get('decisions_log', [])
                    self.peak_value = state.get('peak_value', self.initial_balance)
                    self.max_drawdown = state.get('max_drawdown', 0.0)
                    print(f" Loaded state for {self.agent_id}: Balance ${self.balance:,.2f}")
            except Exception as e:
                print(f" Error loading state for {self.agent_id}: {e}")
    
    def _save_state(self):
        """Save current state to file"""
        try:
            state = {
                'agent_id': self.agent_id,
                'agent_name': self.agent_name,
                'initial_balance': self.initial_balance,
                'balance': self.balance,
                'positions': self.positions,
                'trades_history': self.trades_history,
                'pnl_history': self.pnl_history,
                'decisions_log': self.decisions_log,
                'peak_value': self.peak_value,
                'max_drawdown': self.max_drawdown,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving state for {self.agent_id}: {e}")
    
    def log_decision(self, signal: str, symbol: str, price: float, confidence: int, reasoning: str):
        """Log an agent decision (whether or not it results in a trade)"""
        decision = {
            'timestamp': datetime.now().isoformat(),
            'signal': signal,
            'symbol': symbol,
            'price': price,
            'confidence': confidence,
            'reasoning': reasoning,
            'executed': False
        }
        self.decisions_log.append(decision)
        self._save_state()
        return decision
    
    def execute_signal(self, signal: str, symbol: str, current_price: float, 
                       confidence: int = 0, reasoning: str = "") -> Optional[dict]:
        """
        Execute a trading signal (BUY/SELL/HOLD)
        Returns trade details if executed, None if not
        """
        # Log the decision
        decision = self.log_decision(signal, symbol, current_price, confidence, reasoning)
        
        if signal == 'BUY':
            return self.execute_buy(decision, symbol, current_price)
        elif signal == 'SELL':
            return self._execute_sell(symbol, current_price, decision)
        else:  # HOLD or other
            return None
    
    def execute_buy(self, decision: Dict, symbol: str, price: float, option_type: str = None, strike: float = None, expiration: str = None) -> Optional[Dict]:
        """Execute a BUY order - can add to existing position
        
        Args:
            decision: Decision dict
            symbol: Symbol to buy (stock/crypto ticker or option contract ticker)
            price: Price per unit (stock price or option premium)
            option_type: For options: 'CALL' or 'PUT'
            strike: For options: strike price
            expiration: For options: expiration date
        """
        # For options, calculate position size differently (fixed number of contracts)
        if self.asset_type == "options":
            # Buy 1-2 contracts based on balance
            num_contracts = 2 if self.balance > 5000 else 1
            position_size = price * 100 * num_contracts  # Premium * 100 shares per contract * num contracts
            qty = num_contracts
        else:
            # Calculate position size (10% of available balance)
            position_size = self.balance * 0.10
            qty = position_size / price
        
        # Need minimum balance - CRITICAL CHECK
        if position_size < 100:
            print(f" {self.agent_name}: Insufficient funds for BUY. Balance: ${self.balance:.2f}, Required: $100")
            return None
        
        # Additional safety check: ensure we have enough balance
        if self.balance < position_size:
            print(f" {self.agent_name}: Balance ${self.balance:.2f} < Position size ${position_size:.2f}")
            return None
        
        # Check if we already have a position - if so, add to it (average in)
        if symbol in self.positions:
            existing_pos = self.positions[symbol]
            old_qty = existing_pos['qty']
            old_value = existing_pos['entry_value']
            old_price = existing_pos['entry_price']
            
            # Calculate new average entry price
            new_total_qty = old_qty + qty
            new_total_value = old_value + position_size
            new_avg_price = new_total_value / new_total_qty
            
            if self.asset_type == "options":
                print(f" {self.agent_name}: Adding to {symbol} {option_type} position")
                print(f"   Old: {old_qty:.0f} contracts @ ${old_price:.2f} = ${old_value:.2f}")
                print(f"   New: {qty:.0f} contracts @ ${price:.2f} = ${position_size:.2f}")
                print(f"   Total: {new_total_qty:.0f} contracts @ ${new_avg_price:.2f} = ${new_total_value:.2f}")
            else:
                print(f" {self.agent_name}: Adding to {symbol} position")
                print(f"   Old: {old_qty:.6f} @ ${old_price:.2f} = ${old_value:.2f}")
                print(f"   New: {qty:.6f} @ ${price:.2f} = ${position_size:.2f}")
                print(f"   Total: {new_total_qty:.6f} @ ${new_avg_price:.2f} = ${new_total_value:.2f}")
            
            # Update position with new totals
            position_data = {
                'qty': new_total_qty,
                'entry_price': new_avg_price,
                'entry_time': existing_pos['entry_time'],  # Keep original entry time
                'entry_value': new_total_value
            }
            if self.asset_type == "options":
                position_data.update({
                    'option_type': option_type,
                    'strike': strike,
                    'expiration': expiration
                })
            self.positions[symbol] = position_data
        else:
            # Open new position
            if self.asset_type == "options":
                print(f" {self.agent_name}: Opening {symbol} {option_type} position: {qty:.0f} contracts @ ${price:.2f} (Strike: ${strike:.2f})")
                self.positions[symbol] = {
                    'qty': qty,
                    'entry_price': price,
                    'entry_time': datetime.now().isoformat(),
                    'entry_value': position_size,
                    'option_type': option_type,
                    'strike': strike,
                    'expiration': expiration
                }
            else:
                print(f" {self.agent_name}: Opening new {symbol} position: {qty:.6f} @ ${price:.2f}")
                self.positions[symbol] = {
                    'qty': qty,
                    'entry_price': price,
                    'entry_time': datetime.now().isoformat(),
                    'entry_value': position_size
                }
        
        # Deduct from balance
        self.balance -= position_size
        
        # Record trade
        trade = {
            'id': len(self.trades_history) + 1,
            'type': 'BUY',
            'symbol': symbol,
            'qty': qty,
            'price': price,
            'value': position_size,
            'time': datetime.now().isoformat(),
            'balance_after': self.balance
        }
        if self.asset_type == "options":
            trade.update({
                'option_type': option_type,
                'strike': strike,
                'expiration': expiration
            })
        self.trades_history.append(trade)
        
        # Mark decision as executed
        decision['executed'] = True
        
        # Update PnL history
        self._update_pnl_history()
        
        # Save state
        self._save_state()
        
        return trade
    
    def _execute_sell(self, symbol: str, price: float, decision: dict) -> Optional[dict]:
        """Execute a SELL order"""
        # Can only sell if holding
        if symbol not in self.positions:
            print(f"⚠️ {self.agent_name}: Cannot SELL {symbol} - no open position")
            return None
        
        position = self.positions[symbol]
        qty = position['qty']
        entry_price = position['entry_price']
        
        # Calculate proceeds and PnL
        if self.asset_type == "options":
            # Options: price is premium per share, multiply by 100 shares per contract
            proceeds = qty * price * 100
        else:
            proceeds = qty * price
        
        pnl = proceeds - position['entry_value']
        pnl_pct = (pnl / position['entry_value']) * 100
        
        # Add to balance
        self.balance += proceeds
        
        # Record trade
        trade = {
            'id': len(self.trades_history) + 1,
            'type': 'SELL',
            'symbol': symbol,
            'qty': qty,
            'price': price,
            'value': proceeds,
            'entry_price': entry_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'time': datetime.now().isoformat(),
            'balance_after': self.balance,
            'hold_time': self._calculate_hold_time(position['entry_time'])
        }
        self.trades_history.append(trade)
        
        # Mark decision as executed
        decision['executed'] = True
        
        # Remove position
        del self.positions[symbol]
        
        # Update PnL history
        self._update_pnl_history()
        
        # Save state
        self._save_state()
        
        return trade
    
    def _calculate_hold_time(self, entry_time_str: str) -> str:
        """Calculate how long a position was held"""
        try:
            entry_time = datetime.fromisoformat(entry_time_str)
            duration = datetime.now() - entry_time
            
            hours = duration.total_seconds() / 3600
            if hours < 1:
                return f"{int(duration.total_seconds() / 60)} minutes"
            elif hours < 24:
                return f"{int(hours)} hours"
            else:
                return f"{int(hours / 24)} days"
        except:
            return "Unknown"
    
    def update_position_prices(self, current_prices: Dict[str, float]):
        """Update positions with current market prices and recalculate PnL"""
        self._update_pnl_history(current_prices)
        self._save_state()
    
    def _update_pnl_history(self, current_prices: Optional[Dict[str, float]] = None):
        """Calculate and store current PnL"""
        # Start with cash balance
        total_value = self.balance
        
        # Add value of open positions
        for symbol, position in self.positions.items():
            if current_prices and symbol in current_prices:
                current_price = current_prices[symbol]
            else:
                # Use entry price if no current price provided
                current_price = position['entry_price']
            
            # For options, multiply by 100 (shares per contract)
            if self.asset_type == "options":
                position_value = position['qty'] * current_price * 100
            else:
                position_value = position['qty'] * current_price
            total_value += position_value
        
        # Calculate PnL
        pnl = total_value - self.initial_balance
        pnl_pct = (pnl / self.initial_balance) * 100
        
        # Update peak and drawdown
        if total_value > self.peak_value:
            self.peak_value = total_value
        
        current_drawdown = ((self.peak_value - total_value) / self.peak_value) * 100
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
        
        # Store in history
        pnl_entry = {
            'timestamp': datetime.now().isoformat(),
            'total_value': total_value,
            'balance': self.balance,
            'positions_value': total_value - self.balance,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        }
        self.pnl_history.append(pnl_entry)
        
        # Keep only last 1000 entries to avoid file bloat
        if len(self.pnl_history) > 1000:
            self.pnl_history = self.pnl_history[-1000:]
    
    def get_account_value(self, current_prices: Optional[Dict[str, float]] = None) -> float:
        """Get total account value (cash + positions)"""
        total_value = self.balance
        
        # Add value of open positions
        for symbol, pos in self.positions.items():
            if current_prices and symbol in current_prices:
                current_price = current_prices[symbol]
            else:
                # Use entry price if no current price provided
                current_price = pos['entry_price']
            
            # For options, multiply by 100 (shares per contract)
            if self.asset_type == "options":
                position_value = pos['qty'] * current_price * 100
            else:
                position_value = pos['qty'] * current_price
            total_value += position_value
        
        return total_value
    
    def get_current_stats(self, current_prices: Optional[Dict[str, float]] = None) -> dict:
        """Get current performance statistics"""
        # Update PnL with latest prices
        self._update_pnl_history(current_prices)
        
        # Get latest PnL
        latest_pnl = self.pnl_history[-1] if self.pnl_history else {
            'total_value': self.initial_balance,
            'pnl': 0,
            'pnl_pct': 0
        }
        
        # Calculate trade statistics
        completed_trades = [t for t in self.trades_history if t['type'] == 'SELL']
        winning_trades = [t for t in completed_trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in completed_trades if t.get('pnl', 0) <= 0]
        
        total_trades = len(completed_trades)
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate Sharpe ratio (simplified)
        if len(self.pnl_history) > 1:
            returns = [self.pnl_history[i]['pnl_pct'] - self.pnl_history[i-1]['pnl_pct'] 
                      for i in range(1, len(self.pnl_history))]
            if returns:
                avg_return = sum(returns) / len(returns)
                std_return = math.sqrt(sum((r - avg_return) ** 2 for r in returns) / len(returns)) if len(returns) > 1 else 0
                sharpe = (avg_return / std_return) if std_return > 0 else 0
            else:
                sharpe = 0
        else:
            sharpe = 0
        
        return {
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'balance': round(self.balance, 2),
            'total_value': round(latest_pnl['total_value'], 2),
            'pnl': round(latest_pnl['pnl'], 2),
            'pnl_pct': round(latest_pnl['pnl_pct'], 2),
            'win_rate': round(win_rate, 1),
            'sharpe_ratio': round(sharpe, 2),
            'max_drawdown': round(self.max_drawdown, 2),
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'open_positions': len(self.positions),
            'decisions_count': len(self.decisions_log)
        }
    
    def get_open_positions(self, current_prices: Optional[Dict[str, float]] = None) -> List[dict]:
        """Get list of open positions with current PnL"""
        positions_list = []
        
        for symbol, position in self.positions.items():
            # For options, use the option ticker price; for stocks, use stock price
            current_price = current_prices.get(symbol, position['entry_price']) if current_prices else position['entry_price']
            
            # For options, calculate value based on premium per contract (qty is in contracts, price is premium)
            if self.asset_type == "options":
                # current_price is the option premium, qty is number of contracts
                # Each contract = 100 shares, so value = premium * 100 * contracts
                current_value = position['qty'] * current_price * 100
            else:
                # For stocks/crypto: qty is quantity, price is per unit
                current_value = position['qty'] * current_price
            
            unrealized_pnl = current_value - position['entry_value']
            unrealized_pnl_pct = (unrealized_pnl / position['entry_value']) * 100 if position['entry_value'] != 0 else 0
            
            pos_dict = {
                'symbol': symbol,
                'qty': position['qty'],
                'entry_price': position['entry_price'],
                'current_price': current_price,
                'entry_value': position['entry_value'],
                'current_value': current_value,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_pct': unrealized_pnl_pct,
                'entry_time': position['entry_time'],
                'hold_time': self._calculate_hold_time(position['entry_time'])
            }
            
            # Add option-specific fields
            if self.asset_type == "options":
                pos_dict.update({
                    'option_type': position.get('option_type', 'UNKNOWN'),
                    'strike': position.get('strike', 0),
                    'expiration': position.get('expiration', 'N/A')
                })
            
            positions_list.append(pos_dict)
        
        return positions_list
    
    def get_completed_trades(self, limit: int = 50) -> List[dict]:
        """Get list of completed trades"""
        completed = [t for t in self.trades_history if t['type'] == 'SELL']
        return completed[-limit:] if limit else completed
    
    def get_pnl_history_for_chart(self) -> dict:
        """Get PnL history formatted for chart display"""
        if not self.pnl_history:
            return {
                'timestamps': [],
                'pnl': [],
                'name': self.agent_name
            }
        
        return {
            'timestamps': [entry['timestamp'] for entry in self.pnl_history],
            'pnl': [entry['pnl_pct'] for entry in self.pnl_history],
            'name': self.agent_name
        }
    
    def reset(self):
        """Reset the trading engine to initial state"""
        self.balance = self.initial_balance
        self.positions = {}
        self.trades_history = []
        self.pnl_history = []
        self.decisions_log = []
        self.peak_value = self.initial_balance
        self.max_drawdown = 0.0
        self._save_state()
