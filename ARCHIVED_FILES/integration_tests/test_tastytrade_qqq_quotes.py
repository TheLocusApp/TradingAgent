#!/usr/bin/env python3
"""Test Tastytrade SDK with actual QQQ options and live quotes"""

import os
import asyncio
from datetime import date
from dotenv import load_dotenv
from termcolor import cprint

load_dotenv()

username = os.getenv('TASTYTRADE_USERNAME')
password = os.getenv('TASTYTRADE_PASSWORD')

if not username or not password:
    print("❌ Missing credentials")
    exit(1)

async def test_qqq_options():
    """Test QQQ options with live quotes"""
    try:
        from tastytrade import Session, DXLinkStreamer
        from tastytrade.instruments import Equity, get_option_chain, OptionType
        from tastytrade.dxfeed import Quote
        
        cprint("🔐 Authenticating...", "cyan")
        session = Session(login=username, password=password)
        cprint("✅ Authenticated", "green")
        
        # Get QQQ equity
        cprint("\n📊 Getting QQQ equity...", "cyan")
        qqq = Equity.get_equity(session, 'QQQ')
        cprint(f"✅ QQQ found: {qqq.symbol}", "green")
        cprint(f"   Streamer symbol: {qqq.streamer_symbol}", "cyan")
        
        # Get option chain
        cprint("\n📊 Getting QQQ option chain...", "cyan")
        option_chain = get_option_chain(session, 'QQQ')
        today = date.today()
        today_options = option_chain.get(today)
        
        if not today_options:
            cprint(f"❌ No 0DTE options for QQQ", "red")
            return
        
        cprint(f"✅ Found {len(today_options)} 0DTE options for QQQ", "green")
        
        # Find 621 strike
        cprint("\n📊 Looking for 621 strike...", "cyan")
        call_621 = None
        put_621 = None
        
        for opt in today_options:
            if opt.strike_price == 621:
                if opt.option_type == OptionType.CALL:
                    call_621 = opt
                    cprint(f"✅ Found CALL 621: {opt.streamer_symbol}", "green")
                elif opt.option_type == OptionType.PUT:
                    put_621 = opt
                    cprint(f"✅ Found PUT 621: {opt.streamer_symbol}", "green")
        
        if not call_621 or not put_621:
            cprint("❌ Could not find 621 CALL or PUT", "red")
            return
        
        # Get live quotes using streamer
        cprint("\n📡 Connecting to DXLink streamer for live quotes...", "cyan")
        async with DXLinkStreamer(session) as streamer:
            cprint("✅ Streamer connected", "green")
            
            # Subscribe to quotes
            symbols = [qqq.streamer_symbol, call_621.streamer_symbol, put_621.streamer_symbol]
            cprint(f"   Subscribing to: {symbols}", "yellow")
            await streamer.subscribe(Quote, symbols)
            
            # Listen for quotes
            cprint("   Waiting for quotes (timeout 10s)...", "yellow")
            quotes_received = {sym: None for sym in symbols}
            
            try:
                async for quote in streamer.listen(Quote):
                    if quote.event_symbol in quotes_received:
                        quotes_received[quote.event_symbol] = quote
                        cprint(f"   ✅ Received {quote.event_symbol}", "cyan")
                    
                    # Check if we have all quotes
                    if all(quotes_received.values()):
                        break
            except asyncio.TimeoutError:
                cprint("⚠️ Timeout waiting for quotes", "yellow")
            
            # Display results
            cprint("\n📊 RESULTS:", "cyan")
            cprint("=" * 60, "cyan")
            
            if quotes_received[qqq.streamer_symbol]:
                q = quotes_received[qqq.streamer_symbol]
                cprint(f"\n🔹 QQQ (Underlying)", "cyan")
                cprint(f"   Bid: ${q.bid_price:.2f}", "cyan")
                cprint(f"   Ask: ${q.ask_price:.2f}", "cyan")
                cprint(f"   Mid: ${(q.bid_price + q.ask_price) / 2:.2f}", "cyan")
                cprint(f"   Last: ${q.last_price:.2f}", "cyan")
            
            if quotes_received[call_621.streamer_symbol]:
                q = quotes_received[call_621.streamer_symbol]
                cprint(f"\n🔹 QQQ 621 CALL", "cyan")
                cprint(f"   Symbol: {call_621.streamer_symbol}", "cyan")
                cprint(f"   Bid: ${q.bid_price:.2f}" if q.bid_price else "   Bid: N/A", "cyan")
                cprint(f"   Ask: ${q.ask_price:.2f}" if q.ask_price else "   Ask: N/A", "cyan")
                cprint(f"   Mid: ${(q.bid_price + q.ask_price) / 2:.2f}" if q.bid_price and q.ask_price else "   Mid: N/A", "cyan")
                cprint(f"   Last: ${q.last_price:.2f}" if q.last_price else "   Last: N/A", "cyan")
            
            if quotes_received[put_621.streamer_symbol]:
                q = quotes_received[put_621.streamer_symbol]
                cprint(f"\n🔹 QQQ 621 PUT", "cyan")
                cprint(f"   Symbol: {put_621.streamer_symbol}", "cyan")
                cprint(f"   Bid: ${q.bid_price:.2f}" if q.bid_price else "   Bid: N/A", "cyan")
                cprint(f"   Ask: ${q.ask_price:.2f}" if q.ask_price else "   Ask: N/A", "cyan")
                cprint(f"   Mid: ${(q.bid_price + q.ask_price) / 2:.2f}" if q.bid_price and q.ask_price else "   Mid: N/A", "cyan")
                cprint(f"   Last: ${q.last_price:.2f}" if q.last_price else "   Last: N/A", "cyan")
            
            cprint("\n" + "=" * 60, "cyan")
    
    except Exception as e:
        cprint(f"❌ Error: {e}", "red")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    cprint("\n" + "="*60, "cyan")
    cprint("🧪 TASTYTRADE QQQ 621 OPTIONS TEST", "cyan")
    cprint("="*60, "cyan")
    
    try:
        asyncio.run(test_qqq_options())
    except KeyboardInterrupt:
        cprint("\n⚠️ Test interrupted", "yellow")
    except Exception as e:
        cprint(f"\n❌ Fatal error: {e}", "red")
