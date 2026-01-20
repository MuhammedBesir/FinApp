"""
Data fetching service for stock market data using yfinance
Supports real-time and historical data with caching
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from app.utils.logger import logger
import time


class DataFetcher:
    """Service for fetching stock data from yfinance"""
    
    # Class-level cache for better memory management
    _shared_cache: Dict[str, Dict[str, Any]] = {}
    
    def __init__(self):
        """Initialize the data fetcher"""
        self.cache = DataFetcher._shared_cache  # Use shared cache
        self.cache_ttl: int = 120  # seconds - increased for better performance
        
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
        
        logger.info("DataFetcher initialized")
    
    def validate_ticker(self, ticker: str) -> bool:
        """
        Validate if ticker exists and is tradable
        
        Args:
            ticker: Stock ticker symbol (e.g., "TRALT.IS")
        
        Returns:
            bool: True if ticker is valid
        """
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
        
        try:
            logger.info(f"Fetching real-time data for {ticker} (interval={interval}, period={period})")
            
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)
            
            # Handle None return from yfinance
            if df is None:
                logger.warning(f"yfinance returned None for {ticker} - API may be unavailable")
                return pd.DataFrame()
                
            if df.empty:
                logger.warning(f"No data returned for {ticker} - symbol may be invalid or market closed")
                return pd.DataFrame()
            
            # Clean column names - check if columns exist
            if hasattr(df, 'columns') and len(df.columns) > 0:
                df.columns = df.columns.str.lower()
            
            # Cache the data
            self.cache[cache_key] = {
                'data': df.copy(),
                'timestamp': time.time()
            }
            
            logger.info(f"Successfully fetched {len(df)} data points for {ticker}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching real-time data for {ticker}: {type(e).__name__}: {str(e)}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return pd.DataFrame()
    
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
            df = stock.history(start=start_date, end=end_date)
            
            # Handle None return from yfinance
            if df is None:
                logger.warning(f"yfinance returned None for {ticker}")
                return pd.DataFrame()
                
            if df.empty:
                logger.warning(f"No historical data returned for {ticker}")
                return pd.DataFrame()
            
            # Clean column names - check if columns exist
            if hasattr(df, 'columns') and len(df.columns) > 0:
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
