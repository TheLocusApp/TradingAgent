# Stock Backtesting Guide for TradingAgent

## Overview

This comprehensive guide covers stock backtesting in TradingAgent using the existing backtesting infrastructure. The system uses `backtesting.py` library with `pandas_ta` for technical indicators and supports both manual strategy coding and AI-generated strategies via the RBI Agent.

## Prerequisites

1. Conda environment `tflow` activated
2. Python 3.8+
3. Basic understanding of trading strategies

## Quick Start

### Step 1: Activate Environment

```bash
conda activate tflow
```

### Step 2: Install Required Libraries (if not already installed)

```bash
# Core backtesting library
pip install backtesting

# Data sources
pip install yfinance pandas-datareader alpaca-trade-api

# Technical indicators (DO NOT use backtesting.py's built-in indicators)
pip install pandas-ta ta-lib

# Data processing
pip install pandas numpy

# Visualization
pip install matplotlib plotly mplfinance

# Update requirements.txt
pip freeze > requirements.txt
```

### Step 3: Verify Installation

```bash
python -c "import backtesting; print('backtesting.py version:', backtesting.__version__)"
python -c "import pandas_ta as ta; print('pandas_ta installed successfully')"
python -c "import yfinance as yf; print('yfinance installed successfully')"
```

## Stock Data Sources

### Option 1: Yahoo Finance (Free, Most Popular)

```python
import yfinance as yf

# Download stock data
ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01", end="2024-01-01")

# Download multiple tickers
tickers = ["AAPL", "MSFT", "GOOGL"]
data = yf.download(tickers, start="2020-01-01", end="2024-01-01")

# Get different timeframes
data_1h = yf.download(ticker, start="2023-01-01", interval="1h")
data_5m = yf.download(ticker, start="2024-01-01", period="5d", interval="5m")
```

### Option 2: Alpaca (Free API for US Stocks)

```python
from alpaca_trade_api.rest import REST
import pandas as pd

# Get API keys from alpaca.markets
api_key = "YOUR_ALPACA_KEY"
api_secret = "YOUR_ALPACA_SECRET"
base_url = "https://paper-api.alpaca.markets"  # Paper trading

api = REST(api_key, api_secret, base_url)

# Get historical bars
barset = api.get_bars(
    "AAPL",
    "1Day",
    start="2020-01-01",
    end="2024-01-01"
).df

# Convert to format for backtesting.py
data = barset.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})
```

### Option 3: CSV Files (Historical Data)

```python
import pandas as pd

# Load from CSV
data = pd.read_csv('path/to/stock_data.csv', index_col='Date', parse_dates=True)

# Ensure proper column names
data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
```

## Method 1: Manual Strategy Development

### Example 1: Simple Moving Average Crossover

Create `src/strategies/stocks/sma_crossover.py`:

```python
import yfinance as yf
from backtesting import Backtest, Strategy
import pandas_ta as ta

class SMAStrategy(Strategy):
    """
    Simple Moving Average Crossover Strategy
    Buy when fast SMA crosses above slow SMA
    Sell when fast SMA crosses below slow SMA
    """

    # Strategy parameters (can be optimized)
    fast_period = 10
    slow_period = 30

    def init(self):
        """Initialize indicators"""
        # Calculate SMAs using pandas_ta
        close = self.data.Close
        self.fast_sma = self.I(ta.sma, close, self.fast_period)
        self.slow_sma = self.I(ta.sma, close, self.slow_period)

    def next(self):
        """Execute on each bar"""
        # Crossover: fast SMA crosses above slow SMA
        if self.fast_sma[-1] > self.slow_sma[-1] and self.fast_sma[-2] <= self.slow_sma[-2]:
            if not self.position:
                self.buy()

        # Crossunder: fast SMA crosses below slow SMA
        elif self.fast_sma[-1] < self.slow_sma[-1] and self.fast_sma[-2] >= self.slow_sma[-2]:
            if self.position:
                self.position.close()

# Download data
ticker = "SPY"
data = yf.download(ticker, start="2020-01-01", end="2024-01-01")

# Run backtest
bt = Backtest(data, SMAStrategy, cash=10000, commission=.001)
stats = bt.run()

# Print results
print(stats)
print(f"\nReturn: {stats['Return [%]']:.2f}%")
print(f"Sharpe Ratio: {stats['Sharpe Ratio']:.2f}")
print(f"Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
print(f"Win Rate: {stats['Win Rate [%]']:.2f}%")

# Plot results
bt.plot()
```

