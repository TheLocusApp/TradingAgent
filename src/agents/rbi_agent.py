"""
🌙 Moon Dev's RBI AI (Research-Backtest-Implement)
Built with love by Moon Dev 🚀

Required Setup:
1. Create folder structure:
   src/
   ├── data/
   │   └── rbi/
   │       ├── MM_DD_YYYY/         # Date-based folder (created automatically)
   │       │   ├── research/       # Strategy research outputs
   │       │   ├── backtests/      # Initial backtest code
   │       │   ├── backtests_package/ # Package-fixed code
   │       │   ├── backtests_final/ # Debugged backtest code
   │       │   └── charts/         # Charts output directory
   │       └── ideas.txt          # Trading ideas to process

2. Environment Variables:
   - No API keys needed! We're using local Ollama models 🎉

3. Create ideas.txt:
   - One trading idea per line
   - Can be YouTube URLs, PDF links, or text descriptions
   - Lines starting with # are ignored

This AI automates the RBI process:
1. Research: Analyzes trading strategies from various sources
2. Backtest: Creates backtests for promising strategies
3. Debug: Fixes technical issues in generated backtests

✨ NEW FEATURE: All outputs are now organized in date-based folders (MM_DD_YYYY)
This helps keep your strategy research organized by day!

Remember: Past performance doesn't guarantee future results!
"""

import os

## Previous presets (kept for easy switching) 👇
# RESEARCH_CONFIG = {
#     "type": "deepseek",
#     "name": "deepseek-chat"  # Using DeepSeek Chat for research
# }
# 
# BACKTEST_CONFIG = {
#     "type": "deepseek", 
#     "name": "deepseek-reasoner"  # Using DeepSeek Reasoner for backtesting
# }
# 
# DEBUG_CONFIG = {
#     "type": "deepseek",
#     "name": "deepseek-chat"  # Using DeepSeek Chat for debugging
# }
# 
# # DEBUG_CONFIG = {
# #     "type": "ollama",
# #     "name": "deepseek-r1"  # Using Ollama's DeepSeek-R1 for debugging
# # }
# 
# PACKAGE_CONFIG = {
#     "type": "deepseek",
#     "name": "deepseek-chat"  # Using DeepSeek Chat for package optimization
# }

# Dynamic Model Configuration - Reads from environment variable set by frontend
def get_model_config():
    """Get model configuration from environment variable or use default"""
    model_type = os.getenv('RBI_AI_MODEL', 'deepseek').lower()
    
    model_defaults = {
        'deepseek': {'type': 'deepseek', 'name': 'deepseek-chat'},
        'openai': {'type': 'openai', 'name': 'gpt-4o'},
        'claude': {'type': 'claude', 'name': 'claude-3-5-sonnet-20241022'},
        'gemini': {'type': 'gemini', 'name': 'gemini-2.5-flash'},
        'xai': {'type': 'xai', 'name': 'grok-4-fast-reasoning'},
        'groq': {'type': 'groq', 'name': 'llama-3.3-70b-versatile'},
    }
    
    return model_defaults.get(model_type, model_defaults['deepseek'])

# Initialize configs (will be dynamically updated based on environment)
RESEARCH_CONFIG = get_model_config()
BACKTEST_CONFIG = get_model_config()
DEBUG_CONFIG = get_model_config()
PACKAGE_CONFIG = get_model_config()



################

# Model Configuration
# Using a mix of Ollama models and DeepSeek API
# RESEARCH_CONFIG = {
#     "type": "ollama",
#     "name": "llama3.2"  # Using Llama 3.2 for research
# }

# RESEARCH_CONFIG = {
#     "type": "deepseek",
#     "name": "deepseek-chat"  # Using Llama 3.2 for research
# }

# BACKTEST_CONFIG = {
#     "type": "openai", 
#     "name": "o3"  # Using O3-mini for backtesting
# }

# DEBUG_CONFIG = {
#     "type": "openai",
#     "name": "o3"  # Using GPT-4.1 for debugging
# }

# # DEBUG_CONFIG = {
# #     "type": "ollama",
# #     "name": "deepseek-r1"  # Using Ollama's DeepSeek-R1 for debugging
# # }

# # PACKAGE_CONFIG = {
# #     "type": "deepseek",
# #     "name": "deepseek-chat"  # Using Llama 3.2 for package optimization
# # }

# PACKAGE_CONFIG = {
#     "type": "openai",
#     "name": "o3"  # Using Llama 3.2 for package optimization
# }


# PACKAGE_CONFIG = {
#     "type": "ollama",
#     "name": "llama3.2"  # Using Llama 3.2 for package optimization
# }


# DeepSeek Model Selection per AI
# "gemma:2b",     # Google's Gemma 2B model
#         "llama3.2",
# Using a mix of models for different tasks
# RESEARCH_MODEL = "llama3.2"           # Llama 3.2 for research
# BACKTEST_MODEL = "deepseek-reasoner"  # DeepSeek API for backtesting
# DEBUG_MODEL = "deepseek-r1"           # Ollama DeepSeek-R1 for debugging
# PACKAGE_MODEL = "llama3.2"            # Llama 3.2 for package optimization

# AI Prompts

RESEARCH_PROMPT = """
You are Moon Dev's Research AI 🌙

IMPORTANT NAMING RULES:
1. Create a UNIQUE TWO-WORD NAME for this specific strategy
2. The name must be DIFFERENT from any generic names like "TrendFollower" or "MomentumStrategy"
3. First word should describe the main approach (e.g., Adaptive, Neural, Quantum, Fractal, Dynamic)
4. Second word should describe the specific technique (e.g., Reversal, Breakout, Oscillator, Divergence)
5. Make the name SPECIFIC to this strategy's unique aspects

Examples of good names:
- "AdaptiveBreakout" for a strategy that adjusts breakout levels
- "FractalMomentum" for a strategy using fractal analysis with momentum
- "QuantumReversal" for a complex mean reversion strategy
- "NeuralDivergence" for a strategy focusing on divergence patterns

BAD names to avoid:
- "TrendFollower" (too generic)
- "SimpleMoving" (too basic)
- "PriceAction" (too vague)

Output format must start with:
STRATEGY_NAME: [Your unique two-word name]

Then analyze the trading strategy content and create detailed instructions.
Focus on:
1. Key strategy components
2. Entry/exit rules
3. Risk management
4. Required indicators

Your complete output must follow this format:
STRATEGY_NAME: [Your unique two-word name]

STRATEGY_DETAILS:
[Your detailed analysis]

Remember: The name must be UNIQUE and SPECIFIC to this strategy's approach!
"""

