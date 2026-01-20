"""
Test script for IPO notification system
"""
import asyncio
import sys
from pathlib import Path

# Backend klasörünü path'e ekle
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.ipo_service import IPOService, IPOCompany, IPOStatus, IPOType
from app.services.alert_manager import AlertManager
from datetime import datetime

async def test_ipo_notification():
    """Yeni IPO bildirimini test et"""
    
    print("🧪 IPO Bildirim Sistemi Test Ediliyor...\n")
    
    # IPO Service'i başlat
    ipo_service = IPOService()
    alert_manager = AlertManager()
    
    print(f"📊 Mevcut IPO sayısı: {len(ipo_service.ipos)}")
    print(f"🔔 Mevcut alert sayısı: {len(alert_manager.alerts)}\n")
    
    # Test IPO oluştur
    test_ipo = IPOCompany(
        id="test_ipo_001",
        symbol="TEST",
        name="Test Teknoloji A.Ş.",
        sector="Teknoloji",
        description="Test amaçlı örnek halka arz",
        ipo_type=IPOType.PRIMARY,
        status=IPOStatus.ACTIVE,
        price_range_min=10.0,
        price_range_max=12.0,
        demand_start=datetime.now(),
        demand_end=datetime.now()
    )
    
    print(f"✨ Test IPO oluşturuldu: {test_ipo.name} ({test_ipo.symbol})")
    
    # Manuel bildirim tetikleme
    ipo_service._notify_new_ipo(test_ipo)
    
    print(f"\n🔔 Yeni alert sayısı: {len(alert_manager.alerts)}")
    print(f"📋 Tetiklenen alertler: {len(alert_manager.triggered_alerts)}")
    print(f"📜 Bildirim geçmişi: {len(alert_manager.notification_history)}")
    
    # Son bildirimi göster
    if alert_manager.notification_history:
        last_notif = alert_manager.notification_history[0]
        print(f"\n📬 Son Bildirim:")
        print(f"   Ticker: {last_notif['ticker']}")
        print(f"   Mesaj: {last_notif['message']}")
        print(f"   Öncelik: {last_notif['priority']}")
        print(f"   Durum: {'Okundu' if last_notif.get('read') else 'Okunmadı'}")
    
    # İstatistikleri göster
    stats = alert_manager.get_statistics()
    print(f"\n📊 İstatistikler:")
    print(f"   Toplam Alert: {stats['total_alerts']}")
    print(f"   Aktif Alert: {stats['active_alerts']}")
    print(f"   Bugün Tetiklenen: {stats['triggered_today']}")
    print(f"   Okunmamış: {stats['unread_count']}")
    
    print("\n✅ Test tamamlandı!")

if __name__ == "__main__":
    asyncio.run(test_ipo_notification())
