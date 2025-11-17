# 🎯 Prompt Injection Examples: Before & After

## Question 3 & 5: Is regime/risk info being passed to agents?

**Answer**: Currently **NO** - but here's how it SHOULD work:

---

## Current State (BEFORE)

### System Prompt
```
You are an expert trading AI with deep knowledge of technical analysis, risk management, and market dynamics.

Your role is to analyze real-time market data for BTC-USD and make trading decisions.

OBJECTIVE: Maximize risk-adjusted returns while managing position sizing and drawdown.

TRADING RULES:
- You can BUY to open new positions or add to existing positions (scale in)
- You can SELL to close positions or reduce position size (scale out)
- Use HOLD when conditions don't warrant action or when waiting for better entry/exit
- Consider position sizing - you don't need to use all capital at once

Provide your response in this format:
SIGNAL: [BUY/SELL/HOLD]
CONFIDENCE: [0-100]%
REASONING: [your analysis]
```

### User Prompt
```
It has been 15 minutes since you started trading. The current time is 2025-11-06 10:00:00.

CURRENT MARKET STATE
current_price = 50000.00, current_ema20 = 49800.00, current_macd = 120.50, current_rsi (7 period) = 65.20

Current live positions & performance:
- Balance: $100,000
- Free Capital: $100,000
- No open positions
```

**Problem**: Agent has NO context about:
- Market regime (trending/ranging/high vol)
- VIX level
- Risk guidance (suggested stop loss, position size)
- Strategy recommendations for current regime

---

## Proposed State (AFTER)

### Enhanced System Prompt
```
You are an expert trading AI with deep knowledge of technical analysis, risk management, and market dynamics.

Your role is to analyze real-time market data for BTC-USD and make trading decisions.

OBJECTIVE: Maximize risk-adjusted returns while managing position sizing and drawdown.

TRADING RULES:
- You can BUY to open new positions or add to existing positions (scale in)
- You can SELL to close positions or reduce position size (scale out)
- Use HOLD when conditions don't warrant action or when waiting for better entry/exit
- Consider position sizing - you don't need to use all capital at once

Provide your response in this format:
SIGNAL: [BUY/SELL/HOLD]
CONFIDENCE: [0-100]%
REASONING: [your analysis]
```

### Enhanced User Prompt
```
It has been 15 minutes since you started trading. The current time is 2025-11-06 10:00:00.

=== MARKET REGIME ANALYSIS ===
Current Regime: 📈 Trending Up (Confidence: 85%)
Trend Direction: UPWARD
Technical Indicators:
  - ADX: 32.5 (Strong trend)
  - VIX: 18.2 (Normal volatility)
  - Volatility: 2.1%

Strategy Recommendations:
  - Preferred: Momentum, Trend Following
  - Position Size Adjustment: 120% of normal (increase size in strong trends)
  - Stop Loss Adjustment: 110% of normal (wider stops for trending markets)
  - Avoid: Mean Reversion, Range Trading

=== RISK MANAGEMENT GUIDANCE ===
The Risk Manager has analyzed current conditions and provides the following GUIDANCE:

Suggested Stop Loss: $48,000 (4% below entry)
  Reasoning: Strong trend detected - wider stop to avoid premature exit

Suggested Position Size: $15,000 (15% of capital)
  Reasoning: High confidence (85%); Strong win rate (60%); Normal volatility

Risk Metrics:
  - Risk per trade: $2,000 (2% of capital)
  - Risk/Reward Ratio: 1:2.5
  - Win rate required: 40% (to break even)

IMPORTANT: These are SUGGESTIONS, not commands. You may override if you have strong conviction based on:
  - News context or upcoming events
  - Technical setup that contradicts guidance
  - Market microstructure signals
  - Your own risk assessment

If you choose to override, please explain your reasoning in your response.

=== CURRENT MARKET STATE ===
current_price = 50000.00, current_ema20 = 49800.00, current_macd = 120.50, current_rsi (7 period) = 65.20

Current live positions & performance:
- Balance: $100,000
- Free Capital: $100,000
- No open positions
```

---

## Key Differences

| Aspect | BEFORE | AFTER |
|--------|--------|-------|
| **Market Context** | None | Full regime analysis (trending/ranging/high vol) |
| **VIX Awareness** | None | VIX: 18.2 (Normal volatility) |
| **Strategy Guidance** | None | Preferred: Momentum, Trend Following |
| **Position Sizing** | Agent guesses | Suggested: $15,000 (15% of capital) with reasoning |
| **Stop Loss** | Agent guesses | Suggested: $48,000 (4% below entry) with reasoning |
| **Risk Metrics** | None | Risk/Reward: 1:2.5, Required win rate: 40% |
| **Override Flexibility** | N/A | Agent can override with reasoning |

