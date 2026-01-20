"""
Strategy Backtest API Endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.strategy_tester import StrategyTester
from app.utils.logger import logger
from datetime import datetime, timedelta

router = APIRouter(prefix="/backtest", tags=["strategy-backtest"])

# Initialize tester
tester = StrategyTester()


@router.get("/daily-strategy")
async def test_daily_strategy(
    days: int = Query(180, description="Number of days to backtest (default 6 months)"),
    min_score: int = Query(75, description="Minimum score threshold (75+ for excellent setups)")
):
    """
    Test daily trading strategy for last N days
    
    Returns:
        Win rate, profit factor, equity curve, and detailed metrics
    """
    try:
        logger.info(f"API request: Backtest daily strategy for {days} days")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        results = tester.backtest_daily_strategy(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            min_score=min_score
        )
        
        return results
    
    except Exception as e:
        logger.error(f"Error backtesting strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quick-test")
async def quick_strategy_test():
    """
    Quick backtest for last 30 days
    
    Returns:
        Success metrics and performance summary
    """
    try:
        logger.info("API request: Quick strategy test")
        
        results = tester.quick_test(days=30)
        
        return results
    
    except Exception as e:
        logger.error(f"Error in quick test: {e}")
        raise HTTPException(status_code=500, detail=str(e))
