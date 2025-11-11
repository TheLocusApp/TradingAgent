#!/usr/bin/env python3
"""
🌙 Moon Dev's Agent Manager
Manages multiple trading agents simultaneously
Built with love by Moon Dev 🚀
"""

import threading
import time
from typing import Dict, List
from datetime import datetime
from termcolor import cprint
from pathlib import Path
import json

from src.agents.universal_trading_agent import UniversalTradingAgent
from src.agents.rl_optimizer import RLOptimizer
from src.config.trading_config import TradingConfig
from src.trading.simulated_trading_engine import SimulatedTradingEngine
from src.data_providers.free_market_data import FreeMarketDataProvider


class AgentManager:
    """Manages multiple trading agents"""
    
    def __init__(self):
        """Initialize agent manager"""
        self.agents: Dict[str, Dict] = {}  # {agent_id: {agent, thread, running}}
        self.agent_counter = 1
        self.market_data_provider = FreeMarketDataProvider()
        cprint("✅ Agent Manager initialized", "green")
    
    def create_agent(self, config: TradingConfig) -> str:
        """
        Create and start a new trading agent
        
        Args:
            config: Trading configuration for the agent
            
        Returns:
            agent_id: Unique identifier for the agent
        """
        # Generate unique agent ID
        agent_id = f"agent_{self.agent_counter}"
        self.agent_counter += 1
        
        # Set agent name if not provided
        if not config.agent_name or config.agent_name == "Agent 1":
            config.agent_name = f"Agent {self.agent_counter - 1}"
        
        # Create agent
        agent = UniversalTradingAgent(config)
        
        # Create simulated trading engine (force fresh start to avoid loading old state)
        trading_engine = SimulatedTradingEngine(
            agent_id=agent_id,
            agent_name=config.agent_name,
            initial_balance=config.initial_balance,
            force_fresh_start=True,  # Always start fresh - don't load old state
            asset_type=config.asset_type  # Pass asset type for options support
        )
        
        # Create RL optimizer if enabled
        rl_optimizer = None
        if config.enable_rl:
            config.rl_status = "training"  # Start in training mode
            rl_optimizer = RLOptimizer(agent, config, trading_engine)
        
        # Store agent info
        self.agents[agent_id] = {
            'agent': agent,
            'trading_engine': trading_engine,
            'rl_optimizer': rl_optimizer,
            'thread': None,
            'running': False,
            'created_at': datetime.now().isoformat(),
            'config': config
        }
        
        cprint(f"✅ Created {config.agent_name} (ID: {agent_id})", "green")
        return agent_id
    
    def start_agent(self, agent_id: str) -> bool:
        """
        Start a trading agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            success: True if started successfully
        """
        if agent_id not in self.agents:
            cprint(f"❌ Agent {agent_id} not found", "red")
            return False
        
        agent_info = self.agents[agent_id]
        
        if agent_info['running']:
            cprint(f"⚠️ Agent {agent_id} already running", "yellow")
            return False
        
        # Create and start thread
        agent_info['running'] = True
        thread = threading.Thread(target=self._run_agent, args=(agent_id,), daemon=True)
        thread.start()
        agent_info['thread'] = thread
        
        cprint(f"✅ Started {agent_info['config'].agent_name}", "green")
        return True
    
    def stop_agent(self, agent_id: str) -> bool:
        """
        Stop a trading agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            success: True if stopped successfully
        """
        if agent_id not in self.agents:
            cprint(f"❌ Agent {agent_id} not found", "red")
            return False
        
        agent_info = self.agents[agent_id]
        agent_info['running'] = False
        
        cprint(f"✅ Stopped {agent_info['config'].agent_name}", "green")
        return True
    
    def delete_agent(self, agent_id: str) -> bool:
        """
        Delete a trading agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            success: True if deleted successfully
        """
        if agent_id not in self.agents:
            cprint(f"❌ Agent {agent_id} not found", "red")
            return False
        
        # Stop agent first
        self.stop_agent(agent_id)
        
        # Remove from dict
        agent_name = self.agents[agent_id]['config'].agent_name
        del self.agents[agent_id]
        
        cprint(f"✅ Deleted {agent_name}", "green")
        return True
    
    def get_agent(self, agent_id: str) -> UniversalTradingAgent:
        """Get agent instance"""
        if agent_id in self.agents:
            return self.agents[agent_id]['agent']
        return None
    
    def get_all_agents(self) -> Dict:
        """Get all agents with their status"""
        result = {}
        for agent_id, info in self.agents.items():
            agent = info['agent']
            trading_engine = info['trading_engine']
            
            # Get current prices for all monitored assets
            current_prices = self._get_current_prices(info['config'].monitored_assets, info['config'].asset_type)
            
            # For options, also fetch current option quotes for open positions
            if info['config'].asset_type == "options":
                for option_ticker in trading_engine.positions.keys():
                    try:
                        option_quote = agent.options_provider.get_option_quote(option_ticker)
                        if option_quote and 'mid' in option_quote:
                            current_prices[option_ticker] = option_quote['mid']
                    except Exception as e:
                        pass  # Silently fail for status checks
            
            # Update positions with current prices
            trading_engine.update_position_prices(current_prices)
            
            # Get stats from trading engine with current prices
            stats = trading_engine.get_current_stats(current_prices)
            
            # Get positions from trading engine with current prices
            positions = trading_engine.get_open_positions(current_prices)
            
            # Get RL status if optimizer exists
            rl_status = None
            if info['rl_optimizer']:
                rl_status = info['rl_optimizer'].get_rl_status_display()
            
            result[agent_id] = {
                'id': agent_id,
                'name': info['config'].agent_name,
                'strategy': info['config'].agent_strategy,
                'asset_type': info['config'].asset_type,
                'running': info['running'],
                'created_at': info['created_at'],
                'balance': stats['balance'],
                'total_value': stats['total_value'],
                'pnl': stats['pnl'],
                'pnl_pct': stats['pnl_pct'],
                'win_rate': stats['win_rate'],
                'sharpe_ratio': stats['sharpe_ratio'],
                'max_drawdown': stats['max_drawdown'],
                'total_trades': stats['total_trades'],
                'open_positions': stats['open_positions'],
                'positions': positions,
                'decisions_count': stats['decisions_count'],
                'monitored_assets': info['config'].monitored_assets,
                'rl_status': rl_status
            }
        
        return result
    
    def get_agent_stats(self) -> List[Dict]:
        """Get comparison stats for all agents"""
        stats = []
        
        for agent_id, info in self.agents.items():
            agent = info['agent']
            trading_engine = info['trading_engine']
            
            # Get current prices for all monitored assets
            current_prices = self._get_current_prices(info['config'].monitored_assets, info['config'].asset_type)
            
            # For options, also fetch current option quotes for open positions
            if info['config'].asset_type == "options":
                for option_ticker in trading_engine.positions.keys():
                    try:
                        option_quote = agent.options_provider.get_option_quote(option_ticker)
                        if option_quote and 'mid' in option_quote:
                            current_prices[option_ticker] = option_quote['mid']
                    except Exception as e:
                        pass  # Silently fail for status checks
            
            # Update positions with current prices
            trading_engine.update_position_prices(current_prices)
            
            engine_stats = trading_engine.get_current_stats(current_prices)
            
            stats.append({
                'id': agent_id,
                'name': info['config'].agent_name,
                'balance': engine_stats['total_value'],
                'pnl': engine_stats['pnl'],
                'pnl_pct': engine_stats['pnl_pct'],
                'win_rate': engine_stats['win_rate'],
                'sharpe': engine_stats['sharpe_ratio'],
                'max_dd': engine_stats['max_drawdown'],
                'total_trades': engine_stats['total_trades'],
                'running': info['running']
            })
        
        # Sort by PnL (best first)
        stats.sort(key=lambda x: x['pnl_pct'], reverse=True)
        
        return stats
    
    def get_performance_history(self) -> Dict:
        """Get performance history for all agents (for chart)"""
        history = {}
        
        for agent_id, info in self.agents.items():
            trading_engine = info['trading_engine']
            
            # Get PnL history from trading engine
            pnl_data = trading_engine.get_pnl_history_for_chart()
            
            history[agent_id] = pnl_data
        
        return history
    
    def _run_agent(self, agent_id: str):
        """Run agent in background thread"""
        agent_info = self.agents[agent_id]
        agent = agent_info['agent']
        config = agent_info['config']
        trading_engine = agent_info['trading_engine']
        rl_optimizer = agent_info.get('rl_optimizer')  # Get RL optimizer from agent info
        
        cycle = 0
        cprint(f"\n✨ {config.agent_name} started trading", "cyan")
        
        try:
            while agent_info['running']:
                cycle += 1
                try:
                    # Get current prices for all monitored assets
                    current_prices = self._get_current_prices(config.monitored_assets, config.asset_type)
                    
                    # For options, also fetch current option quotes for open positions
                    if config.asset_type == "options":
                        trading_engine = agent_info['trading_engine']
                        for option_ticker in trading_engine.positions.keys():
                            try:
                                # Fetch current option quote
                                option_quote = agent.options_provider.get_option_quote(option_ticker)
                                if option_quote and 'mid' in option_quote:
                                    current_prices[option_ticker] = option_quote['mid']
                            except Exception as e:
                                cprint(f"⚠️ Could not fetch quote for {option_ticker}: {e}", "yellow")
                    
                    # Update agent's account info from trading engine with current prices
                    agent.update_account_from_engine(trading_engine, current_prices)
                    
                    # Update trading engine with current prices
                    trading_engine.update_position_prices(current_prices)
                    
                    # Process each monitored asset
                    for symbol in config.monitored_assets:
                        try:
                            # Get market state for this specific symbol
                            market_state = agent.get_market_state_for_symbol(symbol)
                            decision = agent.make_decision(market_state)
                            
                            # Record decision for RL if optimizer exists
                            if rl_optimizer:
                                rl_optimizer.record_decision(decision)
                            
                            # Execute decision through trading engine
                            signal = decision.get('signal', 'HOLD')
                            reasoning = decision.get('reasoning', '')
                            
                            # Debug: Log all decisions for RL tracking
                            if rl_optimizer:
                                cprint(f"🔍 RL Decision: {signal} ({decision.get('confidence', 0)}%)", "cyan")
                            
                            # For options, handle BUY and SELL specially
                            if config.asset_type == "options":
                                if signal == "BUY":
                                    cprint(f"🔍 STEP 1: BUY signal detected for {symbol}", "cyan")
                                    
                                    try:
                                        cprint(f"🔍 STEP 2: Fetching options data for {symbol}...", "cyan")
                                        options_data = agent.get_options_data(symbol)
                                        
                                        if not options_data:
                                            cprint(f"❌ STEP 2 FAILED: Could not fetch options data for {symbol}", "red")
                                            continue
                                        
                                        cprint(f"✅ STEP 2: Options data fetched successfully", "green")
                                        cprint(f"   ATM Strike: ${options_data.get('atm_strike', 'N/A')}", "cyan")
                                        cprint(f"   CALL: {options_data.get('call', {}).get('ticker', 'N/A')}", "cyan")
                                        cprint(f"   PUT: {options_data.get('put', {}).get('ticker', 'N/A')}", "cyan")
                                        
                                        # Parse reasoning to determine CALL or PUT
                                        cprint(f"🔍 STEP 3: Parsing reasoning to determine CALL/PUT...", "cyan")
                                        reasoning_upper = reasoning.upper()
                                        cprint(f"   Reasoning text: '{reasoning_upper[:200]}'", "cyan")
                                        
                                        if "BUY CALL" in reasoning_upper or ("CALL" in reasoning_upper and "PUT" not in reasoning_upper):
                                            option_type = "CALL"
                                            option_premium = options_data['call']['mid']
                                            option_ticker = options_data['call']['ticker']
                                            strike = options_data['atm_strike']
                                            expiration = options_data['expiration']
                                            cprint(f"✅ STEP 3: Detected CALL option", "green")
                                        elif "BUY PUT" in reasoning_upper or "PUT" in reasoning_upper:
                                            option_type = "PUT"
                                            option_premium = options_data['put']['mid']
                                            option_ticker = options_data['put']['ticker']
                                            strike = options_data['atm_strike']
                                            expiration = options_data['expiration']
                                            cprint(f"✅ STEP 3: Detected PUT option", "green")
                                        else:
                                            cprint(f"❌ STEP 3 FAILED: No CALL/PUT specified in reasoning", "red")
                                            continue
                                        
                                        # Execute options trade
                                        cprint(f"🔍 STEP 4: Executing options trade...", "cyan")
                                        cprint(f"   Ticker: {option_ticker}", "cyan")
                                        cprint(f"   Type: {option_type}", "cyan")
                                        cprint(f"   Premium: ${option_premium:.2f}", "cyan")
                                        cprint(f"   Strike: ${strike:.2f}", "cyan")
                                        cprint(f"   Expiration: {expiration}", "cyan")
                                        cprint(f"   Balance: ${trading_engine.balance:.2f}", "cyan")
                                        
                                        trade = trading_engine.execute_buy(
                                            decision=decision,
                                            symbol=option_ticker,
                                            price=option_premium,
                                            option_type=option_type,
                                            strike=strike,
                                            expiration=expiration
                                        )
                                        
                                        if trade:
                                            cprint(f"✅ STEP 4: Trade EXECUTED successfully!", "green")
                                            cprint(f"✅ {config.agent_name} Cycle {cycle}: BUY {option_type} {symbol} @ ${option_premium:.2f} (Strike: ${strike:.2f})", "green")
                                            cprint(f"   Positions: {list(trading_engine.positions.keys())}", "cyan")
                                            cprint(f"   Balance after: ${trading_engine.balance:.2f}", "cyan")
                                        else:
                                            cprint(f"❌ STEP 4 FAILED: Trade NOT executed", "red")
                                            cprint(f"   Balance: ${trading_engine.balance:.2f}", "yellow")
                                            cprint(f"   Positions: {list(trading_engine.positions.keys())}", "yellow")
                                    
                                    except Exception as e:
                                        cprint(f"❌ EXCEPTION in options BUY flow: {e}", "red")
                                        import traceback
                                        traceback.print_exc()
                                
                                elif signal == "SELL":
                                    # For SELL, close all option positions for this underlying
                                    positions_to_close = [ticker for ticker in trading_engine.positions.keys() if ticker.startswith('.')]
                                    
                                    if not positions_to_close:
                                        cprint(f"⚠️ {config.agent_name}: SELL signal but no open option positions", "yellow")
                                        continue
                                    
                                    for option_ticker in positions_to_close:
                                        # Get current option quote
                                        try:
                                            option_quote = agent.options_provider.get_option_quote(option_ticker)
                                            if option_quote and 'mid' in option_quote:
                                                current_price = option_quote['mid']
                                            else:
                                                current_price = trading_engine.positions[option_ticker]['entry_price']
                                        except:
                                            current_price = trading_engine.positions[option_ticker]['entry_price']
                                        
                                        # Execute SELL
                                        trade = trading_engine.execute_signal(
                                            signal='SELL',
                                            symbol=option_ticker,
                                            current_price=current_price,
                                            confidence=decision.get('confidence', 0),
                                            reasoning=reasoning
                                        )
                                        
                                        if trade:
                                            cprint(f"✅ {config.agent_name} Cycle {cycle}: SELL {option_ticker} @ ${current_price:.2f} - EXECUTED", "green")
                                            # Record completed trade for RL
                                            if rl_optimizer:
                                                rl_optimizer.record_trade(trade)
                                        else:
                                            cprint(f"⚠️ {config.agent_name} Cycle {cycle}: SELL {option_ticker} - NOT EXECUTED", "yellow")
                            else:
                                # Regular stock/crypto trade
                                current_price = current_prices.get(symbol, market_state.get('current_price', 100000))
                                
                                trade = trading_engine.execute_signal(
                                    signal=signal,
                                    symbol=symbol,
                                    current_price=current_price,
                                    confidence=decision.get('confidence', 0),
                                    reasoning=reasoning
                                )
                                
                                if trade:
                                    cprint(f"✅ {config.agent_name} Cycle {cycle}: {signal} {symbol} @ ${current_price:,.2f} - EXECUTED", "green")
                                    # Record completed trade for RL
                                    if rl_optimizer:
                                        trade_count = len(rl_optimizer.trade_history) + 1
                                        cprint(f"📊 RL Trade #{trade_count}: {signal} {symbol}", "yellow")
                                        rl_optimizer.record_trade(trade)
                                else:
                                    cprint(f"⏸️ {config.agent_name} Cycle {cycle}: {signal} {symbol} ({decision['confidence']}%) - NOT EXECUTED", "cyan")
                        except Exception as symbol_error:
                            cprint(f"⚠️ Error processing {symbol}: {symbol_error}", "yellow")
                    
                except Exception as cycle_error:
                    cprint(f"⚠️ {config.agent_name} error in cycle {cycle}: {str(cycle_error)[:100]}", "yellow")
                
                # Check if RL optimization should be triggered
                if rl_optimizer and rl_optimizer.check_optimization_trigger():
                    rl_optimizer.trigger_optimization()
                
                # Wait for next cycle
                if agent_info['running']:
                    time.sleep(config.cycle_interval)
        
        except Exception as e:
            cprint(f"❌ Fatal error in {config.agent_name}: {e}", "red")
            agent_info['running'] = False
    
    def _get_current_prices(self, symbols: List[str], asset_type: str) -> Dict[str, float]:
        """Get current prices for multiple symbols"""
        prices = {}
        for symbol in symbols:
            try:
                if asset_type == 'crypto':
                    data = self.market_data_provider.get_crypto_price(symbol)
                else:  # stock
                    data = self.market_data_provider.get_stock_price(symbol)
                
                if data and data.get('price'):
                    prices[symbol] = data['price']
            except Exception as e:
                cprint(f"⚠️ Error fetching price for {symbol}: {e}", "yellow")
        return prices


# Global agent manager instance
agent_manager = AgentManager()
