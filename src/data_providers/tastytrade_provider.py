#!/usr/bin/env python3
"""
🌙 Moon Dev's Tastytrade Market Data Provider
Streams real-time stock market data from Tastytrade API
Built with love by Moon Dev 🚀
"""

import os
import requests
import json
from typing import Dict, Optional, List
from datetime import datetime
from termcolor import cprint
from dotenv import load_dotenv

class TastytradeProvider:
    """Provider for Tastytrade stock market data"""
    
    BASE_URL = "https://api.tastytrade.com"
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize Tastytrade provider
        
        Args:
            username: Tastytrade username (or from env TASTYTRADE_USERNAME)
            password: Tastytrade password (or from env TASTYTRADE_PASSWORD)
        """
        load_dotenv()
        
        self.username = username or os.getenv("TASTYTRADE_USERNAME")
        self.password = password or os.getenv("TASTYTRADE_PASSWORD")
        self.account_number = os.getenv("TASTYTRADE_ACCOUNT_NUMBER")
        
        if not self.username or not self.password:
            raise ValueError("❌ TASTYTRADE_USERNAME and TASTYTRADE_PASSWORD required in .env")
        
        self.session_token = None
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        cprint("🔐 Initializing Tastytrade connection...", "cyan")
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Tastytrade API"""
        try:
            url = f"{self.BASE_URL}/sessions"
            payload = {
                "login": self.username,
                "password": self.password
            }
            
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            self.session_token = data['data']['session-token']
            self.headers['Authorization'] = self.session_token
            
            cprint(f"✅ Authenticated with Tastytrade", "green")
            
        except Exception as e:
            cprint(f"❌ Failed to authenticate with Tastytrade: {e}", "red")
            raise
    
    def get_quote(self, symbol: str) -> Dict:
        """
        Get current quote for a symbol
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'TSLA')
            
        Returns:
            Quote data dictionary
        """
        try:
            url = f"{self.BASE_URL}/market-data/quotes/{symbol}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            return data['data']
            
        except Exception as e:
            cprint(f"❌ Failed to get quote for {symbol}: {e}", "red")
            return {}
    
    def get_candles(self, symbol: str, interval: str = "3m", limit: int = 10) -> List[Dict]:
        """
        Get historical candles for a symbol
        
        Args:
            symbol: Stock symbol
            interval: Candle interval (1m, 3m, 5m, 15m, 30m, 1h, 4h, 1d)
            limit: Number of candles to fetch
            
        Returns:
            List of candle data
        """
        try:
            # Tastytrade uses different endpoint for candles
            url = f"{self.BASE_URL}/market-data/candles/{symbol}"
            params = {
                "interval": interval,
                "limit": limit
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', [])
            
        except Exception as e:
            cprint(f"⚠️ Failed to get candles for {symbol}: {e}", "yellow")
            return []
    
    def get_market_state(self, symbol: str) -> Dict:
        """
        Get comprehensive market state for trading agent
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Market state dictionary compatible with trading agent
        """
        try:
            # Get current quote
            quote = self.get_quote(symbol)
            
            if not quote:
                cprint(f"⚠️ No quote data for {symbol}", "yellow")
                return self._get_fallback_state(symbol)
            
            # Get candles for technical indicators
            candles = self.get_candles(symbol, interval="3m", limit=20)
            
            # Extract current price
            current_price = quote.get('last', 0)
            bid = quote.get('bid', current_price)
            ask = quote.get('ask', current_price)
            mid_price = (bid + ask) / 2
            
            # Calculate simple indicators from candles
            prices = [c.get('close', 0) for c in candles if c.get('close')]
            volumes = [c.get('volume', 0) for c in candles if c.get('volume')]
            
            # Simple EMA calculation (20-period)
            ema_20 = self._calculate_ema(prices, 20) if len(prices) >= 20 else current_price
            
            # Build market state
            market_state = {
                'symbol': symbol,
                'asset_type': 'stock',
                'current_price': current_price,
                'bid': bid,
                'ask': ask,
                'mid_price': mid_price,
                'current_ema20': ema_20,
                'current_macd': 0,  # Simplified - would need more data
                'current_rsi_7': 50,  # Simplified - would need more data
                'volume_current': volumes[-1] if volumes else 0,
                'volume_avg': sum(volumes) / len(volumes) if volumes else 0,
                'mid_prices': prices[-10:] if len(prices) >= 10 else prices,
                'ema_20': [ema_20] * 10,  # Simplified
                'current_time': datetime.now().isoformat(),
                'quote_time': quote.get('quote-time', ''),
                'market_session': 'regular' if quote.get('is-regular-hours') else 'extended',
            }
            
            return market_state
            
        except Exception as e:
            cprint(f"❌ Error getting market state for {symbol}: {e}", "red")
            return self._get_fallback_state(symbol)
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return sum(prices) / len(prices) if prices else 0
        
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def _get_fallback_state(self, symbol: str) -> Dict:
        """Return fallback market state when API fails"""
        return {
            'symbol': symbol,
            'asset_type': 'stock',
            'current_price': 0,
            'bid': 0,
            'ask': 0,
            'mid_price': 0,
            'current_ema20': 0,
            'current_macd': 0,
            'current_rsi_7': 50,
            'volume_current': 0,
            'volume_avg': 0,
            'mid_prices': [],
            'ema_20': [],
            'current_time': datetime.now().isoformat(),
            'error': 'Failed to fetch market data'
        }
    
    def close(self):
        """Close the session"""
        if self.session_token:
            try:
                url = f"{self.BASE_URL}/sessions"
                requests.delete(url, headers=self.headers)
                cprint("👋 Tastytrade session closed", "yellow")
            except:
                pass


if __name__ == "__main__":
    # Test the provider
    try:
        provider = TastytradeProvider()
        
        # Test with a popular stock
        symbol = "AAPL"
        cprint(f"\n📊 Testing market data for {symbol}...", "cyan")
        
        market_state = provider.get_market_state(symbol)
        
        cprint(f"\n✅ Market State for {symbol}:", "green")
        cprint(f"   Price: ${market_state.get('current_price', 0):.2f}", "white")
        cprint(f"   Bid/Ask: ${market_state.get('bid', 0):.2f} / ${market_state.get('ask', 0):.2f}", "white")
        cprint(f"   EMA(20): ${market_state.get('current_ema20', 0):.2f}", "white")
        cprint(f"   Session: {market_state.get('market_session', 'unknown')}", "white")
        
        provider.close()
        
    except Exception as e:
        cprint(f"\n❌ Test failed: {e}", "red")
