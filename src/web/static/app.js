// Modern Trading UI - JavaScript
let selectedModels = [];
let updateInterval;
let accountChart;
let chartData = [];

// Initialize on page load
$(document).ready(function() {
    loadOptions();
    loadConfig();
    initializeChart();
    updateTickerPrices(); // Initial ticker update
    
    // Check agent status immediately on page load
    updateStatus().then(() => {
        // Update button states based on actual status
        updateButtonStates();
    });
    
    startAutoUpdate();
    
    // Initialize Select2 for models
    $('#models').select2({
        placeholder: 'Select AI models',
        allowClear: true,
        dropdownParent: $('#settingsModal')
    }).on('change', function() {
        selectedModels = $(this).val() || [];
    });
    
    // Handle asset type change - reload ticker options
    $('#assetType').on('change', function() {
        // Fetch options again to get the right tickers for this asset type
        fetch('/api/options')
            .then(res => res.json())
            .then(options => updateTickerOptions(options))
            .catch(err => console.error('Error loading options:', err));
    });
});

// Update button states based on agent status
function updateButtonStates() {
    // This will be called after updateStatus() to sync UI with backend
}

// Toggle prompt visibility
function togglePrompt(timestamp) {
    const promptDiv = document.getElementById(`prompt-${timestamp}`);
    if (promptDiv) {
        if (promptDiv.style.display === 'none') {
            promptDiv.style.display = 'block';
        } else {
            promptDiv.style.display = 'none';
        }
    }
}

// Initialize ApexCharts
function initializeChart() {
    const options = {
        series: [{
            name: 'Account Value',
            data: chartData
        }],
        chart: {
            type: 'area',
            height: 400,
            background: 'transparent',
            foreColor: '#9ca3af',
            toolbar: {
                show: false
            },
            zoom: {
                enabled: false
            }
        },
        dataLabels: {
            enabled: false
        },
        stroke: {
            curve: 'smooth',
            width: 2,
            colors: ['#6366f1']
        },
        fill: {
            type: 'gradient',
            gradient: {
                shadeIntensity: 1,
                opacityFrom: 0.4,
                opacityTo: 0.1,
                stops: [0, 90, 100]
            },
            colors: ['#6366f1']
        },
        grid: {
            borderColor: '#1f1f2e',
            strokeDashArray: 4,
            xaxis: {
                lines: {
                    show: true
                }
            },
            yaxis: {
                lines: {
                    show: true
                }
            }
        },
        xaxis: {
            type: 'datetime',
            labels: {
                style: {
                    colors: '#6b7280'
                },
                format: 'MMM dd',  // Show month and day only
                datetimeFormatter: {
                    year: 'yyyy',
                    month: 'MMM yyyy',
                    day: 'MMM dd',
                    hour: 'MMM dd'
                }
            },
            axisBorder: {
                color: '#1f1f2e'
            }
        },
        yaxis: {
            labels: {
                style: {
                    colors: '#6b7280'
                },
                formatter: function(value) {
                    return '$' + value.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
                }
            }
        },
        tooltip: {
            theme: 'dark',
            x: {
                format: 'HH:mm:ss'
            },
            y: {
                formatter: function(value) {
                    return '$' + value.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
                }
            }
        }
    };
    
    accountChart = new ApexCharts(document.querySelector("#accountChart"), options);
    accountChart.render();
}

// Update chart with new data
function updateChart(balance) {
    const timestamp = new Date().getTime();
    chartData.push({
        x: timestamp,
        y: balance
    });
    
    // Keep only last 50 data points
    if (chartData.length > 50) {
        chartData.shift();
    }
    
    accountChart.updateSeries([{
        data: chartData
    }]);
}

// Load dropdown options
async function loadOptions() {
    try {
        const response = await fetch('/api/options');
        const options = await response.json();
        
        // Populate models
        const modelsSelect = $('#models');
        modelsSelect.empty();
        options.models.forEach(model => {
            modelsSelect.append(new Option(model.toUpperCase(), model));
        });
        
        // Populate tickers
        updateTickerOptions(options);
        
        // Populate timeframes
        const timeframeSelect = $('#timeframe');
        timeframeSelect.empty();
        options.timeframes.forEach(tf => {
            timeframeSelect.append(new Option(tf, tf));
        });
    } catch (error) {
        console.error('Error loading options:', error);
    }
}

