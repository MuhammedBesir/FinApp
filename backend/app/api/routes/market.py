"""
Market Data Routes - Piyasa Verileri Endpoint'leri
"""
from fastapi import APIRouter, HTTPException
from app.services.market_data import market_data_service

router = APIRouter()

@router.get("/market/all")
async def get_all_market_data():
    """
    Tüm piyasa verilerini getir
    - BIST100, BIST30
    - USD/TRY, EUR/TRY
    - Altın, Bitcoin
    - S&P500, NASDAQ
    """
    result = await market_data_service.get_all_market_data()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Market data fetch failed"))
    return result

@router.get("/market/forex")
async def get_forex_data():
    """Döviz kurları (USD/TRY, EUR/TRY)"""
    result = await market_data_service.get_forex_data()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Forex data fetch failed"))
    return result

@router.get("/market/commodities")
async def get_commodities_data():
    """Emtia verileri (Altın, Bitcoin)"""
    result = await market_data_service.get_commodities_data()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Commodities data fetch failed"))
    return result

@router.get("/market/global")
async def get_global_indices():
    """Küresel endeksler (S&P500, NASDAQ)"""
    result = await market_data_service.get_global_indices_data()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Global indices fetch failed"))
    return result
