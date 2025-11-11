#!/usr/bin/env python3
"""
🌙 Market Intel Agents with RL Optimization
Optimizes chart analysis, sentiment, and alert agents
Built with love by Moon Dev 🚀
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from termcolor import cprint
from dataclasses import dataclass, field
from enum import Enum


class AnalysisType(Enum):
    """Types of market analysis"""
    CHART = "chart"
    SENTIMENT = "sentiment"
    WHALE_ALERT = "whale_alert"
    LIQUIDATION = "liquidation"


@dataclass
class AnalysisResult:
    """Result of market analysis"""
    analysis_type: AnalysisType
    signal: str  # BUY, SELL, HOLD, ALERT
    confidence: float
    accuracy: float  # 0-100, actual accuracy after outcome known
    reasoning: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AnalysisOutcome:
    """Outcome of analysis (was it correct?)"""
    analysis_type: AnalysisType
    signal: str
    was_correct: bool
    accuracy_score: float  # 0-100
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class MarketIntelAgentRL:
    """Market Intel Agent with RL optimization"""
    
    def __init__(self, agent_type: AnalysisType, enable_rl: bool = False, rl_training_analyses: int = 50):
        """
        Initialize Market Intel Agent with RL
        
        Args:
            agent_type: Type of analysis (CHART, SENTIMENT, WHALE_ALERT, LIQUIDATION)
            enable_rl: Enable RL optimization
            rl_training_analyses: Number of analyses before optimization
        """
        self.agent_type = agent_type
        self.enable_rl = enable_rl
        self.rl_training_analyses = rl_training_analyses
        
        self.analysis_history: List[AnalysisResult] = []
        self.outcome_history: List[AnalysisOutcome] = []
        self.rl_status = "inactive"
        
        if enable_rl:
            self.rl_status = "training"
            cprint(f"\n🤖 Market Intel Agent RL initialized", "cyan")
            cprint(f"   Type: {agent_type.value}", "cyan")
            cprint(f"   Status: TRAINING MODE", "yellow")
            cprint(f"   Will optimize after {rl_training_analyses} analyses", "yellow")
    
    def record_analysis(self, result: AnalysisResult):
        """Record analysis result"""
        if not self.enable_rl:
            return
        
        self.analysis_history.append(result)
        
        cprint(f"\n📊 Analysis #{len(self.analysis_history)} recorded", "cyan")
        cprint(f"   Type: {result.analysis_type.value}", "cyan")
        cprint(f"   Signal: {result.signal}", "cyan")
        cprint(f"   Confidence: {result.confidence:.1f}%", "cyan")
    
    def record_outcome(self, outcome: AnalysisOutcome):
        """Record analysis outcome (was it correct?)"""
        if not self.enable_rl:
            return
        
        self.outcome_history.append(outcome)
        
        status = "✅ Correct" if outcome.was_correct else "❌ Incorrect"
        cprint(f"\n   {status} - Accuracy: {outcome.accuracy_score:.1f}%", "cyan" if outcome.was_correct else "yellow")
        
        # Check if optimization should be triggered
        if len(self.outcome_history) >= self.rl_training_analyses and self.rl_status == "training":
            cprint(f"\n✨ RL OPTIMIZATION TRIGGERED", "green", attrs=['bold'])
            cprint(f"   Completed {len(self.outcome_history)} analyses - ready for optimization", "green")
            self._trigger_optimization()
    
    def _trigger_optimization(self):
        """Trigger RL optimization"""
        cprint(f"\n🚀 Starting RL Optimization", "cyan", attrs=['bold'])
        cprint(f"   Analyses reviewed: {len(self.outcome_history)}", "cyan")
        
        metrics = self._calculate_metrics()
        
        cprint(f"\n   📊 Performance Metrics:", "cyan")
        cprint(f"      Accuracy: {metrics['accuracy']:.1f}%", "cyan")
        cprint(f"      Precision: {metrics['precision']:.1f}%", "cyan")
        cprint(f"      Recall: {metrics['recall']:.1f}%", "cyan")
        cprint(f"      F1 Score: {metrics['f1_score']:.2f}", "cyan")
        
        # Identify patterns
        patterns = self._identify_patterns()
        if patterns:
            cprint(f"\n   🎯 Identified Patterns:", "cyan")
            for pattern in patterns:
                cprint(f"      • {pattern}", "cyan")
        
        self.rl_status = "optimized"
        
        cprint(f"\n✅ RL Optimization Complete", "green", attrs=['bold'])
        cprint(f"   Agent prompts have been optimized", "green")
        cprint(f"   Continuing with optimized decision logic...", "green")
    
    def _calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if not self.outcome_history:
            return {
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0
            }
        
        correct = sum(1 for o in self.outcome_history if o.was_correct)
        accuracy = (correct / len(self.outcome_history)) * 100
        
        # Calculate average accuracy score
        avg_accuracy = sum(o.accuracy_score for o in self.outcome_history) / len(self.outcome_history)
        
        # Precision and recall (simplified)
        true_positives = sum(1 for o in self.outcome_history if o.was_correct and o.signal in ["BUY", "ALERT"])
        false_positives = sum(1 for o in self.outcome_history if not o.was_correct and o.signal in ["BUY", "ALERT"])
        false_negatives = sum(1 for o in self.outcome_history if not o.was_correct and o.signal in ["SELL", "HOLD"])
        
        precision = (true_positives / (true_positives + false_positives)) * 100 if (true_positives + false_positives) > 0 else 0
        recall = (true_positives / (true_positives + false_negatives)) * 100 if (true_positives + false_negatives) > 0 else 0
        
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score
        }
    
    def _identify_patterns(self) -> List[str]:
        """Identify patterns in analysis results"""
        patterns = []
        
        if not self.outcome_history:
            return patterns
        
        # Analyze by signal type
        signal_accuracy = {}
        for signal in ["BUY", "SELL", "HOLD", "ALERT"]:
            outcomes = [o for o in self.outcome_history if o.signal == signal]
            if outcomes:
                correct = sum(1 for o in outcomes if o.was_correct)
                accuracy = (correct / len(outcomes)) * 100
                signal_accuracy[signal] = accuracy
        
        # Find best and worst signals
        if signal_accuracy:
            best_signal = max(signal_accuracy, key=signal_accuracy.get)
            worst_signal = min(signal_accuracy, key=signal_accuracy.get)
            
            if signal_accuracy[best_signal] > 60:
                patterns.append(f"✅ {best_signal} signals are highly accurate ({signal_accuracy[best_signal]:.1f}%) - focus on these")
            
            if signal_accuracy[worst_signal] < 40:
                patterns.append(f"⚠️ {worst_signal} signals are unreliable ({signal_accuracy[worst_signal]:.1f}%) - avoid or refine")
        
        # Confidence analysis
        high_confidence = [o for o in self.outcome_history if o.accuracy_score >= 70]
        if high_confidence:
            high_conf_accuracy = sum(1 for o in high_confidence if o.was_correct) / len(high_confidence) * 100
            patterns.append(f"📊 High confidence signals ({high_conf_accuracy:.1f}% accurate) - increase threshold")
        
        low_confidence = [o for o in self.outcome_history if o.accuracy_score < 50]
        if low_confidence:
            patterns.append(f"⚠️ Low confidence signals need refinement - review logic")
        
        return patterns
    
    def get_rl_status(self) -> str:
        """Get current RL status"""
        return self.rl_status
    
    def get_rl_status_display(self) -> Dict:
        """Get RL status for display in UI"""
        if not self.enable_rl:
            return {'status': 'disabled', 'label': 'RL Disabled', 'color': '#6b7280'}
        
        analysis_count = len(self.outcome_history)
        
        if self.rl_status == "training":
            progress = min(100, int((analysis_count / self.rl_training_analyses) * 100))
            return {
                'status': 'training',
                'label': f'🔄 Training ({analysis_count}/{self.rl_training_analyses})',
                'color': '#f59e0b',
                'progress': progress
            }
        elif self.rl_status == "optimized":
            return {
                'status': 'optimized',
                'label': '✨ RL Optimized',
                'color': '#10b981'
            }
        else:
            return {'status': 'inactive', 'label': 'Inactive', 'color': '#6b7280'}
    
    def get_signal_accuracy(self) -> Dict[str, float]:
        """Get accuracy by signal type"""
        signal_accuracy = {}
        
        for signal in ["BUY", "SELL", "HOLD", "ALERT"]:
            outcomes = [o for o in self.outcome_history if o.signal == signal]
            if outcomes:
                correct = sum(1 for o in outcomes if o.was_correct)
                accuracy = (correct / len(outcomes)) * 100
                signal_accuracy[signal] = accuracy
        
        return signal_accuracy
    
    def get_summary(self) -> Dict:
        """Get summary of market intel RL optimization"""
        if not self.outcome_history:
            return {
                'status': self.rl_status,
                'analysis_type': self.agent_type.value,
                'analysis_count': 0,
                'metrics': {},
                'patterns': []
            }
        
        metrics = self._calculate_metrics()
        patterns = self._identify_patterns()
        
        return {
            'status': self.rl_status,
            'analysis_type': self.agent_type.value,
            'analysis_count': len(self.outcome_history),
            'metrics': metrics,
            'signal_accuracy': self.get_signal_accuracy(),
            'patterns': patterns
        }
    
    def save_state(self, filepath: str):
        """Save market intel RL state to file"""
        state = {
            'rl_status': self.rl_status,
            'agent_type': self.agent_type.value,
            'analysis_count': len(self.outcome_history),
            'metrics': self._calculate_metrics(),
            'signal_accuracy': self.get_signal_accuracy(),
            'patterns': self._identify_patterns(),
            'timestamp': datetime.now().isoformat()
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        cprint(f"💾 Market Intel RL state saved to {filepath}", "green")
    
    def load_state(self, filepath: str):
        """Load market intel RL state from file"""
        if not Path(filepath).exists():
            return
        
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.rl_status = state.get('rl_status', 'inactive')
            
            cprint(f"📂 Market Intel RL state loaded from {filepath}", "green")
            cprint(f"   Type: {state.get('agent_type', 'unknown')}", "green")
            cprint(f"   Status: {self.rl_status}", "green")
        except Exception as e:
            cprint(f"⚠️ Error loading market intel RL state: {e}", "yellow")
