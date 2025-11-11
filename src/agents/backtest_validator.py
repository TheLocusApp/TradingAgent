"""
🌙 Moon Dev's Backtest Validator
Validates generated backtest code for common logical errors
"""

import re
import subprocess
import sys
from pathlib import Path
from termcolor import cprint


def validate_backtest_logic(code: str) -> dict:
    """
    Validate backtest code for common logical errors
    
    Returns:
        dict with 'valid' (bool), 'errors' (list), 'warnings' (list)
    """
    errors = []
    warnings = []
    
    # Check 1: Impossible rolling calculation comparisons
    if re.search(r'self\.data\.(Low|High)\[i\]\s*[<>]\s*self\.swing_(low|high)\[i\]', code):
        errors.append(
            "❌ CRITICAL: Comparing data point to its own rolling MIN/MAX calculation. "
            "This condition is mathematically impossible and will never trigger. "
            "Use neighbor comparison instead: if data.Low[i] <= data.Low[i-1] and data.Low[i] <= data.Low[i+1]"
        )
    
    # Check 2: Index out of bounds - accessing i+1 without bounds check
    if re.search(r'for\s+i\s+in\s+range\([^)]+current_index\)', code):
        if re.search(r'\[i\s*\+\s*1\]', code):
            # Check if there's a bounds check
            if not re.search(r'if.*i\s*<\s*len\(.*\)\s*-\s*1', code):
                errors.append(
                    "❌ CRITICAL: Accessing i+1 without bounds check. "
                    "Loop goes to current_index but accesses i+1, causing index error. "
                    "Fix: Stop loop at current_index - 1 or add bounds check."
                )
    
    # Check 3: Divergence detection with insufficient lookback
    if 'divergence' in code.lower():
        lookback_match = re.search(r'lookback\s*=\s*(?:min\()?\s*(\d+)', code)
        if lookback_match:
            lookback = int(lookback_match.group(1))
            if lookback < 20:
                warnings.append(
                    f"⚠️ WARNING: Divergence lookback period is only {lookback} bars. "
                    "This may be too short to find swing points. Consider 30-50 bars for daily data."
                )
    
    # Check 4: Position sizing issues
    if re.search(r'self\.buy\(size\s*=\s*[^)]*\)', code):
        if not re.search(r'round\(.*position_size.*\)', code):
            warnings.append(
                "⚠️ WARNING: Position size may not be rounded to whole units. "
                "Use round(position_size) if trading in units."
            )
    
    # Check 5: Missing yfinance data fetching
    if 'yfinance' not in code and 'yf.Ticker' not in code:
        errors.append(
            "❌ CRITICAL: Missing yfinance data fetching. "
            "Code must use yfinance to fetch data dynamically, not hardcoded CSV paths."
        )
    
    # Check 6: Hardcoded file paths
    if re.search(r'["\'](?:/Users/|C:\\|/home/)[^"\']+\.csv["\']', code):
        errors.append(
            "❌ CRITICAL: Hardcoded CSV file path detected. "
            "Use yfinance to fetch data dynamically instead."
        )
    
    # Check 7: Strategy has entry conditions
    if not re.search(r'self\.(buy|sell)\(', code):
        errors.append(
            "❌ CRITICAL: No buy() or sell() calls found in strategy. "
            "Strategy will never enter trades."
        )
    
    # Check 8: Column names are NOT converted to lowercase
    if re.search(r'data\.columns\s*=\s*data\.columns\.str\.lower\(\)', code):
        errors.append(
            "❌ CRITICAL: Converting columns to lowercase breaks backtesting.py! "
            "backtesting.py requires Title Case columns (Open, High, Low, Close, Volume). "
            "Remove: data.columns = data.columns.str.lower()"
        )
    
    # Check 9: No unnecessary column renaming
    if re.search(r'data\.rename\(columns=\{[\'"]open[\'"]:.*\}\)', code):
        warnings.append(
            "⚠️ WARNING: Unnecessary column renaming detected. "
            "yfinance already provides Title Case columns. Remove rename() call."
        )
    
    # Check 10: Position sizing double-division bug
    if re.search(r'position_size\s*=.*\/.*account_value.*\n.*position_size.*=.*position_size.*\/.*account', code, re.MULTILINE):
        errors.append(
            "❌ CRITICAL: Position sizing divides by account_value twice! "
            "This results in microscopic position sizes (0.0001). "
            "Use either fractional sizing (0.95) OR unit-based sizing, not both."
        )
    
    # Check 11: List pop() without empty check
    if re.search(r'\.pop\(', code):
        # Check if there's a length check before pop
        if not re.search(r'if\s+len\([^)]+\)\s*>\s*0.*\.pop\(', code, re.DOTALL):
            warnings.append(
                "⚠️ WARNING: Using .pop() without checking if list is empty. "
                "Add: if len(list_name) > 0: before calling .pop()"
            )
    
    # Check 12: CRITICAL - SL/TP ordering for LONG orders
    # Look for patterns like: self.buy(...sl=X, tp=Y) where SL might be >= entry
    if re.search(r'self\.buy\s*\([^)]*sl\s*=', code):
        # Check for common wrong patterns
        if re.search(r'stop_loss\s*=\s*.*?-\s*0\.', code) and re.search(r'entry.*\+', code):
            # This looks like it might have the right pattern, but we need to check more carefully
            # Look for patterns where stop_loss calculation might be wrong
            if re.search(r'stop_loss\s*=\s*nearest_support\s*-', code):
                warnings.append(
                    "⚠️ WARNING: Stop loss calculation uses 'nearest_support - value'. "
                    "For LONG orders, ensure: SL < Entry < TP. "
                    "If nearest_support is already below entry, subtracting more may cause SL > Entry!"
                )
    
    # Check 13: CRITICAL - SL/TP ordering for SHORT orders
    if re.search(r'self\.sell\s*\([^)]*sl\s*=', code):
        if re.search(r'stop_loss\s*=\s*nearest_resistance\s*\+', code):
            warnings.append(
                "⚠️ WARNING: Stop loss calculation uses 'nearest_resistance + value'. "
                "For SHORT orders, ensure: TP < Entry < SL. "
                "Verify that SL is above entry price!"
            )
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def test_backtest_execution(file_path: str, timeout: int = 30) -> dict:
    """
    Execute backtest and check if it produces trades
    
    Returns:
        dict with 'success' (bool), 'trades' (int), 'output' (str), 'error' (str)
    """
    try:
        result = subprocess.run(
            [sys.executable, file_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # Replace invalid characters instead of failing
            timeout=timeout,
            cwd=str(Path(file_path).parent)  # Run in backtest directory
        )
        
        output = result.stdout if result.stdout else ""
        error = result.stderr if result.stderr else ""
        
        # Clean output of problematic characters
        output = output.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        error = error.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        
        # Parse number of trades from output
        trades = 0
        trade_match = re.search(r'#\s*Trades\s+(\d+)', output)
        if trade_match:
            trades = int(trade_match.group(1))
        
        # Check win rate
        win_rate = None
        win_rate_match = re.search(r'Win Rate.*?(\d+\.?\d*)%?', output)
        if win_rate_match:
            win_rate = float(win_rate_match.group(1))
        
        return {
            'success': result.returncode == 0,
            'trades': trades,
            'win_rate': win_rate,
            'output': output,
            'error': error,
            'return_code': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'trades': 0,
            'win_rate': None,
            'output': '',
            'error': f'Execution timeout after {timeout} seconds',
            'return_code': -1
        }
    except Exception as e:
        return {
            'success': False,
            'trades': 0,
            'win_rate': None,
            'output': '',
            'error': str(e),
            'return_code': -1
        }


def validate_and_test(code: str, file_path: str = None) -> dict:
    """
    Full validation: logical checks + execution test
    
    Returns:
        dict with all validation results
    """
    cprint("\n🔍 Moon Dev's Backtest Validator", "cyan")
    cprint("=" * 60, "cyan")
    
    # Step 1: Logical validation
    cprint("\n📋 Step 1: Logical Validation", "yellow")
    logic_results = validate_backtest_logic(code)
    
    if logic_results['errors']:
        cprint(f"\n❌ Found {len(logic_results['errors'])} critical errors:", "red")
        for error in logic_results['errors']:
            cprint(f"  {error}", "red")
    else:
        cprint("✅ No critical logical errors found", "green")
    
    if logic_results['warnings']:
        cprint(f"\n⚠️  Found {len(logic_results['warnings'])} warnings:", "yellow")
        for warning in logic_results['warnings']:
            cprint(f"  {warning}", "yellow")
    
    # Step 2: Execution test (if file path provided)
    execution_results = None
    if file_path and Path(file_path).exists():
        cprint("\n📊 Step 2: Execution Test", "yellow")
        execution_results = test_backtest_execution(file_path)
        
        if execution_results['success']:
            cprint(f"✅ Backtest executed successfully", "green")
            cprint(f"📈 Trades: {execution_results['trades']}", "cyan")
            if execution_results['win_rate'] is not None:
                cprint(f"📊 Win Rate: {execution_results['win_rate']:.2f}%", "cyan")
            
            # Flag suspicious results
            if execution_results['trades'] == 0:
                cprint("⚠️  WARNING: Strategy produced ZERO trades!", "red")
                cprint("   This likely means entry conditions never trigger.", "red")
            elif execution_results['win_rate'] == 0:
                cprint("⚠️  WARNING: 0% win rate detected!", "yellow")
                cprint("   Strategy may have logical issues.", "yellow")
        else:
            cprint(f"❌ Backtest execution failed", "red")
            if execution_results['error']:
                cprint(f"   Error: {execution_results['error']}", "red")
    
    cprint("\n" + "=" * 60, "cyan")
    
    return {
        'logic': logic_results,
        'execution': execution_results,
        'overall_valid': logic_results['valid'] and (
            execution_results is None or 
            (execution_results['success'] and execution_results['trades'] > 0)
        )
    }


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python backtest_validator.py <backtest_file.py>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    
    results = validate_and_test(code, file_path)
    
    if results['overall_valid']:
        cprint("\n✅ VALIDATION PASSED", "green")
        sys.exit(0)
    else:
        cprint("\n❌ VALIDATION FAILED", "red")
        sys.exit(1)
