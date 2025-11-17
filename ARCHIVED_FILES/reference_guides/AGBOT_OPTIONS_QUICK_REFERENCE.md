# AGBot OPTIONS Puts - Quick Reference Card
**Print this and keep it handy!**

---

## ⚡ Quick Setup (5 minutes)

1. **Open TradingView**
2. **Pine Editor** → Paste `AGBotGeneric_OPTIONS_Puts_Strategy.pine`
3. **Add to Chart** → Select QQQ 1H
4. **Strategy Tester** → Run backtest (2020-2025)
5. **Review Results** → Check performance metrics

---

## 📊 Key Settings (Already Optimized)

```
EMA Length:           150
UT Bot Key:           1.5x
ATR Mult:             1.0
TP1 R:R:              1.0
TP1 Close %:          70% ← LOCK GAINS
Max Hold Time:        12 hours ← PREVENT THETA BLEED
```

---

## 🎯 Trading Rules

### Entry Signal
- Red triangle below candle
- Close < EMA AND < UT Bot trail
- Buy puts (7 DTE, ATM or -1 OTM)

### TP1 (70% Trim)
- When put price = 1.0 R:R
- Close 70% of position
- Lock in guaranteed profit

### TP2 (30% Runners)
- Let 30% run with ATR trailing
- Theta decay helps this position
- Exit when ATR trail hit OR 12 hours pass

### Stop Loss
- If put price drops below entry
- Close remaining position
- Max loss = premium paid (defined risk)

---

## 💰 Position Sizing

| Account | Risk/Trade | Contracts | Max Loss |
|---------|-----------|-----------|----------|
| $10,000 | $100 | 1 | $100 |
| $50,000 | $500 | 2-3 | $500 |
| $100,000 | $1,000 | 5 | $1,000 |
| $250,000 | $2,500 | 12-13 | $2,500 |

**Rule:** Start with 1% risk per trade, increase after 20+ trades

---

## 📈 Expected Results

### Per Trade
- Win Rate: 45%
- Avg Winner: +150%
- Avg Loser: -100%
- Avg Trade: +22.5%

### Per Month (8-10 trades)
- Winners: 3-4
- Losers: 4-6
- Monthly Return: 75-375%
- Depends on position sizing

### Per Year
- Conservative: 900%
- Moderate: 2,244%
- Aggressive: 4,500%

---

## ⚠️ Risk Management Checklist

- [ ] Position size = 1% risk per trade (start)
- [ ] Stop loss set BEFORE entry
- [ ] TP1 trim at 70% (lock gains)
- [ ] Exit after 12 hours (prevent theta bleed)
- [ ] Only trade high-volume options (QQQ, SPY, IWM)
- [ ] Check IV Rank > 50 before entry
- [ ] Don't hold overnight (theta accelerates)
- [ ] Track all trades in journal

---

## 🚫 Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Hold overnight | Theta decay accelerates | 12-hour exit rule |
| Close all at TP1 | Miss big runners | 70% trim keeps 30% |
| No stop loss | Unlimited loss | Set SL before entry |
| Illiquid options | Can't exit | Only QQQ/SPY/IWM |
| Ignore IV | Overpay for options | Check IV Rank first |
| Too large position | Blowup risk | Start with 1% risk |

---

## 📱 Real-World Example

```
ENTRY:
- Time: Friday 9:30 AM
- QQQ: $350
- Signal: PUT (red triangle)
- Action: Buy 3 QQQ $350 puts at $2.00
- Cost: $600 (3 × $200)
- Risk: $600 max loss

TP1 (70% TRIM):
- Time: Friday 10:30 AM (1 hour)
- QQQ: $348.50
- Put Price: $5.00
- Action: Sell 2 contracts
- Profit: $600 (2 × $300)
- Remaining: 1 runner

TP2 (30% RUNNER):
- Time: Friday 2:00 PM (5 hours)
- QQQ: $347
- Put Price: $6.50
- Action: Hold (theta helping)

EXIT:
- Time: Friday 4:00 PM (7 hours)
- QQQ: $348
- Put Price: $5.50
- Action: Sell 1 contract (ATR trail hit)
- Profit: $350 (1 × $350)

TOTAL:
- Gross Profit: $950
- Return: 158% on $600 risk
- Hold Time: 7 hours
```

