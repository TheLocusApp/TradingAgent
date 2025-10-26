# Quick Start: Options & Stocks Trading with TradingAgent

## Welcome!

This guide provides a quick overview of the new capabilities added to TradingAgent for options and stocks trading.

## What's New

TradingAgent now supports:
1. **Stock Backtesting** - Comprehensive backtesting framework
2. **Options Backtesting** - Options-specific strategies and Greeks
3. **TastyTrade Integration** - Connect to TastyTrade broker for live trading
4. **QWEN AI Model** - New AI model support from Alibaba Cloud
5. **Enhanced DeepSeek Usage** - Guides for using DeepSeek for trading

## Quick Links to Guides

### 1. Options Backtesting
📖 **[BACKTESTING_OPTIONS_GUIDE.md](./BACKTESTING_OPTIONS_GUIDE.md)**

Learn how to:
- Install options backtesting libraries (optopsy, QuantLib)
- Get options data from Yahoo Finance or TastyTrade
- Backtest iron condors, covered calls, credit spreads
- Calculate Greeks (delta, gamma, theta, vega)
- Use AI to generate options strategies

**Quick Example:**
```bash
pip install optopsy yfinance QuantLib-Python
python src/strategies/options/iron_condor_strategy.py
```

### 2. Stock Backtesting
📖 **[BACKTESTING_STOCKS_GUIDE.md](./BACKTESTING_STOCKS_GUIDE.md)**

Learn how to:
- Install stock backtesting libraries
- Download data from Yahoo Finance, Alpaca
- Create strategies with RSI, MACD, Bollinger Bands
- Optimize parameters
- Use RBI Agent to auto-generate strategies from videos

**Quick Example:**
```bash
pip install backtesting yfinance pandas-ta
python src/strategies/stocks/sma_crossover.py
```

### 3. TastyTrade Broker Integration
📖 **[TASTYTRADE_INTEGRATION_GUIDE.md](./TASTYTRADE_INTEGRATION_GUIDE.md)**

Learn how to:
- Set up TastyTrade API access
- Connect TradingAgent to TastyTrade
- Execute stock and options orders
- Stream real-time market data
- Monitor positions and manage risk

**Quick Example:**
```bash
pip install tastytrade
# Add credentials to .env
python src/agents/tastytrade_agent.py
```

### 4. Using DeepSeek & QWEN for Trading
📖 **[DEEPSEEK_QWEN_TRADING_GUIDE.md](./DEEPSEEK_QWEN_TRADING_GUIDE.md)**

Learn how to:
- Use DeepSeek for strategy analysis
- Use QWEN for code generation
- Generate backtests with AI
- Analyze markets in real-time
- Choose the right model for your task

**Quick Example:**
```bash
# Add API keys to .env
DEEPSEEK_KEY=your_key
QWEN_API_KEY=your_key

python src/scripts/ai_strategy_analyzer.py
```

## 5-Minute Quick Start

### Option 1: Backtest a Stock Strategy

```bash
conda activate tflow
cd /home/user/TradingAgent

# Create a simple strategy idea
echo "Buy when RSI < 30 and MACD crosses up, sell when RSI > 70" > src/data/rbi/ideas.txt

# Let AI generate and run the backtest
python src/agents/rbi_agent.py
```

### Option 2: Backtest an Options Strategy

```bash
conda activate tflow
cd /home/user/TradingAgent

# Install options libraries
pip install optopsy QuantLib-Python

# Run example iron condor backtest
python src/strategies/options/iron_condor_complete.py
```

### Option 3: Connect to TastyTrade (Paper Trading)

```bash
conda activate tflow
cd /home/user/TradingAgent

# Install TastyTrade SDK
pip install tastytrade

# Add to .env:
# TASTYTRADE_USERNAME=your_email
# TASTYTRADE_PASSWORD=your_password
# TASTYTRADE_ACCOUNT_NUMBER=your_account

# Test connection
python src/integrations/tastytrade_connector.py
```

## Architecture Overview

