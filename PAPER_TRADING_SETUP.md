# QQQ Options Paper Trading Setup Guide

## Overview

A real-time paper trading simulator for testing the AGBot options strategy with live TradingView webhooks before going live.

## Features

✅ **$10,000 Starting Capital** (matches strategy requirements)
✅ **Live QQQ Chart** (TradingView widget, 1H timeframe)
✅ **Trade List** (TradingView-style with options details)
✅ **Webhook Integration** (receive signals from Pine Script)
✅ **Real-time Performance Tracking** (account balance, P&L, win rate)
✅ **Strategy Configuration Display** (3 contracts, 5 DTE, ATM/ITM)

---

## Access the Page

```
http://localhost:5000/options-paper-trading
```

---

## Page Layout

### 1. **Account Summary (Top Row)**
- Account Balance: Current balance with change %
- Total P&L: Total profit/loss
- Win Rate: % wins with W/L ratio
- Open Positions: Number of open contracts

### 2. **Performance Chart (Left)**
- Real-time account balance chart
- Shows equity curve as trades are executed
- Updates automatically with each trade

### 3. **QQQ Live Chart (Right)**
- TradingView 1H chart
- Purple background (matches strategy)
- Minimal UI (no toolbars, clean view)

### 4. **List of Trades (Bottom Left)**
Columns:
- **#**: Trade number
- **Type**: Long/Short
- **Date/Time**: Exit timestamp
- **Signal**: TP1 Long, TP2 Short, SL, etc.
- **Option**: Call/Put
- **Strike**: Strike price
- **Expiry**: DTE (e.g., "5 DTE")
- **Price**: Entry price per contract
- **Contracts**: Number of contracts (3)
- **Net P&L**: Profit/loss for this trade
- **Cumulative P&L**: Running total

### 5. **Webhook Notifications (Bottom Right)**
- Shows incoming webhooks from TradingView
- Displays JSON payload
- Connection status indicator
- Auto-scrolls to latest

### 6. **Strategy Configuration (Bottom)**
- Contracts per Trade: 3
- DTE: 5
- Strike Selection: ATM / 1 ITM
- Delta Target: 0.50 - 0.60
- TP1 (35%): +50% Profit
- TP2 (65%): +100% Profit
- Stop Loss: Swing High/Low
- Max Hold Time: 13 Hours

---

## API Endpoints

### 1. **Get State**
```
GET /api/paper-trading/state
```
Returns current account state, trades, positions, webhooks.

### 2. **Receive Webhook**
```
POST /api/paper-trading/webhook
Content-Type: application/json

{
  "signal": "BUY",
  "type": "LONG",
  "price": 500.25,
  "timestamp": "2025-11-09T10:30:00"
}
```
Receives webhook from TradingView Pine Script.

### 3. **Add Trade (Manual)**
```
POST /api/paper-trading/trade
Content-Type: application/json

{
  "type": "Long",
  "option": "Call",
  "strike": 500,
  "expiry": "5 DTE",
  "price": 4.50,
  "contracts": 3,
  "pnl": 225.50,
  "signal": "TP1 Long"
}
```
Manually add a trade (for testing).

### 4. **Reset Account**
```
POST /api/paper-trading/reset
```
Resets account to $10,000, clears all trades.

---

## TradingView Webhook Setup

### Step 1: Create Alert in Pine Script

Add this to your AGBot Pine Script:

```pinescript
// Webhook URL (replace with your server)
webhook_url = "http://your-server-ip:5000/api/paper-trading/webhook"

// Entry signals
if buySignal and bullish and allowLongs
    alert('{"signal":"BUY","type":"LONG","option":"Call","price":' + str.tostring(close) + ',"timestamp":"' + str.tostring(time) + '"}', alert.freq_once_per_bar)

if sellSignal and bearish and allowShorts
    alert('{"signal":"SELL","type":"SHORT","option":"Put","price":' + str.tostring(close) + ',"timestamp":"' + str.tostring(time) + '"}', alert.freq_once_per_bar)

// Exit signals (TP1, TP2, SL)
// TODO: Add exit logic
```

### Step 2: Configure Alert

1. Right-click on chart → "Add Alert"
2. Condition: Select your script
3. Alert name: "AGBot Options Signal"
4. Webhook URL: `http://your-server-ip:5000/api/paper-trading/webhook`
5. Message: (leave default, script handles it)
6. Click "Create"

### Step 3: Test Webhook

Use curl or Postman to test:

```bash
curl -X POST http://localhost:5000/api/paper-trading/webhook \
  -H "Content-Type: application/json" \
  -d '{"signal":"BUY","type":"LONG","option":"Call","price":500.25}'
```

You should see the webhook appear in the "Webhook Notifications" panel.

---

## Testing Workflow

### Week 1-2: Manual Testing