// Update ticker options based on asset type
function updateTickerOptions(options) {
    const assetType = $('#assetType').val();
    const tickerSelect = $('#ticker');
    tickerSelect.empty();
    
    let tickers;
    let placeholder;
    
    if (assetType === 'crypto') {
        tickers = options.crypto_tickers;
        placeholder = "Select or type any crypto ticker";
    } else if (assetType === 'options') {
        tickers = options.options_tickers || ['SPY', 'QQQ', 'AAPL', 'TSLA', 'NVDA', 'IWM'];
        placeholder = "Select underlying symbol (e.g., SPY, QQQ)";
    } else {
        tickers = options.stock_tickers;
        placeholder = "Select or type any stock ticker";
    }
    
    tickers.forEach(ticker => {
        tickerSelect.append(new Option(ticker, ticker));
    });
    
    // Update label based on asset type
    const tickerLabel = tickerSelect.closest('.form-group').find('.form-label');
    if (assetType === 'options') {
        tickerLabel.text('Underlying Symbol');
    } else {
        tickerLabel.text('Ticker (type any symbol)');
    }
    
    // Initialize Select2 with tags to allow custom input
    tickerSelect.select2({
        tags: true,
        placeholder: placeholder,
        allowClear: true,
        createTag: function (params) {
            const term = $.trim(params.term);
            if (term === '') {
                return null;
            }
            return {
                id: term.toUpperCase(),
                text: term.toUpperCase(),
                newTag: true
            };
        }
    });
}

// Load current configuration
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();
        
        // Set form values
        $('#models').val(config.models).trigger('change');
        selectedModels = config.models;
        $('#temperature').val(config.model_temperature);
        $('#maxTokens').val(config.model_max_tokens);
        
        // Set system prompt with default as placeholder
        const defaultPrompt = `You are an expert ${config.asset_type} trading AI.

Your role is to analyze real-time market data for ${config.ticker} and make trading decisions on ${config.timeframe} candles.

OBJECTIVE: Maximize risk-adjusted returns on ${config.timeframe} timeframe.

Provide your response in this format:
SIGNAL: [BUY/SELL/HOLD]
CONFIDENCE: [0-100]%
REASONING: [your analysis]`;
        
        $('#systemPrompt').attr('placeholder', defaultPrompt);
        $('#systemPrompt').val(config.system_prompt || '');
        
        $('#assetType').val(config.asset_type);
        $('#ticker').val(config.ticker);
        $('#timeframe').val(config.timeframe);
        $('#cycleInterval').val(config.cycle_interval);
        $('#initialBalance').val(config.initial_balance);
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

// Save settings
async function saveSettings() {
    const config = {
        models: selectedModels,
        model_temperature: parseFloat($('#temperature').val()),
        model_max_tokens: parseInt($('#maxTokens').val()),
        system_prompt: $('#systemPrompt').val().trim(),
        asset_type: $('#assetType').val(),
        ticker: $('#ticker').val(),
        timeframe: $('#timeframe').val(),
        cycle_interval: parseInt($('#cycleInterval').val()),
        initial_balance: parseFloat($('#initialBalance').val())
    };
    
    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        if (result.status === 'success') {
            closeSettings();
            showNotification('Settings saved successfully!', 'success');
        } else {
            showNotification('Failed to save settings: ' + result.message, 'error');
        }
    } catch (error) {
        showNotification('Error saving settings: ' + error.message, 'error');
    }
}

// Start agent
async function startAgent() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    // Validate models are selected
    if (!selectedModels || selectedModels.length === 0) {
        showNotification('Please select at least one AI model in settings', 'error');
        openSettings();
        return;
    }
    
    startBtn.disabled = true;
    stopBtn.disabled = false;
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);
        
        const response = await fetch('/api/start', {
            method: 'POST',
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        const result = await response.json();
        
        if (result.status === 'success') {
            updateStatus();
            showNotification('Agent started successfully!', 'success');
        } else {
            showNotification('Failed to start agent: ' + result.message, 'error');
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            showNotification('Request timeout. Please try again.', 'error');
        } else {
            showNotification('Error starting agent: ' + error.message, 'error');
        }
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }
}

// Stop agent
async function stopAgent() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    try {
        const response = await fetch('/api/stop', {method: 'POST'});
        const result = await response.json();
        
        if (result.status === 'success') {
            startBtn.disabled = false;
            stopBtn.disabled = true;
            updateStatus();
            showNotification('Agent stopped', 'info');
        }
    } catch (error) {
        showNotification('Error stopping agent: ' + error.message, 'error');
    }
}

