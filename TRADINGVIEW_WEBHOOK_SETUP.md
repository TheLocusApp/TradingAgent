# TradingView Webhook Setup & Testing Guide

## Quick Start - ngrok Tunnel

You've already installed ngrok! Now expose your Flask server:

```bash
ngrok http 5000
```

This will output something like:
```
Forwarding                    https://abc123def456.ngrok.io -> http://localhost:5000
```

**Copy that HTTPS URL** - this is your public webhook endpoint.

---

## TradingView Webhook Format

### 1. Webhook URL Configuration

In TradingView Pine Script alerts, use:
```
https://abc123def456.ngrok.io/api/paper-trading/webhook
```

Replace `abc123def456.ngrok.io` with your actual ngrok URL.

### 2. Message Format (JSON)

Use TradingView Pine Script placeholders (NOT hardcoded values):

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
  "market_position_size": "{{strategy.market_position_size}}",
  "prev_market_position": "{{strategy.prev_market_position}}",
  "timestamp": "{{time}}"
}
```

**Key Fields**:
- `ticker`: Symbol ({{ticker}}) - e.g., "QQQ", "BTC"
- `exchange`: Exchange ({{exchange}})
- `interval`: Timeframe ({{interval}}) - e.g., "2m", "3m", "5m", "1h"
- `timeframe`: Timeframe ({{interval}}) - same as interval, for UI display
- `action`: Trade action ({{strategy.order.action}}) - "buy", "sell", "close"
- `contracts`: Number of contracts ({{strategy.order.contracts}})
- `price`: Entry price ({{strategy.order.price}})
- `market_position`: Current position ({{strategy.market_position}}) - "long", "short", "flat"
- `market_position_size`: Position size ({{strategy.market_position_size}})
- `prev_market_position`: Previous position ({{strategy.prev_market_position}})
- `timestamp`: Bar time ({{time}})

### 3. Pine Script Alert Example

In your Pine Script strategy, use the TradingView placeholders:

```pine
//@version=5
strategy("AGBot Webhook Test", overlay=true)

// Simple entry conditions
longCondition = ta.crossover(ta.sma(close, 9), ta.sma(close, 21))
shortCondition = ta.crossunder(ta.sma(close, 9), ta.sma(close, 21))

if longCondition
    alertMessage = '{"ticker": "{{ticker}}", "exchange": "{{exchange}}", "interval": "{{interval}}", "timeframe": "{{interval}}", "action": "{{strategy.order.action}}", "contracts": "{{strategy.order.contracts}}", "price": "{{strategy.order.price}}", "market_position": "{{strategy.market_position}}", "market_position_size": "{{strategy.market_position_size}}", "prev_market_position": "{{strategy.prev_market_position}}", "timestamp": "{{time}}"}'
    alert(alertMessage, alert.freq_once_per_bar_close)

if shortCondition
    alertMessage = '{"ticker": "{{ticker}}", "exchange": "{{exchange}}", "interval": "{{interval}}", "timeframe": "{{interval}}", "action": "{{strategy.order.action}}", "contracts": "{{strategy.order.contracts}}", "price": "{{strategy.order.price}}", "market_position": "{{strategy.market_position}}", "market_position_size": "{{strategy.market_position_size}}", "prev_market_position": "{{strategy.prev_market_position}}", "timestamp": "{{time}}"}'
    alert(alertMessage, alert.freq_once_per_bar_close)
```

---

## Testing with BTC 1m Timeframe

### Step 1: Start ngrok

```bash
ngrok http 5000
```

Note the HTTPS URL.

### Step 2: Create a Test Pine Script

Create a simple script on BTC 1m chart:

```pine
//@version=5
strategy("Webhook Test", overlay=true)

// Simple entry conditions for testing
longCondition = ta.crossover(ta.sma(close, 9), ta.sma(close, 21))
shortCondition = ta.crossunder(ta.sma(close, 9), ta.sma(close, 21))

if longCondition
    alertMessage = '{"action": "ENTRY", "signal": "BUY", "type": "LONG", "underlying": "BTCUSD", "price": ' + str.tostring(close) + ', "timestamp": "' + str.tostring(timenow) + '", "strategy": "AGBot", "timeframe": "1m"}'
    alert(alertMessage, alert.freq_once_per_bar_close)