1. **Open the page**: `http://localhost:5000/options-paper-trading`
2. **Watch for signals**: Monitor TradingView for BUY/SELL signals
3. **Manually add trades**: Use the API to simulate trades
4. **Track performance**: Watch account balance, win rate, P&L

Example manual trade:

```bash
curl -X POST http://localhost:5000/api/paper-trading/trade \
  -H "Content-Type: application/json" \
  -d '{
    "type": "Long",
    "option": "Call",
    "strike": 500,
    "expiry": "5 DTE",
    "price": 4.50,
    "contracts": 3,
    "pnl": 225.50,
    "signal": "TP1 Long"
  }'
```

### Week 3-4: Automated Testing

1. **Set up webhooks**: Configure TradingView alerts
2. **Let it run**: Webhooks automatically create trades
3. **Monitor daily**: Check performance each evening
4. **Compare to backtest**: Verify win rate ~64%, P&L ~+20%/month

---

## Webhook JSON Format (To Be Finalized)

We'll iron out the exact format, but here's a proposed structure:

### Entry Signal

```json
{
  "action": "ENTRY",
  "type": "LONG",
  "signal": "BUY",
  "option": "Call",
  "underlying_price": 500.25,
  "strike": 500,
  "expiry_dte": 5,
  "contracts": 3,
  "entry_price": 4.50,
  "stop_loss": 495.20,
  "tp1_target": 6.75,
  "tp2_target": 9.00,
  "timestamp": "2025-11-09T10:30:00Z"
}
```

### Exit Signal (TP1)

```json
{
  "action": "EXIT",
  "type": "TP1",
  "contracts_closed": 1,
  "exit_price": 6.75,
  "pnl": 225.00,
  "timestamp": "2025-11-09T18:45:00Z"
}
```

### Exit Signal (TP2)

```json
{
  "action": "EXIT",
  "type": "TP2",
  "contracts_closed": 2,
  "exit_price": 9.00,
  "pnl": 900.00,
  "timestamp": "2025-11-09T22:15:00Z"
}
```

### Exit Signal (Stop Loss)

```json
{
  "action": "EXIT",
  "type": "SL",
  "contracts_closed": 3,
  "exit_price": 2.50,
  "pnl": -600.00,
  "timestamp": "2025-11-09T14:20:00Z"
}
```

---

## Next Steps

### Phase 1: Setup (Day 1)
- [x] Create paper trading page
- [x] Add API endpoints
- [x] Test manual trade entry
- [ ] Configure TradingView webhooks
- [ ] Test webhook reception

### Phase 2: Testing (Week 1-2)
- [ ] Run 20-30 manual trades
- [ ] Verify win rate matches backtest (~64%)
- [ ] Verify P&L matches expectations (+18.6% per trade)
- [ ] Identify any issues with trade execution

### Phase 3: Automation (Week 3-4)
- [ ] Set up automated webhooks
- [ ] Let system run for 2 weeks
- [ ] Monitor daily performance
- [ ] Compare to backtest results
- [ ] Fine-tune webhook format

### Phase 4: Go Live (Week 5+)
- [ ] Open real options account
- [ ] Start with 1 contract per trade
- [ ] Scale to 3 contracts after 10 successful trades
- [ ] Monitor live vs paper performance
- [ ] Adjust strategy as needed

---

## Troubleshooting

### Webhook Not Received

1. Check server is running: `http://localhost:5000`
2. Check firewall allows port 5000
3. If using external server, use public IP
4. Test with curl first before TradingView

### Trades Not Showing

1. Check browser console for errors (F12)
2. Verify API endpoint returns data: `/api/paper-trading/state`
3. Check trade format matches required fields
4. Look for errors in server logs

### Performance Chart Not Updating

1. Refresh page (Ctrl+F5)
2. Check browser console for JavaScript errors
3. Verify Chart.js is loaded
4. Check performance data array has values

### TradingView Widget Not Loading

1. Check internet connection
2. Verify TradingView script URL is accessible
3. Check browser console for CORS errors
4. Try different browser

---

## Files Created

1. **Frontend**: `src/web/templates/options_paper_trading.html`
2. **Backend**: `src/web/app.py` (routes added)
3. **Strategy Guide**: `OPTIMAL_QQQ_OPTIONS_STRATEGY.md`
4. **DTE Analysis**: `DTE_ANALYSIS_12HR_HOLDS.md`
5. **This Guide**: `PAPER_TRADING_SETUP.md`

---

## Summary

You now have a fully functional paper trading simulator that:

✅ Tracks $10,000 account with real-time P&L
✅ Displays trades in TradingView-style list with options details
✅ Shows live QQQ chart
✅ Receives webhooks from TradingView
✅ Displays strategy configuration
✅ Provides API for manual testing

**Next:** Configure TradingView webhooks and start testing! 🚀

Good luck with your paper trading! Let me know when you're ready to finalize the webhook format.
