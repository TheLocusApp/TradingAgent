# RL Optimization with Agent Lightning 🤖

**Status**: ✅ Implementation Complete & Tested

## Overview

Agent Lightning RL integration allows your trading agents to automatically optimize their decision logic based on real trading performance. After a configurable number of trades, agents transition from **training mode** to **optimized mode** with improved decision-making.

## How It Works

### Phase 1: Training (First 50 Trades)
```
User creates agent with "Enable RL Optimization" ✓
         ↓
Agent runs with standard prompt
         ↓
🔄 Training tag appears on decisions
         ↓
RL optimizer tracks all trades & decisions
```

### Phase 2: Optimization (After 50 Trades)
```
50 trades completed
         ↓
RL optimizer calculates reward score:
  • Win Rate: 40% weight
  • Sharpe Ratio: 30% weight
  • Total Profit: 30% weight
         ↓
Agent Lightning optimizes prompt variations
         ↓
✨ Optimized tag appears on decisions
```

## Creating an RL-Enabled Agent

### Step 1: Open Live Trading
Navigate to **LIVE TRADING** page

### Step 2: Click "New Agent"
Click the blue **+ New Agent** button

### Step 3: Enable RL Optimization
In the modal, check the box:
```
☑ Enable RL Optimization
```

You'll see:
```
🤖 Agent Lightning RL
Agent will optimize its decision logic after 50 trades. 
Shows training progress with tags on each decision.
```

### Step 4: Configure Agent
- **Agent Name**: e.g., "RL Crypto Trader"
- **Asset Type**: Crypto, Stocks, or Options
- **Monitored Assets**: BTC, ETH, SPY, etc.
- **AI Models**: Select 1+ models (DeepSeek, OpenAI, Gemini, Grok)
- **Strategy**: Your trading strategy description

### Step 5: Create & Start
Click **Create & Start Agent**

## Monitoring RL Progress

### Decision Card Tags

