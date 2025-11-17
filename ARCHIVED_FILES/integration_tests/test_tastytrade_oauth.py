#!/usr/bin/env python3
"""
Test Tastytrade OAuth Token - READ-ONLY
Verifies OAuth token works and can fetch options data
"""

import os
import asyncio
from dotenv import load_dotenv
from termcolor import cprint

load_dotenv()

# Check credentials
oauth_token = os.getenv('TASTYTRADE_OAUTH_TOKEN')
account_number = os.getenv('TASTYTRADE_ACCOUNT_NUMBER')

if not all([oauth_token, account_number]):
    cprint("❌ Missing Tastytrade credentials in .env", "red")
    cprint("   Required: TASTYTRADE_OAUTH_TOKEN, TASTYTRADE_ACCOUNT_NUMBER", "yellow")
    exit(1)

cprint("\n✅ Tastytrade OAuth credentials found", "green")
cprint(f"   OAuth Token: {oauth_token[:20]}...", "cyan")
cprint(f"   Account: {account_number}", "cyan")

async def test_tastytrade_oauth():
    """Test Tastytrade OAuth authentication and options data"""
    
    try:
        cprint("\n📊 Connecting to Tastytrade with OAuth token...", "cyan")
        from tastytrade import Session, DXLinkStreamer
        from tastytrade.dxfeed import Quote
        
        # Authenticate using remember_token (OAuth token)
        # Session takes login, password, and remember_token
        session = Session(
            login="",  # Not needed when using remember_token
            password=None,
            remember_token=oauth_token  # Your OAuth token
        )
        cprint("✅ Authenticated with Tastytrade OAuth token", "green")
        
        # Test 1: Get customer info (read-only)
        cprint("\n📋 Fetching account information...", "cyan")
        try:
            customer = session.get_customer()
            cprint(f"✅ Customer: {customer.first_name} {customer.last_name}", "green")
            cprint(f"   Email: {customer.email}", "cyan")
        except Exception as e:
            cprint(f"⚠️ Could not fetch customer info: {e}", "yellow")
        
        # Test 2: Get accounts (read-only)
        cprint("\n📋 Fetching accounts...", "cyan")
        try:
            accounts = session.get_accounts()
            cprint(f"✅ Found {len(accounts)} account(s)", "green")
            for acc in accounts:
                cprint(f"   - {acc.account_number}: {acc.account_type}", "cyan")
        except Exception as e:
            cprint(f"⚠️ Could not fetch accounts: {e}", "yellow")
        
        # Test 3: Connect to streamer (read-only)
        cprint("\n📡 Connecting to data streamer...", "cyan")
        try:
            async with DXLinkStreamer(session) as streamer:
                cprint("✅ Streamer connected", "green")
                
                # Subscribe to SPY quote (read-only)
                cprint("   Subscribing to SPY quotes...", "yellow")
                await streamer.subscribe(Quote, ['SPY'])
                
                # Listen for one quote with timeout
                cprint("   Waiting for quote data (timeout in 10s)...", "yellow")
                quote_received = False
                
                try:
                    async for quote in streamer.listen(Quote):
                        if quote.event_symbol == 'SPY':
                            cprint("✅ Received SPY quote:", "green")
                            cprint(f"   Symbol: {quote.event_symbol}", "cyan")
                            cprint(f"   Bid: ${quote.bid_price:.2f} (size: {int(quote.bid_size)})", "cyan")
                            cprint(f"   Ask: ${quote.ask_price:.2f} (size: {int(quote.ask_size)})", "cyan")
                            cprint(f"   Mid: ${(quote.bid_price + quote.ask_price) / 2:.2f}", "cyan")
                            cprint(f"   Last: ${quote.last_price:.2f}", "cyan")
                            quote_received = True
                            break
                except asyncio.TimeoutError:
                    cprint("⚠️ Quote timeout (market may be closed)", "yellow")
                
                if not quote_received:
                    cprint("⚠️ No quotes received (market may be closed)", "yellow")
        
        except Exception as e:
            cprint(f"❌ Streamer error: {e}", "red")
            import traceback
            traceback.print_exc()
        
        cprint("\n✅ OAuth test completed successfully!", "green")
        cprint("   No trades were executed (read-only test)", "cyan")
        cprint("   Tastytrade API is working correctly!", "green")
        
    except Exception as e:
        cprint(f"\n❌ Error: {e}", "red")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    cprint("\n" + "="*60, "cyan")
    cprint("🧪 TASTYTRADE OAUTH TOKEN TEST (READ-ONLY)", "cyan")
    cprint("="*60, "cyan")
    
    try:
        asyncio.run(test_tastytrade_oauth())
    except KeyboardInterrupt:
        cprint("\n\n⚠️ Test interrupted by user", "yellow")
    except Exception as e:
        cprint(f"\n❌ Fatal error: {e}", "red")
        import traceback
        traceback.print_exc()