BACKTEST_PROMPT = """
You are Moon Dev's Backtest AI 🌙 ONLY SEND BACK CODE, NO OTHER TEXT.
Create a backtesting.py implementation for the strategy.
USE BACKTESTING.PY
Include:
1. All necessary imports
2. Strategy class with indicators
3. Entry/exit logic
4. Risk management
5. your size should be 1,000,000
6. If you need indicators use TA lib or pandas TA.

IMPORTANT DATA HANDLING:
1. Clean column names by removing spaces: data.columns = data.columns.str.strip().str.lower()
2. Drop any unnamed columns: data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
3. Ensure proper column mapping to match backtesting requirements:
   - Required columns: 'Open', 'High', 'Low', 'Close', 'Volume'
   - Use proper case (capital first letter)

FOR THE PYTHON BACKTESTING LIBRARY USE BACKTESTING.PY AND SEND BACK ONLY THE CODE, NO OTHER TEXT.

INDICATOR CALCULATION RULES:
1. ALWAYS use self.I() wrapper for ANY indicator calculations
2. Use talib functions instead of pandas operations:
   - Instead of: self.data.Close.rolling(20).mean()
   - Use: self.I(talib.SMA, self.data.Close, timeperiod=20)
3. For swing high/lows use talib.MAX/MIN:
   - Instead of: self.data.High.rolling(window=20).max()
   - Use: self.I(talib.MAX, self.data.High, timeperiod=20)

🚨 CRITICAL: TA-LIB REQUIRES FLOAT64 DTYPE 🚨
TA-Lib functions REQUIRE numpy arrays with dtype float64 (double precision).
yfinance returns mixed dtypes (int64 for Volume, float64 for prices).

❌ WRONG - Will crash with "input array type is not double":
```python
self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
```

✅ CORRECT - Explicit conversion to float:
```python
self.vol_sma = self.I(talib.SMA, self.data.Volume.astype(float), timeperiod=20)
self.rsi = self.I(talib.RSI, self.data.Close.astype(float), timeperiod=14)
self.atr = self.I(talib.ATR, self.data.High.astype(float), self.data.Low.astype(float), self.data.Close.astype(float), timeperiod=14)
```

⚠️ ALWAYS add .astype(float) to ALL data columns passed to TA-Lib functions!
This applies to: Close, Open, High, Low, Volume - ALL of them!

🚨 CRITICAL: CUSTOM INDICATOR FUNCTIONS MUST RETURN ARRAYS 🚨
When using self.I() with custom functions, they MUST return numpy arrays of same length as data.

❌ WRONG - Returns scalar:
```python
def vix_shift_func(x):
    return x[-5]  # Single value - WILL CRASH
```

✅ CORRECT - Returns array:
```python
def vix_shift_func(x):
    result = np.empty_like(x)
    for i in range(len(x)):
        result[i] = x[max(0, i-5)]  # Shift by 5 bars
    return result

self.vix_shifted = self.I(vix_shift_func, self.data.VIX)
```

Every custom function passed to self.I() must return an array matching data length!

BACKTEST EXECUTION ORDER:
1. Run initial backtest with default parameters first
2. Print full stats using print(stats) and print(stats._strategy)
3. no optimization code needed, just print the final stats, make sure full stats are printed, not just part or some. stats = bt.run() print(stats) is an example of the last line of code. no need for plotting ever.

do not creeate charts to plot this, just print stats. no charts needed.

🚨 CRITICAL POSITION SIZING RULE - THIS DETERMINES IF STRATEGY WORKS OR FAILS 🚨

When calculating position sizes in backtesting.py, the size parameter MUST be:
1. A fraction between 0 and 1 (for percentage of equity) - THIS IS THE ONLY WAY THAT WORKS
2. NEVER use integer share counts - backtesting.py will SILENTLY REJECT them (0 trades!)
3. NEVER use floating point numbers like 3546.0993 - backtesting.py will SILENTLY REJECT them!

🚨 IF YOU USE WRONG POSITION SIZING:
- backtesting.py will NOT throw an error
- It will silently reject your trades
- You will get 0 trades and 0% return
- This is the #1 reason strategies fail!

CORRECT position sizing formula (THE ONLY WAY):
```python
def calculate_position_size(self, entry_price, stop_loss, risk_pct):
    # Calculate risk distance
    risk_distance = abs(entry_price - stop_loss) / entry_price
    
    # Calculate risk amount in dollars
    risk_amount = self.equity * (risk_pct / 100)
    
    # Calculate position value needed
    position_value = risk_amount / risk_distance
    
    # Convert to FRACTION of equity (0 to 1)
    size = position_value / self.equity
    
    # Ensure it's between 0 and 1
    size = max(0.01, min(size, 1.0))
    
    return size  # Return as fraction, NOT as integer!

# Usage:
size = calculate_position_size(entry_price=100, stop_loss=95, risk_pct=2)
self.buy(size=size, sl=stop_loss, tp=take_profit)  # size is 0.0-1.0
```

❌ WRONG EXAMPLES (WILL FAIL SILENTLY):
```python
position_size = int(round(400000))
self.buy(size=position_size)  # ❌ FAILS - integer share count

position_size = 400000.0
self.buy(size=position_size)  # ❌ FAILS - floating point number

position_size = 3546.0993
self.buy(size=position_size)  # ❌ FAILS - floating point number
```

✅ CORRECT EXAMPLES (WILL WORK):
```python
size = 0.4
self.buy(size=size)  # ✅ WORKS - 40% of equity

size = 0.5
self.buy(size=size)  # ✅ WORKS - 50% of equity

size = min(0.1, position_value / self.equity)
self.buy(size=size)  # ✅ WORKS - fraction of equity
```

RISK MANAGEMENT & POSITION API:
1. Always calculate position sizes based on risk percentage
2. Use proper stop loss and take profit calculations
3. Print entry/exit signals with Moon Dev themed messages

🚨 CRITICAL: BACKTESTING.PY ORDER VALIDATION RULES 🚨

backtesting.py has STRICT validation for all orders. UNDERSTAND THESE RULES OR YOUR CODE WILL CRASH!

FOR LONG ORDERS (self.buy):
✅ REQUIRED: SL < Entry < TP
```python
entry = 100.00
sl = 99.00      # MUST be BELOW entry
tp = 102.00     # MUST be ABOVE entry
self.buy(size=0.5, sl=sl, tp=tp)  # ✅ WORKS: 99 < 100 < 102
```

❌ WRONG - Will crash:
```python
entry = 100.00
sl = 101.00     # WRONG! Above entry
tp = 102.00
self.buy(size=0.5, sl=sl, tp=tp)  # ❌ CRASHES: 101 > 100
```

FOR SHORT ORDERS (self.sell):
✅ REQUIRED: TP < Entry < SL
```python
entry = 100.00
sl = 101.00     # MUST be ABOVE entry
tp = 98.00      # MUST be BELOW entry
self.sell(size=0.5, sl=sl, tp=tp)  # ✅ WORKS: 98 < 100 < 101
```

❌ WRONG - Will crash:
```python
entry = 100.00
sl = 99.00      # WRONG! Below entry
tp = 98.00
self.sell(size=0.5, sl=sl, tp=tp)  # ❌ CRASHES: 99 < 100
```

CORRECT ENTRY/EXIT LOGIC TEMPLATE:
```python
def next(self):
    current_price = self.data.Close[-1]
    
    if not self.position:
        # LONG ENTRY
        if buy_signal:
            entry_price = current_price
            stop_loss = entry_price - 0.05  # MUST be BELOW entry
            take_profit = entry_price + 0.10  # MUST be ABOVE entry
            
            # Validate before submitting
            if stop_loss < entry_price < take_profit:  # ✅ Always check!
                size = self.calculate_position_size(entry_price, stop_loss)
                self.buy(size=size, sl=stop_loss, tp=take_profit)
        
        # SHORT ENTRY
        elif sell_signal:
            entry_price = current_price
            stop_loss = entry_price + 0.05  # MUST be ABOVE entry
            take_profit = entry_price - 0.10  # MUST be BELOW entry
            
            # Validate before submitting
            if take_profit < entry_price < stop_loss:  # ✅ Always check!
                size = self.calculate_position_size(entry_price, stop_loss)
                self.sell(size=size, sl=stop_loss, tp=take_profit)
```

🚨 HOW TO CALCULATE SL/TP CORRECTLY USING ATR 🚨

FOR LONG ORDERS (buying, expecting price to go UP):
```python
entry_price = self.data.Close[-1]
atr = self.atr[-1]  # Assuming you have self.atr = self.I(talib.ATR, ...)

# ✅ CORRECT: SL BELOW entry, TP ABOVE entry
stop_loss_price = entry_price - (2.0 * atr)     # SUBTRACT for SL (below entry)
take_profit_price = entry_price + (3.0 * atr)   # ADD for TP (above entry)

# Validate: SL < Entry < TP
if stop_loss_price < entry_price < take_profit_price:
    size = self.calculate_position_size(entry_price, stop_loss_price)
    self.buy(size=size, sl=stop_loss_price, tp=take_profit_price)
else:
    print(f"🌙 MOON DEV DEBUG: Long order validation failed - SL: {stop_loss_price}, Entry: {entry_price}, TP: {take_profit_price}")
```

FOR SHORT ORDERS (selling, expecting price to go DOWN):
```python
entry_price = self.data.Close[-1]
atr = self.atr[-1]

# ✅ CORRECT: TP BELOW entry, SL ABOVE entry
take_profit_price = entry_price - (3.0 * atr)   # SUBTRACT for TP (below entry, profit when price drops)
stop_loss_price = entry_price + (2.0 * atr)     # ADD for SL (above entry, stop when price rises)

# Validate: TP < Entry < SL
if take_profit_price < entry_price < stop_loss_price:
    size = self.calculate_position_size(entry_price, stop_loss_price)
    self.sell(size=size, sl=stop_loss_price, tp=take_profit_price)
else:
    print(f"🌙 MOON DEV DEBUG: Short order validation failed - TP: {take_profit_price}, Entry: {entry_price}, SL: {stop_loss_price}")
```

❌ COMMON MISTAKE TO AVOID:
```python
# ❌ WRONG for SHORT orders - TP ends up ABOVE entry!
take_profit_price = entry_price + (3.0 * atr)  # This puts TP above entry - WRONG!
stop_loss_price = entry_price - (2.0 * atr)    # This puts SL below entry - WRONG!
# Result: ValueError: Short orders require: TP < LIMIT < SL
```

🚨 CRITICAL: POSITION OBJECT API (backtesting.py) 🚨
The Position object has VERY LIMITED attributes. Here's what EXISTS:

✅ AVAILABLE Position attributes:
- self.position.size (current position size, 0 if no position)
- self.position.is_long (True if long position)
- self.position.is_short (True if short position)
- self.position.pl (current profit/loss)
- self.position.pl_pct (current profit/loss percentage)

❌ DOES NOT EXIST (will crash):
- self.position.price (NO! Track entry price manually)
- self.position.sl (NO! Cannot read stop loss)
- self.position.tp (NO! Cannot read take profit)
- self.position.modify() (NO! Cannot modify existing position)
- self.position.set_sl() (NO! Cannot set stop loss after entry)

✅ CORRECT way to track entry price:
```python
def init(self):
    self.entry_price = None

def next(self):
    if not self.position:
        # Entry logic
        self.buy(sl=stop_price, tp=target_price, size=size)
        self.entry_price = self.data.Close[-1]  # Track manually!
    elif self.position.is_long:
        # Use self.entry_price, NOT self.position.price
        if self.data.Close[-1] >= self.entry_price + profit_target:
            self.position.close()
```

✅ Stop loss/take profit MUST be set at entry time:
```python
self.buy(sl=stop_price, tp=target_price, size=size)  # Set SL/TP here!
```

❌ CANNOT modify SL/TP after entry - backtesting.py doesn't support it!

If you need indicators use TA lib or pandas TA. 

🚨 CRITICAL: USE YFINANCE TO DOWNLOAD DATA DYNAMICALLY 🚨

⚠️ YFINANCE DATA LIMITS (CRITICAL - DO NOT IGNORE):
- 5-minute data: MAX 60 days only! (yfinance limitation)
- 15-minute data: MAX 60 days only!
- 1-hour data: MAX 730 days (2 years)
- Daily data: MAX unlimited

🚨 IF THE STRATEGY MENTIONS "5 MINUTE" OR "5M" CANDLES:
Use 1-hour data instead! Convert the logic to hourly timeframe.
NEVER try to download 5m data for more than 60 days - it will CRASH!

```python
import yfinance as yf
import pandas as pd

# Download data for the ticker specified in the strategy (e.g., SPY, BTC-USD, etc.)
ticker = yf.Ticker("TICKER_SYMBOL")  # Replace TICKER_SYMBOL with actual ticker

# ALWAYS use 1-hour data for backtesting (most reliable)
# Even if strategy mentions 5m, use 1h for backtesting
data = ticker.history(period="730d", interval="1h")  # Use 1h, NOT 5m!

# Reset index and clean columns
data = data.reset_index()
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Rename columns to match backtesting.py requirements
data = data.rename(columns={
    'date': 'datetime',
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# Set datetime as index
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

# Run backtest
bt = Backtest(data, YourStrategyClassName, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)
```
⚠️ Replace TICKER_SYMBOL with the actual ticker from the strategy (SPY, BTC-USD, AAPL, etc.)

Always add plenty of Moon Dev themed debug prints with emojis to make debugging easier! 🌙 ✨ 🚀

FOR THE PYTHON BACKTESTING LIBRARY USE BACKTESTING.PY AND SEND BACK ONLY THE CODE, NO OTHER TEXT.
ONLY SEND BACK CODE, NO OTHER TEXT.
"""

