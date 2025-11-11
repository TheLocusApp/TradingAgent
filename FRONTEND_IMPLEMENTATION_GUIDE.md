# 🎨 Frontend Implementation Guide

## Overview

This guide covers all frontend components needed to expose the hedge fund features to end users.

**Status**: Ready for implementation  
**Estimated Time**: 4-6 hours  
**Complexity**: Medium

---

## 1. Portfolio Dashboard Widget

### Location
Add to `src/web/templates/index_multiagent.html` (top of page, after navbar)

### Component: Portfolio Summary Card

```html
<!-- Portfolio Summary Widget -->
<div class="portfolio-widget" style="margin-bottom: 24px;">
    <div class="widget-header">
        <h2 style="font-size: 18px; font-weight: 600; color: #fff;">
            <i class="fas fa-chart-pie"></i> Portfolio Overview
        </h2>
        <button onclick="rebalancePortfolio()" style="background: #10b981; color: #fff; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 12px;">
            🔄 Rebalance Now
        </button>
    </div>
    
    <div class="portfolio-metrics" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 16px;">
        <!-- Total Value -->
        <div class="metric-card">
            <div class="metric-label">Total Value</div>
            <div class="metric-value" id="portfolio-value">$100,000</div>
            <div class="metric-change" id="portfolio-change">+$5,234 (+5.23%)</div>
        </div>
        
        <!-- Portfolio Sharpe -->
        <div class="metric-card">
            <div class="metric-label">Portfolio Sharpe</div>
            <div class="metric-value" id="portfolio-sharpe">2.45</div>
            <div class="metric-change" style="color: #22c55e;">↑ Excellent</div>
        </div>
        
        <!-- Max Drawdown -->
        <div class="metric-card">
            <div class="metric-label">Max Drawdown</div>
            <div class="metric-value" id="portfolio-dd">-2.3%</div>
            <div class="metric-change" style="color: #22c55e;">✓ Within limits</div>
        </div>
        
        <!-- Active Agents -->
        <div class="metric-card">
            <div class="metric-label">Active Agents</div>
            <div class="metric-value" id="active-agents">3/5</div>
            <div class="metric-change">60% deployed</div>
        </div>
    </div>
    
    <!-- Risk Status Bar -->
    <div style="margin-top: 16px; padding: 12px; background: #1a1a24; border-radius: 6px; border-left: 4px solid #10b981;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="color: #9ca3af; font-size: 12px;">Portfolio Risk Status:</span>
                <span style="color: #10b981; font-weight: 600; margin-left: 8px;" id="risk-status">✓ Healthy</span>
            </div>
            <div style="font-size: 12px; color: #6b7280;">
                <span id="days-until-rebalance">7 days until rebalance</span>
            </div>
        </div>
    </div>
</div>

<style>
.portfolio-widget {
    background: #111318;
    border: 1px solid #2d2d3d;
    border-radius: 12px;
    padding: 20px;
}

.widget-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.metric-card {
    background: #1a1a24;
    border: 1px solid #2d2d3d;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
}

.metric-label {
    color: #9ca3af;
    font-size: 12px;
    margin-bottom: 8px;
}

.metric-value {
    color: #fff;
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 4px;
}

.metric-change {
    color: #6b7280;
    font-size: 12px;
}
</style>
```

### JavaScript: Portfolio Widget Updates

Add to `src/web/static/app.js`:

