#!/usr/bin/env python3
"""
🌙 Moon Dev's Tastytrade Options Data Provider
Real-time 0DTE ATM options data using Tastytrade API
Built with love by Moon Dev 🚀
"""

import os
import asyncio
from datetime import datetime, date
from typing import Dict, Optional
from dotenv import load_dotenv
from termcolor import cprint

load_dotenv()


class TastytradeOptionsProvider:
    """Provides real-time 0DTE ATM options data from Tastytrade"""
    
    def __init__(self):
        """Initialize Tastytrade options provider"""
        # Tastytrade 9.10 uses login/password, not OAuth
        self.username = os.getenv('TASTYTRADE_USERNAME')
        self.password = os.getenv('TASTYTRADE_PASSWORD')
        self.account_number = os.getenv('TASTYTRADE_ACCOUNT_NUMBER')
        
        if not all([self.username, self.password, self.account_number]):
            raise ValueError("TASTYTRADE_USERNAME, TASTYTRADE_PASSWORD, and TASTYTRADE_ACCOUNT_NUMBER required in .env")
        
        self.session = None
        self.streamer = None
        self.live_prices = None
        
        cprint("✅ Tastytrade Options Provider initialized", "green")
    
    async def _init_session(self):
        """Initialize Tastytrade session with login credentials"""
        try:
            from tastytrade import Session
            # Tastytrade 9.10 uses login/password authentication
            self.session = Session(
                login=self.username,
                password=self.password
            )
            cprint("✅ Tastytrade session authenticated", "green")
        except Exception as e:
            cprint(f"❌ Failed to authenticate with Tastytrade: {e}", "red")
            raise
    
    async def _init_streamer(self):
        """Initialize Tastytrade data streamer"""
        try:
            if not self.session:
                await self._init_session()
            
            from tastytrade import DXLinkStreamer
            self.streamer = await DXLinkStreamer(self.session).__aenter__()
            cprint("✅ Tastytrade streamer connected", "green")
        except Exception as e:
            cprint(f"❌ Failed to connect to Tastytrade streamer: {e}", "red")
            raise
    
    def get_underlying_price(self, symbol: str) -> Optional[float]:
        """Get current price of underlying stock"""
        try:
            if not self.session:
                asyncio.run(self._init_session())
            
            from tastytrade import Quote
            
            # Get current quote
            quote = asyncio.run(self._get_quote(symbol))
            if quote:
                return (quote.bid_price + quote.ask_price) / 2
            return None
        except Exception as e:
            cprint(f"⚠️ Error getting underlying price for {symbol}: {e}", "yellow")
            return None
    
    async def _get_quote(self, symbol: str):
        """Get quote for a symbol"""
        try:
            from tastytrade import Quote
            
            if not self.streamer:
                await self._init_streamer()
            
            # Subscribe to quote
            await self.streamer.subscribe(Quote, [symbol])
            
            # Listen for quote
            async for quote in self.streamer.listen(Quote):
                if quote.event_symbol == symbol:
                    return quote
        except Exception as e:
            cprint(f"⚠️ Error getting quote: {e}", "yellow")
            return None
    
    def get_0dte_expiration(self) -> str:
        """Get today's expiration date in YYYY-MM-DD format"""
        return date.today().strftime('%Y-%m-%d')
    
    def _find_atm_strike(self, underlying_price: float) -> float:
        """Find ATM strike price (nearest $1 increment)"""
        return round(underlying_price)
    
    def get_option_quote(self, option_ticker: str) -> Optional[Dict]:
        """Get real-time quote for an option contract"""
        try:
            if not self.session:
                asyncio.run(self._init_session())
            
            quote = asyncio.run(self._get_option_quote_async(option_ticker))
            
            if quote:
                return {
                    'bid': round(quote.bid_price, 2),
                    'ask': round(quote.ask_price, 2),
                    'mid': round((quote.bid_price + quote.ask_price) / 2, 2),
                    'last': round(quote.ask_price, 2),  # Use ask as last
                    'bid_size': int(quote.bid_size),
                    'ask_size': int(quote.ask_size),
                    'timestamp': quote.bid_time
                }
            return None
        except Exception as e:
            cprint(f"⚠️ Error getting option quote for {option_ticker}: {e}", "yellow")
            return None
    
    async def _get_option_quote_async(self, option_ticker: str):
        """Get option quote asynchronously"""
        try:
            from tastytrade import Quote
            
            if not self.streamer:
                await self._init_streamer()
            
            # Subscribe to option quote
            await self.streamer.subscribe(Quote, [option_ticker])
            
            # Listen for quote
            async for quote in self.streamer.listen(Quote):
                if quote.event_symbol == option_ticker:
                    return quote
        except Exception as e:
            cprint(f"⚠️ Error in async quote fetch: {e}", "yellow")
            return None
    
    def get_atm_options_data(self, underlying: str) -> Optional[Dict]:
        """
        Get comprehensive 0DTE ATM options data for both CALL and PUT
        
        Returns:
            {
                'underlying': 'SPY',
                'underlying_price': 580.50,
                'expiration': '2025-11-04',
                'atm_strike': 580.00,
                'call': {'ticker': '...', 'bid': 2.50, 'ask': 2.75, 'mid': 2.625, 'last': 2.75},
                'put': {'ticker': '...', 'bid': 2.40, 'ask': 2.65, 'mid': 2.525, 'last': 2.65}
            }
        """
        try:
            # Get underlying price
            underlying_price = self.get_underlying_price(underlying)
            if not underlying_price:
                return None
            
            # Get ATM strike
            atm_strike = self._find_atm_strike(underlying_price)
            
            # Get expiration
            expiration = self.get_0dte_expiration()
            
            # Format option tickers (Tastytrade format: .SPY230721C387)
            date_str = expiration.replace('-', '')[2:]  # Convert 2025-11-04 to 251104
            strike_str = f"{int(atm_strike * 1000):08d}"  # Format strike with leading zeros
            
            call_ticker = f".{underlying}{date_str}C{strike_str}"
            put_ticker = f".{underlying}{date_str}P{strike_str}"
            
            # Get quotes
            call_quote = self.get_option_quote(call_ticker)
            put_quote = self.get_option_quote(put_ticker)
            
            if not call_quote or not put_quote:
                cprint(f"⚠️ Could not fetch option quotes for {underlying}", "yellow")
                return None
            
            return {
                'underlying': underlying,
                'underlying_price': round(underlying_price, 2),
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
                }
            }
        except Exception as e:
            cprint(f"❌ Error getting ATM options data for {underlying}: {e}", "red")
            return None
    
    async def close(self):
        """Close streamer connection"""
        try:
            if self.streamer:
                await self.streamer.__aexit__(None, None, None)
                cprint("✅ Tastytrade streamer closed", "green")
        except Exception as e:
            cprint(f"⚠️ Error closing streamer: {e}", "yellow")


if __name__ == "__main__":
    # Test the provider
    print("\n🧪 Testing Tastytrade Options Provider...\n")
    
    try:
        provider = TastytradeOptionsProvider()
        
        print("📊 Fetching SPY 0DTE ATM options...")
        data = provider.get_atm_options_data('SPY')
        
        if data:
            print(f"\n✅ Success!")
            print(f"   Underlying: {data['underlying']} @ ${data['underlying_price']}")
            print(f"   ATM Strike: ${data['atm_strike']}")
            print(f"   Expiration: {data['expiration']}")
            print(f"\n   CALL: {data['call']['ticker']}")
            print(f"   Price: ${data['call']['mid']} (bid: ${data['call']['bid']}, ask: ${data['call']['ask']})")
            print(f"\n   PUT: {data['put']['ticker']}")
            print(f"   Price: ${data['put']['mid']} (bid: ${data['put']['bid']}, ask: ${data['put']['ask']})")
        else:
            print("❌ Failed to get options data")
    
    except Exception as e:
        print(f"❌ Error: {e}")
