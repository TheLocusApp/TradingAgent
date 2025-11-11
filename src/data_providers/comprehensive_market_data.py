#!/usr/bin/env python3
"""
🌙 Moon Dev's Comprehensive Market Data Provider
Provides detailed technical indicators matching nof1.ai experiment
Built with love by Moon Dev 🚀
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List
from termcolor import cprint
from datetime import datetime, timedelta
import time

class ComprehensiveMarketDataProvider:
    """Provider for comprehensive market data with full technical indicators"""
    
    def __init__(self):
        """Initialize comprehensive market data provider"""
        self._cache = {}
        self._cache_duration = 180  # 3 minutes cache
        cprint("✅ Comprehensive market data provider initialized", "green")
    
    def get_comprehensive_data(self, symbol: str, timeframe: str = '1m') -> Dict:
        """
        Get comprehensive market data matching nof1.ai format
        
        Args:
            symbol: Asset symbol (e.g., 'BTC-USD', 'SPY', 'QQQ')
            timeframe: Timeframe for analysis ('1m', '5m', '15m', '1h', '4h')
            
        Returns:
            Dict with comprehensive market data
        """
        cache_key = f"{symbol}_{timeframe}"
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self._cache_duration:
                return cached_data
        
        try:
            # Get intraday data (1m or 5m)
            intraday_data = self._get_intraday_data(symbol, timeframe)
            
            # Get 4-hour context data
            context_data = self._get_context_data(symbol)
            
            # Get open interest and funding (for crypto)
            oi_funding = self._get_oi_and_funding(symbol)
            
            # Combine all data
            result = {
                **intraday_data,
                **context_data,
                **oi_funding,
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache result
            self._cache[cache_key] = (result, time.time())
            return result
            
        except Exception as e:
            cprint(f"⚠️ Error getting comprehensive data for {symbol}: {e}", "yellow")
            return self._get_fallback_data(symbol)
    
    def _get_intraday_data(self, symbol: str, timeframe: str) -> Dict:
        """Get intraday technical indicators"""
        try:
            # Convert symbol format (BTC -> BTC-USD)
            if symbol in ['BTC', 'ETH', 'SOL']:
                ticker_symbol = f"{symbol}-USD"
            else:
                ticker_symbol = symbol
            
            # Get data
            ticker = yf.Ticker(ticker_symbol)
            
            # Map unsupported intervals to supported ones
            # yfinance supported: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
            interval_map = {
                '3m': '5m',  # Map 3m to 5m (closest supported)
                '4m': '5m',
                '6m': '5m',
                '10m': '15m',
                '20m': '15m',
                '3h': '1h',
                '2h': '1h'
            }
            
            interval = interval_map.get(timeframe, timeframe)
            
            # Get intraday data with proper period limits per yfinance documentation
            # 1m: max 7 days, 2m: max 60 days, 5m+: max 60 days
            # Note: Crypto tickers sometimes fail with 60d, use 30d for safety
            if interval == '1m':
                period = '5d'  # Use 5 days for 1m to be safe
            elif interval == '2m':
                period = '30d'  # Use 30 days for 2m
            else:
                # Use 30d for crypto, 60d for stocks
                if symbol in ['BTC', 'ETH', 'SOL', 'DOGE', 'XRP', 'BNB', 'ADA', 'DOT', 'MATIC', 'AVAX', 'LINK']:
                    period = '30d'  # Crypto: use 30 days
                else:
                    period = '60d'  # Stocks: use 60 days
            
            try:
                df = ticker.history(period=period, interval=interval)
            except Exception as e:
                cprint(f"⚠️ yfinance error for {ticker_symbol} with {interval}: {e}", "yellow")
                # Fallback to daily data if intraday fails
                df = ticker.history(period='1y', interval='1d')
            
            if df.empty:
                return self._get_fallback_intraday()
            
            # Calculate indicators
            df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
            df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
            
            # MACD
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            
            # RSI (7 and 14 period)
            df['RSI7'] = self._calculate_rsi(df['Close'], 7)
            df['RSI14'] = self._calculate_rsi(df['Close'], 14)
            
            # Get last 10 data points
            recent = df.tail(10)
            
            return {
                'current_price': float(df['Close'].iloc[-1]),
                'current_ema20': float(df['EMA20'].iloc[-1]),
                'current_ema50': float(df['EMA50'].iloc[-1]) if len(df) >= 50 else float(df['EMA20'].iloc[-1]),
                'current_macd': float(df['MACD'].iloc[-1]),
                'current_rsi7': float(df['RSI7'].iloc[-1]),
                'current_rsi14': float(df['RSI14'].iloc[-1]),
                
                # Series data (last 10 points)
                'mid_prices': recent['Close'].tolist(),
                'ema20_series': recent['EMA20'].tolist(),
                'macd_series': recent['MACD'].tolist(),
                'rsi7_series': recent['RSI7'].tolist(),
                'rsi14_series': recent['RSI14'].tolist(),
                'volume_series': recent['Volume'].tolist(),
            }
            
        except Exception as e:
            cprint(f"⚠️ Intraday data error: {e}", "yellow")
            return self._get_fallback_intraday()
    
    def _get_context_data(self, symbol: str) -> Dict:
        """Get 4-hour timeframe context"""
        try:
            # Convert symbol format
            if symbol in ['BTC', 'ETH', 'SOL']:
                ticker_symbol = f"{symbol}-USD"
            else:
                ticker_symbol = symbol
            
            ticker = yf.Ticker(ticker_symbol)
            # Use 30d for crypto, 60d for stocks
            if symbol in ['BTC', 'ETH', 'SOL', 'DOGE', 'XRP', 'BNB', 'ADA', 'DOT', 'MATIC', 'AVAX', 'LINK']:
                period = '30d'
            else:
                period = '60d'
            df = ticker.history(period=period, interval='4h')
            
            if df.empty:
                return self._get_fallback_context()
            
            # Calculate indicators
            df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
            df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
            
            # ATR (Average True Range)
            df['TR'] = np.maximum(
                df['High'] - df['Low'],
                np.maximum(
                    abs(df['High'] - df['Close'].shift()),
                    abs(df['Low'] - df['Close'].shift())
                )
            )
            df['ATR3'] = df['TR'].rolling(window=3).mean()
            df['ATR14'] = df['TR'].rolling(window=14).mean()
            
            # MACD
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            
            # RSI
            df['RSI14'] = self._calculate_rsi(df['Close'], 14)
            
            # Volume average
            avg_volume = df['Volume'].mean()
            
            recent = df.tail(10)
            
            return {
                'context_ema20': float(df['EMA20'].iloc[-1]),
                'context_ema50': float(df['EMA50'].iloc[-1]) if len(df) >= 50 else float(df['EMA20'].iloc[-1]),
                'context_atr3': float(df['ATR3'].iloc[-1]),
                'context_atr14': float(df['ATR14'].iloc[-1]),
                'context_volume': float(df['Volume'].iloc[-1]),
                'context_avg_volume': float(avg_volume),
                'context_macd_series': recent['MACD'].tolist(),
                'context_rsi14_series': recent['RSI14'].tolist(),
            }
            
        except Exception as e:
            cprint(f"⚠️ Context data error: {e}", "yellow")
            return self._get_fallback_context()
    
    def _get_oi_and_funding(self, symbol: str) -> Dict:
        """Get open interest and funding rate (for crypto)"""
        # This would integrate with Hyperliquid/Binance APIs
        # For now, return placeholder
        if symbol in ['BTC', 'ETH', 'SOL']:
            return {
                'open_interest_latest': 0,
                'open_interest_avg': 0,
                'funding_rate': 0,
                'has_oi_data': False
            }
        else:
            return {
                'open_interest_latest': 0,
                'open_interest_avg': 0,
                'funding_rate': 0,
                'has_oi_data': False
            }
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _get_fallback_intraday(self) -> Dict:
        """Fallback intraday data"""
        return {
            'current_price': 0,
            'current_ema20': 0,
            'current_ema50': 0,
            'current_macd': 0,
            'current_rsi7': 50,
            'current_rsi14': 50,
            'mid_prices': [],
            'ema20_series': [],
            'macd_series': [],
            'rsi7_series': [],
            'rsi14_series': [],
            'volume_series': [],
        }
    
    def _get_fallback_context(self) -> Dict:
        """Fallback context data"""
        return {
            'context_ema20': 0,
            'context_ema50': 0,
            'context_atr3': 0,
            'context_atr14': 0,
            'context_volume': 0,
            'context_avg_volume': 0,
            'context_macd_series': [],
            'context_rsi14_series': [],
        }
    
    def _get_fallback_data(self, symbol: str) -> Dict:
        """Complete fallback data"""
        return {
            **self._get_fallback_intraday(),
            **self._get_fallback_context(),
            'open_interest_latest': 0,
            'open_interest_avg': 0,
            'funding_rate': 0,
            'has_oi_data': False,
            'symbol': symbol,
            'timeframe': '1m',
            'timestamp': datetime.now().isoformat()
        }
