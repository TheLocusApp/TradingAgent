#!/usr/bin/env python3
"""
🌙 Moon Dev's FRED API Provider
Federal Reserve Economic Data provider for macro indicators
Built with love by Moon Dev 🚀

Features:
- Real-time macro indicators (GDP, CPI, Unemployment, Fed Funds Rate, etc.)
- Historical trending data (month-over-month, quarter-over-quarter)
- Aggressive caching to prevent rate limits
- Fallback to cached data on errors
"""

import os
import requests
import time
import json
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from termcolor import cprint
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class FREDProvider:
    """FRED API provider for macro economic data"""
    
    # FRED Series IDs for key indicators
    SERIES_IDS = {
        'gdp': 'GDP',                          # Gross Domestic Product
        'unemployment': 'UNRATE',              # Unemployment Rate
        'cpi': 'CPIAUCSL',                     # Consumer Price Index (will convert to YoY %)
        'cpi_yoy': 'CPIAUCSL',                 # For YoY calculation
        'fed_rate': 'FEDFUNDS',                # Federal Funds Rate
        'pmi': 'INDPRO',                       # Industrial Production Index (PMI proxy - more reliable than MANEMP)
        'consumer_confidence': 'UMCSENT',      # University of Michigan Consumer Sentiment
        'vix': 'VIXCLS',                       # VIX (from CBOE)
        'yield_10y': 'DGS10',                  # 10-Year Treasury Yield
        'yield_2y': 'DGS2',                    # 2-Year Treasury Yield
    }
    
    def __init__(self):
        """Initialize FRED provider"""
        self.api_key = os.getenv('FRED_API_KEY', '')
        self.base_url = "https://api.stlouisfed.org/fred/series/observations"
        
        # Cache configuration
        self._cache_dir = Path("src/data/fred_cache")
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache = {}
        self._cache_duration = 3600  # 1 hour cache
        
        # Load cache from disk
        self._load_cache_from_disk()
        
        if not self.api_key:
            cprint("⚠️ FRED_API_KEY not found in .env - using cached data only", "yellow")
        else:
            cprint("✅ FRED provider initialized", "green")
    
    def _load_cache_from_disk(self):
        """Load cached data from disk"""
        try:
            cache_file = self._cache_dir / "fred_cache.json"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    disk_cache = json.load(f)
                    now = time.time()
                    # Only load non-expired entries
                    for key, value in disk_cache.items():
                        if 'timestamp' in value:
                            if now - value['timestamp'] < self._cache_duration:
                                self._cache[key] = value
                cprint(f"📦 Loaded {len(self._cache)} cached FRED entries", "cyan")
        except Exception as e:
            cprint(f"⚠️ Could not load FRED cache: {str(e)}", "yellow")
    
    def _save_cache_to_disk(self):
        """Save cache to disk"""
        try:
            cache_file = self._cache_dir / "fred_cache.json"
            with open(cache_file, 'w') as f:
                json.dump(self._cache, f)
        except Exception as e:
            cprint(f"⚠️ Could not save FRED cache: {str(e)}", "yellow")
    
    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """Get data from cache if valid"""
        if key in self._cache:
            cache_entry = self._cache[key]
            if time.time() - cache_entry['timestamp'] < self._cache_duration:
                return cache_entry['data']
        return None
    
    def _save_to_cache(self, key: str, data: Dict):
        """Save data to cache"""
        self._cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
        self._save_cache_to_disk()
    
    def get_series_data(self, series_id: str, limit: int = 12) -> Optional[List[Dict]]:
        """Get time series data from FRED"""
        cache_key = f"series_{series_id}_{limit}"
        
        # Check cache first
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        if not self.api_key:
            cprint(f"⚠️ No FRED API key - using cached data for {series_id}", "yellow")
            return None
        
        try:
            params = {
                'series_id': series_id,
                'api_key': self.api_key,
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': limit
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            observations = data.get('observations', [])
            
            # Save to cache
            self._save_to_cache(cache_key, observations)
            
            return observations
            
        except Exception as e:
            cprint(f"⚠️ FRED API error for {series_id}: {str(e)}", "yellow")
            return None
    
    def get_latest_value(self, series_id: str) -> Optional[float]:
        """Get the latest value for a series"""
        data = self.get_series_data(series_id, limit=1)
        if data and len(data) > 0:
            try:
                return float(data[0]['value'])
            except (ValueError, KeyError):
                return None
        return None
    
    def calculate_trend(self, series_id: str, periods: int = 2) -> Optional[float]:
        """Calculate trend (percentage change) over periods"""
        data = self.get_series_data(series_id, limit=periods)
        if data and len(data) >= periods:
            try:
                latest = float(data[0]['value'])
                previous = float(data[periods-1]['value'])
                if previous != 0:
                    return ((latest - previous) / previous) * 100
            except (ValueError, KeyError, ZeroDivisionError):
                pass
        return None
    
    def calculate_cpi_inflation(self) -> Optional[float]:
        """Calculate CPI as year-over-year inflation rate (not raw index)"""
        data = self.get_series_data('CPIAUCSL', limit=13)  # Need 13 months for YoY
        if data and len(data) >= 13:
            try:
                latest_cpi = float(data[0]['value'])
                year_ago_cpi = float(data[12]['value'])  # 12 months ago
                if year_ago_cpi != 0:
                    inflation_rate = ((latest_cpi - year_ago_cpi) / year_ago_cpi) * 100
                    return inflation_rate
            except (ValueError, KeyError, ZeroDivisionError):
                pass
        return None
    
    def get_all_macro_indicators(self) -> Dict:
        """Get all macro indicators with trending data"""
        indicators = {}
        
        for name, series_id in self.SERIES_IDS.items():
            # Skip duplicates
            if name == 'cpi_yoy':
                continue
                
            latest = self.get_latest_value(series_id)
            trend_mom = self.calculate_trend(series_id, periods=2)  # Month-over-month
            trend_qoq = self.calculate_trend(series_id, periods=4)  # Quarter-over-quarter
            
            # Special handling for CPI - convert to inflation rate
            if name == 'cpi':
                inflation_rate = self.calculate_cpi_inflation()
                if inflation_rate is not None:
                    latest = inflation_rate
                    # Recalculate trends for inflation rate
                    trend_mom = self.calculate_trend(series_id, periods=2)
            
            # Use MoM trend as primary 'trend' value for UI display
            primary_trend = trend_mom if trend_mom is not None else 0
            
            indicators[name] = {
                'value': latest if latest is not None else 0,
                'trend': primary_trend,  # Primary trend for UI (month-over-month)
                'trend_mom': trend_mom if trend_mom is not None else 0,  # Month-over-month
                'trend_qoq': trend_qoq if trend_qoq is not None else 0,  # Quarter-over-quarter
                'series_id': series_id
            }
        
        # Calculate yield curve (10Y - 2Y spread)
        if indicators['yield_10y']['value'] and indicators['yield_2y']['value']:
            spread_value = indicators['yield_10y']['value'] - indicators['yield_2y']['value']
            # Calculate trend for yield curve spread
            spread_trend = indicators['yield_10y'].get('trend', 0) - indicators['yield_2y'].get('trend', 0)
            indicators['yield_curve'] = {
                'value': spread_value,
                'trend': spread_trend,
                'trend_mom': spread_trend,
                'trend_qoq': 0,
                'series_id': 'YIELD_CURVE'
            }
        
        return indicators
    
    def get_economic_cycle_indicators(self) -> Dict:
        """Get indicators formatted for economic cycle detection"""
        all_indicators = self.get_all_macro_indicators()
        
        return {
            'gdp': {
                'value': all_indicators['gdp']['value'],
                'trend': all_indicators['gdp']['trend_qoq']
            },
            'unemployment': {
                'value': all_indicators['unemployment']['value'],
                'trend': all_indicators['unemployment']['trend_mom']
            },
            'cpi': {
                'value': all_indicators['cpi']['value'],
                'trend': all_indicators['cpi']['trend_mom']
            },
            'fed_rate': {
                'value': all_indicators['fed_rate']['value'],
                'trend': all_indicators['fed_rate']['trend_mom']
            },
            'pmi': {
                'value': all_indicators['pmi']['value'] if all_indicators['pmi']['value'] else 50,
                'trend': all_indicators['pmi']['trend_mom']
            },
            'consumer_confidence': {
                'value': all_indicators['consumer_confidence']['value'],
                'trend': all_indicators['consumer_confidence']['trend_mom']
            },
            'vix': {
                'value': all_indicators['vix']['value'],
                'trend': all_indicators['vix']['trend_mom']
            },
            'yield_curve': {
                'value': all_indicators.get('yield_curve', {}).get('value', 0),
                'trend': 0
            }
        }


if __name__ == "__main__":
    # Test the provider
    provider = FREDProvider()
    indicators = provider.get_all_macro_indicators()
    
    print("\n🌙 FRED Macro Indicators:")
    for name, data in indicators.items():
        print(f"\n{name.upper()}:")
        print(f"  Value: {data['value']}")
        print(f"  MoM Trend: {data['trend_mom']:.2f}%")
        print(f"  QoQ Trend: {data['trend_qoq']:.2f}%")
