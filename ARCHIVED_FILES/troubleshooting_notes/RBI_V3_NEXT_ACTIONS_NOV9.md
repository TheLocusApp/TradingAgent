# RBI V3 Next Actions - November 9, 2025

## What Was Fixed ✅

**KeyError: 'stop_loss_price'** - Optimization loop now runs without crashing

- Changed `optimize_strategy()` from `.format()` to `.replace()`
- Escaped braces in DEBUG_PROMPT and OPTIMIZE_PROMPT
- Allows optimization loop to proceed to next phase

---

## What Needs Fixing ⚠️

### Priority 1: SL/TP Validation Too Strict (BLOCKING)

**Problem**: All orders being rejected, resulting in 0 trades

**Example from logs**:
```
🌙 MOON DEV DEBUG: Short order validation failed - TP: 596.0561645507812, Entry: 589.719970703125, SL: 601.5143701171875
```

**Root Cause**: TP (596.06) is ABOVE entry (589.72) for a SHORT order - this is WRONG!

**Solution**:
1. Update BACKTEST_PROMPT to emphasize:
   - For SHORTS: TP MUST be BELOW entry price
   - For LONGS: TP MUST be ABOVE entry price
2. Add floating point tolerance (0.01% of entry price)
3. Add pre-validation BEFORE calculating SL/TP

**Estimated Time**: 30 minutes

---

### Priority 2: Invalid backtesting.py API Usage (BLOCKING)

**Problem**: `AttributeError: 'DivergenceConfirmer' object has no attribute 'positions'`

**Root Cause**: AI generated `self.positions` (plural) but backtesting.py only has `self.position` (singular)

**Solution**:
1. Update BACKTEST_PROMPT with clear API documentation:
   - `self.position` - Current open position (single)
   - `self.trades` - List of all closed trades
   - `self.positions` - DOES NOT EXIST
2. Add examples of correct position management
3. Emphasize: backtesting.py supports only ONE open position at a time

**Estimated Time**: 20 minutes

---

### Priority 3: Mean Reversion Strategy Generates 0 Trades (MEDIUM)

**Problem**: Strategy prints entry signals but takes 0 trades

**Root Cause**: Likely one of:
1. Position sizing is invalid (integer instead of fraction)
2. Entry conditions too restrictive
3. self.buy() not being called

**Solution**:
1. Check generated code for position sizing
2. Verify entry conditions are reasonable
3. Add validation for entry signal generation

**Estimated Time**: 45 minutes

---

## Testing Plan

### Test 1: Verify KeyError Fix
```bash
# Run RBI V3 with any trading idea
# Should proceed past optimization attempt without KeyError
```

### Test 2: Verify SL/TP Validation
```bash
# Check backtest output for:
# - Orders being accepted (not all rejected)
# - Correct SL/TP ordering
# - Trades > 0
```

### Test 3: Verify backtesting.py API
```bash
# Check for:
# - No AttributeError: 'positions'
# - Correct use of self.position
# - Correct use of self.trades
```

---

## Implementation Order

1. **Test the KeyError fix** (5 min)
   - Run RBI V3, verify optimization loop proceeds

2. **Fix SL/TP validation** (30 min)
   - Update BACKTEST_PROMPT with better examples
   - Add tolerance to validation logic
   - Test with VolatilityBreakout strategy

3. **Fix backtesting.py API** (20 min)
   - Update BACKTEST_PROMPT with API documentation
   - Add examples of correct position management
   - Test with DivergenceConfirmer strategy

4. **Fix mean reversion strategy** (45 min)
   - Debug position sizing
   - Debug entry conditions
   - Test with AdaptiveReversion strategy

---

## Quick Reference: backtesting.py API

### Position Management
```python
# ✅ CORRECT
if self.position:
    # We have an open position
    self.position.close()

# ❌ WRONG
if len(self.positions) >= 1:  # self.positions doesn't exist!
    pass
```

### Trade History
```python
# ✅ CORRECT
if self.trades:
    last_trade = self.trades[-1]
    entry_price = last_trade.entry_price

# ❌ WRONG
entry_price = self.position.entry_price  # Position doesn't have this attribute
```

### Position Sizing
```python
# ✅ CORRECT - Fraction of equity
size = 0.5  # 50% of equity
self.buy(size=size, sl=stop_loss, tp=take_profit)

# ❌ WRONG - Integer share count
size = 100  # 100 shares (backtesting.py rejects this silently)
self.buy(size=size, sl=stop_loss, tp=take_profit)
```

---

## Files to Update

1. `src/agents/rbi_agent_v3.py`
   - BACKTEST_PROMPT: Add SL/TP validation with tolerance
   - BACKTEST_PROMPT: Add backtesting.py API documentation
   - DEBUG_PROMPT: Add API documentation

---

**Status**: Ready for next iteration  
**Blocker**: SL/TP validation and backtesting.py API usage  
**Next Session**: Implement Priority 1 and 2 fixes
