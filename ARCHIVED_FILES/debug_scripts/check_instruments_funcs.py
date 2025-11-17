#!/usr/bin/env python3
"""Check instruments module functions"""

from tastytrade import instruments
import inspect

print("Instruments module functions and classes:")
for name in dir(instruments):
    if not name.startswith('_'):
        obj = getattr(instruments, name)
        if inspect.isfunction(obj) or inspect.isclass(obj):
            if 'option' in name.lower() or 'chain' in name.lower():
                print(f"  - {name}: {type(obj).__name__}")
