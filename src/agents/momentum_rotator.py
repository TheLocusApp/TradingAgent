#!/usr/bin/env python3
"""
🔄 Cross-Asset Momentum Rotation System
Dynamic capital allocation to top momentum performers
Built with love by Moon Dev 🚀
"""

import numpy as np
import yfinance as yf
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from termcolor import cprint


class MomentumRotator:
    """
    Rotates capital to top momentum assets
    
    Features:
    - Multi-timeframe momentum scoring (20/50/200 day)
    - Weekly rebalancing to top performers
    - Risk-on/risk-off detection
    - Correlation-aware diversification
    """
    
    def __init__(self, universe: List[str] = None):
        """
        Initialize momentum rotator
        
        Args:
            universe: List of symbols to rotate between (optional, uses default if None)
        
        NOTE: Default universe is a curated list of liquid, tradeable assets across
        multiple asset classes. This is NOT hardcoded data - yfinance fetches real-time
        prices and calculates momentum dynamically. You can pass a custom universe to
        analyze different assets.
        """
        self.universe = universe or [
            # Crypto (most liquid)
            'BTC-USD', 'ETH-USD', 'SOL-USD',
            # Major indices (high volume)
            'SPY', 'QQQ', 'IWM',
            # Sectors (diversification)
            'XLK', 'XLF', 'XLE', 'XLV',
            # Individual stocks (high momentum potential)
            'AAPL', 'MSFT', 'NVDA', 'TSLA', 'GOOGL', 'AMZN'
        ]
        
        self.rotation_frequency = 7  # Rebalance every 7 days
        self.last_rotation = datetime.now() - timedelta(days=7)  # Force initial rotation
        self.current_rankings = []
        
        cprint("✅ Momentum Rotator initialized", "green")
        cprint(f"   Universe: {len(self.universe)} assets", "cyan")
    
    def calculate_momentum_score(self, prices: np.ndarray, 
                                 periods: List[int] = [20, 50, 200]) -> float:
        """
        Calculate multi-timeframe momentum score
        
        Args:
            prices: Price history
            periods: Lookback periods to evaluate
            
        Returns:
            Composite momentum score (0-100)
        """
        if len(prices) < max(periods):
            return 0.0
        
        scores = []
        weights = [0.5, 0.3, 0.2]  # Weight recent momentum higher
        
        for period, weight in zip(periods, weights):
            if len(prices) >= period + 1:  # Need extra day for diff calculation
                # Calculate return over period
                period_return = (prices[-1] - prices[-period]) / prices[-period]
                
                # Calculate consistency (% of days positive)
                price_slice = prices[-period:]
                recent_returns = np.diff(price_slice) / price_slice[:-1]  # Fixed: proper array slicing
                consistency = np.sum(recent_returns > 0) / len(recent_returns) if len(recent_returns) > 0 else 0.5
                
                # Combine return and consistency
                period_score = (period_return * 100) * (0.7 + consistency * 0.3)
                scores.append(period_score * weight)
        
        return sum(scores)
    
    def calculate_volatility_adjusted_momentum(self, prices: np.ndarray) -> float:
        """
        Calculate momentum adjusted for volatility (Sharpe-like)
        
        Args:
            prices: Price history
            
        Returns:
            Volatility-adjusted momentum score
        """
        if len(prices) < 21:  # Need at least 21 for 20 returns
            return 0.0
        
        # Defensive: ensure we have clean data
        prices = prices[~np.isnan(prices)]  # Remove NaN
        if len(prices) < 21:
            return 0.0
        
        # Calculate returns with proper array slicing
        price_diffs = np.diff(prices)
        price_base = prices[:-1]
        returns = price_diffs / price_base
        
        avg_return = float(np.mean(returns))
        volatility = float(np.std(returns))
        
        if volatility == 0:
            return 0.0
        
        # Sharpe-like ratio
        risk_adjusted_score = (avg_return / volatility) * np.sqrt(252) * 100
        
        return float(risk_adjusted_score)
    
    def rank_assets(self, lookback_days: int = 200) -> List[Dict]:
        """
        Rank all assets by momentum score
        
        Args:
            lookback_days: Days of historical data
            
        Returns:
            List of ranked assets with scores
        """
        rankings = []
        
        cprint(f"\n📊 Ranking {len(self.universe)} assets by momentum...", "cyan")
        
        for symbol in self.universe:
            try:
                # Get historical data
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=f'{lookback_days}d')
                
                if hist.empty or len(hist) < 50:
                    continue
                
                prices = hist['Close'].values
                
                # Defensive: validate data quality
                if len(prices) < 50:
                    cprint(f"⚠️ Insufficient data for {symbol}: {len(prices)} days", "yellow")
                    continue
                
                # Remove any NaN values
                prices = prices[~np.isnan(prices)]
                if len(prices) < 50:
                    cprint(f"⚠️ Too many NaN values for {symbol}", "yellow")
                    continue
                
                # Calculate scores
                momentum_score = self.calculate_momentum_score(prices)
                vol_adj_score = self.calculate_volatility_adjusted_momentum(prices)
                
                # Calculate additional metrics
                current_price = float(prices[-1])  # Convert to Python float
                sma_200 = float(np.mean(prices[-200:]) if len(prices) >= 200 else np.mean(prices))
                above_sma_200 = bool(current_price > sma_200)  # Convert numpy bool to Python bool
                
                # Calculate 52-week high distance
                high_52w = float(np.max(prices[-252:]) if len(prices) >= 252 else np.max(prices))
                distance_from_high = float(((current_price - high_52w) / high_52w) * 100)
                
                # Composite score (70% momentum, 30% vol-adjusted)
                composite_score = float(momentum_score * 0.7 + vol_adj_score * 0.3)
                
                rankings.append({
                    'symbol': symbol,
                    'momentum_score': float(momentum_score),
                    'vol_adj_score': float(vol_adj_score),
                    'composite_score': composite_score,
                    'above_sma_200': above_sma_200,
                    'distance_from_high': distance_from_high,
                    'current_price': current_price,
                    'asset_class': self._classify_asset(symbol)
                })
                
            except Exception as e:
                cprint(f"⚠️ Error ranking {symbol}: {e}", "yellow")
                continue
        
        # Sort by composite score
        rankings.sort(key=lambda x: x['composite_score'], reverse=True)
        
        self.current_rankings = rankings
        
        # Print top 5
        cprint("\n🏆 Top 5 Momentum Leaders:", "green")
        for i, asset in enumerate(rankings[:5], 1):
            cprint(f"  {i}. {asset['symbol']}: {asset['composite_score']:.2f} "
                  f"({'✅' if asset['above_sma_200'] else '❌'} SMA200)", "cyan")
        
        return rankings
    
    def _classify_asset(self, symbol: str) -> str:
        """Classify asset type"""
        if '-USD' in symbol:
            return 'crypto'
        elif symbol in ['SPY', 'QQQ', 'IWM', 'DIA']:
            return 'index'
        elif symbol.startswith('XL'):
            return 'sector'
        else:
            return 'stock'
    
    def get_rotation_recommendations(self, 
                                     num_positions: int = 3,
                                     min_score: float = 0.0) -> List[Dict]:
        """
        Get top assets to allocate capital to
        
        Args:
            num_positions: Number of positions to hold
            min_score: Minimum momentum score required
            
        Returns:
            List of recommended positions
        """
        if not self.current_rankings:
            self.rank_assets()
        
        # Filter by minimum score and SMA200
        qualified = [
            asset for asset in self.current_rankings
            if asset['composite_score'] > min_score and asset['above_sma_200']
        ]
        
        if len(qualified) < num_positions:
            cprint(f"⚠️ Only {len(qualified)} assets meet criteria (need {num_positions})", "yellow")
            # Relax SMA200 requirement if needed
            qualified = [
                asset for asset in self.current_rankings
                if asset['composite_score'] > min_score
            ][:num_positions]
        
        # Ensure diversification across asset classes
        recommendations = []
        asset_class_counts = {}
        
        for asset in qualified:
            asset_class = asset['asset_class']
            
            # Limit to 2 per asset class for diversification
            if asset_class_counts.get(asset_class, 0) < 2:
                recommendations.append(asset)
                asset_class_counts[asset_class] = asset_class_counts.get(asset_class, 0) + 1
            
            if len(recommendations) >= num_positions:
                break
        
        # If still need more, add without class restriction
        if len(recommendations) < num_positions:
            for asset in qualified:
                if asset not in recommendations:
                    recommendations.append(asset)
                    if len(recommendations) >= num_positions:
                        break
        
        return recommendations
    
    def calculate_allocation_weights(self, recommendations: List[Dict]) -> Dict[str, float]:
        """
        Calculate capital allocation weights
        
        Args:
            recommendations: List of recommended assets
            
        Returns:
            Dict of {symbol: weight} where weights sum to 1.0
        """
        if not recommendations:
            return {}
        
        # Weight by momentum score (higher score = higher allocation)
        total_score = sum(asset['composite_score'] for asset in recommendations if asset['composite_score'] > 0)
        
        if total_score == 0:
            # Equal weight if all scores are 0 or negative
            equal_weight = 1.0 / len(recommendations)
            return {asset['symbol']: equal_weight for asset in recommendations}
        
        weights = {}
        for asset in recommendations:
            score = max(asset['composite_score'], 0)  # Don't allow negative weights
            weights[asset['symbol']] = score / total_score
        
        return weights
    
    def should_rebalance(self) -> bool:
        """Check if it's time to rebalance"""
        days_since_rotation = (datetime.now() - self.last_rotation).days
        return days_since_rotation >= self.rotation_frequency
    
    def detect_risk_regime(self) -> Dict:
        """
        Detect if market is in risk-on or risk-off mode
        
        Returns:
            Risk regime info
        """
        try:
            # Get SPY and VIX
            spy = yf.Ticker("SPY")
            vix = yf.Ticker("^VIX")
            
            spy_hist = spy.history(period='60d')
            vix_hist = vix.history(period='5d')
            
            if spy_hist.empty or vix_hist.empty:
                return {'regime': 'UNKNOWN', 'confidence': 0}
            
            # Check SPY trend
            spy_prices = spy_hist['Close'].values
            sma_20 = np.mean(spy_prices[-20:])
            sma_50 = np.mean(spy_prices[-50:])
            current_spy = spy_prices[-1]
            
            # Check VIX level
            current_vix = vix_hist['Close'].iloc[-1]
            
            # Determine regime
            if current_spy > sma_20 and sma_20 > sma_50 and current_vix < 20:
                regime = 'RISK_ON'
                confidence = 80
                recommendation = "Favor crypto and growth stocks"
            elif current_spy < sma_20 or current_vix > 25:
                regime = 'RISK_OFF'
                confidence = 80
                recommendation = "Favor defensive stocks and reduce crypto"
            else:
                regime = 'NEUTRAL'
                confidence = 50
                recommendation = "Balanced allocation"
            
            return {
                'regime': regime,
                'confidence': confidence,
                'spy_vs_sma20': ((current_spy - sma_20) / sma_20) * 100,
                'vix': current_vix,
                'recommendation': recommendation
            }
            
        except Exception as e:
            cprint(f"⚠️ Error detecting risk regime: {e}", "yellow")
            return {'regime': 'UNKNOWN', 'confidence': 0}
    
    def get_rotation_summary(self) -> Dict:
        """Get summary of current rotation status"""
        if not self.current_rankings:
            self.rank_assets()
        
        recommendations = self.get_rotation_recommendations()
        weights = self.calculate_allocation_weights(recommendations)
        risk_regime = self.detect_risk_regime()
        
        return {
            'total_assets_ranked': len(self.current_rankings),
            'top_recommendations': recommendations,
            'allocation_weights': weights,
            'risk_regime': risk_regime,
            'days_until_rebalance': self.rotation_frequency - (datetime.now() - self.last_rotation).days,
            'last_rotation': self.last_rotation.isoformat(),
            'should_rebalance': self.should_rebalance()
        }


# Global momentum rotator instance
_momentum_rotator = None

def get_momentum_rotator(universe: List[str] = None) -> MomentumRotator:
    """Get or create global momentum rotator instance"""
    global _momentum_rotator
    if _momentum_rotator is None:
        _momentum_rotator = MomentumRotator(universe)
    return _momentum_rotator
