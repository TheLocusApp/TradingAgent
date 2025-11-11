#!/usr/bin/env python3
"""
🌙 Moon Dev's Advanced Screener Data Provider
Comprehensive market data for institutional-grade screening
Built with love by Moon Dev 🚀

Features:
- Fundamental analysis (P/E, market cap, revenue growth)
- News sentiment analysis
- Advanced technical indicators (ADX, Stochastic, ROC)
- Multi-timeframe analysis
- Cached data (12-hour windows, refreshed twice daily)
"""

import os
import requests
import time
import json
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from termcolor import cprint
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class ScreenerDataProvider:
    """Advanced screener data provider with fundamentals, news, and technicals"""
    
    def __init__(self):
        """Initialize screener data provider"""
        self._cache = {}
        self._cache_duration = 43200  # 12 hours (refreshed twice daily)
        self._cache_dir = Path("src/data/screener_cache")
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        
        # API Keys
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self.polygon_key = os.getenv('POLYGON_API_KEY', '')
        
        # Rate limiting
        self._request_counts = {
            'alpha_vantage': {'count': 0, 'reset_time': time.time()},
            'polygon': {'count': 0, 'reset_time': time.time()}
        }
        
        # Load cache from disk
        self._load_cache_from_disk()
        
        cprint("✅ Advanced screener data provider initialized", "green")
    
    def _load_cache_from_disk(self):
        """Load cached data from disk"""
        try:
            cache_file = self._cache_dir / "screener_cache.json"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    disk_cache = json.load(f)
                    # Only load non-expired cache entries
                    now = time.time()
                    for key, value in disk_cache.items():
                        if 'timestamp' in value and now - value['timestamp'] < self._cache_duration:
                            self._cache[key] = value
                cprint(f"📦 Loaded {len(self._cache)} cached entries from disk", "cyan")
        except Exception as e:
            cprint(f"⚠️ Could not load cache from disk: {str(e)}", "yellow")
    
    def _save_cache_to_disk(self):
        """Save cache to disk"""
        try:
            cache_file = self._cache_dir / "screener_cache.json"
            with open(cache_file, 'w') as f:
                json.dump(self._cache, f)
        except Exception as e:
            cprint(f"⚠️ Could not save cache to disk: {str(e)}", "yellow")
    
    def _check_rate_limit(self, source: str) -> bool:
        """Check if we're within rate limits"""
        now = time.time()
        
        if source == 'alpha_vantage':
            # Reset counter every 24 hours
            if now - self._request_counts[source]['reset_time'] > 86400:
                self._request_counts[source] = {'count': 0, 'reset_time': now}
            return self._request_counts[source]['count'] < 25
        
        elif source == 'polygon':
            # Reset counter every minute
            if now - self._request_counts[source]['reset_time'] > 60:
                self._request_counts[source] = {'count': 0, 'reset_time': now}
            return self._request_counts[source]['count'] < 5
        
        return True
    
    def _increment_rate_limit(self, source: str):
        """Increment rate limit counter"""
        self._request_counts[source]['count'] += 1
    
    def get_fundamentals(self, symbol: str) -> Dict:
        """
        Get fundamental data for a stock
        
        Returns:
            Dict with P/E, market cap, revenue growth, etc.
        """
        cache_key = f"fundamentals_{symbol}"
        
        # Check cache first (12-hour cache)
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            if time.time() - cached_data.get('timestamp', 0) < self._cache_duration:
                return cached_data.get('data', {})
        
        # Try Alpha Vantage for fundamentals
        if self._check_rate_limit('alpha_vantage'):
            try:
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'OVERVIEW',
                    'symbol': symbol,
                    'apikey': self.alpha_vantage_key
                }
                
                response = requests.get(url, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                self._increment_rate_limit('alpha_vantage')
                
                if data and 'Symbol' in data:
                    fundamentals = {
                        'market_cap': float(data.get('MarketCapitalization', 0)),
                        'pe_ratio': float(data.get('PERatio', 0)) if data.get('PERatio') != 'None' else 0,
                        'peg_ratio': float(data.get('PEGRatio', 0)) if data.get('PEGRatio') != 'None' else 0,
                        'eps': float(data.get('EPS', 0)) if data.get('EPS') != 'None' else 0,
                        'revenue_per_share': float(data.get('RevenuePerShareTTM', 0)) if data.get('RevenuePerShareTTM') != 'None' else 0,
                        'profit_margin': float(data.get('ProfitMargin', 0)) if data.get('ProfitMargin') != 'None' else 0,
                        'roe': float(data.get('ReturnOnEquityTTM', 0)) if data.get('ReturnOnEquityTTM') != 'None' else 0,
                        'debt_to_equity': float(data.get('DebtToEquity', 0)) if data.get('DebtToEquity') != 'None' else 0,
                        'dividend_yield': float(data.get('DividendYield', 0)) if data.get('DividendYield') != 'None' else 0,
                        'sector': data.get('Sector', 'Unknown'),
                        'industry': data.get('Industry', 'Unknown'),
                        '52_week_high': float(data.get('52WeekHigh', 0)) if data.get('52WeekHigh') != 'None' else 0,
                        '52_week_low': float(data.get('52WeekLow', 0)) if data.get('52WeekLow') != 'None' else 0,
                    }
                    
                    # Cache the result
                    self._cache[cache_key] = {
                        'data': fundamentals,
                        'timestamp': time.time()
                    }
                    self._save_cache_to_disk()
                    
                    return fundamentals
                
            except Exception as e:
                cprint(f"⚠️ Alpha Vantage fundamentals failed for {symbol}: {str(e)[:50]}", "yellow")
        
        # Return empty fundamentals if failed
        return {
            'market_cap': 0, 'pe_ratio': 0, 'peg_ratio': 0, 'eps': 0,
            'revenue_per_share': 0, 'profit_margin': 0, 'roe': 0,
            'debt_to_equity': 0, 'dividend_yield': 0,
            'sector': 'Unknown', 'industry': 'Unknown',
            '52_week_high': 0, '52_week_low': 0
        }
    
    def get_news_sentiment(self, symbol: str) -> Dict:
        """
        Get news sentiment for a stock
        
        Returns:
            Dict with sentiment score, label, and article count
        """
        cache_key = f"news_sentiment_{symbol}"
        
        # Check cache first (12-hour cache)
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            if time.time() - cached_data.get('timestamp', 0) < self._cache_duration:
                return cached_data.get('data', {})
        
        # Try Alpha Vantage News Sentiment
        if self._check_rate_limit('alpha_vantage'):
            try:
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'NEWS_SENTIMENT',
                    'tickers': symbol,
                    'apikey': self.alpha_vantage_key,
                    'limit': 50  # Get last 50 news articles
                }
                
                response = requests.get(url, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                self._increment_rate_limit('alpha_vantage')
                
                if 'feed' in data and len(data['feed']) > 0:
                    # Calculate average sentiment
                    sentiments = []
                    for article in data['feed']:
                        for ticker_sentiment in article.get('ticker_sentiment', []):
                            if ticker_sentiment.get('ticker') == symbol:
                                score = float(ticker_sentiment.get('ticker_sentiment_score', 0))
                                sentiments.append(score)
                    
                    if sentiments:
                        avg_sentiment = np.mean(sentiments)
                        
                        # Convert to label
                        if avg_sentiment > 0.15:
                            label = 'Bullish'
                        elif avg_sentiment > 0.05:
                            label = 'Somewhat Bullish'
                        elif avg_sentiment > -0.05:
                            label = 'Neutral'
                        elif avg_sentiment > -0.15:
                            label = 'Somewhat Bearish'
                        else:
                            label = 'Bearish'
                        
                        sentiment_data = {
                            'score': avg_sentiment,
                            'label': label,
                            'article_count': len(sentiments),
                            'relevance': np.mean([float(article.get('relevance_score', 0)) for article in data['feed'][:10]])
                        }
                        
                        # Cache the result
                        self._cache[cache_key] = {
                            'data': sentiment_data,
                            'timestamp': time.time()
                        }
                        self._save_cache_to_disk()
                        
                        return sentiment_data
                
            except Exception as e:
                cprint(f"⚠️ News sentiment failed for {symbol}: {str(e)[:50]}", "yellow")
        
        # Return neutral sentiment if failed
        return {
            'score': 0,
            'label': 'Neutral',
            'article_count': 0,
            'relevance': 0
        }
    
    def calculate_advanced_technicals(self, df: pd.DataFrame) -> Dict:
        """
        Calculate advanced technical indicators
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dict with ADX, Stochastic, ROC, etc.
        """
        try:
            if df.empty or len(df) < 20:
                return self._get_default_technicals()
            
            # Ensure we have the right columns
            if 'Close' not in df.columns:
                df = df.rename(columns={'close': 'Close', 'high': 'High', 'low': 'Low', 'volume': 'Volume'})
            
            technicals = {}
            
            # 1. Rate of Change (ROC) - Momentum indicator
            roc_period = 10
            technicals['roc'] = ((df['Close'].iloc[-1] - df['Close'].iloc[-roc_period-1]) / df['Close'].iloc[-roc_period-1] * 100) if len(df) > roc_period else 0
            
            # 2. Stochastic Oscillator
            if len(df) >= 14:
                low_14 = df['Low'].rolling(window=14).min()
                high_14 = df['High'].rolling(window=14).max()
                technicals['stochastic_k'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
                technicals['stochastic_k'] = float(technicals['stochastic_k'].iloc[-1]) if not pd.isna(technicals['stochastic_k'].iloc[-1]) else 50
                
                # Stochastic %D (3-period SMA of %K)
                technicals['stochastic_d'] = float(technicals['stochastic_k'])  # Simplified
            else:
                technicals['stochastic_k'] = 50
                technicals['stochastic_d'] = 50
            
            # 3. ADX (Average Directional Index) - Trend strength
            if len(df) >= 14:
                # Simplified ADX calculation
                high_low = df['High'] - df['Low']
                high_close = abs(df['High'] - df['Close'].shift())
                low_close = abs(df['Low'] - df['Close'].shift())
                tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                atr = tr.rolling(window=14).mean()
                technicals['atr'] = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0
                
                # Simplified ADX (just use ATR as proxy for trend strength)
                technicals['adx'] = min(100, (technicals['atr'] / df['Close'].iloc[-1] * 100) * 10) if df['Close'].iloc[-1] > 0 else 0
            else:
                technicals['atr'] = 0
                technicals['adx'] = 0
            
            # 4. Bollinger Bands
            if len(df) >= 20:
                sma_20 = df['Close'].rolling(window=20).mean()
                std_20 = df['Close'].rolling(window=20).std()
                technicals['bb_upper'] = float(sma_20.iloc[-1] + (2 * std_20.iloc[-1])) if not pd.isna(sma_20.iloc[-1]) else 0
                technicals['bb_lower'] = float(sma_20.iloc[-1] - (2 * std_20.iloc[-1])) if not pd.isna(sma_20.iloc[-1]) else 0
                technicals['bb_width'] = ((technicals['bb_upper'] - technicals['bb_lower']) / sma_20.iloc[-1] * 100) if sma_20.iloc[-1] > 0 else 0
            else:
                technicals['bb_upper'] = 0
                technicals['bb_lower'] = 0
                technicals['bb_width'] = 0
            
            # 5. Volume indicators
            if len(df) >= 20:
                avg_volume = df['Volume'].rolling(window=20).mean()
                technicals['volume_ratio'] = float(df['Volume'].iloc[-1] / avg_volume.iloc[-1]) if avg_volume.iloc[-1] > 0 else 1.0
                
                # On-Balance Volume (OBV)
                obv = (df['Volume'] * (~df['Close'].diff().le(0) * 2 - 1)).cumsum()
                technicals['obv_trend'] = 'up' if obv.iloc[-1] > obv.iloc[-5] else 'down'
            else:
                technicals['volume_ratio'] = 1.0
                technicals['obv_trend'] = 'neutral'
            
            return technicals
            
        except Exception as e:
            cprint(f"⚠️ Error calculating advanced technicals: {str(e)}", "yellow")
            return self._get_default_technicals()
    
    def _get_default_technicals(self) -> Dict:
        """Return default technical values"""
        return {
            'roc': 0,
            'stochastic_k': 50,
            'stochastic_d': 50,
            'adx': 0,
            'atr': 0,
            'bb_upper': 0,
            'bb_lower': 0,
            'bb_width': 0,
            'volume_ratio': 1.0,
            'obv_trend': 'neutral'
        }
    
    def calculate_investment_score(self, fundamentals: Dict, current_price: float) -> Tuple[float, str]:
        """
        Calculate investment quality score for long-term holdings
        
        Returns:
            Tuple of (score 0-100, rating)
        """
        score = 0
        reasons = []
        
        # 1. Valuation (30 points)
        pe_ratio = fundamentals.get('pe_ratio', 0)
        if 0 < pe_ratio < 15:
            score += 30
            reasons.append("Undervalued P/E")
        elif 15 <= pe_ratio < 25:
            score += 20
            reasons.append("Fair P/E")
        elif 25 <= pe_ratio < 40:
            score += 10
            reasons.append("Moderate P/E")
        
        # 2. Profitability (25 points)
        profit_margin = fundamentals.get('profit_margin', 0)
        roe = fundamentals.get('roe', 0)
        if profit_margin > 0.20:
            score += 15
            reasons.append("High profit margin")
        elif profit_margin > 0.10:
            score += 10
        
        if roe > 0.15:
            score += 10
            reasons.append("Strong ROE")
        elif roe > 0.10:
            score += 5
        
        # 3. Financial Health (20 points)
        debt_to_equity = fundamentals.get('debt_to_equity', 0)
        if debt_to_equity < 0.5:
            score += 20
            reasons.append("Low debt")
        elif debt_to_equity < 1.0:
            score += 15
        elif debt_to_equity < 2.0:
            score += 10
        
        # 4. Market Position (15 points)
        market_cap = fundamentals.get('market_cap', 0)
        if market_cap > 100_000_000_000:  # $100B+
            score += 15
            reasons.append("Large cap")
        elif market_cap > 10_000_000_000:  # $10B+
            score += 12
            reasons.append("Mid cap")
        elif market_cap > 2_000_000_000:  # $2B+
            score += 8
        
        # 5. Price Position (10 points)
        high_52 = fundamentals.get('52_week_high', 0)
        low_52 = fundamentals.get('52_week_low', 0)
        if high_52 > 0 and low_52 > 0:
            position = (current_price - low_52) / (high_52 - low_52) * 100
            if 20 <= position <= 40:  # Sweet spot - not overbought, not oversold
                score += 10
                reasons.append("Good entry point")
            elif 40 < position <= 60:
                score += 7
            elif position < 20:
                score += 5
                reasons.append("Near 52-week low")
        
        # Rating
        if score >= 80:
            rating = "Strong Buy"
        elif score >= 65:
            rating = "Buy"
        elif score >= 50:
            rating = "Hold"
        elif score >= 35:
            rating = "Underperform"
        else:
            rating = "Avoid"
        
        return score, rating, reasons
    
    def get_comprehensive_analysis(self, symbol: str, df: pd.DataFrame, current_price: float) -> Dict:
        """
        Get comprehensive analysis combining fundamentals, news, and technicals
        
        Args:
            symbol: Stock symbol
            df: Historical OHLCV data
            current_price: Current price
            
        Returns:
            Dict with complete analysis
        """
        # Get fundamentals
        fundamentals = self.get_fundamentals(symbol)
        
        # Get news sentiment
        news_sentiment = self.get_news_sentiment(symbol)
        
        # Calculate advanced technicals
        technicals = self.calculate_advanced_technicals(df)
        
        # Calculate investment score
        investment_score, investment_rating, investment_reasons = self.calculate_investment_score(fundamentals, current_price)
        
        return {
            'fundamentals': fundamentals,
            'news_sentiment': news_sentiment,
            'technicals': technicals,
            'investment_score': investment_score,
            'investment_rating': investment_rating,
            'investment_reasons': investment_reasons
        }


if __name__ == "__main__":
    """Test the screener data provider"""
    print("\n🧪 Testing Screener Data Provider\n")
    
    provider = ScreenerDataProvider()
    
    # Test fundamentals
    print("📊 Testing Fundamentals:")
    fundamentals = provider.get_fundamentals('AAPL')
    print(f"  Market Cap: ${fundamentals['market_cap']:,.0f}")
    print(f"  P/E Ratio: {fundamentals['pe_ratio']:.2f}")
    print(f"  Sector: {fundamentals['sector']}")
    
    # Test news sentiment
    print("\n📰 Testing News Sentiment:")
    sentiment = provider.get_news_sentiment('AAPL')
    print(f"  Sentiment: {sentiment['label']} ({sentiment['score']:.3f})")
    print(f"  Articles: {sentiment['article_count']}")
    
    print("\n✅ All tests complete!")
