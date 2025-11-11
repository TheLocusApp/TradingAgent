#!/usr/bin/env python3
"""
🌙 Moon Dev's Tastytrade REST API Options Provider
Real-time 0DTE ATM options data using Tastytrade REST API
Built with love by Moon Dev 🚀
"""

import os
import requests
import time
from datetime import datetime, date
from typing import Dict, Optional, List
from dotenv import load_dotenv
from termcolor import cprint

load_dotenv()


class TastytradeRestProvider:
    """Provides real-time 0DTE ATM options data from Tastytrade REST API"""
    
    BASE_URL = "https://api.tastytrade.com"
    
    def __init__(self):
        """Initialize Tastytrade REST provider"""
        self.username = os.getenv('TASTYTRADE_USERNAME')
        self.password = os.getenv('TASTYTRADE_PASSWORD')
        self.account_number = os.getenv('TASTYTRADE_ACCOUNT_NUMBER')
        
        if not all([self.username, self.password, self.account_number]):
            raise ValueError("TASTYTRADE_USERNAME, TASTYTRADE_PASSWORD, and TASTYTRADE_ACCOUNT_NUMBER required in .env")
        
        self.session_token = None
        self.user_id = None
        self.account_id = None
        self.cache = {}  # Simple cache for quotes
        
        # Authenticate
        self._authenticate()
        cprint("✅ Tastytrade REST Provider initialized", "green")
    
    def _authenticate(self):
        """Authenticate with Tastytrade and get session token"""
        try:
            cprint("🔐 Authenticating with Tastytrade...", "cyan")
            
            url = f"{self.BASE_URL}/sessions"
            payload = {
                "login": self.username,
                "password": self.password,
                "remember-me": True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            self.session_token = data['data']['session-token']
            self.user_id = data['data']['user']['external-id']
            
            cprint(f"✅ Authenticated successfully", "green")
            cprint(f"   User: {data['data']['user']['username']}", "cyan")
            
            # Get account ID
            self._get_account_id()
            
        except Exception as e:
            cprint(f"❌ Authentication failed: {e}", "red")
            raise
    
    def _get_account_id(self):
        """Get account ID from account number"""
        try:
            # For now, use account number directly
            # The API endpoints require different authentication
            self.account_id = self.account_number
            cprint(f"   Account: {self.account_id}", "cyan")
        
        except Exception as e:
            cprint(f"❌ Failed to get account ID: {e}", "red")
            raise
    
    def _get_headers(self) -> Dict:
        """Get request headers with authentication"""
        return {
            "Authorization": f"Bearer {self.session_token}",
            "Content-Type": "application/json"
        }
    
    def get_underlying_price(self, symbol: str) -> Optional[float]:
        """Get current price of underlying stock"""
        try:
            url = f"{self.BASE_URL}/quote-streamer-tokens"
            headers = self._get_headers()
            
            # Get quote token for streaming
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # For now, return None - we'll use the option chain endpoint
            return None
        
        except Exception as e:
            cprint(f"⚠️ Error getting underlying price: {e}", "yellow")
            return None
    
    def get_option_chains(self, underlying: str) -> Optional[Dict]:
        """Get option chains for underlying symbol"""
        try:
            cache_key = f"chains_{underlying}"
            
            # Check cache (30 second TTL)
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < 30:
                    return cached_data
            
            url = f"{self.BASE_URL}/instruments/equities/{underlying}/option-chains"
            headers = self._get_headers()
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            chains = data.get('data', {}).get('items', [])
            
            # Cache the result
            self.cache[cache_key] = (chains, time.time())
            
            return chains
        
        except Exception as e:
            cprint(f"⚠️ Error getting option chains: {e}", "yellow")
            return None
    
    def get_option_quote(self, option_symbol: str) -> Optional[Dict]:
        """Get real-time quote for an option"""
        try:
            cache_key = f"quote_{option_symbol}"
            
            # Check cache (10 second TTL)
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < 10:
                    return cached_data
            
            url = f"{self.BASE_URL}/market-data/quotes/{option_symbol}"
            headers = self._get_headers()
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            quote_data = data.get('data', {})
            
            if quote_data:
                result = {
                    'bid': float(quote_data.get('bid', 0)),
                    'ask': float(quote_data.get('ask', 0)),
                    'mid': float(quote_data.get('mid', 0)),
                    'last': float(quote_data.get('last', 0)),
                    'bid_size': int(quote_data.get('bid-size', 0)),
                    'ask_size': int(quote_data.get('ask-size', 0)),
                    'timestamp': quote_data.get('timestamp', int(time.time() * 1000))
                }
                
                # Cache the result
                self.cache[cache_key] = (result, time.time())
                
                return result
            
            return None
        
        except Exception as e:
            cprint(f"⚠️ Error getting option quote for {option_symbol}: {e}", "yellow")
            return None
    
    def get_0dte_atm_options(self, underlying: str) -> Optional[Dict]:
        """Get 0DTE ATM CALL and PUT options"""
        try:
            cprint(f"📊 Fetching {underlying} 0DTE ATM options...", "cyan")
            
            # Get option chains
            chains = self.get_option_chains(underlying)
            if not chains:
                cprint(f"⚠️ No option chains found for {underlying}", "yellow")
                return None
            
            # Find today's expiration (0DTE)
            today = date.today().isoformat()
            today_chain = None
            
            for chain in chains:
                exp_date = chain.get('expiration-date')
                if exp_date == today:
                    today_chain = chain
                    break
            
            if not today_chain:
                cprint(f"⚠️ No 0DTE options found for {underlying}", "yellow")
                return None
            
            # Get strikes
            strikes = today_chain.get('strikes', [])
            if not strikes:
                cprint(f"⚠️ No strikes found for {underlying}", "yellow")
                return None
            
            # Find ATM strike (middle strike)
            atm_strike = strikes[len(strikes) // 2]
            
            # Build option symbols (Tastytrade format)
            exp_str = today.replace('-', '')[2:]  # Convert 2025-11-04 to 251104
            call_symbol = f".{underlying}{exp_str}C{int(atm_strike * 1000):08d}"
            put_symbol = f".{underlying}{exp_str}P{int(atm_strike * 1000):08d}"
            
            # Get quotes
            call_quote = self.get_option_quote(call_symbol)
            put_quote = self.get_option_quote(put_symbol)
            
            if not call_quote or not put_quote:
                cprint(f"⚠️ Could not fetch quotes for {underlying}", "yellow")
                return None
            
            return {
                'underlying': underlying,
                'atm_strike': atm_strike,
                'expiration': today,
                'call': {
                    'symbol': call_symbol,
                    'bid': call_quote['bid'],
                    'ask': call_quote['ask'],
                    'mid': call_quote['mid'],
                    'last': call_quote['last']
                },
                'put': {
                    'symbol': put_symbol,
                    'bid': put_quote['bid'],
                    'ask': put_quote['ask'],
                    'mid': put_quote['mid'],
                    'last': put_quote['last']
                }
            }
        
        except Exception as e:
            cprint(f"❌ Error getting ATM options: {e}", "red")
            return None


if __name__ == "__main__":
    # Test the provider
    print("\n🧪 Testing Tastytrade REST Provider...\n")
    
    try:
        provider = TastytradeRestProvider()
        
        print("📊 Fetching SPY 0DTE ATM options...")
        data = provider.get_0dte_atm_options('SPY')
        
        if data:
            print(f"\n✅ Success!")
            print(f"   Underlying: {data['underlying']}")
            print(f"   ATM Strike: ${data['atm_strike']}")
            print(f"   Expiration: {data['expiration']}")
            print(f"\n   CALL: {data['call']['symbol']}")
            print(f"   Price: ${data['call']['mid']} (bid: ${data['call']['bid']}, ask: ${data['call']['ask']})")
            print(f"\n   PUT: {data['put']['symbol']}")
            print(f"   Price: ${data['put']['mid']} (bid: ${data['put']['bid']}, ask: ${data['put']['ask']})")
        else:
            print("❌ Failed to get options data")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