// Update status and metrics
async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        
        // Update status badge and button states
        const badge = document.getElementById('status-badge');
        const sessionInfo = document.getElementById('session-info');
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        
        if (status.running) {
            badge.textContent = 'RUNNING';
            badge.className = 'status-badge running';
            sessionInfo.textContent = `Session: ${status.session_id || 'N/A'}`;
            // Update button states
            if (startBtn) startBtn.disabled = true;
            if (stopBtn) stopBtn.disabled = false;
        } else {
            badge.textContent = 'STOPPED';
            badge.className = 'status-badge';
            sessionInfo.textContent = 'No active session';
            // Update button states
            if (startBtn) startBtn.disabled = false;
            if (stopBtn) stopBtn.disabled = true;
        }
        
        // Update metrics
        const balance = status.current_balance || 10000;
        document.getElementById('account-balance').textContent = 
            `$${balance.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        
        // Update chart with new balance
        if (status.running) {
            updateChart(balance);
        }
        
        document.getElementById('win-rate').textContent = 
            `${(status.win_rate || 0).toFixed(1)}%`;
        
        document.getElementById('total-trades').textContent = 
            status.total_trades || 0;
        
        // Update all metrics
        const pnlValue = status.total_pnl || 0;
        const pnlElement = document.getElementById('total-pnl');
        pnlElement.textContent = `$${pnlValue.toFixed(2)}`;
        pnlElement.className = pnlValue >= 0 ? 'metric-value positive' : 'metric-value negative';
        
        document.getElementById('win-loss-ratio').textContent = 
            (status.win_loss_ratio || 0).toFixed(2);
        
        // Only show metrics if there are actual trades
        const maxDD = document.getElementById('max-drawdown');
        const sharpe = document.getElementById('sharpe-ratio');
        const sortino = document.getElementById('sortino-ratio');
        
        if (status.total_trades > 0) {
            maxDD.textContent = `${(status.max_drawdown || 0).toFixed(2)}%`;
            sharpe.textContent = (status.sharpe_ratio || 0).toFixed(2);
            sortino.textContent = (status.sortino_ratio || 0).toFixed(2);
        } else {
            maxDD.textContent = '0%';
            sharpe.textContent = '0.00';
            sortino.textContent = '0.00';
        }
        
    } catch (error) {
        console.error('Error updating status:', error);
    }
}

// Update ticker prices
async function updateTickerPrices() {
    try {
        const response = await fetch('/api/ticker-prices');
        const prices = await response.json();
        
        // Update BTC
        if (prices['BTC/USD']) {
            document.getElementById('btc-price').textContent = 
                `$${prices['BTC/USD'].price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            const btcChange = document.getElementById('btc-change');
            const change = prices['BTC/USD'].change;
            btcChange.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
            btcChange.className = change >= 0 ? 'ticker-change positive' : 'ticker-change negative';
        }
        
        // Update QQQ
        if (prices['QQQ']) {
            document.getElementById('qqq-price').textContent = 
                `$${prices['QQQ'].price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            const qqqChange = document.getElementById('qqq-change');
            const change = prices['QQQ'].change;
            qqqChange.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
            qqqChange.className = change >= 0 ? 'ticker-change positive' : 'ticker-change negative';
        }
        
        // Update SPY
        if (prices['SPY']) {
            document.getElementById('spy-price').textContent = 
                `$${prices['SPY'].price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            const spyChange = document.getElementById('spy-change');
            const change = prices['SPY'].change;
            spyChange.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
            spyChange.className = change >= 0 ? 'ticker-change positive' : 'ticker-change negative';
        }
    } catch (error) {
        console.error('Error updating ticker prices:', error);
    }
}

