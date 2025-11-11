#!/usr/bin/env python3
"""
Test script to verify NaN fix in strategy optimizer
"""
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agents.strategy_optimizer import clean_nan_recursive
import numpy as np

print("="*70)
print("Testing NaN/Inf Cleaning")
print("="*70)

# Test 1: Clean individual values
print("\n1. Testing individual values:")
test_values = {
    'normal_float': 1.5,
    'nan_value': np.nan,
    'inf_value': np.inf,
    'neg_inf': -np.inf,
    'numpy_float': np.float64(2.5),
    'numpy_nan': np.float64(np.nan)
}

for name, value in test_values.items():
    cleaned = clean_nan_recursive(value)
    print(f"  {name}: {value} -> {cleaned}")

# Test 2: Clean nested structure
print("\n2. Testing nested structure:")
nested = {
    'timeframe': '1h',
    'sharpe': np.nan,
    'return': 43.19,
    'win_rate': np.nan,
    'trades': 67,
    'nested_list': [1.0, np.nan, 3.0],
    'nested_dict': {
        'a': np.inf,
        'b': 2.0
    }
}

cleaned_nested = clean_nan_recursive(nested)
print(f"  Original: {nested}")
print(f"  Cleaned: {cleaned_nested}")

# Test 3: Verify JSON serialization
print("\n3. Testing JSON serialization:")
try:
    json_str = json.dumps(cleaned_nested, indent=2)
    print("  ✅ JSON serialization successful!")
    print(f"  JSON output:\n{json_str}")
except Exception as e:
    print(f"  ❌ JSON serialization failed: {e}")

# Test 4: Check actual NVDA file
print("\n4. Checking actual NVDA optimization file:")
opt_dir = project_root / 'src' / 'data' / 'optimizations'
nvda_files = sorted(opt_dir.glob('optimization_NVDA_swing_*.json'), reverse=True)

if nvda_files:
    latest_file = nvda_files[0]
    print(f"  Latest file: {latest_file.name}")
    
    with open(latest_file, 'r') as f:
        content = f.read()
    
    # Check for NaN in file
    if 'NaN' in content or 'Infinity' in content:
        print("  ❌ File contains NaN or Infinity!")
        # Show first occurrence
        lines = content.split('\n')
        for i, line in enumerate(lines[:50]):
            if 'NaN' in line or 'Infinity' in line:
                print(f"    Line {i+1}: {line.strip()}")
                break
    else:
        print("  ✅ File is clean (no NaN or Infinity)")
        
        # Try to parse it
        try:
            with open(latest_file, 'r') as f:
                data = json.load(f)
            print("  ✅ JSON parsing successful!")
            
            # Check first result
            for timeframe, results in data.items():
                if results:
                    first_result = results[0]
                    print(f"\n  First result for {timeframe}:")
                    print(f"    Sharpe: {first_result.get('sharpe')}")
                    print(f"    Return: {first_result.get('return')}")
                    print(f"    Win Rate: {first_result.get('win_rate')}")
                    break
        except Exception as e:
            print(f"  ❌ JSON parsing failed: {e}")
else:
    print("  ⚠️  No NVDA optimization files found")

print("\n" + "="*70)
print("Test Complete")
print("="*70)
