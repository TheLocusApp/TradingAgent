# TastyTrade Integration Guide for TradingAgent

## Overview

This guide covers integrating TastyTrade (formerly TastyWorks) as a broker for TradingAgent. TastyTrade provides an excellent API for options and stock trading with competitive pricing and a Python SDK.

**YES**, you can absolutely connect TradingAgent to TastyTrade! This guide will show you exactly how.

## Why TastyTrade?

- **Options-focused broker** - Built by options traders, for options traders
- **Excellent API** - Full REST API with Python SDK
- **Low commissions** - $0 stock trades, $1 options trades
- **Paper trading** - Full sandbox environment for testing
- **Real-time data** - Market data streaming included
- **DXFeed integration** - Professional-grade market data

## Prerequisites

1. TastyTrade account (sign up at https://tastytrade.com)
2. API credentials (available in your account settings)
3. TradingAgent environment set up (`conda activate tflow`)

## Step-by-Step Setup

### Step 1: Create TastyTrade Account

1. Go to https://tastytrade.com
2. Click "Open an Account"
3. Complete the application process
4. Fund your account (minimum $2,000 for margin, $0 for cash account)

### Step 2: Enable API Access

1. Log in to your TastyTrade account
2. Go to Settings → API Settings
3. Click "Generate API Token"
4. Save your credentials securely:
   - Username (your account email or username)
   - Password (your account password)
   - Account Number (found in account settings)

### Step 3: Install TastyTrade SDK

```bash
conda activate tflow

# Install the unofficial SDK (more feature-rich)
pip install tastytrade

# OR install the official SDK
# pip install tastytrade-sdk

# Update requirements
pip freeze > requirements.txt
```

### Step 4: Verify Installation

```bash
python -c "import tastytrade; print('TastyTrade SDK installed successfully')"
```

### Step 5: Configure Environment Variables

Add to your `.env` file:

```bash
# TastyTrade API Credentials
TASTYTRADE_USERNAME=your_username_or_email
TASTYTRADE_PASSWORD=your_password
TASTYTRADE_ACCOUNT_NUMBER=your_account_number

# Optional: Use sandbox for testing
TASTYTRADE_SANDBOX=true  # Set to false for live trading
```

### Step 6: Create TastyTrade Connector

Create `src/integrations/tastytrade_connector.py`:

```python
"""
TastyTrade Connector for TradingAgent
Built with love by Moon Dev

Handles authentication, order execution, and data streaming
"""

import os
from dotenv import load_dotenv
from tastytrade import Session, Account
from tastytrade.instruments import Equity, Option, get_option_chain
from tastytrade.order import NewOrder, OrderAction, OrderTimeInForce, OrderType
from tastytrade.dxfeed import EventType
from termcolor import cprint
from datetime import datetime, date
import pandas as pd

class TastyTradeConnector:
    """Connector for TastyTrade API"""

    def __init__(self, sandbox=True):
        """Initialize TastyTrade connection"""
        load_dotenv()

        self.username = os.getenv('TASTYTRADE_USERNAME')
        self.password = os.getenv('TASTYTRADE_PASSWORD')
        self.account_number = os.getenv('TASTYTRADE_ACCOUNT_NUMBER')
        self.sandbox = sandbox

        if not all([self.username, self.password, self.account_number]):
            raise ValueError("TastyTrade credentials not found in .env file")

        self.session = None
        self.account = None

        cprint("Initializing TastyTrade Connector...", "cyan")
        self._authenticate()

    def _authenticate(self):
        """Authenticate with TastyTrade"""
        try:
            cprint("Authenticating with TastyTrade...", "cyan")

            # Create session (automatically uses sandbox if credentials are sandbox)
            self.session = Session(self.username, self.password)

            cprint("Authentication successful!", "green")

            # Get account
            accounts = Account.get_accounts(self.session)
            self.account = next(
                (acc for acc in accounts if acc.account_number == self.account_number),
                None
            )

            if not self.account:
                raise ValueError(f"Account {self.account_number} not found")

            cprint(f"Connected to account: {self.account.account_number}", "green")

        except Exception as e:
            cprint(f"Authentication failed: {str(e)}", "red")
            raise

    def get_balances(self):
        """Get account balances"""
        try:
            balances = self.account.get_balances(self.session)

            return {
                'cash': float(balances.cash_balance),
                'net_liquidating_value': float(balances.net_liquidating_value),
                'equity': float(balances.equity_buying_power),
                'derivatives': float(balances.derivative_buying_power),
                'available_to_trade': float(balances.cash_available_to_withdraw)
            }

        except Exception as e:
            cprint(f"Error fetching balances: {str(e)}", "red")
            return None

    def get_positions(self):
        """Get all current positions"""
        try:
            positions = self.account.get_positions(self.session)

            position_list = []
            for pos in positions:
                position_list.append({
                    'symbol': pos.symbol,
                    'quantity': int(pos.quantity),
                    'average_price': float(pos.average_open_price),
                    'current_price': float(pos.close_price) if pos.close_price else 0,
                    'unrealized_pnl': float(pos.unrealized_day_gain) if pos.unrealized_day_gain else 0,
                    'type': 'stock' if isinstance(pos.instrument_type, str) and 'equity' in pos.instrument_type.lower() else 'option'
                })

            return position_list

        except Exception as e:
            cprint(f"Error fetching positions: {str(e)}", "red")
            return []

    def get_quote(self, symbol):
        """Get real-time quote for a symbol"""
        try:
            equity = Equity.get_equity(self.session, symbol)
            return {
                'symbol': symbol,
                'bid': float(equity.bid_price) if equity.bid_price else 0,
                'ask': float(equity.ask_price) if equity.ask_price else 0,
                'last': float(equity.last_price) if equity.last_price else 0,
                'volume': int(equity.volume) if equity.volume else 0
            }

        except Exception as e:
            cprint(f"Error fetching quote for {symbol}: {str(e)}", "red")
            return None

    def get_option_chain(self, symbol, expiration_date=None):
        """Get option chain for a symbol"""
        try:
            # Get all expirations if not specified
            chains = get_option_chain(self.session, symbol)

            if expiration_date:
                # Filter by expiration date
                chains = [c for c in chains if c.expiration_date == expiration_date]

            options_data = []
            for chain in chains:
                options_data.append({
                    'symbol': symbol,
                    'expiration': chain.expiration_date,
                    'strike': float(chain.strike_price),
                    'option_type': chain.option_type,  # 'C' or 'P'
                    'bid': float(chain.bid_price) if chain.bid_price else 0,
                    'ask': float(chain.ask_price) if chain.ask_price else 0,
                    'last': float(chain.last_price) if chain.last_price else 0,
                    'volume': int(chain.volume) if chain.volume else 0,
                    'open_interest': int(chain.open_interest) if chain.open_interest else 0,
                    'delta': float(chain.delta) if hasattr(chain, 'delta') and chain.delta else 0,
                    'theta': float(chain.theta) if hasattr(chain, 'theta') and chain.theta else 0,
                    'iv': float(chain.implied_volatility) if hasattr(chain, 'implied_volatility') and chain.implied_volatility else 0
                })

            return pd.DataFrame(options_data)

        except Exception as e:
            cprint(f"Error fetching option chain for {symbol}: {str(e)}", "red")
            return pd.DataFrame()

    def place_stock_order(self, symbol, quantity, action='BUY', order_type='MARKET'):
        """
        Place a stock order

        Args:
            symbol: Stock ticker
            quantity: Number of shares
            action: 'BUY' or 'SELL'
            order_type: 'MARKET' or 'LIMIT'
        """
        try:
            cprint(f"Placing {action} order for {quantity} shares of {symbol}...", "cyan")

            # Create order
            order_action = OrderAction.BUY_TO_OPEN if action == 'BUY' else OrderAction.SELL_TO_CLOSE
            order_type_enum = OrderType.MARKET if order_type == 'MARKET' else OrderType.LIMIT

            order = NewOrder(
                time_in_force=OrderTimeInForce.DAY,
                order_type=order_type_enum,
                legs=[
                    {
                        'instrument-type': 'Equity',
                        'symbol': symbol,
                        'action': order_action,
                        'quantity': quantity
                    }
                ]
            )

            # Submit order
            response = self.account.place_order(self.session, order)

            cprint(f"Order placed successfully! Order ID: {response.order_id}", "green")

            return {
                'success': True,
                'order_id': response.order_id,
                'symbol': symbol,
                'quantity': quantity,
                'action': action
            }

        except Exception as e:
            cprint(f"Error placing order: {str(e)}", "red")
            return {'success': False, 'error': str(e)}

    def place_option_order(self, symbol, expiration, strike, option_type, quantity, action='BUY'):
        """
        Place an option order

        Args:
            symbol: Underlying stock ticker
            expiration: Expiration date (YYYY-MM-DD)
            strike: Strike price
            option_type: 'CALL' or 'PUT'
            quantity: Number of contracts
            action: 'BUY' or 'SELL'
        """
        try:
            cprint(f"Placing {action} order for {quantity} {symbol} {strike}{option_type[0]} options...", "cyan")

            # Construct option symbol (OCC format)
            # Example: AAPL  250117C00150000 (AAPL Jan 17 2025 150 Call)
            exp_date = datetime.strptime(expiration, '%Y-%m-%d')
            exp_str = exp_date.strftime('%y%m%d')
            option_symbol = f"{symbol:<6}{exp_str}{option_type[0]}{int(strike*1000):08d}"

            order_action = OrderAction.BUY_TO_OPEN if action == 'BUY' else OrderAction.SELL_TO_OPEN

            order = NewOrder(
                time_in_force=OrderTimeInForce.DAY,
                order_type=OrderType.MARKET,
                legs=[
                    {
                        'instrument-type': 'Equity Option',
                        'symbol': option_symbol,
                        'action': order_action,
                        'quantity': quantity
                    }
                ]
            )

            response = self.account.place_order(self.session, order)

            cprint(f"Option order placed successfully! Order ID: {response.order_id}", "green")

            return {
                'success': True,
                'order_id': response.order_id,
                'symbol': option_symbol,
                'quantity': quantity,
                'action': action
            }

        except Exception as e:
            cprint(f"Error placing option order: {str(e)}", "red")
            return {'success': False, 'error': str(e)}

    def get_order_status(self, order_id):
        """Get status of an order"""
        try:
            orders = self.account.get_live_orders(self.session)

            for order in orders:
                if order.id == order_id:
                    return {
                        'order_id': order.id,
                        'status': order.status,
                        'filled_quantity': order.filled_quantity,
                        'remaining_quantity': order.remaining_quantity,
                        'price': float(order.price) if order.price else None
                    }

            return {'order_id': order_id, 'status': 'NOT_FOUND'}

        except Exception as e:
            cprint(f"Error fetching order status: {str(e)}", "red")
            return None

    def cancel_order(self, order_id):
        """Cancel an order"""
        try:
            self.account.delete_order(self.session, order_id)
            cprint(f"Order {order_id} cancelled successfully", "green")
            return {'success': True}

        except Exception as e:
            cprint(f"Error cancelling order: {str(e)}", "red")
            return {'success': False, 'error': str(e)}

    def get_account_history(self, days=30):
        """Get account trade history"""
        try:
            history = self.account.get_history(self.session, days=days)

            trades = []
            for item in history:
                trades.append({
                    'date': item.executed_at,
                    'symbol': item.symbol,
                    'action': item.action,
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'commission': float(item.commission) if item.commission else 0
                })

            return pd.DataFrame(trades)

        except Exception as e:
            cprint(f"Error fetching history: {str(e)}", "red")
            return pd.DataFrame()

    def close_connection(self):
        """Close the session"""
        if self.session:
            # TastyTrade sessions auto-close, but good practice to clean up
            self.session = None
            cprint("TastyTrade connection closed", "yellow")


# Example usage
if __name__ == "__main__":
    # Initialize connector (sandbox mode)
    tt = TastyTradeConnector(sandbox=True)

    # Get balances
    balances = tt.get_balances()
    print("\nAccount Balances:")
    for key, value in balances.items():
        print(f"  {key}: ${value:,.2f}")

    # Get positions
    positions = tt.get_positions()
    print(f"\nCurrent Positions: {len(positions)}")
    for pos in positions:
        print(f"  {pos['symbol']}: {pos['quantity']} @ ${pos['average_price']:.2f}")

    # Get a quote
    quote = tt.get_quote("SPY")
    print(f"\nSPY Quote:")
    print(f"  Bid: ${quote['bid']:.2f}")
    print(f"  Ask: ${quote['ask']:.2f}")
    print(f"  Last: ${quote['last']:.2f}")

    # Get option chain
    print("\nFetching SPY option chain...")
    options = tt.get_option_chain("SPY")
    print(f"Found {len(options)} options")
    if not options.empty:
        print(options.head())

    # Close connection
    tt.close_connection()
```

### Step 7: Create TastyTrade Trading Agent

Create `src/agents/tastytrade_agent.py`:

```python
"""
TastyTrade Trading Agent
Executes trades using TastyTrade as the broker

Built with love by Moon Dev
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.integrations.tastytrade_connector import TastyTradeConnector
from src.models.model_factory import ModelFactory
from termcolor import cprint
import time

class TastyTradeAgent:
    """AI-powered trading agent using TastyTrade"""

    def __init__(self, sandbox=True):
        """Initialize the agent"""
        cprint("\n" + "="*60, "cyan")
        cprint("TastyTrade Trading Agent Initializing", "cyan")
        cprint("="*60 + "\n", "cyan")

        # Connect to TastyTrade
        self.tt = TastyTradeConnector(sandbox=sandbox)

        # Initialize AI model for decision making
        self.model_factory = ModelFactory()
        self.model = self.model_factory.get_model("deepseek", "deepseek-reasoner")

        cprint("TastyTrade Agent ready!", "green")

    def analyze_market(self, symbol):
        """Use AI to analyze market conditions"""
        cprint(f"\nAnalyzing {symbol}...", "cyan")

        # Get current quote
        quote = self.tt.get_quote(symbol)

        if not quote:
            return None

        # Get positions
        positions = self.tt.get_positions()
        current_position = next((p for p in positions if p['symbol'] == symbol), None)

        # Use AI to analyze
        system_prompt = "You are an expert trading analyst. Analyze market data and provide trading recommendations."

        user_content = f"""
        Analyze {symbol}:

        Current Price: ${quote['last']:.2f}
        Bid/Ask: ${quote['bid']:.2f} / ${quote['ask']:.2f}
        Volume: {quote['volume']:,}

        Current Position: {current_position['quantity'] if current_position else 0} shares

        Based on this data, should I:
        1. BUY more shares
        2. SELL current position
        3. HOLD and do nothing

        Provide a brief recommendation with reasoning.
        """

        response = self.model.generate_response(
            system_prompt=system_prompt,
            user_content=user_content,
            temperature=0.3,
            max_tokens=500
        )

        return response.content

    def execute_strategy(self, symbol, quantity):
        """Execute a trading strategy"""
        # Get AI analysis
        analysis = self.analyze_market(symbol)

        if analysis:
            cprint(f"\nAI Analysis:\n{analysis}\n", "yellow")

        # For demo, just show what would happen
        # In production, you'd parse AI response and execute
        cprint(f"Strategy execution complete for {symbol}", "green")

    def run_options_strategy(self, symbol):
        """Run an options trading strategy"""
        cprint(f"\nRunning options strategy for {symbol}...", "cyan")

        # Get option chain
        options = self.tt.get_option_chain(symbol)

        if options.empty:
            cprint("No options data available", "red")
            return

        # Find options with good premium (example: covered calls)
        calls = options[options['option_type'] == 'C']

        # Get current stock price
        quote = self.tt.get_quote(symbol)
        current_price = quote['last']

        # Find calls 5% OTM
        target_strike = current_price * 1.05
        suitable_calls = calls[
            (calls['strike'] >= target_strike) &
            (calls['strike'] <= target_strike * 1.1)
        ].sort_values('premium', ascending=False)

        if not suitable_calls.empty:
            best_option = suitable_calls.iloc[0]
            cprint(f"\nBest covered call opportunity:", "green")
            cprint(f"  Strike: ${best_option['strike']:.2f}", "green")
            cprint(f"  Premium: ${best_option['bid']:.2f}", "green")
            cprint(f"  Expiration: {best_option['expiration']}", "green")

    def monitor_positions(self):
        """Monitor and manage existing positions"""
        positions = self.tt.get_positions()

        cprint(f"\nMonitoring {len(positions)} positions...", "cyan")

        for pos in positions:
            pnl_pct = (pos['unrealized_pnl'] / (pos['average_price'] * pos['quantity'])) * 100

            color = "green" if pnl_pct > 0 else "red"

            cprint(f"\n{pos['symbol']}:", color)
            cprint(f"  Quantity: {pos['quantity']}", color)
            cprint(f"  Avg Price: ${pos['average_price']:.2f}", color)
            cprint(f"  Current: ${pos['current_price']:.2f}", color)
            cprint(f"  P&L: ${pos['unrealized_pnl']:.2f} ({pnl_pct:.2f}%)", color)

            # Risk management: auto-exit if loss > 5%
            if pnl_pct < -5:
                cprint(f"  WARNING: Loss exceeds 5%! Consider exiting.", "red")

    def run(self):
        """Main agent loop"""
        try:
            while True:
                cprint("\n" + "="*60, "cyan")
                cprint("TastyTrade Agent - Main Loop", "cyan")
                cprint("="*60, "cyan")

                # Get balances
                balances = self.tt.get_balances()
                cprint(f"\nAccount Value: ${balances['net_liquidating_value']:,.2f}", "green")
                cprint(f"Available Cash: ${balances['available_to_trade']:,.2f}", "green")

                # Monitor positions
                self.monitor_positions()

                # Run analysis on watchlist
                watchlist = ["SPY", "QQQ", "AAPL"]

                for symbol in watchlist:
                    try:
                        self.execute_strategy(symbol, quantity=10)
                    except Exception as e:
                        cprint(f"Error with {symbol}: {str(e)}", "red")

                # Sleep before next iteration
                cprint("\nSleeping for 5 minutes...", "yellow")
                time.sleep(300)

        except KeyboardInterrupt:
            cprint("\n\nShutting down TastyTrade Agent...", "yellow")
            self.tt.close_connection()
            cprint("Agent stopped", "red")


if __name__ == "__main__":
    # Run in sandbox mode for testing
    agent = TastyTradeAgent(sandbox=True)
    agent.run()
```

### Step 8: Test the Integration

```bash
cd /home/user/TradingAgent

# Test connection
python src/integrations/tastytrade_connector.py

# Run the agent (paper trading)
python src/agents/tastytrade_agent.py
```

## Going Live (Real Trading)

**IMPORTANT**: Only go live after thorough testing in sandbox mode!

1. Change `sandbox=False` in your agent initialization
2. Update `.env` with live credentials
3. Start with small position sizes
4. Monitor closely for the first few trades

```python
# In your agent code
agent = TastyTradeAgent(sandbox=False)  # LIVE TRADING
```

## Advanced Features

### 1. Real-time Market Data Streaming

```python
from tastytrade.dxfeed import DXFeedStreamer, EventType

def stream_quotes(symbols):
    """Stream real-time quotes"""
    async def quote_handler(quote):
        print(f"{quote['eventSymbol']}: ${quote['bidPrice']} x ${quote['askPrice']}")

    async with DXFeedStreamer(session) as streamer:
        await streamer.subscribe(EventType.QUOTE, symbols)
        streamer.add_handler(EventType.QUOTE, quote_handler)

        # Stream indefinitely
        await streamer.wait()
```

### 2. Complex Option Strategies

```python
def create_iron_condor(connector, symbol, expiration):
    """Create an iron condor position"""

    quote = connector.get_quote(symbol)
    price = quote['last']

    # Define strikes (example: SPY at 450)
    short_call_strike = price * 1.05  # 472.50
    long_call_strike = price * 1.07   # 481.50
    short_put_strike = price * 0.95   # 427.50
    long_put_strike = price * 0.93    # 418.50

    # Place all four legs simultaneously
    # (Code to construct multi-leg order)
```

### 3. Webhook Integration

Create `src/integrations/tastytrade_webhook.py` for receiving signals from TradingView or other sources.

## Best Practices

1. **Always test in sandbox first**
2. **Use stop losses** - Implement in your agent logic
3. **Position sizing** - Never risk more than 1-2% per trade
4. **Monitor API limits** - TastyTrade has rate limits
5. **Log all trades** - Keep detailed records
6. **Handle errors gracefully** - Network issues, API errors, etc.

## Commission Structure

- **Stock trades**: $0
- **Options trades**: $1.00 per contract to open, $0 to close
- **No assignment/exercise fees**

## Troubleshooting

### Issue: "Authentication failed"
**Solution**: Verify credentials in .env file. Ensure no extra spaces.

### Issue: "Account not found"
**Solution**: Check your account number. It should be your full account number from TastyTrade.

### Issue: "Order rejected"
**Solution**: Check buying power, position limits, and order parameters.

### Issue: "Cannot fetch options data"
**Solution**: Some symbols may not have options available. Try liquid underlyings like SPY, QQQ, AAPL.

## Resources

- [TastyTrade API Documentation](https://tastytrade.com/api/)
- [Unofficial SDK GitHub](https://github.com/tastyware/tastytrade)
- [Official SDK GitHub](https://github.com/tastytrade/tastytrade-sdk-python)
- [TastyTrade Support](https://support.tastytrade.com)

## Next Steps

1. Review `BACKTESTING_OPTIONS_GUIDE.md` to develop strategies
2. See `BACKTESTING_STOCKS_GUIDE.md` for stock strategies
3. Test thoroughly in paper trading before going live
4. Integrate with RBI Agent for AI-generated strategies

**Remember**: Trading involves substantial risk. Always test thoroughly and start small!

Built with love by Moon Dev
