#!/usr/bin/env python3
"""
🌙 Moon Dev's Free Market Data Provider
100% free market data using CoinGecko (crypto) and yfinance (stocks)
Built with love by Moon Dev 🚀
"""

import requests
from typing import Dict
from termcolor import cprint
import time
from datetime import datetime, timedelta

class FreeMarketDataProvider:
    """Provider for free market data - no API key required"""
    
    def __init__(self):
        """Initialize free market data provider"""
        self._cache = {}  # Cache for rate limiting
        self._cache_duration = 60  # Cache for 60 seconds
        cprint("✅ Free market data provider initialized (with caching)", "green")
    
    def get_crypto_price(self, symbol: str) -> Dict:
        """
        Get crypto price from CoinGecko (100% free, no API key)
        With caching to avoid rate limits
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH', 'SOL')
            
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
                'UNI': 'uniswap'
            }
            
            coin_id = symbol_map.get(symbol.upper(), 'bitcoin')
            
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true'
            }
            
            # Add delay to respect rate limits
            time.sleep(0.5)
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if coin_id in data:
                price = data[coin_id].get('usd', 0)
                change = data[coin_id].get('usd_24h_change', 0)
                
                result = {
                    'price': price,
                    'change': change
                }
                
                # Cache the result
                self._cache[cache_key] = (result, time.time())
                return result
            
            return {'price': 0, 'change': 0}
            
        except Exception as e:
            # Return cached data if available, even if expired
            if cache_key in self._cache:
                cached_data, _ = self._cache[cache_key]
                cprint(f"⚠️ Using cached data for {symbol} due to API error", "yellow")
                return cached_data
            
            cprint(f"⚠️ CoinGecko error for {symbol}: {str(e)[:80]}", "yellow")
            return {'price': 0, 'change': 0}
    
    def get_stock_price(self, symbol: str) -> Dict:
        """
        Get stock price using yfinance (free, no API key)
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'QQQ', 'SPY')
            
        Returns:
            Dict with price and change
        """
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get current price
            price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            
            # Get previous close
            prev_close = info.get('previousClose', 0)
            
            # Calculate change
            change = 0
            if prev_close and prev_close > 0 and price > 0:
                change = ((price - prev_close) / prev_close) * 100
            
            return {
                'price': price,
                'change': change
            }
            
        except ImportError:
            cprint("⚠️ yfinance not installed. Install: pip install yfinance", "yellow")
            return {'price': 0, 'change': 0}
        except Exception as e:
            cprint(f"⚠️ yfinance error for {symbol}: {str(e)[:80]}", "yellow")
            return {'price': 0, 'change': 0}
    
    def get_quote(self, symbol: str, asset_type: str = "stocks") -> Dict:
        """
        Get quote for any symbol
        
        Args:
            symbol: Ticker symbol
            asset_type: 'stocks' or 'crypto'
            
        Returns:
            Dict with price and change
        """
        if asset_type == "crypto":
            return self.get_crypto_price(symbol)
        else:
            return self.get_stock_price(symbol)
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100):
        """
        Get OHLCV (Open, High, Low, Close, Volume) data for charting
        
        Args:
            symbol: Ticker symbol (e.g., 'BTC', 'AAPL')
            timeframe: Timeframe ('15m', '1h', '4h', '1d')
            limit: Number of candles to fetch
            
        Returns:
            pandas DataFrame with OHLCV data or None if failed
        """
        try:
            import yfinance as yf
            import pandas as pd
            
            # Map timeframes to yfinance intervals
            interval_map = {
                '1m': '1m',
                '5m': '5m',
                '15m': '15m',
                '30m': '30m',
                '1h': '1h',
                '4h': '1h',  # yfinance doesn't have 4h, use 1h
                '1d': '1d',
                '1w': '1wk'
            }
            
            # Map timeframes to periods
            period_map = {
                '1m': '1d',
                '5m': '5d',
                '15m': '5d',
                '30m': '1mo',
                '1h': '1mo',
                '4h': '3mo',
                '1d': '1y',
                '1w': '2y'
            }
            
            interval = interval_map.get(timeframe, '1h')
            period = period_map.get(timeframe, '1mo')
            
            # Determine if crypto or stock
            is_crypto = symbol.upper() in ['BTC', 'ETH', 'SOL', 'DOGE', 'ADA', 'DOT', 'MATIC', 'AVAX', 'LINK', 'UNI', 'XRP']
            
            # Add -USD suffix for crypto
            ticker_symbol = f"{symbol}-USD" if is_crypto else symbol
            
            # Fetch data
            ticker = yf.Ticker(ticker_symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                cprint(f"⚠️ No OHLCV data for {symbol}", "yellow")
                return None
            
            # Rename columns to lowercase for consistency
            df.columns = [col.lower() for col in df.columns]
            
            # Ensure we have the required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                cprint(f"⚠️ Missing required columns for {symbol}", "yellow")
                return None
            
            # Limit to requested number of candles
            df = df.tail(limit)
            
            # For 4h timeframe, resample 1h data
            if timeframe == '4h':
                df = df.resample('4H').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
            
            cprint(f"✅ Fetched {len(df)} candles for {symbol} ({timeframe})", "green")
            return df
            
        except ImportError:
            cprint("⚠️ yfinance not installed. Install: pip install yfinance", "yellow")
            return None
        except Exception as e:
            cprint(f"⚠️ Error fetching OHLCV for {symbol}: {str(e)[:80]}", "yellow")
            return None


if __name__ == "__main__":
    """Test the free market data provider"""
    print("\n🧪 Testing Free Market Data Provider\n")
    
    provider = FreeMarketDataProvider()
    
    # Test crypto
    print("🪙 Testing Crypto (CoinGecko):")
    btc = provider.get_crypto_price('BTC')
    print(f"  BTC: ${btc['price']:,.2f} ({btc['change']:+.2f}%)")
    
    eth = provider.get_crypto_price('ETH')
    print(f"  ETH: ${eth['price']:,.2f} ({eth['change']:+.2f}%)\n")
    
    # Test stocks
    print("📊 Testing Stocks (yfinance):")
    qqq = provider.get_stock_price('QQQ')
    print(f"  QQQ: ${qqq['price']:.2f} ({qqq['change']:+.2f}%)")
    
    spy = provider.get_stock_price('SPY')
    print(f"  SPY: ${spy['price']:.2f} ({spy['change']:+.2f}%)")
    
    print("\n✅ All tests complete!")
