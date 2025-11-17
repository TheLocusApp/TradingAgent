#!/usr/bin/env python3
"""Check Quote attributes"""

import os
import asyncio
from datetime import date
from dotenv import load_dotenv
from tastytrade import Session, DXLinkStreamer
from tastytrade.instruments import Equity
from tastytrade.dxfeed import Quote

load_dotenv()

username = os.getenv('TASTYTRADE_USERNAME')
password = os.getenv('TASTYTRADE_PASSWORD')

async def test():
    session = Session(login=username, password=password)
    
    async with DXLinkStreamer(session) as streamer:
        await streamer.subscribe(Quote, ['QQQ'])
        
        async for quote in streamer.listen(Quote):
            if quote.event_symbol == 'QQQ':
                print("Quote attributes:")
                for attr in dir(quote):
                    if not attr.startswith('_'):
                        try:
                            val = getattr(quote, attr)
                            if not callable(val):
                                print(f"  - {attr}: {val}")
                        except:
                            pass
                break

asyncio.run(test())
