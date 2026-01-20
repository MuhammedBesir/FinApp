"""
IPO API Routes - Halka Arz endpointleri
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.services.ipo_service import ipo_service
from app.services.ipo_scheduler import get_scheduler

router = APIRouter(prefix="/ipo", tags=["IPO - Halka Arz"])

class WatchlistRequest(BaseModel):
    user_id: str

class InvestmentCalcRequest(BaseModel):
    lot_count: int

class IPOAddRequest(BaseModel):
    """Manuel IPO ekleme için request model"""
    symbol: str
    name: str
    sector: str
    description: str = ""
    ipo_type: str = "primary"
    status: str = "upcoming"
    price_range_min: float = 0
    price_range_max: float = 0
    lot_size: int = 100
    min_lot: int = 1
    shares_offered: int = 0
    total_shares: int = 0
    market_cap_estimate: float = 0
    demand_start: Optional[str] = None
    demand_end: Optional[str] = None
    allocation_date: Optional[str] = None
    trading_start: Optional[str] = None
    website: Optional[str] = None
    kap_url: Optional[str] = None


# ============ ADMIN ENDPOİNTLERİ (/{ipo_id}'den ÖNCE tanımlanmalı!) ============

@router.get("/admin/status")
async def get_update_status():
    """Güncelleme durumunu getir"""
    status = ipo_service.get_update_status()
    scheduler = get_scheduler()
    scheduler_status = scheduler.get_status()
    
    return {
        "success": True,
        "data_status": status,
        "scheduler_status": scheduler_status
    }


@router.post("/admin/refresh")
async def refresh_ipo_data():
    """Web'den IPO verilerini güncelle (manuel tetikleme)"""
    try:
        result = await ipo_service.refresh_data_async()
        return {
            "success": True,
            "message": "Güncelleme tamamlandı",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Güncelleme hatası: {str(e)}")


@router.post("/admin/trigger-update")
async def trigger_scheduler_update():
    """Scheduler'ı manuel tetikle"""
    scheduler = get_scheduler()
    success = scheduler.trigger_manual_update()
    
    if success:
        return {
            "success": True,
            "message": "Güncelleme tetiklendi"
        }
    else:
        raise HTTPException(status_code=500, detail="Scheduler başlatılamamış")


@router.post("/admin/add")
async def add_ipo_manually(request: IPOAddRequest):
    """Manuel olarak yeni IPO ekle"""
    ipo_data = request.model_dump()
    ipo_id = ipo_service.add_ipo_manually(ipo_data)
    
    if ipo_id:
        return {
            "success": True,
            "message": "IPO başarıyla eklendi",
            "ipo_id": ipo_id
        }
    else:
        raise HTTPException(status_code=500, detail="IPO eklenemedi")


@router.post("/admin/save")
async def save_data():
    """Verileri JSON'a kaydet"""
    success = ipo_service.force_save()
    
    return {
        "success": success,
        "message": "Veriler kaydedildi" if success else "Kaydetme hatası"
    }


@router.get("/admin/scheduler-jobs")
async def get_scheduler_jobs():
    """Scheduler job'larını listele"""
    scheduler = get_scheduler()
    status = scheduler.get_status()
    
    return {
        "success": True,
        "jobs": status.get('jobs', []),
        "is_running": status.get('is_running', False),
        "last_run": status.get('last_run'),
        "run_count": status.get('run_count', 0),
        "error_count": status.get('error_count', 0)
    }


@router.delete("/admin/delete/{ipo_id}")
async def delete_ipo(ipo_id: str):
    """IPO'yu sil"""
    success = ipo_service.delete_ipo(ipo_id)
    
    if success:
        return {
            "success": True,
            "message": "IPO silindi"
        }
    else:
        raise HTTPException(status_code=404, detail="IPO bulunamadı")


# ============ GENEL ENDPOİNTLER ============

@router.get("/")
async def get_all_ipos(
    status: Optional[str] = Query(None, description="upcoming, active, completed, trading"),
    sector: Optional[str] = None
):
    """Tüm halka arzları getir"""
    ipos = ipo_service.get_all_ipos(status=status, sector=sector)
    return {
        "success": True,
        "ipos": ipos,
        "count": len(ipos)
    }

@router.get("/stats")
async def get_ipo_stats():
    """Halka arz istatistikleri"""
    stats = ipo_service.get_ipo_stats()
    return {
        "success": True,
        "stats": stats
    }

@router.get("/active")
async def get_active_ipos():
    """Aktif halka arzlar (talep toplama devam ediyor)"""
    ipos = ipo_service.get_active_ipos()
    return {
        "success": True,
        "ipos": ipos,
        "count": len(ipos)
    }

@router.get("/upcoming")
async def get_upcoming_ipos():
    """Yaklaşan halka arzlar"""
    ipos = ipo_service.get_upcoming_ipos()
    return {
        "success": True,
        "ipos": ipos,
        "count": len(ipos)
    }

@router.get("/recent")
async def get_recent_ipos(days: int = Query(30, ge=1, le=365)):
    """Son X gün içinde işlem görmeye başlayan halka arzlar"""
    ipos = ipo_service.get_recent_ipos(days=days)
    return {
        "success": True,
        "ipos": ipos,
        "count": len(ipos),
        "period_days": days
    }

@router.get("/symbol/{symbol}")
async def get_ipo_by_symbol(symbol: str):
    """Sembole göre halka arz getir"""
    ipo = ipo_service.get_ipo_by_symbol(symbol)
    if not ipo:
        raise HTTPException(status_code=404, detail="Halka arz bulunamadı")
    
    return {
        "success": True,
        "ipo": ipo
    }

@router.get("/watchlist/{user_id}")
async def get_watchlist(user_id: str):
    """Kullanıcının takip listesini getir"""
    ipos = ipo_service.get_watchlist(user_id)
    return {
        "success": True,
        "ipos": ipos,
        "count": len(ipos)
    }


# ============ DYNAMIC ID ENDPOİNTLERİ (en sonda olmalı!) ============

@router.get("/{ipo_id}")
async def get_ipo(ipo_id: str):
    """Belirli bir halka arzı getir"""
    ipo = ipo_service.get_ipo(ipo_id)
    if not ipo:
        raise HTTPException(status_code=404, detail="Halka arz bulunamadı")
    
    return {
        "success": True,
        "ipo": ipo
    }

@router.post("/{ipo_id}/watchlist")
async def add_to_watchlist(ipo_id: str, request: WatchlistRequest):
    """Takip listesine ekle"""
    success = ipo_service.add_to_watchlist(request.user_id, ipo_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Halka arz bulunamadı")
    
    return {
        "success": True,
        "message": "Takip listesine eklendi"
    }

@router.delete("/{ipo_id}/watchlist")
async def remove_from_watchlist(ipo_id: str, user_id: str):
    """Takip listesinden çıkar"""
    success = ipo_service.remove_from_watchlist(user_id, ipo_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Takip listesinde bulunamadı")
    
    return {
        "success": True,
        "message": "Takip listesinden çıkarıldı"
    }

@router.post("/{ipo_id}/calculate")
async def calculate_investment(ipo_id: str, request: InvestmentCalcRequest):
    """Yatırım hesaplama"""
    result = ipo_service.calculate_investment(ipo_id, request.lot_count)
    
    if not result:
        raise HTTPException(status_code=404, detail="Halka arz bulunamadı")
    
    return {
        "success": True,
        "calculation": result
    }
