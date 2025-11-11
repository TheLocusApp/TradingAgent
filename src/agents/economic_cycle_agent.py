"""
🌙 Moon Dev's Economic Cycle Detection Agent
AI-powered economic cycle analysis using DeepSeek/GPT-4
"""

from typing import Dict, Tuple
from termcolor import cprint


class EconomicCycleAgent:
    """AI-powered economic cycle detection"""
    
    def __init__(self, model_factory=None):
        """Initialize with model factory"""
        self.model_factory = model_factory
        if model_factory is None:
            try:
                from src.models import model_factory as mf
                self.model_factory = mf
            except:
                pass
    
    def detect_cycle(self, indicators: Dict) -> Tuple[str, float]:
        """
        Use AI to detect economic cycle phase
        
        Args:
            indicators: Dict with gdp, unemployment, fed_rate, cpi, vix, etc.
        
        Returns:
            Tuple of (phase, confidence)
        """
        try:
            if not self.model_factory:
                return self._fallback_detection(indicators)
            
            # Prepare prompt for AI
            prompt = f"""You are an expert economist analyzing the current economic cycle.

Current Economic Indicators:
- GDP Growth: {indicators.get('gdp', {}).get('value', 'N/A')}% (trend: {indicators.get('gdp', {}).get('trend', 0)}%)
- Unemployment Rate: {indicators.get('unemployment', {}).get('value', 'N/A')}%
- Federal Funds Rate: {indicators.get('fed_rate', {}).get('value', 'N/A')}%
- CPI Inflation: {indicators.get('cpi', {}).get('value', 'N/A')}% YoY
- VIX (Fear Index): {indicators.get('vix', {}).get('value', 'N/A')}
- Consumer Confidence: {indicators.get('consumer_confidence', {}).get('value', 'N/A')}
- Yield Curve (10Y-2Y): {indicators.get('yield_curve', {}).get('value', 'N/A')}%

Economic Cycle Phases:
1. **Early Expansion**: Recovery from recession, GDP rising, unemployment falling, rates low, confidence improving
2. **Mid Expansion**: Strong growth, low unemployment, moderate inflation, rates rising gradually
3. **Late Expansion**: Growth slowing, inflation high, rates high, yield curve flattening/inverting
4. **Peak**: Maximum growth, very low unemployment, high inflation, aggressive rate hikes
5. **Contraction**: GDP declining, unemployment rising, rates falling, recession fears
6. **Recession**: Negative GDP, high unemployment, low rates, low confidence

Based on these indicators, determine:
1. Current economic cycle phase (choose ONE from above)
2. Confidence level (0-100%)

Respond in this EXACT format:
PHASE: [phase name]
CONFIDENCE: [number between 0-100]
REASONING: [2-3 sentence explanation]"""

            # Get AI response
            model = self.model_factory.get_model('deepseek')  # Use DeepSeek for speed
            response_obj = model.generate_response(
                system_prompt="You are an expert economist.",
                user_content=prompt,
                max_tokens=200,
                temperature=0.3
            )
            response = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)
            
            # Parse response
            phase, confidence = self._parse_ai_response(response)
            
            cprint(f"🤖 AI Economic Cycle: {phase} ({confidence}% confidence)", "cyan")
            return phase, confidence / 100.0
            
        except Exception as e:
            cprint(f"⚠️ AI cycle detection failed: {e}, using fallback", "yellow")
            return self._fallback_detection(indicators)
    
    def _parse_ai_response(self, response: str) -> Tuple[str, float]:
        """Parse AI response"""
        try:
            lines = response.strip().split('\n')
            phase = "Mid Expansion"
            confidence = 60.0
            
            for line in lines:
                if line.startswith('PHASE:'):
                    phase = line.split('PHASE:')[1].strip()
                elif line.startswith('CONFIDENCE:'):
                    conf_str = line.split('CONFIDENCE:')[1].strip().replace('%', '')
                    confidence = float(conf_str)
            
            return phase, confidence
        except:
            return "Mid Expansion", 60.0
    
    def _fallback_detection(self, indicators: Dict) -> Tuple[str, float]:
        """Fallback rule-based detection"""
        try:
            gdp_val = indicators.get('gdp', {}).get('value', 2.5)
            gdp_trend = indicators.get('gdp', {}).get('trend', 0)
            unemp_val = indicators.get('unemployment', {}).get('value', 4.0)
            rate_val = indicators.get('fed_rate', {}).get('value', 5.0)
            cpi_val = indicators.get('cpi', {}).get('value', 3.0)
            
            # Simple rule-based logic
            if gdp_trend > 0 and unemp_val < 4.5 and rate_val < 3.0:
                return 'Early Expansion', 0.75
            elif gdp_val > 2.0 and 3.0 <= rate_val < 5.0:
                return 'Mid Expansion', 0.70
            elif cpi_val > 3.5 and rate_val >= 4.5:
                return 'Late Expansion', 0.65
            elif gdp_val < 0.5 or unemp_val > 6.0:
                return 'Contraction', 0.70
            else:
                return 'Mid Expansion', 0.60
        except:
            return 'Mid Expansion', 0.50