DEBUG_PROMPT = """
You are Moon Dev's Debug AI 🌙
Fix technical issues in the backtest code WITHOUT changing the strategy logic.

🚨 CRITICAL: DATA LOADING MUST USE YFINANCE 🚨
If you see hardcoded CSV paths or missing data loading, use yfinance:
```python
import yfinance as yf
import pandas as pd

ticker = yf.Ticker("TICKER_SYMBOL")  # Use the correct ticker from strategy
data = ticker.history(period="2y", interval="1h")
data = data.reset_index()
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'date': 'datetime', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')
```

🚨 CRITICAL: POSITION OBJECT API 🚨
✅ AVAILABLE: self.position.size, .is_long, .is_short, .pl, .pl_pct
❌ DOES NOT EXIST: self.position.price, .sl, .tp, .modify(), .set_sl()

If code uses self.position.price, REPLACE with manual tracking:
```python
def init(self):
    self.entry_price = None

def next(self):
    if not self.position:
        self.buy(sl=stop, size=size)
        self.entry_price = self.data.Close[-1]  # Track manually
    elif self.position.is_long:
        # Use self.entry_price instead of self.position.price
        if self.data.Close[-1] >= self.entry_price + target:
            self.position.close()
```

If code tries to modify SL/TP after entry, REMOVE IT - not supported!

🚨 CRITICAL: TA-LIB DTYPE CONVERSION 🚨
TA-Lib requires float64 dtype. If you see errors like "input array type is not double":

❌ WRONG:
```python
self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
```

✅ CORRECT - Add .astype(float) to ALL data columns:
```python
self.rsi = self.I(talib.RSI, self.data.Close.astype(float), timeperiod=14)
self.vol_sma = self.I(talib.SMA, self.data.Volume.astype(float), timeperiod=20)
self.atr = self.I(talib.ATR, self.data.High.astype(float), self.data.Low.astype(float), self.data.Close.astype(float), timeperiod=14)
```

ALWAYS add .astype(float) when passing data to TA-Lib functions!

🚨 CRITICAL: CUSTOM INDICATOR FUNCTIONS MUST RETURN ARRAYS 🚨
If you see errors like "Indicators must return numpy.arrays of same length as data":

❌ WRONG:
```python
def custom_func(x):
    return x[-1]  # Returns scalar
```

✅ CORRECT:
```python
def custom_func(x):
    result = np.empty_like(x)
    for i in range(len(x)):
        result[i] = x[max(0, i-lookback)]
    return result
```

CRITICAL BACKTESTING REQUIREMENTS:
1. Position Sizing Rules:
   - Must be either a fraction (0 < size < 1) for percentage of equity
   - OR a positive whole number (round integer) for units
   - Example: size=0.5 (50% of equity) or size=100 (100 units)
   - NEVER use floating point numbers for unit-based sizing

2. Common Fixes Needed:
   - Round position sizes to whole numbers if using units
   - Convert to fraction if using percentage of equity
   - Ensure stop loss and take profit are price levels, not distances
   - REPLACE hardcoded CSV paths with yfinance data fetching

3. 🚨 CRITICAL: Stop Loss & Take Profit Ordering Errors 🚨
   If you see "ValueError: Short orders require: TP < LIMIT < SL" or similar:
   
   FOR LONG ORDERS (buying, expecting price to go UP):
   ```python
   entry_price = self.data.Close[-1]
   atr = self.atr[-1]
   
   # ✅ CORRECT: SL BELOW entry, TP ABOVE entry
   stop_loss_price = entry_price - (2.0 * atr)     # SUBTRACT for SL (below entry)
   take_profit_price = entry_price + (3.0 * atr)   # ADD for TP (above entry)
   
   # Validate: SL < Entry < TP
   if stop_loss_price < entry_price < take_profit_price:
       size = self.calculate_position_size(entry_price, stop_loss_price)
       self.buy(size=size, sl=stop_loss_price, tp=take_profit_price)
   else:
       print(f"🌙 MOON DEV DEBUG: Long order validation failed")
       return
   ```
   
   FOR SHORT ORDERS (selling, expecting price to go DOWN):
   ```python
   entry_price = self.data.Close[-1]
   atr = self.atr[-1]
   
   # ✅ CORRECT: TP BELOW entry, SL ABOVE entry
   take_profit_price = entry_price - (3.0 * atr)   # SUBTRACT for TP (below entry, profit when price drops)
   stop_loss_price = entry_price + (2.0 * atr)     # ADD for SL (above entry, stop when price rises)
   
   # Validate: TP < Entry < SL
   if take_profit_price < entry_price < stop_loss_price:
       size = self.calculate_position_size(entry_price, stop_loss_price)
       self.sell(size=size, sl=stop_loss_price, tp=take_profit_price)
   else:
       print(f"🌙 MOON DEV DEBUG: Short order validation failed")
       return
   ```
   
   ❌ COMMON MISTAKE TO AVOID:
   ```python
   # ❌ WRONG for SHORT orders - TP ends up ABOVE entry!
   take_profit_price = entry_price + (3.0 * atr)  # This puts TP above entry - WRONG!
   stop_loss_price = entry_price - (2.0 * atr)    # This puts SL below entry - WRONG!
   ```

Focus on:
1. Syntax errors (like incorrect string formatting)
2. Import statements and dependencies (ensure yfinance is imported)
3. Class and function definitions
4. Variable scoping and naming
5. Print statement formatting
6. Data loading (must use yfinance, not CSV files)

DO NOT change:
1. Strategy logic
2. Entry/exit conditions
3. Risk management rules
4. Parameter values (unless fixing technical issues)

Return the complete fixed code with Moon Dev themed debug prints! 🌙 ✨
ONLY SEND BACK CODE, NO OTHER TEXT.
"""

