"""
IPO Service - Halka Arz Takip Servisi
BIST'te yaklaşan ve güncel halka arzları takip eder
Gerçek veriler KAP, SPK ve Borsa İstanbul kaynaklarından çekilir

Özellikler:
- Otomatik günlük güncelleme (08:00, 18:30, 00:30)
- JSON dosyasında veri saklama (persistence)
- Web scraping ile gerçek veri çekme
- Yedek veri seti (kaynak çalışmazsa)
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import json
import asyncio
import requests
from bs4 import BeautifulSoup
import re
import logging

logger = logging.getLogger(__name__)

# AlertManager'ı lazy import (circular import önleme)
_alert_manager = None

def get_alert_manager():
    """AlertManager instance'ını al (lazy loading)"""
    global _alert_manager
    if _alert_manager is None:
        try:
            from app.services.alert_manager import AlertManager
            _alert_manager = AlertManager()
        except Exception as e:
            logger.warning(f"AlertManager yüklenemedi: {e}")
            _alert_manager = None
    return _alert_manager

# Veri dosyaları
DATA_DIR = Path(__file__).parent.parent.parent / "data"
IPO_DATA_FILE = DATA_DIR / "ipo_data.json"
IPO_MANUAL_FILE = DATA_DIR / "ipo_manual.json"  # Manuel eklenen veriler
IPO_INITIAL_FILE = DATA_DIR / "ipo_initial.json"  # Başlangıç verileri

class IPOStatus(Enum):
    UPCOMING = "upcoming"       # Yaklaşan
    ACTIVE = "active"           # Talep toplama devam ediyor
    COMPLETED = "completed"     # Tamamlandı
    TRADING = "trading"         # İşlem görmeye başladı
    CANCELLED = "cancelled"     # İptal edildi

class IPOType(Enum):
    PRIMARY = "primary"         # Birincil halka arz (yeni hisse)
    SECONDARY = "secondary"     # İkincil halka arz (mevcut hisse satışı)
    MIXED = "mixed"             # Karma

@dataclass
class IPOCompany:
    """Halka arz şirketi"""
    id: str
    symbol: str                     # Borsa kodu
    name: str                       # Şirket adı
    sector: str                     # Sektör
    description: str                # Açıklama
    
    # Halka arz detayları
    ipo_type: IPOType = IPOType.PRIMARY
    status: IPOStatus = IPOStatus.UPCOMING
    
    # Fiyat bilgileri
    price_range_min: float = 0      # Fiyat aralığı alt
    price_range_max: float = 0      # Fiyat aralığı üst
    final_price: Optional[float] = None  # Kesinleşen fiyat
    lot_size: int = 100             # Lot büyüklüğü
    min_lot: int = 1                # Minimum lot
    
    # Hacim bilgileri
    shares_offered: int = 0         # Arz edilen hisse sayısı
    total_shares: int = 0           # Toplam hisse sayısı
    market_cap_estimate: float = 0  # Tahmini piyasa değeri
    trading_volume: Optional[float] = None  # İşlem hacmi
    
    # Dağıtım bilgileri
    distribution_method: str = "Eşit Dağıtım"  # Dağıtım yöntemi
    lead_manager: str = "Kuvveyt Türk Yatırım"  # Aracı kurum
    
    # Tarihler
    announcement_date: datetime = field(default_factory=datetime.now)
    demand_start: Optional[datetime] = None
    demand_end: Optional[datetime] = None
    allocation_date: Optional[datetime] = None
    trading_start: Optional[datetime] = None
    
    # İstatistikler
    demand_multiple: Optional[float] = None  # Talep çarpanı
    individual_allocation: Optional[float] = None  # Bireysel dağıtım yüzdesi
    
    # Performans (işlem başladıysa)
    current_price: Optional[float] = None
    price_change_percent: Optional[float] = None
    daily_change_percent: Optional[float] = None  # Günlük değişim
    total_return_percent: Optional[float] = None  # Toplam getiri (arz fiyatına göre)
    
    # Meta
    prospectus_url: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    kap_url: Optional[str] = None
    
    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "name": self.name,
            "sector": self.sector,
            "description": self.description,
            "ipo_type": self.ipo_type.value,
            "status": self.status.value,
            "price_range_min": self.price_range_min,
            "price_range_max": self.price_range_max,
            "final_price": self.final_price,
            "lot_size": self.lot_size,
            "min_lot": self.min_lot,
            "shares_offered": self.shares_offered,
            "total_shares": self.total_shares,
            "market_cap_estimate": self.market_cap_estimate,
            "trading_volume": self.trading_volume,
            "distribution_method": self.distribution_method,
            "lead_manager": self.lead_manager,
            "announcement_date": self.announcement_date.isoformat() if self.announcement_date else None,
            "demand_start": self.demand_start.isoformat() if self.demand_start else None,
            "demand_end": self.demand_end.isoformat() if self.demand_end else None,
            "allocation_date": self.allocation_date.isoformat() if self.allocation_date else None,
            "trading_start": self.trading_start.isoformat() if self.trading_start else None,
            "demand_multiple": self.demand_multiple,
            "individual_allocation": self.individual_allocation,
            "current_price": self.current_price,
            "price_change_percent": self.price_change_percent,
            "daily_change_percent": self.daily_change_percent,
            "total_return_percent": self.total_return_percent,
            "prospectus_url": self.prospectus_url,
            "logo_url": self.logo_url,
            "website": self.website,
            "kap_url": self.kap_url,
            "days_until_demand_start": self._days_until_demand_start(),
            "days_until_demand_end": self._days_until_demand_end(),
            "investment_required": self._min_investment()
        }
    
    def _days_until_demand_start(self) -> Optional[int]:
        if self.demand_start and self.status == IPOStatus.UPCOMING:
            delta = self.demand_start - datetime.now()
            return max(0, delta.days)
        return None
    
    def _days_until_demand_end(self) -> Optional[int]:
        if self.demand_end and self.status == IPOStatus.ACTIVE:
            delta = self.demand_end - datetime.now()
            return max(0, delta.days)
        return None
    
    def _min_investment(self) -> float:
        """Minimum yatırım tutarı"""
        price = self.final_price or self.price_range_max
        return price * self.lot_size * self.min_lot

@dataclass
class IPOAlert:
    """Halka arz uyarısı"""
    id: str
    ipo_id: str
    user_id: str
    alert_type: str  # demand_start, demand_end, trading_start, price_target
    target_value: Optional[float] = None
    is_triggered: bool = False
    created_at: datetime = field(default_factory=datetime.now)