---

## Example Agent Response (AFTER)

### Scenario 1: Agent Follows Guidance
```
SIGNAL: BUY
CONFIDENCE: 85%
REASONING: Strong uptrend confirmed by ADX 32.5 and price above EMA20. RSI at 65 shows momentum without being overbought. Following Risk Manager guidance: entering with $15,000 position (15% of capital) and stop loss at $48,000. Regime analysis supports momentum strategy. Risk/Reward of 1:2.5 is favorable.
```

### Scenario 2: Agent Overrides Guidance
```
SIGNAL: BUY
CONFIDENCE: 90%
REASONING: Strong uptrend confirmed, but I'm OVERRIDING Risk Manager's suggested position size. Increasing to $20,000 (20% of capital) because: (1) Fed announcement tomorrow likely to reduce volatility, (2) Strong technical support at $49,500 allows tighter stop at $49,000 instead of suggested $48,000, (3) This improves R:R to 1:3.0. Keeping wider stop would risk unnecessary exit on normal pullback.
```

**System then records**: Override successful/failed for learning

---

## Implementation Status

### ✅ Already Built:
- `regime_detector.py` - Detects market regime
- `advanced_risk_manager.py` - Calculates risk guidance
- API endpoints (`/api/regime/current`, `/api/risk/guidance`)
- Frontend regime badge

### ⏳ Needs Integration:
- Inject regime data into agent prompt
- Inject risk guidance into agent prompt
- Track agent overrides
- Learn from override success/failure

---

## Why This Matters

### Without Context (Current):
- Agent: "I'll buy with 10% of capital and 2% stop loss"
- Reality: VIX is 35, market is ranging, mean reversion would work better
- Result: Agent gets stopped out, doesn't know why

### With Context (Proposed):
- Regime: "High volatility, ranging market, avoid momentum strategies"
- Risk Manager: "Suggested: 5% position size, 3% stop loss"
- Agent: "I see high vol and ranging conditions. I'll wait for clearer setup or use mean reversion instead of momentum"
- Result: Agent adapts to market conditions

---

## Next Steps

1. **Modify `universal_trading_agent.py`**:
   - Add regime detection call in `_build_prompt()`
   - Add risk guidance call in `_build_prompt()`
   - Inject both into user prompt

2. **Add Override Tracking**:
   - Compare agent's decision vs guidance
   - Record when agent overrides
   - Track outcome (success/failure)

3. **Learning Loop**:
   - Analyze override success rate
   - Adjust guidance based on what works
   - Feed back into RL optimization

---

## Code Example

```python
def _build_prompt(self, market_state: Dict) -> str:
    """Build comprehensive prompt with regime and risk guidance"""
    
    # Get regime info
    from src.agents.regime_detector import get_regime_detector
    detector = get_regime_detector()
    regime_info = detector.detect_regime(self.config.ticker)
    
    # Get risk guidance
    from src.agents.advanced_risk_manager import get_risk_manager
    rm = get_risk_manager()
    
    current_price = market_state['current_price']
    atr = market_state.get('atr', current_price * 0.02)
    
    risk_guidance = rm.get_risk_guidance(
        balance=self.capital,
        entry_price=current_price,
        direction='LONG',
        confidence=70,  # Default, will be updated with actual
        win_rate=self._get_win_rate(),
        atr=atr,
        regime_info=regime_info
    )
    
    # Build prompt with context
    prompt = f"""
=== MARKET REGIME ANALYSIS ===
Current Regime: {regime_info['display']['emoji']} {regime_info['display']['label']}
Confidence: {regime_info['display']['confidence']:.0f}%
VIX: {regime_info['regime_info']['vix']:.1f}
Strategy Recommendations: {regime_info['display']['recommendation']['preferred_strategies']}

=== RISK MANAGEMENT GUIDANCE ===
Suggested Stop Loss: ${risk_guidance['suggested_stop_loss']:,.0f}
Suggested Position Size: ${risk_guidance['suggested_position_size_dollars']:,.0f}
Reasoning: {risk_guidance['reasoning']}
Override Guidance: {risk_guidance['override_guidance']}

=== CURRENT MARKET STATE ===
{market_state}
"""
    
    return prompt
```

---

**Status**: Backend ready, needs prompt integration (30 min task)
