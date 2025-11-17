#!/usr/bin/env python3
"""Check Quote class methods"""

from tastytrade.dxfeed import Quote
import inspect

print("Quote class methods:")
for name, method in inspect.getmembers(Quote, predicate=inspect.ismethod):
    if not name.startswith('_'):
        print(f"  - {name}")

print("\nQuote class functions:")
for name, func in inspect.getmembers(Quote, predicate=inspect.isfunction):
    if not name.startswith('_'):
        print(f"  - {name}")

print("\nQuote instance attributes (from docstring):")
print(Quote.__doc__)
