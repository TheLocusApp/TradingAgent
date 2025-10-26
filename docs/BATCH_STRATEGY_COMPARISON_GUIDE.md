# Running and Comparing Multiple Strategies Side by Side

## Overview

Moon Dev's TradingAgent includes a powerful batch backtesting system that allows you to:
1. Run multiple strategies automatically
2. Save results for each strategy
3. Compare performance side by side
4. Visualize results in a summary dashboard

## Method 1: Using the RBI Batch Backtester (Easiest)

### Step 1: Create Multiple Strategy Descriptions

Create `.txt` files in your research folder, one for each strategy you want to test:

```bash
cd /home/user/TradingAgent/src/data/rbi/03_14_2025/research

# Or create a new dated folder
mkdir -p src/data/rbi/$(date +%m_%d_%Y)/research
cd src/data/rbi/$(date +%m_%d_%Y)/research
```

Create strategy files:

**`RSI_Mean_Reversion_strategy.txt`:**
```text
STRATEGY_NAME: RSI_Mean_Reversion

Entry Rules:
- RSI(14) crosses below 30 (oversold)
- Volume > 1.2x average volume
- Price is above 200-day SMA (uptrend filter)

Exit Rules:
- RSI crosses above 50
- Stop loss: 5% from entry
- Profit target: 10% from entry

Ticker: SPY
Timeframe: Daily
Initial Capital: $10,000
```

**`MACD_Momentum_strategy.txt`:**
```text
STRATEGY_NAME: MACD_Momentum

Entry Rules:
- MACD line crosses above signal line
- Price is above 50-day SMA
- ADX > 25 (strong trend)

Exit Rules:
- MACD line crosses below signal line
- Stop loss: 3% from entry

Ticker: SPY
Timeframe: Daily
Initial Capital: $10,000
```

**`BB_Reversal_strategy.txt`:**
```text
STRATEGY_NAME: BB_Reversal

Entry Rules:
- Price touches lower Bollinger Band (2 std dev)
- RSI < 35
- Volume spike (>1.5x average)

Exit Rules:
- Price reaches middle Bollinger Band
- RSI > 65
- Stop loss: 4% from entry

Ticker: QQQ
Timeframe: Daily
Initial Capital: $10,000
```

### Step 2: Run the Batch Backtester

```bash
cd /home/user/TradingAgent

# Run all strategies in a folder
python src/agents/rbi_batch_backtester.py /path/to/research/folder

# Or run a single file
python src/agents/rbi_batch_backtester.py --file /path/to/strategy.txt
```

**What happens:**
1. AI reads each strategy description
2. Generates Python backtest code for each one
3. Fixes any package issues automatically
4. Executes each backtest
5. Saves results to `GPT-5/` subfolder within research directory
6. Prints full statistics to terminal

### Step 3: View Results

Results are saved in the `GPT-5/` folder:

```
research/
├── RSI_Mean_Reversion_strategy.txt
├── MACD_Momentum_strategy.txt
├── BB_Reversal_strategy.txt
└── GPT-5/
    ├── RSI_Mean_Reversion_BT.py          # Generated code
    ├── RSI_Mean_Reversion_stdout.txt     # Results
    ├── RSI_Mean_Reversion_stderr.txt     # Errors (if any)
    ├── RSI_Mean_Reversion_results.json   # Structured data
    ├── MACD_Momentum_BT.py
    ├── MACD_Momentum_stdout.txt
    ├── MACD_Momentum_results.json
    ├── BB_Reversal_BT.py
    └── ... (etc)
```

## Method 2: Manual Batch Backtesting

If you prefer more control, run strategies manually and collect results:

Create `src/scripts/batch_backtest_runner.py`:

```python
"""
Batch Strategy Runner
Runs multiple pre-written strategies and compares results
"""

import yfinance as yf
from backtesting import Backtest, Strategy
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import json
from pathlib import Path

# Import your strategies
import sys
sys.path.append('src/strategies/stocks')

class RSIStrategy(Strategy):
    rsi_period = 14
    rsi_lower = 30
    rsi_upper = 50

    def init(self):
        self.rsi = self.I(ta.rsi, self.data.Close, self.rsi_period)

    def next(self):
        if self.rsi[-1] < self.rsi_lower and not self.position:
            self.buy()
        elif self.rsi[-1] > self.rsi_upper and self.position:
            self.position.close()

class MACDStrategy(Strategy):
    def init(self):
        close = self.data.Close
        macd = ta.macd(close)
        self.macd = self.I(lambda x: x, macd['MACD_12_26_9'])
        self.signal = self.I(lambda x: x, macd['MACDs_12_26_9'])

    def next(self):
        if self.macd[-1] > self.signal[-1] and self.macd[-2] <= self.signal[-2]:
            if not self.position:
                self.buy()
        elif self.macd[-1] < self.signal[-1] and self.macd[-2] >= self.signal[-2]:
            if self.position:
                self.position.close()

class BollingerStrategy(Strategy):
    bb_period = 20
    bb_std = 2

    def init(self):
        close = self.data.Close
        bb = ta.bbands(close, length=self.bb_period, std=self.bb_std)
        self.bb_lower = self.I(lambda x: x, bb[f'BBL_{self.bb_period}_{self.bb_std}.0'])
        self.bb_upper = self.I(lambda x: x, bb[f'BBU_{self.bb_period}_{self.bb_std}.0'])

    def next(self):
        price = self.data.Close[-1]
        if price <= self.bb_lower[-1] and not self.position:
            self.buy()
        elif price >= self.bb_upper[-1] and self.position:
            self.position.close()

def run_all_strategies(ticker="SPY", start_date="2020-01-01", end_date="2024-01-01"):
    """Run all strategies and collect results"""

    print(f"\n{'='*80}")
    print(f"Running Multiple Strategies on {ticker}")
    print(f"Period: {start_date} to {end_date}")
    print(f"{'='*80}\n")

    # Download data once
    print(f"Downloading data for {ticker}...")
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)

    if data.empty:
        print("No data available")
        return

    # Define strategies to test
    strategies = {
        "RSI Mean Reversion": RSIStrategy,
        "MACD Momentum": MACDStrategy,
        "Bollinger Bands": BollingerStrategy
    }

    results = []

    # Run each strategy
    for name, strategy_class in strategies.items():
        print(f"\nRunning: {name}")
        print("-" * 60)

        try:
            bt = Backtest(
                data,
                strategy_class,
                cash=10000,
                commission=.001,
                exclusive_orders=True
            )

            stats = bt.run()

            # Extract key metrics
            result = {
                'strategy': name,
                'return': stats['Return [%]'],
                'buy_hold_return': stats['Buy & Hold Return [%]'],
                'sharpe': stats['Sharpe Ratio'],
                'max_drawdown': stats['Max. Drawdown [%]'],
                'win_rate': stats['Win Rate [%]'],
                'num_trades': stats['# Trades'],
                'avg_trade': stats['Avg. Trade [%]'],
                'final_equity': stats['Equity Final [$]']
            }

            results.append(result)

            # Print summary
            print(f"✅ {name}:")
            print(f"   Return: {result['return']:.2f}%")
            print(f"   Sharpe: {result['sharpe']:.2f}")
            print(f"   Max DD: {result['max_drawdown']:.2f}%")
            print(f"   Win Rate: {result['win_rate']:.2f}%")
            print(f"   Trades: {result['num_trades']}")

        except Exception as e:
            print(f"❌ Error with {name}: {str(e)}")
            results.append({
                'strategy': name,
                'error': str(e)
            })

    return results

def print_comparison_table(results):
    """Print a nice comparison table"""

    print(f"\n\n{'='*100}")
    print("STRATEGY COMPARISON SUMMARY")
    print(f"{'='*100}\n")

    # Header
    print(f"{'Strategy':<25} {'Return':<12} {'Sharpe':<10} {'Max DD':<12} {'Win Rate':<12} {'Trades':<10}")
    print("-" * 100)

    # Sort by return
    sorted_results = sorted(results, key=lambda x: x.get('return', -999), reverse=True)

    # Print each strategy
    for result in sorted_results:
        if 'error' in result:
            print(f"{result['strategy']:<25} ERROR: {result['error']}")
        else:
            print(f"{result['strategy']:<25} "
                  f"{result['return']:>10.2f}%  "
                  f"{result['sharpe']:>8.2f}  "
                  f"{result['max_drawdown']:>10.2f}%  "
                  f"{result['win_rate']:>10.2f}%  "
                  f"{result['num_trades']:>8}")

    print("-" * 100)

    # Find best performer
    best = max(sorted_results, key=lambda x: x.get('return', -999))
    if 'error' not in best:
        print(f"\n🏆 Best Performer: {best['strategy']}")
        print(f"   Return: {best['return']:.2f}%")
        print(f"   Sharpe: {best['sharpe']:.2f}")
        print(f"   Max Drawdown: {best['max_drawdown']:.2f}%")

def save_results_json(results, filename="strategy_comparison.json"):
    """Save results to JSON for later analysis"""

    output_dir = Path("src/data/strategy_comparisons")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"{filename.replace('.json', '')}_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")
    return output_file

# Run the comparison
if __name__ == "__main__":
    # Test on multiple tickers
    tickers = ["SPY", "QQQ", "AAPL"]

    all_results = {}

    for ticker in tickers:
        print(f"\n\n{'#'*100}")
        print(f"Testing strategies on {ticker}")
        print(f"{'#'*100}")

        results = run_all_strategies(
            ticker=ticker,
            start_date="2020-01-01",
            end_date="2024-01-01"
        )

        all_results[ticker] = results

        print_comparison_table(results)

    # Save combined results
    save_results_json(all_results, "multi_ticker_comparison.json")

    print("\n\n🎉 Batch backtesting complete!")
```