```javascript
// Update portfolio summary every 10 seconds
setInterval(updatePortfolioSummary, 10000);

async function updatePortfolioSummary() {
    try {
        const response = await fetch('/api/portfolio/summary');
        const data = await response.json();
        
        // Update metrics
        document.getElementById('portfolio-value').textContent = 
            '$' + data.current_value.toLocaleString('en-US', {maximumFractionDigits: 0});
        
        const pnl = data.total_pnl;
        const pnlPct = data.total_pnl_pct;
        const pnlColor = pnl >= 0 ? '#22c55e' : '#ef4444';
        document.getElementById('portfolio-change').innerHTML = 
            `<span style="color: ${pnlColor};">${pnl >= 0 ? '+' : ''}$${pnl.toLocaleString('en-US', {maximumFractionDigits: 2})} (${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%)</span>`;
        
        document.getElementById('portfolio-sharpe').textContent = data.portfolio_sharpe.toFixed(2);
        document.getElementById('portfolio-dd').textContent = (data.current_drawdown * 100).toFixed(1) + '%';
        document.getElementById('active-agents').textContent = 
            `${data.num_active_agents}/${data.num_agents}`;
        
        // Risk status
        const riskStatus = data.current_drawdown < 0.03 ? '✓ Healthy' : 
                          data.current_drawdown < 0.06 ? '⚠️ Elevated' : 
                          '🚨 Critical';
        const riskColor = data.current_drawdown < 0.03 ? '#22c55e' : 
                         data.current_drawdown < 0.06 ? '#f59e0b' : 
                         '#ef4444';
        document.getElementById('risk-status').innerHTML = 
            `<span style="color: ${riskColor};">${riskStatus}</span>`;
        
        document.getElementById('days-until-rebalance').textContent = 
            `${data.days_until_rebalance} days until rebalance`;
            
    } catch (error) {
        console.error('Error updating portfolio:', error);
    }
}

async function rebalancePortfolio() {
    try {
        const response = await fetch('/api/portfolio/rebalance', {method: 'POST'});
        const data = await response.json();
        
        if (data.status === 'success') {
            alert('✅ Portfolio rebalanced successfully!');
            updatePortfolioSummary();
        } else {
            alert('❌ Rebalancing failed: ' + data.message);
        }
    } catch (error) {
        alert('Error rebalancing portfolio: ' + error);
    }
}
```

---

## 2. Market Regime Indicator

### Location
Add to navbar in `src/web/templates/index_multiagent.html`

### Component: Regime Badge

```html
<!-- Market Regime Indicator (in navbar) -->
<div class="regime-indicator" style="position: absolute; right: 20px; top: 50%; transform: translateY(-50%); display: flex; gap: 12px; align-items: center;">
    <!-- Regime Badge -->
    <div class="regime-badge" id="regime-badge" style="background: #1a1a24; border: 1px solid #2d2d3d; border-radius: 8px; padding: 8px 12px; display: flex; align-items: center; gap: 8px;">
        <span id="regime-emoji" style="font-size: 16px;">📈</span>
        <div>
            <div id="regime-label" style="color: #fff; font-size: 12px; font-weight: 600;">Trending Up</div>
            <div id="regime-confidence" style="color: #9ca3af; font-size: 10px;">85% confidence</div>
        </div>
    </div>
    
    <!-- VIX Badge -->
    <div class="vix-badge" id="vix-badge" style="background: #1a1a24; border: 1px solid #2d2d3d; border-radius: 8px; padding: 8px 12px; display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 12px; font-weight: 600; color: #9ca3af;">VIX:</span>
        <span id="vix-value" style="color: #fff; font-size: 14px; font-weight: 600;">18</span>
    </div>
</div>

<style>
.regime-indicator {
    display: flex;
    gap: 12px;
    align-items: center;
}

.regime-badge, .vix-badge {
    cursor: pointer;
    transition: all 0.3s ease;
}

.regime-badge:hover, .vix-badge:hover {
    border-color: #6366f1;
    background: rgba(99, 102, 241, 0.1);
}
</style>
```

### JavaScript: Regime Updates

```javascript
// Update regime every 30 seconds
setInterval(updateRegimeIndicator, 30000);

async function updateRegimeIndicator() {
    try {
        const response = await fetch('/api/regime/current');
        const data = await response.json();
        const display = data.display;
        
        // Update regime badge
        document.getElementById('regime-emoji').textContent = display.emoji;
        document.getElementById('regime-label').textContent = display.label;
        document.getElementById('regime-confidence').textContent = 
            `${display.confidence.toFixed(0)}% confidence`;
        
        // Color code the badge
        const regimeBadge = document.getElementById('regime-badge');
        regimeBadge.style.borderColor = display.color;
        regimeBadge.style.background = display.color + '15';
        
        // Update VIX
        document.getElementById('vix-value').textContent = display.vix.toFixed(1);
        const vixBadge = document.getElementById('vix-badge');
        vixBadge.style.borderColor = display.vix_color;
        vixBadge.style.background = display.vix_color + '15';
        
        // Show tooltip on hover
        regimeBadge.title = `Strategy: ${display.recommendation.preferred_strategies.join(', ')}`;
        
    } catch (error) {
        console.error('Error updating regime:', error);
    }
}

// Call on page load
updateRegimeIndicator();
```

---

## 3. Momentum Rankings Widget

### Location
Add to right sidebar in `src/web/templates/index_multiagent.html`

### Component: Momentum Leaders

```html
<!-- Momentum Rankings Widget -->
<div class="momentum-widget" style="background: #111318; border: 1px solid #2d2d3d; border-radius: 12px; padding: 16px; margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <h3 style="color: #fff; font-size: 14px; font-weight: 600;">
            <i class="fas fa-fire"></i> Top Momentum Leaders
        </h3>
        <button onclick="refreshMomentumRankings()" style="background: none; border: none; color: #6366f1; cursor: pointer; font-size: 12px;">
            🔄 Refresh
        </button>
    </div>
    
    <div id="momentum-list" style="display: flex; flex-direction: column; gap: 8px;">
        <!-- Populated by JavaScript -->
    </div>
    
    <button onclick="showMomentumDetails()" style="width: 100%; background: #6366f1; color: #fff; border: none; padding: 10px; border-radius: 6px; cursor: pointer; font-size: 12px; margin-top: 12px;">
        View All Rankings
    </button>
</div>

<style>
.momentum-item {
    background: #1a1a24;
    border: 1px solid #2d2d3d;
    border-radius: 8px;
    padding: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    transition: all 0.2s ease;
}

.momentum-item:hover {
    border-color: #6366f1;
    background: rgba(99, 102, 241, 0.1);
}

.momentum-rank {
    background: #6366f1;
    color: #fff;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
}

.momentum-symbol {
    color: #fff;
    font-weight: 600;
    font-size: 13px;
}

.momentum-score {
    color: #22c55e;
    font-size: 12px;
    font-weight: 600;
}
</style>
```

### JavaScript: Momentum Updates

```javascript
// Update momentum rankings every 60 seconds
setInterval(updateMomentumRankings, 60000);

async function updateMomentumRankings() {
    try {
        const response = await fetch('/api/momentum/rankings');
        const data = await response.json();
        const rankings = data.rankings.slice(0, 5); // Top 5
        
        const list = document.getElementById('momentum-list');
        list.innerHTML = '';
        
        rankings.forEach((asset, index) => {
            const item = document.createElement('div');
            item.className = 'momentum-item';
            item.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div class="momentum-rank">${index + 1}</div>
                    <div>
                        <div class="momentum-symbol">${asset.symbol}</div>
                        <div style="color: #9ca3af; font-size: 11px;">
                            ${asset.asset_class}
                        </div>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div class="momentum-score">${asset.composite_score.toFixed(2)}</div>
                    <div style="color: #6b7280; font-size: 10px;">
                        ${asset.above_sma_200 ? '✓ Above SMA' : '✗ Below SMA'}
                    </div>
                </div>
            `;
            list.appendChild(item);
        });
        
    } catch (error) {
        console.error('Error updating momentum:', error);
    }
}

