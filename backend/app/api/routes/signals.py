"""
Signal generation API endpoints - V2+V3 HYBRID STRATEGY INTEGRATED
Günde 1 kez çalışır, max 5 sinyal, sektör çeşitlendirmesi aktif
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, date
from typing import List, Optional
from app.services.data_fetcher import DataFetcher
from app.services.technical_analysis import TechnicalAnalysis
from app.services.signal_generator import SignalGenerator
from app.services.hybrid_strategy import HybridSignalGenerator, HybridRiskManagement
from app.utils.logger import logger

router = APIRouter(prefix="/signals", tags=["signals"])

# Initialize services
data_fetcher = DataFetcher()
tech_analysis = TechnicalAnalysis()

# V2+V3 Hybrid Generator (günde 1 kez çalışır)
hybrid_generator = HybridSignalGenerator()

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
    Get current market trading status with V2+V3 Hybrid info
    """
    try:
        # Market filter kontrolü
        market_ok, market_msg = hybrid_generator.check_market_filter()
        daily_status = hybrid_generator.get_daily_status()
        
        return {
            "phase": "hybrid_v2_v3",
            "market_filter": {
                "passed": market_ok,
                "message": market_msg
            },
            "daily_status": daily_status,
            "timestamp": datetime.now().isoformat(),
            "strategy_params": {
                "min_score": 75,
                "max_picks_per_day": 5,
                "max_per_sector": 1,
                "tp1_risk_reward": 2.5,
                "tp2_risk_reward": 4.0,
                "partial_exit_pct": 0.5
            }
        }
    except Exception as e:
        logger.error(f"Error getting market status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# V2+V3 Hybrid cache - günde 1 kez çalışır
daily_picks_cache = {
    "date": None,
    "data": None
}

@router.get("/daily-picks")
async def get_daily_picks(
    strategy: str = Query("hybrid", description="Strategy type (hybrid recommended)"),
    max_picks: int = Query(5, description="Maximum number of picks"),
    min_rr: float = Query(2.0, description="Minimum R/R ratio"),
    force_refresh: bool = Query(False, description="Force refresh (bypass cache)")
):
    """
    🎯 V2+V3 HYBRID DAILY PICKS
    
    Features:
    - Min Score: 75 (V2 quality filter)
    - Market Filter: BIST100 uptrend check
    - Sector Diversification: Max 1 per sector
    - Partial Exit: 50% at TP1, 50% at TP2
    - TP1: 1:2.5 R/R | TP2: 1:4.0 R/R
    
    Updates once per day.
    """
    try:
        today = date.today().isoformat()
        
        # Cache kontrolü - günde 1 kez
        if not force_refresh and daily_picks_cache["date"] == today and daily_picks_cache["data"]:
            logger.info("✅ Returning cached V2+V3 Hybrid daily picks")
            return daily_picks_cache["data"]

        logger.info(f"🚀 Generating V2+V3 Hybrid daily picks (Date: {today})")
        
        # Market filter kontrolü (esnek mod - uyarı ver ama engelleme)
        market_ok, market_msg = hybrid_generator.check_market_filter()
        market_warnings = []
        
        if not market_ok:
            market_warnings.append(f"⚠️ {market_msg} - DİKKATLİ OLUN!")
            market_warnings.append("🔴 BIST100 düşüş trendinde - pozisyon boyutunu %50 azaltın")
            logger.warning(f"Market filter failed but continuing: {market_msg}")
        
        # V2+V3 Hybrid tarama (market durumundan bağımsız)
        result = hybrid_generator.scan_all_stocks(
            tickers=BIST30,
            period='3mo',
            apply_booster=True,
            force_run=True
        )
        
        # Sinyalleri formatla
        picks = []
        for signal in result.get('signals', [])[:max_picks]:
            entry = signal.get('entry_price', 0)
            stop = signal.get('stop_loss', 0)
            tp1 = signal.get('take_profit_1', 0)
            tp2 = signal.get('take_profit_2', 0)
            
            risk_pct = abs((entry - stop) / entry * 100) if entry > 0 else 0
            reward_pct_1 = abs((tp1 - entry) / entry * 100) if entry > 0 else 0
            reward_pct_2 = abs((tp2 - entry) / entry * 100) if entry > 0 else 0
            
            picks.append({
                "ticker": signal.get('ticker', ''),
                "signal": "BUY",
                "strength": signal.get('strength', 0),
                "confidence": signal.get('confidence', 0),
                "entry_price": round(entry, 2),
                "stop_loss": round(stop, 2),
                "take_profit": round(tp1, 2),  # TP1 (legacy)
                "take_profit_1": round(tp1, 2),
                "take_profit_2": round(tp2, 2),
                "risk_reward_ratio": signal.get('risk_reward_1', 2.5),
                "risk_reward_2": signal.get('risk_reward_2', 4.0),
                "sector": hybrid_generator.SECTOR_MAP.get(
                    signal.get('ticker', '').replace('.IS', ''), 'Diğer'
                ),
                "reasons": signal.get('reasons', []),
                "exit_strategy": signal.get('exit_strategy', {
                    "tp1_action": "TP1'de %50 pozisyon kapat",
                    "tp1_new_stop": "Break-even'a çek",
                    "tp2_action": "TP2'de kalan %50 kapat"
                }),
                "partial_exit_pct": 0.5,
                "risk_pct": round(risk_pct, 2),
                "reward_pct": round(reward_pct_1, 2),
                "reward_pct_2": round(reward_pct_2, 2)
            })
        
        response_data = {
            "timestamp": datetime.now().isoformat(),
            "market_status": {
                "phase": "hybrid_v2_v3_active" if market_ok else "hybrid_v2_v3_caution",
                "message": market_msg,
                "tradeable": market_ok,
                "market_trend": "YUKSELIS" if market_ok else "DUSUS"
            },
            "strategy": "hybrid_v2_v3",
            "total_scanned": result.get('summary', {}).get('total_scanned', len(BIST30)),
            "signals_found": len(picks),
            "picks": picks,
            "warnings": market_warnings,
            "strategy_info": {
                "name": "V2+V3 Hybrid",
                "min_score": 75,
                "max_picks_per_day": 5,
                "max_per_sector": 1,
                "partial_exit": "50% at TP1, 50% at TP2",
                "tp1_rr": "1:2.5",
                "tp2_rr": "1:4.0",
                "expected_wr": "62-70%",
                "expected_pf": "2.5+",
                "market_filter_passed": market_ok
            },
            "sectors_used": result.get('summary', {}).get('sectors_used', {}),
            "market_trend": "YUKSELIS" if market_ok else "DUSUS"
        }
        
        # Cache güncelle
        daily_picks_cache["date"] = today
        daily_picks_cache["data"] = response_data
        
        logger.info(f"✅ V2+V3 Hybrid: {len(picks)} picks generated")
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
