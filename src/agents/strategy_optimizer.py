"""
Strategy Optimizer Agent
Optimizes AGBot strategy across multiple timeframes for any ticker
Uses sequential testing with maximum historical data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from backtesting import Backtest
from src.strategies.AGBotGeneric import AGBotGeneric
import json
import warnings
warnings.filterwarnings('ignore')

class StrategyOptimizer:
    """Optimize AGBot strategy for any ticker and timeframe"""
    
    def __init__(self):
        self.results = []
        self.current_progress = 0
        self.total_tests = 0
    
    def fetch_data(self, symbol, timeframe, max_bars=5000):
        """
        Fetch maximum available data for a given timeframe
        
        Args:
            symbol: Ticker symbol (e.g., 'TSLA')
            timeframe: '1m', '5m', '15m', '1h', '4h', '1d', '1w'
            max_bars: Maximum bars to fetch (default: 5000 = ~1 year for 1H)
        
        Returns:
            DataFrame with OHLCV data
        """
        print(f"📊 Fetching {symbol} data ({timeframe})...")
        print(f"[DEBUG] max_bars={max_bars}, timeframe={timeframe}")
        
        # Adjust days_back based on timeframe (yfinance limits)
        if timeframe in ['1m', '2m', '5m', '15m', '30m']:
            # Intraday: yfinance limit is 60 days
            days_back = 59  # Use 59 to be safe
        else:
            # Hourly and daily: can use more data
            days_back = 365
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        print(f"[DEBUG] Fetching from {start_date.date()} to {end_date.date()} ({days_back} days)")
        print(f"[DEBUG] Timestamp: {start_date} → {end_date}")
        
        try:
            print(f"[DEBUG] Calling yfinance.download()...")
            df = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                interval=timeframe,
                progress=False
            )
            print(f"[DEBUG] yfinance.download() returned, rows={len(df)}")
            
            if df.empty:
                print(f"  ❌ No data fetched")
                return None
            
            # Handle MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Select required columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            df = df[required_cols]
            df = df.dropna()
            
            if df.empty:
                print(f"  ❌ No valid data after cleaning")
                return None
            
            print(f"  ✅ Fetched {len(df)} candles")
            print(f"     Date range: {df.index[0]} to {df.index[-1]}")
            return df
        
        except Exception as e:
            print(f"  ❌ Error fetching data: {str(e)}")
            return None
    
    def get_parameter_ranges(self, trade_type='swing', timeframe='1h'):
        """Get parameter ranges for optimization"""
        # MA length varies by trade type AND timeframe
        if trade_type.lower() == 'daytrade':
            ma_lengths = [20, 50, 100]
        else:  # swing trade
            if timeframe in ['1h']:
                # 1H has plenty of data (1,738 bars)
                ma_lengths = [100, 150, 200, 250]
            elif timeframe in ['4h']:
                # 4H has limited data (497 bars) - use shorter MAs
                ma_lengths = [50, 100, 150, 200]
            else:  # 1d and longer
                # Daily has very limited data - use shortest MAs
                ma_lengths = [50, 100, 150]
        
        return {
            'ma_length': ma_lengths,
            'key_value': [1.5, 2.0, 2.5, 3.0],
            'adaptive_atr_mult': [1.0, 1.5, 2.0],
            'tp1_rr_long': [0.5, 1.0, 1.5],
            'tp1_percent': [25, 35, 45]
        }
    
    def test_parameters(self, df, timeframe, **params):
        """Test a specific parameter combination"""
        try:
            class TestStrategy(AGBotGeneric):
                pass
            
            # Set parameters
            for key, value in params.items():
                setattr(TestStrategy, key, value)
            
            bt = Backtest(
                df,
                TestStrategy,
                cash=10000,
                commission=0.0003,
                exclusive_orders=True
            )
            
            stats = bt.run()
            
            # Calculate buy & hold return
            first_price = df['Close'].iloc[0]
            last_price = df['Close'].iloc[-1]
            buy_hold_return = ((last_price - first_price) / first_price) * 100
            
            # Calculate alpha (strategy excess return over buy & hold)
            strategy_return = stats['Return [%]']
            alpha = strategy_return - buy_hold_return
            
            # Calculate backtest duration in days
            first_date = df.index[0]
            last_date = df.index[-1]
            duration_days = (last_date - first_date).days
            
            # Log B&H calculation details
            print(f"[B&H DEBUG] Date range: {first_date} to {last_date} ({duration_days} days)")
            print(f"[B&H DEBUG] First price: ${first_price:.2f}, Last price: ${last_price:.2f}")
            print(f"[B&H DEBUG] B&H Return: {buy_hold_return:.2f}%")
            
            return {
                'timeframe': timeframe,
                'ma_length': params.get('ma_length'),
                'key_value': params.get('key_value'),
                'adaptive_atr_mult': params.get('adaptive_atr_mult'),
                'tp1_rr_long': params.get('tp1_rr_long'),
                'tp1_percent': params.get('tp1_percent'),
                'return': strategy_return,
                'sharpe': stats['Sharpe Ratio'],
                'max_dd': stats['Max. Drawdown [%]'],
                'win_rate': stats['Win Rate [%]'],
                'trades': int(stats['# Trades']),
                'avg_trade': stats['Avg. Trade [%]'],
                'profit_factor': stats['Profit Factor'],
                'equity_final': stats['Equity Final [$]'],
                'buy_hold_return': buy_hold_return,
                'alpha': alpha,
                'duration_days': duration_days
            }
        except Exception as e:
            print(f"[ERROR] test_parameters failed: {type(e).__name__}: {str(e)[:100]}")
            import traceback
            traceback.print_exc()
            return None
    
    def optimize_timeframe(self, symbol, timeframe, trade_type='swing', max_bars=2000, callback=None):
        """
        Optimize strategy for a specific timeframe
        
        Args:
            symbol: Ticker symbol
            timeframe: Timeframe to test
            trade_type: 'swing' or 'daytrade' (affects MA length ranges)
            max_bars: Maximum bars to fetch
            callback: Function to call with progress updates
        
        Returns:
            List of results sorted by Sharpe ratio
        """
        print(f"\n{'='*70}")
        print(f"🔍 Optimizing {symbol} on {timeframe} timeframe")
        print(f"{'='*70}")
        print(f"[DEBUG] Starting optimization with max_bars={max_bars}")
        
        # Auto-adjust max_bars for intraday timeframes (need more data for MA calculation)
        adjusted_max_bars = max_bars
        if timeframe in ['1m', '2m', '3m', '5m', '15m', '30m']:
            # Intraday: need 5x more bars for MA calculation
            adjusted_max_bars = max_bars * 5
            print(f"[DEBUG] Intraday timeframe detected. Adjusting max_bars: {max_bars} → {adjusted_max_bars}")
        
        # Fetch data
        print(f"[DEBUG] Fetching data for {symbol} {timeframe}...")
        df = self.fetch_data(symbol, timeframe, max_bars=adjusted_max_bars)
        print(f"[DEBUG] Data fetch complete. Rows: {len(df) if df is not None else 'None'}")
        
        # Check if we have ANY data
        if df is None or len(df) < 50:
            print(f"  ❌ Insufficient data for {timeframe}")
            print(f"     Have: {len(df) if df is not None else 0} bars")
            print(f"     Need: at least 50 bars for statistical significance")
            return []
        
        # Get parameter ranges and adjust MA lengths if needed
        param_ranges = self.get_parameter_ranges(trade_type, timeframe)
        max_ma_length = max(param_ranges['ma_length'])
        
        # If we don't have enough data for the longest MA, reduce MA lengths
        min_bars_needed = max_ma_length * 2
        if len(df) < min_bars_needed:
            print(f"  ⚠️  Limited data for {timeframe}: {len(df)} bars")
            print(f"     Reducing MA lengths to fit available data...")
            
            # Filter MA lengths to fit available data
            available_ma_lengths = [ma for ma in param_ranges['ma_length'] if ma * 2 <= len(df)]
            
            if not available_ma_lengths:
                # If no MA lengths fit, use the smallest one
                available_ma_lengths = [min(param_ranges['ma_length'])]
            
            param_ranges['ma_length'] = available_ma_lengths
            print(f"     Using MA lengths: {available_ma_lengths}")
        
        print(f"  ✅ Using {len(df)} bars for optimization")
        
        # Calculate total combinations
        total_combinations = 1
        for values in param_ranges.values():
            total_combinations *= len(values)
        
        print(f"\n⏳ Testing {total_combinations} parameter combinations...")
        
        results = []
        tested = 0
        
        # Test all combinations
        for ma_length in param_ranges['ma_length']:
            for key_value in param_ranges['key_value']:
                for adaptive_atr_mult in param_ranges['adaptive_atr_mult']:
                    for tp1_rr_long in param_ranges['tp1_rr_long']:
                        for tp1_percent in param_ranges['tp1_percent']:
                            result = self.test_parameters(
                                df, timeframe,
                                ma_length=ma_length,
                                key_value=key_value,
                                adaptive_atr_mult=adaptive_atr_mult,
                                tp1_rr_long=tp1_rr_long,
                                tp1_percent=tp1_percent
                            )
                            
                            if result is not None:
                                results.append(result)
                            
                            tested += 1
                            if tested % 100 == 0:
                                pct = 100 * tested / total_combinations
                                print(f"   Progress: {tested}/{total_combinations} ({pct:.1f}%)")
                                
                                if callback:
                                    callback({
                                        'status': 'testing',
                                        'timeframe': timeframe,
                                        'progress': pct,
                                        'tested': tested,
                                        'total': total_combinations
                                    })
        
        # Sort by Sharpe ratio (descending)
        if not results:
            print(f"\n⚠️  Completed {timeframe}: 0 valid combinations (all tests failed)")
            return []
        
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('sharpe', ascending=False)
        
        print(f"\n✅ Completed {timeframe}: {len(results)} valid combinations")
        
        return results_df.to_dict('records')
    
    def optimize_all_timeframes(self, symbol, trade_type='swing', max_bars=2000, callback=None):
        """
        Optimize strategy across all timeframes for a ticker
        
        Args:
            symbol: Ticker symbol
            trade_type: 'daytrade' (5m, 15m, 30m) or 'swing' (1h, 4h, 1d)
            max_bars: Maximum bars to fetch (default: 2000 = ~8 months)
            callback: Function to call with progress updates
        
        Returns:
            Dictionary with results for each timeframe
        """
        print(f"\n{'='*70}")
        print(f"🌙 AGBot Strategy Optimizer")
        print(f"{'='*70}")
        print(f"Symbol: {symbol}")
        print(f"Trade Type: {trade_type}")
        print(f"[DEBUG] optimize_all_timeframes called with max_bars={max_bars}")
        
        # Select timeframes based on trade type
        if trade_type.lower() == 'daytrade':
            timeframes = ['5m', '15m', '30m']  # yfinance supported (60 days max)
        else:  # swing
            timeframes = ['1h', '4h', '1d']
        
        all_results = {}
        
        for i, timeframe in enumerate(timeframes, 1):
            print(f"\n📍 Timeframe {i}/{len(timeframes)}: {timeframe}")
            
            results = self.optimize_timeframe(symbol, timeframe, trade_type, max_bars, callback)
            all_results[timeframe] = results
            
            if callback:
                callback({
                    'status': 'timeframe_complete',
                    'timeframe': timeframe,
                    'results_count': len(results)
                })
        
        return all_results
    
    def get_best_combinations(self, all_results, top_n=10):
        """
        Get top N parameter combinations across all timeframes
        
        Args:
            all_results: Dictionary with results for each timeframe
            top_n: Number of top results to return
        
        Returns:
            DataFrame with top combinations
        """
        all_combos = []
        
        for timeframe, results in all_results.items():
            for result in results:
                all_combos.append(result)
        
        df = pd.DataFrame(all_combos)
        df = df.sort_values('sharpe', ascending=False)
        
        return df.head(top_n)
    
    def clean_value(self, value):
        """Clean a single value for JSON serialization"""
        # Handle numpy types
        if isinstance(value, (np.floating, np.integer)):
            value = float(value)
        
        # Handle NaN and Inf
        if isinstance(value, float):
            if np.isnan(value) or np.isinf(value):
                return None  # Convert NaN/Inf to null in JSON
        
        return value
    
    def save_results(self, all_results, symbol, trade_type):
        """Save optimization results to file - CLEANS NaN/Inf at SOURCE"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"optimization_{symbol}_{trade_type}_{timestamp}.json"
        filepath = os.path.join(
            os.path.dirname(__file__),
            '..',
            'data',
            'optimizations',
            filename
        )
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Convert results to JSON-serializable format and CLEAN NaN/Inf
        json_results = {}
        for timeframe, results in all_results.items():
            json_results[timeframe] = [
                {k: self.clean_value(v) for k, v in result.items()}
                for result in results
            ]
        
        with open(filepath, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"\n✅ Results saved to {filepath}")
        return filepath


