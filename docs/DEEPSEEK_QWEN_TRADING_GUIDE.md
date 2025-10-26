# Using DeepSeek and QWEN for Stocks/Options Trading

## Overview

This guide demonstrates how to leverage DeepSeek and QWEN AI models for developing, backtesting, and executing stock and options trading strategies in TradingAgent.

Both DeepSeek and QWEN offer powerful reasoning capabilities that are particularly well-suited for:
- Strategy analysis and development
- Backtest code generation
- Market analysis
- Risk assessment
- Trade signal generation

## Why DeepSeek and QWEN?

### DeepSeek Strengths
- **Reasoning Models**: Shows thinking process for complex decisions
- **Cost-effective**: ~$0.027 per strategy backtest
- **Trading-focused**: Excellent at analyzing market strategies
- **Code generation**: Strong at creating backtesting code

### QWEN Strengths
- **Long Context**: Up to 1M tokens (analyze entire videos/research papers)
- **Latest Models**: Qwen-Max 2025 with enhanced reasoning
- **Specialized Coders**: Qwen-Coder-Turbo for backtest generation
- **Fast Turbo Mode**: Quick decisions for high-frequency analysis

## Setup

### Step 1: Get API Keys

**DeepSeek:**
1. Visit https://platform.deepseek.com
2. Sign up and get your API key
3. Add to `.env`: `DEEPSEEK_KEY=your_key_here`

**QWEN:**
1. Visit https://qwen.ai/apiplatform
2. Register for Alibaba Cloud account
3. Create DashScope API key
4. Add to `.env`: `QWEN_API_KEY=your_key_here`

### Step 2: Verify Installation

```bash
conda activate tflow

# Test DeepSeek
python -c "from src.models.model_factory import ModelFactory; mf = ModelFactory(); print('DeepSeek available:', mf.is_model_available('deepseek'))"

# Test QWEN
python -c "from src.models.model_factory import ModelFactory; mf = ModelFactory(); print('QWEN available:', mf.is_model_available('qwen'))"
```

## Use Cases

### 1. Strategy Analysis and Development

Create `src/scripts/ai_strategy_analyzer.py`:

```python
"""
AI Strategy Analyzer using DeepSeek and QWEN
Analyzes trading strategies and generates implementation code
"""

from src.models.model_factory import ModelFactory
from termcolor import cprint

def analyze_strategy_deepseek(strategy_description):
    """Use DeepSeek Reasoner to analyze a trading strategy"""

    cprint("\n=== DeepSeek Strategy Analysis ===\n", "cyan")

    # Initialize DeepSeek with reasoning model
    model_factory = ModelFactory()
    model = model_factory.get_model("deepseek", "deepseek-reasoner")

    system_prompt = """You are an expert quantitative trading analyst with deep knowledge of:
- Technical analysis and indicators
- Options Greeks and pricing
- Risk management
- Backtesting methodology
- Python programming for trading

Analyze trading strategies thoroughly and provide:
1. Viability assessment
2. Potential risks
3. Implementation approach
4. Expected market conditions for success
"""

    user_content = f"""
Analyze this trading strategy:

{strategy_description}

Provide:
1. Strategy assessment (strengths/weaknesses)
2. Required indicators and data
3. Entry/exit logic
4. Risk management approach
5. Market conditions where it works best
6. Potential pitfalls to avoid
"""

    response = model.generate_response(
        system_prompt=system_prompt,
        user_content=user_content,
        temperature=0.3,
        max_tokens=2000
    )

    cprint(response.content, "white")
    return response.content


def analyze_strategy_qwen(strategy_description):
    """Use QWEN Max to analyze a trading strategy"""

    cprint("\n=== QWEN Strategy Analysis ===\n", "cyan")

    model_factory = ModelFactory()
    model = model_factory.get_model("qwen", "qwen-max-2025-01-25")

    system_prompt = """You are a professional algorithmic trading strategist.
Analyze trading strategies with focus on practical implementation."""

    user_content = f"""
Analyze this trading strategy and provide implementation guidance:

{strategy_description}

Focus on:
1. Key components needed
2. Data requirements
3. Implementation complexity
4. Expected performance characteristics
"""

    response = model.generate_response(
        system_prompt=system_prompt,
        user_content=user_content,
        temperature=0.3,
        max_tokens=2000
    )

    cprint(response.content, "white")
    return response.content


# Example usage
if __name__ == "__main__":
    strategy = """
    Stock Strategy: Mean Reversion with Bollinger Bands

    Entry Rules:
    - Price crosses below lower Bollinger Band (2 std dev)
    - RSI < 30 (oversold)
    - Volume > 1.5x average volume

    Exit Rules:
    - Price returns to middle Bollinger Band
    - RSI > 50
    - Stop loss at 5% from entry

    Target: SPY, QQQ, AAPL (liquid large caps)
    """

    # Compare both models' analysis
    deepseek_analysis = analyze_strategy_deepseek(strategy)
    print("\n" + "="*60 + "\n")
    qwen_analysis = analyze_strategy_qwen(strategy)
```