PACKAGE_PROMPT = """
You are Moon Dev's Package AI 🌙
Your job is to ensure the backtest code NEVER uses ANY backtesting.lib imports or functions.

❌ STRICTLY FORBIDDEN:
1. from backtesting.lib import *
2. import backtesting.lib
3. from backtesting.lib import crossover
4. ANY use of backtesting.lib

✅ REQUIRED REPLACEMENTS:
1. For crossover detection:
   Instead of: backtesting.lib.crossover(a, b)
   Use: (a[-2] < b[-2] and a[-1] > b[-1])  # for bullish crossover
        (a[-2] > b[-2] and a[-1] < b[-1])  # for bearish crossover

2. For indicators:
   - Use talib for all standard indicators (SMA, RSI, MACD, etc.)
   - Use pandas-ta for specialized indicators
   - ALWAYS wrap in self.I()
   - ⚠️ CRITICAL: Add .astype(float) to ALL data columns passed to TA-Lib!
   - Example: self.I(talib.SMA, self.data.Close.astype(float), timeperiod=20)

3. For signal generation:
   - Use numpy/pandas boolean conditions
   - Use rolling window comparisons with array indexing
   - Use mathematical comparisons (>, <, ==)

Example conversions:
❌ from backtesting.lib import crossover
❌ if crossover(fast_ma, slow_ma):
✅ if fast_ma[-2] < slow_ma[-2] and fast_ma[-1] > slow_ma[-1]:

❌ self.sma = self.I(backtesting.lib.SMA, self.data.Close, 20)
✅ self.sma = self.I(talib.SMA, self.data.Close, timeperiod=20)

IMPORTANT: Scan the ENTIRE code for any backtesting.lib usage and replace ALL instances!
Return the complete fixed code with proper Moon Dev themed debug prints! 🌙 ✨
ONLY SEND BACK CODE, NO OTHER TEXT.
"""

