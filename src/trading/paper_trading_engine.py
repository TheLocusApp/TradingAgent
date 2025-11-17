#!/usr/bin/env python3
"""
🌙 Moon Dev's Paper Trading Engine
Handles webhook-based trade execution with proper asset type detection
Supports both stock and options trading with per-timeframe accounts
"""

import json
import os
import math
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from termcolor import cprint


class PaperTradingEngine:
    """
    Comprehensive paper trading engine for AGBot webhook integration
    Features:
    - Per-timeframe account management (1H, 4H, 1D)
    - Automatic asset type detection (stock vs options)
    - Tastytrade option chain integration
    - Proper P&L calculations
    - Trade persistence
    """
    
    def __init__(self, initial_balance: float = 10000.00):
        """Initialize paper trading engine"""
        self.initial_balance = initial_balance
        
        # Single account for all timeframes
        # User filters by timeframe later for performance comparison
        self.account = {
            'account_balance': initial_balance,
            'initial_balance': initial_balance,
            'trades': [],
            'open_positions': [],
            'webhooks': []
        }
        
        self.tastytrade_provider = None
        self._init_tastytrade()
    
    def _init_tastytrade(self):
        """Initialize Tastytrade provider if available"""
        try:
            from src.data_providers.tastytrade_options_provider import TastytradeOptionsProvider
            self.tastytrade_provider = TastytradeOptionsProvider()
            cprint("✅ Tastytrade provider initialized", "green")
        except Exception as e:
            cprint(f"⚠️ Tastytrade not available: {e}", "yellow")
            cprint("   Using fallback option pricing", "yellow")
    
    def _parse_position_size(self, value) -> Optional[float]:
        """Safely convert TradingView position size fields to float"""
        if value is None:
            return None
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                stripped = value.strip().replace(',', '')
                if stripped == '':
                    return None
                return float(stripped)
        except (ValueError, TypeError):
            return None
        return None
    
    def _normalize_action(self, action: str, webhook_data: Dict) -> Tuple[str, Optional[str]]:
        """
        Normalize TradingView action based on comment + position fields.
        Returns (normalized_action, reason_for_change)
        """
        normalized = (action or '').lower().strip()
        if normalized in ['close', 'exit', 'tp1', 'tp2', 'tp3', 'sl']:
            return 'close', 'explicit close action'
        
        # Comment-based exit detection (TradingView uses LX/SX for exits)
        comment_sources = [
            webhook_data.get('comment'),
            webhook_data.get('signal'),
            webhook_data.get('alert_message'),
            webhook_data.get('note')
        ]
        comment_text = ' '.join(str(item) for item in comment_sources if item)
        comment_upper = comment_text.upper()
        exit_keywords = [
            'TP1', 'TP2', 'TP3', 'SL', 'STOP LOSS', 'STOP', 'EXIT', 'CLOSE',
            'LX', 'SX', 'EOD FLAT', 'END OF DAY FLAT'
        ]
        for keyword in exit_keywords:
            if keyword in comment_upper:
                return 'close', f'comment keyword "{keyword}"'
        
        market_position = (webhook_data.get('market_position') or '').lower().strip()
        prev_market_position = (webhook_data.get('prev_market_position') or '').lower().strip()
        market_position_size = self._parse_position_size(webhook_data.get('market_position_size'))
        prev_market_position_size = self._parse_position_size(webhook_data.get('prev_market_position_size'))
        
        def is_flat(position: str, size: Optional[float]) -> bool:
            if position == 'flat':
                return True
            if size is not None and abs(size) < 1e-9:
                return True
            return False
        
        became_flat = is_flat(market_position, market_position_size)
        was_positioned = prev_market_position in ['long', 'short'] or (
            prev_market_position_size is not None and abs(prev_market_position_size) > 0
        )
        if normalized in ['buy', 'sell'] and was_positioned and became_flat:
            return 'close', 'position flattened'
        
        size_reduced = (
            prev_market_position_size is not None and
            market_position_size is not None and
            market_position_size < prev_market_position_size
        )
        
        if normalized == 'sell' and prev_market_position == 'long':
            if market_position != 'short' and (became_flat or size_reduced):
                return 'close', 'long position reduced'
        
        if normalized == 'buy' and prev_market_position == 'short':
            if market_position != 'long' and (became_flat or size_reduced):
                return 'close', 'short position reduced'
        
        return normalized, None
    
    def _get_desired_position_direction(self, webhook_data: Dict) -> Optional[str]:
        """
        Infer whether the close signal should target a LONG (CALL) or SHORT (PUT) position.
        Returns 'long', 'short', or None if unknown.
        """
        comment_sources = [
            webhook_data.get('comment'),
            webhook_data.get('signal'),
            webhook_data.get('alert_message'),
            webhook_data.get('note')
        ]
        comment_text = ' '.join(str(item) for item in comment_sources if item)
        comment_upper = comment_text.upper()
        
        if 'SHORT' in comment_upper or 'SX' in comment_upper:
            return 'short'
        if 'LONG' in comment_upper or 'LX' in comment_upper:
            return 'long'
        
        prev_market_position = (webhook_data.get('prev_market_position') or '').lower().strip()
        market_position = (webhook_data.get('market_position') or '').lower().strip()
        
        if prev_market_position in ['long', 'short']:
            return prev_market_position
        if market_position in ['long', 'short']:
            return market_position
        
        prev_size = self._parse_position_size(webhook_data.get('prev_market_position_size'))
        curr_size = self._parse_position_size(webhook_data.get('market_position_size'))
        if prev_size and prev_size > 0:
            size_diff = prev_size - (curr_size or 0)
            # Positive diff indicates reduction of existing exposure
            if size_diff > 0:
                # If strategy previously long (size positive) assume long
                return 'long'
        
        return None
    
    def _shares_to_option_contracts(self, shares) -> Optional[int]:
        """Convert TradingView share counts to option contracts (1 contract = 100 shares)"""
        size = self._parse_position_size(shares)
        if size is None:
            return None
        if size <= 0:
            return 0
        contracts = math.ceil(size / 100.0)
        return max(contracts, 1)
    
    def _determine_close_contracts(self, share_value, webhook_data: Dict, open_pos: Dict) -> int:
        """Determine how many option contracts to close for partial exits"""
        requested_contracts = self._shares_to_option_contracts(share_value)
        
        prev_size = self._parse_position_size(webhook_data.get('prev_market_position_size'))
        curr_size = self._parse_position_size(webhook_data.get('market_position_size'))
        size_based_contracts = None
        if prev_size is not None:
            diff = prev_size - (curr_size or 0)
            if diff > 0:
                size_based_contracts = self._shares_to_option_contracts(diff)
        
        close_contracts = size_based_contracts or requested_contracts
        remaining = open_pos.get('remaining_contracts', 0) or open_pos.get('contracts', 0)
        if remaining <= 0:
            remaining = open_pos.get('initial_contracts') or 0
        if not close_contracts or close_contracts <= 0:
            close_contracts = remaining or 1
        
        close_contracts = min(close_contracts, remaining or close_contracts)
        return max(close_contracts, 1)
    
    def _get_option_close_price(self, open_pos: Dict, fallback_price: float) -> float:
        """
        Determine an exit option price.
        Priority: live Tastytrade quote → webhook price if it looks like an option quote → delta-adjusted estimate.
        """
        option_symbol = open_pos.get('option_symbol')
        
        # Try live quote
        if option_symbol and self.tastytrade_provider:
            quote = self.tastytrade_provider.get_option_quote(option_symbol)
            if quote and quote.get('mid'):
                return quote['mid']
        
        # If webhook price already looks like an option premium (< $50), use it
        if fallback_price and fallback_price < 50:
            return round(fallback_price, 2)
        
        entry_option_price = open_pos.get('entry_price', 1.0) or 1.0
        entry_underlying = open_pos.get('underlying_price')
        
        if fallback_price and entry_underlying and entry_underlying > 0:
            ratio = fallback_price / entry_underlying
            if ratio > 0:
                estimate = round(entry_option_price * ratio, 2)
                if estimate > 0:
                    return estimate
        
        return round(entry_option_price, 2)
    
    def _detect_asset_type(self, webhook_data: Dict) -> str:
        """
        Get asset type from webhook JSON
        
        Expected: webhook_data['asset_type'] = 'stock' or 'option'
        
        Returns: 'stock' or 'option'
        """
        # Use explicit field from webhook
        asset_type = webhook_data.get('asset_type', 'stock').lower()
        
        if asset_type in ['stock', 'option']:
            return asset_type
        
        # Safe default
        return 'stock'
    
    def _get_timeframe(self, webhook_data: Dict) -> str:
        """
        Extract timeframe from webhook
        
        Returns: '2m', '3m', '1H', etc.
        
        Note: Timeframe is stored with each trade for later filtering
        """
        # Try explicit timeframe field first
        timeframe = webhook_data.get('timeframe', '').lower()
        if timeframe:
            return timeframe
        
        # Try interval field
        interval = webhook_data.get('interval', '').lower()
        
        # Map common intervals
        interval_map = {
            '2': '2m',
            '3': '3m',
            '5': '5m',
            '15': '15m',
            '30': '30m',
            '60': '1H',
            '1h': '1H',
            '4': '4H',
            '4h': '4H',
            '1d': '1D',
            'day': '1D'
        }
        
        if interval in interval_map:
            return interval_map[interval]
        
        # Default to 1H
        return '1H'
    
    def _get_option_data(self, ticker: str, signal_type: str, webhook_price: float = None) -> Optional[Dict]:
        """
        Fetch option data from Tastytrade or use fallback pricing
        
        Args:
            ticker: Stock ticker (e.g., 'QQQ')
            signal_type: 'buy' or 'sell' (determines CALL or PUT)
            webhook_price: Current price from webhook (used for ATM strike calculation)
        
        Returns:
            {
                'option_symbol': '.QQQ251110C500',
                'strike': 500,
                'expiry': '2025-11-10',
                'type': 'CALL' or 'PUT',
                'bid': 2.50,
                'ask': 2.75,
                'mid': 2.625,
                'underlying_price': 500.50
            }
        """
        try:
            # Try Tastytrade first
            if self.tastytrade_provider:
                data = self.tastytrade_provider.get_atm_options_data(ticker)
                if data:
                    option_type = 'CALL' if signal_type == 'buy' else 'PUT'
                    option_data = data['call'] if option_type == 'CALL' else data['put']
                    
                    return {
                        'option_symbol': option_data['ticker'],
                        'strike': data['atm_strike'],
                        'expiry': data['expiration'],
                        'type': option_type,
                        'bid': option_data['bid'],
                        'ask': option_data['ask'],
                        'mid': option_data['mid'],
                        'underlying_price': data['underlying_price']
                    }
        except Exception as e:
            cprint(f"⚠️ Tastytrade fetch failed: {e}", "yellow")
        
        # Fallback: Generate realistic option pricing using webhook price
        return self._generate_fallback_option_data(ticker, signal_type, webhook_price=webhook_price)
    
    def _generate_fallback_option_data(self, ticker: str, signal_type: str, webhook_price: float = None) -> Dict:
        """
        Generate realistic fallback option pricing when Tastytrade unavailable
        
        Args:
            ticker: Stock ticker
            signal_type: 'buy' or 'sell'
            webhook_price: Use webhook price as underlying price if available
        """
        import random
        from datetime import datetime, timedelta
        
        # Default underlying prices (fallback if webhook price not provided)
        underlying_prices = {
            'QQQ': 620.00,
            'SPY': 580.00,
            'AAPL': 240.00,
            'NVDA': 140.00,
            'TSLA': 280.00
        }
        
        # Use webhook price if provided, otherwise use default
        if webhook_price and webhook_price > 0:
            underlying_price = webhook_price
        else:
            underlying_price = underlying_prices.get(ticker, 100.00)
        
        atm_strike = round(underlying_price)
        
        # Realistic option pricing (ATM options typically $1.50-$4.00)
        base_price = random.uniform(1.50, 3.50)
        bid = round(base_price - 0.10, 2)
        ask = round(base_price + 0.10, 2)
        mid = round((bid + ask) / 2, 2)
        
        option_type = 'CALL' if signal_type == 'buy' else 'PUT'
        expiry = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        date_str = expiry.replace('-', '')[2:]
        strike_str = f"{int(atm_strike * 1000):08d}"
        option_symbol = f".{ticker}{date_str}{option_type[0]}{strike_str}"
        
        return {
            'option_symbol': option_symbol,
            'strike': atm_strike,
            'expiry': expiry,
            'type': option_type,
            'bid': bid,
            'ask': ask,
            'mid': mid,
            'underlying_price': underlying_price
        }
    
    def execute_trade(self, webhook_data: Dict) -> Dict:
        """
        Execute trade based on webhook data
        
        Returns:
            {
                'success': bool,
                'message': str,
                'trade': dict or None,
                'account_balance': float,
                'error': str or None,
                'timeframe': str
            }
        """
        try:
            # Extract data
            ticker = webhook_data.get('ticker', 'QQQ')
            action = webhook_data.get('action', '').lower()
            contracts_value = self._parse_position_size(webhook_data.get('contracts'))
            contracts = int(contracts_value) if contracts_value is not None else 0
            try:
                price = float(webhook_data.get('price', 0))
            except (TypeError, ValueError):
                price = 0.0
            timeframe = self._get_timeframe(webhook_data)
            asset_type = self._detect_asset_type(webhook_data)
            
            # Extract comment/signal for TP tracking
            comment = webhook_data.get('comment') or webhook_data.get('signal') or ''
            
            normalized_action, normalization_reason = self._normalize_action(action, webhook_data)
            if normalization_reason:
                cprint(f"   🔄 Normalized action {action.upper()} → {normalized_action.upper()} ({normalization_reason})", "yellow")
            action = normalized_action
            
            cprint(f"\n📡 Webhook: {action.upper()} {contracts} {ticker} @ ${price} ({timeframe})", "cyan")
            if comment:
                cprint(f"   Signal: {comment}", "yellow")
            cprint(f"   Asset Type: {asset_type.upper()}", "cyan")
            
            # Normalize close/exit/TP actions
            if action in ['close', 'exit', 'tp1', 'tp2', 'sl']:
                action = 'close'
            
            # Validate action
            if action not in ['buy', 'sell', 'close']:
                return {
                    'success': False,
                    'message': f'Unsupported action: {action}',
                    'trade': None,
                    'account_balance': self.account['account_balance'],
                    'error': f'Action "{action}" not supported',
                    'timeframe': timeframe
                }
            
            # Execute based on asset type
            if asset_type == 'stock':
                return self._execute_stock_trade(
                    ticker, action, contracts, price, timeframe, comment
                )
            else:
                return self._execute_options_trade(
                    ticker, action, contracts_value, price, timeframe, comment, webhook_data
                )
        
        except Exception as e:
            cprint(f"❌ Trade execution error: {e}", "red")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': 'Trade execution failed',
                'trade': None,
                'account_balance': 0,
                'error': str(e)
            }
    
    def _execute_stock_trade(self, ticker: str, action: str, 
                            contracts: int, price: float, timeframe: str, comment: str = '') -> Dict:
        """Execute stock trade (no 100x multiplier)"""
        
        # Calculate cost/proceeds (NO 100x multiplier for stocks)
        cost_basis = contracts * price
        
        if action == 'buy':
            # Check balance
            if self.account['account_balance'] < cost_basis:
                cprint(f"❌ Insufficient balance: need ${cost_basis:.2f}, have ${self.account['account_balance']:.2f}", "red")
                return {
                    'success': False,
                    'message': 'Insufficient balance',
                    'trade': None,
                    'account_balance': self.account['account_balance'],
                    'error': f'Need ${cost_basis:.2f}, have ${self.account["account_balance"]:.2f}',
                    'timeframe': timeframe
                }
            
            # Deduct balance
            self.account['account_balance'] -= cost_basis
            
            # Create position
            trade = {
                'id': f"{ticker}_{timeframe}_{datetime.now().timestamp()}",
                'type': 'BUY',
                'asset_type': 'STOCK',
                'ticker': ticker,
                'contracts': contracts,
                'entry_price': price,
                'cost_basis': cost_basis,
                'entry_time': datetime.now().strftime('%b %d, %Y, %H:%M:%S'),
                'status': 'OPEN',
                'pnl': 0,
                'pnl_percent': 0,
                'timeframe': timeframe,
                'signal': comment
            }
            
            self.account['open_positions'].append(trade)
            
            cprint(f"✅ STOCK BUY: {contracts} {ticker} @ ${price} = ${cost_basis:.2f}", "green")
            cprint(f"   Balance: ${self.account['account_balance']:.2f}", "green")
            
            return {
                'success': True,
                'message': f'Stock BUY executed',
                'trade': trade,
                'account_balance': self.account['account_balance'],
                'error': None,
                'timeframe': timeframe
            }
        
        elif action == 'sell':
            # Find open position
            open_pos = None
            for pos in self.account['open_positions']:
                if pos['ticker'] == ticker and pos['status'] == 'OPEN':
                    open_pos = pos
                    break
            
            if not open_pos:
                cprint(f"⚠️ No open position for {ticker}", "yellow")
                proceeds = cost_basis
                trade = None
            else:
                proceeds = cost_basis
                pnl = proceeds - open_pos['cost_basis']
                pnl_percent = (pnl / open_pos['cost_basis'] * 100) if open_pos['cost_basis'] > 0 else 0
                
                open_pos['exit_price'] = price
                open_pos['exit_time'] = datetime.now().strftime('%b %d, %Y, %H:%M:%S')
                open_pos['status'] = 'CLOSED'
                open_pos['pnl'] = pnl
                open_pos['pnl_percent'] = pnl_percent
                
                trade = {
                    'id': open_pos['id'],
                    'type': 'SELL',
                    'asset_type': 'STOCK',
                    'ticker': ticker,
                    'contracts': contracts,
                    'entry_price': open_pos['entry_price'],
                    'exit_price': price,
                    'entry_time': open_pos['entry_time'],
                    'exit_time': open_pos['exit_time'],
                    'cost_basis': open_pos['cost_basis'],
                    'proceeds': proceeds,
                    'pnl': pnl,
                    'pnl_percent': pnl_percent,
                    'status': 'CLOSED',
                    'timeframe': timeframe
                }
                self.account['trades'].append(trade)
                
                cprint(f"✅ STOCK SELL: {contracts} {ticker} @ ${price} = ${proceeds:.2f}", "green")
                cprint(f"   P&L: ${pnl:+.2f} ({pnl_percent:+.2f}%)", "green")
            
            self.account['account_balance'] += proceeds
            cprint(f"   Balance: ${self.account['account_balance']:.2f}", "green")
            
            return {
                'success': True,
                'message': f'Stock SELL executed',
                'trade': trade,
                'account_balance': self.account['account_balance'],
                'error': None,
                'timeframe': timeframe
            }
    
    def _execute_options_trade(self, ticker: str, action: str,
                              contracts_value, price: float, timeframe: str, comment: str = '',
                              webhook_data: Optional[Dict] = None) -> Dict:
        """Execute options trade (with 100x multiplier)
        
        Note: Strategy sends shares (e.g., 100), we convert to option contracts (e.g., 1)
        """
        
        # Convert shares to option contracts (1 contract = 100 shares)
        option_contracts = self._shares_to_option_contracts(contracts_value)
        if not option_contracts:
            option_contracts = 1  # Minimum 1 contract
        
        share_display = contracts_value if contracts_value is not None else 'unknown'
        cprint(f"   Converting {share_display} shares → {option_contracts} option contract(s)", "cyan")
        
        # Fetch option data (pass webhook price for accurate ATM strike)
        option_data = self._get_option_data(ticker, action, webhook_price=price)
        
        # Calculate cost/proceeds (WITH 100x multiplier for options)
        cost_basis = option_contracts * option_data['mid'] * 100
        
        if action == 'buy':
            # Check balance
            if self.account['account_balance'] < cost_basis:
                cprint(f"❌ Insufficient balance: need ${cost_basis:.2f}, have ${self.account['account_balance']:.2f}", "red")
                return {
                    'success': False,
                    'message': 'Insufficient balance',
                    'trade': None,
                    'account_balance': self.account['account_balance'],
                    'error': f'Need ${cost_basis:.2f}, have ${self.account["account_balance"]:.2f}',
                    'timeframe': timeframe
                }
            
            # Deduct balance
            self.account['account_balance'] -= cost_basis
            
            # Create position
            trade_direction = 'long'
            trade = {
                'id': f"{option_data['option_symbol']}_{timeframe}_{datetime.now().timestamp()}",
                'type': 'BUY',
                'asset_type': 'OPTION',
                'option_symbol': option_data['option_symbol'],
                'option_type': option_data['type'],
                'ticker': ticker,
                'strike': option_data['strike'],
                'expiry': option_data['expiry'],
                'contracts': option_contracts,  # Converted from shares
                'initial_contracts': option_contracts,
                'remaining_contracts': option_contracts,
                'entry_price': option_data['mid'],
                'cost_basis': cost_basis,
                'remaining_cost_basis': cost_basis,
                'entry_time': datetime.now().strftime('%b %d, %Y, %H:%M:%S'),
                'status': 'OPEN',
                'pnl': 0,
                'pnl_percent': 0,
                'unrealizedPnl': 0,
                'timeframe': timeframe,
                'underlying_price': option_data['underlying_price'],
                'signal': comment,
                'direction': trade_direction
            }
            
            self.account['open_positions'].append(trade)
            
            cprint(f"✅ OPTION BUY: {option_contracts} {option_data['type']} {ticker} ${option_data['strike']} @ ${option_data['mid']} = ${cost_basis:.2f}", "green")
            cprint(f"   Symbol: {option_data['option_symbol']}", "green")
            cprint(f"   Balance: ${self.account['account_balance']:.2f}", "green")
            
            return {
                'success': True,
                'message': f'Option BUY executed',
                'trade': trade,
                'account_balance': self.account['account_balance'],
                'error': None,
                'timeframe': timeframe
            }
        
        elif action == 'sell':
            # SELL signal = Open a PUT position (not close CALL)
            # Check balance
            if self.account['account_balance'] < cost_basis:
                cprint(f"❌ Insufficient balance: need ${cost_basis:.2f}, have ${self.account['account_balance']:.2f}", "red")
                return {
                    'success': False,
                    'message': 'Insufficient balance',
                    'trade': None,
                    'account_balance': self.account['account_balance'],
                    'error': f'Need ${cost_basis:.2f}, have ${self.account["account_balance"]:.2f}',
                    'timeframe': timeframe
                }
            
            # Deduct balance
            self.account['account_balance'] -= cost_basis
            
            # Create PUT position
            trade_direction = 'short'
            trade = {
                'id': f"{option_data['option_symbol']}_{timeframe}_{datetime.now().timestamp()}",
                'type': 'SELL',
                'asset_type': 'OPTION',
                'option_symbol': option_data['option_symbol'],
                'option_type': option_data['type'],  # PUT
                'ticker': ticker,
                'strike': option_data['strike'],
                'expiry': option_data['expiry'],
                'contracts': option_contracts,  # Converted from shares
                'initial_contracts': option_contracts,
                'remaining_contracts': option_contracts,
                'entry_price': option_data['mid'],
                'cost_basis': cost_basis,
                'remaining_cost_basis': cost_basis,
                'entry_time': datetime.now().strftime('%b %d, %Y, %H:%M:%S'),
                'status': 'OPEN',
                'pnl': 0,
                'pnl_percent': 0,
                'unrealizedPnl': 0,
                'timeframe': timeframe,
                'underlying_price': option_data['underlying_price'],
                'signal': comment,
                'direction': trade_direction
            }
            
            self.account['open_positions'].append(trade)
            
            cprint(f"✅ OPTION SELL: {option_contracts} {option_data['type']} {ticker} ${option_data['strike']} @ ${option_data['mid']} = ${cost_basis:.2f}", "green")
            cprint(f"   Symbol: {option_data['option_symbol']}", "green")
            cprint(f"   Balance: ${self.account['account_balance']:.2f}", "green")
            
            return {
                'success': True,
                'message': f'Option SELL (PUT) executed',
                'trade': trade,
                'account_balance': self.account['account_balance'],
                'error': None,
                'timeframe': timeframe
            }
        
        elif action == 'close':
            # CLOSE/EXIT/TP1/TP2/SL = Close the most recent open position for this ticker
            desired_direction = self._get_desired_position_direction(webhook_data or {})
            open_candidates = [
                pos for pos in self.account['open_positions']
                if pos.get('ticker') == ticker and pos['status'] == 'OPEN'
            ]
            
            if not open_candidates:
                cprint(f"⚠️ No open position for {ticker} to close", "yellow")
                return {
                    'success': False,
                    'message': f'No open position for {ticker}',
                    'trade': None,
                    'account_balance': self.account['account_balance'],
                    'error': f'No open position found',
                    'timeframe': timeframe
                }
            
            def _matches_direction(pos):
                if not desired_direction:
                    return True
                direction = (pos.get('direction') or '').lower()
                option_type = (pos.get('option_type') or '').lower()
                if desired_direction == 'long':
                    return direction == 'long' or option_type == 'call'
                if desired_direction == 'short':
                    return direction == 'short' or option_type == 'put'
                return True
            
            directional_matches = [pos for pos in open_candidates if _matches_direction(pos)]
            target_list = directional_matches if directional_matches else open_candidates
            open_pos = target_list[-1]
            
            close_contracts = self._determine_close_contracts(contracts_value, webhook_data or {}, open_pos)
            option_exit_price = self._get_option_close_price(open_pos, price)
            
            remaining_contracts = open_pos.get('remaining_contracts', open_pos.get('contracts', close_contracts))
            remaining_contracts = max(remaining_contracts, close_contracts)
            remaining_cost_basis = open_pos.get('remaining_cost_basis', open_pos.get('cost_basis', 0))
            cost_per_contract = (remaining_cost_basis / remaining_contracts) if remaining_contracts > 0 else (open_pos.get('entry_price', 0) * 100)
            cost_basis_closed = cost_per_contract * close_contracts
            
            proceeds = close_contracts * option_exit_price * 100
            pnl = proceeds - cost_basis_closed
            entry_price = open_pos.get('entry_price', 0)
            pnl_percent = ((option_exit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            
            remaining_after = max(remaining_contracts - close_contracts, 0)
            open_pos['remaining_contracts'] = remaining_after
            open_pos['contracts'] = remaining_after
            open_pos['remaining_cost_basis'] = max(remaining_cost_basis - cost_basis_closed, 0)
            open_pos['exit_time'] = datetime.now().strftime('%b %d, %Y, %H:%M:%S')
            open_pos['realized_pnl'] = open_pos.get('realized_pnl', 0) + pnl
            open_pos['pnl_percent'] = pnl_percent
            
            if remaining_after <= 0:
                open_pos['status'] = 'CLOSED'
                open_pos['exit_price'] = option_exit_price
                open_pos['pnl'] = open_pos['realized_pnl']
            else:
                open_pos['status'] = 'OPEN'
                open_pos['exit_price'] = option_exit_price
                open_pos['pnl'] = open_pos.get('realized_pnl', 0)
            
            trade_status = 'CLOSED' if remaining_after <= 0 else 'PARTIAL'
            trade_id = open_pos['id'] if trade_status == 'CLOSED' else f"{open_pos['id']}_partial_{datetime.now().timestamp()}"
            
            trade = {
                'id': trade_id,
                'type': open_pos['type'],
                'asset_type': 'OPTION',
                'option_symbol': open_pos.get('option_symbol'),
                'option_type': open_pos.get('option_type'),
                'ticker': ticker,
                'strike': open_pos.get('strike'),
                'expiry': open_pos.get('expiry'),
                'contracts': close_contracts,
                'entry_price': open_pos['entry_price'],
                'exit_price': option_exit_price,
                'entry_time': open_pos['entry_time'],
                'exit_time': open_pos['exit_time'],
                'cost_basis': cost_basis_closed,
                'proceeds': proceeds,
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'status': trade_status,
                'timeframe': timeframe,
                'signal': comment,
                'remaining_contracts': remaining_after,
                'direction': open_pos.get('direction')
            }
            self.account['trades'].append(trade)
            
            # Update balance
            self.account['account_balance'] += proceeds
            
            cprint(f"✅ OPTION CLOSE: Closed {close_contracts} contract(s) @ ${option_exit_price:.2f} = ${proceeds:.2f}", "green")
            cprint(f"   P&L: ${pnl:+.2f} ({pnl_percent:+.2f}%) | Remaining contracts: {remaining_after}", "green")
            cprint(f"   Balance: ${self.account['account_balance']:.2f}", "green")
            
            return {
                'success': True,
                'message': f'Option {trade_status} exit executed',
                'trade': trade,
                'account_balance': self.account['account_balance'],
                'error': None,
                'timeframe': timeframe
            }
    
    def get_account_state(self) -> Dict:
        """Get account state"""
        return self.account
    
    def save_state(self, filepath: str):
        """Save account to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.account, f, indent=2)
            cprint(f"✅ Saved trading state to {filepath}", "green")
        except Exception as e:
            cprint(f"❌ Error saving state: {e}", "red")
    
    def load_state(self, filepath: str):
        """Load account from JSON file"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    self.account = json.load(f)
                cprint(f"✅ Loaded trading state from {filepath}", "green")
        except Exception as e:
            cprint(f"❌ Error loading state: {e}", "red")