### 2. Generating Stock Backtest Code

Create `src/scripts/ai_backtest_generator.py`:

```python
"""
AI Backtest Code Generator
Uses DeepSeek Coder or QWEN Coder to generate backtesting code
"""

from src.models.model_factory import ModelFactory
from termcolor import cprint
import os

def generate_stock_backtest_deepseek(strategy_name, strategy_rules):
    """Generate stock backtest code using DeepSeek"""

    model_factory = ModelFactory()
    model = model_factory.get_model("deepseek", "deepseek-chat")

    system_prompt = """You are an expert Python developer specializing in algorithmic trading.
Generate production-ready backtesting code using the backtesting.py library.

Requirements:
- Use pandas_ta for all technical indicators (NOT backtesting.py built-in indicators)
- Include proper error handling
- Add comments explaining the logic
- Use realistic commission (0.001)
- Include stop loss and position sizing
"""

    user_content = f"""
Generate a complete backtesting.py strategy for:

Strategy Name: {strategy_name}

Rules:
{strategy_rules}

Requirements:
1. Use yfinance to download data
2. Use pandas_ta for indicators
3. Implement the strategy as a class
4. Include main execution block
5. Print comprehensive stats
6. Save plot to file

Return only the Python code, ready to execute.
"""

    response = model.generate_response(
        system_prompt=system_prompt,
        user_content=user_content,
        temperature=0.2,
        max_tokens=2000
    )

    return response.content


def generate_stock_backtest_qwen(strategy_name, strategy_rules):
    """Generate stock backtest code using QWEN Coder"""

    model_factory = ModelFactory()
    model = model_factory.get_model("qwen", "qwen-coder-turbo")

    system_prompt = """You are a Python expert for trading strategy implementation.
Generate clean, well-documented backtesting code."""

    user_content = f"""
Create a backtesting.py strategy for:

{strategy_name}

Strategy Rules:
{strategy_rules}

Use:
- backtesting.py library
- pandas_ta for indicators
- yfinance for data
- Proper position sizing
"""

    response = model.generate_response(
        system_prompt=system_prompt,
        user_content=user_content,
        temperature=0.2,
        max_tokens=2000
    )

    return response.content


# Example usage
if __name__ == "__main__":
    strategy_name = "RSI_MACD_Combo"

    strategy_rules = """
Entry:
- RSI crosses above 30 (oversold to normal)
- MACD line crosses above signal line
- Volume > average volume

Exit:
- RSI crosses above 70 (overbought)
- MACD line crosses below signal line
- Stop loss: 3% from entry

Position Sizing: Risk 2% of capital per trade
"""

    print("Generating code with DeepSeek...")
    code_deepseek = generate_stock_backtest_deepseek(strategy_name, strategy_rules)

    # Save to file
    output_file = f"src/strategies/stocks/{strategy_name}_deepseek.py"
    with open(output_file, 'w') as f:
        f.write(code_deepseek)

    cprint(f"\nDeepSeek code saved to: {output_file}", "green")

    print("\nGenerating code with QWEN...")
    code_qwen = generate_stock_backtest_qwen(strategy_name, strategy_rules)

    output_file = f"src/strategies/stocks/{strategy_name}_qwen.py"
    with open(output_file, 'w') as f:
        f.write(code_qwen)

    cprint(f"QWEN code saved to: {output_file}", "green")
```

