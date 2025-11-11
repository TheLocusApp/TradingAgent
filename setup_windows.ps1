# setup_windows.ps1
Write-Host ""
Write-Host "🌙 Moon Dev's TradingAgent - Windows Setup" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

$PROJECT_ROOT = $PSScriptRoot
if ($PROJECT_ROOT -eq "") { $PROJECT_ROOT = Get-Location }

$env:PYTHONPATH = $PROJECT_ROOT
Write-Host "✅ PYTHONPATH set to: $PROJECT_ROOT" -ForegroundColor Green

$condaEnv = $env:CONDA_DEFAULT_ENV
if ($condaEnv -eq "tflow") {
    Write-Host "✅ Conda environment 'tflow' is active" -ForegroundColor Green
} else {
    Write-Host "⚠️  Warning: Conda environment 'tflow' not active" -ForegroundColor Yellow
    Write-Host "   Run: conda activate tflow" -ForegroundColor White
}

Write-Host ""
Write-Host "Testing imports..." -ForegroundColor Cyan
python -c "from src.models.model_factory import ModelFactory; print('✅ Imports working!')" 2>&1

Write-Host ""
Write-Host "✨ Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "You can now run:" -ForegroundColor Cyan
Write-Host "  python src/agents/rbi_agent.py" -ForegroundColor White
Write-Host ""
