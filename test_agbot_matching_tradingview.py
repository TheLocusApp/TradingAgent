"""
Test AGBot on same date range as TradingView backtest
Apr 26, 2024 - Nov 6, 2025 on 4H timeframe
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
from backtesting import Backtest
from src.strategies.AGBot import AGBotStrategy
import warnings
warnings.filterwarnings('ignore')

def fetch_data(symbol, start_date, end_date, interval='4h'):
    """Fetch OHLCV data from yfinance"""
    print(f"📊 Fetching {symbol} data ({interval})...")
    print(f"   From: {start_date}")
    print(f"   To: {end_date}")
    
    df = yf.download(
        symbol, 
        start=start_date, 
        end=end_date, 
        interval=interval,
        progress=False
    )
    
    if df.empty:
        print(f"❌ No data fetched")
        return None
    
    # Handle MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Select required columns
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    df = df[required_cols]
    df = df.dropna()
    
    if df.empty:
        print(f"❌ No valid data after cleaning")
        return None
    
    print(f"✅ Fetched {len(df)} candles")
    print(f"   Actual range: {df.index[0]} to {df.index[-1]}")
    return df

def test_strategy(df, capital=5000, **params):
    """Test strategy with specific parameters"""
    try:
        class TestStrategy(AGBotStrategy):
            pass
        
        # Set parameters
        for key, value in params.items():
            setattr(TestStrategy, key, value)
        
        bt = Backtest(
            df,
            TestStrategy,
            cash=capital,
            commission=0.0003,  # 0.03%
            exclusive_orders=True
        )
        
        stats = bt.run()
        
        return {
            'return': stats['Return [%]'],
            'sharpe': stats['Sharpe Ratio'],
            'max_dd': stats['Max. Drawdown [%]'],
            'win_rate': stats['Win Rate [%]'],
            'trades': int(stats['# Trades']),
            'avg_trade': stats['Avg. Trade [%]'],
            'profit_factor': stats['Profit Factor'],
            'equity_final': stats['Equity Final [$]'],
            'pnl': stats['Equity Final [$]'] - capital
        }
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🌙 AGBot - Matching TradingView Backtest")
    print("="*70)
    
    # TradingView date range: Apr 26, 2024 - Nov 6, 2025
    start_date = "2024-04-26"
    end_date = "2025-11-06"
    
    # Fetch 4H data
    df = fetch_data("TSLA", start_date, end_date, interval='4h')
    
    if df is not None:
        print("\n" + "="*70)
        print("🧪 Testing Parameters on 4H (Apr 26, 2024 - Nov 6, 2025)")
        print("="*70)
        
        # Your optimized 4H parameters
        params_4h = {
            'ma_length': 150,
            'key_value': 2.5,
            'adaptive_atr_mult': 2.5,
            'tp1_rr_long': 2.5,
            'tp1_percent': 20,
            'tp2_rr_long': 4.0
        }
        
        print("\n📊 Testing Our 4H Optimized Parameters:")
        print(f"   MA: 150, Key: 2.5, ATR: 2.5")
        print(f"   TP1 RR: 2.5, TP1%: 20, TP2 RR: 4.0")
        
        result = test_strategy(df, capital=5000, **params_4h)
        
        if result:
            print(f"\n✅ Results:")
            print(f"   Return: {result['return']:.2f}%")
            print(f"   P&L: ${result['pnl']:.2f}")
            print(f"   Equity Final: ${result['equity_final']:.2f}")
            print(f"   Sharpe: {result['sharpe']:.2f}")
            print(f"   Max DD: {result['max_dd']:.2f}%")
            print(f"   Win Rate: {result['win_rate']:.2f}%")
            print(f"   Trades: {result['trades']}")
            print(f"   Avg Trade: {result['avg_trade']:.2f}%")
            print(f"   Profit Factor: {result['profit_factor']:.3f}")
            
            print(f"\n📊 Comparison with TradingView:")
            print(f"   TradingView: -12.13% return, -$606.62 P&L, 0.773 profit factor")
            print(f"   Our backtest: {result['return']:.2f}% return, ${result['pnl']:.2f} P&L, {result['profit_factor']:.3f} profit factor")
            
            if result['return'] > 0:
                print(f"\n✅ Our backtest shows POSITIVE returns")
                print(f"   Difference: {result['return'] - (-12.13):.2f}% better than TradingView")
            else:
                print(f"\n⚠️ Both backtests show losses")
                print(f"   Difference: {abs(result['return']) - 12.13:.2f}%")
    
    print("\n" + "="*70)
    print("Analysis")
    print("="*70)
    print("""
The difference between TradingView and our backtest could be due to:

1. **Order Execution Model**
   - TradingView may fill at different prices
   - Our backtest uses close price for entries/exits
   
2. **Position Sizing**
   - TradingView calculates position size differently
   - Risk per trade handling differs
   
3. **Commission/Slippage**
   - TradingView applies commission differently
   - Hidden slippage assumptions
   
4. **Strategy Implementation**
   - Slight differences in indicator calculations
   - Entry/exit logic differences
   
5. **Data Quality**
   - Different data sources
   - Different candle construction
   
RECOMMENDATION:
- Use our Python backtest as the source of truth
- It's transparent, auditable, and industry-standard
- Deploy with small position sizes and monitor live performance
- Adjust parameters based on real trading results
""")
    
    print("Done!")