**During Training** (First 50 trades):
```
┌─────────────────────────────────────┐
│ BUY • Agent 1  🔄 Training (15/50)  │
│ Confidence: 72%                     │
│ Reasoning: ...                      │
└─────────────────────────────────────┘
```
- Yellow background (#f59e0b)
- Shows progress: `15/50` means 15 trades completed
- Updates in real-time

**After Optimization** (50+ trades):
```
┌─────────────────────────────────────┐
│ BUY • Agent 1  ✨ RL Optimized      │
│ Confidence: 78%                     │
│ Reasoning: ...                      │
└─────────────────────────────────────┘
```
- Green background (#10b981)
- Indicates optimized decision logic is active
- Confidence typically increases

### Agent Comparison Table

The **Agent Comparison** table shows:
- **Win Rate**: Should improve after optimization
- **Sharpe Ratio**: Risk-adjusted returns
- **Total Trades**: Count of completed trades
- **P&L**: Profit/loss in dollars and percentage

## Technical Details

### Configuration Fields

```python
# In TradingConfig
enable_rl: bool = False              # Enable/disable RL
rl_training_trades: int = 50         # Trades before optimization
rl_status: str = "inactive"          # "inactive", "training", "optimized"
rl_optimized_prompt: str = ""        # Stores optimized prompt
```

### Reward Calculation

```python
reward = (win_rate * 0.4) + (sharpe_ratio * 0.3) + (profit * 0.3)
```

**Example**:
- Win Rate: 55% (0.55 * 0.4 = 0.22)
- Sharpe Ratio: 1.2 (1.2 * 0.3 = 0.36)
- Profit: $500 (normalized, 0.5 * 0.3 = 0.15)
- **Total Reward**: 0.73

### RLOptimizer Class

Located in `src/agents/rl_optimizer.py`:

```python
class RLOptimizer:
    def record_decision(decision)     # Track each decision
    def record_trade(trade)           # Track completed trades
    def check_optimization_trigger()  # Check if 50 trades reached
    def calculate_reward()            # Calculate reward score
    def trigger_optimization()        # Run optimization
    def get_rl_status_display()       # Get UI status/tags
```

## Files Modified

### Backend
- **`src/config/trading_config.py`**
  - Added `enable_rl`, `rl_training_trades`, `rl_status`, `rl_optimized_prompt` fields
  - Updated `to_dict()` and `from_dict()` methods

- **`src/agents/agent_manager.py`**
  - Imports `RLOptimizer`
  - Creates optimizer when `enable_rl=True`
  - Includes RL status in agent stats

- **`src/agents/rl_optimizer.py`** (NEW)
  - Complete RL wrapper implementation
  - Tracks trades and decisions
  - Calculates rewards
  - Provides status display

### Frontend
- **`src/web/templates/index_multiagent.html`**
  - Added RL checkbox in "Create New Agent" modal
  - Added info box explaining RL optimization
  - Updated decision rendering to show tags
  - Tags display training progress or optimized status

## API Integration

### Create Agent with RL

```javascript
const config = {
    agent_name: "RL Trader",
    asset_type: "crypto",
    monitored_assets: ["BTC", "ETH"],
    models: ["deepseek"],
    enable_rl: true,           // ← Enable RL
    rl_training_trades: 50     // ← Trades before optimization
};

fetch('/api/agents', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(config)
});
```

### Get Agent Status with RL

```javascript
GET /api/agents
```

Response includes:
```json
{
    "agent_1": {
        "name": "RL Trader",
        "rl_status": {
            "status": "training",
            "label": "🔄 Training (15/50)",
            "color": "#f59e0b",
            "progress": 30
        }
    }
}
```

## Testing

Run the test suite:

```bash
python test_rl_implementation.py
```

Tests verify:
- ✅ RL config fields initialization
- ✅ Config serialization/deserialization
- ✅ RLOptimizer creation
- ✅ Status display formatting
- ✅ Agent manager integration

## Best Practices

### 1. Strategy Description
Provide clear strategy instructions:
```
"Analyze BTC/USD on 3-minute candles. Use RSI(14), MACD, 
and EMA(20) for signals. Buy when RSI < 30 and MACD crosses up. 
Sell when RSI > 70 or MACD crosses down. Manage risk with 2% 
stop-loss and 3:1 reward:risk ratio."
```

### 2. Training Duration
- **50 trades** = ~2-4 hours of active trading (3-min candles)
- Longer training = more data for optimization
- Consider increasing to 100 trades for more robust optimization

### 3. Multiple Agents
Create multiple RL agents with different strategies:
- Agent 1: Momentum trading (RSI-based)
- Agent 2: Mean reversion (Bollinger Bands)
- Agent 3: Trend following (Moving averages)

Compare their optimized performance in the Agent Comparison table.

### 4. Monitor Progress
- Watch the training progress tags (🔄 Training 15/50)
- Check win rate and Sharpe ratio trends
- Note confidence changes after optimization

## Future Enhancements

### Phase 2: Agent Lightning Integration
Currently, optimization is a placeholder. Next phase will integrate:
- Actual prompt optimization using Agent Lightning
- Multi-prompt testing (100+ variations)
- Automatic prompt refinement
- Persistent optimization results

### Phase 3: Advanced Features
- Adaptive training thresholds (adjust based on market conditions)
- Multi-agent collaboration (agents learn from each other)
- Continuous optimization (re-optimize every 50 new trades)
- Strategy mutation (generate new strategy variations)

## Troubleshooting

### Tags Not Showing
- Ensure `enable_rl: true` in agent config
- Check browser console for errors
- Verify agent is running (status = "running")

### Optimization Not Triggering
- Confirm 50 trades have completed
- Check agent's trade history in console logs
- Verify `rl_status` is "training" before optimization

### Performance Decreased After Optimization
- This can happen if training data was noisy
- Consider increasing training trades to 100+
- Verify strategy description is clear and specific

## Support

For issues or questions:
1. Check the test suite: `test_rl_implementation.py`
2. Review logs in console output
3. Check agent decision cards for RL status tags
4. Verify config in agent stats response

---

**Built with ❤️ by Moon Dev**  
**Powered by Agent Lightning 🚀**
