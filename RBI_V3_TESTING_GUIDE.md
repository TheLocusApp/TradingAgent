# RBI V3 Testing Guide - After Critical Fixes

## Quick Test

### Test 1: Data Loading Fix
**Goal**: Verify data loads without KeyError: 'datetime'

**Steps**:
1. Run RBI V3 with any trading idea
2. Watch for Phase 1 (Research) and Phase 2 (Backtest)
3. Check output for:
   - ✅ "🌙 MOON DEV DATA LOADED: X rows"
   - ❌ KeyError: 'datetime' (should NOT appear)

**Expected Output**:
```
🌙 MOON DEV DATA LOADED: 3494 rows, columns: ['Open', 'High', 'Low', 'Close', 'Volume', ...]
```

---

### Test 2: SL/TP Validation Fix
**Goal**: Verify SL/TP validation prevents crashes

**Steps**:
1. Run RBI V3 with mean reversion strategy
2. Watch for debug messages during execution
3. Check for:
   - ✅ "🌙 MOON DEV DEBUG: Long order validation failed" (skipped invalid orders)
   - ✅ "🌙 MOON DEV SHORT ENTRY: Size: X, Entry: Y, SL: Z, TP: W" (valid orders)
   - ❌ ValueError: Long orders require: SL < LIMIT < TP (should NOT appear)

**Expected Output**:
```
🌙 MOON DEV ALERT: Upper BB touched! RSI: 77.73, Volume: 9081658 > 8911452
📉 MOON DEV SHORT ENTRY: Size: 4167, Entry: 452.15, SL: 454.55, TP: 451.39
🌙 MOON DEV DEBUG: Short order validation failed - TP: 559.25, Entry: 559.17, SL: 562.75
📉 MOON DEV SHORT ENTRY: Size: 2604, Entry: 559.68, SL: 563.41, TP: 559.38
```

---

### Test 3: Full Optimization Loop
**Goal**: Verify optimization loop runs without crashes

**Steps**:
1. Run RBI V3 with 50% target return
2. Watch for:
   - Phase 1: Research ✅
   - Phase 2: Backtest ✅
   - Phase 3: Debug (if needed) ✅
   - Phase 4: Execution ✅
   - Optimization Loop (1-10 iterations) ✅

**Expected Output**:
```
🎉 BACKTEST EXECUTED SUCCESSFULLY WITH TRADES!
📊 Extracted return: -1.10157%
📊 Current Return: -1.10157%
🎯 Target Return: 50%
📈 Need to gain 51.10157% more to hit target
🎯 Starting OPTIMIZATION LOOP...

🔄 Optimization attempt 1/10
🎯 Starting Optimization AI (iteration 1)...
✅ Backtest executed successfully in 4.39s!
```

---

## Detailed Checks

### Check 1: Data Loading
```python
# Look for this in output:
🌙 MOON DEV DATA LOADED: 3494 rows, columns: ['Open', 'High', 'Low', 'Close', 'Volume', 'dividends', 'stock splits', 'capital gains']

# NOT this:
KeyError: 'datetime'
```

### Check 2: SL/TP Validation
```python
# Look for valid orders:
📉 MOON DEV SHORT ENTRY: Size: 4167, Entry: 452.15, SL: 454.55, TP: 451.39
# Verify: TP (451.39) < Entry (452.15) < SL (454.55) ✅

🚀 MOON DEV LONG ENTRY: Size: 2667, Entry: 497.71, SL: 493.96, TP: 498.57
# Verify: SL (493.96) < Entry (497.71) < TP (498.57) ✅

# Look for skipped invalid orders:
🌙 MOON DEV DEBUG: Short order validation failed - TP: 559.25, Entry: 559.17, SL: 562.75
# Verify: TP (559.25) < Entry (559.17)? NO! ❌ Correctly skipped
```

### Check 3: Backtest Execution
```python
# Look for successful execution:
✅ Backtest executed successfully in 3.35s!

# Look for stats output:
Return [%]                           -1.10157
# Trades                                   11
Win Rate [%]                         72.72727
Sharpe Ratio                         -0.17253

# NOT this:
❌ Backtest failed with return code: 1
ValueError: Long orders require: SL < LIMIT < TP
```

---

## Troubleshooting

### If you see: KeyError: 'datetime'
**Cause**: Data loading still using reset_index()
**Fix**: Check that BACKTEST_PROMPT doesn't have:
```python
data = data.reset_index()  # ❌ WRONG
data['datetime'] = pd.to_datetime(data['datetime'])  # ❌ WRONG
```

**Should have**:
```python
data = yf.Ticker("SPY").history(period="2y", interval="1d")
# datetime is already INDEX - keep it there! ✅
```

---

### If you see: ValueError: Long orders require: SL < LIMIT < TP
**Cause**: SL/TP ordering validation not working
**Fix**: Check that generated code has validation:
```python
# For LONG orders
if stop_loss_price >= entry_price or take_profit_price <= entry_price:
    print(f"🌙 MOON DEV DEBUG: Long order validation failed")
    return  # Skip invalid order
```

**If missing**: Debug AI needs to add this validation code

---

### If you see: 0 trades in backtest
**Cause**: Either:
1. Entry signals never triggered
2. All orders were skipped due to validation
3. Position sizing is wrong

**Check**:
- Look for "ENTRY SIGNAL" debug messages
- Look for "validation failed" debug messages
- Check position size is int or 0-1 fraction

---

## Success Criteria

✅ **Test 1 Passed**: Data loads without KeyError
✅ **Test 2 Passed**: SL/TP validation prevents crashes
✅ **Test 3 Passed**: Optimization loop runs 1-10 iterations
✅ **All Checks Passed**: Backtest executes with trades and stats

---

## Example Test Run

```bash
# Run RBI V3 with mean reversion on SPY 1h
python src/agents/rbi_agent_v3.py

# Expected flow:
🚀 Moon Dev's RBI AI v3.0 Processing New Idea!
🎯 Target Return: 50%
📝 Processing idea: mean reversion on SPY 1h...

🧪 Phase 1: Research
✅ Strategy name: AdaptiveReversion

📈 Phase 2: Backtest
🌙 MOON DEV DATA LOADED: 3494 rows
📉 MOON DEV SHORT ENTRY: Size: 4167, Entry: 452.15, SL: 454.55, TP: 451.39
🌙 MOON DEV DEBUG: Short order validation failed - TP: 559.25, Entry: 559.17, SL: 562.75
🎉 BACKTEST EXECUTED SUCCESSFULLY WITH TRADES!
📊 Extracted return: -1.10157%

🔄 Optimization attempt 1/10
✅ Backtest executed successfully in 4.39s!
```

---

## Performance Expectations

| Metric | Expected |
|--------|----------|
| Data Load Time | < 1 second |
| Backtest Execution | 3-5 seconds |
| Optimization Iteration | 4-6 seconds |
| Full Loop (10 iterations) | 40-60 seconds |
| Total Time (Research + Backtest + Optimize) | 2-5 minutes |

---

**Date**: November 8, 2025  
**Status**: Testing Guide Ready  
**Next**: Run tests and verify all checks pass