Run it:

```bash
python src/scripts/batch_backtest_runner.py
```

## Method 3: Creating a Results Dashboard

Create `src/scripts/strategy_comparison_dashboard.py`:

```python
"""
Strategy Comparison Dashboard
Visualizes results from multiple strategy backtests
"""

import json
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

def load_batch_results(results_dir):
    """Load all results JSON files from a directory"""

    results_path = Path(results_dir)
    json_files = list(results_path.glob("*_results.json"))

    all_results = []

    for json_file in json_files:
        with open(json_file, 'r') as f:
            data = json.load(f)

            # Extract strategy name from filename
            strategy_name = json_file.stem.replace('_results', '')

            # Parse stdout for stats (if available)
            stdout = data.get('stdout', '')

            # Add to results
            all_results.append({
                'strategy': strategy_name,
                'success': data.get('success', False),
                'execution_time': data.get('execution_time', 0),
                'output': stdout
            })

    return all_results

def create_comparison_dashboard(results):
    """Create visual dashboard comparing strategies"""

    print("\n" + "="*80)
    print("STRATEGY PERFORMANCE DASHBOARD")
    print("="*80 + "\n")

    # Summary table
    df = pd.DataFrame(results)

    print(df.to_string(index=False))

    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Strategy Comparison Dashboard', fontsize=16)

    # Example visualizations (customize based on your data)
    strategies = [r['strategy'] for r in results]

    # 1. Success rate
    success_count = sum(1 for r in results if r['success'])
    failure_count = len(results) - success_count

    axes[0, 0].bar(['Success', 'Failed'], [success_count, failure_count], color=['green', 'red'])
    axes[0, 0].set_title('Backtest Success Rate')
    axes[0, 0].set_ylabel('Count')

    # 2. Execution time
    exec_times = [r['execution_time'] for r in results]
    axes[0, 1].barh(strategies, exec_times, color='skyblue')
    axes[0, 1].set_title('Execution Time (seconds)')
    axes[0, 1].set_xlabel('Seconds')

    # 3. & 4. - Add more visualizations based on parsed results

    plt.tight_layout()

    # Save figure
    output_file = Path("src/data/strategy_comparisons/dashboard.png")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')

    print(f"\n📊 Dashboard saved to: {output_file}")

    plt.show()

# Example usage
if __name__ == "__main__":
    # Load results from batch backtester output
    results_dir = "src/data/rbi/03_14_2025/research/GPT-5"

    results = load_batch_results(results_dir)

    if results:
        create_comparison_dashboard(results)
    else:
        print("No results found. Run the batch backtester first!")
```

