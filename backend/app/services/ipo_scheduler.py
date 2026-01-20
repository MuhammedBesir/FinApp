"""
IPO Scheduler - Otomatik Güncelleme Zamanlayıcısı
APScheduler kullanarak IPO verilerini belirli aralıklarla günceller
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED

logger = logging.getLogger(__name__)

class IPOScheduler:
    """
    IPO verilerini otomatik güncelleyen zamanlayıcı
    
    Güncelleme zamanları:
    - Her gün saat 08:00 (piyasa açılmadan önce)
    - Her gün saat 18:00 (piyasa kapandıktan sonra)
    - Her 6 saatte bir yedek güncelleme
    """
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.is_running = False
        self._update_callback: Optional[Callable] = None
        self._last_run: Optional[datetime] = None
        self._run_count = 0
        self._error_count = 0
    
    def setup(self, update_callback: Callable):
        """
        Scheduler'ı kur
        
        Args:
            update_callback: Güncelleme yapılacak async fonksiyon
        """
        self._update_callback = update_callback
        
        # Scheduler oluştur
        self.scheduler = AsyncIOScheduler(
            timezone='Europe/Istanbul',
            job_defaults={
                'coalesce': True,  # Kaçırılan işleri birleştir
                'max_instances': 1,  # Aynı anda tek instance
                'misfire_grace_time': 3600  # 1 saat tolerans
            }
        )
        
        # Event listener ekle
        self.scheduler.add_listener(self._job_event_listener, 
                                     EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED)
        
        # Zamanlanmış görevleri ekle
        self._add_scheduled_jobs()
        
        logger.info("IPO Scheduler configured")
    
    def _add_scheduled_jobs(self):
        """Zamanlanmış görevleri ekle"""
        if not self.scheduler:
            return
        
        # 1. Sabah güncellemesi - Her gün 08:00 (piyasa öncesi)
        self.scheduler.add_job(
            self._run_update,
            CronTrigger(hour=8, minute=0),
            id='ipo_morning_update',
            name='IPO Sabah Güncellemesi',
            replace_existing=True
        )
        
        # 2. Akşam güncellemesi - Her gün 18:30 (piyasa sonrası)
        self.scheduler.add_job(
            self._run_update,
            CronTrigger(hour=18, minute=30),
            id='ipo_evening_update',
            name='IPO Akşam Güncellemesi',
            replace_existing=True
        )
        
        # 3. Gece güncellemesi - Her gün 00:30 
        self.scheduler.add_job(
            self._run_update,
            CronTrigger(hour=0, minute=30),
            id='ipo_midnight_update',
            name='IPO Gece Güncellemesi',
            replace_existing=True
        )
        
        # 4. Yedek güncelleme - Her 4 saatte bir
        self.scheduler.add_job(
            self._run_update_if_stale,
            IntervalTrigger(hours=4),
            id='ipo_backup_update',
            name='IPO Yedek Güncelleme',
            replace_existing=True
        )
        
        # 5. Hafta sonu özel - Cumartesi 10:00 (hafta sonu özeti)
        self.scheduler.add_job(
            self._run_update,
            CronTrigger(day_of_week='sat', hour=10, minute=0),
            id='ipo_weekend_summary',
            name='IPO Hafta Sonu Özeti',
            replace_existing=True
        )
        
        logger.info("Added 5 scheduled jobs for IPO updates")
    
    async def _run_update(self):
        """Güncelleme işlemini çalıştır"""
        if not self._update_callback:
            logger.warning("No update callback configured")
            return
        
        try:
            logger.info("Running scheduled IPO update...")
            start_time = datetime.now()
            
            # Callback'i çağır
            result = await self._update_callback()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            self._last_run = datetime.now()
            self._run_count += 1
            
            logger.info(f"IPO update completed in {elapsed:.2f}s (run #{self._run_count})")
            return result
            
        except Exception as e:
            self._error_count += 1
            logger.error(f"Error in scheduled IPO update: {e} (error #{self._error_count})")
            raise
    
    async def _run_update_if_stale(self):
        """Veri eskiyse güncelle"""
        # Son güncelleme 3 saatten eskiyse güncelle
        if self._last_run is None or (datetime.now() - self._last_run) > timedelta(hours=3):
            logger.info("Data is stale, running backup update...")
            await self._run_update()
        else:
            logger.debug("Data is fresh, skipping backup update")
    
    def _job_event_listener(self, event):
        """Job event'lerini dinle"""
        if event.exception:
            logger.error(f"Job {event.job_id} failed: {event.exception}")
        elif hasattr(event, 'job_id'):
            if 'error' in str(event).lower():
                logger.warning(f"Job event: {event}")
    
    def start(self):
        """Scheduler'ı başlat"""
        if self.scheduler and not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("IPO Scheduler started")
            
            # Başlangıçta bir güncelleme yap
            asyncio.create_task(self._initial_update())
    
    async def _initial_update(self):
        """Başlangıç güncellemesi"""
        try:
            # 5 saniye bekle (uygulama başlasın)
            await asyncio.sleep(5)
            logger.info("Running initial IPO update on startup...")
            await self._run_update()
        except Exception as e:
            logger.error(f"Initial update failed: {e}")
    
    def stop(self):
        """Scheduler'ı durdur"""
        if self.scheduler and self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("IPO Scheduler stopped")
    
    def get_status(self) -> dict:
        """Scheduler durumunu döndür"""
        jobs = []
        if self.scheduler:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })
        
        return {
            'is_running': self.is_running,
            'last_run': self._last_run.isoformat() if self._last_run else None,
            'run_count': self._run_count,
            'error_count': self._error_count,
            'jobs': jobs
        }
    
    def trigger_manual_update(self):
        """Manuel güncelleme tetikle"""
        if self._update_callback:
            asyncio.create_task(self._run_update())
            return True
        return False
    
    def reschedule_job(self, job_id: str, hour: int, minute: int = 0):
        """Bir job'ı yeniden zamanla"""
        if self.scheduler:
            try:
                self.scheduler.reschedule_job(
                    job_id,
                    trigger=CronTrigger(hour=hour, minute=minute)
                )
                logger.info(f"Rescheduled job {job_id} to {hour:02d}:{minute:02d}")
                return True
            except Exception as e:
                logger.error(f"Failed to reschedule job {job_id}: {e}")
        return False


# Global scheduler instance
_scheduler: Optional[IPOScheduler] = None

def get_scheduler() -> IPOScheduler:
    """Global scheduler instance döndür"""
    global _scheduler
    if _scheduler is None:
        _scheduler = IPOScheduler()
    return _scheduler


def setup_ipo_scheduler(update_callback: Callable):
    """IPO scheduler'ı kur ve başlat"""
    scheduler = get_scheduler()
    scheduler.setup(update_callback)
    return scheduler


def start_ipo_scheduler():
    """IPO scheduler'ı başlat"""
    scheduler = get_scheduler()
    scheduler.start()


def stop_ipo_scheduler():
    """IPO scheduler'ı durdur"""
    scheduler = get_scheduler()
    scheduler.stop()
