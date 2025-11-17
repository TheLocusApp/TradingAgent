#!/usr/bin/env python3
"""Check what's available in Tastytrade SDK"""

import tastytrade
import inspect

print("Tastytrade SDK modules and classes:")
print(f"Version: {tastytrade.__version__ if hasattr(tastytrade, '__version__') else 'unknown'}\n")

# Check main module
print("Main module contents:")
for name in dir(tastytrade):
    if not name.startswith('_'):
        obj = getattr(tastytrade, name)
        if inspect.isclass(obj) or inspect.ismodule(obj):
            print(f"  - {name}: {type(obj).__name__}")

# Check instruments module
print("\nInstruments module:")
try:
    from tastytrade import instruments
    for name in dir(instruments):
        if not name.startswith('_'):
            obj = getattr(instruments, name)
            if inspect.isclass(obj):
                print(f"  - {name}")
except Exception as e:
    print(f"  Error: {e}")

# Check dxfeed module
print("\nDXFeed module:")
try:
    from tastytrade import dxfeed
    for name in dir(dxfeed):
        if not name.startswith('_'):
            obj = getattr(dxfeed, name)
            if inspect.isclass(obj):
                print(f"  - {name}")
except Exception as e:
    print(f"  Error: {e}")
