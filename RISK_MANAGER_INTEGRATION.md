# 🛡️ Risk Manager Integration Guide

## Problem Statement

The Advanced Risk Manager is currently a standalone system. It needs to be integrated into the agent execution loop so that:

1. **Dynamic Stop Losses** are calculated based on volatility
2. **Trailing Stops** automatically tighten as profits increase
3. **Position Sizing** adjusts based on confidence and regime
4. **Risk Limits** pause agents when drawdown exceeds thresholds

---

## Solution: Integrate into Agent Manager

### Step 1: Modify `agent_manager.py`

Add Risk Manager to agent initialization:

```python
# In AgentManager.__init__()
from src.agents.advanced_risk_manager import get_risk_manager

self.risk_manager = get_risk_manager()
```

### Step 2: Modify Agent Execution Loop

Update `agent_manager._run_agent()` to use risk management:

```python
def _run_agent(self, agent_id: str):
    """Run agent in background with risk management"""
    agent_info = self.agents[agent_id]
    agent = agent_info['agent']
    trading_engine = agent_info['trading_engine']
    config = agent_info['config']
    
    cycle = 0
    while agent_info['running']:
        cycle += 1
        try:
            # 1. Get market state
            market_state = agent.get_market_state()
            
            # 2. Get current regime for risk adjustment
            from src.agents.regime_detector import get_regime_detector
            detector = get_regime_detector()
            regime_info = detector.detect_regime(config.ticker)
            
            # 3. Make trading decision
            decision = agent.make_decision(market_state)
            
            # 4. RISK MANAGEMENT: Adjust position size based on regime & confidence
            if decision['signal'] in ['BUY', 'SELL']:
                current_price = market_state['current_price']
                atr = market_state.get('atr', current_price * 0.02)
                
                # Calculate dynamic stop loss
                stop_loss = self.risk_manager.calculate_dynamic_stop_loss(
                    entry_price=current_price,
                    direction=decision['signal'],
                    atr=atr,
                    volatility_regime=regime_info['regime']
                )
                
                # Calculate position size with risk adjustment
                position_size_dollars, position_size_units = self.risk_manager.calculate_position_size(
                    balance=trading_engine.balance,
                    entry_price=current_price,
                    stop_loss_price=stop_loss,
                    confidence=decision['confidence'],
                    win_rate=self._get_agent_win_rate(agent_id),
                    volatility_multiplier=1.0 + (regime_info['vix'] - 18) / 10  # Adjust for VIX
                )
                
                # Store stop loss for this position
                position_id = f"{agent_id}_{cycle}"
                self.risk_manager.initialize_trailing_stop(
                    position_id=position_id,
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    direction=decision['signal'],
                    atr=atr
                )
                
                # Execute trade with adjusted position size
                decision['position_size'] = position_size_dollars
                decision['stop_loss'] = stop_loss
            
            # 5. Execute signal
            if decision['signal'] in ['BUY', 'SELL']:
                trade = trading_engine.execute_signal(
                    signal=decision['signal'],
                    symbol=config.ticker,
                    current_price=market_state['current_price'],
                    confidence=decision['confidence'],
                    reasoning=decision['reasoning']
                )
                
                if trade:
                    print(f"✅ {agent_info['config'].agent_name}: {decision['signal']} @ ${market_state['current_price']:.2f}")
            
            # 6. UPDATE TRAILING STOPS for open positions
            for position_id in list(self.risk_manager.position_trackers.keys()):
                if position_id.startswith(agent_id):
                    new_stop, should_exit = self.risk_manager.update_trailing_stop(
                        position_id=position_id,
                        current_price=market_state['current_price'],
                        current_atr=atr
                    )
                    
                    if should_exit:
                        # Exit position if stop hit
                        trading_engine.execute_signal('SELL', config.ticker, market_state['current_price'])
                        self.risk_manager.remove_position_tracker(position_id)
            
            # 7. CHECK PORTFOLIO RISK LIMITS
            from src.agents.portfolio_manager import get_portfolio_manager
            portfolio_mgr = get_portfolio_manager()
            all_agent_stats = self.get_all_agents()
            pause_decisions = portfolio_mgr.check_risk_limits(
                current_portfolio_value=sum(s.get('balance', 0) for s in all_agent_stats.values()),
                agent_stats=all_agent_stats
            )
            
            if pause_decisions.get(agent_id, False):
                print(f"⚠️ {agent_info['config'].agent_name}: Paused due to risk limits")
                agent_info['running'] = False
                break
            
            # 8. Update RL optimizer if enabled
            if agent_info['rl_optimizer']:
                agent_info['rl_optimizer'].update_with_trade(trade if decision['signal'] in ['BUY', 'SELL'] else None)
            
        except Exception as e:
            print(f"⚠️ Error in cycle {cycle}: {str(e)[:100]}")
        
        # Wait for next cycle
        if agent_info['running']:
            time.sleep(config.cycle_interval)
```

