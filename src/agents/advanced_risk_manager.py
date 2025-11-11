#!/usr/bin/env python3
"""
🛡️ Advanced Risk Management System
Dynamic position sizing, trailing stops, and risk controls
Built with love by Moon Dev 🚀
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from termcolor import cprint


class AdvancedRiskManager:
    """
    Advanced risk management with dynamic features
    
    AGENTIC APPROACH: Provides GUIDANCE, not commands
    - Calculates suggested metrics
    - Agent receives as recommendations
    - Agent can override with reasoning
    - Tracks override success for learning
    
    Features:
    - Kelly Criterion position sizing
    - Volatility-adjusted stops
    - Multi-level trailing stops
    - Confidence-based sizing
    - Regime-aware risk adjustment
    """
    
    def __init__(self, base_risk_pct: float = 0.02):
        """
        Initialize risk manager
        
        Args:
            base_risk_pct: Base risk per trade (default 2%)
        """
        self.base_risk_pct = base_risk_pct
        self.position_trackers: Dict[str, Dict] = {}  # Track position metrics
        self.override_history: List[Dict] = []  # Track when agents override guidance
        
        cprint("✅ Advanced Risk Manager initialized (Agentic Mode)", "green")
    
    def calculate_position_size(self, 
                                balance: float,
                                entry_price: float,
                                stop_loss_price: float,
                                confidence: int = 70,
                                win_rate: float = 0.50,
                                volatility_multiplier: float = 1.0) -> Tuple[float, float]:
        """
        Calculate optimal position size using multiple factors
        
        Args:
            balance: Available capital
            entry_price: Entry price
            stop_loss_price: Stop loss price
            confidence: AI confidence (0-100)
            win_rate: Historical win rate (0-1)
            volatility_multiplier: Regime volatility adjustment
            
        Returns:
            (position_size_dollars, position_size_units)
        """
        # Base risk amount
        base_risk_dollars = balance * self.base_risk_pct
        
        # Adjust for confidence (50% confidence = 0.5x size, 90% = 1.5x size)
        confidence_multiplier = 0.5 + (confidence / 100) * 1.0
        
        # Adjust for win rate (Kelly-inspired)
        if win_rate > 0.5:
            win_rate_multiplier = 1.0 + (win_rate - 0.5) * 0.5  # Up to 1.25x for 100% win rate
        else:
            win_rate_multiplier = 0.5 + win_rate  # Down to 0.5x for 0% win rate
        
        # Adjust for volatility (reduce size in high vol)
        vol_adjusted_multiplier = 1.0 / volatility_multiplier
        
        # Calculate final risk amount
        adjusted_risk = base_risk_dollars * confidence_multiplier * win_rate_multiplier * vol_adjusted_multiplier
        
        # Clamp between 0.5% and 5% of balance
        adjusted_risk = max(balance * 0.005, min(adjusted_risk, balance * 0.05))
        
        # Calculate position size based on stop distance
        stop_distance = abs(entry_price - stop_loss_price)
        if stop_distance == 0:
            stop_distance = entry_price * 0.02  # Default 2% stop
        
        position_size_units = adjusted_risk / stop_distance
        position_size_dollars = position_size_units * entry_price
        
        # Don't exceed 30% of balance in single position
        max_position = balance * 0.30
        if position_size_dollars > max_position:
            position_size_dollars = max_position
            position_size_units = position_size_dollars / entry_price
        
        return position_size_dollars, position_size_units
    
    def calculate_dynamic_stop_loss(self,
                                    entry_price: float,
                                    direction: str,
                                    atr: float,
                                    volatility_regime: str = "NORMAL") -> float:
        """
        Calculate volatility-adjusted stop loss
        
        Args:
            entry_price: Entry price
            direction: 'LONG' or 'SHORT'
            atr: Average True Range
            volatility_regime: Market volatility state
            
        Returns:
            Stop loss price
        """
        # Base ATR multiplier
        if volatility_regime == "HIGH_VOL":
            atr_multiplier = 2.5  # Wider stops in high vol
        elif volatility_regime == "LOW_VOL":
            atr_multiplier = 1.5  # Tighter stops in low vol
        else:
            atr_multiplier = 2.0  # Normal stops
        
        stop_distance = atr * atr_multiplier
        
        if direction == 'LONG':
            stop_loss = entry_price - stop_distance
        else:  # SHORT
            stop_loss = entry_price + stop_distance
        
        return stop_loss
    
    def initialize_trailing_stop(self,
                                 position_id: str,
                                 entry_price: float,
                                 stop_loss: float,
                                 direction: str,
                                 atr: float):
        """
        Initialize multi-level trailing stop system
        
        Args:
            position_id: Unique position identifier
            entry_price: Entry price
            stop_loss: Initial stop loss
            direction: 'LONG' or 'SHORT'
            atr: Average True Range
        """
        self.position_trackers[position_id] = {
            'entry_price': entry_price,
            'current_stop': stop_loss,
            'peak_price': entry_price,
            'direction': direction,
            'atr': atr,
            'trailing_active': False,
            'trail_level': 0,  # 0-5 levels
            'created_at': datetime.now().isoformat()
        }
    
    def update_trailing_stop(self,
                            position_id: str,
                            current_price: float,
                            current_atr: float) -> Tuple[float, bool]:
        """
        Update trailing stop based on profit levels
        
        Multi-level trailing system:
        - Breakeven: +2% profit → move stop to entry
        - Level 1: +5% profit → trail at 1.5 ATR
        - Level 2: +10% profit → trail at 1.0 ATR
        - Level 3: +15% profit → trail at 0.7 ATR
        - Level 4: +20% profit → trail at 0.5 ATR
        
        Args:
            position_id: Position identifier
            current_price: Current market price
            current_atr: Current ATR
            
        Returns:
            (new_stop_loss, should_exit)
        """
        if position_id not in self.position_trackers:
            return None, False
        
        tracker = self.position_trackers[position_id]
        entry_price = tracker['entry_price']
        direction = tracker['direction']
        current_stop = tracker['current_stop']
        
        # Update peak price
        if direction == 'LONG':
            if current_price > tracker['peak_price']:
                tracker['peak_price'] = current_price
            profit_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # SHORT
            if current_price < tracker['peak_price']:
                tracker['peak_price'] = current_price
            profit_pct = ((entry_price - current_price) / entry_price) * 100
        
        # Check if stop hit
        if direction == 'LONG' and current_price <= current_stop:
            return current_stop, True
        elif direction == 'SHORT' and current_price >= current_stop:
            return current_stop, True
        
        # Determine trailing level based on profit
        new_stop = current_stop
        
        if profit_pct >= 20:  # Level 4: Tight trail
            trail_distance = current_atr * 0.5
            tracker['trail_level'] = 4
        elif profit_pct >= 15:  # Level 3
            trail_distance = current_atr * 0.7
            tracker['trail_level'] = 3
        elif profit_pct >= 10:  # Level 2
            trail_distance = current_atr * 1.0
            tracker['trail_level'] = 2
        elif profit_pct >= 5:  # Level 1
            trail_distance = current_atr * 1.5
            tracker['trail_level'] = 1
        elif profit_pct >= 2:  # Breakeven
            new_stop = entry_price
            tracker['trailing_active'] = True
            tracker['current_stop'] = new_stop
            return new_stop, False
        else:
            # No trailing yet
            return current_stop, False
        
        # Calculate new trailing stop
        if direction == 'LONG':
            potential_stop = tracker['peak_price'] - trail_distance
            new_stop = max(current_stop, potential_stop)  # Only move up
        else:  # SHORT
            potential_stop = tracker['peak_price'] + trail_distance
            new_stop = min(current_stop, potential_stop)  # Only move down
        
        tracker['current_stop'] = new_stop
        tracker['trailing_active'] = True
        
        return new_stop, False
    
    def calculate_take_profit_levels(self,
                                     entry_price: float,
                                     direction: str,
                                     atr: float,
                                     risk_reward_ratio: float = 2.5) -> List[Dict]:
        """
        Calculate multiple take profit levels
        
        Args:
            entry_price: Entry price
            direction: 'LONG' or 'SHORT'
            atr: Average True Range
            risk_reward_ratio: Target risk/reward ratio
            
        Returns:
            List of take profit levels with percentages
        """
        # Calculate target based on ATR and R:R ratio
        target_distance = atr * risk_reward_ratio * 2
        
        if direction == 'LONG':
            full_target = entry_price + target_distance
            
            levels = [
                {'level': 1, 'price': entry_price + target_distance * 0.33, 'size_pct': 33, 'label': 'TP1 (33%)'},
                {'level': 2, 'price': entry_price + target_distance * 0.67, 'size_pct': 33, 'label': 'TP2 (67%)'},
                {'level': 3, 'price': full_target, 'size_pct': 34, 'label': 'TP3 (100%)'}
            ]
        else:  # SHORT
            full_target = entry_price - target_distance
            
            levels = [
                {'level': 1, 'price': entry_price - target_distance * 0.33, 'size_pct': 33, 'label': 'TP1 (33%)'},
                {'level': 2, 'price': entry_price - target_distance * 0.67, 'size_pct': 33, 'label': 'TP2 (67%)'},
                {'level': 3, 'price': full_target, 'size_pct': 34, 'label': 'TP3 (100%)'}
            ]
        
        return levels
    
    def should_reduce_risk(self,
                          recent_trades: List[Dict],
                          lookback: int = 10) -> Tuple[bool, float, str]:
        """
        Determine if risk should be reduced based on recent performance
        
        Args:
            recent_trades: List of recent trade results
            lookback: Number of trades to analyze
            
        Returns:
            (should_reduce, multiplier, reason)
        """
        if len(recent_trades) < lookback:
            return False, 1.0, "Insufficient trade history"
        
        recent = recent_trades[-lookback:]
        
        # Calculate metrics
        losses = [t for t in recent if t.get('pnl', 0) < 0]
        loss_streak = 0
        for t in reversed(recent):
            if t.get('pnl', 0) < 0:
                loss_streak += 1
            else:
                break
        
        loss_rate = len(losses) / len(recent)
        
        # Reduce risk conditions
        if loss_streak >= 3:
            return True, 0.5, f"Loss streak: {loss_streak} trades"
        
        if loss_rate > 0.7:  # More than 70% losses
            return True, 0.6, f"High loss rate: {loss_rate*100:.0f}%"
        
        # Calculate drawdown
        cumulative_pnl = sum(t.get('pnl', 0) for t in recent)
        if cumulative_pnl < -0.05:  # More than 5% drawdown
            return True, 0.7, f"Recent drawdown: {cumulative_pnl*100:.1f}%"
        
        return False, 1.0, "Risk levels normal"
    
    def get_position_risk_summary(self, position_id: str) -> Optional[Dict]:
        """Get risk summary for a position"""
        if position_id not in self.position_trackers:
            return None
        
        tracker = self.position_trackers[position_id]
        
        return {
            'position_id': position_id,
            'entry_price': tracker['entry_price'],
            'current_stop': tracker['current_stop'],
            'peak_price': tracker['peak_price'],
            'direction': tracker['direction'],
            'trailing_active': tracker['trailing_active'],
            'trail_level': tracker['trail_level'],
            'created_at': tracker['created_at']
        }
    
    def remove_position_tracker(self, position_id: str):
        """Remove position tracker when position is closed"""
        if position_id in self.position_trackers:
            del self.position_trackers[position_id]
    
    def get_risk_guidance(self,
                         balance: float,
                         entry_price: float,
                         direction: str,
                         confidence: int,
                         win_rate: float,
                         atr: float,
                         regime_info: Dict,
                         news_context: str = "") -> Dict:
        """
        Generate risk guidance for agent (AGENTIC APPROACH)
        
        Returns guidance that agent can choose to follow or override
        
        Args:
            balance: Available capital
            entry_price: Proposed entry price
            direction: 'LONG' or 'SHORT'
            confidence: AI confidence (0-100)
            win_rate: Historical win rate
            atr: Average True Range
            regime_info: Market regime data
            news_context: Recent news summary
            
        Returns:
            Risk guidance dict with suggestions and reasoning
        """
        # Calculate suggested metrics
        volatility_regime = regime_info.get('regime', 'NORMAL')
        vix = regime_info.get('vix', 18)
        
        # Suggested stop loss
        suggested_stop = self.calculate_dynamic_stop_loss(
            entry_price, direction, atr, volatility_regime
        )
        
        # Suggested position size
        vol_multiplier = 1.0 + (vix - 18) / 10
        suggested_size_dollars, suggested_size_units = self.calculate_position_size(
            balance, entry_price, suggested_stop, confidence, win_rate, vol_multiplier
        )
        
        # Calculate risk metrics
        risk_dollars = abs(suggested_size_units * (entry_price - suggested_stop))
        risk_pct = (risk_dollars / balance) * 100
        
        # Generate reasoning
        reasoning_parts = []
        
        if vix > 25:
            reasoning_parts.append(f"High volatility (VIX: {vix:.1f}) - consider reducing size")
        elif vix < 15:
            reasoning_parts.append(f"Low volatility (VIX: {vix:.1f}) - can increase size slightly")
        
        if confidence < 60:
            reasoning_parts.append(f"Lower confidence ({confidence}%) - reduced position size")
        elif confidence > 80:
            reasoning_parts.append(f"High confidence ({confidence}%) - increased position size")
        
        if win_rate < 0.45:
            reasoning_parts.append(f"Below-average win rate ({win_rate*100:.0f}%) - conservative sizing")
        elif win_rate > 0.60:
            reasoning_parts.append(f"Strong win rate ({win_rate*100:.0f}%) - aggressive sizing allowed")
        
        if 'TRENDING' in volatility_regime:
            reasoning_parts.append("Trending market - wider stops recommended")
        elif 'RANGING' in volatility_regime:
            reasoning_parts.append("Ranging market - tighter stops recommended")
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Normal market conditions"
        
        # Override flexibility based on context
        override_allowed = True
        override_guidance = "You may override these suggestions if you have strong conviction based on news, technical setup, or market microstructure."
        
        if vix > 30:
            override_guidance = "⚠️ Extreme volatility - overrides should be rare and well-justified."
        
        guidance = {
            'suggested_stop_loss': suggested_stop,
            'suggested_position_size_dollars': suggested_size_dollars,
            'suggested_position_size_units': suggested_size_units,
            'risk_dollars': risk_dollars,
            'risk_pct': risk_pct,
            'reasoning': reasoning,
            'override_allowed': override_allowed,
            'override_guidance': override_guidance,
            'regime': volatility_regime,
            'vix': vix,
            'confidence_used': confidence,
            'win_rate_used': win_rate,
            'atr_used': atr,
            'timestamp': datetime.now().isoformat()
        }
        
        return guidance
    
    def record_override(self,
                       agent_id: str,
                       guidance: Dict,
                       actual_decision: Dict,
                       reasoning: str):
        """
        Record when agent overrides risk guidance
        
        Args:
            agent_id: Agent identifier
            guidance: Original guidance provided
            actual_decision: What agent actually decided
            reasoning: Agent's reasoning for override
        """
        override = {
            'agent_id': agent_id,
            'timestamp': datetime.now().isoformat(),
            'guidance': guidance,
            'actual_decision': actual_decision,
            'reasoning': reasoning,
            'outcome': None  # Will be filled when trade closes
        }
        
        self.override_history.append(override)
        
        # Keep only last 100 overrides
        if len(self.override_history) > 100:
            self.override_history = self.override_history[-100:]
    
    def get_override_success_rate(self, agent_id: str = None) -> Dict:
        """
        Calculate success rate of guidance overrides
        
        Args:
            agent_id: Optional agent filter
            
        Returns:
            Override statistics
        """
        overrides = self.override_history
        if agent_id:
            overrides = [o for o in overrides if o['agent_id'] == agent_id]
        
        if not overrides:
            return {'total': 0, 'success_rate': 0, 'message': 'No overrides recorded'}
        
        completed = [o for o in overrides if o.get('outcome') is not None]
        if not completed:
            return {'total': len(overrides), 'success_rate': 0, 'message': 'No completed overrides yet'}
        
        successful = sum(1 for o in completed if o['outcome'] == 'success')
        success_rate = successful / len(completed)
        
        return {
            'total_overrides': len(overrides),
            'completed_overrides': len(completed),
            'successful_overrides': successful,
            'success_rate': success_rate,
            'message': f"{success_rate*100:.1f}% of overrides were successful"
        }


# Global risk manager instance
_risk_manager = None

def get_risk_manager() -> AdvancedRiskManager:
    """Get or create global risk manager instance"""
    global _risk_manager
    if _risk_manager is None:
        _risk_manager = AdvancedRiskManager()
    return _risk_manager