### Example 2: RSI Mean Reversion Strategy

Create `src/strategies/stocks/rsi_mean_reversion.py`:

```python
import yfinance as yf
from backtesting import Backtest, Strategy
import pandas_ta as ta

class RSIMeanReversion(Strategy):
    """
    RSI Mean Reversion Strategy
    Buy when RSI < 30 (oversold)
    Sell when RSI > 70 (overbought)
    """

    rsi_period = 14
    rsi_lower = 30
    rsi_upper = 70

    def init(self):
        """Initialize RSI indicator"""
        close = self.data.Close
        self.rsi = self.I(ta.rsi, close, self.rsi_period)

    def next(self):
        """Execute trading logic"""
        # Buy when oversold
        if self.rsi[-1] < self.rsi_lower:
            if not self.position:
                self.buy()

        # Sell when overbought
        elif self.rsi[-1] > self.rsi_upper:
            if self.position:
                self.position.close()

# Download data
data = yf.download("TSLA", start="2020-01-01", end="2024-01-01")

# Run backtest
bt = Backtest(data, RSIMeanReversion, cash=10000, commission=.001)
stats = bt.run()

print(stats)
bt.plot()
```

### Example 3: Multi-Indicator Strategy

Create `src/strategies/stocks/multi_indicator.py`:

```python
import yfinance as yf
from backtesting import Backtest, Strategy
import pandas_ta as ta

class MultiIndicatorStrategy(Strategy):
    """
    Combines RSI, MACD, and Bollinger Bands
    Entry: RSI oversold + MACD bullish crossover + price near lower BB
    Exit: RSI overbought or MACD bearish crossover
    """

    # Parameters
    rsi_period = 14
    bb_period = 20
    bb_std = 2

    def init(self):
        """Initialize all indicators"""
        close = self.data.Close

        # RSI
        self.rsi = self.I(ta.rsi, close, self.rsi_period)

        # MACD
        macd_data = ta.macd(close)
        self.macd = self.I(lambda x: x, macd_data['MACD_12_26_9'])
        self.signal = self.I(lambda x: x, macd_data['MACDs_12_26_9'])

        # Bollinger Bands
        bb = ta.bbands(close, length=self.bb_period, std=self.bb_std)
        self.bb_lower = self.I(lambda x: x, bb[f'BBL_{self.bb_period}_{self.bb_std}.0'])
        self.bb_upper = self.I(lambda x: x, bb[f'BBU_{self.bb_period}_{self.bb_std}.0'])

    def next(self):
        """Execute strategy logic"""
        price = self.data.Close[-1]

        # Buy conditions
        rsi_oversold = self.rsi[-1] < 30
        macd_bullish = self.macd[-1] > self.signal[-1]
        near_lower_bb = price <= self.bb_lower[-1] * 1.02  # Within 2% of lower BB

        if rsi_oversold and macd_bullish and near_lower_bb:
            if not self.position:
                self.buy()

        # Sell conditions
        rsi_overbought = self.rsi[-1] > 70
        macd_bearish = self.macd[-1] < self.signal[-1]

        if rsi_overbought or macd_bearish:
            if self.position:
                self.position.close()

# Download data
data = yf.download("NVDA", start="2020-01-01", end="2024-01-01")

# Run backtest
bt = Backtest(data, MultiIndicatorStrategy, cash=10000, commission=.001)
stats = bt.run()

print(stats)
bt.plot()
```

## Method 2: AI-Generated Strategies (RBI Agent)

The RBI (Research-Backtest-Implement) Agent can automatically generate backtests from YouTube videos, PDFs, or text descriptions.

### Step 1: Create Ideas File

Create or edit `src/data/rbi/ideas.txt`:

```text
# Stock trading strategy ideas (one per line)
# Lines starting with # are ignored

# From YouTube videos
https://www.youtube.com/watch?v=example_macd_strategy

# From text descriptions
Buy when 20-day SMA crosses above 50-day SMA and volume is 1.5x average, sell when it crosses below

# From trading concepts
VWAP reversal strategy for intraday trading on liquid stocks

# Momentum strategy
Buy stocks with RSI > 50 and ADX > 25, indicating strong upward momentum
```