### Step 3: Add Helper Methods to AgentManager

```python
def _get_agent_win_rate(self, agent_id: str) -> float:
    """Get agent's historical win rate"""
    agent_info = self.agents.get(agent_id)
    if not agent_info:
        return 0.50  # Default 50%
    
    trading_engine = agent_info['trading_engine']
    if not trading_engine.trades_history:
        return 0.50
    
    wins = sum(1 for t in trading_engine.trades_history if t.get('pnl', 0) > 0)
    return wins / len(trading_engine.trades_history)

def get_agent_risk_summary(self, agent_id: str) -> Dict:
    """Get risk summary for an agent"""
    agent_info = self.agents.get(agent_id)
    if not agent_info:
        return {}
    
    trading_engine = agent_info['trading_engine']
    
    # Get open positions
    open_positions = []
    for position_id, tracker in self.risk_manager.position_trackers.items():
        if position_id.startswith(agent_id):
            open_positions.append(tracker)
    
    return {
        'agent_id': agent_id,
        'agent_name': agent_info['config'].agent_name,
        'balance': trading_engine.balance,
        'open_positions': len(open_positions),
        'total_pnl': trading_engine.balance - agent_info['config'].initial_balance,
        'win_rate': self._get_agent_win_rate(agent_id),
        'max_drawdown': trading_engine.max_drawdown,
        'open_position_details': open_positions
    }
```

### Step 4: Add API Endpoint for Risk Summary

Add to `src/web/app.py`:

```python
@app.route('/api/agent/<agent_id>/risk-summary', methods=['GET'])
def get_agent_risk_summary(agent_id):
    """Get risk summary for specific agent"""
    try:
        summary = agent_manager.get_agent_risk_summary(agent_id)
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## Integration Points

### 1. **Position Sizing** 
- **Before**: Fixed 10% of balance
- **After**: Dynamic based on confidence, win rate, volatility

### 2. **Stop Loss Placement**
- **Before**: Fixed percentage (2%)
- **After**: ATR-based, adjusted for regime (wider in high vol, tighter in low vol)

### 3. **Exit Management**
- **Before**: Manual or fixed time-based
- **After**: Automatic trailing stops with 5 profit levels

### 4. **Risk Limits**
- **Before**: No portfolio-level controls
- **After**: Automatic pause if drawdown >3% per agent or >6% portfolio

### 5. **Regime Awareness**
- **Before**: Same strategy in all market conditions
- **After**: Position sizing and stops adjust based on regime

---

## Data Flow

```
Agent Decision
    ↓
Risk Manager: Calculate Dynamic Stop
    ↓
Risk Manager: Calculate Position Size (confidence × win_rate × volatility)
    ↓
Execute Trade with Adjusted Size
    ↓
Initialize Trailing Stop
    ↓
Every Cycle: Update Trailing Stop
    ↓
Portfolio Manager: Check Risk Limits
    ↓
If Limit Hit: Pause Agent
```

---

## Testing the Integration

### Test 1: Dynamic Position Sizing

```python
# Create agent with 85% confidence
config = TradingConfig(
    agent_name="Test Agent",
    initial_balance=100000,
    enable_rl=False
)

agent_id = agent_manager.create_agent(config)
agent_manager.start_agent(agent_id)

# Monitor position sizes in console
# Should see: "Position size: $10,000" (10% base)
# With 85% confidence: $10,000 * 1.35 = $13,500
```

### Test 2: Trailing Stops

```python
# Simulate price movement
# Entry: $50,000
# Price: $51,000 (+2%) → Stop moves to entry
# Price: $52,500 (+5%) → Stop trails at 1.5 ATR
# Price: $55,000 (+10%) → Stop trails at 1.0 ATR
# Price: $54,500 (-0.9%) → Stop hit, position closed
```

### Test 3: Risk Limits

```python
# Create 3 agents
# Start all agents
# Monitor portfolio drawdown
# When drawdown > 3%: Agent should pause
# When drawdown > 6%: All agents should pause
```

---

## Frontend Display

The risk metrics will be displayed on each agent card:

```
Stop Loss: $49,000
Trailing: Level 2 (1.0 ATR)
Position: 1.5 BTC
R:R Ratio: 1:2.5
```

---

## Performance Impact

- **Computation**: +5-10ms per cycle (negligible)
- **Memory**: +100KB per agent (position trackers)
- **Network**: No additional API calls (all local)

---

## Rollback Plan

If issues arise:
1. Comment out risk manager calls in `_run_agent()`
2. Revert to fixed position sizing
3. Remove trailing stop updates
4. Keep portfolio risk limits (safety feature)

---

**Status**: Ready for implementation  
**Estimated Time**: 1-2 hours  
**Complexity**: Medium
