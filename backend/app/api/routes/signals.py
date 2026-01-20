"""
Signal generation API endpoints - PROFESSIONAL TRADING RULES INTEGRATED
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import List, Optional
from app.services.data_fetcher import DataFetcher
from app.services.technical_analysis import TechnicalAnalysis
from app.services.signal_generator import SignalGenerator
from app.services.trading_rules import get_trading_rules_engine, TradingRulesEngine
from app.utils.logger import logger

router = APIRouter(prefix="/signals", tags=["signals"])

# Initialize services
data_fetcher = DataFetcher()
tech_analysis = TechnicalAnalysis()

# BIST30 for daily picks
BIST30 = [
    "AKBNK.IS", "AKSEN.IS", "ARCLK.IS", "ASELS.IS", "BIMAS.IS",
    "EKGYO.IS", "ENKAI.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS",
    "GUBRF.IS", "HEKTS.IS", "ISCTR.IS", "KCHOL.IS", "KRDMD.IS",
    "ODAS.IS", "PETKM.IS", "PGSUS.IS", "SAHOL.IS", "SASA.IS",
    "SISE.IS", "TAVHL.IS", "TCELL.IS", "THYAO.IS", "TKFEN.IS",
    "TOASO.IS", "TUPRS.IS", "YKBNK.IS"
]


@router.get("/market-status")
async def get_market_status():
    """
    Get current market trading status
    
    Returns:
        Market phase, tradeable status, and warnings
    """
    try:
        rules_engine = get_trading_rules_engine()
        tradeable, message = rules_engine.is_tradeable_time()
        phase = rules_engine.get_market_phase()
        
        return {
            "phase": phase.value,
            "tradeable": tradeable,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "risk_parameters": {
                "max_position_risk_pct": rules_engine.risk_params.max_position_risk_pct,
                "max_daily_loss_pct": rules_engine.risk_params.max_daily_loss_pct,
                "min_risk_reward": rules_engine.risk_params.min_risk_reward,
                "max_open_positions": rules_engine.risk_params.max_open_positions
            }
        }
    except Exception as e:
        logger.error(f"Error getting market status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Simple in-memory cache for daily picks
daily_picks_cache = {
    "date": None,
    "data": None
}

@router.get("/daily-picks")
async def get_daily_picks(
    strategy: str = Query("moderate", description="Strategy type"),
    max_picks: int = Query(5, description="Maximum number of picks"),
    min_rr: float = Query(2.0, description="Minimum R/R ratio")
):
    """
    Get daily trading picks - IMPROVED STRATEGY
    Updates once per day.
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Check Cache
        if daily_picks_cache["date"] == today and daily_picks_cache["data"]:
            logger.info("Returning cached daily picks")
            return daily_picks_cache["data"]

        logger.info(f"Generating daily picks with {strategy} strategy (Date: {today})")
        
        rules_engine = get_trading_rules_engine()
        signal_gen = SignalGenerator(strategy_type=strategy)
        
        picks = []
        warnings = []
        
        for ticker in BIST30:
            try:
                # Fetch data - USING DAILY DATA (1y history for robust trend analysis)
                df = data_fetcher.fetch_realtime_data(ticker, "1d", "1y")
                
                if df.empty or len(df) < 50:
                    continue
                
                # Calculate indicators
                df_with_indicators = tech_analysis.calculate_all_indicators(df)
                latest_indicators = tech_analysis.get_latest_indicators(df_with_indicators)
                
                # Generate signal
                signal = signal_gen.generate_signal(df_with_indicators, latest_indicators)
                
                # Only include BUY signals
                if signal['signal'] == 'BUY':
                    signal['ticker'] = ticker
                    signal['sector'] = get_sector(ticker)
                    picks.append(signal)
                    
            except Exception as e:
                logger.warning(f"Error processing {ticker}: {e}")
                continue
        
        # Sort by score/strength
        picks.sort(key=lambda x: x['strength'], reverse=True)
        
        # Limit picks
        top_picks = picks[:max_picks]
        
        response_data = {
            "timestamp": datetime.now().isoformat(),
            "market_status": {
                "phase": "analiz_tamamlandi"
            },
            "strategy": strategy,
            "total_scanned": len(BIST30),
            "signals_found": len(picks),
            "picks": top_picks,
            "warnings": warnings,
            "risk_rules": {
                 "info": "Improved Strategy v3"
            }
        }
        
        # Update Cache
        daily_picks_cache["date"] = today
        daily_picks_cache["data"] = response_data
        
        return response_data
    
    except Exception as e:
        logger.error(f"Error generating daily picks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/position-calculator")