// Update decisions feed with color coding
async function updateDecisions() {
    try {
        const response = await fetch('/api/decisions');
        const data = await response.json();
        
        const feed = document.getElementById('decisions-feed');
        
        // Extract decisions array from response
        const decisions = data.decisions || [];
        
        if (!decisions || decisions.length === 0) {
            feed.innerHTML = `
                <div style="text-align: center; color: #6b7280; padding: 40px 0;">
                    <i class="fas fa-robot" style="font-size: 32px; margin-bottom: 12px;"></i>
                    <div>No decisions yet</div>
                    <div style="font-size: 12px; margin-top: 8px;">Start the agent to see live trading decisions</div>
                </div>
            `;
            return;
        }
        
        // Show last 10 decisions
        const recentDecisions = decisions.slice(-10).reverse();
        
        feed.innerHTML = recentDecisions.map(d => {
            const signalClass = d.signal.toLowerCase();
            const time = new Date(d.timestamp).toLocaleTimeString();
            
            // Color coding: BUY=green, SELL=burgundy, HOLD=amber
            let badgeStyle = '';
            if (signalClass === 'buy') {
                badgeStyle = 'background: rgba(34, 197, 94, 0.15); color: #22c55e;';
            } else if (signalClass === 'sell') {
                badgeStyle = 'background: rgba(153, 27, 27, 0.15); color: #dc2626;';
            } else {
                badgeStyle = 'background: rgba(245, 158, 11, 0.15); color: #f59e0b;';
            }
            
            // Get detailed reasoning from individual decisions
            let detailedReasoning = d.reasoning || 'No reasoning provided';
            let promptData = '';
            
            if (d.individual_decisions) {
                const modelDecisions = Object.entries(d.individual_decisions);
                if (modelDecisions.length > 0) {
                    const [modelName, modelData] = modelDecisions[0];
                    detailedReasoning = modelData.reasoning || detailedReasoning;
                    
                    // Build prompt data for expansion
                    if (modelData.prompt && modelData.system_prompt) {
                        promptData = `
                            <div id="prompt-${d.timestamp}" style="display: none; margin-top: 12px; padding: 12px; background: #0a0a0f; border-radius: 6px; border: 1px solid #1f1f2e;">
                                <div style="margin-bottom: 12px;">
                                    <div style="color: #6366f1; font-size: 11px; font-weight: 600; margin-bottom: 6px;">SYSTEM PROMPT:</div>
                                    <div style="color: #9ca3af; font-size: 11px; line-height: 1.6; white-space: pre-wrap;">${modelData.system_prompt}</div>
                                </div>
                                <div>
                                    <div style="color: #6366f1; font-size: 11px; font-weight: 600; margin-bottom: 6px;">MARKET DATA SENT:</div>
                                    <div style="color: #9ca3af; font-size: 11px; line-height: 1.6; white-space: pre-wrap;">${modelData.prompt}</div>
                                </div>
                            </div>
                        `;
                    }
                }
            }
            
            return `
                <div class="trade-item">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span style="padding: 6px 12px; border-radius: 6px; font-size: 13px; font-weight: 700; ${badgeStyle}">${d.signal}</span>
                        <span style="font-size: 12px; color: #6b7280;">${time}</span>
                    </div>
                    <div style="display: flex; gap: 16px; margin-bottom: 12px; font-size: 13px;">
                        <div style="color: #9ca3af;">
                            Confidence: <span style="color: #fff; font-weight: 600;">${d.confidence}%</span>
                        </div>
                        <div style="color: #9ca3af;">
                            Models: <span style="color: #fff; font-weight: 600;">${d.model_count || 1}</span>
                        </div>
                    </div>
                    <div style="font-size: 13px; color: #d1d5db; line-height: 1.6; padding: 12px; background: #0f0f16; border-radius: 6px; position: relative;">
                        <div style="color: #6b7280; font-size: 11px; font-weight: 600; margin-bottom: 8px;">REASONING:</div>
                        ${detailedReasoning}
                        ${promptData ? `
                            <div style="text-align: right; margin-top: 8px;">
                                <button onclick="togglePrompt('${d.timestamp}')" style="background: none; border: none; color: #6366f1; font-size: 10px; cursor: pointer; text-decoration: underline;">
                                    click to expand prompt
                                </button>
                            </div>
                        ` : ''}
                    </div>
                    ${promptData}
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error updating decisions:', error);
    }
}

// Auto-update based on cycle interval
function startAutoUpdate() {
    updateStatus();
    updateDecisions();
    
    // Update ticker prices every 30 seconds
    setInterval(updateTickerPrices, 30000);
    
    // Update status and decisions based on cycle interval (default 3 minutes = 180 seconds)
    // For better UX, we'll update every 10 seconds to feel more "live"
    updateInterval = setInterval(() => {
        updateStatus();
        updateDecisions();
    }, 10000); // 10 seconds for smoother UX
}

// Modal functions
function openSettings() {
    document.getElementById('settingsModal').classList.add('active');
}

function closeSettings() {
    document.getElementById('settingsModal').classList.remove('active');
}

// Notification system
function showNotification(message, type = 'info') {
    // Simple alert for now - can be enhanced with toast notifications
    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️'
    };
    alert(`${icons[type]} ${message}`);
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('settingsModal');
    if (event.target === modal) {
        closeSettings();
    }
}
