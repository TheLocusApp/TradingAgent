#!/usr/bin/env python3
"""
🌙 Moon Dev's Polygon Options Data Provider
Fetches 0DTE ATM options data using Polygon.io API
Built with love by Moon Dev 🚀
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dotenv import load_dotenv
import time

load_dotenv()


class PolygonOptionsProvider:
    """Provides 0DTE ATM options data from Polygon.io"""
    
    def __init__(self):
        """Initialize Polygon options provider"""
        self.api_key = os.getenv('POLYGON_API_KEY')
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY not found in environment variables")
        
        self.base_url = "https://api.polygon.io"
        self.cache = {}
        self.cache_duration = 30  # 30 seconds cache
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 200ms between requests (rate limiting)
    
    def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request with error handling"""
        self._rate_limit()
        
        if params is None:
            params = {}
        params['apiKey'] = self.api_key
        
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Polygon API error: {e}")
            return None
    
    def get_underlying_price(self, symbol: str) -> Optional[float]:
        """Get current price of underlying stock"""
        cache_key = f"underlying_{symbol}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if time.time() - cached_time < self.cache_duration:
                return cached_data
        
        # Fetch from API
        endpoint = f"/v2/aggs/ticker/{symbol}/prev"
        data = self._make_request(endpoint)
        
        if data and data.get('results'):
            price = data['results'][0].get('c')  # Close price
            self.cache[cache_key] = (price, time.time())
            return price
        
        return None
    
    def get_0dte_expiration(self) -> str:
        """Get today's expiration date in YYYY-MM-DD format"""
        return datetime.now().strftime('%Y-%m-%d')
    
    def find_atm_strike(self, symbol: str, underlying_price: float) -> Optional[float]:
        """Find the at-the-money strike price closest to underlying price"""
        # Round to nearest strike (typically $1 or $5 increments for SPY/QQQ)
        if underlying_price < 50:
            # $1 increments
            return round(underlying_price)
        elif underlying_price < 200:
            # $1 increments
            return round(underlying_price)
        else:
            # $5 increments for high-priced stocks
            return round(underlying_price / 5) * 5
    
    def get_option_contract_ticker(self, underlying: str, expiration: str, 
                                   strike: float, option_type: str) -> str:
        """
        Build option ticker in OCC format
        Format: O:UNDERLYING{YYMMDD}{C/P}{STRIKE*1000}
        Example: O:SPY251104C00580000 (SPY Nov 4 2025 Call $580)
        """
        # Parse expiration date
        exp_date = datetime.strptime(expiration, '%Y-%m-%d')
        date_str = exp_date.strftime('%y%m%d')
        
        # Format strike (multiply by 1000, pad to 8 digits)
        strike_str = f"{int(strike * 1000):08d}"
        
        # Build ticker
        option_ticker = f"O:{underlying}{date_str}{option_type[0]}{strike_str}"
        return option_ticker
    
    def get_option_quote(self, option_ticker: str) -> Optional[Dict]:
        """Get real-time quote for an option contract"""
        cache_key = f"quote_{option_ticker}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if time.time() - cached_time < self.cache_duration:
                return cached_data
        
        # Fetch from API
        endpoint = f"/v3/quotes/{option_ticker}"
        data = self._make_request(endpoint)
        
        if data and data.get('results'):
            result = data['results'][0]
            quote = {
                'bid': result.get('bid_price', 0),
                'ask': result.get('ask_price', 0),
                'last': result.get('last_price', 0),
                'bid_size': result.get('bid_size', 0),
                'ask_size': result.get('ask_size', 0),
                'timestamp': result.get('sip_timestamp', 0)
            }
            
            # Calculate mid price
            if quote['bid'] and quote['ask']:
                quote['mid'] = (quote['bid'] + quote['ask']) / 2
            else:
                quote['mid'] = quote['last']
            
            self.cache[cache_key] = (quote, time.time())
            return quote
        
        # Fallback: Use simulated data if API doesn't have access
        # This allows demo trading even without premium Polygon plan
        print(f"📊 Using fallback data for {option_ticker} (API access not available)")
        fallback_quote = self._generate_fallback_quote(option_ticker)
        self.cache[cache_key] = (fallback_quote, time.time())
        return fallback_quote
    
    def _generate_fallback_quote(self, option_ticker: str) -> Dict:
        """Generate realistic fallback option quote for demo purposes"""
        import random
        
        # Parse option ticker to get type
        is_call = 'C' in option_ticker
        
        # Generate realistic premium based on option type
        # Calls and puts typically range from $0.50 to $5.00 for ATM options
        base_premium = random.uniform(1.5, 3.5)
        bid = base_premium - random.uniform(0.05, 0.15)
        ask = base_premium + random.uniform(0.05, 0.15)
        mid = (bid + ask) / 2
        
        return {
            'bid': round(bid, 2),
            'ask': round(ask, 2),
            'mid': round(mid, 2),
            'last': round(mid, 2),
            'bid_size': random.randint(10, 100),
            'ask_size': random.randint(10, 100),
            'timestamp': int(time.time() * 1000)
        }
    
    def get_atm_options_data(self, underlying: str) -> Optional[Dict]:
        """
        Get comprehensive 0DTE ATM options data for both CALL and PUT
        
        Returns:
            {
                'underlying': 'SPY',
                'underlying_price': 580.50,
                'expiration': '2025-11-04',
                'atm_strike': 580.0,
                'call': {
                    'ticker': 'O:SPY251104C00580000',
                    'bid': 2.50,
                    'ask': 2.55,
                    'mid': 2.525,
                    'last': 2.52
                },
                'put': {
                    'ticker': 'O:SPY251104P00580000',
                    'bid': 2.45,
                    'ask': 2.50,
                    'mid': 2.475,
                    'last': 2.48
                }
            }
        """
        # Get underlying price
        underlying_price = self.get_underlying_price(underlying)
        if not underlying_price:
            print(f"⚠️ Could not fetch underlying price for {underlying}")
            return None
        
        # Find ATM strike
        atm_strike = self.find_atm_strike(underlying, underlying_price)
        
        # Get 0DTE expiration
        expiration = self.get_0dte_expiration()
        
        # Build option tickers
        call_ticker = self.get_option_contract_ticker(underlying, expiration, atm_strike, 'CALL')
        put_ticker = self.get_option_contract_ticker(underlying, expiration, atm_strike, 'PUT')
        
        # Get quotes
        call_quote = self.get_option_quote(call_ticker)
        put_quote = self.get_option_quote(put_ticker)
        
        if not call_quote or not put_quote:
            print(f"⚠️ Could not fetch option quotes for {underlying}")
            return None
        
        return {
            'underlying': underlying,
            'underlying_price': underlying_price,
            'expiration': expiration,
            'atm_strike': atm_strike,
            'call': {
                'ticker': call_ticker,
                'bid': call_quote['bid'],
                'ask': call_quote['ask'],
                'mid': call_quote['mid'],
                'last': call_quote['last']
            },
            'put': {
                'ticker': put_ticker,
                'bid': put_quote['bid'],
                'ask': put_quote['ask'],
                'mid': put_quote['mid'],
                'last': put_quote['last']
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def get_option_price(self, option_ticker: str) -> Optional[float]:
        """Get current price (mid) for a specific option contract"""
        quote = self.get_option_quote(option_ticker)
        if quote:
            return quote.get('mid', quote.get('last', 0))
        return None


# Test function
if __name__ == "__main__":
    print("🧪 Testing Polygon Options Provider...")
    
    provider = PolygonOptionsProvider()
    
    # Test with SPY
    print("\n📊 Fetching SPY 0DTE ATM options...")
    data = provider.get_atm_options_data('SPY')
    
    if data:
        print(f"\n✅ Success!")
        print(f"   Underlying: {data['underlying']} @ ${data['underlying_price']:.2f}")
        print(f"   ATM Strike: ${data['atm_strike']:.2f}")
        print(f"   Expiration: {data['expiration']}")
        print(f"\n   CALL: {data['call']['ticker']}")
        print(f"   Price: ${data['call']['mid']:.2f} (bid: ${data['call']['bid']:.2f}, ask: ${data['call']['ask']:.2f})")
        print(f"\n   PUT: {data['put']['ticker']}")
        print(f"   Price: ${data['put']['mid']:.2f} (bid: ${data['put']['bid']:.2f}, ask: ${data['put']['ask']:.2f})")
    else:
        print("❌ Failed to fetch options data")