def clean_nan_recursive(obj):
    """Recursively clean NaN and Inf from nested structures"""
    if isinstance(obj, dict):
        return {k: clean_nan_recursive(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_recursive(item) for item in obj]
    elif isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    elif isinstance(obj, (np.floating, np.integer)):
        value = float(obj)
        if np.isnan(value) or np.isinf(value):
            return None
        return value
    return obj


def optimize_strategy(symbol, trade_type='swing', max_bars=2000, callback=None):
    """
    Main function to optimize strategy for a ticker
    
    Args:
        symbol: Ticker symbol (e.g., 'TSLA')
        trade_type: 'daytrade' or 'swing'
        max_bars: Maximum bars to fetch (default: 2000 = ~8 months)
        callback: Function to call with progress updates
    
    Returns:
        Dictionary with all results (NaN/Inf cleaned)
    """
    optimizer = StrategyOptimizer()
    all_results = optimizer.optimize_all_timeframes(symbol, trade_type, max_bars, callback)
    
    # Save results (already cleans NaN/Inf)
    optimizer.save_results(all_results, symbol, trade_type)
    
    # Get best combinations
    best = optimizer.get_best_combinations(all_results, top_n=10)
    
    # Clean NaN/Inf from in-memory results before returning
    result = {
        'all_results': all_results,
        'best_combinations': best.to_dict('records'),
        'symbol': symbol,
        'trade_type': trade_type,
        'timestamp': datetime.now().isoformat()
    }
    
    # CRITICAL: Clean NaN/Inf at SOURCE before returning
    return clean_nan_recursive(result)


if __name__ == "__main__":
    # Example usage
    result = optimize_strategy('TSLA', trade_type='swing')
    print("\n" + "="*70)
    print("🏆 Best Combinations")
    print("="*70)
    best_df = pd.DataFrame(result['best_combinations'])
    print(best_df[['timeframe', 'ma_length', 'key_value', 'sharpe', 'return', 'trades']])
