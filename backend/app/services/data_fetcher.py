"""
Data fetching service for stock market data using yfinance
Supports real-time and historical data with caching
With fallback to mock data for serverless environments
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from app.utils.logger import logger
import time
import os
import random
import numpy as np


class DataFetcher:
    """Service for fetching stock data from yfinance with mock data fallback"""
    
    # Class-level cache for better memory management
    _shared_cache: Dict[str, Dict[str, Any]] = {}
    
    # Base prices for mock data generation (approximate real prices in TRY)
    MOCK_BASE_PRICES = {
        "AKBNK.IS": 52.0,
        "AKSEN.IS": 28.0,
        "ARCLK.IS": 180.0,
        "ASELS.IS": 95.0,
        "BIMAS.IS": 520.0,
        "EKGYO.IS": 12.0,
        "ENKAI.IS": 85.0,
        "EREGL.IS": 58.0,
        "FROTO.IS": 1250.0,
        "GARAN.IS": 125.0,
        "GUBRF.IS": 185.0,
        "HEKTS.IS": 95.0,
        "ISCTR.IS": 18.0,
        "KCHOL.IS": 245.0,
        "KRDMD.IS": 32.0,
        "ODAS.IS": 8.5,
        "PETKM.IS": 22.0,
        "PGSUS.IS": 980.0,
        "SAHOL.IS": 78.0,
        "SASA.IS": 65.0,
        "SISE.IS": 52.0,
        "TAVHL.IS": 145.0,
        "TCELL.IS": 95.0,
        "THYAO.IS": 320.0,
        "TKFEN.IS": 185.0,
        "TOASO.IS": 380.0,
        "TRALT.IS": 42.0,
        "TUPRS.IS": 185.0,
        "YKBNK.IS": 32.0,
    }
    
    def __init__(self):
        """Initialize the data fetcher"""
        self.cache = DataFetcher._shared_cache  # Use shared cache
        self.cache_ttl: int = 300  # 5 minutes - prevents Yahoo Finance rate limiting
        self.use_mock_data = os.getenv("VERCEL") == "1"  # Use mock data on Vercel
        
        # BIST 30 + Altın hisseleri
        self.bist30_tickers = [
            "AKBNK.IS",   # Akbank
            "AKSEN.IS",   # Aksa Enerji
            "ARCLK.IS",   # Arçelik
            "ASELS.IS",   # Aselsan
            "BIMAS.IS",   # BİM
            "EKGYO.IS",   # Emlak Konut GYO
            "ENKAI.IS",   # Enka İnşaat
            "EREGL.IS",   # Ereğli Demir Çelik
            "FROTO.IS",   # Ford Otosan
            "GARAN.IS",   # Garanti BBVA
            "GUBRF.IS",   # Gübre Fabrikaları
            "HEKTS.IS",   # Hektaş
            "ISCTR.IS",   # İş Bankası C
            "KCHOL.IS",   # Koç Holding
            "KRDMD.IS",   # Kardemir D
            "ODAS.IS",    # Odaş Elektrik
            "PETKM.IS",   # Petkim
            "PGSUS.IS",   # Pegasus
            "SAHOL.IS",   # Sabancı Holding
            "SASA.IS",    # Sasa Polyester
            "SISE.IS",    # Şişecam
            "TAVHL.IS",   # TAV Havalimanları
            "TCELL.IS",   # Turkcell
            "THYAO.IS",   # Türk Hava Yolları
            "TKFEN.IS",   # Tekfen Holding
            "TOASO.IS",   # Tofaş
            "TRALT.IS",   # Türk Altın
            "TUPRS.IS",   # Tüpraş
            "YKBNK.IS",   # Yapı Kredi
        ]
        
        logger.info(f"DataFetcher initialized (mock_data={self.use_mock_data})")
    
    def _generate_mock_data(self, ticker: str, interval: str, period: str) -> pd.DataFrame:
        """
        Generate realistic mock stock data for demo purposes
        
        Args:
            ticker: Stock ticker symbol
            interval: Data interval (1d, 1h, etc.)
            period: Data period (1mo, 3mo, etc.)
        
        Returns:
            DataFrame with mock OHLCV data
        """
        # Get base price for ticker or use default
        base_price = self.MOCK_BASE_PRICES.get(ticker, 100.0)
        
        # Calculate number of data points based on period and interval
        period_days = {
            "1d": 1, "5d": 5, "1mo": 22, "3mo": 66, 
            "6mo": 132, "1y": 252, "2y": 504, "max": 1000
        }
        interval_minutes = {
            "1m": 1, "2m": 2, "5m": 5, "15m": 15, "30m": 30,
            "60m": 60, "90m": 90, "1h": 60, "1d": 1440, "1wk": 10080
        }
        
        days = period_days.get(period, 22)
        interval_min = interval_minutes.get(interval, 60)
        
        # Calculate number of data points (trading hours: 10:00-18:00 = 8 hours)
        if interval_min >= 1440:  # Daily or longer
            num_points = days
        else:
            trading_minutes_per_day = 480  # 8 hours
            points_per_day = trading_minutes_per_day // interval_min
            num_points = min(days * points_per_day, 1000)  # Cap at 1000 points
        
        # Generate timestamps
        end_time = datetime.now()
        if interval_min >= 1440:
            # Daily data - go back by days
            timestamps = [end_time - timedelta(days=i) for i in range(num_points)]
        else:
            # Intraday data
            timestamps = [end_time - timedelta(minutes=i * interval_min) for i in range(num_points)]
        timestamps = timestamps[::-1]  # Oldest first
        
        # Generate realistic price movements using random walk
        np.random.seed(hash(ticker + period) % 2**32)  # Consistent data for same ticker
        
        # Daily volatility (BIST stocks are typically 2-4% daily volatility)
        daily_volatility = 0.025
        if interval_min < 1440:
            # Scale volatility for intraday
            volatility = daily_volatility * np.sqrt(interval_min / 1440)
        else:
            volatility = daily_volatility
        
        # Generate returns with slight positive drift
        returns = np.random.normal(0.0002, volatility, num_points)
        
        # Calculate prices from returns
        price_multipliers = np.exp(np.cumsum(returns))
        close_prices = base_price * price_multipliers
        
        # Generate OHLC from close prices
        data = []
        for i, (ts, close) in enumerate(zip(timestamps, close_prices)):
            # Generate realistic OHLC
            daily_range = close * volatility * 2
            high = close + random.uniform(0, daily_range)
            low = close - random.uniform(0, daily_range)
            open_price = random.uniform(low, high)
            
            # Ensure proper OHLC relationship
            high = max(open_price, close, high)
            low = min(open_price, close, low)
            
            # Generate volume (higher volume for larger stocks)
            base_volume = int(base_price * 10000)
            volume = int(base_volume * random.uniform(0.5, 2.0))
            
            data.append({
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close, 2),
                'volume': volume
            })
        
        df = pd.DataFrame(data, index=pd.DatetimeIndex(timestamps))
        df.index.name = 'Datetime'
        
        logger.info(f"Generated {len(df)} mock data points for {ticker}")
        return df
    
    def validate_ticker(self, ticker: str) -> bool:
        """
        Validate if ticker exists and is tradable
        
        Args:
            ticker: Stock ticker symbol (e.g., "TRALT.IS")
        
        Returns:
            bool: True if ticker is valid
        """
        # On Vercel serverless, skip strict validation - just check format
        import os
        if os.getenv("VERCEL"):
            # Basic format check for BIST tickers
            if ticker.endswith(".IS") and len(ticker) >= 5:
                logger.info(f"Vercel env: Skipping strict validation for {ticker}")
                return True
        
        # Also accept known tickers without API call
        if ticker in self.bist30_tickers:
            logger.info(f"Known ticker: {ticker}")
            return True
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info or 'symbol' not in info:
                logger.warning(f"Invalid ticker: {ticker}")
                return False
            
            logger.info(f"Validated ticker: {ticker}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating ticker {ticker}: {e}")
            # On error, allow if format looks correct
            if ticker.endswith(".IS"):
                return True
            return False
    
    def _get_cache_key(self, ticker: str, interval: str, period: str) -> str:
        """Generate cache key for data"""
        return f"{ticker}_{interval}_{period}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key].get('timestamp', 0)
        current_time = time.time()
        
        return (current_time - cached_time) < self.cache_ttl
    
    def fetch_realtime_data(
        self, 
        ticker: str, 
        interval: str = "5m", 
        period: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch real-time stock data
        
        Args:
            ticker: Stock ticker symbol (e.g., "TRALT.IS")
            interval: Data interval - 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
            period: Data period - 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume, and datetime index
        """
        cache_key = self._get_cache_key(ticker, interval, period)
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            logger.info(f"Returning cached data for {ticker}")
            return self.cache[cache_key]['data'].copy()
        
        df = pd.DataFrame()
        
        # Try yfinance first (unless we know it won't work on Vercel)
        if not self.use_mock_data:
            try:
                logger.info(f"Fetching real-time data for {ticker} (interval={interval}, period={period})")
                
                stock = yf.Ticker(ticker)
                
                # Add timeout and better error handling for yfinance
                try:
                    df = stock.history(period=period, interval=interval, timeout=15)
                except TypeError:
                    # Older yfinance versions don't support timeout parameter
                    df = stock.history(period=period, interval=interval)
                except Exception as hist_err:
                    logger.error(f"yfinance history error for {ticker}: {hist_err}")
                    df = pd.DataFrame()
                
                # Handle None return from yfinance
                if df is None:
                    df = pd.DataFrame()
                
                # Check if df is actually a DataFrame
                if not isinstance(df, pd.DataFrame):
                    logger.warning(f"yfinance returned unexpected type {type(df)} for {ticker}")
                    df = pd.DataFrame()
                    
                if not df.empty:
                    # Clean column names - check if columns exist
                    if hasattr(df, 'columns') and df.columns is not None and len(df.columns) > 0:
                        df.columns = df.columns.str.lower()
                    
                    logger.info(f"Successfully fetched {len(df)} real data points for {ticker}")
                    
            except Exception as e:
                logger.error(f"Error fetching real-time data for {ticker}: {type(e).__name__}: {str(e)}")
                df = pd.DataFrame()
        
        # Fallback to mock data if yfinance failed or we're on Vercel
        if df.empty:
            logger.info(f"Using mock data for {ticker} (Vercel={self.use_mock_data})")
            df = self._generate_mock_data(ticker, interval, period)
        
        # Cache the data
        if not df.empty:
            self.cache[cache_key] = {
                'data': df.copy(),
                'timestamp': time.time()
            }
        
        return df
    
    def fetch_historical_data(
        self, 
        ticker: str, 
        start_date: str, 
        end_date: str
    ) -> pd.DataFrame:
        """
        Fetch historical stock data
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        
        Returns:
            DataFrame with historical data
        """
        try:
            logger.info(f"Fetching historical data for {ticker} from {start_date} to {end_date}")
            
            stock = yf.Ticker(ticker)
            
            # Add timeout and better error handling for yfinance
            try:
                df = stock.history(start=start_date, end=end_date, timeout=10)
            except TypeError:
                # Older yfinance versions don't support timeout parameter
                df = stock.history(start=start_date, end=end_date)
            
            # Handle None return from yfinance
            if df is None:
                logger.warning(f"yfinance returned None for {ticker}")
                return pd.DataFrame()
            
            # Check if df is actually a DataFrame
            if not isinstance(df, pd.DataFrame):
                logger.warning(f"yfinance returned unexpected type {type(df)} for {ticker}")
                return pd.DataFrame()
                
            if df.empty:
                logger.warning(f"No historical data returned for {ticker}")
                return pd.DataFrame()
            
            # Clean column names - check if columns exist
            if hasattr(df, 'columns') and df.columns is not None and len(df.columns) > 0:
                df.columns = df.columns.str.lower()
            
            logger.info(f"Successfully fetched {len(df)} historical data points for {ticker}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {ticker}: {e}")
            return pd.DataFrame()
    
    def get_current_price(self, ticker: str) -> Optional[float]:
        """
        Get current price for a ticker
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Current price or None if unavailable
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Try different price fields
            price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
            
            if price:
                logger.info(f"Current price for {ticker}: {price}")
                return float(price)
            else:
                logger.warning(f"No current price available for {ticker}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting current price for {ticker}: {e}")
            return None
    
    def get_market_status(self) -> Dict[str, Any]:
        """
        Get market status (simplified version)
        
        Returns:
            Dictionary with market status information
        """
        try:
            # Get BIST 100 index as market indicator
            bist = yf.Ticker("XU100.IS")
            info = bist.info
            
            status = {
                "market": "BIST",
                "is_open": True,  # Simplified - would need real-time API for actual status
                "current_time": datetime.now().isoformat(),
                "index_price": info.get('regularMarketPrice', 'N/A')
            }
            
            logger.info("Market status retrieved")
            return status
            
        except Exception as e:
            logger.error(f"Error getting market status: {e}")
            return {
                "market": "BIST",
                "is_open": False,
                "current_time": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """
        Get detailed stock information
        
        Args:
            ticker: Stock ticker symbol
        
        Returns:
            Dictionary with stock information
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Extract relevant information
            stock_info = {
                "symbol": info.get('symbol', ticker),
                "name": info.get('longName', 'N/A'),
                "sector": info.get('sector', 'N/A'),
                "industry": info.get('industry', 'N/A'),
                "market_cap": info.get('marketCap', 'N/A'),
                "currency": info.get('currency', 'TRY'),
                "exchange": info.get('exchange', 'IST'),
                "current_price": info.get('currentPrice') or info.get('regularMarketPrice', 'N/A'),
                "previous_close": info.get('previousClose', 'N/A'),
                "volume": info.get('volume', 'N/A'),
                "average_volume": info.get('averageVolume', 'N/A'),
                "fifty_two_week_high": info.get('fiftyTwoWeekHigh', 'N/A'),
                "fifty_two_week_low": info.get('fiftyTwoWeekLow', 'N/A'),
            }
            
            logger.info(f"Retrieved info for {ticker}")
            return stock_info
            
        except Exception as e:
            logger.error(f"Error getting stock info for {ticker}: {e}")
            return {"error": str(e)}
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        logger.info("Cache cleared")
