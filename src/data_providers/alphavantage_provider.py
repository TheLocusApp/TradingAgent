#!/usr/bin/env python3
"""
🌙 Moon Dev's Alpha Vantage Provider
Production-ready provider for stocks, crypto, macro data, and market intelligence
Built with love by Moon Dev 🚀

Features:
- Top gainers/losers/active stocks (dynamic discovery)
- Macro indicators (GDP, CPI, unemployment, Fed rate)
- Sector performance
- Economic cycle detection
- Crypto data (fallback for CoinGecko)
- Aggressive caching (prevent rate limits)
"""

import os
import requests
import time
import json
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from termcolor import cprint
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class AlphaVantageProvider:
    """Production-ready Alpha Vantage provider with aggressive caching"""
    
    def __init__(self):
        """Initialize Alpha Vantage provider"""
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self.base_url = "https://www.alphavantage.co/query"
        
        # Cache configuration
        self._cache_dir = Path("src/data/alphavantage_cache")
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache = {}
        
        # Cache durations (in seconds)
        self._cache_durations = {
            'macro': 86400,        # 24 hours (daily data)
            'sector': 43200,       # 12 hours (twice daily)
            'fundamentals': 43200, # 12 hours
            'top_movers': 300,     # 5 minutes
            'crypto': 300,         # 5 minutes
            'news': 3600,          # 1 hour
        }
        
        # Rate limiting
        self._request_count = 0
        self._request_reset_time = time.time()
        self._max_requests_per_day = 25  # Free tier limit
        
        # Load cache from disk
        self._load_cache_from_disk()
        
        cprint("✅ Alpha Vantage provider initialized (production mode)", "green")
    
    def _load_cache_from_disk(self):
        """Load cached data from disk"""
        try:
            cache_file = self._cache_dir / "av_cache.json"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    disk_cache = json.load(f)
                    now = time.time()
                    # Only load non-expired entries
                    for key, value in disk_cache.items():
                        if 'timestamp' in value:
                            cache_type = value.get('type', 'macro')
                            duration = self._cache_durations.get(cache_type, 3600)
                            if now - value['timestamp'] < duration:
                                self._cache[key] = value
                cprint(f"📦 Loaded {len(self._cache)} cached Alpha Vantage entries", "cyan")
        except Exception as e:
            cprint(f"⚠️ Could not load cache: {str(e)}", "yellow")
    
    def _save_cache_to_disk(self):
        """Save cache to disk"""
        try:
            cache_file = self._cache_dir / "av_cache.json"
            with open(cache_file, 'w') as f:
                json.dump(self._cache, f)
        except Exception as e:
            cprint(f"⚠️ Could not save cache: {str(e)}", "yellow")
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        now = time.time()
        
        # Reset counter every 24 hours
        if now - self._request_reset_time > 86400:
            self._request_count = 0
            self._request_reset_time = now
        
        return self._request_count < self._max_requests_per_day
    
    def _make_request(self, params: Dict, cache_key: str, cache_type: str = 'macro') -> Optional[Dict]:
        """Make API request with caching and rate limiting"""
        
        # Check cache first
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            cache_duration = self._cache_durations.get(cache_type, 3600)
            if time.time() - cached_data.get('timestamp', 0) < cache_duration:
                cprint(f"📦 Using cached data for {cache_key}", "cyan")
                return cached_data.get('data')
        
        # Check rate limit
        if not self._check_rate_limit():
            cprint(f"⚠️ Alpha Vantage rate limit reached ({self._max_requests_per_day}/day)", "yellow")
            # Return cached data even if expired
            if cache_key in self._cache:
                cprint(f"📦 Using expired cache for {cache_key}", "yellow")
                return self._cache[cache_key].get('data')
            return None
        
        # Make request
        try:
            params['apikey'] = self.api_key
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            self._request_count += 1
            
            # Check for API errors
            if 'Error Message' in data or 'Note' in data:
                cprint(f"⚠️ Alpha Vantage error: {data.get('Error Message', data.get('Note'))}", "yellow")
                return None
            
            # Cache the result
            self._cache[cache_key] = {
                'data': data,
                'timestamp': time.time(),
                'type': cache_type
            }
            self._save_cache_to_disk()
            
            cprint(f"✅ Alpha Vantage API call successful ({self._request_count}/{self._max_requests_per_day})", "green")
            return data
            
        except Exception as e:
            cprint(f"❌ Alpha Vantage request failed: {str(e)[:100]}", "red")
            # Return cached data if available
            if cache_key in self._cache:
                return self._cache[cache_key].get('data')
            return None
    
    def get_top_gainers_losers(self) -> Dict:
        """
        Get top gainers, losers, and most actively traded stocks
        
        Returns:
            Dict with 'top_gainers', 'top_losers', 'most_actively_traded'
        """
        cache_key = "top_movers"
        params = {'function': 'TOP_GAINERS_LOSERS'}
        
        data = self._make_request(params, cache_key, 'top_movers')
        
        if not data:
            return {'top_gainers': [], 'top_losers': [], 'most_actively_traded': []}
        
        return {
            'top_gainers': data.get('top_gainers', [])[:20],  # Top 20
            'top_losers': data.get('top_losers', [])[:20],
            'most_actively_traded': data.get('most_actively_traded', [])[:20]
        }
    
    def get_sector_performance(self) -> Dict:
        """
        Get real-time and historical sector performance
        
        Returns:
            Dict with sector performance data
        """
        cache_key = "sector_performance"
        params = {'function': 'SECTOR'}
        
        data = self._make_request(params, cache_key, 'sector')
        
        if not data:
            return {}
        
        # Extract real-time performance
        realtime = data.get('Rank A: Real-Time Performance', {})
        
        return {
            'realtime': realtime,
            'one_day': data.get('Rank B: 1 Day Performance', {}),
            'five_day': data.get('Rank C: 5 Day Performance', {}),
            'one_month': data.get('Rank D: 1 Month Performance', {}),
            'three_month': data.get('Rank E: 3 Month Performance', {}),
            'ytd': data.get('Rank F: Year-to-Date (YTD) Performance', {}),
            'one_year': data.get('Rank G: 1 Year Performance', {}),
        }
    
    def get_macro_indicator(self, indicator: str) -> Optional[pd.DataFrame]:
        """
        Get macro economic indicator
        
        Args:
            indicator: GDP, CPI, UNEMPLOYMENT, FEDERAL_FUNDS_RATE, etc.
            
        Returns:
            DataFrame with historical data
        """
        cache_key = f"macro_{indicator}"
        params = {'function': indicator}
        
        data = self._make_request(params, cache_key, 'macro')
        
        if not data or 'data' not in data:
            return None
        
        try:
            df = pd.DataFrame(data['data'])
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date', ascending=False)
            return df
        except Exception as e:
            cprint(f"⚠️ Error parsing macro data: {str(e)}", "yellow")
            return None
    
    def get_gdp(self) -> Optional[pd.DataFrame]:
        """Get GDP data"""
        return self.get_macro_indicator('REAL_GDP')
    
    def get_cpi(self) -> Optional[pd.DataFrame]:
        """Get CPI (inflation) data"""
        return self.get_macro_indicator('CPI')
    
    def get_unemployment(self) -> Optional[pd.DataFrame]:
        """Get unemployment rate data"""
        return self.get_macro_indicator('UNEMPLOYMENT')
    
    def get_federal_funds_rate(self) -> Optional[pd.DataFrame]:
        """Get Federal Funds Rate data"""
        return self.get_macro_indicator('FEDERAL_FUNDS_RATE')
    
    def get_treasury_yield(self, maturity: str = '10year') -> Optional[pd.DataFrame]:
        """
        Get Treasury yield data
        
        Args:
            maturity: '3month', '2year', '5year', '10year', '30year'
        """
        indicator_map = {
            '3month': 'TREASURY_YIELD',
            '2year': 'TREASURY_YIELD',
            '5year': 'TREASURY_YIELD',
            '10year': 'TREASURY_YIELD',
            '30year': 'TREASURY_YIELD'
        }
        
        cache_key = f"treasury_{maturity}"
        params = {
            'function': 'TREASURY_YIELD',
            'interval': 'monthly',
            'maturity': maturity
        }
        
        data = self._make_request(params, cache_key, 'macro')
        
        if not data or 'data' not in data:
            return None
        
        try:
            df = pd.DataFrame(data['data'])
            df['date'] = pd.to_datetime(df['date'])
            df['value'] = pd.to_numeric(df['value'])
            df = df.sort_values('date', ascending=False)
            return df
        except Exception as e:
            cprint(f"⚠️ Error parsing treasury data: {str(e)}", "yellow")
            return None
    
    def get_crypto_price(self, symbol: str, market: str = 'USD') -> Optional[Dict]:
        """
        Get cryptocurrency price (fallback for CoinGecko)
        
        Args:
            symbol: Crypto symbol (BTC, ETH, etc.)
            market: Market currency (USD, EUR, etc.)
            
        Returns:
            Dict with price and change data
        """
        cache_key = f"crypto_{symbol}_{market}"
        params = {
            'function': 'CURRENCY_EXCHANGE_RATE',
            'from_currency': symbol,
            'to_currency': market
        }
        
        data = self._make_request(params, cache_key, 'crypto')
        
        if not data or 'Realtime Currency Exchange Rate' not in data:
            return None
        
        try:
            rate_data = data['Realtime Currency Exchange Rate']
            price = float(rate_data.get('5. Exchange Rate', 0))
            
            return {
                'price': price,
                'change': 0,  # Alpha Vantage doesn't provide 24h change directly
                'volume': 0,
                'source': 'alphavantage'
            }
        except Exception as e:
            cprint(f"⚠️ Error parsing crypto data: {str(e)}", "yellow")
            return None
    
    def detect_economic_cycle(self) -> Tuple[str, float, Dict]:
        """
        Detect current economic cycle phase using macro indicators
        
        Returns:
            Tuple of (phase, confidence, indicators)
            
        Phases:
        - Early Expansion: GDP rising, unemployment falling, rates low
        - Mid Expansion: GDP strong, employment high, rates rising
        - Late Expansion: GDP slowing, inflation high, rates high
        - Recession: GDP negative, unemployment rising, rates falling
        """
        try:
            # Get macro indicators
            gdp = self.get_gdp()
            unemployment = self.get_unemployment()
            fed_rate = self.get_federal_funds_rate()
            cpi = self.get_cpi()
            
            indicators = {}
            
            # GDP trend
            if gdp is not None and len(gdp) >= 2:
                gdp['value'] = pd.to_numeric(gdp['value'])
                latest_gdp = gdp.iloc[0]['value']
                prev_gdp = gdp.iloc[1]['value']
                gdp_trend = 'rising' if latest_gdp > prev_gdp else 'falling'
                indicators['gdp'] = {'value': latest_gdp, 'trend': gdp_trend}
            else:
                indicators['gdp'] = {'value': 2.5, 'trend': 'rising'}  # Default
            
            # Unemployment trend
            if unemployment is not None and len(unemployment) >= 2:
                unemployment['value'] = pd.to_numeric(unemployment['value'])
                latest_unemp = unemployment.iloc[0]['value']
                prev_unemp = unemployment.iloc[1]['value']
                unemp_trend = 'falling' if latest_unemp < prev_unemp else 'rising'
                indicators['unemployment'] = {'value': latest_unemp, 'trend': unemp_trend}
            else:
                indicators['unemployment'] = {'value': 4.0, 'trend': 'falling'}  # Default
            
            # Fed rate level
            if fed_rate is not None and len(fed_rate) >= 1:
                fed_rate['value'] = pd.to_numeric(fed_rate['value'])
                latest_rate = fed_rate.iloc[0]['value']
                indicators['fed_rate'] = {'value': latest_rate}
            else:
                indicators['fed_rate'] = {'value': 5.0}  # Default
            
            # CPI (inflation)
            if cpi is not None and len(cpi) >= 1:
                cpi['value'] = pd.to_numeric(cpi['value'])
                latest_cpi = cpi.iloc[0]['value']
                indicators['cpi'] = {'value': latest_cpi}
            else:
                indicators['cpi'] = {'value': 3.0}  # Default
            
            # Cycle detection logic
            gdp_val = indicators['gdp']['value']
            gdp_trend = indicators['gdp']['trend']
            unemp_trend = indicators['unemployment']['trend']
            rate_val = indicators['fed_rate']['value']
            cpi_val = indicators['cpi']['value']
            
            # Early Expansion: GDP rising, unemployment falling, rates low
            if gdp_trend == 'rising' and unemp_trend == 'falling' and rate_val < 3.0:
                phase = 'Early Expansion'
                confidence = 0.85
            
            # Mid Expansion: GDP strong, employment good, rates rising
            elif gdp_val > 2.0 and gdp_trend == 'rising' and 3.0 <= rate_val < 5.0:
                phase = 'Mid Expansion'
                confidence = 0.80
            
            # Late Expansion: GDP slowing, inflation high, rates high
            elif gdp_trend == 'falling' and cpi_val > 3.5 and rate_val >= 4.5:
                phase = 'Late Expansion'
                confidence = 0.75
            
            # Recession: GDP negative or very low, unemployment rising
            elif gdp_val < 0.5 or unemp_trend == 'rising':
                phase = 'Recession'
                confidence = 0.80
            
            # Default to Mid Expansion
            else:
                phase = 'Mid Expansion'
                confidence = 0.60
            
            cprint(f"📊 Economic Cycle: {phase} ({confidence*100:.0f}% confidence)", "cyan")
            
            return phase, confidence, indicators
            
        except Exception as e:
            cprint(f"⚠️ Error detecting economic cycle: {str(e)}", "yellow")
            return 'Mid Expansion', 0.50, {}
    
    def get_sector_allocation_recommendation(self, cycle_phase: str) -> Dict:
        """
        Get recommended sector allocation based on economic cycle
        
        Args:
            cycle_phase: Economic cycle phase
            
        Returns:
            Dict with sector allocations (percentages)
        """
        # Sector allocation by cycle phase
        allocations = {
            'Early Expansion': {
                'Technology': 25,
                'Consumer Discretionary': 20,
                'Financials': 15,
                'Industrials': 15,
                'Healthcare': 10,
                'Materials': 10,
                'Energy': 5,
                'Consumer Staples': 0,
                'Utilities': 0,
                'Real Estate': 0
            },
            'Mid Expansion': {
                'Technology': 20,
                'Industrials': 20,
                'Materials': 15,
                'Energy': 15,
                'Financials': 10,
                'Consumer Discretionary': 10,
                'Healthcare': 10,
                'Consumer Staples': 0,
                'Utilities': 0,
                'Real Estate': 0
            },
            'Late Expansion': {
                'Energy': 25,
                'Materials': 20,
                'Healthcare': 15,
                'Consumer Staples': 15,
                'Utilities': 10,
                'Financials': 10,
                'Technology': 5,
                'Consumer Discretionary': 0,
                'Industrials': 0,
                'Real Estate': 0
            },
            'Recession': {
                'Healthcare': 30,
                'Consumer Staples': 25,
                'Utilities': 20,
                'Technology': 15,
                'Financials': 10,
                'Consumer Discretionary': 0,
                'Industrials': 0,
                'Materials': 0,
                'Energy': 0,
                'Real Estate': 0
            }
        }
        
        return allocations.get(cycle_phase, allocations['Mid Expansion'])