if shortCondition
    alertMessage = '{"action": "ENTRY", "signal": "SELL", "type": "SHORT", "underlying": "BTCUSD", "price": ' + str.tostring(close) + ', "timestamp": "' + str.tostring(timenow) + '", "strategy": "AGBot", "timeframe": "1m"}'
    alert(alertMessage, alert.freq_once_per_bar_close)
```

### Step 3: Add Alert

1. Click "Add Alert" on the chart
2. Select your strategy
3. In the "Message" field, paste (use TradingView placeholders):
```json
{"ticker": "{{ticker}}", "exchange": "{{exchange}}", "interval": "{{interval}}", "time": "{{time}}", "timenow": "{{timenow}}", "position_size": "{{strategy.position_size}}", "action": "{{strategy.order.action}}", "contracts": "{{strategy.order.contracts}}", "price": "{{strategy.order.price}}", "order_id": "{{strategy.order.id}}", "comment": "{{strategy.order.comment}}", "alert_message": "{{strategy.order.alert_message}}", "market_position": "{{strategy.market_position}}", "market_position_size": "{{strategy.market_position_size}}", "prev_market_position": "{{strategy.prev_market_position}}", "prev_market_position_size": "{{strategy.prev_market_position_size}}"}
```

4. In "Webhook URL" field, paste your ngrok URL:
```
https://abc123def456.ngrok.io/api/paper-trading/webhook
```

5. Click "Create Alert"

### Step 4: Test the Webhook

The alert will fire when the condition is met. Check:

1. **Paper Trading Page**: `http://localhost:5000/options-paper-trading`
   - Look for the notification in the "Notifications" panel
   - Click the info button (ⓘ) next to "Notifications" to see strategy config

2. **Browser Console**: Open DevTools (F12) → Console
   - Should see: `Received webhook: {...}`

3. **Flask Server Logs**: Check terminal running Flask
   - Should see webhook received message

---

## Manual Testing (Without TradingView)

### Test 1: Send Test Webhook via cURL

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

### Test 2: Send Test Webhook via Python

```python
import requests
import json
from datetime import datetime

webhook_url = "https://abc123def456.ngrok.io/api/paper-trading/webhook"

payload = {
    "ticker": "BTCUSD",
    "exchange": "BINANCE",
    "interval": "1m",
    "time": datetime.utcnow().isoformat() + "Z",
    "timenow": datetime.utcnow().isoformat() + "Z",
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

response = requests.post(webhook_url, json=payload)
print(response.json())
```

### Test 3: Send Test Webhook via JavaScript

```javascript
const webhookUrl = "https://abc123def456.ngrok.io/api/paper-trading/webhook";

const payload = {
    ticker: "BTCUSD",
    exchange: "BINANCE",
    interval: "1m",
    time: new Date().toISOString(),
    timenow: new Date().toISOString(),
    position_size: "1",
    action: "buy",
    contracts: "1",
    price: "45000.50",
    order_id: "12345",
    comment: "SMA crossover signal",
    alert_message: "Long entry signal",
    market_position: "long",
    market_position_size: "1",
    prev_market_position: "flat",
    prev_market_position_size: "0"
};

fetch(webhookUrl, {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
})
.then(response => response.json())
.then(data => console.log("Webhook sent:", data))
.catch(error => console.error("Error:", error));
```

---

## Backend Endpoint Details

### Current Endpoint

**URL**: `/api/paper-trading/webhook`
**Method**: POST
**Content-Type**: application/json

### Current Response

```json
{
  "success": true,
  "message": "Webhook received",
  "timestamp": "2025-11-09T11:30:00Z"
}
```

### Current Behavior

✅ Receives webhook
✅ Displays in Notifications panel
❌ Does NOT execute trades yet (see `WEBHOOK_TRADING_ENGINE_PLAN.md`)

---

## Troubleshooting

### Issue: ngrok URL keeps changing

**Solution**: Use ngrok's reserved domain feature (requires paid plan) or restart ngrok and update TradingView alert.

### Issue: Webhook not received