### 3. Generating Options Strategy Code

Create `src/scripts/ai_options_generator.py`:

```python
"""
AI Options Strategy Generator
Generates options trading code using DeepSeek and QWEN
"""

from src.models.model_factory import ModelFactory
from termcolor import cprint

def generate_options_strategy_deepseek(strategy_type, parameters):
    """Generate options strategy code using DeepSeek"""

    model_factory = ModelFactory()
    model = model_factory.get_model("deepseek", "deepseek-reasoner")

    system_prompt = """You are an expert options trader and Python developer.
Generate complete options trading code including:
- Greeks calculation
- Risk management
- Position construction
- P&L tracking
"""

    user_content = f"""
Generate Python code for this options strategy:

Strategy: {strategy_type}
Parameters: {parameters}

Requirements:
1. Use QuantLib for Greeks calculation
2. Use yfinance for options data
3. Include entry/exit logic
4. Track max profit/loss
5. Include position Greeks
6. Risk management checks

Provide complete, executable code.
"""

    response = model.generate_response(
        system_prompt=system_prompt,
        user_content=user_content,
        temperature=0.2,
        max_tokens=3000
    )

    return response.content


def generate_options_strategy_qwen(strategy_type, parameters):
    """Generate options strategy code using QWEN"""

    model_factory = ModelFactory()
    model = model_factory.get_model("qwen", "qwen-coder-turbo")

    system_prompt = """Expert options trading programmer.
Create production-ready options strategy code."""

    user_content = f"""
Create Python code for:

Options Strategy: {strategy_type}
Config: {parameters}

Include:
- Options chain analysis
- Strike selection
- Greeks monitoring
- Risk limits
- Position tracking
"""

    response = model.generate_response(
        system_prompt=system_prompt,
        user_content=user_content,
        temperature=0.2,
        max_tokens=3000
    )

    return response.content


# Example usage
if __name__ == "__main__":
    # Iron Condor example
    strategy = "Iron Condor"
    params = {
        "underlying": "SPY",
        "dte_range": "30-45 days",
        "short_delta": "0.20",
        "wing_width": "$5",
        "profit_target": "50% of max profit",
        "stop_loss": "2x credit received"
    }

    print("Generating Iron Condor code with DeepSeek...")
    code = generate_options_strategy_deepseek(strategy, params)

    output_file = "src/strategies/options/iron_condor_deepseek.py"
    with open(output_file, 'w') as f:
        # Extract just the code if wrapped in markdown
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        f.write(code)

    cprint(f"\nCode saved to: {output_file}", "green")

    # Covered Call example
    strategy = "Covered Call"
    params = {
        "underlying": "AAPL",
        "num_shares": 100,
        "strike_selection": "5% OTM",
        "min_premium": "$0.50",
        "dte": "30-45 days"
    }

    print("\nGenerating Covered Call code with QWEN...")
    code = generate_options_strategy_qwen(strategy, params)

    output_file = "src/strategies/options/covered_call_qwen.py"
    with open(output_file, 'w') as f:
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        f.write(code)

    cprint(f"Code saved to: {output_file}", "green")
```

### 4. Real-time Market Analysis

Create `src/agents/ai_analysis_agent.py`:

```python
"""
AI Market Analysis Agent
Uses DeepSeek and QWEN for real-time market analysis
"""

import yfinance as yf
from src.models.model_factory import ModelFactory
from termcolor import cprint
import pandas as pd
import pandas_ta as ta

class AIAnalysisAgent:
    """AI-powered market analysis using DeepSeek and QWEN"""

    def __init__(self, use_model="deepseek"):
        """
        Initialize the agent

        Args:
            use_model: "deepseek" or "qwen"
        """
        self.model_factory = ModelFactory()

        if use_model == "deepseek":
            self.model = self.model_factory.get_model("deepseek", "deepseek-reasoner")
        else:
            self.model = self.model_factory.get_model("qwen", "qwen-max-2025-01-25")

        cprint(f"\nAI Analysis Agent initialized with {use_model}", "green")

    def analyze_stock(self, ticker):
        """Analyze a stock using AI"""

        cprint(f"\n{'='*60}", "cyan")
        cprint(f"Analyzing {ticker}", "cyan")
        cprint(f"{'='*60}\n", "cyan")

        # Get recent data
        data = yf.download(ticker, period="3mo", interval="1d", progress=False)

        if data.empty:
            cprint(f"No data available for {ticker}", "red")
            return None

        # Calculate indicators
        data['RSI'] = ta.rsi(data['Close'], length=14)
        macd = ta.macd(data['Close'])
        data['MACD'] = macd['MACD_12_26_9']
        data['Signal'] = macd['MACDs_12_26_9']
        data['SMA20'] = ta.sma(data['Close'], length=20)
        data['SMA50'] = ta.sma(data['Close'], length=50)

        # Get latest values
        latest = data.iloc[-1]
        prev = data.iloc[-2]

        # Prepare market snapshot
        snapshot = f"""
Ticker: {ticker}
Current Price: ${latest['Close']:.2f}
Change: {((latest['Close'] - prev['Close']) / prev['Close'] * 100):.2f}%

Technical Indicators:
- RSI(14): {latest['RSI']:.2f}
- MACD: {latest['MACD']:.4f}
- Signal: {latest['Signal']:.4f}
- SMA(20): ${latest['SMA20']:.2f}
- SMA(50): ${latest['SMA50']:.2f}

Volume: {latest['Volume']:,.0f}
Avg Volume (20d): {data['Volume'].tail(20).mean():,.0f}

Recent Performance:
- 1 Week: {((latest['Close'] - data['Close'].iloc[-5]) / data['Close'].iloc[-5] * 100):.2f}%
- 1 Month: {((latest['Close'] - data['Close'].iloc[-20]) / data['Close'].iloc[-20] * 100):.2f}%
"""

        # Get AI analysis
        system_prompt = """You are a professional stock analyst and trader.
Analyze the technical data and provide:
1. Current market trend assessment
2. Trading recommendation (BUY/SELL/HOLD)
3. Key support/resistance levels
4. Risk factors
5. Suggested entry/exit points

Be concise and actionable."""

        user_content = f"""Analyze this stock data and provide trading recommendation:

{snapshot}

Provide clear, actionable guidance."""

        response = self.model.generate_response(
            system_prompt=system_prompt,
            user_content=user_content,
            temperature=0.3,
            max_tokens=800
        )

        cprint("\nAI Analysis:\n", "yellow")
        cprint(response.content, "white")

        return response.content

    def analyze_options_opportunity(self, ticker):
        """Analyze options trading opportunities"""

        cprint(f"\nAnalyzing options for {ticker}...", "cyan")

        # Get stock data and options chain
        stock = yf.Ticker(ticker)
        current_price = stock.history(period="1d")['Close'].iloc[-1]

        # Get implied volatility and basic info
        info = stock.info
        iv = info.get('impliedVolatility', 0) * 100 if 'impliedVolatility' in info else None

        snapshot = f"""
Ticker: {ticker}
Current Price: ${current_price:.2f}
Implied Volatility: {iv:.2f}% (if available)

Market Conditions:
- Beta: {info.get('beta', 'N/A')}
- 52-Week Range: ${info.get('fiftyTwoWeekLow', 0):.2f} - ${info.get('fiftyTwoWeekHigh', 0):.2f}
"""

        system_prompt = """You are an expert options trader.
Recommend options strategies based on current market conditions.
Consider volatility, trend, and risk/reward."""

        user_content = f"""Based on this data, recommend the best options strategy:

{snapshot}

Suggest:
1. Optimal strategy (covered call, cash-secured put, spread, etc.)
2. Strike selection guidance
3. Expiration timeframe
4. Risk management approach
"""

        response = self.model.generate_response(
            system_prompt=system_prompt,
            user_content=user_content,
            temperature=0.3,
            max_tokens=800
        )

        cprint("\nOptions Strategy Recommendation:\n", "yellow")
        cprint(response.content, "white")

        return response.content


# Example usage
if __name__ == "__main__":
    # Test with DeepSeek
    agent_ds = AIAnalysisAgent(use_model="deepseek")
    agent_ds.analyze_stock("AAPL")
    agent_ds.analyze_options_opportunity("AAPL")

    print("\n" + "="*60 + "\n")

    # Test with QWEN
    agent_qwen = AIAnalysisAgent(use_model="qwen")
    agent_qwen.analyze_stock("SPY")
    agent_qwen.analyze_options_opportunity("SPY")
```

