"""
Market Analyst Agent - Deep dive analysis for individual tickers
Provides bull case, bear case, and actionable recommendations
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from termcolor import cprint
import os

from src.models.deepseek_model import DeepSeekModel
from src.data_providers.comprehensive_market_data import ComprehensiveMarketDataProvider
from src.data_providers.screener_data_provider import ScreenerDataProvider


class MarketAnalystAgent:
    """Generates comprehensive bull/bear analysis and trading recommendations"""
    
    def __init__(self):
        """Initialize the market analyst"""
        api_key = os.getenv('DEEPSEEK_KEY')
        if not api_key:
            raise ValueError("DEEPSEEK_KEY not found in environment")
        self.llm = DeepSeekModel(api_key=api_key, model_name="deepseek-chat")
        self.data_provider = ComprehensiveMarketDataProvider()
        self.screener_provider = ScreenerDataProvider()
        cprint("✅ Market Analyst Agent initialized with comprehensive data sources", "green")
    
    def analyze_ticker(self, symbol: str) -> Dict:
        """
        Perform comprehensive analysis on a ticker
        
        Args:
            symbol: Ticker symbol (e.g., 'BTC', 'AAPL')
        
        Returns:
            Dict with bull_case, bear_case, conclusion, signal, confidence, timeframe, etc.
        """
        cprint(f"\n🔍 Analyzing {symbol}...", "cyan")
        
        try:
            # 1. Get comprehensive market data
            market_data = self._get_market_data(symbol)
            
            # Filter out $0 prices (invalid data)
            if market_data.get('current_price', 0) <= 0:
                cprint(f"⚠️ {symbol} has $0 price, skipping", "yellow")
                return None
            
            # 2. Calculate fair value and entry zones
            fair_value_data = self._calculate_fair_value(symbol, market_data)
            
            # 3. Get business cycle context (for long-term analysis)
            business_cycle = self._get_business_cycle_context()
            
            # 4. Generate AI analysis (AI determines timeframe)
            analysis = self._generate_analysis(symbol, market_data, business_cycle)
            
            return {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'timeframe': analysis.get('timeframe', 'swing'),
                'market_data': market_data,
                'chart_analysis': {},
                
                # AI Analysis
                'ai_summary': analysis.get('ai_summary', ''),
                'ai_detailed': analysis.get('ai_detailed', ''),
                
                # Bull/Bear Cases
                'bull_case': analysis.get('bull_case', {'points': [], 'probability': 50}),
                'bear_case': analysis.get('bear_case', {'points': [], 'probability': 50}),
                
                # Conclusion
                'conclusion': analysis.get('conclusion', {}),
                'signal': analysis.get('signal', analysis.get('conclusion', {}).get('signal', 'HOLD')),
                'confidence': analysis.get('confidence', analysis.get('conclusion', {}).get('confidence', 50)),
                'entry_range': analysis.get('entry_range', analysis.get('conclusion', {}).get('entry_range')),
                'target': analysis.get('target', analysis.get('conclusion', {}).get('target')),
                'stop_loss': analysis.get('stop_loss', analysis.get('conclusion', {}).get('stop_loss')),
                'trailing_stop': analysis.get('conclusion', {}).get('trailing_stop', ''),
                'reasoning': analysis.get('reasoning', analysis.get('conclusion', {}).get('reasoning', '')),
                
                # Fair Value & Entry Zones (NEW)
                'fair_value': fair_value_data.get('fair_value', 0),
                'upside_potential': fair_value_data.get('upside_pct', 0),
                'entry_zones': fair_value_data.get('entry_zones', {}),
                'entry_price': fair_value_data.get('entry_price', 0),
                'target_price': fair_value_data.get('target_price', 0),
                'stop_loss': fair_value_data.get('stop_loss', 0),
                'risk_reward_ratio': fair_value_data.get('risk_reward', 0),
                
                # Risk Management
                'risk_management': analysis.get('risk_management', {}),
                
                # Macro Triggers
                'macro_triggers': analysis.get('macro_triggers', {}),
                
                # Business Cycle Context
                'business_cycle': business_cycle
            }
            
        except Exception as e:
            cprint(f"❌ Error analyzing {symbol}: {e}", "red")
            import traceback
            traceback.print_exc()
            # Return fallback analysis
            fallback = self._generate_fallback_analysis(self._get_market_data(symbol))
            return {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'timeframe': 'swing',
                'market_data': {},
                'chart_analysis': {},
                'bull_case': fallback['bull_case'],
                'bear_case': fallback['bear_case'],
                'conclusion': fallback['conclusion'],
                'signal': fallback['conclusion']['signal'],
                'confidence': fallback['conclusion']['confidence'],
                'entry_range': None,
                'target': None,
                'stop_loss': None,
                'reasoning': fallback['conclusion']['reasoning']
            }
    
    def _get_market_data(self, symbol: str) -> Dict:
        """Get comprehensive market data including fundamentals, technicals, and sentiment"""
        try:
            # Determine asset type
            asset_type = 'crypto' if symbol in ['BTC', 'ETH', 'SOL', 'DOGE', 'ADA'] else 'stock'
            
            # Get comprehensive technical data
            data = self.data_provider.get_comprehensive_data(
                symbol=f"{symbol}-USD" if asset_type == 'crypto' else symbol,
                timeframe='1m'
            )
            
            # Get screener data (fundamentals, news, advanced technicals)
            # Note: screener needs price data, so we'll fetch fundamentals and news separately
            fundamentals = self.screener_provider.get_fundamentals(symbol)
            news_sentiment = self.screener_provider.get_news_sentiment(symbol)
            
            screener_data = {
                'fundamentals': fundamentals,
                'news_sentiment': news_sentiment,
                'technicals': {},  # Will be populated from comprehensive data
                'ai_analysis': ''
            }
            
            # Build result with multiple fallback layers
            current_price = data.get('current_price', 0)
            
            # If comprehensive data failed, try yfinance as fallback
            if current_price <= 0:
                try:
                    import yfinance as yf
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                    cprint(f"✅ Fallback to yfinance for {symbol}: ${current_price}", "yellow")
                except Exception as yf_error:
                    cprint(f"⚠️ yfinance fallback failed: {yf_error}", "yellow")
            
            return {
                # Price data with fallback
                'current_price': current_price,
                'price_change_pct': data.get('price_change_pct', 0),
                
                # Technical indicators with fallbacks
                'rsi_7': data.get('current_rsi7') or data.get('rsi_7', 50),
                'rsi_14': data.get('current_rsi14') or data.get('rsi_14', 50),
                'macd': data.get('macd', 'N/A'),
                'ema_20': data.get('current_ema20') or current_price,
                'volume': data.get('current_volume', 'N/A'),
                'avg_volume': data.get('context_avg_volume', 'N/A'),
                'atr': data.get('atr') or (current_price * 0.02),  # Default 2% ATR
                
                # Advanced technicals from screener with fallbacks
                'roc': screener_data.get('technicals', {}).get('roc', 0),
                'adx': screener_data.get('technicals', {}).get('adx', 25),  # Default neutral
                'stoch': screener_data.get('technicals', {}).get('stoch', 50),  # Default neutral
                'obv': screener_data.get('technicals', {}).get('obv', 'neutral'),
                
                # Fundamentals (stocks only)
                'fundamentals': screener_data.get('fundamentals', {}),
                
                # News sentiment
                'news_sentiment': screener_data.get('news_sentiment', {}),
                
                # AI analysis from screener
                'ai_summary': screener_data.get('ai_analysis', ''),
                
                # Asset type
                'asset_type': asset_type,
                
                # Volatility estimate
                'volatility': data.get('volatility', 20)  # Default 20%
            }
        except Exception as e:
            cprint(f"⚠️ Error getting market data: {e}", "yellow")
            import traceback
            traceback.print_exc()
            # Return minimal fallback data
            return {
                'current_price': 0,
                'price_change_pct': 0,
                'rsi_14': 50,
                'macd': 'N/A',
                'volume': 'N/A',
                'atr': 0,
                'roc': 0,
                'adx': 25,
                'stoch': 50,
                'obv': 'neutral',
                'fundamentals': {},
                'news_sentiment': {},
                'asset_type': 'stock'
            }
    
    def _get_business_cycle_context(self) -> Dict:
        """Get current business cycle phase and implications"""
        try:
            import requests
            response = requests.get('http://localhost:5000/api/portfolio/macro', timeout=5)
            if response.status_code == 200:
                data = response.json()
                cycle = data.get('cycle', {})
                phase = cycle.get('phase', 'Unknown')
                confidence = cycle.get('confidence', 0)
                
                # Generate implications based on phase
                implications_map = {
                    'Expansion': 'Growth stocks and cyclicals tend to outperform. Consider increasing equity exposure.',
                    'Peak': 'Market at highs, inflation rising. Consider defensive positioning and profit-taking.',
                    'Contraction': 'Recession risk elevated. Favor defensive sectors, quality stocks, and cash.',
                    'Recovery': 'Early recovery phase. Cyclicals and value stocks may lead the rebound.'
                }
                
                return {
                    'phase': phase,
                    'confidence': confidence,
                    'implications': implications_map.get(phase, 'Economic cycle provides context for positioning.')
                }
        except Exception as e:
            cprint(f"⚠️ Could not fetch business cycle: {e}", "yellow")
        
        return None
    
    def _generate_analysis(self, symbol: str, market_data: Dict, business_cycle: Dict = None) -> Dict:
        """Generate AI-powered bull/bear analysis and recommendation"""
        
        # Build analysis prompt (include business cycle for long-term context)
        prompt = self._build_analysis_prompt(symbol, market_data, business_cycle)
        
        try:
            # Get AI analysis
            response = self.llm.generate_response(
                system_prompt="You are a professional market analyst providing structured JSON analysis.",
                user_content=prompt,
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse JSON response
            if not response.content or not response.content.strip():
                cprint(f"⚠️ Empty AI response, using fallback", "yellow")
                return self._generate_fallback_analysis(market_data)
            
            # Try to extract JSON from response
            content = response.content.strip()
            
            # Sometimes AI wraps JSON in markdown code blocks
            if content.startswith('```'):
                # Extract JSON from code block
                lines = content.split('\n')
                json_lines = []
                in_json = False
                for line in lines:
                    if line.startswith('```'):
                        if in_json:
                            break
                        in_json = True
                        continue
                    if in_json:
                        json_lines.append(line)
                content = '\n'.join(json_lines)
            
            analysis = json.loads(content)
            
            return analysis
            
        except json.JSONDecodeError as e:
            cprint(f"⚠️ Failed to parse AI response: {e}", "yellow")
            cprint(f"Response content: {response.content[:200] if response and response.content else 'None'}", "yellow")
            # Return fallback analysis
            return self._generate_fallback_analysis(market_data)
        except Exception as e:
            cprint(f"❌ Error generating analysis: {e}", "red")
            import traceback
            traceback.print_exc()
            return self._generate_fallback_analysis(market_data)
    
    def _build_analysis_prompt(self, symbol: str, market_data: Dict, business_cycle: Dict = None) -> str:
        """Build the comprehensive analysis prompt for the LLM"""
        
        fundamentals = market_data.get('fundamentals', {})
        
        # Add business cycle context if available
        cycle_context = ""
        if business_cycle:
            phase = business_cycle.get('phase', 'Unknown')
            confidence = int(business_cycle.get('confidence', 0) * 100)
            implications = business_cycle.get('implications', '')
            cycle_context = f"""
            