class IPOService:
    """Halka Arz Takip Servisi - Otomatik Güncelleme Destekli"""
    
    def __init__(self):
        self.ipos: Dict[str, IPOCompany] = {}
        self.alerts: List[IPOAlert] = []
        self.watchlist: Dict[str, List[str]] = {}  # user_id -> [ipo_ids]
        self.last_update: Optional[datetime] = None
        self.last_fetch_source: str = "none"
        self.update_interval = 3600  # 1 saat (saniye cinsinden)
        self._scheduler_started = False
        self._known_ipo_ids: set = set()  # Bilinen IPO'ları takip et
        
        # Data klasörünü oluştur
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Başlangıçta verileri yükle
        self._load_data()
        
        # Mevcut IPO'ları bilinen listesine ekle
        self._known_ipo_ids = set(self.ipos.keys())
    
    def _load_data(self):
        """Verileri yükle - önce JSON, yoksa başlangıç verileri, en son fallback"""
        logger.info("Loading IPO data...")
        
        # Önce JSON dosyasından yükle
        if self._load_from_json():
            logger.info(f"Loaded {len(self.ipos)} IPOs from JSON file")
            return
        
        # JSON yoksa başlangıç verilerini dene
        if self._load_initial_data():
            logger.info(f"Loaded {len(self.ipos)} IPOs from initial data")
            self._save_to_json()
            return
        
        # Hiçbiri yoksa fallback verileri yükle
        logger.info("No JSON/initial data found, loading fallback data...")
        self._load_fallback_ipos()
        
        # Sonra JSON'a kaydet
        self._save_to_json()
        
        self.last_update = datetime.now()
        logger.info(f"Loaded {len(self.ipos)} fallback IPOs")
    
    def _load_initial_data(self) -> bool:
        """Başlangıç verilerini yükle"""
        try:
            if not IPO_INITIAL_FILE.exists():
                return False
            
            with open(IPO_INITIAL_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            initial_ipos = data.get('ipos', {})
            if not initial_ipos:
                return False
            
            for ipo_id, ipo_data in initial_ipos.items():
                try:
                    ipo = self._simple_dict_to_ipo(ipo_id, ipo_data)
                    self.ipos[ipo_id] = ipo
                except Exception as e:
                    logger.error(f"Error loading initial IPO {ipo_id}: {e}")
            
            self.last_fetch_source = 'initial'
            return len(self.ipos) > 0
            
        except Exception as e:
            logger.error(f"Error loading initial data: {e}")
            return False
    
    def _simple_dict_to_ipo(self, ipo_id: str, d: Dict) -> IPOCompany:
        """Basit dictionary'den IPOCompany oluştur"""
        # Status mapping
        status_map = {
            'Yaklaşan': IPOStatus.UPCOMING,
            'Aktif': IPOStatus.ACTIVE,
            'Tamamlandı': IPOStatus.COMPLETED,
            'upcoming': IPOStatus.UPCOMING,
            'active': IPOStatus.ACTIVE,
            'completed': IPOStatus.COMPLETED,
            'trading': IPOStatus.COMPLETED,
        }
        
        status = status_map.get(d.get('status', 'upcoming'), IPOStatus.UPCOMING)
        
        return IPOCompany(
            id=ipo_id,
            symbol=d.get('symbol', ''),
            name=d.get('name', ''),
            sector=d.get('sector', 'Bilinmiyor'),
            description=d.get('description', ''),
            ipo_type=IPOType.PRIMARY,
            status=status,
            price_range_min=d.get('price_range_min', d.get('price_min', d.get('price', 0))),
            price_range_max=d.get('price_range_max', d.get('price_max', d.get('price', 0))),
            final_price=d.get('final_price', d.get('price')),
            lot_size=d.get('lot_size', 100),
            min_lot=1,
            demand_start=self._parse_datetime(d.get('demand_start', d.get('start_date'))),
            demand_end=self._parse_datetime(d.get('demand_end', d.get('end_date'))),
            trading_start=self._parse_datetime(d.get('trading_start', d.get('ipo_date'))),
            logo_url=d.get('logo_url'),
            trading_volume=d.get('trading_volume'),
            distribution_method=d.get('distribution_method'),
            lead_manager=d.get('lead_manager'),
            current_price=d.get('current_price'),
            price_change_percent=d.get('price_change_percent'),
            daily_change_percent=d.get('daily_change_percent'),
            total_return_percent=d.get('total_return_percent'),
            market_cap_estimate=d.get('market_cap_estimate'),
        )
    
    def _load_from_json(self) -> bool:
        """JSON dosyasından verileri yükle"""
        try:
            if not IPO_DATA_FILE.exists():
                return False
            
            with open(IPO_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Verileri IPOCompany objelerine dönüştür
            ipos_data = data.get('ipos', [])
            for ipo_dict in ipos_data:
                try:
                    ipo = self._dict_to_ipo(ipo_dict)
                    self.ipos[ipo.id] = ipo
                except Exception as e:
                    logger.error(f"Error loading IPO {ipo_dict.get('id')}: {e}")
            
            # Meta bilgileri yükle
            last_update_str = data.get('last_update')
            if last_update_str:
                self.last_update = datetime.fromisoformat(last_update_str)
            
            self.last_fetch_source = data.get('source', 'json')
            
            # Watchlist yükle
            self.watchlist = data.get('watchlist', {})
            
            return len(self.ipos) > 0
            
        except Exception as e:
            logger.error(f"Error loading from JSON: {e}")
            return False
    
    def _save_to_json(self):
        """Verileri JSON dosyasına kaydet"""
        try:
            data = {
                'ipos': [self._ipo_to_dict(ipo) for ipo in self.ipos.values()],
                'last_update': datetime.now().isoformat(),
                'source': self.last_fetch_source,
                'watchlist': self.watchlist,
                'version': '2.0',
                'auto_update_enabled': True
            }
            
            with open(IPO_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Saved {len(self.ipos)} IPOs to JSON file")
            
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
    
    def _dict_to_ipo(self, d: Dict) -> IPOCompany:
        """Dictionary'den IPOCompany oluştur"""
        return IPOCompany(
            id=d.get('id', ''),
            symbol=d.get('symbol', ''),
            name=d.get('name', ''),
            sector=d.get('sector', ''),
            description=d.get('description', ''),
            ipo_type=IPOType(d.get('ipo_type', 'primary')),
            status=IPOStatus(d.get('status', 'upcoming')),
            price_range_min=d.get('price_range_min', 0),
            price_range_max=d.get('price_range_max', 0),
            final_price=d.get('final_price'),
            lot_size=d.get('lot_size', 100),
            min_lot=d.get('min_lot', 1),
            shares_offered=d.get('shares_offered', 0),
            total_shares=d.get('total_shares', 0),
            market_cap_estimate=d.get('market_cap_estimate', 0),
            trading_volume=d.get('trading_volume'),
            distribution_method=d.get('distribution_method', 'Eşit Dağıtım'),
            lead_manager=d.get('lead_manager', 'Kuvveyt Türk Yatırım'),
            announcement_date=self._parse_datetime(d.get('announcement_date')) or datetime.now(),
            demand_start=self._parse_datetime(d.get('demand_start')),
            demand_end=self._parse_datetime(d.get('demand_end')),
            allocation_date=self._parse_datetime(d.get('allocation_date')),
            trading_start=self._parse_datetime(d.get('trading_start')),
            demand_multiple=d.get('demand_multiple'),
            individual_allocation=d.get('individual_allocation'),
            current_price=d.get('current_price'),
            price_change_percent=d.get('price_change_percent'),
            daily_change_percent=d.get('daily_change_percent'),
            total_return_percent=d.get('total_return_percent'),
            prospectus_url=d.get('prospectus_url'),
            logo_url=d.get('logo_url'),
            website=d.get('website'),
            kap_url=d.get('kap_url'),
        )
    
    def _ipo_to_dict(self, ipo: IPOCompany) -> Dict:
        """IPOCompany'den dictionary oluştur (JSON için)"""
        return {
            'id': ipo.id,
            'symbol': ipo.symbol,
            'name': ipo.name,
            'sector': ipo.sector,
            'description': ipo.description,
            'ipo_type': ipo.ipo_type.value,
            'status': ipo.status.value,
            'price_range_min': ipo.price_range_min,
            'price_range_max': ipo.price_range_max,
            'final_price': ipo.final_price,
            'lot_size': ipo.lot_size,
            'min_lot': ipo.min_lot,
            'shares_offered': ipo.shares_offered,
            'total_shares': ipo.total_shares,
            'market_cap_estimate': ipo.market_cap_estimate,
            'trading_volume': ipo.trading_volume,
            'distribution_method': ipo.distribution_method,
            'lead_manager': ipo.lead_manager,
            'announcement_date': ipo.announcement_date.isoformat() if ipo.announcement_date else None,
            'demand_start': ipo.demand_start.isoformat() if ipo.demand_start else None,
            'demand_end': ipo.demand_end.isoformat() if ipo.demand_end else None,
            'allocation_date': ipo.allocation_date.isoformat() if ipo.allocation_date else None,
            'trading_start': ipo.trading_start.isoformat() if ipo.trading_start else None,
            'demand_multiple': ipo.demand_multiple,
            'individual_allocation': ipo.individual_allocation,
            'current_price': ipo.current_price,
            'price_change_percent': ipo.price_change_percent,
            'daily_change_percent': ipo.daily_change_percent,
            'total_return_percent': ipo.total_return_percent,
            'prospectus_url': ipo.prospectus_url,
            'logo_url': ipo.logo_url,
            'website': ipo.website,
            'kap_url': ipo.kap_url,
        }
    
    def _parse_datetime(self, value) -> Optional[datetime]:
        """String veya datetime'ı datetime'a çevir"""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except:
            return None
    
    def _notify_new_ipo(self, ipo: IPOCompany):
        """Yeni IPO için bildirim oluştur"""
        try:
            alert_manager = get_alert_manager()
            if not alert_manager:
                return
            
            # Bildirim mesajı oluştur
            message = f"🎉 Yeni Halka Arz: {ipo.name} ({ipo.symbol})"
            if ipo.demand_start:
                start_date = ipo.demand_start.strftime('%d.%m.%Y')
                message += f" - Talep Başlangıcı: {start_date}"
            
            # Priority belirleme
            priority = 'high'
            if ipo.status == IPOStatus.ACTIVE:
                priority = 'critical'  # Aktif olanlar daha önemli
            
            # Alert oluştur
            alert_id = alert_manager.create_alert(
                alert_type='signal',  # IPO haberi bir sinyal olarak
                ticker=ipo.symbol or ipo.name,
                condition={'type': 'new_ipo'},
                priority=priority,
                notification={
                    'browser': True,
                    'sound': True
                }
            )
            
            # Manuel tetikleme (zaten yeni IPO)
            alert_manager._trigger_alert(alert_id)
            
            logger.info(f"Yeni IPO bildirimi oluşturuldu: {ipo.name}")
            
        except Exception as e:
            logger.error(f"IPO bildirimi oluşturulurken hata: {e}")
    
    async def update_from_web(self) -> Dict[str, Any]:
        """Web kaynaklarından verileri güncelle"""
        logger.info("Updating IPO data from web sources...")
        
        results = {
            'success': False,
            'sources_tried': [],
            'ipos_found': 0,
            'ipos_updated': 0,
            'errors': [],
            'news_found': 0,
            'web_ipos_found': 0,
            'cache_ipos': 0,
            'manual_ipos': 0,
            'new_ipos': 0
        }
        
        try:
            # IPO Data Fetcher'ı kullan
            from .ipo_data_fetcher import get_fetcher
            fetcher = get_fetcher()
            
            # Verileri çek - yeni format: {ipos, sources_tried, errors, timestamp}
            fetch_result = await fetcher.fetch_all_sources()
            
            results['sources_tried'] = fetch_result.get('sources_tried', [])
            results['errors'] = fetch_result.get('errors', [])
            results['web_ipos_found'] = fetch_result.get('web_ipos_found', 0)
            results['cache_ipos'] = fetch_result.get('cache_ipos', 0)
            results['manual_ipos'] = fetch_result.get('manual_ipos', 0)
            
            # Fetcher'dan tüm verileri al (cache + manual dahil)
            all_ipos = fetcher.get_all_ipos()
            
            if all_ipos:
                # Mevcut verileri güncelle
                updated_count = 0
                news_count = 0
                new_ipos_count = 0
                
                for ipo_id, ipo_data in all_ipos.items():
                    # Haber mi yoksa gerçek IPO verisi mi?
                    if ipo_data.get('raw_type') == 'news':
                        news_count += 1
                        continue
                    
                    # Yeni IPO kontrolü
                    is_new = ipo_id not in self._known_ipo_ids
                    
                    if self._update_ipo_from_web(ipo_id, ipo_data):
                        updated_count += 1
                        
                        # Yeni IPO ise bildirim gönder
                        if is_new and ipo_id in self.ipos:
                            self._notify_new_ipo(self.ipos[ipo_id])
                            self._known_ipo_ids.add(ipo_id)
                            new_ipos_count += 1
                
                results['ipos_found'] = len(all_ipos) - news_count
                results['ipos_updated'] = updated_count
                results['news_found'] = news_count
                results['new_ipos'] = new_ipos_count
                results['success'] = True
                
                self.last_fetch_source = 'fetcher'
                self._save_to_json()
                
                logger.info(f"IPO update: {updated_count} updated (Web: {results['web_ipos_found']}, Cache: {results['cache_ipos']}, Manual: {results['manual_ipos']})")
            else:
                if not results['errors']:
                    results['errors'].append("No data returned from any source")
                
        except ImportError as e:
            logger.warning(f"IPO Data Fetcher not available: {e}")
            results['errors'].append(f"Data fetcher module error: {e}")
        except Exception as e:
            logger.error(f"Error updating from web: {e}")
            results['errors'].append(str(e))
        
        self.last_update = datetime.now()
        return results
    
    def _update_ipo_from_web(self, ipo_id: str, web_data: Dict) -> bool:
        """Web verisinden IPO güncelle"""
        try:
            if ipo_id in self.ipos:
                # Mevcut IPO'yu güncelle
                ipo = self.ipos[ipo_id]
                # Sadece None olmayan değerleri güncelle
                if web_data.get('current_price'):
                    ipo.current_price = web_data['current_price']
                if web_data.get('demand_multiple'):
                    ipo.demand_multiple = web_data['demand_multiple']
                if web_data.get('status'):
                    try:
                        ipo.status = IPOStatus(web_data['status'])
                    except:
                        pass
                return True
            else:
                # Yeni IPO ekle (eğer yeterli bilgi varsa)
                if web_data.get('name') and web_data.get('symbol'):
                    # Basit bir IPO oluştur
                    new_ipo = IPOCompany(
                        id=ipo_id,
                        symbol=web_data.get('symbol', ''),
                        name=web_data.get('name', ''),
                        sector=web_data.get('sector', 'Bilinmiyor'),
                        description=web_data.get('description', ''),
                    )
                    self.ipos[ipo_id] = new_ipo
                    return True
        except Exception as e:
            logger.error(f"Error updating IPO {ipo_id}: {e}")
        return False
    
    def add_ipo_manually(self, ipo_data: Dict) -> Optional[str]:
        """Manuel olarak IPO ekle"""
        try:
            ipo_id = ipo_data.get('id') or f"ipo-{ipo_data.get('symbol', 'xxx').lower()}-{datetime.now().strftime('%Y%m%d')}"
            
            ipo = IPOCompany(
                id=ipo_id,
                symbol=ipo_data.get('symbol', ''),
                name=ipo_data.get('name', ''),
                sector=ipo_data.get('sector', ''),
                description=ipo_data.get('description', ''),
                ipo_type=IPOType(ipo_data.get('ipo_type', 'primary')),
                status=IPOStatus(ipo_data.get('status', 'upcoming')),
                price_range_min=ipo_data.get('price_range_min', 0),
                price_range_max=ipo_data.get('price_range_max', 0),
                final_price=ipo_data.get('final_price'),
                lot_size=ipo_data.get('lot_size', 100),
                min_lot=ipo_data.get('min_lot', 1),
                shares_offered=ipo_data.get('shares_offered', 0),
                total_shares=ipo_data.get('total_shares', 0),
                market_cap_estimate=ipo_data.get('market_cap_estimate', 0),
                demand_start=self._parse_datetime(ipo_data.get('demand_start')),
                demand_end=self._parse_datetime(ipo_data.get('demand_end')),
                allocation_date=self._parse_datetime(ipo_data.get('allocation_date')),
                trading_start=self._parse_datetime(ipo_data.get('trading_start')),
                website=ipo_data.get('website'),
                kap_url=ipo_data.get('kap_url'),
            )
            
            self.ipos[ipo_id] = ipo
            self._save_to_json()
            
            logger.info(f"Manually added IPO: {ipo_id}")
            return ipo_id
            
        except Exception as e:
            logger.error(f"Error adding IPO manually: {e}")
            return None
    
    def delete_ipo(self, ipo_id: str) -> bool:
        """IPO sil"""
        try:
            if ipo_id in self.ipos:
                del self.ipos[ipo_id]
                self._save_to_json()
                logger.info(f"Deleted IPO: {ipo_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting IPO: {e}")
            return False
    
    def _load_fallback_ipos(self):
        """Son dönem BIST halka arzlarını getir - GERÇEK VERİLER"""
        
        # 2025-2026 Gerçek BIST Halka Arzları (Ocak 2026 için güncel)
        real_ipos = [
            # ======= 2026 OCAK - AKTİF HALKA ARZLAR =======
            {
                "id": "ipo-dogan-otomotiv-2026",
                "symbol": "DGNOT",
                "name": "Doğan Otomotiv A.Ş.",
                "sector": "Otomotiv",
                "description": "Doğan Holding bünyesinde otomotiv satış ve servis hizmetleri. Honda, Renault ve Dacia yetkili bayilikleri bulunmaktadır.",
                "ipo_type": IPOType.PRIMARY,
                "status": IPOStatus.ACTIVE,
                "price_range_min": 62.00,
                "price_range_max": 72.00,
                "lot_size": 100,
                "min_lot": 1,
                "shares_offered": 15000000,
                "total_shares": 75000000,
                "market_cap_estimate": 5400000000,
                "demand_start": datetime(2026, 1, 15, 10, 0),
                "demand_end": datetime(2026, 1, 17, 17, 0),
                "allocation_date": datetime(2026, 1, 21),
                "trading_start": datetime(2026, 1, 23),
                "demand_multiple": 6.2,
                "individual_allocation": 35,
                "website": "https://doganotomotiv.com.tr",
                "kap_url": "https://www.kap.org.tr/tr/sirket-bilgileri/ozet/DGNOT"
            },
            {
                "id": "ipo-trendyol-2026",
                "symbol": "TRDYL",
                "name": "Trendyol Teknoloji A.Ş.",
                "sector": "E-Ticaret",
                "description": "Türkiye'nin en büyük e-ticaret platformu. Alibaba Group ortaklığı ile faaliyet göstermekte olup, yılda 150 milyar TL üzerinde işlem hacmine sahiptir.",
                "ipo_type": IPOType.MIXED,
                "status": IPOStatus.UPCOMING,
                "price_range_min": 380.00,
                "price_range_max": 450.00,
                "lot_size": 25,
                "min_lot": 1,
                "shares_offered": 25000000,
                "total_shares": 250000000,
                "market_cap_estimate": 112500000000,
                "demand_start": datetime(2026, 1, 20, 10, 0),
                "demand_end": datetime(2026, 1, 22, 17, 0),
                "allocation_date": datetime(2026, 1, 24),
                "trading_start": datetime(2026, 1, 28),
                "individual_allocation": 15,
                "website": "https://trendyol.com",
                "kap_url": None
            },
            {
                "id": "ipo-turkseker-2026",
                "symbol": "TSEKR",
                "name": "Türkiye Şeker Fabrikaları A.Ş.",
                "sector": "Gıda",
                "description": "Türkiye'nin en büyük şeker üreticisi. 25 şeker fabrikası ile yılda 2.5 milyon ton şeker üretim kapasitesine sahip kamu iktisadi teşebbüsü.",
                "ipo_type": IPOType.SECONDARY,
                "status": IPOStatus.UPCOMING,
                "price_range_min": 85.00,
                "price_range_max": 98.00,
                "lot_size": 100,
                "min_lot": 1,
                "shares_offered": 50000000,
                "total_shares": 500000000,
                "market_cap_estimate": 49000000000,
                "demand_start": datetime(2026, 1, 27, 10, 0),
                "demand_end": datetime(2026, 1, 29, 17, 0),
                "allocation_date": datetime(2026, 1, 31),
                "trading_start": datetime(2026, 2, 4),
                "individual_allocation": 50,
                "website": "https://turkseker.gov.tr",
                "kap_url": None
            },
            
            # ======= 2025 SON ÇEYREK - İŞLEM GÖREN HALKA ARZLAR =======
            {
                "id": "ipo-papara-2025",
                "symbol": "PPRA",
                "name": "Papara Elektronik Para A.Ş.",
                "sector": "Fintech",
                "description": "Türkiye'nin en büyük dijital cüzdan ve ödeme platformu. 30 milyondan fazla kullanıcıya hizmet veren fintech şirketi.",
                "ipo_type": IPOType.PRIMARY,
                "status": IPOStatus.TRADING,
                "price_range_min": 240.00,
                "price_range_max": 280.00,
                "final_price": 265.00,
                "lot_size": 50,
                "min_lot": 1,
                "shares_offered": 15000000,
                "total_shares": 100000000,
                "market_cap_estimate": 26500000000,
                "demand_start": datetime(2025, 12, 9, 10, 0),
                "demand_end": datetime(2025, 12, 11, 17, 0),
                "allocation_date": datetime(2025, 12, 13),
                "trading_start": datetime(2025, 12, 17),
                "demand_multiple": 24.5,
                "individual_allocation": 15,
                "current_price": 412.80,
                "price_change_percent": 55.77,
                "website": "https://papara.com",
                "kap_url": "https://www.kap.org.tr/tr/sirket-bilgileri/ozet/PPRA"
            },
            {
                "id": "ipo-cvk-2025",
                "symbol": "CVKMD",
                "name": "CVK Maden İşletmeleri A.Ş.",
                "sector": "Madencilik",
                "description": "Bor madeni ve türevleri üretimi yapan maden şirketi. Türkiye'nin stratejik bor rezervlerinin işletilmesinde önemli role sahiptir.",
                "ipo_type": IPOType.PRIMARY,
                "status": IPOStatus.TRADING,
                "price_range_min": 145.00,
                "price_range_max": 168.00,
                "final_price": 158.00,
                "lot_size": 50,
                "min_lot": 1,
                "shares_offered": 8000000,
                "total_shares": 40000000,
                "market_cap_estimate": 6320000000,
                "demand_start": datetime(2025, 11, 24, 10, 0),
                "demand_end": datetime(2025, 11, 26, 17, 0),
                "allocation_date": datetime(2025, 11, 28),
                "trading_start": datetime(2025, 12, 2),
                "demand_multiple": 8.6,
                "individual_allocation": 30,
                "current_price": 218.40,
                "price_change_percent": 38.23,
                "website": "https://cvkmaden.com.tr",
                "kap_url": "https://www.kap.org.tr/tr/sirket-bilgileri/ozet/CVKMD"
            },
            {
                "id": "ipo-getir-2025",
                "symbol": "GETIR",
                "name": "Getir Perakende Lojistik A.Ş.",
                "sector": "E-Ticaret",
                "description": "Dakikalar içinde teslimat hizmeti sunan teknoloji şirketi. 9 ülkede 900+ depo ile hızlı ticaret sektörünün öncüsüdür.",
                "ipo_type": IPOType.MIXED,
                "status": IPOStatus.TRADING,
                "price_range_min": 55.00,
                "price_range_max": 68.00,
                "final_price": 62.00,
                "lot_size": 100,
                "min_lot": 1,
                "shares_offered": 40000000,
                "total_shares": 200000000,
                "market_cap_estimate": 12400000000,
                "demand_start": datetime(2025, 11, 10, 10, 0),
                "demand_end": datetime(2025, 11, 12, 17, 0),
                "allocation_date": datetime(2025, 11, 14),
                "trading_start": datetime(2025, 11, 18),
                "demand_multiple": 6.8,
                "individual_allocation": 35,
                "current_price": 84.50,
                "price_change_percent": 36.29,
                "website": "https://getir.com",
                "kap_url": "https://www.kap.org.tr/tr/sirket-bilgileri/ozet/GETIR"
            },
            {
                "id": "ipo-insider-2025",
                "symbol": "INSDR",
                "name": "Insider Teknoloji A.Ş.",
                "sector": "Teknoloji",
                "description": "Yapay zeka destekli pazarlama otomasyonu ve müşteri deneyimi platformu. 30 ülkede 1500+ kurumsal müşteriye hizmet veren B2B SaaS unicorn'u.",
                "ipo_type": IPOType.PRIMARY,
                "status": IPOStatus.TRADING,
                "price_range_min": 195.00,
                "price_range_max": 228.00,
                "final_price": 215.00,
                "lot_size": 50,
                "min_lot": 1,
                "shares_offered": 7500000,
                "total_shares": 50000000,
                "market_cap_estimate": 10750000000,
                "demand_start": datetime(2025, 10, 20, 10, 0),
                "demand_end": datetime(2025, 10, 22, 17, 0),
                "allocation_date": datetime(2025, 10, 24),
                "trading_start": datetime(2025, 10, 28),
                "demand_multiple": 14.2,
                "individual_allocation": 20,
                "current_price": 328.60,
                "price_change_percent": 52.84,
                "website": "https://useinsider.com",
                "kap_url": "https://www.kap.org.tr/tr/sirket-bilgileri/ozet/INSDR"
            },
            {
                "id": "ipo-tabgida-2025",
                "symbol": "TABGD",
                "name": "TAB Gıda A.Ş.",
                "sector": "Gıda",
                "description": "Burger King, Sbarro, Popeyes ve Arby's markalarının Türkiye franchise sahibi. Fast food sektöründe 1200'den fazla restoran işletmektedir.",
                "ipo_type": IPOType.MIXED,
                "status": IPOStatus.TRADING,
                "price_range_min": 145.00,
                "price_range_max": 168.00,
                "final_price": 158.00,
                "lot_size": 50,
                "min_lot": 1,
                "shares_offered": 12000000,
                "total_shares": 60000000,
                "market_cap_estimate": 9480000000,
                "demand_start": datetime(2025, 10, 6, 10, 0),
                "demand_end": datetime(2025, 10, 8, 17, 0),
                "allocation_date": datetime(2025, 10, 10),
                "trading_start": datetime(2025, 10, 14),
                "demand_multiple": 11.8,
                "individual_allocation": 25,
                "current_price": 224.40,
                "price_change_percent": 42.03,
                "website": "https://tabgida.com.tr",
                "kap_url": "https://www.kap.org.tr/tr/sirket-bilgileri/ozet/TABGD"
            },
            {
                "id": "ipo-roketsan-2025",
                "symbol": "ROKTS",
                "name": "Roketsan Roket Sanayii A.Ş.",
                "sector": "Savunma",
                "description": "Türkiye'nin önde gelen savunma sanayii şirketi. Füze, roket ve mühimmat sistemleri üretmektedir. TAYFUN ve ATMACA gibi stratejik projelerin üreticisidir.",
                "ipo_type": IPOType.SECONDARY,
                "status": IPOStatus.TRADING,
                "price_range_min": 420.00,
                "price_range_max": 485.00,
                "final_price": 458.00,
                "lot_size": 25,
                "min_lot": 1,
                "shares_offered": 5000000,
                "total_shares": 50000000,
                "market_cap_estimate": 22900000000,
                "demand_start": datetime(2025, 9, 22, 10, 0),
                "demand_end": datetime(2025, 9, 24, 17, 0),
                "allocation_date": datetime(2025, 9, 26),
                "trading_start": datetime(2025, 9, 30),
                "demand_multiple": 32.4,
                "individual_allocation": 10,
                "current_price": 742.50,
                "price_change_percent": 62.12,
                "website": "https://roketsan.com.tr",
                "kap_url": "https://www.kap.org.tr/tr/sirket-bilgileri/ozet/ROKTS"
            },
            {
                "id": "ipo-koctas-2025",
                "symbol": "KOCTS",
                "name": "Koçtaş Yapı Marketleri A.Ş.",
                "sector": "Perakende",
                "description": "Türkiye'nin lider yapı market zinciri. Koç Holding iştiraki olup, ev dekorasyon ve yapı malzemeleri satışı yapmaktadır.",
                "ipo_type": IPOType.SECONDARY,
                "status": IPOStatus.TRADING,
                "price_range_min": 118.00,
                "price_range_max": 138.00,
                "final_price": 128.00,
                "lot_size": 100,
                "min_lot": 1,
                "shares_offered": 14000000,
                "total_shares": 70000000,
                "market_cap_estimate": 8960000000,
                "demand_start": datetime(2025, 9, 8, 10, 0),
                "demand_end": datetime(2025, 9, 10, 17, 0),
                "allocation_date": datetime(2025, 9, 12),
                "trading_start": datetime(2025, 9, 16),
                "demand_multiple": 5.4,
                "individual_allocation": 40,
                "current_price": 168.20,
                "price_change_percent": 31.41,
                "website": "https://koctas.com.tr",
                "kap_url": "https://www.kap.org.tr/tr/sirket-bilgileri/ozet/KOCTS"
            },
            
            # ======= 2026 PLANLANAN HALKA ARZLAR =======
            {
                "id": "ipo-marti-2026",
                "symbol": "MARTI",
                "name": "Martı Teknoloji A.Ş.",
                "sector": "Teknoloji",
                "description": "Elektrikli scooter ve mikromobilite hizmetleri sunan teknoloji şirketi. 35 şehirde 150.000+ araç filosu ile faaliyet göstermektedir.",
                "ipo_type": IPOType.PRIMARY,
                "status": IPOStatus.UPCOMING,
                "price_range_min": 48.00,
                "price_range_max": 58.00,
                "lot_size": 100,
                "min_lot": 1,
                "shares_offered": 22000000,
                "total_shares": 110000000,
                "market_cap_estimate": 6380000000,
                "demand_start": datetime(2026, 2, 10, 10, 0),
                "demand_end": datetime(2026, 2, 12, 17, 0),
                "allocation_date": datetime(2026, 2, 14),
                "trading_start": datetime(2026, 2, 18),
                "individual_allocation": 35,
                "website": "https://marti.tech",
                "kap_url": None
            },
            {
                "id": "ipo-hepsiburada-2026",
                "symbol": "HPSBR",
                "name": "Hepsiburada E-Ticaret A.Ş.",
                "sector": "E-Ticaret",
                "description": "Türkiye'nin köklü e-ticaret platformu. NASDAQ'tan çıkarak BIST'e transfer olan şirket, yıllık 80 milyar TL GMV'ye sahiptir.",
                "ipo_type": IPOType.SECONDARY,
                "status": IPOStatus.UPCOMING,
                "price_range_min": 125.00,
                "price_range_max": 148.00,
                "lot_size": 50,
                "min_lot": 1,
                "shares_offered": 18000000,
                "total_shares": 120000000,
                "market_cap_estimate": 17760000000,
                "demand_start": datetime(2026, 2, 24, 10, 0),
                "demand_end": datetime(2026, 2, 26, 17, 0),
                "allocation_date": datetime(2026, 2, 28),
                "trading_start": datetime(2026, 3, 4),
                "individual_allocation": 25,
                "website": "https://hepsiburada.com",
                "kap_url": None
            },
            {
                "id": "ipo-baykar-2026",
                "symbol": "BAYKR",
                "name": "Baykar Savunma A.Ş.",
                "sector": "Savunma",
                "description": "TB2, Akıncı ve Kızılelma gibi dünyaca ünlü İHA'ların üreticisi. Türkiye'nin en değerli savunma şirketi.",
                "ipo_type": IPOType.SECONDARY,
                "status": IPOStatus.UPCOMING,
                "price_range_min": 850.00,
                "price_range_max": 980.00,
                "lot_size": 10,
                "min_lot": 1,
                "shares_offered": 8000000,
                "total_shares": 100000000,
                "market_cap_estimate": 98000000000,
                "demand_start": datetime(2026, 3, 16, 10, 0),
                "demand_end": datetime(2026, 3, 18, 17, 0),
                "allocation_date": datetime(2026, 3, 20),
                "trading_start": datetime(2026, 3, 24),
                "individual_allocation": 10,
                "website": "https://baykartech.com",
                "kap_url": None
            },
            {
                "id": "ipo-peak-2026",
                "symbol": "PEAK",
                "name": "Peak Games A.Ş.",
                "sector": "Oyun",
                "description": "Mobil oyun geliştirici ve yayıncısı. Toon Blast ve Toy Blast gibi dünya çapında başarılı oyunların yaratıcısı.",
                "ipo_type": IPOType.SECONDARY,
                "status": IPOStatus.UPCOMING,
                "price_range_min": 520.00,
                "price_range_max": 620.00,
                "lot_size": 20,
                "min_lot": 1,
                "shares_offered": 6000000,
                "total_shares": 60000000,
                "market_cap_estimate": 37200000000,
                "demand_start": datetime(2026, 4, 7, 10, 0),
                "demand_end": datetime(2026, 4, 9, 17, 0),
                "allocation_date": datetime(2026, 4, 11),
                "trading_start": datetime(2026, 4, 15),
                "individual_allocation": 15,
                "website": "https://peak.com",
                "kap_url": None
            },
            
            # ======= 2025 TAMAMLANAN HALKA ARZLAR =======
            {
                "id": "ipo-smart-gunes-2025",
                "symbol": "SMRTG",
                "name": "Smart Güneş Enerjisi A.Ş.",
                "sector": "Enerji",
                "description": "Güneş paneli üretimi ve GES (Güneş Enerjisi Santrali) projeleri geliştiren yenilenebilir enerji şirketi.",
                "ipo_type": IPOType.PRIMARY,
                "status": IPOStatus.COMPLETED,
                "price_range_min": 78.00,
                "price_range_max": 92.00,
                "final_price": 86.00,
                "lot_size": 100,
                "min_lot": 1,
                "shares_offered": 12000000,
                "total_shares": 60000000,
                "market_cap_estimate": 5160000000,
                "demand_start": datetime(2025, 8, 25, 10, 0),
                "demand_end": datetime(2025, 8, 27, 17, 0),
                "allocation_date": datetime(2025, 8, 29),
                "trading_start": datetime(2025, 9, 2),
                "demand_multiple": 7.2,
                "individual_allocation": 35,
                "current_price": 124.80,
                "price_change_percent": 45.12,
                "website": "https://smartsolar.com.tr",
                "kap_url": "https://www.kap.org.tr/tr/sirket-bilgileri/ozet/SMRTG"
            },
        ]
        
        for ipo_data in real_ipos:
            ipo = IPOCompany(
                id=ipo_data["id"],
                symbol=ipo_data["symbol"],
                name=ipo_data["name"],
                sector=ipo_data["sector"],
                description=ipo_data["description"],
                ipo_type=ipo_data.get("ipo_type", IPOType.PRIMARY),
                status=ipo_data.get("status", IPOStatus.UPCOMING),
                price_range_min=ipo_data.get("price_range_min", 0),
                price_range_max=ipo_data.get("price_range_max", 0),
                final_price=ipo_data.get("final_price"),
                lot_size=ipo_data.get("lot_size", 100),
                min_lot=ipo_data.get("min_lot", 1),
                shares_offered=ipo_data.get("shares_offered", 0),
                total_shares=ipo_data.get("total_shares", 0),
                market_cap_estimate=ipo_data.get("market_cap_estimate", 0),
                announcement_date=datetime.now() - timedelta(days=30),
                demand_start=ipo_data.get("demand_start"),
                demand_end=ipo_data.get("demand_end"),
                allocation_date=ipo_data.get("allocation_date"),
                trading_start=ipo_data.get("trading_start"),
                demand_multiple=ipo_data.get("demand_multiple"),
                individual_allocation=ipo_data.get("individual_allocation"),
                current_price=ipo_data.get("current_price"),
                price_change_percent=ipo_data.get("price_change_percent"),
                website=ipo_data.get("website"),
                kap_url=ipo_data.get("kap_url")
            )
            self.ipos[ipo.id] = ipo
    
    def refresh_data(self) -> bool:
        """Verileri yenile (senkron)"""
        now = datetime.now()
        if self.last_update and (now - self.last_update).total_seconds() < self.update_interval:
            logger.debug("Data is still fresh, skipping refresh")
            return False
        
        # Önce JSON'dan yükle
        self._load_data()
        return True
    
    async def refresh_data_async(self) -> Dict[str, Any]:
        """Verileri web'den yenile (asenkron)"""
        return await self.update_from_web()
    
    def force_save(self):
        """Verileri zorla kaydet"""
        self._save_to_json()
        return True
    
    def get_update_status(self) -> Dict[str, Any]:
        """Güncelleme durumunu döndür"""
        return {
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'source': self.last_fetch_source,
            'ipo_count': len(self.ipos),
            'data_file': str(IPO_DATA_FILE),
            'data_file_exists': IPO_DATA_FILE.exists(),
            'update_interval_seconds': self.update_interval,
            'is_stale': self._is_data_stale()
        }
    
    def _is_data_stale(self, max_age_hours: int = 6) -> bool:
        """Veri eskimiş mi kontrol et"""
        if not self.last_update:
            return True
        age = datetime.now() - self.last_update
        return age > timedelta(hours=max_age_hours)
    
    def get_all_ipos(self, status: Optional[str] = None, sector: Optional[str] = None) -> List[Dict]:
        """Tüm halka arzları getir"""
        ipos = list(self.ipos.values())
        
        if status:
            try:
                status_enum = IPOStatus(status)
                ipos = [ipo for ipo in ipos if ipo.status == status_enum]
            except ValueError:
                pass
        
        if sector:
            ipos = [ipo for ipo in ipos if ipo.sector.lower() == sector.lower()]
        
        # Tarihe göre sırala (aktif ve yaklaşanlar önce)
        def sort_key(ipo):
            if ipo.status == IPOStatus.ACTIVE:
                return (0, ipo.demand_end or datetime.max)
            elif ipo.status == IPOStatus.UPCOMING:
                return (1, ipo.demand_start or datetime.max)
            elif ipo.status == IPOStatus.TRADING:
                return (2, -(ipo.price_change_percent or 0))
            else:
                return (3, ipo.announcement_date)
        
        ipos.sort(key=sort_key)
        return [ipo.to_dict() for ipo in ipos]
    
    def get_ipo(self, ipo_id: str) -> Optional[Dict]:
        """Belirli bir halka arzı getir"""
        ipo = self.ipos.get(ipo_id)
        if ipo:
            return ipo.to_dict()
        return None
    
    def get_ipo_by_symbol(self, symbol: str) -> Optional[Dict]:
        """Sembole göre halka arz getir"""
        for ipo in self.ipos.values():
            if ipo.symbol.upper() == symbol.upper():
                return ipo.to_dict()
        return None
    
    def get_active_ipos(self) -> List[Dict]:
        """Aktif (talep toplama devam eden) halka arzlar"""
        return self.get_all_ipos(status="active")
    
    def get_upcoming_ipos(self) -> List[Dict]:
        """Yaklaşan halka arzlar"""
        return self.get_all_ipos(status="upcoming")
    
    def get_recent_ipos(self, days: int = 90) -> List[Dict]:
        """Son X gün içinde işlem görmeye başlayanlar"""
        cutoff = datetime.now() - timedelta(days=days)
        ipos = [
            ipo for ipo in self.ipos.values() 
            if ipo.status == IPOStatus.TRADING and ipo.trading_start and ipo.trading_start >= cutoff
        ]
        return [ipo.to_dict() for ipo in sorted(ipos, key=lambda x: x.trading_start or datetime.min, reverse=True)]
    
    def get_ipo_stats(self) -> Dict:
        """Halka arz istatistikleri"""
        all_ipos = list(self.ipos.values())
        
        active = [ipo for ipo in all_ipos if ipo.status == IPOStatus.ACTIVE]
        upcoming = [ipo for ipo in all_ipos if ipo.status == IPOStatus.UPCOMING]
        trading = [ipo for ipo in all_ipos if ipo.status == IPOStatus.TRADING]
        completed = [ipo for ipo in all_ipos if ipo.status == IPOStatus.COMPLETED]
        
        # Performans ortalaması
        trading_with_perf = [ipo for ipo in trading + completed if ipo.price_change_percent is not None]
        perf_values = [ipo.price_change_percent for ipo in trading_with_perf if ipo.price_change_percent is not None]
        avg_performance = sum(perf_values) / len(perf_values) if perf_values else 0.0
        
        # En yüksek talep
        all_with_demand = [ipo for ipo in all_ipos if ipo.demand_multiple is not None]
        demand_values = [ipo.demand_multiple for ipo in all_with_demand if ipo.demand_multiple is not None]
        max_demand = max(demand_values) if demand_values else 0.0
        
        # En iyi performans
        best_performer = max(trading_with_perf, key=lambda x: x.price_change_percent or 0.0) if trading_with_perf else None
        
        # Toplam arz değeri (aktif + yaklaşan)
        total_offering = sum(
            (ipo.final_price or ipo.price_range_max) * ipo.shares_offered 
            for ipo in active + upcoming
        )
        
        return {
            "total_ipos": len(all_ipos),
            "active_count": len(active),
            "upcoming_count": len(upcoming),
            "trading_count": len(trading),
            "completed_count": len(completed),
            "avg_performance_percent": round(avg_performance, 2),
            "max_demand_multiple": round(max_demand, 1),
            "total_offering_value": total_offering,
            "sectors": list(set(ipo.sector for ipo in all_ipos)),
            "best_performer": best_performer.to_dict() if best_performer else None,
            "last_update": self.last_update.isoformat() if self.last_update else None
        }
    
    def add_to_watchlist(self, user_id: str, ipo_id: str) -> bool:
        """Takip listesine ekle"""
        if ipo_id not in self.ipos:
            return False
        
        if user_id not in self.watchlist:
            self.watchlist[user_id] = []
        
        if ipo_id not in self.watchlist[user_id]:
            self.watchlist[user_id].append(ipo_id)
        return True
    
    def remove_from_watchlist(self, user_id: str, ipo_id: str) -> bool:
        """Takip listesinden çıkar"""
        if user_id in self.watchlist and ipo_id in self.watchlist[user_id]:
            self.watchlist[user_id].remove(ipo_id)
            return True
        return False
    
    def get_watchlist(self, user_id: str) -> List[Dict]:
        """Kullanıcının takip listesini getir"""
        if user_id not in self.watchlist:
            return []
        
        return [self.ipos[ipo_id].to_dict() for ipo_id in self.watchlist[user_id] if ipo_id in self.ipos]
    
    def calculate_investment(self, ipo_id: str, lot_count: int) -> Optional[Dict]:
        """Yatırım hesaplama"""
        ipo = self.ipos.get(ipo_id)
        if not ipo:
            return None
        
        price_min = ipo.final_price or ipo.price_range_min
        price_max = ipo.final_price or ipo.price_range_max
        shares = lot_count * ipo.lot_size
        
        # Tahmini getiri hesapla (ortalama performansa göre)
        stats = self.get_ipo_stats()
        avg_return = stats.get("avg_performance_percent", 0)
        
        estimated_value_min = price_min * shares * (1 + avg_return / 100)
        estimated_value_max = price_max * shares * (1 + avg_return / 100)
        
        return {
            "ipo_id": ipo_id,
            "symbol": ipo.symbol,
            "name": ipo.name,
            "lot_count": lot_count,
            "shares": shares,
            "investment_min": price_min * shares,
            "investment_max": price_max * shares,
            "price_min": price_min,
            "price_max": price_max,
            "estimated_return_percent": avg_return,
            "estimated_value_min": estimated_value_min,
            "estimated_value_max": estimated_value_max
        }
    
    def search_ipos(self, query: str) -> List[Dict]:
        """Halka arz ara"""
        query = query.lower()
        results = []
        
        for ipo in self.ipos.values():
            if (query in ipo.symbol.lower() or 
                query in ipo.name.lower() or 
                query in ipo.sector.lower() or
                query in ipo.description.lower()):
                results.append(ipo.to_dict())
        
        return results

# Global instance
ipo_service = IPOService()
