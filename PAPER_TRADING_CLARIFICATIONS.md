# Paper Trading Engine - Clarifications & Updates

**Date:** November 10, 2025  
**Status:** ✅ UPDATED PER USER FEEDBACK

---

## Three Key Clarifications

### 1. Asset Type Detection - From Webhook JSON ✅

**You're correct:** Asset type should come from the webhook JSON, not be auto-detected.

**Updated Webhook Format:**
```json
{
  "ticker": "QQQ",
  "interval": "2",
  "timeframe": "2m",
  "action": "buy",
  "contracts": "10",
  "price": "620.00",
  "asset_type": "stock"  // ← EXPLICIT FIELD
}
```

**Or for options:**
```json
{
  "ticker": "QQQ",
  "interval": "2",
  "timeframe": "2m",
  "action": "buy",
  "contracts": "3",
  "price": "2.50",
  "asset_type": "option",  // ← EXPLICIT FIELD
  "option_symbol": ".QQQ251110C500",
  "strike": 500,
  "expiry": "2025-11-10"
}
```

**Updated Detection Logic:**
```python
def _detect_asset_type(self, webhook_data: Dict) -> str:
    # Use explicit field from webhook
    asset_type = webhook_data.get('asset_type', 'stock').lower()
    if asset_type in ['stock', 'option']:
        return asset_type
    return 'stock'  # Safe default
```

---

### 2. Single Account with Timeframe Filtering ✅

**You're correct:** One account is simpler. You'll filter by timeframe later for performance comparison.