**BUSINESS CYCLE CONTEXT**:
- Current Phase: {phase}
- Confidence: {confidence}%
- Implications: {implications}

Consider this macro context when determining timeframe and risk assessment, especially for LONG TERM recommendations.
"""
        news_sentiment = market_data.get('news_sentiment', {})
        
        # Safe formatting function that handles both numeric and string values
        def safe_format(value, default=0, format_spec='.2f', prefix='', suffix=''):
            """Safely format a value that might be string or numeric"""
            if isinstance(value, str):
                return value
            try:
                if format_spec == ',.0f':
                    return f"{prefix}{float(value):,.0f}{suffix}"
                elif format_spec == ',.2f':
                    return f"{prefix}{float(value):,.2f}{suffix}"
                elif format_spec == '.2f':
                    return f"{prefix}{float(value):.2f}{suffix}"
                else:
                    return f"{prefix}{value}{suffix}"
            except (ValueError, TypeError):
                return str(value) if value else str(default)
        
        # Pre-format all values to avoid f-string format code conflicts
        current_price = safe_format(market_data.get('current_price', 0), format_spec=',.2f', prefix='$')
        price_change = safe_format(market_data.get('price_change_pct', 0), format_spec='.2f', suffix='%')
        rsi_7 = safe_format(market_data.get('rsi_7', 0), format_spec='.2f')
        rsi_14 = safe_format(market_data.get('rsi_14', 0), format_spec='.2f')
        macd = safe_format(market_data.get('macd', 0), format_spec='.2f')
        ema_20 = safe_format(market_data.get('ema_20', 0), format_spec=',.2f', prefix='$')
        volume = safe_format(market_data.get('volume', 0), format_spec=',.0f')
        avg_volume = safe_format(market_data.get('avg_volume', 0), format_spec=',.0f')
        roc = safe_format(market_data.get('roc', 0), format_spec='.2f', suffix='%')
        adx = safe_format(market_data.get('adx', 0), format_spec='.2f')
        stoch = safe_format(market_data.get('stoch', 0), format_spec='.2f')
        obv = str(market_data.get('obv', 'neutral'))
        pe_ratio = str(fundamentals.get('pe_ratio', 'N/A'))
        sector = str(fundamentals.get('sector', 'N/A'))
        market_cap = str(fundamentals.get('market_cap', 'N/A'))
        profit_margin = str(fundamentals.get('profit_margin', 'N/A'))
        roe = str(fundamentals.get('roe', 'N/A'))
        sentiment_label = str(news_sentiment.get('label', 'Neutral'))
        sentiment_score = safe_format(news_sentiment.get('score', 0), format_spec='.2f')
        article_count = news_sentiment.get('article_count', 0)
        
        prompt = f"""You are an ADVANCED institutional-grade market analyst. Analyze {symbol} comprehensively using ALL available data sources.