### 5. Using RBI Agent with DeepSeek/QWEN

The RBI Agent can use either DeepSeek or QWEN. Edit `src/agents/rbi_agent.py`:

```python
# At the top of rbi_agent.py, change the model configuration:

# Use DeepSeek for all tasks
RESEARCH_CONFIG = {
    "type": "deepseek",
    "name": "deepseek-chat"
}

BACKTEST_CONFIG = {
    "type": "deepseek",
    "name": "deepseek-reasoner"
}

DEBUG_CONFIG = {
    "type": "deepseek",
    "name": "deepseek-chat"
}

# OR use QWEN for all tasks
RESEARCH_CONFIG = {
    "type": "qwen",
    "name": "qwen-max-2025-01-25"
}

BACKTEST_CONFIG = {
    "type": "qwen",
    "name": "qwen-coder-turbo"  # Use coder for backtest generation
}

DEBUG_CONFIG = {
    "type": "qwen",
    "name": "qwen-turbo"  # Use turbo for fast debugging
}
```

Then run normally:

```bash
cd /home/user/TradingAgent
python src/agents/rbi_agent.py
```

## Model Selection Guide

### When to Use DeepSeek

**Best for:**
- Complex strategy reasoning
- Cost-effective analysis (~$0.027 per backtest)
- When you want to see the thinking process
- Trading strategy development

**Recommended Models:**
- `deepseek-reasoner`: Strategy analysis, complex decisions
- `deepseek-chat`: Code generation, quick analysis

### When to Use QWEN

**Best for:**
- Long document analysis (1M token context with qwen-long)
- Fast iterations with qwen-turbo
- Code generation with qwen-coder-turbo
- When you need latest reasoning (Qwen Max 2025)

**Recommended Models:**
- `qwen-max-2025-01-25`: Complex analysis, strategy development
- `qwen-coder-turbo`: Backtest code generation
- `qwen-turbo`: Quick market analysis, high-frequency decisions
- `qwen-long`: Analyzing long research papers, multiple videos

## Best Practices

1. **Use appropriate temperature**:
   - 0.2-0.3 for code generation
   - 0.3-0.5 for analysis
   - 0.5-0.7 for creative strategy ideas

2. **Provide context**: Give the model enough information about your goals, risk tolerance, and constraints

3. **Validate AI output**: Always review and test generated code before using it

4. **Iterate**: Use AI to refine strategies iteratively

5. **Combine models**: Use DeepSeek for reasoning, QWEN for code generation

## Cost Comparison

**DeepSeek:**
- deepseek-chat: $0.14 / 1M input tokens, $0.28 / 1M output
- deepseek-reasoner: Similar pricing

**QWEN:**
- Varies by model and region
- Generally competitive with GPT-4 pricing
- Check current pricing at https://qwen.ai/apiplatform

## Troubleshooting

### Issue: "Model not available"
**Solution**: Check API key in .env file, ensure correct key name (DEEPSEEK_KEY or QWEN_API_KEY)

### Issue: "Generated code has errors"
**Solution**: Use the DEBUG_CONFIG in RBI agent or manually review/fix the code

### Issue: "QWEN API connection failed"
**Solution**: Ensure you're using international base URL: https://dashscope-intl.aliyuncs.com/compatible-mode/v1

## Next Steps

1. Review `BACKTESTING_STOCKS_GUIDE.md` for stock backtesting details
2. See `BACKTESTING_OPTIONS_GUIDE.md` for options strategies
3. Check `TASTYTRADE_INTEGRATION_GUIDE.md` for live trading
4. Experiment with different AI models for your use case

Built with love by Moon Dev
