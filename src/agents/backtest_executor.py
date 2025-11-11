"""
Simple Backtest Executor for Strategy Lab
Executes generated backtest code and returns real results
"""

import subprocess
import json
import re
from pathlib import Path
from datetime import datetime


def run_single_backtest(strategy_name: str, backtest_code: str = None) -> dict:
    """
    Execute a single backtest and return results
    
    Args:
        strategy_name: Name of the strategy
        backtest_code: Optional backtest code to execute. If None, looks for existing file.
    
    Returns:
        dict with status, results, or error
    """
    try:
        # Import validator
        from src.agents.backtest_validator import validate_backtest_logic
        # Find the backtest file - check ALL RBI folders (v3, v2, v1)
        today = datetime.now().strftime("%m_%d_%Y")
        
        # Define all possible RBI directories in priority order
        base_data_dir = Path(__file__).parent.parent / "data"
        rbi_dirs = [
            base_data_dir / "rbi_v3" / today / "backtests_final",
            base_data_dir / "rbi_v2" / today / "backtests_final",
            base_data_dir / "rbi" / today / "backtests_final",
        ]
        
        # Find the first directory that exists and contains the strategy file
        backtest_dir = None
        backtest_file = None
        
        for dir_path in rbi_dirs:
            if dir_path.exists():
                # Try exact match with _BTFinal.py suffix
                test_file = dir_path / f"{strategy_name}_BTFinal.py"
                if test_file.exists():
                    backtest_dir = dir_path
                    backtest_file = test_file
                    break
                
                # Try glob pattern for _BTFinal*.py (includes _WORKING variants)
                matching_files = list(dir_path.glob(f"{strategy_name}_BTFinal*.py"))
                if matching_files:
                    backtest_dir = dir_path
                    backtest_file = matching_files[0]  # Use first match
                    break
        
        # If not found in today's folders, search all date folders
        if not backtest_file:
            for base_dir in [base_data_dir / "rbi_v3", base_data_dir / "rbi_v2", base_data_dir / "rbi"]:
                if base_dir.exists():
                    for date_folder in base_dir.iterdir():
                        if date_folder.is_dir():
                            final_dir = date_folder / "backtests_final"
                            if final_dir.exists():
                                matching_files = list(final_dir.glob(f"{strategy_name}_BTFinal*.py"))
                                if matching_files:
                                    backtest_dir = final_dir
                                    backtest_file = matching_files[0]
                                    break
                    if backtest_file:
                        break
        
        # Check if we found the file
        if not backtest_file:
            return {
                'status': 'error',
                'error': f'Backtest file not found for strategy: {strategy_name}'
            }
        
        print(f"📊 Executing backtest: {backtest_file}")
        
        # Read the backtest file for validation
        with open(backtest_file, 'r', encoding='utf-8') as f:
            backtest_file_code = f.read()
        
        # Validate the code before running
        print("\n🔍 Pre-backtest validation...")
        validation_results = validate_backtest_logic(backtest_file_code)
        
        if validation_results['errors']:
            print("\n❌ VALIDATION FAILED - Critical errors found:")
            for error in validation_results['errors']:
                print(f"  {error}")
            return {
                'status': 'error',
                'error': 'Code validation failed - critical errors detected',
                'validation_errors': validation_results['errors']
            }
        
        if validation_results['warnings']:
            print("\n⚠️  VALIDATION WARNINGS:")
            for warning in validation_results['warnings']:
                print(f"  {warning}")
        
        print("✅ Code validation passed\n")
        
        # Execute the backtest with proper encoding handling for Windows
        try:
            result = subprocess.run(
                ['python', str(backtest_file)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace invalid characters instead of failing
                timeout=60,  # 60 second timeout
                cwd=str(backtest_file.parent)  # Run in backtest directory
            )
        except UnicodeDecodeError:
            # Fallback: try with system encoding
            print("⚠️ UTF-8 decode failed, trying system encoding...")
            result = subprocess.run(
                ['python', str(backtest_file)],
                capture_output=True,
                text=True,
                errors='replace',
                timeout=60,
                cwd=str(backtest_file.parent)
            )
        
        # Parse output safely
        stdout = result.stdout if result.stdout else ""
        stderr = result.stderr if result.stderr else ""
        
        # Clean output of any problematic characters
        stdout = stdout.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        stderr = stderr.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        
        if result.returncode != 0:
            print(f"\n❌ Backtest execution failed!")
            print(f"📊 Return code: {result.returncode}")
            print(f"📝 STDOUT:\n{stdout}")
            print(f"❌ STDERR:\n{stderr}")
            return {
                'status': 'error',
                'error': f'Backtest failed with code {result.returncode}',
                'stderr': stderr,
                'stdout': stdout
            }
        
        # Extract metrics from output
        metrics = parse_backtest_output(stdout)
        
        if not metrics:
            return {
                'status': 'error',
                'error': 'Could not parse backtest results',
                'stdout': stdout
            }
        
        return {
            'status': 'success',
            'results': metrics,
            'stdout': stdout
        }
        
    except subprocess.TimeoutExpired:
        return {
            'status': 'error',
            'error': 'Backtest execution timed out (>60s)'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': f'Execution error: {str(e)}'
        }


def parse_backtest_output(output: str) -> dict:
    """
    Parse backtest output to extract metrics
    Looks for backtesting.py stats format and common patterns
    """
    metrics = {}
    
    try:
        # Backtesting.py specific patterns (from stats output)
        patterns = {
            'total_return': r'(?:Return \[%\]|Total Return)[:\s]+([+-]?\d+\.?\d*)%?',
            'sharpe_ratio': r'(?:Sharpe Ratio|Sharpe)[:\s]+([+-]?\d+\.?\d*)',
            'max_drawdown': r'(?:Max\. Drawdown \[%\]|Max Drawdown|Maximum Drawdown)[:\s]+([+-]?\d+\.?\d*)%?',
            'win_rate': r'(?:Win Rate \[%\]|Win Rate|Win %)[:\s]+([+-]?\d+\.?\d*)%?',
            'total_trades': r'(?:\# Trades|Total Trades|Trades)[:\s]+(\d+)',
            'buy_hold_return': r'(?:Buy & Hold Return \[%\]|Buy.?Hold|B&H)[:\s]+([+-]?\d+\.?\d*)%?',
            'equity_final': r'(?:Equity Final|Final Equity)[:\s]+\$?([\d,]+\.?\d*)',
            'return_annual': r'(?:Return \(Ann\.\)|Annual Return)[:\s]+([+-]?\d+\.?\d*)%?'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                metrics[key] = value
        
        # Calculate risk grade if we have sharpe and win rate
        if 'sharpe_ratio' in metrics and 'win_rate' in metrics:
            sharpe = metrics['sharpe_ratio']
            win_rate = metrics['win_rate']
            
            if sharpe > 1.5 and win_rate > 65:
                metrics['risk_grade'] = 'A'
            elif sharpe > 1.0 and win_rate > 55:
                metrics['risk_grade'] = 'B'
            elif sharpe > 0.5 and win_rate > 45:
                metrics['risk_grade'] = 'C'
            elif sharpe > 0 and win_rate > 35:
                metrics['risk_grade'] = 'D'
            else:
                metrics['risk_grade'] = 'F'
        
        # Add defaults for missing metrics
        if 'total_return' not in metrics:
            metrics['total_return'] = 0.0
        if 'sharpe_ratio' not in metrics:
            metrics['sharpe_ratio'] = 0.0
        if 'max_drawdown' not in metrics:
            metrics['max_drawdown'] = 0.0
        if 'win_rate' not in metrics:
            metrics['win_rate'] = 50.0
        if 'total_trades' not in metrics:
            metrics['total_trades'] = 0
        if 'risk_grade' not in metrics:
            metrics['risk_grade'] = 'C'
        
        return metrics
        
    except Exception as e:
        print(f"⚠️ Error parsing backtest output: {e}")
        return None
