#!/usr/bin/env python3
"""Check option chain structure"""

from tastytrade import Session
from tastytrade.instruments import get_option_chain
import os
from dotenv import load_dotenv
import json

load_dotenv()

username = os.getenv('TASTYTRADE_USERNAME')
password = os.getenv('TASTYTRADE_PASSWORD')

# Authenticate
session = Session(login=username, password=password)

# Get option chain
chain = get_option_chain(session, 'SPY')

print(f"Type: {type(chain)}")
print(f"Keys: {chain.keys() if hasattr(chain, 'keys') else 'N/A'}")
print(f"\nFirst few items:")
for key in list(chain.keys())[:5]:
    print(f"  {key}: {type(chain[key])}")
    if hasattr(chain[key], '__len__') and len(chain[key]) > 0:
        print(f"    First item: {chain[key][0] if isinstance(chain[key], list) else chain[key]}")