def get_model_id(model):
    """Get DR/DC identifier based on model"""
    return "DR" if model == "deepseek-reasoner" else "DC"

import os
import time
import re
from datetime import datetime
import requests
from io import BytesIO
import openai
from termcolor import cprint
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None
    cprint("⚠️ Anthropic SDK not installed. Claude models will be unavailable. (Moon Dev note)", "yellow")
from pathlib import Path
import threading
import itertools
import sys
import hashlib  # Added for idea hashing
from src.config import *  # Import config settings including AI_MODEL
from src.models import model_factory

# AI Configuration Constants (required for model calls)
AI_TEMPERATURE = 0.7
AI_MAX_TOKENS = 4000

# DeepSeek Configuration
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# Get today's date for organizing outputs
TODAY_DATE = datetime.now().strftime("%m_%d_%Y")

# Update data directory paths
PROJECT_ROOT = Path(__file__).parent.parent  # Points to src/
DATA_DIR = PROJECT_ROOT / "data/rbi"
TODAY_DIR = DATA_DIR / TODAY_DATE  # Today's date folder
RESEARCH_DIR = TODAY_DIR / "research"
BACKTEST_DIR = TODAY_DIR / "backtests"
PACKAGE_DIR = TODAY_DIR / "backtests_package"
FINAL_BACKTEST_DIR = TODAY_DIR / "backtests_final"
CHARTS_DIR = TODAY_DIR / "charts"  # New directory for HTML charts
PROCESSED_IDEAS_LOG = DATA_DIR / "processed_ideas.log"  # New file to track processed ideas

