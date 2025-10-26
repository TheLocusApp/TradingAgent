# Options Backtesting Guide for TradingAgent

## Overview

This guide will walk you through setting up and running options backtesting in TradingAgent. The project supports multiple approaches for options backtesting using specialized Python libraries.

## Prerequisites

1. Conda environment `tflow` activated
2. Python 3.8+
3. Required dependencies installed

## Installation

### Step 1: Activate Environment

```bash
conda activate tflow
```

### Step 2: Install Options Backtesting Libraries

```bash
# Install optopsy (specialized options backtesting library)
pip install optopsy

# Install yfinance for options data
pip install yfinance

# Install pandas-ta for technical indicators
pip install pandas-ta

# Install QuantLib for options pricing (optional but recommended)
pip install QuantLib-Python

# Update requirements.txt
pip freeze > requirements.txt
```

### Step 3: Verify Installation

```bash
python -c "import optopsy; print('Optopsy version:', optopsy.__version__)"
python -c "import yfinance as yf; print('yfinance installed successfully')"
```

## Options Data Sources

### Option 1: Yahoo Finance (Free)

Yahoo Finance provides free options data for most US-listed stocks.

```python
import yfinance as yf

# Get options chain for a ticker
ticker = yf.Ticker("AAPL")
options_dates = ticker.options  # Available expiration dates

# Get options data for specific expiration
opts = ticker.option_chain('2025-01-17')
calls = opts.calls
puts = opts.puts
```

### Option 2: TastyTrade API (Real Broker Data)

See `TASTYTRADE_INTEGRATION_GUIDE.md` for connecting to TastyTrade for live options data.

### Option 3: Historical Options Data Providers

For comprehensive backtesting, consider:
- **HistoricalOptionData.com** - Historical options data
- **CBOE DataShop** - Official CBOE data
- **Polygon.io** - Real-time and historical options data

## Backtesting Strategies

### Approach 1: Using Optopsy (Recommended for Options-Specific Strategies)

Create a file: `src/strategies/options/iron_condor_strategy.py`

```python
import pandas as pd
import optopsy as op
from optopsy import filters

# Load historical options data
# Data must have columns: underlying_symbol, quote_date, expiration, strike, option_type, bid, ask, delta, gamma, vega, theta
data = pd.read_csv('path/to/options_data.csv')

# Define filters for iron condor
filters_dict = {
    'entry_dte': (30, 45),  # Enter 30-45 days to expiration
    'leg1_delta': 0.30,      # Short call delta
    'leg2_delta': 0.20,      # Long call delta
    'leg3_delta': -0.30,     # Short put delta
    'leg4_delta': -0.20,     # Long put delta
}

# Run backtest
results = op.backtest(
    data,
    strategy='iron_condor',
    entry_dte=filters_dict['entry_dte'],
    exit_dte=7,  # Exit 7 days before expiration
    contracts=1
)

# Analyze results
print(results.stats)
print(f"Total Return: {results.total_return}")
print(f"Win Rate: {results.win_rate}")
print(f"Max Drawdown: {results.max_drawdown}")
```

### Approach 2: Using Backtesting.py with Options Logic

Create a file: `src/strategies/options/covered_call_backtest.py`

