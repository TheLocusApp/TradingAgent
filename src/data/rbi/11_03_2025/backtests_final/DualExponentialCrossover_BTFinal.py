import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import talib
from pathlib import Path

# 🌙 Moon Dev Debug: Robust data loader with friendly fallbacks
def load_data(csv_name='SPY-60m.csv'):
    candidates = []

    # Try path relative to this file (if available)
    try:
        file_base = Path(__file__).resolve()
        candidates.append(file_base.parents[2] / csv_name)
        candidates.append(file_base.parent / csv_name)
        print(f"🌙 Moon Dev Debug: __file__ detected at {file_base}")
    except NameError:
        print("🌙 Moon Dev Debug: __file__ not available, using CWD and parent paths ✨")

    # Try current working directory and its parents
    cwd = Path.cwd()
    candidates.append(cwd / csv_name)
    candidates.append(cwd.parent / csv_name)
    candidates.append(cwd.parent.parent / csv_name)