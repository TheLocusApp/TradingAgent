# Paper Trading Page - Fixed & Ready

## ✅ Issues Resolved

### 1. **404 Not Found Error - FIXED**
- **Problem**: Route `/options-paper-trading` was not being recognized
- **Solution**: Server needed restart to load new routes
- **Status**: ✅ Page now accessible at `http://localhost:5000/options-paper-trading`

### 2. **TastyTrade Integration - ADDED**
- **Problem**: Backend needed TastyTrade API for option chain data
- **Solution**: Added TastyTrade provider initialization and API endpoint
- **Status**: ✅ Ready to use (requires credentials in `.env`)

---

## 🚀 How to Access

```
http://localhost:5000/options-paper-trading
```

Server is running on:
- Local: `http://127.0.0.1:5000`
- Network: `http://192.168.1.109:5000`

---

## 📡 API Endpoints Available

### 1. **Get Paper Trading State**
```
GET /api/paper-trading/state
```
Returns account balance, trades, positions, webhooks.

### 2. **Receive Webhook from TradingView**
```
POST /api/paper-trading/webhook
Content-Type: application/json

{
  "signal": "BUY",
  "type": "LONG",
  "price": 500.25
}
```

### 3. **Add Trade Manually**
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

### 4. **Reset Account**
```
POST /api/paper-trading/reset
```

### 5. **Get Option Chain (TastyTrade)** ⭐ NEW
```
GET /api/paper-trading/option-chain?symbol=QQQ&dte=5
```
Returns option chain data from TastyTrade API.

---

## 🔑 TastyTrade Setup

### Required Environment Variables

Add to your `.env` file:

```bash
TASTYTRADE_OAUTH_TOKEN=your_oauth_token_here
TASTYTRADE_ACCOUNT_NUMBER=your_account_number_here
```

### How to Get TastyTrade Credentials

1. **Login to TastyTrade**: https://trade.tastytrade.com
2. **Generate OAuth Token**: 
   - Go to Settings → API
   - Create new OAuth token
   - Copy the token
3. **Get Account Number**:
   - Go to Account → Account Details
   - Copy your account number

### Provider Status

The server will show one of these on startup:

**With Credentials:**
```
✅ TastyTrade options provider initialized
```

**Without Credentials:**
```
⚠️ TastyTrade provider not available: ...
   Add TASTYTRADE_OAUTH_TOKEN and TASTYTRADE_ACCOUNT_NUMBER to .env
```

---

## 🧪 Testing the Page

### Test 1: Load the Page

```bash
# Open in browser
http://localhost:5000/options-paper-trading
```

**Expected**: Page loads with:
- Account summary showing $10,000
- Empty trade list
- QQQ chart widget
- Webhook panel waiting for connections

### Test 2: Add a Manual Trade

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

**Expected**: 
- Trade appears in list
- Account balance updates to $10,225.50
- Performance chart shows increase

### Test 3: Send a Webhook

```bash
curl -X POST http://localhost:5000/api/paper-trading/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "signal": "BUY",
    "type": "LONG",
    "option": "Call",
    "price": 500.25,
    "timestamp": "2025-11-09T11:30:00"
  }'
```

**Expected**:
- Webhook appears in notifications panel
- Status indicator turns green
- Timestamp shows current time

### Test 4: Get Option Chain (TastyTrade)

```bash
curl http://localhost:5000/api/paper-trading/option-chain?symbol=QQQ&dte=5
```

**Expected** (with credentials):
```json
{
  "symbol": "QQQ",
  "underlying_price": 500.25,
  "dte": 5,
  "calls": [],
  "puts": []
}
```

**Expected** (without credentials):
```json
{
  "error": "TastyTrade provider not initialized",
  "message": "Add TASTYTRADE_OAUTH_TOKEN and TASTYTRADE_ACCOUNT_NUMBER to .env"
}
```

---

## 📊 Page Features

### Account Summary (Top)
- **Account Balance**: $10,000 starting
- **Total P&L**: Running profit/loss
- **Win Rate**: % wins with W/L count
- **Open Positions**: Number of active contracts

### Performance Chart (Left)
- Real-time equity curve
- Updates with each trade
- Shows account growth/decline

### QQQ Chart (Right)
- TradingView 1H chart
- Purple theme (matches strategy)
- Live price updates

### Trade List (Bottom Left)
Columns:
- # (trade number)
- Type (Long/Short)
- Date/Time
- Signal (TP1, TP2, SL)
- Option (Call/Put)
- Strike
- Expiry (DTE)
- Price
- Contracts
- Net P&L
- Cumulative P&L

### Webhook Panel (Bottom Right)
- Connection status
- Live webhook messages
- JSON payload display
- Auto-scrolls to latest

### Strategy Config (Bottom)
- 3 contracts per trade
- 5 DTE expiry
- ATM/1 ITM strikes
- Delta 0.50-0.60
- TP1: +50% (35% close)
- TP2: +100% (65% close)
- Stop: Swing high/low
- Hold: 13 hours max

---

## 🔧 Troubleshooting

### Page Shows 404

**Problem**: Server not running or route not loaded

**Solution**:
```bash
# Kill existing server
taskkill /F /IM python.exe

# Restart server
python src/web/app.py

# Wait 5 seconds, then try:
http://localhost:5000/options-paper-trading
```

### TastyTrade Not Working

**Problem**: Missing credentials

**Solution**:
1. Check `.env` file exists in project root
2. Add these lines:
   ```
   TASTYTRADE_OAUTH_TOKEN=your_token
   TASTYTRADE_ACCOUNT_NUMBER=your_account
   ```
3. Restart server

### Webhooks Not Showing

**Problem**: Polling not working

**Solution**:
1. Open browser console (F12)
2. Check for errors
3. Verify `/api/paper-trading/state` returns data
4. Refresh page (Ctrl+F5)

### Chart Not Loading

**Problem**: TradingView widget blocked

**Solution**:
1. Check internet connection
2. Disable ad blockers
3. Try different browser
4. Check browser console for CORS errors

---

## 📝 Lint Warnings (Can Ignore)

You may see JavaScript lint warnings about missing semicolons in the TradingView widget code. These are **false positives** - the code is a JSON configuration object, not JavaScript statements. The widget will work perfectly.

---

## ✅ Summary

**Status**: ✅ Paper trading page is LIVE and READY

**What Works**:
- ✅ Page accessible at `/options-paper-trading`
- ✅ Account tracking ($10,000 starting)
- ✅ Trade list with options details
- ✅ QQQ live chart
- ✅ Webhook reception
- ✅ Performance chart
- ✅ TastyTrade integration (with credentials)
- ✅ API endpoints for all operations

**Next Steps**:
1. Add TastyTrade credentials to `.env`
2. Test manual trade entry
3. Configure TradingView webhooks
4. Run paper trading for 2-4 weeks
5. Go live when confident

Good luck with your paper trading! 🚀
