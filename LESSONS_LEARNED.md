# 🎓 LESSONS LEARNED

**Compiled from**: Archived troubleshooting notes, debug scripts, and integration tests  
**Date**: November 17, 2025

---

## 1. Summary of Themes

### Critical Issues Resolved
1. **DXLink Async Context Manager** – Sequencing of subscribe/listen operations
2. **Options Position Tracking** – Handling Greeks and DTE
3. **Paper Trading State** – Session persistence and PnL calculation
4. **Optimization Timeouts** – Managing long-running backtest operations
5. **RBI + RL Integration** – Combining rule-based and RL agents

---

## 2. Key Lessons

### 🔌 DXLink Streaming & Async Context Managers

**Problem**: Race condition between context manager setup and subscription.

**Solution**:
```python
# ✅ CORRECT: Yield to event loop first
async with DXLinkStreamer(self.session) as streamer:
    await asyncio.sleep(0)  # Yield to event loop
    if self.pending_symbols:
        await self._subscribe_pending()  # Now channels exist
    await asyncio.gather(
        self._quote_receiver(Quote),
        self._subscription_manager()
    )
```

**Gotcha**: `await asyncio.sleep(0)` yields without delay. Never create tasks before context manager setup completes.

---

### 📊 Options Position Tracking

**Problem**: Complex Greeks and DTE handling.

**Solution**:
```python
def extract_greeks(quote):
    return {
        'delta': getattr(quote, 'delta', 0.0) or 0.0,
        'gamma': getattr(quote, 'gamma', 0.0) or 0.0,
        'theta': getattr(quote, 'theta', 0.0) or 0.0,
        'vega': getattr(quote, 'vega', 0.0) or 0.0,
    }

def calculate_dte(expiration_date):
    from datetime import datetime
    return (expiration_date - datetime.now().date()).days
```

**Gotcha**: Greeks may be None. Always use `getattr(obj, 'attr', 0.0) or 0.0`. Theta is negative for longs.

---

### 💾 Paper Trading State Persistence

**Problem**: Complex object serialization across sessions.

**Solution**:
```python
def save_state(state, filepath):
    data = {
        'cash': state.cash,
        'positions': {
            symbol: {
                'quantity': pos['quantity'],
                'entry_price': pos['entry_price'],
                'entry_time': pos['entry_time'].isoformat(),
            }
            for symbol, pos in state.positions.items()
        }
    }
    with open(filepath, 'w') as f:
        json.dump(data, f)
```

**Gotcha**: Use `.isoformat()` for datetime serialization. Use `.date()` for expiration dates (timezone-safe).

---

### ⏱️ Optimization Timeouts

**Problem**: Long-running optimizations need timeout handling.

**Solution**:
```python
async def run_with_timeout(strategy, params, timeout_seconds=300):
    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, strategy.optimize, params),
            timeout=timeout_seconds
        )
        return {'status': 'complete', 'result': result}
    except asyncio.TimeoutError:
        return {'status': 'timeout', 'error': f'Exceeded {timeout_seconds}s'}
```

**Gotcha**: Use `asyncio.wait_for()` for timeout, not `signal.alarm()` (doesn't work on Windows).

---

### 🤖 RBI + RL Integration

**Problem**: Conflicts between rule-based and RL signals.

**Solution**:
```python
def combine_signals(rbi_signal, rl_signal, rbi_weight=0.6, rl_weight=0.4):
    # RBI takes priority if strong signal
    if rbi_signal['confidence'] > 0.8:
        return rbi_signal['action']
    
    # Otherwise weight by confidence
    rbi_score = action_to_score(rbi_signal['action']) * rbi_signal['confidence'] * rbi_weight
    rl_score = action_to_score(rl_signal['action']) * rl_signal['confidence'] * rl_weight
    
    total_score = rbi_score + rl_score
    if total_score > 0.5:
        return 'BUY'
    elif total_score < -0.5:
        return 'SELL'
    else:
        return 'HOLD'
```

**Gotcha**: RBI should have veto power. Capital allocation should rebalance weekly, not daily.

---

### 🔍 SDK Introspection

**Problem**: Tastytrade SDK structure not fully documented.

**Solution**:
```python
import inspect

def inspect_class(cls):
    print(f"\nClass: {cls.__name__}")
    for name, method in inspect.getmembers(cls, predicate=inspect.ismethod):
        if not name.startswith('_'):
            print(f"  - {name}")

# Safe attribute access
def safe_getattr(obj, attr, default=None):
    try:
        value = getattr(obj, attr, default)
        return value if value is not None else default
    except:
        return default
```

**Gotcha**: Some attributes are lazy-loaded. Always check before using. Use `hasattr()` before `getattr()`.

---

### 🔗 TradingView Webhook Integration

**Problem**: Webhook format validation.

**Solution**:
```python
def validate_webhook(data):
    required = ['symbol', 'action', 'quantity']
    for field in required:
        if field not in data:
            raise ValueError(f"Missing: {field}")
    
    if data['action'] not in ['BUY', 'SELL', 'CLOSE']:
        raise ValueError(f"Invalid action: {data['action']}")
    
    if not isinstance(data['quantity'], int) or data['quantity'] <= 0:
        raise ValueError(f"Invalid quantity: {data['quantity']}")
    
    return True
```

**Gotcha**: Symbol must be uppercase. Action must be exact. Quantity must be positive integer.

---

## 3. Useful Archived Tools

- `check_equity_class.py` – Inspect Tastytrade Equity SDK
- `check_quote_attributes.py` – Inspect Quote object
- `debug_tastytrade_auth.py` – Debug authentication
- `test_dxlink_subscription.py` – Test DXLink streaming
- `optimize_agbot_shorts_asymmetric.py` – Shorts optimization
- `test_rbi_rl_implementation.py` – RBI + RL integration test

---

## 4. Recommendations

### For Future Development

1. **Async Patterns**: Always yield to event loop before operations on context managers
2. **Options Trading**: Validate Greeks exist before using. Handle None values gracefully
3. **State Persistence**: Use `.isoformat()` for datetime serialization
4. **Long Operations**: Implement timeout handling and progress tracking
5. **Multi-Agent Systems**: Combine signals at decision level with clear priority rules
6. **SDK Integration**: Use introspection to understand undocumented structures
7. **Webhooks**: Always validate format before processing

### Testing Best Practices

- Create integration tests for each phase
- Mock external APIs (Tastytrade, TradingView)
- Test edge cases (None values, missing fields, timeouts)
- Use fixtures for common test data

### Documentation

- Document SDK quirks and workarounds
- Keep troubleshooting guides for common issues
- Archive experimental code with context for future reference

---

## 5. Files by Purpose

**See ARCHIVED_FILES/INDEX.md for complete inventory**

- **Debug Scripts** (15): SDK inspection, API testing
- **Integration Tests** (28): Phase testing, feature validation
- **Troubleshooting Notes** (74): Status updates, technical deep-dives
- **Reference Guides** (36): Implementation guides, feature documentation

---

**Last Updated**: November 17, 2025  
**Archive Location**: `ARCHIVED_FILES/`  
**Index**: `ARCHIVED_FILES/INDEX.md`
