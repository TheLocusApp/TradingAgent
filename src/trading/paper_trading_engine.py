#!/usr/bin/env python3
"""
🌙 Moon Dev's Paper Trading Engine
Handles webhook-based trade execution with proper asset type detection
Supports both stock and options trading with per-timeframe accounts
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional, List
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
            contracts = int(webhook_data.get('contracts', 0))
            price = float(webhook_data.get('price', 0))
            timeframe = self._get_timeframe(webhook_data)
            asset_type = self._detect_asset_type(webhook_data)
            
            cprint(f"\n📡 Webhook: {action.upper()} {contracts} {ticker} @ ${price} ({timeframe})", "cyan")
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
                    ticker, action, contracts, price, timeframe
                )
            else:
                return self._execute_options_trade(
                    ticker, action, contracts, price, timeframe
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
                            contracts: int, price: float, timeframe: str) -> Dict:
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
                'timeframe': timeframe
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
                              contracts: int, price: float, timeframe: str) -> Dict:
        """Execute options trade (with 100x multiplier)
        
        Note: Strategy sends shares (e.g., 100), we convert to option contracts (e.g., 1)
        """
        
        # Convert shares to option contracts (1 contract = 100 shares)
        option_contracts = int(contracts / 100)
        if option_contracts < 1:
            option_contracts = 1  # Minimum 1 contract
        
        cprint(f"   Converting {contracts} shares → {option_contracts} option contract(s)", "cyan")
        
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
                'entry_price': option_data['mid'],
                'cost_basis': cost_basis,
                'entry_time': datetime.now().strftime('%b %d, %Y, %H:%M:%S'),
                'status': 'OPEN',
                'pnl': 0,
                'pnl_percent': 0,
                'unrealizedPnl': 0,
                'timeframe': timeframe,
                'underlying_price': option_data['underlying_price']
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
                'entry_price': option_data['mid'],
                'cost_basis': cost_basis,
                'entry_time': datetime.now().strftime('%b %d, %Y, %H:%M:%S'),
                'status': 'OPEN',
                'pnl': 0,
                'pnl_percent': 0,
                'unrealizedPnl': 0,
                'timeframe': timeframe,
                'underlying_price': option_data['underlying_price']
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
            open_pos = None
            for pos in reversed(self.account['open_positions']):
                if pos.get('ticker') == ticker and pos['status'] == 'OPEN':
                    open_pos = pos
                    break
            
            if not open_pos:
                cprint(f"⚠️ No open position for {ticker} to close", "yellow")
                return {
                    'success': False,
                    'message': f'No open position for {ticker}',
                    'trade': None,
                    'account_balance': self.account['account_balance'],
                    'error': f'No open position found',
                    'timeframe': timeframe
                }
            
            # Calculate P&L
            proceeds = option_contracts * price * 100
            pnl = proceeds - open_pos['cost_basis']
            pnl_percent = (pnl / open_pos['cost_basis'] * 100) if open_pos['cost_basis'] > 0 else 0
            
            # Update open position
            open_pos['exit_price'] = price
            open_pos['exit_time'] = datetime.now().strftime('%b %d, %Y, %H:%M:%S')
            open_pos['status'] = 'CLOSED'
            open_pos['pnl'] = pnl
            open_pos['pnl_percent'] = pnl_percent
            
            # Create closed trade record
            trade = {
                'id': open_pos['id'],
                'type': open_pos['type'],
                'asset_type': 'OPTION',
                'option_symbol': open_pos.get('option_symbol'),
                'option_type': open_pos.get('option_type'),
                'ticker': ticker,
                'strike': open_pos.get('strike'),
                'expiry': open_pos.get('expiry'),
                'contracts': option_contracts,
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
            
            # Update balance
            self.account['account_balance'] += proceeds
            
            cprint(f"✅ OPTION CLOSE: {option_contracts} {open_pos.get('option_type')} {ticker} @ ${price} = ${proceeds:.2f}", "green")
            cprint(f"   P&L: ${pnl:+.2f} ({pnl_percent:+.2f}%)", "green")
            cprint(f"   Balance: ${self.account['account_balance']:.2f}", "green")
            
            return {
                'success': True,
                'message': f'Option CLOSE executed',
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
