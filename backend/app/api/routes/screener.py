"""
Stock Screener API Endpoints
Daily trading picks ve signals
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.stock_screener import StockScreener
from app.utils.logger import logger
from datetime import datetime

router = APIRouter(prefix="/screener", tags=["screener"])

# Initialize screener
screener = StockScreener()


@router.get("/daily-picks")
async def get_daily_picks(
    top_n: int = Query(10, description="Number of top stocks to return"),
    min_score: int = Query(75, description="Minimum momentum score threshold (75+ for excellent setups)")
):
    """
    Get top daily stock picks based on momentum score
    
    Returns:
        Top N stocks with highest momentum scores for day trading
    """
    try:
        logger.info(f"API request: Get daily picks (top {top_n}, min_score {min_score})")
        
        picks = screener.get_top_picks(n=top_n, min_score=min_score)
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "market_time": datetime.now().strftime("%H:%M"),
            "total_picks": len(picks),
            "picks": picks
        }
    
    except Exception as e:
        logger.error(f"Error getting daily picks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/signal")
async def get_stock_signal(
    ticker: str,
    interval: str = Query("5m", description="Data interval"),
    period: str = Query("1d", description="Data period")
):
    """
    Get real-time entry/exit signal for a specific stock
    
    Args:
        ticker: Stock ticker symbol
        interval: Data interval
        period: Data period
    
    Returns:
        Momentum score, recommendation, and entry/exit levels
    """
    try:
        logger.info(f"API request: Get signal for {ticker}")
        
        signal = screener.get_stock_signal(ticker, interval, period)
        
        if 'error' in signal:
            raise HTTPException(status_code=404, detail=signal['error'])
        
        return signal
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scan")
async def scan_all_stocks(
    interval: str = Query("5m", description="Data interval"),
    period: str = Query("1d", description="Data period")
):
    """
    Scan all BIST30 stocks and return scores
    
    Returns:
        All stocks with momentum scores (sorted by score)
    """
    try:
        logger.info("API request: Scan all stocks")
        
        results = screener.screen_all_stocks(interval, period)
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "market_time": datetime.now().strftime("%H:%M"),
            "total_stocks": len(results),
            "stocks": results
        }
    
    except Exception as e:
        logger.error(f"Error scanning stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-movers")
async def get_top_movers(
    top_n: int = Query(5, description="Kaç hisse gösterilecek")
):
    """
    🔥 EN ÇOK HAREKET EDEN HİSSELER - BIST30 Günlük
    
    Günlük en çok yükselen ve düşen BIST30 hisselerini döndürür.
    Her zaman güncel veri sağlar.
    
    Returns:
        Top gainers (yükselenler) ve top losers (düşenler)
    """
    try:
        logger.info(f"API request: Top movers (top {top_n})")
        
        result = screener.get_top_movers(top_n=top_n)
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting top movers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/morning-picks")
async def get_morning_picks(
    capital: float = Query(10000, description="Toplam yatırım sermayesi (TL) - Sadece referans"),
    max_picks: int = Query(5, description="Önerilecek maksimum hisse sayısı")
):
    """
    🌅 SABAH 5 HİSSE - Günlük İşlem Stratejisi v2
    
    Her sabah piyasa açılışında (09:30-10:00) alınacak en iyi 5 hisseyi döndürür.
    
    GELİŞTİRMELER:
    - Score eşiği: 75+ (sadece çok güçlü sinyaller)
    - Stop-Loss: Teknik destek seviyelerinde (~%2)
    - Take-Profit: Teknik direnç + 1:3 R:R (%6-8)
    - Market filtresi: Sadece BIST100 yükselişteyken
    - Sektör çeşitlendirmesi: Her sektörden max 1 hisse
    
    Args:
        capital: Toplam sermaye (sadece referans, miktar hesaplanmaz)
        max_picks: Önerilecek hisse sayısı (varsayılan: 5)
    
    Returns:
        - Önerilen hisseler ve sektörleri
        - Teknik giriş, stop-loss, take-profit seviyeleri
        - Risk:Ödül oranları
        - Günlük işlem talimatları
    """
    try:
        logger.info(f"API request: Morning picks v2 (max: {max_picks})")
        
        result = screener.get_morning_picks(capital=capital, max_picks=max_picks)
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting morning picks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/day-trade-status")
async def get_day_trade_status():
    """
    Günlük işlem durumu ve piyasa zamanlaması
    
    Returns:
        - Piyasa durumu (açık/kapalı)
        - İşlem zamanı (alım/satım/izleme)
        - Önerilen aksiyon
    """
    try:
        import pytz
        from datetime import time as dt_time
        
        tz = pytz.timezone('Europe/Istanbul')
        now = datetime.now(tz)
        current_time = now.time()
        
        # Market timing
        MARKET_OPEN = dt_time(9, 0)
        AVOID_UNTIL = dt_time(9, 30)
        BUY_WINDOW_END = dt_time(10, 0)
        SELL_START = dt_time(17, 0)
        SELL_END = dt_time(17, 30)
        MARKET_CLOSE = dt_time(18, 0)
        
        if current_time < MARKET_OPEN:
            phase = "PRE_MARKET"
            action = "Piyasa açılışını bekleyin"
            color = "gray"
        elif current_time < AVOID_UNTIL:
            phase = "OPENING_VOLATILITY"
            action = "⚠️ Yüksek volatilite - Bekleyin"
            color = "orange"
        elif current_time < BUY_WINDOW_END:
            phase = "BUY_WINDOW"
            action = "✅ ALIM ZAMANI - Sabah hisselerini alın!"
            color = "green"
        elif current_time < SELL_START:
            phase = "MONITORING"
            action = "📊 Pozisyonları izleyin"
            color = "blue"
        elif current_time < SELL_END:
            phase = "SELL_WINDOW"
            action = "🔔 SATIŞ ZAMANI - Pozisyonları kapatın!"
            color = "red"
        elif current_time < MARKET_CLOSE:
            phase = "CLOSING"
            action = "⚠️ Piyasa kapanıyor"
            color = "orange"
        else:
            phase = "CLOSED"
            action = "Piyasa kapalı - Yarını planlayın"
            color = "gray"
        
        # Weekend check
        if now.weekday() >= 5:
            phase = "WEEKEND"
            action = "Hafta sonu - Piyasa kapalı"
            color = "gray"
        
        return {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "phase": phase,
            "action": action,
            "color": color,
            "market_open": MARKET_OPEN.strftime("%H:%M"),
            "buy_window": f"{AVOID_UNTIL.strftime('%H:%M')} - {BUY_WINDOW_END.strftime('%H:%M')}",
            "sell_window": f"{SELL_START.strftime('%H:%M')} - {SELL_END.strftime('%H:%M')}",
            "market_close": MARKET_CLOSE.strftime("%H:%M")
        }
        
    except Exception as e:
        logger.error(f"Error getting day trade status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