async function showMomentumDetails() {
    try {
        const response = await fetch('/api/momentum/recommendations');
        const data = await response.json();
        
        let details = '🏆 Top Momentum Recommendations:\n\n';
        data.top_recommendations.forEach((rec, i) => {
            details += `${i+1}. ${rec.symbol}\n`;
            details += `   Score: ${rec.composite_score.toFixed(2)}\n`;
            details += `   Allocation: ${(data.allocation_weights[rec.symbol] * 100).toFixed(1)}%\n\n`;
        });
        details += `\nRisk Regime: ${data.risk_regime.regime}\n`;
        details += `Recommendation: ${data.risk_regime.recommendation}`;
        
        alert(details);
    } catch (error) {
        alert('Error fetching momentum details: ' + error);
    }
}

// Call on page load
updateMomentumRankings();
```

---

## 4. RBI Deployment Panel

### Location
Add to `src/web/templates/strategy_lab.html`

### Component: Deploy Button & Status

```html
<!-- RBI Strategy Deployment Section -->
<div class="deployment-panel" style="background: #111318; border: 1px solid #2d2d3d; border-radius: 12px; padding: 20px; margin-top: 20px;">
    <h3 style="color: #fff; font-size: 16px; font-weight: 600; margin-bottom: 16px;">
        <i class="fas fa-rocket"></i> Deploy to Live Trading
    </h3>
    
    <div style="background: #1a1a24; border: 1px solid #2d2d3d; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
            <!-- Backtest Results -->
            <div>
                <div style="color: #9ca3af; font-size: 12px; margin-bottom: 4px;">Backtest Sharpe</div>
                <div style="color: #fff; font-size: 20px; font-weight: 600;" id="deploy-sharpe">2.34</div>
            </div>
            <div>
                <div style="color: #9ca3af; font-size: 12px; margin-bottom: 4px;">Total Trades</div>
                <div style="color: #fff; font-size: 20px; font-weight: 600;" id="deploy-trades">234</div>
            </div>
            <div>
                <div style="color: #9ca3af; font-size: 12px; margin-bottom: 4px;">Return %</div>
                <div style="color: #22c55e; font-size: 20px; font-weight: 600;" id="deploy-return">+45.67%</div>
            </div>
            <div>
                <div style="color: #9ca3af; font-size: 12px; margin-bottom: 4px;">Max Drawdown</div>
                <div style="color: #fff; font-size: 20px; font-weight: 600;" id="deploy-dd">-5.23%</div>
            </div>
        </div>
        
        <!-- Deployment Info -->
        <div style="background: #111318; border-radius: 6px; padding: 12px; margin-bottom: 16px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <i class="fas fa-info-circle" style="color: #6366f1;"></i>
                <span style="color: #9ca3af; font-size: 12px;">
                    Deploying to live trading will:
                </span>
            </div>
            <ul style="color: #9ca3af; font-size: 12px; margin-left: 24px; list-style: disc;">
                <li>Create a new live trading agent with backtest parameters</li>
                <li>Run in paper trading for 14 days for validation</li>
                <li>Auto-promote to live if performance matches expectations</li>
                <li>Alert if live performance deviates >30% from backtest</li>
            </ul>
        </div>
        
        <!-- Deploy Button -->
        <button onclick="deployStrategy()" style="width: 100%; background: #10b981; color: #fff; border: none; padding: 12px; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600;">
            🚀 Deploy Strategy to Live
        </button>
    </div>
    
    <!-- Deployment Status -->
    <div id="deployment-status" style="display: none; background: #1a1a24; border: 1px solid #2d2d3d; border-radius: 8px; padding: 16px;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <i class="fas fa-check-circle" style="color: #22c55e; font-size: 16px;"></i>
            <span style="color: #fff; font-weight: 600;">Deployment Successful!</span>
        </div>
        <div style="color: #9ca3af; font-size: 12px; line-height: 1.6;">
            <div>Deployment ID: <span id="deployment-id" style="color: #6366f1; font-family: monospace;"></span></div>
            <div>Agent ID: <span id="agent-id" style="color: #6366f1; font-family: monospace;"></span></div>
            <div>Status: <span id="deployment-state" style="color: #f59e0b;">Paper Trading (14 days)</span></div>
            <div style="margin-top: 12px;">
                <a href="/" style="color: #6366f1; text-decoration: none;">→ View in Live Trading</a>
            </div>
        </div>
    </div>
