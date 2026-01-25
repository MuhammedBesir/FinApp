"""
Stock data API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.data_fetcher import DataFetcher
from app.services.technical_analysis import TechnicalAnalysis
from app.utils.logger import logger
import os

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/debug/yfinance")
async def debug_yfinance():
    """
    Debug endpoint to test yfinance connectivity
    """
    import sys
    result = {
        "environment": {
            "vercel": os.getenv("VERCEL", "not set"),
            "python_version": sys.version,
        },
        "tests": []
    }
    
    # Test 1: Import yfinance
    try:
        import yfinance as yf
        result["tests"].append({
            "test": "import yfinance",
            "status": "success",
            "yfinance_version": yf.__version__ if hasattr(yf, '__version__') else "unknown"
        })
    except Exception as e:
        result["tests"].append({
            "test": "import yfinance",
            "status": "error",
            "error": str(e)
        })
        return result
    
    # Test 2: Create ticker object
    ticker = "THYAO.IS"
    try:
        stock = yf.Ticker(ticker)
        result["tests"].append({
            "test": f"create ticker {ticker}",
            "status": "success"
        })
    except Exception as e:
        result["tests"].append({
            "test": f"create ticker {ticker}",
            "status": "error",
            "error": str(e)
        })
        return result
    
    # Test 3: Get info
    try:
        info = stock.info
        result["tests"].append({
            "test": "get ticker info",
            "status": "success" if info else "empty",
            "info_keys": list(info.keys())[:10] if info else []
        })
    except Exception as e:
        result["tests"].append({
            "test": "get ticker info",
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        })
    
    # Test 4: Get history
    try:
        df = stock.history(period="5d", interval="1d")
        result["tests"].append({
            "test": "get history (5d, 1d)",
            "status": "success" if not df.empty else "empty",
            "rows": len(df) if df is not None else 0,
            "columns": list(df.columns) if df is not None and hasattr(df, 'columns') else []
        })
    except Exception as e:
        result["tests"].append({
            "test": "get history (5d, 1d)",
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        })
    
    # Test 5: Try download function directly
    try:
        df2 = yf.download(ticker, period="5d", interval="1d", progress=False)
        result["tests"].append({
            "test": "yf.download direct",
            "status": "success" if not df2.empty else "empty",
            "rows": len(df2) if df2 is not None else 0
        })
    except Exception as e:
        result["tests"].append({
            "test": "yf.download direct",
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        })
    
    return result

# Initialize services
data_fetcher = DataFetcher()
tech_analysis = TechnicalAnalysis()


@router.get("/{ticker}/data")
async def get_stock_data(
    ticker: str,
    interval: str = Query("1h", description="Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)"),
    period: str = Query("1mo", description="Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)")
):
    """
    Get stock price data
    
    Args:
        ticker: Stock ticker symbol (e.g., TRALT.IS)
        interval: Data interval
        period: Data period
    
    Returns:
        Stock data with OHLCV
    """
    try:
        logger.info(f"API request: Get data for {ticker}")
        
        # Validate ticker
        if not data_fetcher.validate_ticker(ticker):
            raise HTTPException(status_code=404, detail=f"Invalid ticker: {ticker}")
        
        # Fetch data
        df = data_fetcher.fetch_realtime_data(ticker, interval, period)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data available for {ticker} (interval={interval}, period={period})")
        
        # Convert to JSON-friendly format
        data = []
        for idx, row in df.iterrows():
            data.append({
                "timestamp": str(idx),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": int(row['volume'])
            })
        
        return {
            "ticker": ticker,
            "interval": interval,
            "period": period,
            "data_points": len(data),
            "data": data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/indicators")
async def get_indicators(
    ticker: str,
    interval: str = Query("1h", description="Data interval"),
    period: str = Query("1mo", description="Data period")
):
    """
    Get technical indicators for a stock
    
    Args:
        ticker: Stock ticker symbol
        interval: Data interval
        period: Data period
    
    Returns:
        Technical indicators
    """
    try:
        logger.info(f"API request: Get indicators for {ticker}")
        
        # Fetch data
        df = data_fetcher.fetch_realtime_data(ticker, interval, period)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Calculate indicators
        df_with_indicators = tech_analysis.calculate_all_indicators(df)
        latest_indicators = tech_analysis.get_latest_indicators(df_with_indicators)
        
        # Get support/resistance
        support_resistance = tech_analysis.detect_support_resistance(df)
        
        # Get pivot points
        pivot_points = tech_analysis.calculate_pivot_points(df)
        
        # Get current price
        current_price = float(df.iloc[-1]['close'])
        
        return {
            "ticker": ticker,
            "timestamp": str(df.index[-1]),
            "current_price": current_price,
            "indicators": latest_indicators,
            "support_resistance": support_resistance,
            "pivot_points": pivot_points
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/info")
async def get_stock_info(ticker: str):
    """
    Get stock information
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Stock information
    """
    try:
        logger.info(f"API request: Get info for {ticker}")
        
        info = data_fetcher.get_stock_info(ticker)
        
        if "error" in info:
            raise HTTPException(status_code=404, detail=info["error"])
        
        return info
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/current-price")
async def get_current_price(ticker: str):
    """
    Get current price for a stock
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Current price
    """
    try:
        logger.info(f"API request: Get current price for {ticker}")
        
        price = data_fetcher.get_current_price(ticker)
        
        if price is None:
            raise HTTPException(status_code=404, detail="Price not available")
        
        return {
            "ticker": ticker,
            "price": price
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current price: {e}")
        raise HTTPException(status_code=500, detail=str(e))
