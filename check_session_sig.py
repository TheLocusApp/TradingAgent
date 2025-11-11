#!/usr/bin/env python3
from tastytrade import Session
import inspect

sig = inspect.signature(Session.__init__)
print("Session.__init__ signature:")
print(sig)
print("\nParameters:")
for param_name, param in sig.parameters.items():
    print(f"  {param_name}: {param.annotation if param.annotation != inspect.Parameter.empty else 'no annotation'}")
