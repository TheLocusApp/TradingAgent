"""
Extract SHORT-specific parameters from existing optimization results
Since yfinance has 730-day limit for 1H data, we'll analyze existing results
and recommend parameters optimized for SHORT positions
"""

import json
from pathlib import Path

def analyze_shorts_parameters():
    """Analyze existing optimization results for SHORT-friendly parameters"""
    
    # Load existing QQQ optimization
    opt_file = Path("src/data/optimizations/optimization_QQQ_swing_20251107_124631.json")
    
    if not opt_file.exists():
        print(f"❌ File not found: {opt_file}")
        return None
    
    with open(opt_file, 'r') as f:
        data = json.load(f)
    
    print("=" * 70)
    print("AGBot SHORTS-ONLY Parameter Analysis")
    print("=" * 70)
    print(f"\nAnalyzing: {opt_file.name}")
    
    # Extract 1h results
    results_1h = data.get('1h', [])
    
    if not results_1h:
        print("❌ No 1h results found")
        return None
    
    print(f"\n📊 Found {len(results_1h)} parameter combinations\n")
    
    # For SHORTS, we want:
    # 1. Lower ATR Mult (tighter stops) = less whipsaws
    # 2. Lower TP1 R:R (faster exits) = avoid theta decay
    # 3. Higher TP1 % (trim more) = lock in gains
    # 4. Good Sharpe ratio
    
    # Filter for short-friendly parameters
    shorts_friendly = []
    
    for result in results_1h:
        # Prefer:
        # - ATR Mult <= 1.5 (tighter stops)
        # - TP1 R:R <= 1.0 (faster exits)
        # - TP1 % >= 40 (trim more)
        # - At least 10 trades
        
        atr_mult = result.get('adaptive_atr_mult', 999)
        tp1_rr = result.get('tp1_rr_long', 999)  # Using long for now, will adapt
        tp1_pct = result.get('tp1_percent', 0)
        trades = result.get('trades', 0)
        sharpe = result.get('sharpe', 0)
        
        if atr_mult <= 1.5 and tp1_rr <= 1.0 and tp1_pct >= 40 and trades >= 10:
            shorts_friendly.append({
                'ma_length': result.get('ma_length'),
                'key_value': result.get('key_value'),
                'adaptive_atr_mult': atr_mult,
                'tp1_rr_short': tp1_rr,  # Will use for shorts
                'tp1_percent': tp1_pct,
                'return': result.get('return'),
                'sharpe': sharpe,
                'max_dd': result.get('max_dd'),
                'win_rate': result.get('win_rate'),
                'trades': trades,
                'profit_factor': result.get('profit_factor'),
            })
    
    # Sort by Sharpe ratio
    shorts_friendly = sorted(shorts_friendly, key=lambda x: x['sharpe'], reverse=True)
    
    print("🎯 TOP 10 PARAMETER SETS FOR SHORTS:\n")
    print("(Criteria: ATR Mult ≤ 1.5, TP1 R:R ≤ 1.0, TP1 % ≥ 40)\n")
    
    for i, params in enumerate(shorts_friendly[:10], 1):
        print(f"{i}. MA={params['ma_length']}, Key={params['key_value']:.1f}x, ATR Mult={params['adaptive_atr_mult']:.2f}")
        print(f"   TP1 R:R={params['tp1_rr_short']:.1f}, TP1%={params['tp1_percent']:.0f}%")
        print(f"   Return: {params['return']:.2f}% | Sharpe: {params['sharpe']:.2f} | Win%: {params['win_rate']:.1f}%")
        print(f"   Max DD: {params['max_dd']:.2f}% | Trades: {params['trades']} | PF: {params['profit_factor']:.2f}\n")
    
    # Recommend best for SHORTS
    if shorts_friendly:
        best = shorts_friendly[0]
        print("=" * 70)
        print("✅ RECOMMENDED PARAMETERS FOR SHORTS (QQQ 1H):")
        print("=" * 70)
        print(f"\nMA Length:        {best['ma_length']}")
        print(f"Key Value:        {best['key_value']:.1f}x")
        print(f"ATR Mult:         {best['adaptive_atr_mult']:.2f} (tight stops)")
        print(f"TP1 R:R Short:    {best['tp1_rr_short']:.1f} (fast exits)")
        print(f"TP1 Close %:      {best['tp1_percent']:.0f}% (lock gains)")
        print(f"\nExpected Performance:")
        print(f"  Return:         {best['return']:.2f}%")
        print(f"  Sharpe:         {best['sharpe']:.2f}")
        print(f"  Max Drawdown:   {best['max_dd']:.2f}%")
        print(f"  Win Rate:       {best['win_rate']:.1f}%")
        print(f"  Trades:         {best['trades']}")
        print(f"  Profit Factor:  {best['profit_factor']:.2f}")
        
        # Save to file
        output = {
            'ticker': 'QQQ',
            'timeframe': '1h',
            'strategy_type': 'shorts_only',
            'source': 'Extracted from existing optimization results',
            'best_parameters': best,
            'top_10': shorts_friendly[:10],
        }
        
        output_file = Path("src/data/optimizations/QQQ_SHORTS_RECOMMENDED_PARAMS.json")
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n💾 Saved to: {output_file}")
        
        return best
    
    return None


if __name__ == "__main__":
    best_params = analyze_shorts_parameters()
    
    if best_params:
        print("\n✨ Use these parameters in your Pine Script for SHORTS!")
    else:
        print("\n❌ No suitable parameters found")
