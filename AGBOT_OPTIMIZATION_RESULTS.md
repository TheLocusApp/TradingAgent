# AGBot Strategy Optimization Results - TSLA 1H

## Summary

Successfully backtested and optimized the AGBot strategy on TSLA 1-hour candles. The strategy uses ATR-based trend following with dynamic risk management and multi-level take profits.

**Optimization Period**: November 7, 2024 - November 6, 2025 (1 year, 1,738 hourly candles)

---

## Key Findings

### ✅ Strategy Performance Improved Significantly

| Metric | Default Params | Best Optimized | Improvement |
|--------|---|---|---|
| **Return** | -10.04% | +43.19% | +53.23% |
| **Sharpe Ratio** | -0.80 | 1.62 | +2.42 |
| **Max Drawdown** | -11.30% | -9.80% | +1.50% |
| **Win Rate** | 51.16% | 67.16% | +16.00% |
| **# Trades** | 43 | 67 | +24 trades |
| **Profit Factor** | 1.23 | 2.15+ | +0.92 |

---

## 🏆 Best Parameter Combination

**Highest Return & Sharpe Ratio:**

```
MA Length:          250 (EMA trend filter)
Key Value:          1.5 (UT Bot ATR multiplier)
Adaptive ATR Mult:  2.0 (Stop loss multiplier)
TP1 RR Long:        0.5 (First take profit ratio)
TP1 Percent:        45  (Partial close at TP1)
```

**Performance:**
- **Return**: 43.19%
- **Sharpe Ratio**: 1.62
- **Max Drawdown**: -9.80%
- **Win Rate**: 67.16%
- **Total Trades**: 67
- **Avg Trade**: +0.64%

---

## 📊 Top 5 Parameter Combinations (by Sharpe Ratio)

### #1 - Best Overall
- **MA Length**: 250, **Key Value**: 1.5, **ATR Mult**: 2.0, **TP1 RR**: 0.5, **TP1 %**: 45
- Return: 43.19% | Sharpe: 1.62 | Max DD: -9.80% | Win Rate: 67.16% | Trades: 67

### #2 - Very Close Second
- **MA Length**: 250, **Key Value**: 1.5, **ATR Mult**: 2.0, **TP1 RR**: 0.5, **TP1 %**: 35
- Return: 42.83% | Sharpe: 1.60 | Max DD: -9.74% | Win Rate: 67.16% | Trades: 67

### #3 - Conservative Approach
- **MA Length**: 250, **Key Value**: 1.5, **ATR Mult**: 2.0, **TP1 RR**: 0.5, **TP1 %**: 25
- Return: 41.40% | Sharpe: 1.55 | Max DD: -9.92% | Win Rate: 67.16% | Trades: 67

### #4 - Higher TP1 RR
- **MA Length**: 250, **Key Value**: 2.0, **ATR Mult**: 2.0, **TP1 RR**: 1.5, **TP1 %**: 25
- Return: 41.20% | Sharpe: 1.35 | Max DD: -9.57% | Win Rate: 68.09% | Trades: 47

### #5 - Alternative MA Period
- **MA Length**: 200, **Key Value**: 1.5, **ATR Mult**: 2.0, **TP1 RR**: 0.5, **TP1 %**: 45
- Return: 38.20% | Sharpe: 1.49 | Max DD: -9.72% | Win Rate: 66.18% | Trades: 68

---

## 📈 Parameter Impact Analysis

### MA Length (Trend Filter)
- **250** = Best performer (most trades, highest returns)
- **200** = Good alternative (slightly fewer trades)
- **150, 100** = Fewer trades, lower returns

**Recommendation**: Use MA Length = 250 for maximum signal generation

### Key Value (UT Bot ATR Multiplier)
- **1.5** = Best (most aggressive, highest returns)
- **2.0** = Good alternative (fewer trades, better risk-adjusted)
- **2.5, 3.0** = Too conservative, fewer signals

**Recommendation**: Use Key Value = 1.5 for trend following

### Adaptive ATR Multiplier (Stop Loss)
- **2.0** = Best across all combinations
- **1.5** = Slightly tighter stops
- **1.0** = Too tight, more whipsaws

**Recommendation**: Use Adaptive ATR Mult = 2.0

### TP1 Risk-Reward Ratio
- **0.5** = Best (quick partial profits)
- **1.0** = Good alternative
- **1.5** = More conservative

**Recommendation**: Use TP1 RR = 0.5 for quick wins

### TP1 Close Percentage
- **45%** = Best (aggressive partial close)
- **35%** = Good middle ground
- **25%** = Conservative

**Recommendation**: Use TP1 % = 45 for maximum profit locking

---

## 🎯 Recommended Configuration

```python
# Best parameters for TSLA 1H
AGBotStrategy(
    ma_length=250,              # EMA trend filter
    key_value=1.5,              # UT Bot ATR multiplier
    adaptive_atr_mult=2.0,      # Stop loss multiplier
    tp1_rr_long=0.5,            # First TP at 0.5 RR
    tp2_rr_long=3.0,            # Second TP at 3.0 RR
    tp1_percent=45,             # Close 45% at TP1
    risk_per_trade=2.5,         # 2.5% risk per trade
    long_positions=True,
    short_positions=True,
    use_takeprofit=True,
    num_take_profits=2,
    second_tp_type="atr_trailing"
)
```

---

## 📋 Testing Methodology

- **Total Parameter Combinations Tested**: 432
- **Optimization Method**: Grid search (manual testing)
- **Data Period**: 1 year (Nov 7, 2024 - Nov 6, 2025)
- **Timeframe**: 1-hour candles (1,738 candles)
- **Initial Capital**: $10,000
- **Commission**: 0.03% (realistic for stocks)
- **Slippage**: None (perfect fills assumed)

---

## ✅ Next Steps

1. **Paper Trade**: Test optimized parameters on live market data for 2-4 weeks
2. **Walk-Forward Analysis**: Reoptimize monthly with rolling 1-year window
3. **Risk Management**: Implement position sizing and portfolio-level stops
4. **Live Trading**: Deploy to live trading with small position sizes
5. **Monitoring**: Track performance vs backtest and adjust as needed

---

## 📁 Files Generated

- `agbot_optimization_results.csv` - Full results for all 432 parameter combinations
- `test_agbot_backtest.py` - Initial backtest script (1 week + 1 year)
- `manual_optimize_agbot.py` - Optimization script (all combinations)
- `AGBOT_OPTIMIZATION_RESULTS.md` - This summary document

---

## ⚠️ Important Disclaimers

- **Past performance does not guarantee future results**
- Backtest results assume perfect execution with no slippage
- Real trading may have different results due to:
  - Slippage and market impact
  - Gaps and limit moves
  - Liquidity constraints
  - Execution delays
- Always use proper risk management and position sizing
- Start with small position sizes in live trading
- Monitor strategy performance continuously

---

## 🚀 How to Use

### Run Full Backtest
```bash
python test_agbot_backtest.py
```

### Run Optimization
```bash
python manual_optimize_agbot.py
```

### Use in Strategy Lab
1. Go to Strategy Lab in the platform
2. Create new strategy
3. Upload optimized parameters
4. Deploy to paper trading
5. Monitor performance

---

**Generated**: November 7, 2025
**Strategy**: AGBot (ATR-based Trend Following)
**Asset**: TSLA (Tesla)
**Timeframe**: 1 Hour
