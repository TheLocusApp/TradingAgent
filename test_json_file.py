import json

# Test if JSON file is valid
filepath = 'src/data/optimizations/optimization_NVDA_swing_20251107_114138.json'

try:
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    print("✅ Valid JSON file")
    print(f"Timeframes: {list(data.keys())}")
    
    for tf, results in data.items():
        print(f"\n{tf}: {len(results)} results")
        if results:
            first = results[0]
            print(f"  First result: sharpe={first.get('sharpe')}, return={first.get('return')}, trades={first.get('trades')}")
    
except Exception as e:
    print(f"❌ Error: {e}")
