"""
🌙 Moon Dev's Strategy Comparison Tool
Compare multiple backtest results side by side

Usage:
    python src/scripts/compare_strategies.py [results_directory]

If no directory specified, uses most recent research folder
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from termcolor import cprint
from tabulate import tabulate
import re

def find_latest_research_folder():
    """Find the most recent research folder with results"""
    rbi_data_path = Path("src/data/rbi")

    if not rbi_data_path.exists():
        return None

    # Look for dated folders
    date_folders = [f for f in rbi_data_path.iterdir() if f.is_dir() and not f.name.startswith('.')]

    for folder in sorted(date_folders, reverse=True):
        research_path = folder / "research" / "GPT-5"
        if research_path.exists():
            json_files = list(research_path.glob("*_results.json"))
            if json_files:
                return research_path

    return None

def parse_backtest_stats(stdout_text):
    """Parse backtesting.py output to extract key metrics"""

    stats = {}

    if not stdout_text:
        return stats

    # Common patterns in backtesting.py output
    patterns = {
        'return': r"Return\s+(?:\[%\])?\s*([-\d.]+)",
        'buy_hold_return': r"Buy & Hold Return\s+(?:\[%\])?\s*([-\d.]+)",
        'sharpe': r"Sharpe Ratio\s+([-\d.]+)",
        'max_drawdown': r"Max\.? Drawdown\s+(?:\[%\])?\s*([-\d.]+)",
        'win_rate': r"Win Rate\s+(?:\[%\])?\s*([-\d.]+)",
        'num_trades': r"# Trades\s+(\d+)",
        'avg_trade': r"Avg\.? Trade\s+(?:\[%\])?\s*([-\d.]+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, stdout_text, re.IGNORECASE)
        if match:
            try:
                stats[key] = float(match.group(1))
            except:
                stats[key] = match.group(1)

    return stats

def load_results_from_directory(results_dir):
    """Load all backtest results from a directory"""

    results_path = Path(results_dir)

    if not results_path.exists():
        cprint(f"❌ Directory not found: {results_dir}", "red")
        return []

    json_files = list(results_path.glob("*_results.json"))

    if not json_files:
        cprint(f"❌ No results found in: {results_dir}", "red")
        return []

    cprint(f"\n📊 Found {len(json_files)} backtest results\n", "cyan")

    all_results = []

    for json_file in sorted(json_files):
        with open(json_file, 'r') as f:
            data = json.load(f)

        # Get strategy name from filename
        strategy_name = json_file.stem.replace('_results', '').replace('_BT', '')

        # Parse stats from stdout
        stdout = data.get('stdout', '')
        stats = parse_backtest_stats(stdout)

        result = {
            'strategy': strategy_name,
            'success': data.get('success', False),
            'execution_time': data.get('execution_time', 0),
            **stats  # Add parsed stats
        }

        all_results.append(result)

    return all_results

def print_comparison_table(results):
    """Print a beautiful comparison table"""

    if not results:
        cprint("No results to display", "yellow")
        return

    # Prepare table data
    table_data = []

    for result in results:
        if not result.get('success'):
            row = [
                result['strategy'],
                '❌ FAILED',
                '-',
                '-',
                '-',
                '-',
                '-'
            ]
        else:
            row = [
                result['strategy'],
                '✅ Success',
                f"{result.get('return', 0):.2f}%" if 'return' in result else 'N/A',
                f"{result.get('sharpe', 0):.2f}" if 'sharpe' in result else 'N/A',
                f"{result.get('max_drawdown', 0):.2f}%" if 'max_drawdown' in result else 'N/A',
                f"{result.get('win_rate', 0):.2f}%" if 'win_rate' in result else 'N/A',
                str(result.get('num_trades', 'N/A'))
            ]

        table_data.append(row)

    headers = ['Strategy', 'Status', 'Return', 'Sharpe', 'Max DD', 'Win Rate', 'Trades']

    cprint("\n" + "="*100, "cyan")
    cprint("STRATEGY COMPARISON RESULTS", "cyan", attrs=['bold'])
    cprint("="*100 + "\n", "cyan")

    print(tabulate(table_data, headers=headers, tablefmt='fancy_grid'))

    # Find best performers
    successful_results = [r for r in results if r.get('success') and 'return' in r]

    if successful_results:
        best_return = max(successful_results, key=lambda x: x.get('return', -999))
        best_sharpe = max(successful_results, key=lambda x: x.get('sharpe', -999))
        best_winrate = max(successful_results, key=lambda x: x.get('win_rate', 0))

        cprint("\n" + "="*100, "green")
        cprint("🏆 BEST PERFORMERS", "green", attrs=['bold'])
        cprint("="*100, "green")

        print(f"\n📈 Highest Return:     {best_return['strategy']:<30} ({best_return.get('return', 0):.2f}%)")
        print(f"⚡ Best Sharpe Ratio:  {best_sharpe['strategy']:<30} ({best_sharpe.get('sharpe', 0):.2f})")
        print(f"🎯 Highest Win Rate:   {best_winrate['strategy']:<30} ({best_winrate.get('win_rate', 0):.2f}%)")

        cprint("\n" + "="*100, "green")

    # Summary stats
    total = len(results)
    successful = sum(1 for r in results if r.get('success'))
    failed = total - successful

    cprint(f"\n📊 Summary: {successful}/{total} strategies successful, {failed} failed\n", "cyan")

def print_detailed_results(results):
    """Print detailed results for each strategy"""

    cprint("\n" + "="*100, "yellow")
    cprint("DETAILED STRATEGY RESULTS", "yellow", attrs=['bold'])
    cprint("="*100 + "\n", "yellow")

    for i, result in enumerate(results, 1):
        cprint(f"\n{i}. {result['strategy']}", "cyan", attrs=['bold'])
        cprint("-" * 60, "cyan")

        if not result.get('success'):
            cprint("   Status: ❌ Failed", "red")
        else:
            cprint("   Status: ✅ Success", "green")

            metrics = [
                ('Return', 'return', '%'),
                ('Buy & Hold Return', 'buy_hold_return', '%'),
                ('Sharpe Ratio', 'sharpe', ''),
                ('Max Drawdown', 'max_drawdown', '%'),
                ('Win Rate', 'win_rate', '%'),
                ('Number of Trades', 'num_trades', ''),
                ('Avg Trade', 'avg_trade', '%'),
            ]

            for label, key, suffix in metrics:
                if key in result:
                    value = result[key]
                    if isinstance(value, float):
                        print(f"   {label:<20}: {value:>10.2f}{suffix}")
                    else:
                        print(f"   {label:<20}: {value:>10}{suffix}")

        print(f"   Execution Time      : {result.get('execution_time', 0):.2f}s")

def export_to_csv(results, output_file="strategy_comparison.csv"):
    """Export results to CSV for further analysis"""

    import csv

    if not results:
        return

    output_path = Path("src/data/strategy_comparisons") / output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine all possible fields
    all_fields = set()
    for result in results:
        all_fields.update(result.keys())

    fields = ['strategy', 'success', 'return', 'sharpe', 'max_drawdown', 'win_rate',
              'num_trades', 'avg_trade', 'execution_time']

    # Add any extra fields
    for field in all_fields:
        if field not in fields:
            fields.append(field)

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for result in results:
            row = {field: result.get(field, '') for field in fields}
            writer.writerow(row)

    cprint(f"\n💾 Results exported to: {output_path}", "green")

def main():
    cprint("\n🌙 Moon Dev's Strategy Comparison Tool", "cyan", attrs=['bold'])
    cprint("="*100 + "\n", "cyan")

    # Get results directory
    if len(sys.argv) > 1:
        results_dir = Path(sys.argv[1])
    else:
        cprint("🔍 Searching for latest results...", "yellow")
        results_dir = find_latest_research_folder()

        if results_dir is None:
            cprint("❌ No results found. Please specify a directory or run batch backtester first.", "red")
            cprint("\nUsage: python src/scripts/compare_strategies.py [results_directory]", "yellow")
            return

        cprint(f"✅ Found results in: {results_dir}\n", "green")

    # Load results
    results = load_results_from_directory(results_dir)

    if not results:
        return

    # Print comparison table
    print_comparison_table(results)

    # Ask if user wants detailed view
    print("\n" + "="*100)
    try:
        choice = input("\n📋 Show detailed results? (y/n): ").strip().lower()
        if choice == 'y':
            print_detailed_results(results)

        choice = input("\n💾 Export to CSV? (y/n): ").strip().lower()
        if choice == 'y':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_to_csv(results, f"comparison_{timestamp}.csv")
    except KeyboardInterrupt:
        print("\n")

    cprint("\n✨ Comparison complete! 🚀\n", "green", attrs=['bold'])

if __name__ == "__main__":
    main()
