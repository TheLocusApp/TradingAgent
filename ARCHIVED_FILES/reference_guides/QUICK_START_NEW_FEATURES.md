# 🚀 Quick Start: New Features

## Test Everything in 5 Minutes

---

## 1️⃣ Start the Server

```bash
python src/web/app.py
```

Wait for: `✅ Advanced Risk Manager initialized (Agentic Mode)`

---

## 2️⃣ Test Regime Indicator (Live Trading Page)

1. Open: http://localhost:5000
2. Look at **top-right corner**
3. Should see: 📈 Trending Up • 85% • VIX: 18
4. **Click the badge** → Should show full regime details
5. Wait 30 seconds → Should auto-update

**Expected**: Badge changes color based on regime (green=trending up, yellow=ranging, red=trending down)

---

## 3️⃣ Test Momentum Screener (Analyst Page)

1. Open: http://localhost:5000/analyst
2. Scroll down to **"🔥 Momentum Screener"** section
3. Wait 2 seconds → Table should populate with top 20 assets
4. **Filter by "Crypto"** → Should show only BTC, ETH, SOL
5. **Check "Above SMA200 Only"** → Should filter results
6. **Click "Analyze"** on any asset → Should auto-fill ticker and run analysis

**Expected**: Full table with rankings, scores, prices, and analyze buttons

---

## 4️⃣ Test Risk Guidance API

```bash
curl -X POST http://localhost:5000/api/risk/guidance \
  -H "Content-Type: application/json" \
  -d "{\"balance\": 100000, \"entry_price\": 50000, \"direction\": \"LONG\", \"confidence\": 85, \"win_rate\": 0.60, \"atr\": 1000}"
```

**Expected Response**:
```json
{
  "suggested_stop_loss": 48000,
  "suggested_position_size_dollars": 12500,
  "reasoning": "High confidence (85%) - increased position size",
  "override_allowed": true
}
```

---

## 5️⃣ Test All Backend Systems

```bash
python test_hedge_fund_features.py
```

**Expected**: All 5 tests pass
- ✅ Portfolio Manager
- ✅ RBI Deployment
- ✅ Regime Detector
- ✅ Risk Manager
- ✅ Momentum Rotator

---

## 🎯 What You Should See

### Live Trading Page
- **Top-right**: Regime badge with emoji, label, confidence, VIX
- **Clickable**: Shows full regime analysis
- **Auto-updates**: Every 30 seconds

### Analyst Page
- **Momentum Screener**: Full table below ticker input
- **Filters**: Asset class, timeframe, above SMA200
- **Analyze Button**: Click to auto-fill ticker
- **Auto-loads**: 2 seconds after page load

### API Endpoints
- `GET /api/regime/current` → Current market regime
- `GET /api/momentum/rankings` → Top 20 momentum assets
- `POST /api/risk/guidance` → Risk guidance for trade
- `GET /api/risk/override-stats` → Override success rate

---

## 🐛 Troubleshooting

### Regime Badge Not Showing
- Check browser console for errors
- Verify `/api/regime/current` returns data
- Wait 2 seconds for initial load

### Momentum Screener Empty
- Check browser console for errors
- Verify `/api/momentum/rankings` returns data
- May take 15-20 seconds to rank all assets

### Risk Guidance Error
- Verify regime detector is working
- Check if yfinance can fetch SPY data
- Try with different entry_price values

---

## 📊 Performance Notes

- **Regime Detection**: ~10-15 seconds (fetches SPY data)
- **Momentum Rankings**: ~15-20 seconds (ranks 15+ assets)
- **Risk Guidance**: <1 second (calculations only)

All endpoints cache results appropriately.

---

## ✅ Success Criteria

You've successfully tested everything if:

1. ✅ Regime badge appears and updates
2. ✅ Momentum screener loads with data
3. ✅ Filters work correctly
4. ✅ Analyze button auto-fills ticker
5. ✅ API endpoints return valid JSON
6. ✅ Test suite passes all 5 tests

---

## 🎉 You're Ready!

All features are working. Now you can:
- See market regime at a glance
- Screen for top momentum plays
- Get intelligent risk guidance
- Let agents make contextual decisions

**Next**: Integrate risk guidance into agent prompts for full agentic decision-making.
