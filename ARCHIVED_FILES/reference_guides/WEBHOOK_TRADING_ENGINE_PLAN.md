# Webhook Trading Engine - Implementation Plan

## Current Status: ⚠️ NEEDS IMPLEMENTATION

### Question #8 Answer:
**"When the alert is received from TradingView, will the correct option be bought?"**

**Answer**: NO - Not yet implemented. The webhook currently only **displays** the notification. It does NOT:
- ❌ Parse the webhook data
- ❌ Fetch option chain from TastyTrade
- ❌ Select correct strike/expiry
- ❌ Calculate quantity based on strategy
- ❌ Execute the option trade
- ❌ Track the position

**This is the next critical step to implement.**

---

## What Needs to Be Built

### Phase 1: Webhook Parser (Backend)

**File**: `src/trading/webhook_parser.py` (NEW)

```python
class WebhookParser:
    """Parse TradingView webhook and extract trade parameters"""
    
    def parse_signal(self, webhook_data):
        """
        Input: {
            "signal": "BUY" or "SELL",
            "type": "LONG" or "SHORT",
            "price": 500.25,
            "timestamp": "2025-11-09T11:30:00"
        }
        
        Output: {
            "direction": "CALL" or "PUT",
            "underlying_price": 500.25,
            "strategy_type": "LONG" or "SHORT",
            "timestamp": datetime
        }
        """
```

### Phase 2: Option Chain Selector (Backend)

**File**: `src/trading/option_selector.py` (NEW)

```python
class OptionSelector:
    """Select optimal strike/expiry based on strategy rules"""
    
    def __init__(self, tastytrade_provider):
        self.provider = tastytrade_provider
    
    def select_option(self, signal, underlying_price, strategy_config):
        """
        Based on strategy config:
        - LONGS: ATM or 1 ITM Call, 5 DTE
        - SHORTS: ATM or 1 ITM Put, 5 DTE
        - Delta target: 0.50-0.60
        
        Returns: {
            "symbol": "QQQ251114C500",
            "strike": 500,
            "expiry": "2025-11-14",
            "dte": 5,
            "option_type": "CALL",
            "bid": 4.50,
            "ask": 4.55,
            "mid": 4.525,
            "delta": 0.55
        }
        """
```

### Phase 3: Position Sizer (Backend)

**File**: `src/trading/position_sizer.py` (NEW)

```python
class PositionSizer:
    """Calculate number of contracts based on risk management"""
    
    def calculate_contracts(self, account_balance, risk_percent, option_price, strategy_type):
        """
        Strategy rules:
        - Risk per trade: 2.5% of account
        - Contracts: 3 (fixed for now)
        - LONGS: Full 2.5% risk
        - SHORTS in bull market: 50% reduction (1.25% risk)
        
        Returns: {
            "contracts": 3,
            "cost_per_contract": 450,  # $4.50 * 100
            "total_cost": 1350,
            "risk_amount": 250,  # 2.5% of $10k
            "max_loss": 1350  # Full premium at risk
        }
        """
```

### Phase 4: Trade Executor (Backend)

**File**: `src/trading/paper_trade_executor.py` (NEW)

```python
class PaperTradeExecutor:
    """Execute paper trades and track positions"""
    
    def execute_entry(self, option_data, contracts, account_balance):
        """
        Creates position entry:
        - Deducts cost from account balance
        - Creates position record
        - Sets TP1/TP2 targets based on strategy
        - Sets stop loss (swing high/low)
        
        Returns: {
            "position_id": "uuid",
            "entry_time": datetime,
            "option_symbol": "QQQ251114C500",
            "contracts": 3,
            "entry_price": 4.525,
            "cost_basis": 1357.50,
            "tp1_target": 6.79,  # +50% for TP1
            "tp2_target": 9.05,  # +100% for TP2
            "stop_loss": 2.26,   # Swing low
            "status": "OPEN"
        }
        """
    
    def check_exits(self, position, current_option_price):
        """
        Checks if TP1, TP2, or SL hit:
        - TP1 (35% for longs, 70% for shorts): Close partial
        - TP2 (65% for longs, 30% for shorts): Close remaining
        - SL: Close all
        
        Returns: {
            "exit_type": "TP1" | "TP2" | "SL",
            "contracts_closed": 1 or 2 or 3,
            "exit_price": 6.79,
            "pnl": 675.75,
            "remaining_contracts": 2 or 0
        }
        """
```