```
TradingAgent/
├── src/
│   ├── agents/
│   │   ├── rbi_agent.py              # AI strategy generator
│   │   ├── tastytrade_agent.py       # TastyTrade trading agent (NEW)
│   │   └── ai_analysis_agent.py      # Real-time AI analysis (NEW)
│   ├── models/
│   │   ├── model_factory.py          # Updated with QWEN support
│   │   ├── qwen_model.py             # NEW: QWEN integration
│   │   ├── deepseek_model.py         # Existing
│   │   └── README.md                 # Updated with QWEN docs
│   ├── strategies/
│   │   ├── stocks/                   # Stock strategies (NEW)
│   │   └── options/                  # Options strategies (NEW)
│   ├── integrations/
│   │   └── tastytrade_connector.py   # NEW: TastyTrade API wrapper
│   └── scripts/
│       ├── ai_strategy_analyzer.py   # NEW: AI strategy analysis
│       ├── ai_backtest_generator.py  # NEW: AI code generation
│       └── ai_options_generator.py   # NEW: Options code gen
└── docs/
    ├── BACKTESTING_OPTIONS_GUIDE.md          # NEW: Options guide
    ├── BACKTESTING_STOCKS_GUIDE.md           # NEW: Stocks guide
    ├── TASTYTRADE_INTEGRATION_GUIDE.md       # NEW: Broker integration
    ├── DEEPSEEK_QWEN_TRADING_GUIDE.md        # NEW: AI models guide
    └── QUICK_START_OPTIONS_STOCKS.md         # NEW: This file
```

## Supported AI Models

TradingAgent now supports these AI models:

| Model | Best For | Cost |
|-------|----------|------|
| **DeepSeek Reasoner** | Complex strategy analysis | ~$0.027/backtest |
| **DeepSeek Chat** | Quick code generation | Very low |
| **QWEN Max 2025** | Latest reasoning, complex analysis | Competitive |
| **QWEN Coder Turbo** | Fast code generation | Low |
| **QWEN Turbo** | High-frequency decisions | Very low |
| **QWEN Long** | Long documents (1M tokens) | Moderate |
| Claude, GPT-4, etc. | Various | As before |

## Environment Variables Needed

Add these to your `.env` file:

```bash
# Existing keys
ANTHROPIC_KEY=your_claude_key
OPENAI_KEY=your_openai_key
DEEPSEEK_KEY=your_deepseek_key

# NEW: QWEN support
QWEN_API_KEY=your_qwen_key

# NEW: TastyTrade integration
TASTYTRADE_USERNAME=your_username
TASTYTRADE_PASSWORD=your_password
TASTYTRADE_ACCOUNT_NUMBER=your_account_number
```

## Common Workflows

### Workflow 1: Develop a New Stock Strategy

1. Describe strategy in plain English
2. Use DeepSeek/QWEN to analyze viability
3. Generate backtest code with AI
4. Run backtest on historical data
5. Optimize parameters
6. Deploy to paper trading via TastyTrade

### Workflow 2: Options Income Strategy

1. Research options strategy (e.g., wheel, iron condor)
2. Use AI to generate implementation code
3. Backtest with historical options data
4. Calculate Greeks and risk metrics
5. Deploy to TastyTrade sandbox
6. Monitor and adjust

### Workflow 3: AI-Powered Market Analysis

1. Configure watchlist (SPY, QQQ, AAPL, etc.)
2. Run AI analysis agent with DeepSeek/QWEN
3. Get real-time recommendations
4. Review AI reasoning
5. Execute via TastyTrade or manual review

## Best Practices

1. ✅ **Always test in sandbox/paper trading first**
2. ✅ **Use realistic commission and slippage assumptions**
3. ✅ **Validate AI-generated code before running**
4. ✅ **Start with small position sizes**
5. ✅ **Backtest across multiple market conditions**
6. ✅ **Use stop losses and risk management**
7. ✅ **Keep detailed logs of all trades**

## Getting Help

- **GitHub Issues**: Report bugs or request features
- **Documentation**: Read the detailed guides linked above
- **Moon Dev Discord**: Join the community
- **YouTube**: Watch Moon Dev's tutorials

## Next Steps

1. Choose your path: **Options** or **Stocks** (or both!)
2. Read the relevant guide(s) above
3. Set up your API keys
4. Run the quick start example
5. Develop your first strategy
6. Join the community and share your results!

## Important Disclaimers

⚠️ **Risk Warning**: Trading stocks and options involves substantial risk of loss. This is an experimental educational project. No guarantees of profitability.

⚠️ **Testing Required**: Always thoroughly test strategies in paper trading before risking real capital.

⚠️ **AI Validation**: AI-generated code and analysis should be reviewed and validated by humans before use.

---

**Built with love by Moon Dev** 🌙

Ready to get started? Pick a guide above and dive in!
