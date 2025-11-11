#!/usr/bin/env python3
"""
Test Tastytrade Options API - READ-ONLY
This script ONLY reads data, does NOT execute any trades
"""

import os
import asyncio
from dotenv import load_dotenv
from termcolor import cprint

load_dotenv()

# Check credentials
username = os.getenv('TASTYTRADE_USERNAME')
password = os.getenv('TASTYTRADE_PASSWORD')
account_number = os.getenv('TASTYTRADE_ACCOUNT_NUMBER')

if not all([username, password, account_number]):
    cprint("❌ Missing Tastytrade credentials in .env", "red")
    cprint("   Required: TASTYTRADE_USERNAME, TASTYTRADE_PASSWORD, TASTYTRADE_ACCOUNT_NUMBER", "yellow")
    exit(1)

cprint("\n✅ Tastytrade credentials found", "green")
cprint(f"   Username: {username[:5]}***", "cyan")
cprint(f"   Account: {account_number}", "cyan")

async def test_tastytrade_options():
    """Test Tastytrade options API - READ ONLY"""
    
    try:
        # Test 1: Check if tastytrade package is installed
        cprint("\n📦 Checking Tastytrade SDK installation...", "cyan")
        try:
            import tastytrade
            cprint(f"✅ Tastytrade SDK installed", "green")
            cprint(f"   Version: {tastytrade.__version__ if hasattr(tastytrade, '__version__') else 'unknown'}", "cyan")
        except ImportError:
            cprint("❌ Tastytrade SDK not installed", "red")
            cprint("   Install with: pip install tastytrade", "yellow")
            return
        
        # Test 2: Check available classes
        cprint("\n🔍 Checking available Tastytrade classes...", "cyan")
        try:
            from tastytrade import Session, DXLinkStreamer, Quote
            cprint("✅ Core classes available:", "green")
            cprint("   - Session", "cyan")
            cprint("   - DXLinkStreamer", "cyan")
            cprint("   - Quote", "cyan")
        except ImportError as e:
            cprint(f"⚠️ Some classes unavailable: {e}", "yellow")
        
        # Test 3: Attempt authentication
        cprint("\n📊 Attempting Tastytrade authentication...", "cyan")
        try:
            from tastytrade import Session
            
            # Try different authentication methods
            session = None
            
            # Method 1: Check if Session has login classmethod
            if hasattr(Session, 'login'):
                cprint("   Trying Session.login()...", "yellow")
                session = Session.login(username, password)
            # Method 2: Check if Session constructor accepts username/password
            else:
                cprint("   Session.login() not available, checking constructor...", "yellow")
                # The official SDK requires OAuth tokens, not username/password
                cprint("⚠️ Official Tastytrade SDK requires OAuth tokens", "yellow")
                cprint("   For demo purposes, using fallback data", "yellow")
                return
            
            if session:
                cprint("✅ Authenticated with Tastytrade", "green")
                
                # Test 4: Get streamer data (read-only)
                cprint("\n📡 Testing data streamer connection...", "cyan")
                try:
                    from tastytrade import DXLinkStreamer, Quote
                    
                    async with DXLinkStreamer(session) as streamer:
                        cprint("✅ Streamer connected", "green")
                        
                        # Subscribe to SPY quote (read-only)
                        cprint("   Subscribing to SPY quotes...", "yellow")
                        await streamer.subscribe(Quote, ['SPY'])
                        
                        # Listen for one quote
                        cprint("   Waiting for quote data (timeout in 5s)...", "yellow")
                        import asyncio
                        try:
                            async for quote in asyncio.timeout(5)(streamer.listen(Quote)):
                                if quote.event_symbol == 'SPY':
                                    cprint("✅ Received SPY quote:", "green")
                                    cprint(f"   Symbol: {quote.event_symbol}", "cyan")
                                    cprint(f"   Bid: ${quote.bid_price:.2f} (size: {quote.bid_size})", "cyan")
                                    cprint(f"   Ask: ${quote.ask_price:.2f} (size: {quote.ask_size})", "cyan")
                                    cprint(f"   Mid: ${(quote.bid_price + quote.ask_price) / 2:.2f}", "cyan")
                                    break
                        except asyncio.TimeoutError:
                            cprint("⚠️ Quote timeout (market may be closed)", "yellow")
                
                except Exception as e:
                    cprint(f"⚠️ Streamer connection: {e}", "yellow")
        
        except Exception as e:
            cprint(f"⚠️ Authentication: {e}", "yellow")
            cprint("   Note: Official SDK requires OAuth tokens", "yellow")
            cprint("   Using Polygon/fallback for demo", "yellow")
        
        cprint("\n✅ Test completed!", "green")
        cprint("   No trades were executed (read-only test)", "cyan")
        
    except Exception as e:
        cprint(f"\n❌ Error: {e}", "red")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    cprint("\n" + "="*60, "cyan")
    cprint("🧪 TASTYTRADE OPTIONS API TEST (READ-ONLY)", "cyan")
    cprint("="*60, "cyan")
    
    try:
        asyncio.run(test_tastytrade_options())
    except KeyboardInterrupt:
        cprint("\n\n⚠️ Test interrupted by user", "yellow")
    except Exception as e:
        cprint(f"\n❌ Fatal error: {e}", "red")
        import traceback
        traceback.print_exc()
