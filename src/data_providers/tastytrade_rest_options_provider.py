#!/usr/bin/env python3
"""
🌙 Moon Dev's Tastytrade REST API Options Provider
Real-time 0DTE ATM options quotes using Tastytrade REST API
Built with love by Moon Dev 🚀
"""

import os
import requests
import time
from datetime import date
from typing import Dict, Optional
from dotenv import load_dotenv
from termcolor import cprint

load_dotenv()


class TastytradeRestOptionsProvider:
    """Provides real-time 0DTE ATM options quotes from Tastytrade REST API"""
    
    BASE_URL = "https://api.tastytrade.com"
    
    def __init__(self):
        """Initialize Tastytrade REST options provider"""
        self.username = os.getenv('TASTYTRADE_USERNAME')
        self.password = os.getenv('TASTYTRADE_PASSWORD')
        self.account_number = os.getenv('TASTYTRADE_ACCOUNT_NUMBER')
        
        if not all([self.username, self.password, self.account_number]):
            raise ValueError("TASTYTRADE_USERNAME, TASTYTRADE_PASSWORD, and TASTYTRADE_ACCOUNT_NUMBER required in .env")
        
        self.session_token = None
        self.cache = {}
        
        # Authenticate
        self._authenticate()
        cprint("✅ Tastytrade REST Options Provider initialized", "green")
    
    def _authenticate(self):
        """Authenticate with Tastytrade and get session token"""
        try:
            cprint("🔐 Authenticating with Tastytrade REST API...", "cyan")
            
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
            
            cprint(f"✅ Authenticated successfully", "green")
            cprint(f"   User: {data['data']['user']['username']}", "cyan")
            
        except Exception as e:
            cprint(f"❌ Authentication failed: {e}", "red")
            raise
    
    def _get_headers(self) -> Dict:
        """Get request headers with authentication"""
        return {
            "Authorization": f"Bearer {self.session_token}",
            "Content-Type": "application/json"
        }
    
    def get_option_quote(self, option_symbol: str) -> Optional[Dict]:
        """Get real-time quote for an option using REST API"""
        try:
            cache_key = f"quote_{option_symbol}"
            
            # Check cache (10 second TTL)
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < 10:
                    return cached_data
            
            # Get quote from REST API
            # Format: /market-data/quotes/{symbol}
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
    
    def get_0dte_atm_options(self, underlying: str, atm_strike: float = None) -> Optional[Dict]:
        """Get 0DTE ATM options with real quotes"""
        try:
            cprint(f"📊 Fetching {underlying} 0DTE ATM options...", "cyan")
            
            from tastytrade.instruments import Equity, get_option_chain, OptionType
            from tastytrade import Session
            
            # Create SDK session for getting option chain
            session = Session(login=self.username, password=self.password)
            
            # Get equity
            equity = Equity.get_equity(session, underlying)
            if not equity:
                cprint(f"⚠️ Could not find equity {underlying}", "yellow")
                return None
            
            # Get option chain
            option_chain = get_option_chain(session, underlying)
            if not option_chain:
                cprint(f"⚠️ No option chain found for {underlying}", "yellow")
                return None
            
            # Find today's expiration (0DTE)
            today = date.today()
            today_options = option_chain.get(today)
            
            if not today_options:
                cprint(f"⚠️ No 0DTE options found for {underlying}", "yellow")
                return None
            
            # Get unique strikes
            strikes = sorted(set(opt.strike_price for opt in today_options))
            if not strikes:
                cprint(f"⚠️ No strikes found for {underlying}", "yellow")
                return None
            
            # Use provided strike or find ATM
            if atm_strike is None:
                # For ATM, use middle strike
                atm_strike = strikes[len(strikes) // 2]
            
            # Find CALL and PUT options at specified strike
            call_opt = None
            put_opt = None
            
            for opt in today_options:
                if opt.strike_price == atm_strike:
                    if opt.option_type == OptionType.CALL:
                        call_opt = opt
                    elif opt.option_type == OptionType.PUT:
                        put_opt = opt
            
            if not call_opt or not put_opt:
                cprint(f"⚠️ Could not find CALL/PUT at strike {atm_strike}", "yellow")
                return None
            
            cprint(f"✅ Found options at strike ${atm_strike}", "green")
            cprint(f"   CALL: {call_opt.symbol}", "cyan")
            cprint(f"   PUT: {put_opt.symbol}", "cyan")
            
            # Get real quotes from REST API
            cprint(f"📡 Fetching real quotes from REST API...", "cyan")
            call_quote = self.get_option_quote(call_opt.symbol)
            put_quote = self.get_option_quote(put_opt.symbol)
            
            if not call_quote or not put_quote:
                cprint(f"⚠️ Could not fetch quotes", "yellow")
                return None
            
            return {
                'underlying': underlying,
                'atm_strike': float(atm_strike),
                'expiration': today.isoformat(),
                'call': {
                    'symbol': call_opt.symbol,
                    'streamer_symbol': call_opt.streamer_symbol,
                    'bid': call_quote['bid'],
                    'ask': call_quote['ask'],
                    'mid': call_quote['mid'],
                    'last': call_quote['last']
                },
                'put': {
                    'symbol': put_opt.symbol,
                    'streamer_symbol': put_opt.streamer_symbol,
                    'bid': put_quote['bid'],
                    'ask': put_quote['ask'],
                    'mid': put_quote['mid'],
                    'last': put_quote['last']
                }
            }
        
        except Exception as e:
            cprint(f"❌ Error getting ATM options: {e}", "red")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    # Test the provider
    print("\n🧪 Testing Tastytrade REST Options Provider...\n")
    
    try:
        provider = TastytradeRestOptionsProvider()
        
        print("📊 Fetching QQQ 621 0DTE options...")
        data = provider.get_0dte_atm_options('QQQ', atm_strike=621)
        
        if data:
            print(f"\n✅ Success!")
            print(f"   Underlying: {data['underlying']}")
            print(f"   ATM Strike: ${data['atm_strike']}")
            print(f"   Expiration: {data['expiration']}")
            print(f"\n   CALL: {data['call']['symbol']}")
            print(f"   Bid: ${data['call']['bid']:.2f}, Ask: ${data['call']['ask']:.2f}, Mid: ${data['call']['mid']:.2f}")
            print(f"\n   PUT: {data['put']['symbol']}")
            print(f"   Bid: ${data['put']['bid']:.2f}, Ask: ${data['put']['ask']:.2f}, Mid: ${data['put']['mid']:.2f}")
        else:
            print("❌ Failed to get options data")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
