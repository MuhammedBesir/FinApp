"""
Advanced Technical Indicators API Endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.data_fetcher import DataFetcher
from app.services.technical_analysis import TechnicalAnalysis, TrendChannelIndicator
from app.utils.logger import logger
import pandas as pd

router = APIRouter(prefix="/indicators", tags=["indicators"])

# Initialize services
data_fetcher = DataFetcher()
tech_analysis = TechnicalAnalysis()


@router.get("/{ticker}/ichimoku")
async def get_ichimoku(
    ticker: str,
    interval: str = Query("5m", description="Data interval (1m, 5m, 15m, 1h, 1d)"),
    period: str = Query("1d", description="Data period (1d, 5d, 1mo, 3mo, 1y)")
):
    """
    Get Ichimoku Cloud indicator data
    
    Args:
        ticker: Stock ticker symbol (e.g., THYAO.IS)
        interval: Data interval
        period: Data period
    
    Returns:
        Ichimoku Cloud data with all 5 lines
    """
    try:
        logger.info(f"API request: Get Ichimoku for {ticker}")
        
        # Validate ticker
        if not data_fetcher.validate_ticker(ticker):
            raise HTTPException(status_code=404, detail=f"Invalid ticker: {ticker}")
        
        # Fetch data
        df = data_fetcher.fetch_realtime_data(ticker, interval, period)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Calculate Ichimoku
        df_ichimoku = tech_analysis.calculate_ichimoku(df)
        
        # Convert to JSON-friendly format
        data = []
        for idx, row in df_ichimoku.iterrows():
            data.append({
                "timestamp": str(idx),
                "tenkan": float(row.get('ichimoku_tenkan', 0)) if not pd.isna(row.get('ichimoku_tenkan')) else None,
                "kijun": float(row.get('ichimoku_kijun', 0)) if not pd.isna(row.get('ichimoku_kijun')) else None,
                "senkou_a": float(row.get('ichimoku_senkou_a', 0)) if not pd.isna(row.get('ichimoku_senkou_a')) else None,
                "senkou_b": float(row.get('ichimoku_senkou_b', 0)) if not pd.isna(row.get('ichimoku_senkou_b')) else None,
                "chikou": float(row.get('ichimoku_chikou', 0)) if not pd.isna(row.get('ichimoku_chikou')) else None,
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
        logger.error(f"Error getting Ichimoku data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/fibonacci")
async def get_fibonacci(
    ticker: str,
    interval: str = Query("5m", description="Data interval"),
    period: str = Query("1d", description="Data period"),
    lookback: int = Query(100, description="Lookback period for swing high/low detection")
):
    """
    Get Fibonacci Retracement levels
    
    Args:
        ticker: Stock ticker symbol
        interval: Data interval
        period: Data period
        lookback: Number of candles to look back for swing detection
    
    Returns:
        Fibonacci retracement levels
    """
    try:
        logger.info(f"API request: Get Fibonacci for {ticker}")
        
        # Validate ticker
        if not data_fetcher.validate_ticker(ticker):
            raise HTTPException(status_code=404, detail=f"Invalid ticker: {ticker}")
        
        # Fetch data
        df = data_fetcher.fetch_realtime_data(ticker, interval, period)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Calculate Fibonacci levels
        fib_levels = tech_analysis.calculate_fibonacci_levels(df, lookback=lookback)
        
        return {
            "ticker": ticker,
            "interval": interval,
            "period": period,
            "lookback": lookback,
            "levels": {
                "high": float(fib_levels['high']),
                "low": float(fib_levels['low']),
                "fib_0": float(fib_levels['fib_0']),
                "fib_236": float(fib_levels['fib_236']),
                "fib_382": float(fib_levels['fib_382']),
                "fib_500": float(fib_levels['fib_500']),
                "fib_618": float(fib_levels['fib_618']),
                "fib_786": float(fib_levels['fib_786']),
                "fib_100": float(fib_levels['fib_100']),
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Fibonacci levels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/bollinger")
async def get_bollinger_bands(
    ticker: str,
    interval: str = Query("5m", description="Data interval"),
    period: str = Query("1d", description="Data period"),
    bb_period: int = Query(20, description="Bollinger Bands period"),
    std_dev: float = Query(2.0, description="Standard deviation multiplier")
):
    """
    Get Bollinger Bands indicator data
    
    Args:
        ticker: Stock ticker symbol
        interval: Data interval
        period: Data period
        bb_period: Bollinger Bands calculation period
        std_dev: Standard deviation multiplier
    
    Returns:
        Bollinger Bands data (upper, middle, lower)
    """
    try:
        logger.info(f"API request: Get Bollinger Bands for {ticker}")
        
        # Validate ticker
        if not data_fetcher.validate_ticker(ticker):
            raise HTTPException(status_code=404, detail=f"Invalid ticker: {ticker}")
        
        # Fetch data
        df = data_fetcher.fetch_realtime_data(ticker, interval, period)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Calculate Bollinger Bands
        df_bb = tech_analysis.calculate_bollinger_bands(df, period=bb_period, std=std_dev)
        
        # Convert to JSON-friendly format
        data = []
        for idx, row in df_bb.iterrows():
            data.append({
                "timestamp": str(idx),
                "bb_upper": float(row.get('bb_upper', 0)) if not pd.isna(row.get('bb_upper')) else None,
                "bb_middle": float(row.get('bb_middle', 0)) if not pd.isna(row.get('bb_middle')) else None,
                "bb_lower": float(row.get('bb_lower', 0)) if not pd.isna(row.get('bb_lower')) else None,
            })
        
        return {
            "ticker": ticker,
            "interval": interval,
            "period": period,
            "bb_period": bb_period,
            "std_dev": std_dev,
            "data_points": len(data),
            "data": data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Bollinger Bands data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/trend-channel")
async def get_trend_channel(
    ticker: str,
    interval: str = Query("1d", description="Data interval (5m, 15m, 1h, 1d)"),
    period: str = Query("3mo", description="Data period (1mo, 3mo, 6mo, 1y)"),
    channel_period: int = Query(20, description="Channel calculation period")
):
    """
    Get Trend Channel indicator with trading signals
    
    Yükselen/Düşen kanal tespiti ve AL/SAT sinyalleri
    
    Args:
        ticker: Stock ticker symbol (e.g., THYAO.IS)
        interval: Data interval
        period: Data period
        channel_period: Lookback period for channel calculation
    
    Returns:
        Trend channel analysis with signals, support/resistance levels
    """
    try:
        logger.info(f"API request: Get Trend Channel for {ticker}")
        
        # Validate ticker
        if not data_fetcher.validate_ticker(ticker):
            raise HTTPException(status_code=404, detail=f"Invalid ticker: {ticker}")
        
        # Fetch data
        df = data_fetcher.fetch_realtime_data(ticker, interval, period)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available")
        
        if len(df) < channel_period:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient data. Need at least {channel_period} data points, got {len(df)}"
            )
        
        # Calculate Trend Channel
        channel_indicator = TrendChannelIndicator(df, channel_period)
        analysis = channel_indicator.get_full_analysis()
        
        # Get channel lines for charting
        lines = channel_indicator.get_channel_lines(future_points=5)
        
        return {
            "success": True,
            "ticker": ticker,
            "interval": interval,
            "period": period,
            "channel_period": channel_period,
            "data_points": len(df),
            "analysis": {
                "timestamp": analysis['timestamp'],
                "signal": analysis['signal'],
                "channel_data": analysis['channel_data'],
                "recommendation": analysis['recommendation']
            },
            "chart_data": {
                "support_line": lines['support_points'],
                "resistance_line": lines['resistance_points']
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Trend Channel data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trend-channel/analyze")
async def analyze_trend_channel(
    symbol: str = Query(..., description="Stock symbol (e.g., THYAO.IS)"),
    period: int = Query(20, description="Channel period")
):
    """
    Quick trend channel analysis for a stock
    
    Returns:
        Quick analysis with signal and recommendation
    """
    try:
        # Fetch daily data
        df = data_fetcher.fetch_realtime_data(symbol, "1d", "3mo")
        
        if df.empty or len(df) < period:
            raise HTTPException(status_code=404, detail="Insufficient data")
        
        # Analyze
        indicator = TrendChannelIndicator(df, period)
        result = indicator.generate_signal()
        
        return {
            "success": True,
            "symbol": symbol,
            "signal": result['signal'],
            "channel": result['channel_data']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in trend channel analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
