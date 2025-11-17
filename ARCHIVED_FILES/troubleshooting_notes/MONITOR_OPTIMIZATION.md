# How to Monitor Optimization Progress

## 🎯 Problem
You started optimization 10 minutes ago and nothing appears to be happening. How do you know if it's actually working?

## ✅ Solution: Monitor Script

### Option 1: Real-Time Monitoring (Recommended)

```bash
python monitor_optimization.py
```

**What it does:**
- Watches the `src/data/optimizations/` directory
- Shows new files as they're created
- Displays file size and modification time
- Shows results summary (Sharpe, Return, etc.)
- Updates every 5 seconds
- Press Ctrl+C to stop

**Example output:**
```
📊 Strategy Optimizer Monitor
Watching directory: C:\...\src\data\optimizations

⏳ Checking again in 5 seconds...

📁 Current optimization files (0):
   (No optimization files yet)

⏳ Checking again in 5 seconds...

🆕 New optimization file detected!
   📁 optimization_TSLA_swing_20251107_120000.json
   📍 C:\...\src\data\optimizations\optimization_TSLA_swing_20251107_120000.json

   📊 Results Summary:
      1H: 540 combinations
         Best Sharpe: 1.45
         Best Return: 28.50%
      4H: 540 combinations
         Best Sharpe: 1.62
         Best Return: 34.37%
      1D: 540 combinations
         Best Sharpe: 1.23
         Best Return: 18.90%
```

### Option 2: Show Latest Results Only

```bash
python monitor_optimization.py --latest
```

**What it does:**
- Shows the most recent optimization results
- Displays top 3 combinations per timeframe
- Exits immediately (doesn't keep watching)

**Example output:**
```
📊 Latest Optimization Results
File: optimization_TSLA_swing_20251107_120000.json

🕐 1H TIMEFRAME:
   Total Combinations: 540

   #1:
      MA Length: 150
      Key Value: 2.5
      ATR Mult: 2.0
      TP1 RR: 1.5
      TP1 %: 25
      ---
      Sharpe: 1.45 ⭐
      Return: 28.50%
      Win Rate: 62.5%
      Trades: 24
```

---

## 📁 Where Results Are Saved

All optimization results are saved to:
```
src/data/optimizations/optimization_{SYMBOL}_{TRADETYPE}_{TIMESTAMP}.json
```

**Examples:**
```
optimization_TSLA_swing_20251107_120000.json
optimization_AAPL_daytrade_20251107_121500.json
optimization_SPY_swing_20251107_130000.json
```

---

## 🔍 Manual File Inspection

### Check if files exist:
```bash
# Windows PowerShell
dir src\data\optimizations\

# Or from Python
import os
files = os.listdir('src/data/optimizations')
print(f"Found {len(files)} optimization files")
for f in files:
    print(f"  - {f}")
```

### Check file size (growing = working):
```bash
# Windows PowerShell
Get-Item src\data\optimizations\*.json | Select-Object Name, Length, LastWriteTime

# Or from Python
import os
from pathlib import Path
for f in Path('src/data/optimizations').glob('*.json'):
    size_mb = f.stat().st_size / (1024 * 1024)
    print(f"{f.name}: {size_mb:.2f} MB")
```

### Read JSON file directly:
```python
import json

with open('src/data/optimizations/optimization_TSLA_swing_20251107_120000.json', 'r') as f:
    data = json.load(f)

# Show timeframes
for timeframe, results in data.items():
    print(f"{timeframe}: {len(results)} combinations")
```

---

## 📊 What to Expect

### Timeline for Swing Trade (3 timeframes, 540 combinations each)

```
0-2 min:   Fetching data for 1h timeframe
2-5 min:   Testing 540 combinations for 1h
           File created: optimization_TSLA_swing_*.json
           File size: ~100 KB

5-7 min:   Fetching data for 4h timeframe
7-10 min:  Testing 540 combinations for 4h
           File size: ~200 KB

10-12 min: Fetching data for 1d timeframe
12-15 min: Testing 540 combinations for 1d
           File size: ~300 KB

15 min:    Complete! Results displayed in frontend
```

### File Size Growth

```
After 1h:   ~100 KB (1 timeframe done)
After 2h:   ~200 KB (2 timeframes done)
After 3h:   ~300 KB (all 3 timeframes done)
```

---

## 🚨 Troubleshooting

### "No optimization files yet" after 5 minutes

**Possible causes:**
1. Optimization hasn't started yet
2. Data fetching is taking longer than expected
3. Error occurred (check server logs)

**Solutions:**
1. Check server console for errors
2. Verify ticker is valid (try TSLA)
3. Check internet connection
4. Try with fewer bars (500 instead of 2000)

### File size not growing

**Possible causes:**
1. Optimization crashed
2. Backtesting is stuck
3. Data fetch failed

**Solutions:**
1. Check server console for errors
2. Restart the server
3. Try with a different ticker
4. Try with fewer bars

### Results look wrong (0 trades, 0% win rate)

**Possible causes:**
1. Strategy didn't generate signals
2. Data is invalid
3. Parameters are too restrictive

**Solutions:**
1. Try a different ticker
2. Try a different trade type
3. Increase max_bars to get more data
4. Check strategy logic in AGBotGeneric.py

---

## 💡 Pro Tips

1. **Start with 500 bars** for quick testing
2. **Monitor in one terminal** while working in another
3. **Check latest results** frequently to see progress
4. **Save results** before closing the page
5. **Compare multiple runs** to find best parameters

---

## 📞 Quick Commands

```bash
# Watch optimization in real-time
python monitor_optimization.py

# Show latest results only
python monitor_optimization.py --latest

# Check if files exist
dir src\data\optimizations\

# Delete old results (keep latest)
# (Be careful with this!)
```

---

**Status:** ✅ Ready to use  
**Last Updated:** November 7, 2025
