#!/usr/bin/env python3
"""
🌙 Moon Dev's Tastytrade DXLink Options Provider
Real-time 0DTE ATM options quotes using Tastytrade DXLink Streamer
Built with love by Moon Dev 🚀
"""

import os
import asyncio
from datetime import date
from typing import Dict, Optional
from dotenv import load_dotenv
from termcolor import cprint

load_dotenv()


class TastytradeDXLinkProvider:
    """Provides real-time 0DTE ATM options quotes from Tastytrade DXLink Streamer"""
    
    def __init__(self):
        """Initialize Tastytrade DXLink provider"""
        self.username = os.getenv('TASTYTRADE_USERNAME')
        self.password = os.getenv('TASTYTRADE_PASSWORD')
        self.account_number = os.getenv('TASTYTRADE_ACCOUNT_NUMBER')
        
        if not all([self.username, self.password, self.account_number]):
            raise ValueError("TASTYTRADE_USERNAME, TASTYTRADE_PASSWORD, and TASTYTRADE_ACCOUNT_NUMBER required in .env")
        
        self.session = None
        cprint("✅ Tastytrade DXLink Provider initialized", "green")
    
    def _init_session(self):
        """Initialize Tastytrade session"""
        try:
            from tastytrade import Session
            
            cprint("🔐 Authenticating with Tastytrade...", "cyan")
            self.session = Session(login=self.username, password=self.password)
            cprint("✅ Authenticated", "green")
        except Exception as e:
            cprint(f"❌ Failed to authenticate: {e}", "red")
            raise
    
    def get_0dte_atm_options(self, underlying: str, atm_strike: float = None) -> Optional[Dict]:
        """Get 0DTE ATM options with REAL quotes (synchronous wrapper)"""
        try:
            # Run async function in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._get_0dte_atm_options_async(underlying, atm_strike))
            loop.close()
            return result
        except Exception as e:
            cprint(f"❌ Error getting ATM options: {e}", "red")
            return None
    
    def get_option_quote(self, option_symbol: str) -> Dict:
        """Get real-time quote for a single option (synchronous wrapper)"""
        try:
            # Run async function in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._get_option_quote_async(option_symbol))
            loop.close()
            return result
        except Exception as e:
            cprint(f"⚠️ Error getting option quote: {e}", "yellow")
            return None
    
    async def _get_option_quote_async(self, option_symbol: str) -> Dict:
        """Get real-time quote for a single option (async)"""
        try:
            if not self.session:
                self._init_session()
            
            from tastytrade import DXLinkStreamer
            from tastytrade.dxfeed import Quote
            
            async with DXLinkStreamer(self.session) as streamer:
                await streamer.subscribe(Quote, [option_symbol])
                
                async for quote in streamer.listen(Quote):
                    if quote.event_symbol == option_symbol:
                        return {
                            'bid': float(quote.bid_price) if quote.bid_price else 0,
                            'ask': float(quote.ask_price) if quote.ask_price else 0,
                            'mid': float((quote.bid_price + quote.ask_price) / 2) if quote.bid_price and quote.ask_price else 0,
                            'bid_size': int(quote.bid_size) if quote.bid_size else 0,
                            'ask_size': int(quote.ask_size) if quote.ask_size else 0,
                        }
            return None
        except Exception as e:
            cprint(f"⚠️ Error in async quote fetch: {e}", "yellow")
            return None
    
    async def get_option_quotes(self, option_symbols: list) -> Dict[str, Dict]:
        """Get real-time quotes for option symbols using DXLink streamer"""
        try:
            if not self.session:
                self._init_session()
            
            from tastytrade import DXLinkStreamer
            from tastytrade.dxfeed import Quote
            
            quotes = {}
            
            async with DXLinkStreamer(self.session) as streamer:
                cprint(f"📡 Subscribing to {len(option_symbols)} option symbols...", "cyan")
                await streamer.subscribe(Quote, option_symbols)
                
                cprint("   Waiting for quotes...", "yellow")
                received = set()
                
                async for quote in streamer.listen(Quote):
                    if quote.event_symbol in option_symbols:
                        quotes[quote.event_symbol] = {
                            'bid': float(quote.bid_price) if quote.bid_price else 0,
                            'ask': float(quote.ask_price) if quote.ask_price else 0,
                            'mid': float((quote.bid_price + quote.ask_price) / 2) if quote.bid_price and quote.ask_price else 0,
                            'bid_size': int(quote.bid_size) if quote.bid_size else 0,
                            'ask_size': int(quote.ask_size) if quote.ask_size else 0,
                        }
                        received.add(quote.event_symbol)
                        cprint(f"   ✅ {quote.event_symbol}: Bid=${quote.bid_price:.2f}, Ask=${quote.ask_price:.2f}", "cyan")
                        
                        # Stop when we have all quotes
                        if len(received) == len(option_symbols):
                            break
            
            return quotes
        
        except Exception as e:
            cprint(f"❌ Error getting option quotes: {e}", "red")
            import traceback
            traceback.print_exc()
            return {}
    
    async def _get_0dte_atm_options_async(self, underlying: str, atm_strike: float = None) -> Optional[Dict]:
        """Get 0DTE ATM options with REAL quotes (async)"""
        try:
            cprint(f"📊 Fetching {underlying} 0DTE ATM options...", "cyan")
            
            if not self.session:
                self._init_session()
            
            from tastytrade.instruments import Equity, get_option_chain, OptionType
            
            # Get equity
            equity = Equity.get_equity(self.session, underlying)
            if not equity:
                cprint(f"⚠️ Could not find equity {underlying}", "yellow")
                return None
            
            # Get option chain
            option_chain = get_option_chain(self.session, underlying)
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
            
            cprint(f"📊 Available strikes: {strikes}", "cyan")
            
            # If ATM strike not provided, we need to fetch underlying price first to find true ATM
            if atm_strike is None:
                cprint(f"📡 Fetching underlying price to calculate true ATM strike...", "cyan")
                
                # Fetch just the underlying price first
                underlying_quotes = await self.get_option_quotes([equity.streamer_symbol])
                underlying_quote = underlying_quotes.get(equity.streamer_symbol, {})
                underlying_price = underlying_quote.get('mid', None)
                
                if underlying_price:
                    # Convert to Decimal to match strike type (Decimal from Tastytrade)
                    from decimal import Decimal
                    underlying_price_decimal = Decimal(str(underlying_price))
                    # Find strike closest to current underlying price
                    atm_strike = min(strikes, key=lambda x: abs(x - underlying_price_decimal))
                    cprint(f"✅ Underlying price: ${float(underlying_price_decimal):.2f}, ATM strike: ${float(atm_strike):.2f}", "green")
                else:
                    # Fallback to middle strike
                    atm_strike = strikes[len(strikes) // 2]
                    cprint(f"⚠️ Could not fetch underlying price, using middle strike: ${float(atm_strike):.2f}", "yellow")
            
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
            cprint(f"   CALL: {call_opt.streamer_symbol}", "cyan")
            cprint(f"   PUT: {put_opt.streamer_symbol}", "cyan")
            
            # Get REAL quotes from DXLink streamer (including underlying and options)
            cprint(f"📡 Fetching REAL quotes from DXLink streamer...", "cyan")
            symbols_to_fetch = [equity.streamer_symbol, call_opt.streamer_symbol, put_opt.streamer_symbol]
            quotes = await self.get_option_quotes(symbols_to_fetch)
            
            if not quotes or len(quotes) < 3:
                cprint(f"⚠️ Could not fetch all quotes", "yellow")
                return None
            
            underlying_quote = quotes.get(equity.streamer_symbol, {})
            call_quote = quotes.get(call_opt.streamer_symbol, {})
            put_quote = quotes.get(put_opt.streamer_symbol, {})
            
            underlying_price = underlying_quote.get('mid', float(atm_strike))
            
            return {
                'underlying': underlying,
                'underlying_price': underlying_price,
                'atm_strike': float(atm_strike),
                'expiration': today.isoformat(),
                'call': {
                    'ticker': call_opt.streamer_symbol,
                    'symbol': call_opt.symbol,
                    'streamer_symbol': call_opt.streamer_symbol,
                    'bid': call_quote.get('bid', 0),
                    'ask': call_quote.get('ask', 0),
                    'mid': call_quote.get('mid', 0),
                    'last': call_quote.get('mid', 0),  # Use mid as last
                    'bid_size': call_quote.get('bid_size', 0),
                    'ask_size': call_quote.get('ask_size', 0),
                },
                'put': {
                    'ticker': put_opt.streamer_symbol,
                    'symbol': put_opt.symbol,
                    'streamer_symbol': put_opt.streamer_symbol,
                    'bid': put_quote.get('bid', 0),
                    'ask': put_quote.get('ask', 0),
                    'mid': put_quote.get('mid', 0),
                    'last': put_quote.get('mid', 0),  # Use mid as last
                    'bid_size': put_quote.get('bid_size', 0),
                    'ask_size': put_quote.get('ask_size', 0),
                }
            }
        
        except Exception as e:
            cprint(f"❌ Error getting ATM options: {e}", "red")
            import traceback
            traceback.print_exc()
            return None


async def main():
    # Test the provider
    print("\n🧪 Testing Tastytrade DXLink Provider...\n")
    
    try:
        provider = TastytradeDXLinkProvider()
        
        print("📊 Fetching QQQ 621 0DTE options with REAL quotes...")
        data = await provider.get_0dte_atm_options('QQQ', atm_strike=621)
        
        if data:
            print(f"\n✅ SUCCESS! REAL OPTION QUOTES:")
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


if __name__ == "__main__":
    asyncio.run(main())
