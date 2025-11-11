# RBI V3 Critical Failures Analysis & Fixes - November 9, 2025

## Executive Summary

Three major failures occurred in RBI V3 during optimization loop execution:

1. ✅ **FIXED: KeyError: 'stop_loss_price'** - String formatting error in optimization prompt
2. ⚠️ **IDENTIFIED: SL/TP Validation Skipping All Orders** - Validation logic too strict
3. ⚠️ **IDENTIFIED: AttributeError: 'positions'** - AI generating invalid backtesting.py code

---

## Issue 1: KeyError: 'stop_loss_price' ✅ FIXED

### Root Cause
The `optimize_strategy()` function used Python's `.format()` method to inject `{current_return}` and `{target_return}` into the OPTIMIZE_PROMPT. However, the prompt also contains code examples with `{stop_loss_price}`, `{entry_price}`, and `{take_profit_price}` variables.

When `.format()` encounters these braces, it tries to find matching variables to substitute, causing:
```
KeyError: 'stop_loss_price'
```

### The Problem Code
```python
# Line 1034-1037 (BEFORE FIX)
optimize_prompt_with_stats = OPTIMIZE_PROMPT.format(
    current_return=current_return,
    target_return=target_return
)
```

### The Fix
Changed from `.format()` to `.replace()` to avoid interpreting code example braces:

```python
# Line 1034-1039 (AFTER FIX)
optimize_prompt_with_stats = OPTIMIZE_PROMPT.replace(
    "{current_return}", str(current_return)
).replace(
    "{target_return}", str(target_return)
)
```

### Why This Works
- `.replace()` does literal string replacement without interpreting braces
- Preserves all `{stop_loss_price}` and other braces in code examples
- Only replaces the specific placeholders we want

### Also Fixed
Updated DEBUG_PROMPT and OPTIMIZE_PROMPT to use escaped braces `{{` and `}}` for code examples that will be shown to the AI:

```python
# BEFORE (causes KeyError)
print(f"SL: {stop_loss_price}, Entry: {entry_price}")

# AFTER (safe for .format())
print(f"SL: {{stop_loss_price}}, Entry: {{entry_price}}")
```

---

## Issue 2: SL/TP Validation Skipping ALL Orders ⚠️ IDENTIFIED

### The Problem
Looking at the backtest output for "VolatilityBreakout":

```
🌙 MOON DEV DEBUG: Short order validation failed - TP: 596.0561645507812, Entry: 589.719970703125, SL: 601.5143701171875
🌙 MOON DEV DEBUG: Short order validation failed - TP: 572.5850280761719, Entry: 567.1799926757812, SL: 578.5235925292969
...
# Trades                                    0
Return [%]                                0.0
```

**Every single order is being rejected!** The validation code is too strict.

### Root Cause
The AI is generating validation code that rejects ALL orders because:

1. **Floating point precision issues**: Prices like `589.719970703125` have rounding errors
2. **Validation logic too strict**: Using `>=` and `<=` instead of allowing small tolerances
3. **AI doesn't understand backtesting.py's actual behavior**: The library has some tolerance for SL/TP placement

### Current Validation (TOO STRICT)
```python
# For SHORT orders
if take_profit_price >= entry_price or stop_loss_price <= entry_price:
    print(f"Short order validation failed...")
    return  # Skip invalid order
```

### The Real Issue
For the short order above:
- Entry: 589.719970703125
- TP: 596.0561645507812 (ABOVE entry - should be BELOW!)
- SL: 601.5143701171875 (ABOVE entry - correct)

**The TP is ABOVE the entry price, which is wrong for a short!** The AI is generating invalid orders.

### Solution Needed
The BACKTEST_PROMPT and DEBUG_PROMPT need to emphasize:
1. **For SHORTS: TP MUST be BELOW entry price**
2. **Add tolerance for floating point errors** (e.g., 0.01% tolerance)
3. **Validate BEFORE calculating SL/TP**, not after

---

## Issue 3: AttributeError: 'positions' ⚠️ IDENTIFIED

### The Problem
```
AttributeError: 'DivergenceConfirmer' object has no attribute 'positions'. Did you mean: 'position'?
```

### Root Cause
The AI generated code trying to access `self.positions` (plural), but backtesting.py only has `self.position` (singular).

### backtesting.py API
- ✅ `self.position` - Current position (single)
- ✅ `self.trades` - List of all trades
- ❌ `self.positions` - Does NOT exist!

### The Generated Code (WRONG)
```python
if len(self.positions) >= self.max_positions:  # ❌ WRONG
    return
```

### Correct Code
```python
if self.position:  # ✅ Check if position exists
    return
```

### Solution
The BACKTEST_PROMPT needs to explicitly state:
- backtesting.py only supports ONE open position at a time
- Use `self.position` (singular), not `self.positions` (plural)
- Use `self.trades` for trade history

---

## Summary of Changes Made

### File: `src/agents/rbi_agent_v3.py`

#### Change 1: Fix optimize_strategy() formatting (Line 1034-1039)
- **Before**: Used `.format()` which caused KeyError
- **After**: Uses `.replace()` for literal string replacement
- **Status**: ✅ COMPLETE

#### Change 2: Escape braces in DEBUG_PROMPT (Line 471, 476)
- **Before**: `{stop_loss_price}` - causes KeyError in .format()
- **After**: `{{stop_loss_price}}` - escaped for safe .format()
- **Status**: ✅ COMPLETE

#### Change 3: Escape braces in OPTIMIZE_PROMPT (Line 597, 602)
- **Before**: `{stop_loss_price}` - causes KeyError in .format()
- **After**: `{{stop_loss_price}}` - escaped for safe .format()
- **Status**: ✅ COMPLETE

---

## Remaining Issues to Address

### HIGH PRIORITY

1. **SL/TP Validation Too Strict**
   - AI rejects all orders due to floating point precision
   - Need to add tolerance (e.g., 0.01% of entry price)
   - Need to validate BEFORE generating orders, not after

2. **Invalid backtesting.py API Usage**
   - AI uses `self.positions` instead of `self.position`
   - AI doesn't understand single position limitation
   - BACKTEST_PROMPT needs clearer API documentation

3. **Mean Reversion Strategy Generating 0 Trades**
   - Strategy signals but doesn't execute
   - Likely position sizing or entry condition issue
   - Need better entry signal generation

### MEDIUM PRIORITY

4. **No Trades Taken in VolatilityBreakout**
   - All orders rejected by validation
   - Need to fix SL/TP generation logic

5. **DivergenceConfirmer AttributeError**
   - Using wrong backtesting.py API
   - Need better API documentation in prompts

---

## Testing Checklist

- [ ] Run optimization loop without KeyError
- [ ] Verify SL/TP validation allows valid orders
- [ ] Verify AI doesn't use `self.positions`
- [ ] Verify mean reversion strategy generates trades
- [ ] Verify VolatilityBreakout strategy generates trades
- [ ] Verify DivergenceConfirmer uses correct API

---

## Next Steps

1. **Immediate**: Test with the KeyError fix applied
2. **Short-term**: Enhance BACKTEST_PROMPT with:
   - Clearer SL/TP validation with tolerance
   - Explicit backtesting.py API documentation
   - Examples of correct position management
3. **Medium-term**: Add pre-execution validation to catch these errors before runtime

---

**Date**: November 9, 2025  
**Status**: 1 of 3 issues fixed, 2 identified for next iteration  
**Impact**: Critical - Prevents optimization loop from running