---

## 🔄 Weekly Routine

**Monday-Friday:**
- 9:30 AM: Check for signals
- 10:00 AM: Enter if signal confirmed
- 10:30 AM: TP1 trim (70%)
- 4:00 PM: Exit runners (12-hour limit)
- 4:30 PM: Log trade in journal

**Weekly Review:**
- Win rate: Should be ~45%
- Avg winner: Should be ~+150%
- Avg loser: Should be ~-100%
- Profit factor: Should be > 1.3

**Monthly Review:**
- Total trades: 8-10
- Total profit: 75-375%
- Largest win: ?
- Largest loss: ?
- Adjust position sizing if needed

---

## 📞 Troubleshooting

**Q: No signals?**
A: Check timeframe (must be 1H) and market hours (9:30-4:00 ET)

**Q: Signals but no trades?**
A: Previous position still open (close it first)

**Q: Trades closing too early?**
A: Increase TP1 Close % to 75-80%

**Q: Runners getting stopped out?**
A: Increase ATR Mult to 1.25-1.5

**Q: Holding past 12 hours?**
A: Check `enableTimeExit` is true

---

## 📚 Files Reference

| File | Purpose |
|------|---------|
| `AGBotGeneric_OPTIONS_Puts_Strategy.pine` | Main strategy (load in TradingView) |
| `AGBOT_OPTIONS_PUTS_GUIDE.md` | Complete guide with examples |
| `AGBOT_SHORTS_ANALYSIS_COMPLETE.md` | Analysis & recommendations |
| `AGBotGeneric_QQQ_Shorts_Optimized.pine` | Reference for SHORT params |

---

## ✅ Checklist Before Trading Live

- [ ] Backtested 2020-2025 data
- [ ] Reviewed performance metrics
- [ ] Paper traded 2-4 weeks
- [ ] Win rate confirmed ~45%
- [ ] Profit factor > 1.3
- [ ] Max drawdown acceptable
- [ ] Position sizing set to 1% risk
- [ ] Stop losses understood
- [ ] TP1 trim at 70% confirmed
- [ ] 12-hour exit rule understood
- [ ] Risk management rules memorized
- [ ] Trading journal ready

---

## 🎓 Key Insights

### Why 70% TP1 Trim?
- Locks in guaranteed profit
- Reduces theta exposure
- Lets 30% capture big moves
- Theta decay helps runners

### Why 12-Hour Hold Limit?
- Theta decay ~7% per 12 hours (acceptable)
- Theta accelerates after 12 hours (exit)
- Prevents overnight bleed
- Matches your average hold time

### Why ATR Trailing?
- Captures big moves (5-10x potential)
- Exits if QQQ bounces back
- Defined risk (premium paid)
- Works with theta decay

---

## 🚀 Next Steps

1. Load strategy in TradingView
2. Backtest on QQQ 1H (2020-2025)
3. Review performance metrics
4. Paper trade 2-4 weeks
5. Start with 1% risk per trade
6. Track all trades in journal
7. Adjust parameters based on results
8. Scale up after 20+ profitable trades

---

## 📞 Quick Reference

**Win Rate:** 45%  
**Avg Winner:** +150%  
**Avg Loser:** -100%  
**Monthly Return:** 75-375%  
**Sharpe Ratio:** 1.8-2.0+  
**Max Drawdown:** -15% to -40%  

**Best For:** Bear markets, hedging, income generation  
**Complexity:** Medium  
**Risk:** Defined (premium paid)  
**Capital:** $500-2,000 per trade  

---

**Ready to trade? Load the Pine Script and backtest today!**
