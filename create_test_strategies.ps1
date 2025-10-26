# create_test_strategies.ps1
# Quick script to create example strategies for batch backtesting

Write-Host ""
Write-Host "🌙 Creating Test Strategies for Batch Backtesting" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# Create research directory
$researchDir = "src/data/rbi/my_test/research"
New-Item -Path $researchDir -ItemType Directory -Force | Out-Null

Write-Host "📂 Created directory: $researchDir" -ForegroundColor Green

# Strategy 1: RSI Mean Reversion
$strategy1 = @"
STRATEGY_NAME: RSI_Mean_Reversion

Entry Rules:
- RSI(14) crosses below 30 (oversold)
- Volume is greater than 1.2x average volume
- Price is above 200-day SMA (uptrend filter)

Exit Rules:
- RSI crosses above 50
- Stop loss: 5% from entry
- Profit target: 10% from entry

Configuration:
- Ticker: SPY
- Timeframe: Daily
- Initial Capital: `$10,000
- Commission: 0.001 (0.1%)

Notes:
This is a mean reversion strategy that buys oversold conditions
and exits when price returns to neutral territory.
"@

$strategy1 | Out-File -FilePath "$researchDir/Strategy1_RSI.txt" -Encoding UTF8
Write-Host "✅ Created: Strategy1_RSI.txt" -ForegroundColor Green

# Strategy 2: MACD Momentum
$strategy2 = @"
STRATEGY_NAME: MACD_Momentum

Entry Rules:
- MACD line crosses above signal line (bullish crossover)
- Price is above 50-day SMA (trend filter)
- ADX > 25 (strong trend confirmation)

Exit Rules:
- MACD line crosses below signal line (bearish crossover)
- Stop loss: 3% from entry

Configuration:
- Ticker: SPY
- Timeframe: Daily
- Initial Capital: `$10,000
- Commission: 0.001 (0.1%)

Notes:
This is a momentum strategy that follows strong uptrends
using MACD crossovers and trend strength filters.
"@

$strategy2 | Out-File -FilePath "$researchDir/Strategy2_MACD.txt" -Encoding UTF8
Write-Host "✅ Created: Strategy2_MACD.txt" -ForegroundColor Green

# Strategy 3: Bollinger Bands Reversal
$strategy3 = @"
STRATEGY_NAME: Bollinger_Reversal

Entry Rules:
- Price touches or crosses below lower Bollinger Band (2 std dev)
- RSI < 35 (oversold confirmation)
- Volume spike (> 1.5x average volume)

Exit Rules:
- Price reaches middle Bollinger Band
- RSI > 65 (overbought)
- Stop loss: 4% from entry

Configuration:
- Ticker: QQQ
- Timeframe: Daily
- Initial Capital: `$10,000
- Commission: 0.001 (0.1%)

Notes:
This strategy catches oversold bounces using Bollinger Bands
with RSI confirmation and volume filters.
"@

$strategy3 | Out-File -FilePath "$researchDir/Strategy3_BB.txt" -Encoding UTF8
Write-Host "✅ Created: Strategy3_BB.txt" -ForegroundColor Green

# Strategy 4: SMA Crossover
$strategy4 = @"
STRATEGY_NAME: SMA_Crossover

Entry Rules:
- 50-day SMA crosses above 200-day SMA (golden cross)
- Volume > average volume
- Price closes above both SMAs

Exit Rules:
- 50-day SMA crosses below 200-day SMA (death cross)
- Stop loss: 7% from entry

Configuration:
- Ticker: SPY
- Timeframe: Daily
- Initial Capital: `$10,000
- Commission: 0.001 (0.1%)

Notes:
Classic trend following strategy using the golden cross/death cross
signals with volume confirmation.
"@

$strategy4 | Out-File -FilePath "$researchDir/Strategy4_SMA.txt" -Encoding UTF8
Write-Host "✅ Created: Strategy4_SMA.txt" -ForegroundColor Green

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Green
Write-Host "✨ Successfully created 4 test strategies!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Green
Write-Host ""
Write-Host "📋 Strategy Files Created:" -ForegroundColor Cyan
Write-Host "  1. Strategy1_RSI.txt     - RSI Mean Reversion" -ForegroundColor White
Write-Host "  2. Strategy2_MACD.txt    - MACD Momentum" -ForegroundColor White
Write-Host "  3. Strategy3_BB.txt      - Bollinger Reversal" -ForegroundColor White
Write-Host "  4. Strategy4_SMA.txt     - SMA Crossover" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Make sure you've run setup_windows.ps1:" -ForegroundColor Yellow
Write-Host "     .\setup_windows.ps1" -ForegroundColor White
Write-Host ""
Write-Host "  2. Run the batch backtester:" -ForegroundColor Yellow
Write-Host "     python src/agents/rbi_batch_backtester.py $researchDir" -ForegroundColor White
Write-Host ""
Write-Host "  3. Compare results:" -ForegroundColor Yellow
Write-Host "     python src/scripts/compare_strategies.py $researchDir/GPT-5" -ForegroundColor White
Write-Host ""
Write-Host "💡 The batch backtester will:" -ForegroundColor Cyan
Write-Host "   - Generate Python code for each strategy using AI" -ForegroundColor White
Write-Host "   - Run backtests automatically" -ForegroundColor White
Write-Host "   - Save results to GPT-5 folder" -ForegroundColor White
Write-Host "   - Show performance statistics" -ForegroundColor White
Write-Host ""
