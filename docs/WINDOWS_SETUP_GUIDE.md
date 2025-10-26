# Windows Setup Guide for TradingAgent

## Fixing Import Errors on Windows

If you see `ModuleNotFoundError: No module named 'src'`, here's how to fix it:

### Quick Fix (Every Time You Open PowerShell)

```powershell
# Navigate to your project directory
cd C:\Users\ahmed\CascadeProjects\moon-dev-ai-agents

# Set PYTHONPATH to current directory
$env:PYTHONPATH = "$PWD"

# Now run scripts
python src/agents/rbi_agent.py
```

### Permanent Fix (Recommended)

#### Option 1: Add to PowerShell Profile

1. Open PowerShell profile:
```powershell
notepad $PROFILE
```

If you get an error, create it first:
```powershell
New-Item -Path $PROFILE -Type File -Force
notepad $PROFILE
```

2. Add this line to the file:
```powershell
# Auto-set PYTHONPATH when in trading agent directory
function Set-TradingAgentPath {
    if (Test-Path "C:\Users\ahmed\CascadeProjects\moon-dev-ai-agents") {
        cd C:\Users\ahmed\CascadeProjects\moon-dev-ai-agents
        $env:PYTHONPATH = "$PWD"
        Write-Host "✅ TradingAgent environment ready!" -ForegroundColor Green
    }
}

# Create an alias
Set-Alias -Name trading -Value Set-TradingAgentPath
```

3. Save and close. Now you can just type `trading` in any PowerShell window!

#### Option 2: Create a Startup Script

Create `setup_windows.ps1` in your project root:

```powershell
# setup_windows.ps1
# Run this before using TradingAgent

Write-Host "🌙 Moon Dev's TradingAgent - Windows Setup" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Get current directory
$PROJECT_ROOT = $PSScriptRoot

# Set PYTHONPATH
$env:PYTHONPATH = $PROJECT_ROOT

Write-Host "✅ PYTHONPATH set to: $PROJECT_ROOT" -ForegroundColor Green
Write-Host "✅ Ready to run TradingAgent scripts!" -ForegroundColor Green
Write-Host ""
Write-Host "Examples:" -ForegroundColor Yellow
Write-Host "  python src/agents/rbi_agent.py" -ForegroundColor White
Write-Host "  python src/scripts/compare_strategies.py" -ForegroundColor White
Write-Host ""
```

Then use it:
```powershell
# Run this first
.\setup_windows.ps1

# Then run your scripts
python src/agents/rbi_agent.py
```

### Option 3: Use Python -m (No Setup Required)

Instead of running scripts directly, use Python's module syntax:

```powershell
# Instead of: python src/agents/rbi_agent.py
# Use this:
python -m src.agents.rbi_agent

# Instead of: python src/scripts/compare_strategies.py
# Use this:
python -m src.scripts.compare_strategies
```

## Running Batch Backtester on Windows

### Correct Paths

Your project is at: `C:\Users\ahmed\CascadeProjects\moon-dev-ai-agents`

NOT at: `/home/user/TradingAgent` (that's Linux)

### Create Test Strategies

```powershell
# Create research folder
New-Item -Path "src/data/rbi/my_test/research" -ItemType Directory -Force

# Create strategy files
Set-Location "src/data/rbi/my_test/research"

# Strategy 1
@"
STRATEGY_NAME: RSI_Strategy
Buy when RSI < 30, sell when RSI > 70
Ticker: SPY
Timeframe: Daily
"@ | Out-File -FilePath "Strategy1_RSI.txt" -Encoding UTF8

# Strategy 2
@"
STRATEGY_NAME: MACD_Strategy
Buy on MACD bullish crossover, sell on bearish crossover
Ticker: SPY
Timeframe: Daily
"@ | Out-File -FilePath "Strategy2_MACD.txt" -Encoding UTF8

# Strategy 3
@"
STRATEGY_NAME: BB_Strategy
Buy when price touches lower Bollinger Band, sell at upper BB
Ticker: SPY
Timeframe: Daily
"@ | Out-File -FilePath "Strategy3_BB.txt" -Encoding UTF8
```

### Run Batch Backtester

```powershell
# Go back to project root
cd C:\Users\ahmed\CascadeProjects\moon-dev-ai-agents

# Set PYTHONPATH
$env:PYTHONPATH = "$PWD"

# Run batch backtester
python src/agents/rbi_batch_backtester.py src/data/rbi/my_test/research
```

### Compare Results

```powershell
# After batch backtester finishes
python src/scripts/compare_strategies.py src/data/rbi/my_test/research/GPT-5
```

## Conda Environment on Windows

Make sure you're in the right conda environment:

```powershell
# Activate conda environment
conda activate tflow

# Verify Python location
python --version
where python

# Install any missing packages
pip install backtesting yfinance pandas-ta tabulate termcolor
```

## Common Windows Issues

### Issue 1: "conda: command not found"

**Fix:** Make sure Conda is installed and in your PATH. Try:
```powershell
# If using Anaconda
C:\ProgramData\Anaconda3\Scripts\activate.bat

# If using Miniconda
C:\Users\ahmed\Miniconda3\Scripts\activate.bat
```

### Issue 2: "Execution of scripts is disabled"

**Fix:** Enable script execution (run PowerShell as Administrator):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue 3: Path too long errors

**Fix:** Enable long paths in Windows:
```powershell
# Run as Administrator
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

### Issue 4: "Cannot find path /home/user/..."

**Fix:** Don't use Linux paths. Your path is:
```
C:\Users\ahmed\CascadeProjects\moon-dev-ai-agents
```

NOT `/home/user/TradingAgent`

## Quick Reference Card

Save this for easy access:

```powershell
# === TradingAgent Quick Commands (Windows) ===

# 1. Setup (run once per PowerShell session)
cd C:\Users\ahmed\CascadeProjects\moon-dev-ai-agents
$env:PYTHONPATH = "$PWD"
conda activate tflow

# 2. Run RBI Agent
python src/agents/rbi_agent.py

# 3. Run Batch Backtester
python src/agents/rbi_batch_backtester.py src/data/rbi/my_test/research

# 4. Compare Strategies
python src/scripts/compare_strategies.py

# 5. Run any script (general format)
python src/agents/[script_name].py
python src/scripts/[script_name].py
```

## Testing Your Setup

Create `test_imports.py` in your project root:

```python
# test_imports.py
import sys
print("Python path:")
for p in sys.path:
    print(f"  {p}")

print("\nTrying to import src modules...")

try:
    from src.models.model_factory import ModelFactory
    print("✅ model_factory imported successfully")
except ImportError as e:
    print(f"❌ Failed to import model_factory: {e}")

try:
    from src.agents import rbi_agent
    print("✅ rbi_agent imported successfully")
except ImportError as e:
    print(f"❌ Failed to import rbi_agent: {e}")

print("\n✨ If you see ✅ marks, you're good to go!")
```

Run it:
```powershell
cd C:\Users\ahmed\CascadeProjects\moon-dev-ai-agents
$env:PYTHONPATH = "$PWD"
python test_imports.py
```

If you see ✅ marks, you're all set!

## Alternative: Use VS Code

If using VS Code, add this to `.vscode/settings.json`:

```json
{
    "python.envFile": "${workspaceFolder}/.env",
    "python.analysis.extraPaths": [
        "${workspaceFolder}"
    ],
    "terminal.integrated.env.windows": {
        "PYTHONPATH": "${workspaceFolder}"
    }
}
```

Then VS Code will automatically set PYTHONPATH!

---

Built with love by Moon Dev 🌙
For Windows users! 🪟
