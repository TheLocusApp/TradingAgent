#!/usr/bin/env python3
"""
📊 Market Regime Detection System
Classifies market conditions for strategy adaptation
Built with love by Moon Dev 🚀
"""

import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
from termcolor import cprint
import yfinance as yf


class RegimeDetector:
    """
    Detects market regime for strategy optimization
    
    Regimes:
    - TRENDING_UP: Strong uptrend (ADX>25, price>EMA)
    - TRENDING_DOWN: Strong downtrend (ADX>25, price<EMA)
    - RANGING: Sideways market (ADX<20)
    - HIGH_VOLATILITY: Volatile conditions (VIX>25 or ATR spike)
    - LOW_VOLATILITY: Calm market (VIX<15)
    """
    
    def __init__(self):
        """Initialize regime detector"""
        self.current_regime = "UNKNOWN"
        self.regime_confidence = 0.0
        self.regime_history = []
        
        # Thresholds
        self.adx_trend_threshold = 25
        self.adx_range_threshold = 20
        self.vix_high_threshold = 25
        self.vix_low_threshold = 15
        
        cprint("✅ Regime Detector initialized", "green")
    
    def calculate_adx(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
        """
        Calculate Average Directional Index (ADX)
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: ADX period (default 14)
            
        Returns:
            Current ADX value
        """
        # Calculate True Range
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        
        # Calculate Directional Movement
        up_move = high - np.roll(high, 1)
        down_move = np.roll(low, 1) - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # Smooth with EMA
        atr = self._ema(tr, period)
        plus_di = 100 * self._ema(plus_dm, period) / atr
        minus_di = 100 * self._ema(minus_dm, period) / atr
        
        # Calculate DX and ADX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        adx = self._ema(dx, period)
        
        return adx[-1] if len(adx) > 0 else 0
    
    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        alpha = 2 / (period + 1)
        ema = np.zeros_like(data)
        ema[0] = data[0]
        
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        
        return ema
    
    def calculate_volatility(self, close: np.ndarray, period: int = 20) -> float:
        """
        Calculate historical volatility (annualized)
        
        Args:
            close: Close prices
            period: Lookback period
            
        Returns:
            Annualized volatility
        """
        returns = np.diff(np.log(close))
        volatility = np.std(returns[-period:]) * np.sqrt(252) * 100
        return volatility
    
    def get_vix(self) -> float:
        """
        Get current VIX level
        
        Returns:
            VIX value or estimated volatility
        """
        try:
            vix = yf.Ticker("^VIX")
            hist = vix.history(period='1d')
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
        except:
            pass
        
        # Fallback: estimate from SPY volatility
        try:
            spy = yf.Ticker("SPY")
            hist = spy.history(period='30d')
            if not hist.empty:
                return self.calculate_volatility(hist['Close'].values)
        except:
            pass
        
        return 18.0  # Default moderate volatility
    
    def detect_regime(self, symbol: str = "SPY", lookback_days: int = 60) -> Dict:
        """
        Detect current market regime
        
        Args:
            symbol: Symbol to analyze (default SPY for market regime)
            lookback_days: Days of historical data
            
        Returns:
            Regime info dict
        """
        try:
            # Get market data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=f'{lookback_days}d')
            
            if hist.empty or len(hist) < 30:
                return self._default_regime()
            
            # Extract OHLC
            high = hist['High'].values
            low = hist['Low'].values
            close = hist['Close'].values
            
            # Calculate indicators
            adx = self.calculate_adx(high, low, close)
            volatility = self.calculate_volatility(close)
            vix = self.get_vix()
            
            # Calculate EMAs for trend direction
            ema_20 = self._ema(close, 20)
            ema_50 = self._ema(close, 50)
            current_price = close[-1]
            
            # Determine regime
            regime = "UNKNOWN"
            confidence = 0.0
            
            # Check for trending conditions
            if adx > self.adx_trend_threshold:
                if current_price > ema_20[-1] and ema_20[-1] > ema_50[-1]:
                    regime = "TRENDING_UP"
                    confidence = min((adx / 40) * 100, 100)  # Scale ADX to confidence
                elif current_price < ema_20[-1] and ema_20[-1] < ema_50[-1]:
                    regime = "TRENDING_DOWN"
                    confidence = min((adx / 40) * 100, 100)
                else:
                    regime = "TRENDING_MIXED"
                    confidence = 50
            
            # Check for ranging conditions
            elif adx < self.adx_range_threshold:
                regime = "RANGING"
                confidence = min(((self.adx_range_threshold - adx) / self.adx_range_threshold) * 100, 100)
            
            # Overlay volatility regime
            if vix > self.vix_high_threshold or volatility > 30:
                regime = f"{regime}_HIGH_VOL"
                confidence *= 0.9  # Reduce confidence in high vol
            elif vix < self.vix_low_threshold:
                regime = f"{regime}_LOW_VOL"
            
            # Store regime
            self.current_regime = regime
            self.regime_confidence = confidence
            
            regime_info = {
                'regime': regime,
                'confidence': confidence,
                'adx': adx,
                'vix': vix,
                'volatility': volatility,
                'trend_direction': 'UP' if current_price > ema_50[-1] else 'DOWN',
                'price_vs_ema20': ((current_price - ema_20[-1]) / ema_20[-1]) * 100,
                'price_vs_ema50': ((current_price - ema_50[-1]) / ema_50[-1]) * 100,
                'detected_at': datetime.now().isoformat(),
                'symbol': symbol
            }
            
            # Add to history
            self.regime_history.append(regime_info)
            if len(self.regime_history) > 100:
                self.regime_history = self.regime_history[-100:]
            
            return regime_info
            
        except Exception as e:
            cprint(f"⚠️ Error detecting regime: {e}", "yellow")
            return self._default_regime()
    
    def _default_regime(self) -> Dict:
        """Return default regime when detection fails"""
        return {
            'regime': 'UNKNOWN',
            'confidence': 0,
            'adx': 0,
            'vix': 18,
            'volatility': 15,
            'trend_direction': 'NEUTRAL',
            'price_vs_ema20': 0,
            'price_vs_ema50': 0,
            'detected_at': datetime.now().isoformat(),
            'symbol': 'SPY'
        }
    
    def get_strategy_recommendation(self, regime_info: Dict) -> Dict:
        """
        Get contextual guidance based on regime (NOT prescriptive commands)
        
        Provides historical performance data and context, but lets agent decide.
        
        Args:
            regime_info: Regime detection result
            
        Returns:
            Contextual guidance with historical performance
        """
        regime = regime_info['regime']
        adx = regime_info['adx']
        vix = regime_info['vix']
        
        recommendations = {
            'regime': regime,
            'confidence': regime_info['confidence'],
            'context': '',
            'historical_performance': {},
            'risk_considerations': []
        }
        
        # Trending up context
        if 'TRENDING_UP' in regime:
            recommendations.update({
                'context': f'Strong upward trend detected (ADX: {adx:.1f}). Directional momentum is present.',
                'historical_performance': {
                    'momentum': {'win_rate': 0.65, 'avg_return': 2.8, 'description': 'Strong in trending markets'},
                    'trend_following': {'win_rate': 0.62, 'avg_return': 2.5, 'description': 'Rides established trends'},
                    'breakout': {'win_rate': 0.58, 'avg_return': 3.2, 'description': 'Captures continuation moves'},
                    'mean_reversion': {'win_rate': 0.45, 'avg_return': 1.2, 'description': 'Fights the trend'},
                    'range_trading': {'win_rate': 0.38, 'avg_return': 0.8, 'description': 'No clear ranges in trends'}
                },
                'position_size_guidance': 1.2,  # Suggestion, not command
                'stop_loss_guidance': 1.5,  # Wider stops suggested
                'risk_considerations': [
                    'Trend exhaustion possible - watch for divergences',
                    'Wider stops reduce whipsaw but increase risk per trade',
                    'Consider scaling in on pullbacks rather than chasing'
                ]
            })
        
        # Trending down strategies
        elif 'TRENDING_DOWN' in regime:
            recommendations.update({
                'preferred_strategies': ['short_momentum', 'defensive', 'hedging'],
                'position_size_multiplier': 0.8,  # Reduce size in downtrends
                'stop_loss_multiplier': 1.3,
                'hold_time_multiplier': 1.5,
                'avoid_strategies': ['long_only', 'momentum']
            })
        
        # Ranging strategies
        elif 'RANGING' in regime:
            recommendations.update({
                'preferred_strategies': ['mean_reversion', 'range_trading', 'scalping'],
                'position_size_multiplier': 1.0,
                'stop_loss_multiplier': 0.8,  # Tighter stops in ranges
                'hold_time_multiplier': 0.5,  # Shorter holds in ranges
                'avoid_strategies': ['trend_following', 'breakout']
            })
        
        # High volatility adjustments
        if 'HIGH_VOL' in regime:
            recommendations['position_size_multiplier'] *= 0.7  # Reduce size in high vol
            recommendations['stop_loss_multiplier'] *= 1.5  # Wider stops
            recommendations['risk_warning'] = "High volatility detected - reduce position sizes"
        
        # Low volatility adjustments
        elif 'LOW_VOL' in regime:
            recommendations['position_size_multiplier'] *= 1.1  # Slightly increase size
            recommendations['stop_loss_multiplier'] *= 0.9  # Tighter stops
        
        return recommendations
    
    def get_regime_display(self) -> Dict:
        """
        Get regime info formatted for UI display
        
        Returns:
            Display-ready regime info
        """
        if not self.regime_history:
            regime_info = self.detect_regime()
        else:
            regime_info = self.regime_history[-1]
        
        regime = regime_info['regime']
        
        # Determine display properties
        if 'TRENDING_UP' in regime:
            emoji = '📈'
            color = '#22c55e'
            label = 'Trending Up'
        elif 'TRENDING_DOWN' in regime:
            emoji = '📉'
            color = '#ef4444'
            label = 'Trending Down'
        elif 'RANGING' in regime:
            emoji = '↔️'
            color = '#eab308'
            label = 'Ranging'
        else:
            emoji = '❓'
            color = '#6b7280'
            label = 'Unknown'
        
        # Add volatility indicator
        vix = regime_info.get('vix', 18)
        if vix > 25:
            vol_label = 'High Volatility'
            vol_color = '#ef4444'
        elif vix < 15:
            vol_label = 'Low Volatility'
            vol_color = '#22c55e'
        else:
            vol_label = 'Normal Volatility'
            vol_color = '#eab308'
        
        return {
            'regime': regime,
            'emoji': emoji,
            'label': label,
            'color': color,
            'confidence': regime_info.get('confidence', 0),
            'vix': vix,
            'vix_label': vol_label,
            'vix_color': vol_color,
            'adx': regime_info.get('adx', 0),
            'recommendation': self.get_strategy_recommendation(regime_info)
        }


# Global regime detector instance
_regime_detector = None

def get_regime_detector() -> RegimeDetector:
    """Get or create global regime detector instance"""
    global _regime_detector
    if _regime_detector is None:
        _regime_detector = RegimeDetector()
    return _regime_detector
