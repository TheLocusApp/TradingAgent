#!/usr/bin/env python3
"""
🌙 Moon Dev's Enhanced Market Data Provider
Multi-source data fetching with automatic fallbacks
Built with love by Moon Dev 🚀

Data Source Priority:
1. yfinance (free, unlimited)
2. Alpha Vantage (free tier: 25 requests/day)
3. Polygon.io (free tier: 5 requests/minute)
"""

import os
import requests
import time
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from termcolor import cprint
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

class EnhancedMarketDataProvider:
    """Multi-source market data provider with automatic fallbacks"""
    
    def __init__(self):
        """Initialize enhanced market data provider"""
        self._cache = {}
        self._cache_duration = 60  # Cache for 60 seconds
        self._request_counts = {
            'alpha_vantage': {'count': 0, 'reset_time': time.time()},
            'polygon': {'count': 0, 'reset_time': time.time()}
        }
        
        # API Keys (optional - will use free tier if not provided)
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self.polygon_key = os.getenv('POLYGON_API_KEY', '')
        
        cprint("✅ Enhanced market data provider initialized with fallbacks", "green")
    
    def _check_rate_limit(self, source: str) -> bool:
        """Check if we're within rate limits for a data source"""
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
    
    def get_stock_price_yfinance(self, symbol: str) -> Optional[Dict]:
        """
        Primary: Get stock price using yfinance
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'SQ')
            
        Returns:
            Dict with price and change, or None if failed
        """
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='5d')
            
            if hist.empty or len(hist) < 2:
                return None
            
            current_price = float(hist['Close'].iloc[-1])
            prev_price = float(hist['Close'].iloc[-2])
            change_pct = ((current_price - prev_price) / prev_price) * 100
            
            return {
                'price': current_price,
                'change': change_pct,
                'volume': float(hist['Volume'].iloc[-1]),
                'source': 'yfinance'
            }
            
        except Exception as e:
            cprint(f"⚠️ yfinance failed for {symbol}: {str(e)[:50]}", "yellow")
            return None
    
    def get_stock_price_alpha_vantage(self, symbol: str) -> Optional[Dict]:
        """
        Fallback 1: Get stock price using Alpha Vantage
        Free tier: 25 requests per day
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict with price and change, or None if failed
        """
        if not self._check_rate_limit('alpha_vantage'):
            cprint(f"⚠️ Alpha Vantage rate limit reached (25/day)", "yellow")
            return None
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            self._increment_rate_limit('alpha_vantage')
            
            if 'Global Quote' in data and data['Global Quote']:
                quote = data['Global Quote']
                price = float(quote.get('05. price', 0))
                change_pct = float(quote.get('10. change percent', '0').replace('%', ''))
                volume = float(quote.get('06. volume', 0))
                
                if price > 0:
                    return {
                        'price': price,
                        'change': change_pct,
                        'volume': volume,
                        'source': 'alpha_vantage'
                    }
            
            return None
            
        except Exception as e:
            cprint(f"⚠️ Alpha Vantage failed for {symbol}: {str(e)[:50]}", "yellow")
            return None
    
    def get_stock_price_polygon(self, symbol: str) -> Optional[Dict]:
        """
        Fallback 2: Get stock price using Polygon.io
        Free tier: 5 requests per minute
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict with price and change, or None if failed
        """
        if not self.polygon_key:
            return None
        
        if not self._check_rate_limit('polygon'):
            cprint(f"⚠️ Polygon rate limit reached (5/min)", "yellow")
            return None
        
        try:
            # Get previous close
            prev_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            url = f"https://api.polygon.io/v1/open-close/{symbol}/{prev_date}"
            params = {'apiKey': self.polygon_key}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            self._increment_rate_limit('polygon')
            
            if data.get('status') == 'OK':
                prev_close = float(data.get('close', 0))
                
                # Get current price from snapshot
                snapshot_url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"
                snapshot_response = requests.get(snapshot_url, params=params, timeout=10)
                snapshot_data = snapshot_response.json()
                
                if snapshot_data.get('status') == 'OK' and 'ticker' in snapshot_data:
                    ticker_data = snapshot_data['ticker']
                    current_price = float(ticker_data.get('lastTrade', {}).get('p', 0))
                    volume = float(ticker_data.get('day', {}).get('v', 0))
                    
                    if current_price > 0 and prev_close > 0:
                        change_pct = ((current_price - prev_close) / prev_close) * 100
                        return {
                            'price': current_price,
                            'change': change_pct,
                            'volume': volume,
                            'source': 'polygon'
                        }
            
            return None
            
        except Exception as e:
            cprint(f"⚠️ Polygon failed for {symbol}: {str(e)[:50]}", "yellow")
            return None
    
    def get_stock_price(self, symbol: str) -> Dict:
        """
        Get stock price with automatic fallback chain
        
        Priority:
        1. yfinance (free, unlimited)
        2. Alpha Vantage (25/day)
        3. Polygon.io (5/min)
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict with price and change
        """
        # Check cache first
        cache_key = f"stock_{symbol}"
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self._cache_duration:
                return cached_data
        
        # Try each source in order
        sources = [
            ('yfinance', self.get_stock_price_yfinance),
            ('alpha_vantage', self.get_stock_price_alpha_vantage),
            ('polygon', self.get_stock_price_polygon)
        ]
        
        for source_name, source_func in sources:
            result = source_func(symbol)
            if result:
                cprint(f"✅ {symbol} data from {source_name}", "green")
                # Cache the result
                self._cache[cache_key] = (result, time.time())
                return result
        
        # All sources failed
        cprint(f"❌ All data sources failed for {symbol}", "red")
        return {'price': 0, 'change': 0, 'volume': 0, 'source': 'none'}
    
    def get_crypto_price(self, symbol: str) -> Dict:
        """
        Get crypto price from CoinGecko (free, no API key required)
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Dict with price and change
        """
        # Check cache first
        cache_key = f"crypto_{symbol}"
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self._cache_duration:
                return cached_data
        
        try:
            # Map symbols to CoinGecko IDs
            symbol_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'SOL': 'solana',
                'DOGE': 'dogecoin',
                'ADA': 'cardano',
                'DOT': 'polkadot',
                'MATIC': 'matic-network',
                'AVAX': 'avalanche-2',
                'LINK': 'chainlink',
                'UNI': 'uniswap',
                'XRP': 'ripple'
            }
            
            coin_id = symbol_map.get(symbol.upper(), 'bitcoin')
            
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true'
            }
            
            time.sleep(0.5)  # Respect rate limits
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if coin_id in data:
                price = data[coin_id].get('usd', 0)
                change = data[coin_id].get('usd_24h_change', 0)
                
                result = {
                    'price': price,
                    'change': change,
                    'volume': 0,  # CoinGecko free tier doesn't include volume in this endpoint
                    'source': 'coingecko'
                }
                
                # Cache the result
                self._cache[cache_key] = (result, time.time())
                return result
            
            return {'price': 0, 'change': 0, 'volume': 0, 'source': 'none'}
            
        except Exception as e:
            # Return cached data if available
            if cache_key in self._cache:
                cached_data, _ = self._cache[cache_key]
                cprint(f"⚠️ Using cached data for {symbol}", "yellow")
                return cached_data
            
            cprint(f"❌ CoinGecko failed for {symbol}: {str(e)[:50]}", "red")
            return {'price': 0, 'change': 0, 'volume': 0, 'source': 'none'}
    
    def get_quote(self, symbol: str, asset_type: str = "stocks") -> Dict:
        """
        Get quote for any symbol with automatic fallbacks
        
        Args:
            symbol: Ticker symbol
            asset_type: 'stocks' or 'crypto'
            
        Returns:
            Dict with price, change, volume, and source
        """
        if asset_type == "crypto":
            return self.get_crypto_price(symbol)
        else:
            return self.get_stock_price(symbol)


if __name__ == "__main__":
    """Test the enhanced market data provider"""
    print("\n🧪 Testing Enhanced Market Data Provider\n")
    
    provider = EnhancedMarketDataProvider()
    
    # Test stocks with fallbacks
    print("📊 Testing Stocks (with fallbacks):")
    test_symbols = ['AAPL', 'SQ', 'MATIC']  # SQ might be delisted
    
    for symbol in test_symbols:
        data = provider.get_stock_price(symbol)
        if data['price'] > 0:
            print(f"  {symbol}: ${data['price']:.2f} ({data['change']:+.2f}%) [source: {data['source']}]")
        else:
            print(f"  {symbol}: No data available")
    
    print("\n🪙 Testing Crypto:")
    btc = provider.get_crypto_price('BTC')
    print(f"  BTC: ${btc['price']:,.2f} ({btc['change']:+.2f}%) [source: {btc['source']}]")
    
    eth = provider.get_crypto_price('ETH')
    print(f"  ETH: ${eth['price']:,.2f} ({eth['change']:+.2f}%) [source: {eth['source']}]")
    
    print("\n✅ All tests complete!")