if __name__ == "__main__":
    """Test the Alpha Vantage provider"""
    print("\n🧪 Testing Alpha Vantage Provider\n")
    
    provider = AlphaVantageProvider()
    
    # Test top movers
    print("📊 Testing Top Movers:")
    movers = provider.get_top_gainers_losers()
    print(f"  Top Gainers: {len(movers['top_gainers'])}")
    print(f"  Top Losers: {len(movers['top_losers'])}")
    print(f"  Most Active: {len(movers['most_actively_traded'])}")
    
    # Test sector performance
    print("\n📈 Testing Sector Performance:")
    sectors = provider.get_sector_performance()
    if sectors.get('realtime'):
        print(f"  Sectors tracked: {len(sectors['realtime'])}")
    
    # Test economic cycle
    print("\n🔄 Testing Economic Cycle Detection:")
    phase, confidence, indicators = provider.detect_economic_cycle()
    print(f"  Phase: {phase}")
    print(f"  Confidence: {confidence*100:.0f}%")
    print(f"  Indicators: {indicators}")
    
    # Test sector allocation
    print("\n💼 Testing Sector Allocation:")
    allocation = provider.get_sector_allocation_recommendation(phase)
    for sector, pct in allocation.items():
        if pct > 0:
            print(f"  {sector}: {pct}%")
    
    print("\n✅ All tests complete!")
