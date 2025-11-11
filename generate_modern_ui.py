#!/usr/bin/env python3
"""
Generate modern UI HTML file
"""

html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alpha Arena - AI Trading</title>
    <link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='modern-style.css') }}">
</head>
<body>
    <!-- Top Navigation -->
    <div class="top-nav">
        <div class="logo">Alpha<span>Arena</span></div>
        <div class="nav-links">
            <a href="#" class="active">LIVE</a>
            <a href="#">LEADERBOARD</a>
            <a href="#">BLOG</a>
            <a href="#">MODELS</a>
            <button class="settings-btn" onclick="openSettings()">
                <i class="fas fa-cog"></i> Settings
            </button>
        </div>
    </div>
    
    <!-- Ticker Bar -->
    <div class="container">
        <div class="ticker-bar">
            <div class="ticker-item">
                <span class="ticker-symbol">🪙 BTC</span>
                <span class="ticker-price" id="btc-price">$0</span>
                <span class="ticker-change positive">+0%</span>
            </div>
            <div class="ticker-item">
                <span class="ticker-symbol">⟠ ETH</span>
                <span class="ticker-price" id="eth-price">$0</span>
                <span class="ticker-change positive">+0%</span>
            </div>
            <div class="ticker-item">
                <span class="ticker-symbol">◎ SOL</span>
                <span class="ticker-price" id="sol-price">$0</span>
                <span class="ticker-change positive">+0%</span>
            </div>
        </div>
        
        <!-- Main Grid -->
        <div class="main-grid">
            <!-- Chart Section -->
            <div class="chart-section">
                <div class="chart-header">
                    <div class="chart-title">TOTAL ACCOUNT VALUE</div>
                </div>
                <div style="height: 400px; display: flex; align-items: center; justify-content: center; color: #6b7280;">
                    <div style="text-align: center;">
                        <i class="fas fa-chart-line" style="font-size: 48px; margin-bottom: 16px;"></i>
                        <div>Chart visualization coming soon</div>
                    </div>
                </div>
                
                <!-- Metrics Grid -->
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Win Rate</div>
                        <div class="metric-value" id="win-rate">0%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Total Trades</div>
                        <div class="metric-value" id="total-trades">0</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Max Drawdown</div>
                        <div class="metric-value negative" id="max-drawdown">0%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Sharpe Ratio</div>
                        <div class="metric-value" id="sharpe-ratio">0.00</div>
                    </div>
                </div>
            </div>
            
            <!-- Right Sidebar -->
            <div>
                <!-- Status Card -->
                <div class="status-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <div class="status-badge" id="status-badge">STOPPED</div>
                        <div style="font-size: 12px;" id="session-info">No session</div>
                    </div>
                    <div class="account-value" id="account-balance">$10,000</div>
                    <div style="font-size: 13px; opacity: 0.9;">Current Balance</div>
                    <div style="display: flex; gap: 12px; margin-top: 16px;">
                        <button class="btn btn-primary" id="startBtn" onclick="startAgent()">
                            <i class="fas fa-play"></i> Start
                        </button>
                        <button class="btn btn-secondary" id="stopBtn" onclick="stopAgent()" disabled>
                            <i class="fas fa-stop"></i> Stop
                        </button>
                    </div>
                </div>
                
                <!-- Trades Feed -->
                <div class="trades-feed">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <div style="font-size: 16px; font-weight: 600; color: #fff;">Live Decisions</div>
                        <div style="background: #1f1f2e; padding: 6px 12px; border-radius: 6px; font-size: 12px; color: #9ca3af;">Last 10</div>
                    </div>
                    <div id="decisions-feed">
                        <div style="text-align: center; color: #6b7280; padding: 40px 0;">
                            <i class="fas fa-robot" style="font-size: 32px; margin-bottom: 12px;"></i>
                            <div>No decisions yet</div>
                            <div style="font-size: 12px; margin-top: 8px;">Start the agent to see live trading decisions</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Settings Modal -->
    <div class="modal" id="settingsModal">
        <div class="modal-content">
            <div class="modal-header">
                <div style="font-size: 20px; font-weight: 700; color: #fff;">⚙️ Trading Settings</div>
                <button style="background: none; border: none; color: #9ca3af; font-size: 24px; cursor: pointer;" onclick="closeSettings()">×</button>
            </div>
            <div style="padding: 24px;">
                <!-- Model Settings -->
                <div style="margin-bottom: 32px;">
                    <div style="font-size: 16px; font-weight: 600; color: #fff; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid #1f1f2e;">AI Models</div>
                    <div class="form-group">
                        <label class="form-label">Select Models</label>
                        <select id="models" class="form-select" multiple></select>
                        <div style="font-size: 12px; color: #6b7280; margin-top: 6px;">Choose one or more AI models</div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Temperature</label>
                        <input type="number" id="temperature" class="form-input" step="0.1" min="0" max="2" value="0.7">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Max Tokens</label>
                        <input type="number" id="maxTokens" class="form-input" value="1024">
                    </div>
                </div>
                
                <!-- System Prompt -->
                <div style="margin-bottom: 32px;">
                    <div style="font-size: 16px; font-weight: 600; color: #fff; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid #1f1f2e;">System Prompt</div>
                    <div class="form-group">
                        <label class="form-label">Custom System Prompt</label>
                        <textarea id="systemPrompt" class="form-textarea" placeholder="Leave empty to use default prompt..."></textarea>
                        <div style="font-size: 12px; color: #6b7280; margin-top: 6px;">Customize how the AI analyzes market data</div>
                    </div>
                </div>
                
                <!-- Trading Settings -->
                <div style="margin-bottom: 32px;">
                    <div style="font-size: 16px; font-weight: 600; color: #fff; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid #1f1f2e;">Trading Configuration</div>
                    <div class="form-group">
                        <label class="form-label">Asset Type</label>
                        <select id="assetType" class="form-select">
                            <option value="crypto">Cryptocurrency</option>
                            <option value="stock">Stock</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Ticker</label>
                        <select id="ticker" class="form-select"></select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Timeframe</label>
                        <select id="timeframe" class="form-select"></select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Cycle Interval (seconds)</label>
                        <input type="number" id="cycleInterval" class="form-input" value="180">
                    </div>
                </div>
                
                <!-- Simulation -->
                <div style="margin-bottom: 32px;">
                    <div style="font-size: 16px; font-weight: 600; color: #fff; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid #1f1f2e;">Simulation</div>
                    <div class="form-group">
                        <label class="form-label">Initial Balance</label>
                        <input type="number" id="initialBalance" class="form-input" value="10000">
                    </div>
                </div>
            </div>
            <div style="padding: 24px; border-top: 1px solid #1f1f2e; display: flex; justify-content: flex-end; gap: 12px;">
                <button style="background: #1f1f2e; color: #9ca3af; padding: 12px 24px; border: 1px solid #2d2d3d; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer;" onclick="closeSettings()">Cancel</button>
                <button style="background: #6366f1; color: #fff; padding: 12px 24px; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer;" onclick="saveSettings()">Save Configuration</button>
            </div>
        </div>
    </div>
    
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
    <script src="{{ url_for('static', filename='app.js') }}"></script>
</body>
</html>'''

# Write to file
with open('src/web/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("✅ Modern UI HTML generated successfully!")
print("📁 File: src/web/templates/index.html")