## Quick Start: Complete Workflow

### 1. Create Strategies

```bash
# Create research folder
mkdir -p src/data/rbi/my_strategies/research
cd src/data/rbi/my_strategies/research

# Create 3 strategy files
cat > Strategy1_RSI.txt << 'EOF'
STRATEGY_NAME: RSI_Strategy
Buy when RSI < 30, sell when RSI > 70
Ticker: SPY
EOF

cat > Strategy2_MACD.txt << 'EOF'
STRATEGY_NAME: MACD_Strategy
Buy on MACD bullish crossover, sell on bearish crossover
Ticker: SPY
EOF

cat > Strategy3_BB.txt << 'EOF'
STRATEGY_NAME: BB_Strategy
Buy when price touches lower BB, sell at upper BB
Ticker: SPY
EOF
```

### 2. Run Batch Backtest

```bash
cd /home/user/TradingAgent
python src/agents/rbi_batch_backtester.py src/data/rbi/my_strategies/research
```

### 3. View Results

```bash
# View all stdout files (the actual results)
cat src/data/rbi/my_strategies/research/GPT-5/*_stdout.txt

# Or view JSON results
python -c "
import json
from pathlib import Path
for f in Path('src/data/rbi/my_strategies/research/GPT-5').glob('*_results.json'):
    with open(f) as file:
        data = json.load(file)
        print(f'\n{f.stem}:')
        print(f\"Success: {data.get('success')}\")
        print(f\"Time: {data.get('execution_time')}s\")
"
```

### 4. Create Comparison Table

Create `src/scripts/quick_compare.py`:

```python
"""Quick comparison of batch backtest results"""

import json
from pathlib import Path
from tabulate import tabulate  # pip install tabulate

def compare_results(results_dir):
    results = []

    for json_file in Path(results_dir).glob("*_results.json"):
        with open(json_file) as f:
            data = json.load(f)

        strategy = json_file.stem.replace('_results', '')

        results.append({
            'Strategy': strategy,
            'Success': '✅' if data.get('success') else '❌',
            'Time (s)': f"{data.get('execution_time', 0):.2f}"
        })

    print(tabulate(results, headers='keys', tablefmt='grid'))

# Usage
compare_results("src/data/rbi/my_strategies/research/GPT-5")
```

## Tips for Best Results

1. **Use consistent parameters**: Same initial capital, same ticker, same timeframe
2. **Test on same data period**: Ensures fair comparison
3. **Include multiple market conditions**: Bull, bear, and sideways markets
4. **Document assumptions**: Note any special conditions in strategy files
5. **Save everything**: Keep all output files for later analysis

## Troubleshooting

**Issue**: Batch backtester fails on some strategies
- Check `*_stderr.txt` files for errors
- The system will auto-retry with debug fixes
- If still failing, manually review generated code

**Issue**: Can't find results
- Check the `GPT-5/` subfolder within your research directory
- Results are saved next to the generated Python files

**Issue**: Want to re-run a single strategy
- Use `--file` flag: `python src/agents/rbi_batch_backtester.py --file path/to/strategy.txt`

## Next Steps

- Check out `BACKTESTING_STOCKS_GUIDE.md` for individual strategy development
- See `DEEPSEEK_QWEN_TRADING_GUIDE.md` for AI-powered analysis
- Review generated code in `GPT-5/` folder and customize as needed

Built with love by Moon Dev 🌙
