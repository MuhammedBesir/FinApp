"""
Alert API Endpoints
Trading alert yönetimi
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.services.alert_manager import AlertManager
from app.services.data_fetcher import DataFetcher
from app.utils.logger import logger

router = APIRouter(prefix="/alerts", tags=["alerts"])

# Initialize services
alert_manager = AlertManager()
data_fetcher = DataFetcher()


class AlertCreate(BaseModel):
    type: str  # 'price', 'score', 'signal', 'position'
    ticker: str
    condition: Dict[str, Any]
    notification: Optional[Dict[str, bool]] = None
    priority: Optional[str] = 'medium'  # low, medium, high, critical


@router.post("/create")
async def create_alert(alert: AlertCreate):
    """
    Yeni alert oluştur
    
    Examples:
        - Price: {"type": "price", "ticker": "THYAO.IS", "condition": {"price_above": 450}}
        - Score: {"type": "score", "ticker": "THYAO.IS", "condition": {"score_above": 80}}
        - Signal: {"type": "signal", "ticker": "THYAO.IS", "condition": {}}
    """
    try:
        alert_id = alert_manager.create_alert(
            alert_type=alert.type,
            ticker=alert.ticker,
            condition=alert.condition,
            notification=alert.notification,
            priority=alert.priority or 'medium'
        )
        
        return {
            "success": True,
            "alert_id": alert_id,
            "message": "Alert created successfully"
        }
    
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_alerts():
    """Aktif alertleri getir"""
    try:
        alerts = alert_manager.get_active_alerts()
        
        return {
            "success": True,
            "count": len(alerts),
            "alerts": alerts
        }
    
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check")
async def check_alerts():
    """
    Tüm alertleri kontrol et ve tetiklenen alertleri döndür
    
    Frontend polling için kullanılır (30 saniyede bir)
    Vercel timeout'unu önlemek için optimize edildi
    """
    try:
        # Önce aktif alertleri kontrol et - yoksa hızlıca dön
        active_alerts = alert_manager.get_active_alerts()
        
        if not active_alerts:
            # Aktif alert yoksa hızlıca boş döndür
            return {
                "success": True,
                "triggered_count": 0,
                "triggered_alerts": []
            }
        
        # Maksimum 3 ticker kontrol et (Vercel 10s timeout)
        unique_tickers = list(set(alert['ticker'] for alert in active_alerts))[:3]
        
        # Tüm hisseler için güncel veriyi topla
        market_data = {}
        
        for ticker in unique_tickers:
            try:
                # Sadece fiyat verisini al (hızlı)
                current_price = data_fetcher.get_current_price(ticker)
                
                market_data[ticker] = {
                    'price': current_price or 0,
                    'score': 0,  # Score hesaplaması yavaş, atla
                    'recommendation': ''
                }
            except Exception as e:
                logger.warning(f"Error fetching data for {ticker}: {e}")
                market_data[ticker] = {'price': 0, 'score': 0, 'recommendation': ''}
                continue
        
        # Alertleri kontrol et
        newly_triggered = alert_manager.check_all_alerts(market_data)
        
        # Daha önce tetiklenen alertleri de al
        all_triggered = alert_manager.get_triggered_alerts(clear=True)
        
        return {
            "success": True,
            "triggered_count": len(all_triggered),
            "triggered_alerts": all_triggered
        }
    
    except Exception as e:
        logger.error(f"Error checking alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{alert_id}")
async def delete_alert(alert_id: str):
    """Alert sil"""
    try:
        success = alert_manager.delete_alert(alert_id)
        
        if success:
            return {
                "success": True,
                "message": "Alert deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{alert_id}/toggle")
async def toggle_alert(alert_id: str, active: bool):
    """Alert'i aktif/pasif yap"""
    try:
        success = alert_manager.toggle_alert(alert_id, active)
        
        if success:
            return {
                "success": True,
                "message": f"Alert {'activated' if active else 'deactivated'} successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_notification_history(
    limit: int = 50,
    unread_only: bool = False
):
    """Bildirim geçmişini getir"""
    try:
        history = alert_manager.get_notification_history(
            limit=limit,
            unread_only=unread_only
        )
        
        return {
            "success": True,
            "count": len(history),
            "notifications": history
        }
    
    except Exception as e:
        logger.error(f"Error getting notification history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/{alert_id}/read")
async def mark_notification_read(alert_id: str):
    """Bildirimi okundu olarak işaretle"""
    try:
        success = alert_manager.mark_notification_read(alert_id)
        
        if success:
            return {
                "success": True,
                "message": "Notification marked as read"
            }
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/read-all")
async def mark_all_read():
    """Tüm bildirimleri okundu işaretle"""
    try:
        count = alert_manager.mark_all_read()
        
        return {
            "success": True,
            "marked_count": count,
            "message": f"{count} notifications marked as read"
        }
    
    except Exception as e:
        logger.error(f"Error marking all notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/clear")
async def clear_notification_history(days: Optional[int] = None):
    """Bildirim geçmişini temizle"""
    try:
        count = alert_manager.clear_history(days=days)
        
        return {
            "success": True,
            "cleared_count": count,
            "message": f"{count} notifications cleared"
        }
    
    except Exception as e:
        logger.error(f"Error clearing notification history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_alert_statistics():
    """Bildirim istatistiklerini getir"""
    try:
        stats = alert_manager.get_statistics()
        
        return {
            "success": True,
            "statistics": stats
        }
    
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
