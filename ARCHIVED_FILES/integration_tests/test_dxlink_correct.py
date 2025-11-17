#!/usr/bin/env python3
"""Test DXLink subscription with correct EventType usage"""

import os
import asyncio
from datetime import date
from dotenv import load_dotenv
from tastytrade import Session, DXLinkStreamer
from tastytrade.dxfeed import EventType, Quote

load_dotenv()

username = os.getenv('TASTYTRADE_USERNAME')
password = os.getenv('TASTYTRADE_PASSWORD')

async def test_correct_usage():
    """Use EventType.QUOTE instead of Quote class"""
    session = Session(login=username, password=password)
    
    # Test with both stock and option symbols
    symbols = [
        'QQQ',  # Stock
        '.QQQ251114C00613000'  # Option
    ]
    
    print(f"Testing subscription to: {symbols}")
    
    async with DXLinkStreamer(session) as streamer:
        print(">>> DXLink connection established")
        
        # Use EventType.QUOTE instead of Quote class
        await streamer.subscribe(EventType.QUOTE, symbols)
        print(f">>> Subscribed to {len(symbols)} symbols using EventType.QUOTE")
        
        print(">>> Listening for quotes...")
        count = 0
        async for quote in streamer.listen(EventType.QUOTE):
            # Check the actual attribute name
            symbol = getattr(quote, 'eventSymbol', None)
            bid_price = getattr(quote, 'bidPrice', None)
            ask_price = getattr(quote, 'askPrice', None)
            
            print(f"\n>>> Quote #{count + 1}:")
            print(f"  Symbol: {symbol}")
            print(f"  Bid: {bid_price}")
            print(f"  Ask: {ask_price}")
            
            # Show all attributes on first quote
            if count == 0:
                print(f"\n  Available attributes:")
                for attr in dir(quote):
                    if not attr.startswith('_') and not callable(getattr(quote, attr)):
                        try:
                            val = getattr(quote, attr)
                            print(f"    - {attr}: {val}")
                        except:
                            pass
            
            count += 1
            if count >= 10:  # Get 10 quotes then exit
                break
    
    print(f"\n>>> SUCCESS! Received {count} quotes.")

if __name__ == "__main__":
    asyncio.run(test_correct_usage())