async def calculate_position(
    entry_price: float = Query(..., description="Entry price"),
    stop_loss: float = Query(..., description="Stop loss price"),
    portfolio_value: float = Query(100000, description="Portfolio value in TRY"),
    risk_percent: float = Query(2.0, description="Risk percentage (1-5)")
):
    """
    Calculate position size using professional risk management
    
    Formula: Position = Risk Amount / (Entry - Stop Loss)
    
    Example:
    - Portfolio: 100,000 TRY
    - Risk: 2% = 2,000 TRY max loss
    - Entry: 50 TRY, Stop: 47 TRY
    - Position = 2,000 / 3 = 666 shares
    """
    try:
        if risk_percent < 1 or risk_percent > 5:
            raise HTTPException(status_code=400, detail="Risk percentage must be between 1-5%")
        
        if stop_loss >= entry_price:
            raise HTTPException(status_code=400, detail="Stop loss must be below entry price for BUY")
        
        risk_amount = portfolio_value * (risk_percent / 100)
        risk_per_share = entry_price - stop_loss
        
        if risk_per_share <= 0:
            raise HTTPException(status_code=400, detail="Invalid stop loss level")
        
        position_shares = int(risk_amount / risk_per_share)
        position_value = position_shares * entry_price
        position_pct = (position_value / portfolio_value) * 100
        
        return {
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "portfolio_value": portfolio_value,
            "risk_percent": risk_percent,
            "calculation": {
                "shares": position_shares,
                "position_value": round(position_value, 2),
                "position_pct": round(position_pct, 2),
                "risk_amount": round(risk_amount, 2),
                "risk_per_share": round(risk_per_share, 2),
                "max_loss": round(position_shares * risk_per_share, 2)
            },
            "recommendations": {
                "target_1": round(entry_price + (risk_per_share * 2), 2),
                "target_2": round(entry_price + (risk_per_share * 3), 2),
                "trailing_stop_activate": round(entry_price * 1.05, 2)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_sector(ticker: str) -> str:
    """Get sector for a ticker"""
    sector_map = {
        "AKBNK.IS": "Bankacılık", "GARAN.IS": "Bankacılık", 
        "ISCTR.IS": "Bankacılık", "YKBNK.IS": "Bankacılık",
        "THYAO.IS": "Havacılık", "PGSUS.IS": "Havacılık", 
        "TAVHL.IS": "Havacılık",
        "FROTO.IS": "Otomotiv", "TOASO.IS": "Otomotiv",
        "SAHOL.IS": "Holding", "KCHOL.IS": "Holding",
        "BIMAS.IS": "Perakende",
        "EREGL.IS": "Demir Çelik", "KRDMD.IS": "Demir Çelik",
        "TUPRS.IS": "Enerji", "AKSEN.IS": "Enerji", "ODAS.IS": "Enerji",
        "TCELL.IS": "Telekomünikasyon",
        "ARCLK.IS": "Beyaz Eşya",
        "SISE.IS": "Cam", "SASA.IS": "Kimya", "PETKM.IS": "Kimya",
        "ASELS.IS": "Savunma", "ENKAI.IS": "İnşaat",
        "GUBRF.IS": "Gübre", "HEKTS.IS": "Gübre",
        "EKGYO.IS": "GYO", "TKFEN.IS": "İnşaat"
    }
    return sector_map.get(ticker, "Diğer")


@router.get("/{ticker}")
async def get_signals(
    ticker: str,
    strategy: str = Query("moderate", description="Strategy type: conservative, moderate, aggressive"),
    interval: str = Query("5m", description="Data interval"),
    period: str = Query("1d", description="Data period")
):
    """
    Generate trading signals for  a stock
    
    Args:
        ticker: Stock ticker symbol
        strategy: Strategy type
        interval: Data interval
        period: Data period
    
    Returns:
        Trading signal with entry/exit levels
    """
    try:
        logger.info(f"API request: Generate signal for {ticker} with {strategy} strategy")
        
        # Validate strategy
        if strategy not in ["conservative", "moderate", "aggressive"]:
            raise HTTPException(status_code=400, detail="Invalid strategy type")
        
        # Fetch data
        df = data_fetcher.fetch_realtime_data(ticker, interval, period)
        
        if df.empty or len(df) < 50:
            raise HTTPException(status_code=404, detail="Insufficient data for signal generation")
        
        # Calculate indicators
        df_with_indicators = tech_analysis.calculate_all_indicators(df)
        latest_indicators = tech_analysis.get_latest_indicators(df_with_indicators)
        
        # Generate signal
        signal_gen = SignalGenerator(strategy_type=strategy)
        signal = signal_gen.generate_signal(df_with_indicators, latest_indicators)
        
        # Add ticker and interval info
        signal['ticker'] = ticker
        signal['interval'] = interval
        signal['strategy'] = strategy
        signal['sector'] = get_sector(ticker)
        
        return signal
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))