```python
import yfinance as yf
import pandas as pd
from backtesting import Backtest, Strategy
import numpy as np

class CoveredCallStrategy(Strategy):
    """
    Covered Call Strategy:
    - Own 100 shares of stock
    - Sell 1 call option OTM (out of the money)
    - Collect premium while capping upside
    """

    strike_offset = 0.05  # Sell calls 5% OTM
    min_premium = 0.50     # Minimum premium per contract

    def init(self):
        # Track if we have an active covered call position
        self.call_sold = False
        self.strike_price = 0
        self.expiration = 0
        self.premium_collected = 0

    def next(self):
        current_price = self.data.Close[-1]

        # If no position, buy stock
        if not self.position:
            self.buy()
            self.call_sold = False

        # If we own stock but haven't sold a call
        elif self.position and not self.call_sold:
            # Calculate strike price (5% OTM)
            self.strike_price = current_price * (1 + self.strike_offset)

            # Simulate selling a call (in real backtest, fetch actual option prices)
            # For simulation, estimate premium using Black-Scholes or historical data
            estimated_premium = self.estimate_call_premium(current_price, self.strike_price)

            if estimated_premium >= self.min_premium:
                self.premium_collected += estimated_premium * 100  # 1 contract = 100 shares
                self.call_sold = True
                print(f"Sold call at strike {self.strike_price:.2f} for ${estimated_premium:.2f} premium")

        # If stock price exceeds strike, we get called away
        elif self.position and self.call_sold and current_price >= self.strike_price:
            self.position.close()
            self.call_sold = False
            print(f"Stock called away at {self.strike_price:.2f}. Premium: ${self.premium_collected:.2f}")

    def estimate_call_premium(self, stock_price, strike):
        """Simple premium estimation - replace with real option pricing"""
        # This is a simplified estimation
        # In production, use Black-Scholes or fetch real option prices
        time_value = 0.02 * stock_price  # Assume 2% time value
        intrinsic = max(0, stock_price - strike)
        return intrinsic + time_value

# Download stock data
ticker = "SPY"
data = yf.download(ticker, start="2020-01-01", end="2024-01-01")

# Run backtest
bt = Backtest(data, CoveredCallStrategy, cash=10000, commission=.002)
stats = bt.run()

print(stats)
print(f"\nTotal Premium Collected: ${stats._strategy.premium_collected:.2f}")
bt.plot()
```

### Approach 3: Using RBI Agent to Generate Options Backtests

The RBI Agent can generate options backtests from YouTube videos or PDFs explaining options strategies.

Create `src/data/rbi/ideas_options.txt`:

```text
# Options strategy ideas (one per line)

# Iron Condor on SPY with 45 DTE
https://www.youtube.com/watch?v=example_iron_condor_video

# Wheel Strategy on High IV Stocks
Sell cash-secured puts on stocks with IV > 40%, when assigned sell covered calls at 30 delta

# Credit Spreads on Earnings
Sell credit spreads 1 day before earnings on stocks with high implied volatility
```

Then run:

```bash
cd /home/user/TradingAgent
python src/agents/rbi_agent.py
```

The RBI agent will:
1. Read the options strategy descriptions
2. Use DeepSeek or GPT-5 to understand the strategy
3. Generate backtesting code
4. Execute and return results

## Advanced: Options Greeks Analysis

For strategies involving Greeks (delta, gamma, theta, vega):

```python
import QuantLib as ql
import pandas as pd
from datetime import datetime

def calculate_option_greeks(spot_price, strike, risk_free_rate, volatility, days_to_expiry):
    """Calculate Black-Scholes Greeks"""

    # Setup QuantLib date
    calculation_date = ql.Date.todaysDate()
    ql.Settings.instance().evaluationDate = calculation_date

    # Option parameters
    option_type = ql.Option.Call  # or ql.Option.Put
    payoff = ql.PlainVanillaPayoff(option_type, strike)

    # Expiration
    expiry_date = calculation_date + days_to_expiry
    exercise = ql.EuropeanExercise(expiry_date)

    # European option
    european_option = ql.VanillaOption(payoff, exercise)

    # Market data
    spot_handle = ql.QuoteHandle(ql.SimpleQuote(spot_price))
    flat_ts = ql.YieldTermStructureHandle(
        ql.FlatForward(calculation_date, risk_free_rate, ql.Actual365Fixed())
    )
    flat_vol_ts = ql.BlackVolTermStructureHandle(
        ql.BlackConstantVol(calculation_date, ql.NullCalendar(), volatility, ql.Actual365Fixed())
    )

    # Black-Scholes process
    bs_process = ql.BlackScholesProcess(spot_handle, flat_ts, flat_vol_ts)

    # Pricing engine
    european_option.setPricingEngine(ql.AnalyticEuropeanEngine(bs_process))

    # Calculate Greeks
    return {
        'price': european_option.NPV(),
        'delta': european_option.delta(),
        'gamma': european_option.gamma(),
        'vega': european_option.vega() / 100,  # Vega per 1% change
        'theta': european_option.theta() / 365,  # Theta per day
        'rho': european_option.rho() / 100
    }

# Example usage
greeks = calculate_option_greeks(
    spot_price=450,
    strike=455,
    risk_free_rate=0.05,
    volatility=0.20,
    days_to_expiry=30
)

print(f"Delta: {greeks['delta']:.4f}")
print(f"Gamma: {greeks['gamma']:.4f}")
print(f"Theta: {greeks['theta']:.4f}")
print(f"Vega: {greeks['vega']:.4f}")
```

