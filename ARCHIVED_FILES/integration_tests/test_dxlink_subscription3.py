#!/usr/bin/env python3
"""Test DXLink subscription - Pattern 3: Check library version and proper usage"""

import os
import asyncio
from datetime import date
from dotenv import load_dotenv
from tastytrade import Session, DXLinkStreamer
from tastytrade.dxfeed import Quote
import tastytrade

load_dotenv()

username = os.getenv('TASTYTRADE_USERNAME')
password = os.getenv('TASTYTRADE_PASSWORD')

async def test_simple():
    """Test the exact pattern from check_quote_attributes.py"""
    session = Session(login=username, password=password)
    
    print(f"Tastytrade version: {tastytrade.__version__ if hasattr(tastytrade, '__version__') else 'unknown'}")
    
    async with DXLinkStreamer(session) as streamer:
        print(">>> Connection established")
        
        # This is the pattern from the working example
        await streamer.subscribe(Quote, ['QQQ'])
        print(">>> Subscribed to QQQ")
        
        print(">>> Listening...")
        async for quote in streamer.listen(Quote):
            symbol = getattr(quote, 'event_symbol', 'unknown')
            bid = getattr(quote, 'bidPrice', None) or getattr(quote, 'bid_price', None)
            ask = getattr(quote, 'askPrice', None) or getattr(quote, 'ask_price', None)
            
            print(f">>> Got quote for {symbol}: bid={bid}, ask={ask}")
            
            if symbol == 'QQQ':
                print("\n>>> Success! Stock quotes work.")
                
                # Now try option
                print("\n>>> Now trying option symbol...")
                await streamer.subscribe(Quote, ['.QQQ251114C00613000'])
                print(">>> Subscribed to option")
            
            if hasattr(quote, 'event_symbol'):
                if '.QQQ' in quote.event_symbol:
                    print(f">>> SUCCESS! Got option quote: {quote.event_symbol}")
                    break

if __name__ == "__main__":
    try:
        asyncio.run(test_simple())
    except Exception as e:
        print(f">>> Error: {e}")
        import traceback
        traceback.print_exc()