</div>

<style>
.deployment-panel {
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>
```

### JavaScript: Deployment Logic

```javascript
async function deployStrategy() {
    const strategyName = document.getElementById('strategy-name').textContent || 'DivergenceVolatilityEnhanced';
    
    const backtest_results = {
        sharpe_ratio: parseFloat(document.getElementById('deploy-sharpe').textContent) || 2.34,
        total_return: parseFloat(document.getElementById('deploy-return').textContent) || 45.67,
        total_trades: parseInt(document.getElementById('deploy-trades').textContent) || 234,
        max_drawdown: parseFloat(document.getElementById('deploy-dd').textContent) || -5.23
    };
    
    try {
        const response = await fetch('/api/rbi/deploy', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                strategy_name: strategyName,
                backtest_results: backtest_results
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Show success status
            document.getElementById('deployment-status').style.display = 'block';
            document.getElementById('deployment-id').textContent = data.deployment_id;
            document.getElementById('agent-id').textContent = data.agent_id;
            
            alert(`✅ Strategy deployed successfully!\n\nAgent: ${data.agent_id}\nStatus: Paper Trading (14 days)`);
        } else {
            alert(`❌ Deployment failed: ${data.message}`);
        }
    } catch (error) {
        alert(`Error deploying strategy: ${error}`);
    }
}
```

---

## 5. Agent Risk Management Display

### Location
Add to agent card in `src/web/templates/index_multiagent.html`

### Component: Risk Metrics on Agent Card

```html
<!-- Add to each agent decision card -->
<div class="agent-risk-metrics" style="background: #1a1a24; border-top: 1px solid #2d2d3d; margin-top: 12px; padding-top: 12px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 11px;">
    <!-- Stop Loss -->
    <div>
        <span style="color: #9ca3af;">Stop Loss:</span>
        <span style="color: #ef4444; font-weight: 600;" id="agent-stop-loss">$49,000</span>
    </div>
    
    <!-- Trailing Status -->
    <div>
        <span style="color: #9ca3af;">Trailing:</span>
        <span style="color: #22c55e; font-weight: 600;" id="agent-trailing">Level 2</span>
    </div>
    
    <!-- Position Size -->
    <div>
        <span style="color: #9ca3af;">Position:</span>
        <span style="color: #6366f1; font-weight: 600;" id="agent-position-size">1.5 BTC</span>
    </div>
    
    <!-- Risk/Reward -->
    <div>
        <span style="color: #9ca3af;">R:R Ratio:</span>
        <span style="color: #f59e0b; font-weight: 600;" id="agent-rr-ratio">1:2.5</span>
    </div>
</div>
```

---

## 6. CSS Styling

Add to `src/web/static/modern-style.css`:

```css
/* Portfolio Widget Styles */
.portfolio-widget {
    background: linear-gradient(135deg, #111318 0%, #1a1a24 100%);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.metric-card {
    transition: all 0.3s ease;
}

.metric-card:hover {
    border-color: #6366f1;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
}

/* Regime Indicator */
.regime-badge {
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
}

/* Momentum Widget */
.momentum-widget {
    max-height: 400px;
    overflow-y: auto;
}

.momentum-widget::-webkit-scrollbar {
    width: 6px;
}

.momentum-widget::-webkit-scrollbar-track {
    background: #1a1a24;
    border-radius: 3px;
}

.momentum-widget::-webkit-scrollbar-thumb {
    background: #6366f1;
    border-radius: 3px;
}

/* Deployment Panel */
.deployment-panel {
    box-shadow: 0 4px 6px rgba(16, 185, 129, 0.1);
}

/* Risk Metrics */
.agent-risk-metrics {
    border-radius: 6px;
}

.agent-risk-metrics span {
    display: inline-block;
}
```

---

## 7. Integration Checklist

- [ ] Add Portfolio Widget to `index_multiagent.html`
- [ ] Add Regime Indicator to navbar
- [ ] Add Momentum Rankings widget to sidebar
- [ ] Add RBI Deployment panel to `strategy_lab.html`
- [ ] Add Risk Metrics to agent cards
- [ ] Add all JavaScript functions to `app.js`
- [ ] Add CSS styles to `modern-style.css`
- [ ] Test all API endpoints
- [ ] Verify real-time updates
- [ ] Test responsive design on mobile

---

## 8. Testing

### Manual Testing Steps

1. **Portfolio Widget**
   - Create 3 agents with different strategies
   - Start all agents
   - Verify portfolio metrics update every 10 seconds
   - Click "Rebalance Now" and verify allocation changes

2. **Regime Indicator**
   - Verify regime badge shows current market state
   - Check VIX updates correctly
   - Hover over badge to see strategy recommendations

3. **Momentum Rankings**
   - Verify top 5 assets display
   - Click "View All Rankings" to see full list
   - Verify allocation weights sum to 100%

4. **RBI Deployment**
   - Generate strategy in Strategy Lab
   - Click "Deploy to Live"
   - Verify agent created in Live Trading
   - Check deployment status shows "Paper Trading"

5. **Risk Metrics**
   - Verify stop loss displays correctly
   - Check trailing stop level updates as price moves
   - Verify position size matches agent config

---

## 9. Performance Optimization

- Use `setInterval` for periodic updates (10-60 seconds)
- Cache API responses when appropriate
- Lazy load momentum rankings (only when needed)
- Use CSS animations instead of JavaScript where possible
- Debounce rapid API calls

---

## 10. Accessibility

- Add `aria-labels` to all interactive elements
- Ensure color contrast meets WCAG AA standards
- Support keyboard navigation
- Add tooltips for complex metrics

---

**Status**: Ready for implementation  
**Next Step**: Implement components in order of priority (Portfolio → Regime → Momentum → Deployment → Risk Metrics)
