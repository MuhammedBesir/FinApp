"""
Stock Screening Scheduler - Günlük Hisse Tarama Zamanlayıcısı
Her gün piyasa kapandıktan sonra (18:30) otomatik tarama yapar
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED

logger = logging.getLogger(__name__)

# Data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DAILY_PICKS_FILE = DATA_DIR / "daily_picks.json"


class StockScheduler:
    """
    Günlük hisse tarama zamanlayıcısı
    
    BIST piyasa saatleri: 10:00 - 18:00 (Türkiye saati)
    
    Tarama zamanı:
    - Her gün saat 18:30 (piyasa kapandıktan 30 dakika sonra)
    """
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.is_running = False
        self._scan_callback: Optional[Callable] = None
        self._last_run: Optional[datetime] = None
        self._last_result: Optional[Dict] = None
        self._run_count = 0
        self._error_count = 0
    
    def setup(self, scan_callback: Callable):
        """
        Scheduler'ı kur
        
        Args:
            scan_callback: Tarama yapılacak async fonksiyon
        """
        self._scan_callback = scan_callback
        
        # Scheduler oluştur
        self.scheduler = AsyncIOScheduler(
            timezone='Europe/Istanbul',
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 3600  # 1 saat tolerans
            }
        )
        
        # Event listener ekle
        self.scheduler.add_listener(
            self._job_event_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED
        )
        
        # Zamanlanmış görevi ekle
        self._add_scheduled_job()
        
        logger.info("📊 Stock Scheduler configured - Daily scan at 18:30")
    
    def _add_scheduled_job(self):
        """Zamanlanmış görevi ekle"""
        if not self.scheduler:
            return
        
        # Piyasa kapanışından 30 dk sonra - Her gün 18:30
        self.scheduler.add_job(
            self._run_scan,
            CronTrigger(hour=18, minute=30),
            id='daily_stock_scan',
            name='Günlük Hisse Taraması',
            replace_existing=True
        )
        
        logger.info("📅 Daily stock scan scheduled at 18:30 (Europe/Istanbul)")
    
    def _job_event_listener(self, event):
        """Job event listener"""
        if event.exception:
            self._error_count += 1
            logger.error(f"❌ Stock scan job failed: {event.exception}")
        else:
            logger.info(f"✅ Stock scan job completed successfully")
    
    async def _run_scan(self):
        """Tarama çalıştır ve sonuçları kaydet"""
        logger.info("🔄 Starting scheduled stock scan...")
        
        try:
            if self._scan_callback:
                result = await self._scan_callback()
                self._last_run = datetime.now()
                self._last_result = result
                self._run_count += 1
                
                # Sonuçları JSON dosyasına kaydet
                await self._save_daily_picks(result)
                
                logger.info(f"✅ Stock scan completed - {len(result.get('picks', []))} picks saved")
                return result
            else:
                logger.warning("⚠️ No scan callback configured")
                return None
                
        except Exception as e:
            self._error_count += 1
            logger.error(f"❌ Stock scan failed: {e}")
            raise
    
    async def _save_daily_picks(self, result: Dict):
        """Günlük önerileri JSON dosyasına kaydet"""
        try:
            # Mevcut veriyi oku
            history = []
            if DAILY_PICKS_FILE.exists():
                try:
                    with open(DAILY_PICKS_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        history = data.get('history', [])
                except:
                    history = []
            
            # Bugünün tarihini al
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Bugünün verisini hazırla
            today_data = {
                "date": today,
                "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "picks": result.get('picks', []),
                "total_picks": len(result.get('picks', [])),
                "market_warnings": result.get('market_warnings', []),
                "strategy_version": "v4_optimized"
            }
            
            # Aynı günün verisi varsa güncelle, yoksa ekle
            updated = False
            for i, h in enumerate(history):
                if h.get('date') == today:
                    history[i] = today_data
                    updated = True
                    break
            
            if not updated:
                history.append(today_data)
            
            # Son 30 günü tut
            history = sorted(history, key=lambda x: x['date'], reverse=True)[:30]
            
            # Dosyaya kaydet
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            output = {
                "last_update": datetime.now().isoformat(),
                "latest": today_data,
                "history": history
            }
            
            with open(DAILY_PICKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Daily picks saved to {DAILY_PICKS_FILE}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save daily picks: {e}")
            raise
    
    def start(self):
        """Scheduler'ı başlat"""
        if self.scheduler and not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("🚀 Stock Scheduler started")
    
    def stop(self):
        """Scheduler'ı durdur"""
        if self.scheduler and self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("🛑 Stock Scheduler stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Scheduler durumunu döndür"""
        next_run = None
        if self.scheduler:
            job = self.scheduler.get_job('daily_stock_scan')
            if job and job.next_run_time:
                next_run = job.next_run_time.isoformat()
        
        return {
            "is_running": self.is_running,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "next_run": next_run,
            "run_count": self._run_count,
            "error_count": self._error_count,
            "schedule": "Daily at 18:30 (Europe/Istanbul)"
        }
    
    async def run_now(self) -> Dict:
        """Manuel olarak taramayı şimdi çalıştır"""
        logger.info("🔄 Running manual stock scan...")
        return await self._run_scan()
    
    def get_latest_picks(self) -> Optional[Dict]:
        """Kaydedilmiş son günlük önerileri döndür"""
        try:
            if DAILY_PICKS_FILE.exists():
                with open(DAILY_PICKS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('latest')
            return None
        except Exception as e:
            logger.error(f"Error reading daily picks: {e}")
            return None
    
    def get_picks_history(self, days: int = 7) -> List[Dict]:
        """Son N günün öneri geçmişini döndür"""
        try:
            if DAILY_PICKS_FILE.exists():
                with open(DAILY_PICKS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    history = data.get('history', [])
                    return history[:days]
            return []
        except Exception as e:
            logger.error(f"Error reading picks history: {e}")
            return []


# Global instance
stock_scheduler = StockScheduler()


def setup_stock_scheduler(scan_callback: Callable):
    """Stock scheduler'ı kur"""
    stock_scheduler.setup(scan_callback)


def start_stock_scheduler():
    """Stock scheduler'ı başlat"""
    stock_scheduler.start()


def stop_stock_scheduler():
    """Stock scheduler'ı durdur"""
    stock_scheduler.stop()