## Sample Data Structure for Options

Your options data CSV should have these columns:

```csv
quote_date,underlying_symbol,expiration,strike,option_type,bid,ask,volume,open_interest,implied_volatility,delta,gamma,theta,vega
2024-01-15,SPY,2024-02-16,450,call,5.20,5.30,1250,15000,0.18,0.52,0.015,-0.05,0.12
2024-01-15,SPY,2024-02-16,450,put,4.80,4.90,980,12000,0.19,-0.48,0.015,-0.05,0.12
```

## Best Practices

1. **Realistic Costs**: Include commission ($0.65 per contract typical) and slippage
2. **Bid-Ask Spread**: Use midpoint or conservative fills (closer to ask for buys, bid for sells)
3. **Assignment Risk**: Account for early assignment on American options
4. **IV Crush**: Model implied volatility changes after earnings
5. **Liquidity Filters**: Only trade options with sufficient volume/open interest
6. **Multiple Market Cycles**: Test across bull, bear, and sideways markets
7. **Greeks Management**: Monitor and manage delta, theta decay, and vega risk

## Complete Example: Backtesting an Iron Condor

Create `src/strategies/options/iron_condor_complete.py`:

```python
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

class IronCondorBacktest:
    def __init__(self, ticker, start_date, end_date):
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.trades = []
        self.equity_curve = []

    def fetch_options_data(self, date):
        """Fetch options data for a specific date"""
        ticker_obj = yf.Ticker(self.ticker)

        # Get options expiring 30-45 days out
        exp_dates = ticker_obj.options
        target_exp = None

        for exp in exp_dates:
            exp_date = datetime.strptime(exp, '%Y-%m-%d')
            dte = (exp_date - date).days
            if 30 <= dte <= 45:
                target_exp = exp
                break

        if not target_exp:
            return None

        # Get options chain
        opts = ticker_obj.option_chain(target_exp)
        return opts.calls, opts.puts, target_exp

    def construct_iron_condor(self, calls, puts, spot_price):
        """Construct iron condor by selecting strikes"""

        # Short call: 0.20 delta (or ~5% OTM)
        short_call_strike = spot_price * 1.05
        short_call = calls.iloc[(calls['strike'] - short_call_strike).abs().argsort()[:1]]

        # Long call: 0.10 delta (or ~7% OTM)
        long_call_strike = spot_price * 1.07
        long_call = calls.iloc[(calls['strike'] - long_call_strike).abs().argsort()[:1]]

        # Short put: -0.20 delta (or ~5% OTM)
        short_put_strike = spot_price * 0.95
        short_put = puts.iloc[(puts['strike'] - short_put_strike).abs().argsort()[:1]]

        # Long put: -0.10 delta (or ~7% OTM)
        long_put_strike = spot_price * 0.93
        long_put = puts.iloc[(puts['strike'] - long_put_strike).abs().argsort()[:1]]

        # Calculate net credit (what we collect)
        credit = (
            short_call['bid'].values[0] + short_put['bid'].values[0] -
            long_call['ask'].values[0] - long_put['ask'].values[0]
        ) * 100  # Per contract

        # Calculate max loss (width of spread - credit)
        call_spread_width = (long_call_strike - short_call_strike) * 100
        put_spread_width = (short_put_strike - long_put_strike) * 100
        max_loss = max(call_spread_width, put_spread_width) - credit

        return {
            'credit': credit,
            'max_loss': max_loss,
            'short_call_strike': short_call_strike,
            'long_call_strike': long_call_strike,
            'short_put_strike': short_put_strike,
            'long_put_strike': long_put_strike,
            'max_profit': credit
        }

    def run_backtest(self):
        """Run the iron condor backtest"""
        print(f"Backtesting Iron Condor on {self.ticker}")
        print(f"Period: {self.start_date} to {self.end_date}\n")

        current_date = self.start_date
        account_value = 10000

        while current_date <= self.end_date:
            # Check for new trade entry (weekly)
            if current_date.weekday() == 0:  # Monday
                try:
                    calls, puts, exp_date = self.fetch_options_data(current_date)
                    spot = yf.Ticker(self.ticker).history(start=current_date, end=current_date + timedelta(days=1))['Close'][0]

                    ic = self.construct_iron_condor(calls, puts, spot)

                    # Risk management: only trade if credit is sufficient
                    if ic['credit'] > 50:  # At least $50 credit per contract
                        self.trades.append({
                            'entry_date': current_date,
                            'expiration': exp_date,
                            'spot_at_entry': spot,
                            **ic
                        })
                        print(f"Entered Iron Condor on {current_date.strftime('%Y-%m-%d')}")
                        print(f"  Credit: ${ic['credit']:.2f}")
                        print(f"  Max Loss: ${ic['max_loss']:.2f}")
                        print(f"  Strikes: {ic['long_put_strike']:.0f}/{ic['short_put_strike']:.0f}/{ic['short_call_strike']:.0f}/{ic['long_call_strike']:.0f}\n")

                except Exception as e:
                    print(f"Could not enter trade on {current_date}: {str(e)}")

            current_date += timedelta(days=1)

        # Calculate total results
        total_credit = sum(t['credit'] for t in self.trades)
        print(f"\nBacktest Complete!")
        print(f"Total Trades: {len(self.trades)}")
        print(f"Total Credit Collected: ${total_credit:.2f}")

        return self.trades

# Run the backtest
backtest = IronCondorBacktest(
    ticker="SPY",
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2024, 1, 1)
)

results = backtest.run_backtest()
```