PRICE DATA:
- Current Price: {current_price}
- Price Change: {price_change}

TECHNICAL INDICATORS:
- RSI(7): {rsi_7}
- RSI(14): {rsi_14}
- MACD: {macd}
- EMA(20): {ema_20}
- Volume: {volume} (Avg: {avg_volume})

ADVANCED TECHNICALS:
- ROC: {roc}
- ADX: {adx}
- Stochastic: {stoch}
- OBV: {obv}

FUNDAMENTALS (if stock):
- P/E Ratio: {pe_ratio}
- Sector: {sector}
- Market Cap: {market_cap}
- Profit Margin: {profit_margin}
- ROE: {roe}

NEWS SENTIMENT:
- Sentiment: {sentiment_label}
- Score: {sentiment_score}
- Article Count: {article_count}
{cycle_context}

Provide a comprehensive institutional-grade analysis in JSON format:

{{
  "timeframe": "day|swing|long",
  "ai_summary": "One concise sentence summarizing the opportunity (MUST mention macro context if relevant)",
  "ai_detailed": "Detailed 2-3 paragraph analysis explaining the full thesis, risks, catalysts, and how current macro conditions support or challenge this trade",
  "bull_case": {{
    "points": ["Technical reason", "Fundamental reason", "Sentiment reason", "Macro reason"],
    "probability": 65
  }},
  "bear_case": {{
    "points": ["Technical risk", "Fundamental risk", "Sentiment risk", "Macro risk"],
    "probability": 35
  }},
  "conclusion": {{
    "signal": "BUY|SELL|HOLD",
    "confidence": 75,
    "entry_range": {{"low": 103500, "high": 104500}},
    "target": 108000,
    "stop_loss": 101000,
    "trailing_stop": "Use 3% trailing stop after 5% profit",
    "reasoning": "2-3 sentence summary of why this is the best trade"
  }},
  "risk_management": {{
    "position_size": "Suggested % of portfolio (e.g., 5-10%)",
    "risk_reward": "Risk/reward ratio (e.g., 1:3)",
    "max_loss": "Maximum acceptable loss %",
    "scaling": "How to scale in/out (e.g., 'Enter 50% at $100, 50% at $95')"
  }},
  "macro_triggers": {{
    "exit_conditions": ["Condition 1 to exit", "Condition 2 to exit"],
    "watch_for": ["Key event to monitor", "Economic indicator to track"],
    "catalysts": ["Upcoming catalyst 1", "Upcoming catalyst 2"]
  }}
}}