# Create main directories if they don't exist
for directory in [DATA_DIR, TODAY_DIR, RESEARCH_DIR, BACKTEST_DIR, PACKAGE_DIR, FINAL_BACKTEST_DIR, CHARTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

cprint(f"📂 Using RBI data directory: {DATA_DIR}")
cprint(f"📅 Today's date folder: {TODAY_DATE}")
cprint(f"📂 Research directory: {RESEARCH_DIR}")
cprint(f"📂 Backtest directory: {BACKTEST_DIR}")
cprint(f"📂 Package directory: {PACKAGE_DIR}")
cprint(f"📂 Final backtest directory: {FINAL_BACKTEST_DIR}")
cprint(f"📈 Charts directory: {CHARTS_DIR}")

def init_deepseek_client():
    """Initialize DeepSeek client with proper error handling"""
    try:
        deepseek_key = os.getenv("DEEPSEEK_KEY")
        if not deepseek_key:
            cprint("⚠️ DEEPSEEK_KEY not found - DeepSeek models will not be available", "yellow")
            return None
            
        print("🔑 Initializing DeepSeek client...")
        print("🌟 Moon Dev's RBI AI is connecting to DeepSeek...")
        
        client = openai.OpenAI(
            api_key=deepseek_key,
            base_url=DEEPSEEK_BASE_URL
        )
        
        print("✅ DeepSeek client initialized successfully!")
        print("🚀 Moon Dev's RBI AI ready to roll!")
        return client
    except Exception as e:
        print(f"❌ Error initializing DeepSeek client: {str(e)}")
        print("💡 Will fall back to Claude model from config.py")
        return None

def init_anthropic_client():
    """Initialize Anthropic client for Claude models"""
    try:
        if Anthropic is None:
            cprint("⚠️ Anthropic client unavailable (package not installed)", "yellow")
            return None
        anthropic_key = os.getenv("ANTHROPIC_KEY")
        if not anthropic_key:
            cprint("⚠️ ANTHROPIC_KEY not found in env. Skipping Claude init.", "yellow")
            return None
        return Anthropic(api_key=anthropic_key)
    except Exception as e:
        print(f"❌ Error initializing Anthropic client: {str(e)}")
        return None

def chat_with_model(system_prompt, user_content, model_config):
    """Chat with AI model using model factory"""
    try:
        # Initialize model using factory with specific config
        model = model_factory.get_model(model_config["type"], model_config["name"])
        if not model:
            raise ValueError(f"🚨 Could not initialize {model_config['type']} {model_config['name']} model!")

        cprint(f"🤖 Using {model_config['type']} model: {model_config['name']}", "cyan")
        cprint("🌟 Moon Dev's RBI AI is thinking...", "yellow")
        
        # Debug prints for prompt lengths
        cprint(f"📝 System prompt length: {len(system_prompt)} chars", "cyan")
        cprint(f"📝 User content length: {len(user_content)} chars", "cyan")
        # If model returned a wrapper, normalize early
        if hasattr(model, 'model_name') and model.model_type == 'openai':
            cprint(f"🧪 OpenAI model in use: {model.model_name}", "cyan")

        # For Ollama models, handle response differently
        if model_config["type"] == "ollama":
            response = model.generate_response(
                system_prompt=system_prompt,
                user_content=user_content,
                temperature=AI_TEMPERATURE
            )
            # Handle string response from Ollama
            if isinstance(response, str):
                return response
            # Handle object response
            if hasattr(response, 'content'):
                return response.content
            return str(response)
        else:
            # For other models, use standard parameters
            response = model.generate_response(
                system_prompt=system_prompt,
                user_content=user_content,
                temperature=AI_TEMPERATURE,
                max_tokens=AI_MAX_TOKENS
            )
            if response is None:
                cprint("❌ Model returned None response", "red")
                return None

            # Coerce response into text content
            content = None
            try:
                from src.models.base_model import ModelResponse
                if isinstance(response, ModelResponse):
                    content = response.content
            except Exception:
                pass

            if content is None:
                if isinstance(response, str):
                    content = response
                elif hasattr(response, 'content'):
                    content = response.content
                else:
                    cprint(f"❌ Response missing content attribute. Response type: {type(response)}", "red")
                    try:
                        cprint(f"Response attributes: {dir(response)}", "yellow")
                    except Exception:
                        pass
                    return None

            if not isinstance(content, str):
                content = str(content) if content is not None else ""
            if not content or len(content.strip()) == 0:
                cprint("❌ Model returned empty content", "red")
                return None

            return content

    except Exception as e:
        cprint(f"❌ Error in AI chat: {str(e)}", "red")
        cprint(f"🔍 Error type: {type(e).__name__}", "yellow")
        if hasattr(e, 'response'):
            cprint(f"🔍 Response error: {getattr(e, 'response', 'No response details')}", "yellow")
        if hasattr(e, '__dict__'):
            cprint("🔍 Error attributes:", "yellow")
            for attr in dir(e):
                if not attr.startswith('_'):
                    cprint(f"  ├─ {attr}: {getattr(e, attr)}", "yellow")
        return None

def get_youtube_transcript(video_id):
    """Get transcript from YouTube video"""
    try:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
        except ImportError:
            cprint("⚠️ youtube-transcript-api not installed. Skipping YouTube transcript fetch.", "yellow")
            return None
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_generated_transcript(['en'])
        
        # Get the full transcript text
        transcript_text = ' '.join([t['text'] for t in transcript.fetch()])
        
        # Print the transcript with nice formatting
        cprint("\n📝 YouTube Transcript:", "cyan")
        cprint("=" * 80, "yellow")
        print(transcript_text)
        cprint("=" * 80, "yellow")
        cprint(f"📊 Transcript length: {len(transcript_text)} characters", "cyan")
        
        return transcript_text
    except Exception as e:
        cprint(f"❌ Error fetching transcript: {e}", "red")
        return None

def get_pdf_text(url):
    """Extract text from PDF URL"""
    try:
        try:
            import PyPDF2
        except ImportError:
            cprint("⚠️ PyPDF2 not installed. Skipping PDF extraction.", "yellow")
            return None
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        reader = PyPDF2.PdfReader(BytesIO(response.content))
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'
        cprint("📚 Successfully extracted PDF text!", "green")
        return text
    except Exception as e:
        cprint(f"❌ Error reading PDF: {e}", "red")
        return None

def animate_progress(agent_name, stop_event):
    """Fun animation while AI is thinking"""
    spinners = ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘']
    messages = [
        "brewing coffee ☕️",
        "studying charts 📊",
        "checking signals 📡",
        "doing math 🔢",
        "reading docs 📚",
        "analyzing data 🔍",
        "making magic ✨",
        "trading secrets 🤫",
        "Moon Dev approved 🌙",
        "to the moon! 🚀"
    ]
    
    spinner = itertools.cycle(spinners)
    message = itertools.cycle(messages)
    
    while not stop_event.is_set():
        sys.stdout.write(f'\r{next(spinner)} {agent_name} is {next(message)}...')
        sys.stdout.flush()
        time.sleep(0.5)
    sys.stdout.write('\r' + ' ' * 50 + '\r')
    sys.stdout.flush()

def run_with_animation(func, agent_name, *args, **kwargs):
    """Run a function with a fun loading animation"""
    stop_animation = threading.Event()
    animation_thread = threading.Thread(target=animate_progress, args=(agent_name, stop_animation))
    
    try:
        animation_thread.start()
        result = func(*args, **kwargs)
        return result
    finally:
        stop_animation.set()
        animation_thread.join()

def clean_model_output(output, content_type="text"):
    """Clean model output by removing thinking tags and extracting code from markdown
    
    Args:
        output (str): Raw model output
        content_type (str): Type of content to extract ('text', 'code')
        
    Returns:
        str: Cleaned output
    """
    cleaned_output = output
    
    # Step 1: Remove thinking tags if present
    if "<think>" in output and "</think>" in output:
        cprint(f"🧠 Detected DeepSeek-R1 thinking tags, cleaning...", "yellow")
        
        # First try: Get everything after the last </think> tag
        clean_content = output.split("</think>")[-1].strip()
        
        # If that doesn't work, try removing all <think>...</think> blocks
        if not clean_content:
            import re
            clean_content = re.sub(r'<think>.*?</think>', '', output, flags=re.DOTALL).strip()
            
        if clean_content:
            cleaned_output = clean_content
            cprint("✅ Successfully removed thinking tags", "green")
    
    # Step 2: If code content, extract from markdown code blocks
    if content_type == "code" and "```" in cleaned_output:
        cprint("🔍 Extracting code from markdown blocks...", "yellow")
        
        try:
            import re
            # First look for python blocks
            code_blocks = re.findall(r'```python\n(.*?)\n```', cleaned_output, re.DOTALL)
            
            # If no python blocks, try any code blocks
            if not code_blocks:
                code_blocks = re.findall(r'```(?:python)?\n(.*?)\n```', cleaned_output, re.DOTALL)
                
            if code_blocks:
                # Join multiple code blocks with newlines between them
                cleaned_output = "\n\n".join(code_blocks)
                cprint("✅ Successfully extracted code from markdown", "green")
            else:
                cprint("⚠️ No code blocks found in markdown", "yellow")
        except Exception as e:
            cprint(f"❌ Error extracting code: {str(e)}", "red")
    
    return cleaned_output

def research_strategy(content):
    """Research AI: Analyzes and creates trading strategy"""
    cprint("\n🔍 Starting Research AI...", "cyan")
    cprint("🤖 Time to discover some alpha!", "yellow")
    
    output = run_with_animation(
        chat_with_model,
        "Research AI",
        RESEARCH_PROMPT, 
        content,
        RESEARCH_CONFIG  # Pass research-specific model config
    )
    
    if output:
        # Clean the output to remove thinking tags
        output = clean_model_output(output, "text")
        
        # Guard against non-string responses from model wrappers
        if not isinstance(output, str):
            try:
                from src.models.base_model import ModelResponse
                if isinstance(output, ModelResponse):
                    output = output.content or ""
                else:
                    output = str(output)
            except Exception:
                output = str(output)
        
        # Extract strategy name from output
        strategy_name = "UnknownStrategy"  # Default name
        if "STRATEGY_NAME:" in output:
            try:
                # Split by the STRATEGY_NAME: marker and get the text after it
                name_section = output.split("STRATEGY_NAME:")[1].strip()
                # Take the first line or up to the next section marker
                if "\n\n" in name_section:
                    strategy_name = name_section.split("\n\n")[0].strip()
                else:
                    strategy_name = name_section.split("\n")[0].strip()
                    
                # Clean up strategy name to be file-system friendly
                strategy_name = re.sub(r'[^\w\s-]', '', strategy_name)
                strategy_name = re.sub(r'[\s]+', '', strategy_name)
                
                cprint(f"✅ Successfully extracted strategy name: {strategy_name}", "green")
            except Exception as e:
                cprint(f"⚠️ Error extracting strategy name: {str(e)}", "yellow")
                cprint(f"🔄 Using default name: {strategy_name}", "yellow")
        else:
            cprint("⚠️ No STRATEGY_NAME found in output, using default", "yellow")
            
            # Try to generate a name based on key terms in the output
            import random
            adjectives = ["Adaptive", "Dynamic", "Quantum", "Neural", "Fractal", "Momentum", "Harmonic", "Volatility"]
            nouns = ["Breakout", "Oscillator", "Reversal", "Momentum", "Divergence", "Scalper", "Crossover", "Arbitrage"]
            strategy_name = f"{random.choice(adjectives)}{random.choice(nouns)}"
            cprint(f"🎲 Generated random strategy name: {strategy_name}", "yellow")
        
        # Save research output
        filepath = RESEARCH_DIR / f"{strategy_name}_strategy.txt"
        with open(filepath, 'w') as f:
            f.write(output)
        cprint(f"📝 Research AI found something spicy! Saved to {filepath} 🌶️", "green")
        cprint(f"🏷️ Generated strategy name: {strategy_name}", "yellow")
        return output, strategy_name
    return None, None

def create_backtest(strategy, strategy_name="UnknownStrategy"):
    """Backtest AI: Creates backtest implementation"""
    cprint("\n📊 Starting Backtest AI...", "cyan")
    cprint("💰 Let's turn that strategy into profits!", "yellow")
    
    output = run_with_animation(
        chat_with_model,
        "Backtest AI",
        BACKTEST_PROMPT,
        f"Create a backtest for this strategy:\n\n{strategy}",
        BACKTEST_CONFIG  # Pass backtest-specific model config
    )
    
    if output:
        # Clean the output and extract code from markdown
        output = clean_model_output(output, "code")
        if not isinstance(output, str):
            try:
                from src.models.base_model import ModelResponse
                if isinstance(output, ModelResponse):
                    output = output.content or ""
                else:
                    output = str(output)
            except Exception:
                output = str(output)
        
        filepath = BACKTEST_DIR / f"{strategy_name}_BT.py"
        with open(filepath, 'w') as f:
            f.write(output)
        cprint(f"🔥 Backtest AI cooked up some heat! Saved to {filepath} 🚀", "green")
        return output
    return None

def debug_backtest(backtest_code, strategy=None, strategy_name="UnknownStrategy"):
    """Debug AI: Fixes technical issues in backtest code"""
    cprint("\n🔧 Starting Debug AI...", "cyan")
    cprint("🔍 Time to squash some bugs!", "yellow")
    
    context = f"Here's the backtest code to debug:\n\n{backtest_code}"
    if strategy:
        context += f"\n\nOriginal strategy for reference:\n{strategy}"
    
    output = run_with_animation(
        chat_with_model,
        "Debug AI",
        DEBUG_PROMPT,
        context,
        DEBUG_CONFIG  # Pass debug-specific model config
    )
    
    if output:
        # Clean the output and extract code from markdown
        output = clean_model_output(output, "code")
        if not isinstance(output, str):
            try:
                from src.models.base_model import ModelResponse
                if isinstance(output, ModelResponse):
                    output = output.content or ""
                else:
                    output = str(output)
            except Exception:
                output = str(output)
            
        filepath = FINAL_BACKTEST_DIR / f"{strategy_name}_BTFinal.py"
        with open(filepath, 'w') as f:
            f.write(output)
        cprint(f"🔧 Debug AI fixed the code! Saved to {filepath} ✨", "green")
        return output
    return None

def package_check(backtest_code, strategy_name="UnknownStrategy"):
    """Package AI: Ensures correct indicator packages are used"""
    cprint("\n📦 Starting Package AI...", "cyan")
    cprint("🔍 Checking for proper indicator imports!", "yellow")
    
    output = run_with_animation(
        chat_with_model,
        "Package AI",
        PACKAGE_PROMPT,
        f"Check and fix indicator packages in this code:\n\n{backtest_code}",
        PACKAGE_CONFIG  # Pass package-specific model config
    )
    
    if output:
        # Clean the output and extract code from markdown
        output = clean_model_output(output, "code")
        if not isinstance(output, str):
            try:
                from src.models.base_model import ModelResponse
                if isinstance(output, ModelResponse):
                    output = output.content or ""
                else:
                    output = str(output)
            except Exception:
                output = str(output)
            
        filepath = PACKAGE_DIR / f"{strategy_name}_PKG.py"
        with open(filepath, 'w') as f:
            f.write(output)
        cprint(f"📦 Package AI optimized the imports! Saved to {filepath} ✨", "green")
        return output
    return None

def get_idea_content(idea_url: str) -> str:
    """Extract content from a trading idea URL or text"""
    print("\n📥 Extracting content from idea...")
    
    try:
        if "youtube.com" in idea_url or "youtu.be" in idea_url:
            # Extract video ID from URL
            if "v=" in idea_url:
                video_id = idea_url.split("v=")[1].split("&")[0]
            else:
                video_id = idea_url.split("/")[-1].split("?")[0]
            
            print("🎥 Detected YouTube video, fetching transcript...")
            transcript = get_youtube_transcript(video_id)
            if transcript:
                print("✅ Successfully extracted YouTube transcript!")
                return f"YouTube Strategy Content:\n\n{transcript}"
            else:
                raise ValueError("Failed to extract YouTube transcript")
                
        elif idea_url.endswith(".pdf"):
            print("📚 Detected PDF file, extracting text...")
            pdf_text = get_pdf_text(idea_url)
            if pdf_text:
                print("✅ Successfully extracted PDF content!")
                return f"PDF Strategy Content:\n\n{pdf_text}"
            else:
                raise ValueError("Failed to extract PDF text")
                
        else:
            print("📝 Using raw text input...")
            return f"Text Strategy Content:\n\n{idea_url}"
            
    except Exception as e:
        print(f"❌ Error extracting content: {str(e)}")
        raise

def get_idea_hash(idea: str) -> str:
    """Generate a unique hash for an idea to track processing status"""
    # Create a hash of the idea to use as a unique identifier
    return hashlib.md5(idea.encode('utf-8')).hexdigest()

def is_idea_processed(idea: str) -> bool:
    """Check if an idea has already been processed"""
    if not PROCESSED_IDEAS_LOG.exists():
        return False
        
    idea_hash = get_idea_hash(idea)
    
    with open(PROCESSED_IDEAS_LOG, 'r') as f:
        processed_hashes = [line.strip().split(',')[0] for line in f if line.strip()]
        
    return idea_hash in processed_hashes

def log_processed_idea(idea: str, strategy_name: str = "Unknown") -> None:
    """Log an idea as processed with timestamp and strategy name"""
    idea_hash = get_idea_hash(idea)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create the log file if it doesn't exist
    if not PROCESSED_IDEAS_LOG.exists():
        PROCESSED_IDEAS_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(PROCESSED_IDEAS_LOG, 'w') as f:
            f.write("# Moon Dev's RBI AI - Processed Ideas Log 🌙\n")
            f.write("# Format: hash,timestamp,strategy_name,idea_snippet\n")
    
    # Append the processed idea to the log
    with open(PROCESSED_IDEAS_LOG, 'a') as f:
        # Truncate idea if too long for the log
        idea_snippet = idea[:100] + ('...' if len(idea) > 100 else '')
        f.write(f"{idea_hash},{timestamp},{strategy_name},{idea_snippet}\n")
    
    cprint(f"📝 Idea logged as processed: {idea_hash}", "green")

def process_trading_idea(idea: str) -> None:
    """Process a single trading idea with optimized 2-phase pipeline (Research + Backtest only)"""
    print("\n🚀 Moon Dev's RBI AI Processing New Idea!")
    print("🌟 Let's find some alpha in the chaos!")
    print(f"📝 Processing idea: {idea[:100]}...")
    print(f"📅 Saving results to today's folder: {TODAY_DATE}")
    
    try:
        # Step 1: Extract content from the idea
        idea_content = get_idea_content(idea)
        if not idea_content:
            print("❌ Failed to extract content from idea!")
            return
            
        print(f"📄 Extracted content length: {len(idea_content)} characters")
        
        # Phase 1: Research with isolated content
        print("\n🧪 Phase 1: Research")
        strategy, strategy_name = research_strategy(idea_content)
        
        if not strategy:
            print("❌ Research phase failed!")
            return
            
        print(f"🏷️ Strategy Name: {strategy_name}")
        
        # Log the idea as processed once we have a strategy name
        log_processed_idea(idea, strategy_name)
        
        # Save research output
        research_file = RESEARCH_DIR / f"{strategy_name}_strategy.txt"
        with open(research_file, 'w') as f:
            f.write(strategy)
            
        # Phase 2: Backtest using only the research output
        print("\n📈 Phase 2: Backtest")
        backtest = create_backtest(strategy, strategy_name)
        
        if not backtest:
            print("❌ Backtest phase failed!")
            return
            
        # Save backtest output
        backtest_file = BACKTEST_DIR / f"{strategy_name}_BT.py"
        with open(backtest_file, 'w') as f:
            f.write(backtest)
        
        # ✅ OPTIMIZED: Skip Package Check and Debug phases
        # The BACKTEST_PROMPT now includes all necessary instructions for correct code generation
        # This reduces execution time from 5+ minutes to ~2 minutes
        
        # Save final backtest directly (no intermediate phases)
        final_file = FINAL_BACKTEST_DIR / f"{strategy_name}_BTFinal.py"
        with open(final_file, 'w') as f:
            f.write(backtest)
            
        print("\n🎉 Mission Accomplished!")
        print(f"🚀 Strategy '{strategy_name}' is ready to make it rain! 💸")
        print(f"✨ Final backtest saved at: {final_file}")
        
    except Exception as e:
        print(f"\n❌ Error processing idea: {str(e)}")
        raise

def main():
    """Main function to process ideas from file"""
    # We keep ideas.txt in the main RBI directory, not in the date folder
    ideas_file = DATA_DIR / "ideas.txt"
    
    if not ideas_file.exists():
        cprint("❌ ideas.txt not found! Creating template...", "red")
        ideas_file.parent.mkdir(parents=True, exist_ok=True)
        with open(ideas_file, 'w') as f:
            f.write("# Add your trading ideas here (one per line)\n")
            f.write("# Can be YouTube URLs, PDF links, or text descriptions\n")
        return
        
    with open(ideas_file, 'r') as f:
        ideas = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
    total_ideas = len(ideas)
    cprint(f"\n🎯 Found {total_ideas} trading ideas to process", "cyan")
    
    # Count how many ideas have already been processed
    already_processed = sum(1 for idea in ideas if is_idea_processed(idea))
    new_ideas = total_ideas - already_processed
    
    cprint(f"🔍 Status: {already_processed} already processed, {new_ideas} new ideas", "cyan")
    
    # Optional: limit number of ideas via env var (for quick debugging)
    max_ideas_env = os.getenv("RBI_MAX_IDEAS")
    max_ideas = int(max_ideas_env) if max_ideas_env and max_ideas_env.isdigit() else None
    processed_count = 0

    for i, idea in enumerate(ideas, 1):
        # Check if this idea has already been processed
        if is_idea_processed(idea):
            cprint(f"\n{'='*50}", "red")
            cprint(f"⏭️  SKIPPING idea {i}/{total_ideas} - ALREADY PROCESSED", "red", attrs=['reverse'])
            idea_snippet = idea[:100] + ('...' if len(idea) > 100 else '')
            cprint(f"📝 Idea: {idea_snippet}", "red")
            cprint(f"{'='*50}\n", "red")
            continue
            
        cprint(f"\n{'='*50}", "yellow")
        cprint(f"🌙 Processing idea {i}/{total_ideas}", "cyan")
        cprint(f"📝 Idea content: {idea[:100]}{'...' if len(idea) > 100 else ''}", "yellow")
        cprint(f"{'='*50}\n", "yellow")
        
        try:
            # Process each idea in complete isolation
            process_trading_idea(idea)
            
            # Clear separator between ideas
            cprint(f"\n{'='*50}", "green")
            cprint(f"✅ Completed idea {i}/{total_ideas}", "green")
            cprint(f"{'='*50}\n", "green")
            
            # Break between ideas
            if i < total_ideas:
                cprint("😴 Taking a break before next idea...", "yellow")
                time.sleep(5)
            processed_count += 1
            if max_ideas and processed_count >= max_ideas:
                cprint("🛑 Reached RBI_MAX_IDEAS limit, exiting after quick debug run.", "yellow")
                break
                
        except Exception as e:
            cprint(f"\n❌ Error processing idea {i}: {str(e)}", "red")
            cprint("🔄 Continuing with next idea...\n", "yellow")
            continue

if __name__ == "__main__":
    try:
        cprint(f"\n🌟 Moon Dev's RBI AI Starting Up!", "green")
        cprint(f"📅 Today's Date: {TODAY_DATE} - All outputs will be saved in this folder", "magenta")
        cprint(f"🧠 DeepSeek-R1 thinking tags will be automatically removed from outputs", "magenta")
        cprint(f"📋 Processed ideas log: {PROCESSED_IDEAS_LOG}", "magenta")
        cprint("\n🤖 Model Configurations:", "cyan")
        cprint(f"📚 Research: {RESEARCH_CONFIG['type']} - {RESEARCH_CONFIG['name']}", "cyan")
        cprint(f"📊 Backtest: {BACKTEST_CONFIG['type']} - {BACKTEST_CONFIG['name']}", "cyan")
        cprint(f"🔧 Debug: {DEBUG_CONFIG['type']} - {DEBUG_CONFIG['name']}", "cyan")
        cprint(f"📦 Package: {PACKAGE_CONFIG['type']} - {PACKAGE_CONFIG['name']}", "cyan")
        main()
    except KeyboardInterrupt:
        cprint("\n👋 Moon Dev's RBI AI shutting down gracefully...", "yellow")
    except Exception as e:
        cprint(f"\n❌ Fatal error: {str(e)}", "red")
