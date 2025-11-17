#!/usr/bin/env python3
"""Test DXLink subscription - Pattern 2: Listen first, then subscribe"""

import os
import asyncio
from datetime import date
from dotenv import load_dotenv
from tastytrade import Session, DXLinkStreamer
from tastytrade.dxfeed import Quote

load_dotenv()

username = os.getenv('TASTYTRADE_USERNAME')
password = os.getenv('TASTYTRADE_PASSWORD')

async def test_option_quotes():
    session = Session(login=username, password=password)
    
    # Test with both stock and option symbols
    symbols = [
        'QQQ',  # Stock
        '.QQQ251114C00613000'  # Option
    ]
    
    print(f"Testing subscription to: {symbols}")
    
    async with DXLinkStreamer(session) as streamer:
        print(">>> DXLink connection established")
        
        # Create listener task FIRST (to create channels)
        async def listen_task():
            print(">>> Listening for quotes...")
            count = 0
            async for quote in streamer.listen(Quote):
                # Check the actual attribute name
                symbol = getattr(quote, 'event_symbol', None) or getattr(quote, 'eventSymbol', None)
                
                print(f"\n>>> Quote received:")
                print(f"  Symbol: {symbol}")
                
                # Check all available attributes
                if count == 0:
                    print(f"\n  Available attributes:")
                    for attr in dir(quote):
                        if not attr.startswith('_'):
                            try:
                                val = getattr(quote, attr)
                                if not callable(val):
                                    print(f"    - {attr}: {val}")
                            except:
                                pass
                
                count += 1
                if count >= 5:  # Get 5 quotes then exit
                    break
            
            print(f"\n>>> Test complete. Received {count} quotes.")
        
        # Start listener in background
        listener = asyncio.create_task(listen_task())
        
        # Wait a bit for channels to be created
        await asyncio.sleep(2.0)
        
        # Now subscribe
        print(">>> Subscribing to symbols...")
        await streamer.subscribe(Quote, symbols)
        print(f">>> Subscribed to {len(symbols)} symbols")
        
        # Wait for listener to complete
        await listener

if __name__ == "__main__":
    asyncio.run(test_option_quotes())

