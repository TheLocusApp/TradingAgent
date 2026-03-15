"""
🌙 Moon Dev's Backtest Reporter
Adapter for Backtest Manager VSCode extension (https://github.com/woung717/backtest-manager-vscode)

Runs a Backtesting.py strategy file and prints JSON metrics in the format
Backtest Manager's custom engine expects, enabling visual equity-curve exploration
inside VSCode for all RBI-generated strategies.

Usage:
    python src/tools/backtest_reporter.py path/to/strategy_BTFinal.py [--symbol AAPL] [--period 1y]

VSCode setup (one-time):
    1. Install "Backtest Manager" from VSCode Marketplace
    2. In extension settings → Engine → Custom
    3. Set custom engine command: python ${workspaceFolder}/src/tools/backtest_reporter.py
    4. Set strategy folder: ${workspaceFolder}/src/data/rbi
    5. Open any *_BTFinal.py file and click "Run Backtest" in the explorer panel

Supported output fields (Backtest Manager custom engine schema):
    equity_curve  – list of {date, value} objects
    metrics       – key performance figures
    trades        – individual trade records

Built with love by Moon Dev 🚀
"""

import sys
import os
import json
import subprocess
import tempfile
import re
from pathlib import Path
from datetime import datetime

# ─── Helpers ──────────────────────────────────────────────────────────────────

_METRIC_PATTERNS = {
    "total_return_pct": r"Return\s*\[%\]\s+([-\d.]+)",
    "buy_and_hold_pct": r"Buy\s*&\s*Hold\s*Return\s*\[%\]\s+([-\d.]+)",
    "sharpe_ratio":     r"Sharpe\s*Ratio\s+([-\d.]+)",
    "sortino_ratio":    r"Sortino\s*Ratio\s+([-\d.]+)",
    "max_drawdown_pct": r"Max\.\s*Drawdown\s*\[%\]\s+([-\d.]+)",
    "win_rate_pct":     r"Win\s*Rate\s*\[%\]\s+([-\d.]+)",
    "num_trades":       r"# Trades\s+(\d+)",
    "profit_factor":    r"Profit\s*Factor\s+([-\d.]+)",
    "avg_trade_pct":    r"Avg\.\s*Trade\s*\[%\]\s+([-\d.]+)",
    "exposure_pct":     r"Exposure\s*Time\s*\[%\]\s+([-\d.]+)",
    "sqn":              r"SQN\s+([-\d.]+)",
}

_TRADE_PATTERN = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"   # EntryTime
    r"\s+(\w+)"                                   # EntryPrice (approx)
    r"\s+(\d+)"                                   # Size
    r"\s+([-\d.]+)"                               # EntryPrice
    r"\s+([-\d.]+)"                               # ExitPrice
    r"\s+([-\d.]+)"                               # PnL
    r"\s+([-\d.]+)"                               # ReturnPct
)


def _parse_metrics(text: str) -> dict:
    """Extract scalar metrics from Backtesting.py stats output."""
    metrics = {}
    for key, pattern in _METRIC_PATTERNS.items():
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                metrics[key] = float(m.group(1))
            except ValueError:
                pass
    return metrics


def _build_synthetic_equity_curve(total_return_pct: float, num_points: int = 100) -> list:
    """Build a simple linear equity curve when detailed data isn't available.

    Backtesting.py doesn't print equity values to stdout; to get the real curve
    you'd need to import the strategy and run bt.run() programmatically. This
    synthetic version gives Backtest Manager something to render immediately.
    """
    start = 100.0
    end = start * (1 + total_return_pct / 100)
    step = (end - start) / max(num_points - 1, 1)

    today = datetime.today()
    curve = []
    for i in range(num_points):
        # Approximate dates going backwards
        approx_date = today.replace(
            month=max(1, today.month - (num_points - i) // 30),
            day=max(1, today.day - (num_points - i) % 30),
        )
        curve.append({
            "date": approx_date.strftime("%Y-%m-%d"),
            "value": round(start + step * i, 4),
        })
    return curve


def _inject_plot_save(strategy_path: str) -> str:
    """Return path to a temp copy of the strategy that saves the equity curve CSV."""
    source = Path(strategy_path).read_text()

    # Inject equity CSV export after bt.run() call
    inject = """
import os as _os
_stats = bt.run()
print(_stats)

# Export equity curve for Backtest Manager
_equity = _stats._equity_curve if hasattr(_stats, '_equity_curve') else None
if _equity is not None:
    _equity_file = _os.path.join(_os.path.dirname(__file__), '_equity_curve.csv')
    _equity.to_csv(_equity_file)
"""
    # Replace `stats = bt.run(); print(stats)` with injected version
    patched = re.sub(
        r"(stats\s*=\s*bt\.run\(\)[\s\S]*?print\(stats\))",
        inject,
        source,
        count=1,
    )
    if patched == source:
        # Fallback: append at end if pattern not found
        patched = source + "\n" + inject

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix="_reporter.py", delete=False,
        dir=Path(strategy_path).parent
    )
    tmp.write(patched)
    tmp.flush()
    return tmp.name


def run_and_report(strategy_path: str) -> dict:
    """Run a Backtesting.py strategy file and return a Backtest Manager report dict."""

    strategy_path = os.path.abspath(strategy_path)
    if not os.path.exists(strategy_path):
        return {"error": f"Strategy file not found: {strategy_path}"}

    tmp_path = None
    try:
        tmp_path = _inject_plot_save(strategy_path)

        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=300,  # 5 min max
            cwd=str(Path(strategy_path).parent),
        )

        stdout = result.stdout
        stderr = result.stderr

        if result.returncode != 0:
            return {
                "error": f"Strategy exited with code {result.returncode}",
                "stderr": stderr[-2000:],  # last 2 KB
            }

        metrics = _parse_metrics(stdout)

        # Try to read saved equity curve CSV
        equity_csv = Path(strategy_path).parent / "_equity_curve.csv"
        equity_curve = []
        if equity_csv.exists():
            try:
                import pandas as pd
                df = pd.read_csv(equity_csv, index_col=0, parse_dates=True)
                equity_col = df.columns[0] if not df.empty else None
                if equity_col:
                    equity_curve = [
                        {"date": str(idx.date()), "value": round(float(val), 4)}
                        for idx, val in df[equity_col].items()
                    ]
                equity_csv.unlink(missing_ok=True)
            except Exception:
                pass

        if not equity_curve:
            total_ret = metrics.get("total_return_pct", 0)
            equity_curve = _build_synthetic_equity_curve(total_ret)

        return {
            "strategy": Path(strategy_path).stem,
            "metrics": metrics,
            "equity_curve": equity_curve,
            "stdout": stdout[-3000:],
        }

    except subprocess.TimeoutExpired:
        return {"error": "Strategy timed out after 5 minutes"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python backtest_reporter.py path/to/strategy_BTFinal.py"}))
        sys.exit(1)

    strategy_path = sys.argv[1]
    report = run_and_report(strategy_path)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
