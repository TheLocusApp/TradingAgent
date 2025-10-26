# setup_windows.ps1
# Windows Setup Script for TradingAgent
# Run this before using any TradingAgent scripts

Write-Host ""
Write-Host "🌙 Moon Dev's TradingAgent - Windows Setup" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# Get current directory (project root)
$PROJECT_ROOT = $PSScriptRoot
Write-Host "📂 Project Root: $PROJECT_ROOT" -ForegroundColor Yellow

# Set PYTHONPATH to project root
$env:PYTHONPATH = $PROJECT_ROOT
Write-Host "✅ PYTHONPATH set to: $PROJECT_ROOT" -ForegroundColor Green

# Check if conda environment is active
$condaEnv = $env:CONDA_DEFAULT_ENV
if ($condaEnv -eq "tflow") {
    Write-Host "✅ Conda environment 'tflow' is active" -ForegroundColor Green
} else {
    Write-Host "⚠️  Warning: Conda environment 'tflow' not active" -ForegroundColor Yellow
    Write-Host "   Run: conda activate tflow" -ForegroundColor White
}

# Test imports
Write-Host ""
Write-Host "🔍 Testing Python imports..." -ForegroundColor Cyan

$testImports = @"
import sys
sys.path.insert(0, r'$PROJECT_ROOT')

try:
    from src.models.model_factory import ModelFactory
    print('✅ model_factory import OK')
except ImportError as e:
    print(f'❌ model_factory import failed: {e}')

try:
    from src.agents import rbi_agent
    print('✅ rbi_agent import OK')
except ImportError as e:
    print(f'❌ rbi_agent import failed: {e}')
"@

python -c $testImports

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Green
Write-Host "✨ Setup Complete! You can now run TradingAgent scripts" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Green
Write-Host ""
Write-Host "📚 Quick Start Examples:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Run RBI Agent:" -ForegroundColor Yellow
Write-Host "     python src/agents/rbi_agent.py" -ForegroundColor White
Write-Host ""
Write-Host "  2. Run Batch Backtester:" -ForegroundColor Yellow
Write-Host "     python src/agents/rbi_batch_backtester.py src/data/rbi/my_test/research" -ForegroundColor White
Write-Host ""
Write-Host "  3. Compare Strategies:" -ForegroundColor Yellow
Write-Host "     python src/scripts/compare_strategies.py" -ForegroundColor White
Write-Host ""
Write-Host "  4. Create test strategies:" -ForegroundColor Yellow
Write-Host "     .\create_test_strategies.ps1" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tip: Run this setup script each time you open a new PowerShell window" -ForegroundColor Cyan
Write-Host "    Or add it to your PowerShell profile for automatic setup" -ForegroundColor Cyan
Write-Host ""