### Step 2: Run RBI Agent

```bash
cd /home/user/TradingAgent
python src/agents/rbi_agent.py
```

The RBI Agent will:
1. Read each idea from `ideas.txt`
2. Use AI (DeepSeek/GPT-5/Claude) to analyze the strategy
3. Generate Python backtesting code
4. Fix any errors automatically
5. Execute the backtest
6. Save results to `src/data/rbi/[date]/`

### Step 3: Review Generated Strategies

Generated backtests are saved in date-based folders:

```
src/data/rbi/
├── 03_14_2025/
│   ├── research/           # AI analysis of strategies
│   ├── backtests/          # Initial generated code
│   ├── backtests_final/    # Debugged, working code
│   └── charts/             # Performance charts
└── ideas.txt
```

You can review and modify the generated strategies in `backtests_final/`.

## Parameter Optimization

Optimize strategy parameters to find the best combination:

```python
import yfinance as yf
from backtesting import Backtest, Strategy
import pandas_ta as ta

class OptimizableRSI(Strategy):
    rsi_period = 14
    rsi_lower = 30
    rsi_upper = 70

    def init(self):
        self.rsi = self.I(ta.rsi, self.data.Close, self.rsi_period)

    def next(self):
        if self.rsi[-1] < self.rsi_lower:
            if not self.position:
                self.buy()
        elif self.rsi[-1] > self.rsi_upper:
            if self.position:
                self.position.close()

# Download data
data = yf.download("AAPL", start="2020-01-01", end="2024-01-01")

# Run backtest
bt = Backtest(data, OptimizableRSI, cash=10000, commission=.001)

# Optimize parameters
stats = bt.optimize(
    rsi_period=range(10, 30, 2),
    rsi_lower=range(20, 40, 5),
    rsi_upper=range(60, 80, 5),
    maximize='Sharpe Ratio',
    constraint=lambda p: p.rsi_lower < p.rsi_upper  # Ensure lower < upper
)

print(stats)
print(f"\nBest Parameters:")
print(f"RSI Period: {stats._strategy.rsi_period}")
print(f"RSI Lower: {stats._strategy.rsi_lower}")
print(f"RSI Upper: {stats._strategy.rsi_upper}")
```

## Advanced Techniques

### 1. Position Sizing

```python
class PositionSizedStrategy(Strategy):
    risk_per_trade = 0.02  # Risk 2% per trade

    def init(self):
        close = self.data.Close
        self.sma20 = self.I(ta.sma, close, 20)
        self.sma50 = self.I(ta.sma, close, 50)

    def next(self):
        # Calculate position size based on ATR stop loss
        atr = ta.atr(self.data.High, self.data.Low, self.data.Close, 14).iloc[-1]
        stop_distance = 2 * atr
        risk_amount = self.equity * self.risk_per_trade
        shares = int(risk_amount / stop_distance)

        if self.sma20[-1] > self.sma50[-1]:
            if not self.position:
                self.buy(size=shares)
        elif self.sma20[-1] < self.sma50[-1]:
            if self.position:
                self.position.close()
```

### 2. Stop Loss and Take Profit

```python
class StopLossTakeProfit(Strategy):
    stop_loss_pct = 0.05  # 5% stop loss
    take_profit_pct = 0.10  # 10% take profit

    def init(self):
        close = self.data.Close
        self.sma = self.I(ta.sma, close, 20)
        self.entry_price = 0

    def next(self):
        # Entry logic
        if self.data.Close[-1] > self.sma[-1]:
            if not self.position:
                self.buy()
                self.entry_price = self.data.Close[-1]

        # Exit logic
        if self.position:
            current_price = self.data.Close[-1]
            pnl_pct = (current_price - self.entry_price) / self.entry_price

            # Stop loss hit
            if pnl_pct <= -self.stop_loss_pct:
                self.position.close()

            # Take profit hit
            elif pnl_pct >= self.take_profit_pct:
                self.position.close()
```

### 3. Multiple Timeframe Analysis