**Checklist**:
1. Is ngrok running? (`ngrok http 5000`)
2. Is Flask server running? (`python src/web/app.py`)
3. Is the ngrok URL correct in TradingView alert?
4. Check browser console for errors (F12)
5. Check Flask server logs for errors

### Issue: "Connection refused" error

**Solution**: Make sure Flask is running on port 5000:
```bash
python src/web/app.py
```

### Issue: Webhook shows in console but not on page

**Solution**: 
1. Refresh the page
2. Check if polling is working (should poll every 2 seconds)
3. Open browser DevTools → Network tab to see API calls

---

## Advanced: Authentication (Optional)

If you want to add authentication to your webhook:

### Option 1: API Key

Add to webhook URL:
```
https://abc123def456.ngrok.io/api/paper-trading/webhook?key=your_secret_key
```

### Option 2: Bearer Token

Add to TradingView alert message headers (if supported):
```
Authorization: Bearer your_secret_token
```

### Option 3: HMAC Signature

TradingView can sign the webhook. Add to Flask:
```python
import hmac
import hashlib

@app.route('/api/paper-trading/webhook', methods=['POST'])
def receive_webhook():
    signature = request.headers.get('X-Signature')
    payload = request.get_data()
    
    # Verify signature
    expected_sig = hmac.new(
        b'your_secret_key',
        payload,
        hashlib.sha256
    ).hexdigest()
    
    if signature != expected_sig:
        return {'error': 'Invalid signature'}, 401
    
    # Process webhook...
```

---

## Production Checklist

Before going live:

- [ ] ngrok URL is stable (use reserved domain)
- [ ] Flask server has error handling
- [ ] Webhook validation is in place
- [ ] Rate limiting is configured
- [ ] Logging is comprehensive
- [ ] Trading engine is implemented (see `WEBHOOK_TRADING_ENGINE_PLAN.md`)
- [ ] Paper trading tested for 2-4 weeks
- [ ] Risk management rules are enforced
- [ ] Circuit breakers are in place

---

## Next Steps

1. **Test with BTC 1m**: Use the simple SMA crossover script above
2. **Verify Notifications**: Check that webhooks appear in the panel
3. **Review Strategy Config**: Click the info button to see Longs/Shorts settings
4. **Plan Trading Engine**: See `WEBHOOK_TRADING_ENGINE_PLAN.md` for implementation
5. **Implement Trading Logic**: Build the option selection and execution engine

---

## Quick Reference

| Item | Value |
|------|-------|
| **Webhook URL** | `https://[ngrok-url]/api/paper-trading/webhook` |
| **Method** | POST |
| **Content-Type** | application/json |
| **Format** | TradingView placeholders (NOT hardcoded) |
| **Key Fields** | `ticker`, `action`, `contracts`, `price`, `market_position` |
| **Action Values** | "buy", "sell", "close" |
| **Market Position** | "long", "short", "flat" |
| **Paper Trading Page** | `http://localhost:5000/options-paper-trading` |
| **Strategy Config Button** | Click ⓘ next to "Notifications" |
| **Test Timeframe** | BTC 1m (fast signals) |
| **Polling Interval** | 2 seconds |
| **Max Webhooks Stored** | 100 (oldest removed) |

---

## Example Full Workflow

```
1. Start ngrok
   $ ngrok http 5000
   → https://abc123def456.ngrok.io

2. Create Pine Script on BTC 1m chart
   → SMA 9/21 crossover strategy

3. Add Alert with webhook URL
   → https://abc123def456.ngrok.io/api/paper-trading/webhook

4. Open Paper Trading page
   → http://localhost:5000/options-paper-trading

5. Wait for signal on BTC 1m chart
   → Alert fires → Webhook sent → Notification appears

6. Click ⓘ button to see strategy config
   → View Longs/Shorts/Common settings

7. Review notification in panel
   → See signal details

8. Next: Implement trading engine to execute trades
   → See WEBHOOK_TRADING_ENGINE_PLAN.md
```

---

## Support

For issues:
1. Check Flask server logs
2. Check browser console (F12)
3. Verify ngrok is running
4. Test with cURL/Python/JavaScript
5. Check webhook format matches JSON schema

Good luck with testing! 🚀
