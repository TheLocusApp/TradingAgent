#!/usr/bin/env python3
"""Check Equity class methods"""

from tastytrade import Session
from tastytrade.instruments import Equity
import inspect
import os
from dotenv import load_dotenv

load_dotenv()

username = os.getenv('TASTYTRADE_USERNAME')
password = os.getenv('TASTYTRADE_PASSWORD')

# Authenticate
session = Session(login=username, password=password)

# Get equity
equity = Equity.get_equity(session, 'SPY')

print("Equity object methods and attributes:")
for name in dir(equity):
    if not name.startswith('_'):
        obj = getattr(equity, name)
        if callable(obj):
            print(f"  - {name}() [method]")
        else:
            print(f"  - {name} = {obj}")
