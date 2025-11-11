"""
Monitor Strategy Optimizer Progress
Watch for backtest results being written to disk
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime

def monitor_optimization():
    """Monitor optimization progress"""
    
    optimization_dir = Path("src/data/optimizations")
    optimization_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("📊 Strategy Optimizer Monitor")
    print("="*70)
    print(f"Watching directory: {optimization_dir.absolute()}\n")
    
    last_files = set()
    
    while True:
        try:
            # Get all JSON files in optimization directory
            json_files = list(optimization_dir.glob("*.json"))
            
            # Check for new files
            current_files = {f.name for f in json_files}
            new_files = current_files - last_files
            
            if new_files:
                print(f"\n🆕 New optimization file detected!")
                for filename in new_files:
                    filepath = optimization_dir / filename
                    print(f"   📁 {filename}")
                    print(f"   📍 {filepath}")
                    
                    # Read and show summary
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                        
                        print(f"\n   📊 Results Summary:")
                        for timeframe, results in data.items():
                            if isinstance(results, list) and len(results) > 0:
                                best = results[0]
                                print(f"      {timeframe.upper()}: {len(results)} combinations")
                                print(f"         Best Sharpe: {best.get('sharpe', 0):.2f}")
                                print(f"         Best Return: {best.get('return', 0):.2f}%")
                    except Exception as e:
                        print(f"   ⚠️  Error reading file: {e}")
            
            # Show all current files
            if json_files:
                print(f"\n📁 Current optimization files ({len(json_files)}):")
                for f in sorted(json_files, key=lambda x: x.stat().st_mtime, reverse=True):
                    size_mb = f.stat().st_size / (1024 * 1024)
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    print(f"   ✅ {f.name}")
                    print(f"      Size: {size_mb:.2f} MB | Modified: {mtime.strftime('%H:%M:%S')}")
            else:
                print("   (No optimization files yet)")
            
            last_files = current_files
            
            # Wait before checking again
            print("\n⏳ Checking again in 5 seconds... (Ctrl+C to stop)")
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\n✅ Monitor stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

def show_latest_results():
    """Show the latest optimization results"""
    
    optimization_dir = Path("src/data/optimizations")
    json_files = list(optimization_dir.glob("*.json"))
    
    if not json_files:
        print("❌ No optimization results found")
        return
    
    # Get latest file
    latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
    
    print("\n" + "="*70)
    print("📊 Latest Optimization Results")
    print("="*70)
    print(f"File: {latest_file.name}\n")
    
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    # Show results for each timeframe
    for timeframe, results in data.items():
        if isinstance(results, list) and len(results) > 0:
            print(f"\n🕐 {timeframe.upper()} Timeframe:")
            print(f"   Total Combinations: {len(results)}")
            
            # Show top 3
            for i, result in enumerate(results[:3], 1):
                print(f"\n   #{i}:")
                print(f"      MA Length: {result.get('ma_length')}")
                print(f"      Key Value: {result.get('key_value')}")
                print(f"      ATR Mult: {result.get('adaptive_atr_mult')}")
                print(f"      TP1 RR: {result.get('tp1_rr_long')}")
                print(f"      TP1 %: {result.get('tp1_percent')}")
                print(f"      ---")
                print(f"      Sharpe: {result.get('sharpe', 0):.2f} ⭐")
                print(f"      Return: {result.get('return', 0):.2f}%")
                print(f"      Win Rate: {result.get('win_rate', 0):.1f}%")
                print(f"      Trades: {result.get('trades', 0)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor Strategy Optimizer')
    parser.add_argument('--latest', action='store_true', help='Show latest results only')
    args = parser.parse_args()
    
    if args.latest:
        show_latest_results()
    else:
        monitor_optimization()