### Phase 5: Integration (Backend API)

**File**: `src/web/app.py` - Update webhook endpoint

```python
@app.route('/api/paper-trading/webhook', methods=['POST'])
def receive_webhook():
    """Enhanced webhook handler with trade execution"""
    try:
        webhook_data = request.get_json()
        
        # 1. Parse webhook
        parser = WebhookParser()
        signal = parser.parse_signal(webhook_data)
        
        # 2. Determine strategy config (longs vs shorts)
        if signal['strategy_type'] == 'LONG':
            config = {
                'tp1_rr': 1.0,
                'tp2_rr': 3.0,
                'tp1_close_pct': 35,
                'dte': 5,
                'delta_target': (0.50, 0.60)
            }
        else:  # SHORT
            config = {
                'tp1_rr': 1.5,
                'tp2_rr': 3.0,
                'tp1_close_pct': 70,
                'dte': 5,
                'delta_target': (0.50, 0.60)
            }
        
        # 3. Get option chain from TastyTrade
        selector = OptionSelector(tastytrade_provider)
        option = selector.select_option(
            signal=signal,
            underlying_price=signal['underlying_price'],
            strategy_config=config
        )
        
        # 4. Calculate position size
        sizer = PositionSizer()
        position_size = sizer.calculate_contracts(
            account_balance=paper_trading_state['account_balance'],
            risk_percent=2.5,
            option_price=option['mid'],
            strategy_type=signal['strategy_type']
        )
        
        # 5. Execute trade
        executor = PaperTradeExecutor()
        position = executor.execute_entry(
            option_data=option,
            contracts=position_size['contracts'],
            account_balance=paper_trading_state['account_balance']
        )
        
        # 6. Update state
        paper_trading_state['account_balance'] -= position['cost_basis']
        paper_trading_state['open_positions'].append(position)
        paper_trading_state['webhooks'].insert(0, webhook_data)
        
        # 7. Start monitoring position for exits
        # (This will be a background task)
        
        return jsonify({
            'success': True,
            'message': 'Trade executed',
            'position': position
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Phase 6: Position Monitoring (Background Task)

**File**: `src/trading/position_monitor.py` (NEW)

```python
class PositionMonitor:
    """Monitor open positions and execute exits"""
    
    def monitor_positions(self, open_positions, tastytrade_provider):
        """
        Runs every 60 seconds:
        1. Fetch current option prices for all open positions
        2. Check if TP1, TP2, or SL hit
        3. Execute exits as needed
        4. Update position status
        5. Add completed trades to trade history
        """