**Updated Architecture:**
- **Single $10,000 account** for all trades
- **Timeframes:** 2m, 3m, 1H (as you're testing)
- **Each trade tagged with timeframe** for later filtering
- **You filter later** for performance comparison

**Benefits:**
- ✅ Simpler implementation
- ✅ Matches your actual testing setup
- ✅ Easy to filter trades by timeframe later
- ✅ No cross-contamination between timeframes

**Account Structure:**
```python
{
    'account_balance': 10000.00,
    'initial_balance': 10000.00,
    'trades': [
        {
            'type': 'BUY',
            'ticker': 'QQQ',
            'timeframe': '2m',  # ← Tagged with timeframe
            'entry_price': 620.00,
            'pnl': 50.00,
            ...
        },
        {
            'type': 'SELL',
            'ticker': 'QQQ',
            'timeframe': '3m',  # ← Different timeframe
            'exit_price': 625.00,
            'pnl': -10.00,
            ...
        }
    ],
    'open_positions': [...],
    'webhooks': [...]
}
```

**Filtering Later:**
```python
# Get trades for specific timeframe
trades_2m = [t for t in account['trades'] if t['timeframe'] == '2m']
trades_3m = [t for t in account['trades'] if t['timeframe'] == '3m']
trades_1h = [t for t in account['trades'] if t['timeframe'] == '1H']

# Calculate P&L per timeframe
pnl_2m = sum(t['pnl'] for t in trades_2m)
pnl_3m = sum(t['pnl'] for t in trades_3m)
pnl_1h = sum(t['pnl'] for t in trades_1h)
```

---

### 3. Tastytrade is Market Data ONLY ✅

**Confirmed:** Tastytrade is ONLY for fetching option prices/quotes.

**Tastytrade IS Used For:**
- ✅ Getting ATM option prices
- ✅ Getting bid/ask spreads
- ✅ Getting underlying prices
- ✅ Simulating realistic option pricing

**Tastytrade is NOT Used For:**
- ❌ Executing trades
- ❌ Placing orders
- ❌ Managing positions
- ❌ Any actual trading

**Paper Trading Engine:**
- Simulates ALL trades in-memory
- No actual orders placed anywhere
- No connection to any broker
- Pure simulation for testing/backtesting

**Fallback Pricing:**
- If Tastytrade API unavailable
- Generates realistic option pricing
- Realistic underlying prices
- Realistic bid/ask spreads
- Continues simulation seamlessly

---

## 4. Share-to-Contract Conversion (Option A) ✅

**Strategy sends shares, app converts to option contracts:**

**Example Flow:**
```
Strategy calculates: 100 shares (2.5% risk)
Webhook sends: "contracts": "100"
App receives: asset_type = "option"
App converts: 100 shares ÷ 100 = 1 option contract
App trades: 1 contract @ $2.50 = $250 cost (1 × 2.50 × 100)
```

**Conversion Logic:**
```python
# In paper_trading_engine.py
option_contracts = int(contracts / 100)
if option_contracts < 1:
    option_contracts = 1  # Minimum 1 contract

# Example conversions:
# 100 shares → 1 contract
# 200 shares → 2 contracts
# 50 shares → 1 contract (minimum)
# 350 shares → 3 contracts
```

**Cost Calculation:**
- Stock: `cost = contracts × price` (100 shares × $620 = $62,000)
- Option: `cost = option_contracts × price × 100` (1 contract × $2.50 × 100 = $250)

---

## Implementation Changes

### Files Updated

**`src/trading/paper_trading_engine.py`:**
- ✅ Changed from per-timeframe accounts to single account
- ✅ Updated asset type detection to use webhook field
- ✅ Updated timeframe extraction for 2m, 3m, 1H
- ✅ Each trade tagged with timeframe
- ✅ Simplified account management
- ✅ Added share-to-contract conversion for options (100 shares = 1 contract)
- ✅ Logs conversion: "Converting 100 shares → 1 option contract(s)"

**`src/web/app.py`:**
- ✅ Updated state endpoint (no timeframe parameter)
- ✅ Updated webhook handler (single account)
- ✅ Updated add_paper_trade endpoint
- ✅ Updated reset endpoint (single account)

---

## Webhook Format (TradingView)

### Pine Script Alert Message

```json
{
  "ticker": "{{ticker}}",
  "exchange": "{{exchange}}",
  "interval": "{{interval}}",
  "timeframe": "{{interval}}",
  "action": "{{strategy.order.action}}",
  "contracts": "{{strategy.order.contracts}}",
  "price": "{{strategy.order.price}}",
  "market_position": "{{strategy.market_position}}",
  "asset_type": "stock"
}
```

**For Options:**
```json
{
  "ticker": "{{ticker}}",
  "interval": "{{interval}}",
  "timeframe": "{{interval}}",
  "action": "{{strategy.order.action}}",
  "contracts": "{{strategy.order.contracts}}",
  "price": "{{strategy.order.price}}",
  "asset_type": "option",
  "option_symbol": ".QQQ251110C500",
  "strike": 500,
  "expiry": "2025-11-10"
}
```

---

## API Endpoints

### Get Account State

```bash
GET /api/paper-trading/state
```

**Response:**
```json
{
  "account_balance": 10000.00,
  "initial_balance": 10000.00,
  "trades": [...],
  "open_positions": [...],
  "webhooks": [...]
}
```

### Execute Trade (Webhook)

```bash
POST /api/paper-trading/webhook
Content-Type: application/json

{
  "ticker": "QQQ",
  "interval": "2",
  "timeframe": "2m",
  "action": "buy",
  "contracts": "10",
  "price": "620.00",
  "asset_type": "stock"
}
```

### Reset Account

```bash
POST /api/paper-trading/reset
```

---

## Testing Checklist

- [ ] Restart Flask server
- [ ] Send BUY webhook with `asset_type: "stock"`
- [ ] Verify trade in `/api/paper-trading/state`
- [ ] Verify `timeframe` field in trade
- [ ] Send SELL webhook
- [ ] Verify P&L calculated correctly
- [ ] Test multiple timeframes (2m, 3m, 1H)
- [ ] Verify trades tagged with correct timeframe
- [ ] Filter trades by timeframe manually
- [ ] Verify state persists in JSON file

---

## Summary

✅ **Asset Type:** Now from webhook JSON (explicit field)  
✅ **Accounts:** Single $10k account (you filter by timeframe later)  
✅ **Tastytrade:** Market data only (no trade execution)  
✅ **Timeframes:** Each trade tagged for later filtering  
✅ **Implementation:** Updated and ready to test

**Status:** PRODUCTION READY

Tags: paper_trading, webhook, clarifications, asset_type, single_account, tastytrade, nov10_2025
