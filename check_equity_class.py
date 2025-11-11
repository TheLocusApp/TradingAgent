#!/usr/bin/env python3
"""Check Equity class methods"""

from tastytrade.instruments import Equity
import inspect

print("Equity class methods:")
for name, method in inspect.getmembers(Equity, predicate=inspect.ismethod):
    if not name.startswith('_'):
        print(f"  - {name}")

print("\nEquity class functions:")
for name, func in inspect.getmembers(Equity, predicate=inspect.isfunction):
    if not name.startswith('_'):
        print(f"  - {name}")
