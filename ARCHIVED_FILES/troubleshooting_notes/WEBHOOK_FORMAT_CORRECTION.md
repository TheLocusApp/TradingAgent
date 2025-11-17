# Webhook Format Correction - Nov 9, 2025

## Issue Found ❌ → Fixed ✅

**Problem**: The webhook JSON format was hardcoding values instead of using TradingView placeholders.

**Example of Wrong Format**:
```json
{
  "action": "ENTRY",
  "signal": "BUY",
  "type": "LONG",
  "underlying": "QQQ",
  "price": 500.25,
  "timestamp": "2025-11-09T11:30:00Z",
  "strategy": "AGBot",
  "timeframe": "1H"
}
```

**Why This Was Wrong**:
- ❌ Hardcoded values don't reflect actual strategy state
- ❌ Can't determine if it's a LONG or SHORT from the data
- ❌ Missing critical position information
- ❌ Can't track previous position state

---

## Correct Format ✅

Use **TradingView Pine Script placeholders** (from the image you provided):

```json
{
  "ticker": "{{ticker}}",
  "exchange": "{{exchange}}",
  "interval": "{{interval}}",
  "time": "{{time}}",
  "timenow": "{{timenow}}",
  "position_size": "{{strategy.position_size}}",
  "action": "{{strategy.order.action}}",
  "contracts": "{{strategy.order.contracts}}",
  "price": "{{strategy.order.price}}",
  "order_id": "{{strategy.order.id}}",
  "comment": "{{strategy.order.comment}}",
  "alert_message": "{{strategy.order.alert_message}}",
  "market_position": "{{strategy.market_position}}",
  "market_position_size": "{{strategy.market_position_size}}",
  "prev_market_position": "{{strategy.prev_market_position}}",
  "prev_market_position_size": "{{strategy.prev_market_position_size}}"
}
```

---

## Key Differences

### Old (Wrong) vs New (Correct)

| Aspect | Old | New |
|--------|-----|-----|
| **Format** | Hardcoded values | TradingView placeholders |
| **Direction** | Hardcoded "BUY"/"SELL" | Dynamic `{{strategy.order.action}}` |
| **Position Type** | Hardcoded "LONG"/"SHORT" | Dynamic `{{strategy.market_position}}` |
| **Contracts** | Hardcoded "3" | Dynamic `{{strategy.order.contracts}}` |
| **Price** | Hardcoded price | Dynamic `{{strategy.order.price}}` |
| **Previous State** | Not tracked | Tracked with `prev_market_position` |
| **Flexibility** | Limited | Full strategy data available |

---

## How Placeholders Work

When TradingView sends the webhook, it **replaces** each `{{placeholder}}` with the actual value:

**Example - What TradingView Sends**:
```json
{
  "ticker": "BTCUSD",
  "exchange": "BINANCE",
  "interval": "1m",
  "time": "2025-11-09T11:30:00Z",
  "timenow": "2025-11-09T11:30:00Z",
  "position_size": "1",
  "action": "buy",
  "contracts": "1",
  "price": "45000.50",
  "order_id": "12345",
  "comment": "SMA crossover signal",
  "alert_message": "Long entry signal",
  "market_position": "long",
  "market_position_size": "1",
  "prev_market_position": "flat",
  "prev_market_position_size": "0"
}
```

---

## Pine Script Implementation

Use this in your strategy's alert message:

```pine
//@version=5
strategy("AGBot Webhook Test", overlay=true)

longCondition = ta.crossover(ta.sma(close, 9), ta.sma(close, 21))
shortCondition = ta.crossunder(ta.sma(close, 9), ta.sma(close, 21))

if longCondition
    alertMessage = '{"ticker": "{{ticker}}", "exchange": "{{exchange}}", "interval": "{{interval}}", "time": "{{time}}", "timenow": "{{timenow}}", "position_size": "{{strategy.position_size}}", "action": "{{strategy.order.action}}", "contracts": "{{strategy.order.contracts}}", "price": "{{strategy.order.price}}", "order_id": "{{strategy.order.id}}", "comment": "{{strategy.order.comment}}", "alert_message": "{{strategy.order.alert_message}}", "market_position": "{{strategy.market_position}}", "market_position_size": "{{strategy.market_position_size}}", "prev_market_position": "{{strategy.prev_market_position}}", "prev_market_position_size": "{{strategy.prev_market_position_size}}"}'
    alert(alertMessage, alert.freq_once_per_bar_close)

if shortCondition
    alertMessage = '{"ticker": "{{ticker}}", "exchange": "{{exchange}}", "interval": "{{interval}}", "time": "{{time}}", "timenow": "{{timenow}}", "position_size": "{{strategy.position_size}}", "action": "{{strategy.order.action}}", "contracts": "{{strategy.order.contracts}}", "price": "{{strategy.order.price}}", "order_id": "{{strategy.order.id}}", "comment": "{{strategy.order.comment}}", "alert_message": "{{strategy.order.alert_message}}", "market_position": "{{strategy.market_position}}", "market_position_size": "{{strategy.market_position_size}}", "prev_market_position": "{{strategy.prev_market_position}}", "prev_market_position_size": "{{strategy.prev_market_position_size}}"}'
    alert(alertMessage, alert.freq_once_per_bar_close)
```

---

## What Each Field Means

| Field | Source | Meaning |
|-------|--------|---------|
| `ticker` | `{{ticker}}` | Symbol (BTCUSD, AAPL, etc.) |
| `exchange` | `{{exchange}}` | Exchange (BINANCE, NYSE, etc.) |
| `interval` | `{{interval}}` | Timeframe (1m, 5m, 1h, 4h, 1d) |
| `time` | `{{time}}` | Bar close time |
| `timenow` | `{{timenow}}` | Current time |
| `position_size` | `{{strategy.position_size}}` | Initial position size |
| `action` | `{{strategy.order.action}}` | Order action: "buy", "sell", "close" |
| `contracts` | `{{strategy.order.contracts}}` | Number of contracts |
| `price` | `{{strategy.order.price}}` | Entry/exit price |
| `order_id` | `{{strategy.order.id}}` | Unique order ID |
| `comment` | `{{strategy.order.comment}}` | Custom comment |
| `alert_message` | `{{strategy.order.alert_message}}` | Alert message |
| `market_position` | `{{strategy.market_position}}` | Current position: "long", "short", "flat" |
| `market_position_size` | `{{strategy.market_position_size}}` | Current position size |
| `prev_market_position` | `{{strategy.prev_market_position}}` | Previous position: "long", "short", "flat" |
| `prev_market_position_size` | `{{strategy.prev_market_position_size}}` | Previous position size |

---

## Benefits of This Approach

✅ **Dynamic**: Values change based on actual strategy state
✅ **Complete**: All position information available
✅ **Flexible**: Works with any strategy
✅ **Trackable**: Can see position transitions
✅ **Accurate**: No hardcoding errors
✅ **Scalable**: Works for multiple strategies

---

## Testing

### Test with cURL

```bash
curl -X POST https://abc123def456.ngrok.io/api/paper-trading/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "BTCUSD",
    "exchange": "BINANCE",
    "interval": "1m",
    "time": "2025-11-09T11:30:00Z",
    "timenow": "2025-11-09T11:30:00Z",
    "position_size": "1",
    "action": "buy",
    "contracts": "1",
    "price": "45000.50",
    "order_id": "12345",
    "comment": "SMA crossover signal",
    "alert_message": "Long entry signal",
    "market_position": "long",
    "market_position_size": "1",
    "prev_market_position": "flat",
    "prev_market_position_size": "0"
  }'
```

---

## Files Updated

- `TRADINGVIEW_WEBHOOK_SETUP.md` - Complete webhook guide with correct format
  - Message format section updated
  - Pine Script examples updated
  - Manual testing examples updated
  - Quick reference updated

---

## Summary

**Old Format**: ❌ Hardcoded, inflexible, incomplete
**New Format**: ✅ Dynamic TradingView placeholders, complete, flexible

**Key Change**: Use `{{placeholder}}` syntax instead of hardcoded values

**Result**: Backend receives complete, accurate strategy state for proper trade execution

---

## Next Steps

1. Update your Pine Script to use the new format
2. Test with BTC 1m chart
3. Verify webhook contains all fields
4. Implement trading engine to parse and execute trades

Good luck! 🚀