```python
import yfinance as yf
import pandas as pd
from backtesting import Backtest, Strategy
import pandas_ta as ta

# Download multiple timeframes
ticker = "SPY"
daily = yf.download(ticker, start="2020-01-01", end="2024-01-01", interval="1d")
hourly = yf.download(ticker, start="2023-01-01", end="2024-01-01", interval="1h")

class MultiTimeframeStrategy(Strategy):
    """Trade hourly based on daily trend"""

    def init(self):
        # Hourly indicators
        self.hourly_rsi = self.I(ta.rsi, self.data.Close, 14)

        # Would need to merge daily data into hourly bars
        # This is a simplified example

    def next(self):
        # Only take longs if daily trend is up
        # Only take shorts if daily trend is down
        # Use hourly RSI for entry timing
        pass

# In practice, you'd align the timeframes properly
```

### 4. Sector Rotation Strategy

```python
import yfinance as yf
from backtesting import Backtest, Strategy

class SectorRotation(Strategy):
    """Invest in best performing sector ETF"""

    def init(self):
        # Would compare multiple sector ETFs
        # XLK (Tech), XLF (Finance), XLE (Energy), etc.
        pass

    def next(self):
        # Calculate momentum for each sector
        # Switch to sector with highest momentum
        # Rebalance monthly
        pass
```

## Using AI Models for Strategy Development

TradingAgent supports using DeepSeek and QWEN for strategy analysis and generation.

### Example: Using DeepSeek for Strategy Research

Create `src/scripts/deepseek_strategy_analyzer.py`:

```python
from src.models.model_factory import ModelFactory

# Initialize DeepSeek
model = ModelFactory().get_model("deepseek", "deepseek-reasoner")

# Analyze a strategy concept
strategy_description = """
I want to create a mean reversion strategy for SPY that:
1. Identifies when price deviates significantly from 20-day moving average
2. Uses Bollinger Bands to determine entry points
3. Exits when price returns to the mean
4. Only trades in low volatility environments (VIX < 20)
"""

system_prompt = "You are an expert quantitative trading strategist. Analyze trading strategies and provide detailed implementation guidance."

response = model.generate_response(
    system_prompt=system_prompt,
    user_content=f"Analyze this strategy and provide Python backtesting code using backtesting.py library:\n\n{strategy_description}",
    temperature=0.3,
    max_tokens=4000
)

print(response.content)

# The AI will generate complete backtesting code for you
```

## Sample Data Files

Example CSV format (`src/data/stocks/AAPL.csv`):

```csv
Date,Open,High,Low,Close,Volume
2020-01-02,74.06,75.15,73.80,75.09,135480400
2020-01-03,74.29,75.14,74.13,74.36,146322800
2020-01-06,73.45,74.99,73.19,74.95,118387200
```

## Complete End-to-End Example

Create `src/examples/complete_stock_backtest.py`:

```python
import yfinance as yf
import pandas as pd
from backtesting import Backtest, Strategy
import pandas_ta as ta
from datetime import datetime

class TrendFollowingStrategy(Strategy):
    """
    Trend Following Strategy with:
    - EMA crossover for trend direction
    - ADX for trend strength
    - ATR-based position sizing and stops
    """

    fast_ema = 12
    slow_ema = 26
    adx_period = 14
    adx_threshold = 25
    atr_period = 14
    atr_multiplier = 2.0

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low

        # EMAs
        self.ema_fast = self.I(ta.ema, close, self.fast_ema)
        self.ema_slow = self.I(ta.ema, close, self.slow_ema)

        # ADX for trend strength
        adx_data = ta.adx(high, low, close, self.adx_period)
        self.adx = self.I(lambda x: x, adx_data[f'ADX_{self.adx_period}'])

        # ATR for stops
        self.atr = self.I(ta.atr, high, low, close, self.atr_period)

        self.entry_price = 0

    def next(self):
        # Trend following conditions
        bullish_trend = self.ema_fast[-1] > self.ema_slow[-1]
        bearish_trend = self.ema_fast[-1] < self.ema_slow[-1]
        strong_trend = self.adx[-1] > self.adx_threshold

        current_price = self.data.Close[-1]

        # Entry: Bullish crossover with strong trend
        if bullish_trend and strong_trend and not self.position:
            self.buy()
            self.entry_price = current_price

        # Exit: Bearish crossover or ATR-based stop
        if self.position:
            stop_price = self.entry_price - (self.atr[-1] * self.atr_multiplier)

            if bearish_trend or current_price < stop_price:
                self.position.close()

def run_complete_backtest(ticker, start_date, end_date):
    """Run a complete backtest with analysis"""

    print(f"\n{'='*60}")
    print(f"Backtesting {ticker} from {start_date} to {end_date}")
    print(f"{'='*60}\n")

    # Download data
    print("Downloading data...")
    data = yf.download(ticker, start=start_date, end=end_date)

    if data.empty:
        print("No data available for this ticker")
        return

    print(f"Data downloaded: {len(data)} bars\n")

    # Run backtest
    print("Running backtest...")
    bt = Backtest(
        data,
        TrendFollowingStrategy,
        cash=100000,
        commission=.001,  # 0.1% commission
        exclusive_orders=True
    )

    stats = bt.run()

    # Print results
    print(f"\n{'='*60}")
    print("BACKTEST RESULTS")
    print(f"{'='*60}")
    print(f"Initial Capital:     ${100000:,.2f}")
    print(f"Final Value:         ${stats['Equity Final [$]']:,.2f}")
    print(f"Return:              {stats['Return [%]']:.2f}%")
    print(f"Buy & Hold Return:   {stats['Buy & Hold Return [%]']:.2f}%")
    print(f"Sharpe Ratio:        {stats['Sharpe Ratio']:.2f}")
    print(f"Max Drawdown:        {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate:            {stats['Win Rate [%]']:.2f}%")
    print(f"Total Trades:        {stats['# Trades']}")
    print(f"Avg Trade:           {stats['Avg. Trade [%]']:.2f}%")
    print(f"Avg Trade Duration:  {stats['Avg. Trade Duration']}")
    print(f"{'='*60}\n")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"src/data/stocks/backtest_{ticker}_{timestamp}.html"

    # Plot and save
    bt.plot(filename=results_file, open_browser=False)
    print(f"Results saved to: {results_file}\n")

    return stats

# Run backtests on multiple stocks
if __name__ == "__main__":
    tickers = ["SPY", "AAPL", "MSFT", "NVDA"]

    for ticker in tickers:
        try:
            run_complete_backtest(
                ticker=ticker,
                start_date="2020-01-01",
                end_date="2024-01-01"
            )
        except Exception as e:
            print(f"Error backtesting {ticker}: {str(e)}")
```

Run it:

```bash
cd /home/user/TradingAgent
python src/examples/complete_stock_backtest.py
```

## Best Practices

1. **Use Realistic Assumptions**
   - Include commission costs (typically 0.1% per trade)
   - Account for slippage (1-5 basis points)
   - Consider market impact for large positions

2. **Avoid Overfitting**
   - Use out-of-sample testing
   - Don't over-optimize parameters
   - Test across multiple market conditions

3. **Use pandas_ta, NOT backtesting.py Built-in Indicators**
   - Per CLAUDE.md: "Use pandas_ta or talib for technical indicators instead"

4. **Risk Management**
   - Implement stop losses
   - Use position sizing
   - Set maximum drawdown limits

5. **Validation**
   - Walk-forward analysis
   - Test on different time periods
   - Test on different stocks/sectors

## Troubleshooting

### Issue: "Cannot import backtesting"
**Solution**:
```bash
pip install backtesting
```

### Issue: "No data returned from yfinance"
**Solution**: Check ticker symbol and date range. Some stocks have limited history.

### Issue: "Strategy shows unrealistic returns"
**Solution**: Check for look-ahead bias, ensure you're using proper indicators, and verify commission/slippage settings.

### Issue: "pandas_ta indicator returning None"
**Solution**: Some indicators need minimum data points. Ensure you have sufficient history.

## Next Steps

1. Review `BACKTESTING_OPTIONS_GUIDE.md` for options strategies
2. See `TASTYTRADE_INTEGRATION_GUIDE.md` for live trading
3. Explore `src/agents/rbi_agent.py` for AI-generated strategies
4. Check `src/models/README.md` for using different AI models

## Additional Resources

- [backtesting.py Documentation](https://kernc.github.io/backtesting.py/)
- [pandas_ta Documentation](https://github.com/twopirllc/pandas-ta)
- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
- [TradingView for Strategy Ideas](https://www.tradingview.com/scripts/)
- [QuantStart Backtesting Guide](https://www.quantstart.com/articles/backtesting-systematic-trading-strategies-in-python-considerations-and-open-source-frameworks/)

Built with love by Moon Dev