## Troubleshooting

### Issue: "No options data available"
**Solution**: Yahoo Finance may not have options data for all dates. Use a paid provider or ensure you're querying during market hours.

### Issue: "QuantLib installation failed"
**Solution**:
```bash
# On Mac
brew install boost
pip install QuantLib-Python

# On Ubuntu/Debian
sudo apt-get install libquantlib0-dev
pip install QuantLib-Python
```

### Issue: "Optopsy requires specific data format"
**Solution**: Ensure your CSV has all required columns. See sample data structure above.

## Next Steps

1. Review `BACKTESTING_STOCKS_GUIDE.md` for stock-specific backtesting
2. See `TASTYTRADE_INTEGRATION_GUIDE.md` to connect live broker data
3. Explore `src/agents/rbi_agent.py` for AI-generated strategy backtests
4. Check `src/models/README.md` for using DeepSeek/QWEN for strategy analysis

## Resources

- [Optopsy Documentation](https://github.com/michaelchu/optopsy)
- [Options Greeks Explained](https://www.optionseducation.org/referencelibrary/greeks)
- [Iron Condor Strategy Guide](https://www.tastytrade.com/definitions/iron-condor)
- [Backtesting Best Practices](https://www.quantstart.com/articles/backtesting-systematic-trading-strategies-in-python-considerations-and-open-source-frameworks/)

Built with love by Moon Dev