TIMEFRAME DETERMINATION:
- "day": For intraday/scalping opportunities (RSI extremes, high volatility, clear short-term patterns)
- "swing": For 3-7 day trades (moderate trends, consolidation breakouts, mean reversion setups)
- "long": For weeks/months holds (strong fundamentals, major trend changes, accumulation zones)

IMPORTANT:
- YOU MUST determine the best timeframe based on market conditions
- Bull/bear probabilities must sum to 100
- Signal must be BUY, SELL, or HOLD
- Confidence is 0-100
- Entry range, target, stop_loss should match the timeframe:
  * Day trades: tighter stops (1-2%), smaller targets (2-3%)
  * Swing trades: moderate stops (3-5%), medium targets (4-7%)
  * Long-term: wider stops (10-15%), larger targets (15-30%)

Return ONLY valid JSON, no other text."""

        return prompt
    
    def _generate_fallback_analysis(self, market_data: Dict) -> Dict:
        """Generate simple rule-based analysis as fallback"""
        
        rsi = market_data.get('rsi_7', 50)
        price = market_data.get('current_price', 0)
        ema = market_data.get('ema_20', price)
        
        # Simple rules
        if rsi < 30 and price < ema:
            signal = 'BUY'
            confidence = 65
            bull_prob = 70
            bear_prob = 30
        elif rsi > 70 and price > ema:
            signal = 'SELL'
            confidence = 65
            bull_prob = 30
            bear_prob = 70
        else:
            signal = 'HOLD'
            confidence = 50
            bull_prob = 50
            bear_prob = 50
        
        return {
            'timeframe': 'swing',
            'bull_case': {
                'points': ['Technical indicators suggest potential upside', 'Price action shows momentum'],
                'probability': bull_prob
            },
            'bear_case': {
                'points': ['Market conditions show downside risk', 'Volatility remains elevated'],
                'probability': bear_prob
            },
            'conclusion': {
                'signal': signal,
                'confidence': confidence,
                'reasoning': 'Analysis based on technical indicators and market conditions'
            }
        }
    
    def analyze_multiple(self, symbols: List[str]) -> List[Dict]:
        """Analyze multiple tickers (AI determines best timeframe for each)"""
        results = []
        for symbol in symbols:
            result = self.analyze_ticker(symbol)
            if result:  # Filter out None results ($0 prices)
                results.append(result)
        return results
    
    def _calculate_fair_value(self, symbol: str, market_data: Dict) -> Dict:
        """
        Calculate fair value and entry zones using hedge fund methodology
        
        Returns:
            Dict with fair_value, upside_pct, entry_zones, risk_reward
        """
        try:
            current_price = market_data.get('current_price', 0)
            if current_price <= 0:
                return self._get_default_fair_value()
            
            fundamentals = market_data.get('fundamentals', {})
            pe_ratio = fundamentals.get('pe_ratio', 0)
            sector_avg_pe = 20  # Default sector average
            
            # Calculate fair value using multiple methods
            fair_values = []
            
            # Method 1: P/E based valuation (if available)
            if pe_ratio > 0 and pe_ratio < 100:  # Reasonable P/E range
                pe_fair_value = current_price * (sector_avg_pe / pe_ratio)
                fair_values.append(pe_fair_value)
            
            # Method 2: Technical-based fair value (support/resistance)
            rsi = market_data.get('rsi_14', 50)
            if rsi < 30:  # Oversold
                tech_fair_value = current_price * 1.15  # 15% upside
            elif rsi > 70:  # Overbought
                tech_fair_value = current_price * 0.95  # 5% downside
            else:
                tech_fair_value = current_price * 1.05  # 5% upside
            fair_values.append(tech_fair_value)
            
            # Method 3: 52-week range analysis
            week_52_high = fundamentals.get('52_week_high', 0)
            week_52_low = fundamentals.get('52_week_low', 0)
            if week_52_high > 0 and week_52_low > 0:
                # Fair value at 60% of 52-week range
                range_fair_value = week_52_low + (week_52_high - week_52_low) * 0.6
                fair_values.append(range_fair_value)
            
            # Calculate weighted average fair value
            if fair_values:
                fair_value = sum(fair_values) / len(fair_values)
            else:
                fair_value = current_price * 1.10  # Default 10% upside
            
            # Calculate upside potential
            upside_pct = ((fair_value - current_price) / current_price) * 100
            
            # Calculate Entry/Target/Stop Loss (fund manager style)
            # Entry: Current price or slight pullback
            entry_price = current_price
            
            # Target: Beyond fair value for profit taking (1.5x move to fair value)
            # If fair value is above current: target = fair_value + (fair_value - current) * 0.5
            # This gives us a more aggressive profit target beyond just fair value
            if fair_value > current_price:
                target_price = fair_value + (fair_value - current_price) * 0.5
            else:
                # If price above fair value, target is fair value
                target_price = fair_value
            
            # Stop Loss: Based on volatility and support
            atr = market_data.get('atr', current_price * 0.02)  # Default 2% ATR
            stop_loss = current_price - (atr * 2)  # 2x ATR stop
            
            # Ensure stop loss is reasonable (max 10% below entry)
            min_stop = current_price * 0.90
            stop_loss = max(stop_loss, min_stop)
            
            # Calculate risk/reward ratio
            risk = entry_price - stop_loss
            reward = target_price - entry_price
            risk_reward = reward / risk if risk > 0 else 0
            
            # Entry zones for reference (optional display)
            entry_zones = {
                'entry': entry_price,
                'target': target_price,
                'stop_loss': stop_loss
            }
            
            return {
                'fair_value': round(fair_value, 2),
                'upside_pct': round(upside_pct, 2),
                'entry_zones': entry_zones,
                'entry_price': round(entry_price, 2),
                'target_price': round(target_price, 2),
                'stop_loss': round(stop_loss, 2),
                'risk_reward': round(risk_reward, 2)
            }
            
        except Exception as e:
            cprint(f"⚠️ Fair value calculation error: {e}", "yellow")
            return self._get_default_fair_value()
    
    def _get_default_fair_value(self) -> Dict:
        """Return default fair value data"""
        return {
            'fair_value': 0,
            'upside_pct': 0,
            'entry_zones': {
                'aggressive': {'min': 0, 'max': 0, 'label': 'Now', 'description': 'N/A'},
                'moderate': {'min': 0, 'max': 0, 'label': 'Pullback', 'description': 'N/A'},
                'conservative': {'min': 0, 'max': 0, 'label': 'Dip', 'description': 'N/A'}
            },
            'stop_loss': 0,
            'take_profit': 0,
            'risk_reward': 0
        }


if __name__ == "__main__":
    # Test the analyst
    analyst = MarketAnalystAgent()
    
    # Test with BTC
    result = analyst.analyze_ticker('BTC')
    
    print("\n" + "="*60)
    print(f"ANALYSIS: {result['symbol']}")
    print("="*60)
    print(f"\n🐂 BULL CASE (Probability: {result['bull_case']['probability']}%)")
    for point in result['bull_case']['points']:
        print(f"  • {point}")
    
    print(f"\n🐻 BEAR CASE (Probability: {result['bear_case']['probability']}%)")
    for point in result['bear_case']['points']:
        print(f"  • {point}")
    
    print(f"\n🎯 CONCLUSION")
    print(f"  Signal: {result['conclusion']['signal']}")
    print(f"  Confidence: {result['conclusion']['confidence']}%")
    print(f"  Reasoning: {result['conclusion']['reasoning']}")