```

---

## Implementation Timeline

### Week 1: Core Infrastructure
- [ ] Create `WebhookParser` class
- [ ] Create `OptionSelector` class
- [ ] Create `PositionSizer` class
- [ ] Test with mock data

### Week 2: Trade Execution
- [ ] Create `PaperTradeExecutor` class
- [ ] Integrate with TastyTrade API
- [ ] Update webhook endpoint
- [ ] Test entry execution

### Week 3: Position Management
- [ ] Create `PositionMonitor` class
- [ ] Implement background monitoring task
- [ ] Test TP1/TP2/SL exits
- [ ] Verify P&L calculations

### Week 4: Testing & Refinement
- [ ] End-to-end testing with live webhooks
- [ ] Verify strategy rules (longs vs shorts)
- [ ] Test edge cases (no liquidity, API errors)
- [ ] Performance optimization

---

## Strategy Configuration Matrix

### LONGS (META Exact)
```python
LONGS_CONFIG = {
    'option_type': 'CALL',
    'strike_selection': 'ATM or 1 ITM',
    'dte': 5,
    'delta_target': (0.50, 0.60),
    'contracts': 3,
    'risk_percent': 2.5,
    'tp1_rr': 1.0,
    'tp2_rr': 3.0,
    'tp1_close_pct': 35,
    'tp2_close_pct': 65,
    'stop_type': 'ATR or Swing Low',
    'atr_mult': 2.0,
    'swing_bars': 10,
    'regime_filter': False,
    'ema_filter': False
}
```

### SHORTS (Swing High Optimized)
```python
SHORTS_CONFIG = {
    'option_type': 'PUT',
    'strike_selection': 'ATM or 1 ITM',
    'dte': 5,
    'delta_target': (0.50, 0.60),
    'contracts': 3,
    'risk_percent': 2.5,
    'tp1_rr': 1.5,
    'tp2_rr': 3.0,
    'tp1_close_pct': 70,
    'tp2_close_pct': 30,
    'stop_type': 'Swing High',
    'swing_bars': 5,
    'regime_filter': True,
    'ema_filter': True,
    'ema_ribbon': (13, 48, 200),
    'regime_sma': (50, 200),
    'bull_risk_reduction': 0.5  # 50% reduction in bull markets
}
```

---

## Webhook Format (Final Proposal)

### Entry Signal
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

### Exit Signal (Auto-detected by monitor)
The position monitor will automatically detect exits based on:
- Current option price vs TP1/TP2 targets
- Current option price vs stop loss
- Time-based exits (max hold time 13 hours)

---

## TastyTrade Integration Requirements

### Required API Calls:

1. **Get Underlying Price**
   ```python
   price = tastytrade_provider.get_underlying_price('QQQ')
   ```

2. **Get Option Chain**
   ```python
   chain = tastytrade_provider.get_option_chain(
       symbol='QQQ',
       expiration_date='2025-11-14',
       option_type='CALL'
   )
   ```

3. **Get Option Quote**
   ```python
   quote = tastytrade_provider.get_option_quote('.QQQ251114C500')
   ```

4. **Get Greeks**
   ```python
   greeks = tastytrade_provider.get_option_greeks('.QQQ251114C500')
   # Returns: delta, gamma, theta, vega
   ```

---

## Testing Strategy

### Phase 1: Unit Tests
- Test webhook parsing with various formats
- Test option selection logic
- Test position sizing calculations
- Test P&L calculations

### Phase 2: Integration Tests
- Test full webhook → trade execution flow
- Test position monitoring and exits
- Test error handling (API failures, no liquidity)

### Phase 3: Paper Trading
- Run for 2-4 weeks with live webhooks
- Compare results to Pine Script backtest
- Verify win rate ~64%, profit factor ~1.4
- Verify TP1/TP2/SL execution accuracy

### Phase 4: Go Live
- Start with 1 contract per trade
- Scale to 3 contracts after 10 successful trades
- Monitor slippage and execution quality

---

## Risk Management

### Position Limits
- Max open positions: 3
- Max risk per trade: 2.5% of account
- Max total risk: 7.5% of account (3 positions)

### Circuit Breakers
- Stop trading if account down 10% in one day
- Stop trading if 3 consecutive losses
- Require manual restart after circuit breaker

### Error Handling
- If TastyTrade API fails: Skip trade, log error
- If no suitable options found: Skip trade, log reason
- If insufficient balance: Skip trade, alert user

---

## Summary

**Current Status**: Webhook reception works, but NO trade execution

**What's Needed**:
1. ✅ Webhook parser
2. ✅ Option selector (TastyTrade integration)
3. ✅ Position sizer
4. ✅ Trade executor
5. ✅ Position monitor
6. ✅ Exit logic (TP1/TP2/SL)

**Estimated Time**: 3-4 weeks for full implementation

**Priority**: HIGH - This is the core functionality needed for live trading

**Next Step**: Start with Phase 1 (WebhookParser) and test with mock data

---

## Files to Create

1. `src/trading/webhook_parser.py`
2. `src/trading/option_selector.py`
3. `src/trading/position_sizer.py`
4. `src/trading/paper_trade_executor.py`
5. `src/trading/position_monitor.py`
6. `tests/test_webhook_trading_engine.py`

**Let me know when you're ready to start implementation!** 🚀
