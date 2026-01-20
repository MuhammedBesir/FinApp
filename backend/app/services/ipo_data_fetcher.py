"""
IPO Data Fetcher - Halka Arz Veri Çekici (Gelişmiş Bot Bypass)
Gerçek kaynaklardan halka arz verilerini çeker ve günceller

Bot Koruması Aşma Teknikleri:
1. Cloudscraper - Cloudflare/JS challenge bypass
2. Gerçekçi browser headers + fingerprint
3. Random delays ve request throttling
4. Cookie persistence
5. Referer spoofing
"""
import asyncio
import json
import os
import logging
import re
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Cloudscraper - Cloudflare bypass
try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False
    cloudscraper = None

# aiohttp fallback
import aiohttp

# BeautifulSoup for parsing
from bs4 import BeautifulSoup

# feedparser opsiyonel
try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    feedparser = None

logger = logging.getLogger(__name__)

# Data dosyası yolu
DATA_DIR = Path(__file__).parent.parent.parent / "data"
IPO_DATA_FILE = DATA_DIR / "ipo_data.json"
IPO_CACHE_FILE = DATA_DIR / "ipo_cache.json"
IPO_MANUAL_FILE = DATA_DIR / "ipo_manual.json"
IPO_INITIAL_FILE = DATA_DIR / "ipo_initial.json"


class IPODataFetcher:
    """
    Halka arz verilerini bot korumasını aşarak çeker
    
    Veri Kaynakları:
    1. halkaarz.com - Cloudscraper ile
    2. bigpara.hurriyet.com.tr - Cloudscraper ile
    3. investing.com - Cloudscraper ile
    4. KAP RSS - feedparser ile
    5. finnet.com.tr - API
    """
    
    # Güncel veri kaynakları
    SOURCES = {
        # Primary - Halka arz özel siteler
        "halkaarz": "https://halkaarz.com/",
        "halkaarzcom_aktif": "https://halkaarz.com/aktif-halka-arzlar/",
        "halkaarzcom_yaklasan": "https://halkaarz.com/yaklasan-halka-arzlar/",
        "halkaarzcom_gecmis": "https://halkaarz.com/gecmis-halka-arzlar/",
        
        # Finans portalleri
        "bigpara": "https://bigpara.hurriyet.com.tr/borsa/halka-arz/",
        "bigpara_detay": "https://bigpara.hurriyet.com.tr/borsa/halka-arz-detay/",
        "investing": "https://tr.investing.com/equities/turkiye",
        
        # Resmi kaynaklar
        "kap_bildirim": "https://www.kap.org.tr/tr/bildirim-sorgu",
        "bist": "https://www.borsaistanbul.com/tr/sayfa/471/halka-arz",
        
        # RSS Feeds
        "kap_rss": "https://www.kap.org.tr/tr/rss/tum",
        "bloomberght_rss": "https://www.bloomberght.com/rss",
    }
    
    # Gerçekçi browser fingerprints
    BROWSER_PROFILES = [
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        },
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        },
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        },
    ]
    
    def __init__(self):
        self.scraper = None
        self.aio_session: Optional[aiohttp.ClientSession] = None
        self.last_fetch: Optional[datetime] = None
        self.cached_data: Dict[str, Any] = {}
        self.manual_data: Dict[str, Any] = {}
        self.fetch_errors: List[str] = []
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 saniye arası
        
        # Data klasörünü oluştur
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Başlangıç verilerini yükle
        self._load_initial_data()
        
        # Cache ve manuel verileri yükle
        self._load_cache()
        self._load_manual_data()
        
        # Cloudscraper'ı başlat
        self._init_scraper()
    
    def _load_initial_data(self):
        """Başlangıç verilerini yükle (ilk çalıştırma için)"""
        try:
            if IPO_INITIAL_FILE.exists():
                with open(IPO_INITIAL_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    initial_ipos = data.get('ipos', {})
                    # Cache boşsa başlangıç verilerini yükle
                    if not self.cached_data:
                        self.cached_data = initial_ipos.copy()
                        logger.info(f"Loaded {len(initial_ipos)} initial IPOs")
        except Exception as e:
            logger.error(f"Error loading initial data: {e}")
    
    def _init_scraper(self):
        """Cloudscraper'ı başlat"""
        if HAS_CLOUDSCRAPER and cloudscraper is not None:
            try:
                browser = random.choice(['chrome', 'firefox'])
                self.scraper = cloudscraper.create_scraper(
                    browser={
                        'browser': browser,
                        'platform': random.choice(['windows', 'darwin', 'linux']),
                        'desktop': True,
                    },
                    delay=random.uniform(3, 7),
                )
                # Random cookie ekle
                self.scraper.cookies.set('visited', 'true', domain='.halkaarz.com')
                logger.info(f"Cloudscraper initialized with {browser}")
            except Exception as e:
                logger.error(f"Failed to init cloudscraper: {e}")
                self.scraper = None
        else:
            logger.warning("Cloudscraper not available, using basic requests")
    
    def _get_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """Rastgele gerçekçi headers döndür"""
        headers = random.choice(self.BROWSER_PROFILES).copy()
        if referer:
            headers['Referer'] = referer
        return headers
    
    def _rate_limit(self):
        """Rate limiting uygula"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed + random.uniform(0.1, 0.5))
        self.last_request_time = time.time()
    
    def _load_manual_data(self):
        """Manuel eklenen verileri yükle"""
        try:
            if IPO_MANUAL_FILE.exists():
                with open(IPO_MANUAL_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.manual_data = data.get('ipos', {})
                    logger.info(f"Loaded {len(self.manual_data)} manual IPOs")
        except Exception as e:
            logger.error(f"Error loading manual data: {e}")
            self.manual_data = {}
    
    def _load_cache(self):
        """Cache'den verileri yükle"""
        try:
            if IPO_CACHE_FILE.exists():
                with open(IPO_CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cached_data = data.get('ipos', {})
                    last_fetch = data.get('last_fetch')
                    if last_fetch:
                        self.last_fetch = datetime.fromisoformat(last_fetch)
                    logger.info(f"Loaded {len(self.cached_data)} IPOs from cache")
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            self.cached_data = {}
    
    def _save_cache(self):
        """Verileri cache'e kaydet"""
        try:
            data = {
                'ipos': self.cached_data,
                'last_fetch': datetime.now().isoformat(),
                'source': 'auto_fetch'
            }
            with open(IPO_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"Saved {len(self.cached_data)} IPOs to cache")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def save_manual_ipo(self, ipo_data: Dict) -> bool:
        """Manuel olarak IPO ekle/güncelle"""
        try:
            ipo_id = ipo_data.get('id') or f"manual-{ipo_data.get('symbol', 'xxx')}-{datetime.now().strftime('%Y%m%d')}"
            ipo_data['id'] = ipo_id
            ipo_data['source'] = 'manual'
            ipo_data['added_at'] = datetime.now().isoformat()
            
            self.manual_data[ipo_id] = ipo_data
            
            data = {
                'ipos': self.manual_data,
                'last_update': datetime.now().isoformat()
            }
            with open(IPO_MANUAL_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Saved manual IPO: {ipo_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving manual IPO: {e}")
            return False
    
    def delete_manual_ipo(self, ipo_id: str) -> bool:
        """Manuel IPO'yu sil"""
        try:
            if ipo_id in self.manual_data:
                del self.manual_data[ipo_id]
                data = {
                    'ipos': self.manual_data,
                    'last_update': datetime.now().isoformat()
                }
                with open(IPO_MANUAL_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting manual IPO: {e}")
            return False
    
    def get_all_ipos(self) -> Dict[str, Any]:
        """Tüm IPO'ları döndür (manuel + otomatik)"""
        all_ipos = {}
        all_ipos.update(self.cached_data)
        all_ipos.update(self.manual_data)
        return all_ipos
    
    def get_last_errors(self) -> List[str]:
        """Son fetch hatalarını döndür"""
        return self.fetch_errors.copy()
    
    def _fetch_with_cloudscraper(self, url: str, referer: Optional[str] = None) -> Optional[str]:
        """Cloudscraper ile sayfa çek (bot bypass)"""
        if not self.scraper:
            self._init_scraper()
        
        if not self.scraper:
            return None
        
        self._rate_limit()
        
        try:
            headers = self._get_headers(referer)
            response = self.scraper.get(
                url,
                headers=headers,
                timeout=15,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully fetched {url} ({len(response.text)} chars)")
                return response.text
            else:
                logger.warning(f"HTTP {response.status_code} for {url}")
                return None
                
        except Exception as e:
            logger.error(f"Cloudscraper error for {url}: {e}")
            return None
    
    async def _fetch_async(self, url: str) -> Optional[str]:
        """Async HTTP fetch"""
        try:
            if self.aio_session is None or self.aio_session.closed:
                timeout = aiohttp.ClientTimeout(total=15, connect=5)
                connector = aiohttp.TCPConnector(ssl=False, limit=3, force_close=True)
                self.aio_session = aiohttp.ClientSession(
                    headers=self._get_headers(),
                    timeout=timeout,
                    connector=connector
                )
            
            async with self.aio_session.get(url) as response:
                if response.status == 200:
                    return await response.text()
        except Exception as e:
            logger.error(f"Async fetch error for {url}: {e}")
        return None
    
    async def fetch_all_sources(self) -> Dict[str, Any]:
        """Tüm kaynaklardan veri çek"""
        logger.info("=" * 50)
        logger.info("IPO Data Fetch başlatılıyor...")
        logger.info("=" * 50)
        
        self.fetch_errors = []
        results = {}
        sources_tried = []
        news_items = []
        web_ipos_found = 0
        
        # 1. Önce başlangıç/cache verilerini kontrol et
        if not self.cached_data:
            self._load_initial_data()
            if self.cached_data:
                sources_tried.append('initial_data')
                logger.info(f"✓ Başlangıç verileri: {len(self.cached_data)} IPO yüklendi")
        
        # 2. halkaarz.com'dan veri çek (Cloudscraper ile)
        try:
            halkaarz_data = await self._fetch_halkaarz()
            if halkaarz_data:
                results['halkaarz'] = halkaarz_data
                sources_tried.append('halkaarz')
                web_ipos_found += len(halkaarz_data)
                logger.info(f"✓ halkaarz.com: {len(halkaarz_data)} IPO bulundu")
        except Exception as e:
            self.fetch_errors.append(f"halkaarz: {str(e)[:100]}")
            logger.error(f"halkaarz.com error: {e}")
        
        # 3. bigpara'dan veri çek
        try:
            bigpara_data = await self._fetch_bigpara()
            if bigpara_data:
                results['bigpara'] = bigpara_data
                sources_tried.append('bigpara')
                web_ipos_found += len(bigpara_data)
                logger.info(f"✓ bigpara: {len(bigpara_data)} IPO bulundu")
        except Exception as e:
            self.fetch_errors.append(f"bigpara: {str(e)[:100]}")
            logger.error(f"bigpara error: {e}")
        
        # 4. RSS Feed'lerden haber çek
        if HAS_FEEDPARSER:
            try:
                rss_data = await self._fetch_rss_feeds()
                if rss_data:
                    news_items.extend(rss_data)
                    sources_tried.append('rss')
                    logger.info(f"✓ RSS: {len(rss_data)} haber bulundu")
            except Exception as e:
                self.fetch_errors.append(f"RSS: {str(e)[:100]}")
        
        # 5. investing.com'dan veri çek
        try:
            investing_data = await self._fetch_investing()
            if investing_data:
                results['investing'] = investing_data
                sources_tried.append('investing')
                web_ipos_found += len(investing_data)
                logger.info(f"✓ investing: {len(investing_data)} veri bulundu")
        except Exception as e:
            self.fetch_errors.append(f"investing: {str(e)[:100]}")
        
        # Sonuçları birleştir
        merged_ipos = self._merge_results(results)
        
        # Cache'e kaydet
        if merged_ipos:
            for ipo_id, ipo_data in merged_ipos.items():
                if ipo_id not in self.cached_data:
                    self.cached_data[ipo_id] = ipo_data
                else:
                    # Mevcut veriyi güncelle
                    self.cached_data[ipo_id].update(ipo_data)
            
            self.last_fetch = datetime.now()
            self._save_cache()
        
        # Web'den veri gelmese bile cache/initial veriler varsa başarılı say
        total_ipos = len(self.cached_data) + len(self.manual_data)
        success = total_ipos > 0
        
        # Web'den veri gelmediğinde ama cache varsa uyarı ver
        if web_ipos_found == 0 and total_ipos > 0:
            self.fetch_errors.append(f"Web kaynakları erişilemedi, mevcut {total_ipos} IPO verisi kullanılıyor")
            sources_tried.append('cache')
        
        logger.info("=" * 50)
        logger.info(f"Fetch tamamlandı: {len(sources_tried)} kaynak, toplam {total_ipos} IPO")
        logger.info(f"Web'den: {web_ipos_found}, Cache: {len(self.cached_data)}, Manuel: {len(self.manual_data)}")
        logger.info(f"Hatalar: {len(self.fetch_errors)}")
        logger.info("=" * 50)
        
        return {
            'success': success,
            'ipos': merged_ipos if merged_ipos else self.cached_data,
            'sources_tried': sources_tried,
            'ipos_found': total_ipos,
            'ipos_updated': len(merged_ipos),
            'web_ipos_found': web_ipos_found,
            'cache_ipos': len(self.cached_data),
            'manual_ipos': len(self.manual_data),
            'errors': self.fetch_errors,
            'news_found': len(news_items),
            'timestamp': datetime.now().isoformat()
        }
    
    async def _fetch_halkaarz(self) -> List[Dict]:
        """halkaarz.com'dan veri çek"""
        ipos = []
        
        # Thread pool ile cloudscraper kullan
        loop = asyncio.get_event_loop()
        
        urls = [
            (self.SOURCES['halkaarz'], None),
            (self.SOURCES['halkaarzcom_aktif'], self.SOURCES['halkaarz']),
            (self.SOURCES['halkaarzcom_yaklasan'], self.SOURCES['halkaarz']),
        ]
        
        for url, referer in urls:
            try:
                html = await loop.run_in_executor(
                    self.executor,
                    self._fetch_with_cloudscraper,
                    url,
                    referer
                )
                
                if html and len(html) > 1000:  # Gerçek içerik kontrolü
                    parsed = self._parse_halkaarz_html(html)
                    ipos.extend(parsed)
                    logger.info(f"  halkaarz {url}: {len(parsed)} IPO parsed")
                    
                # Rate limiting
                await asyncio.sleep(random.uniform(1.5, 3.0))
                
            except Exception as e:
                logger.error(f"halkaarz fetch error for {url}: {e}")
        
        return ipos
    
    def _parse_halkaarz_html(self, html: str) -> List[Dict]:
        """halkaarz.com HTML parse"""
        ipos = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # IPO kartlarını bul - farklı CSS selector'ları dene
            selectors = [
                'div.ipo-card',
                'div.halka-arz-card',
                'article.ipo',
                'div.card',
                'div[class*="ipo"]',
                'div[class*="halka"]',
                'tr[class*="ipo"]',
            ]
            
            for selector in selectors:
                cards = soup.select(selector)
                for card in cards:
                    ipo = self._extract_ipo_from_element(card, 'halkaarz')
                    if ipo and ipo.get('name'):
                        ipos.append(ipo)
            
            # Tablo varsa parse et
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:  # Header'ı atla
                    ipo = self._parse_table_row(row, 'halkaarz')
                    if ipo and ipo.get('name'):
                        ipos.append(ipo)
            
            # Link'lerden şirket adları çıkar
            links = soup.find_all('a', href=re.compile(r'/halka-arz/|/sirket/', re.I))
            for link in links:
                text = link.get_text(strip=True)
                if text and len(text) > 3 and 'halka' not in text.lower():
                    ipos.append({
                        'name': text,
                        'source': 'halkaarz_link',
                        'url': link.get('href', ''),
                    })
            
        except Exception as e:
            logger.error(f"halkaarz parse error: {e}")
        
        return ipos
    
    async def _fetch_bigpara(self) -> List[Dict]:
        """bigpara.hurriyet.com.tr'den veri çek"""
        ipos = []
        
        loop = asyncio.get_event_loop()
        
        try:
            html = await loop.run_in_executor(
                self.executor,
                self._fetch_with_cloudscraper,
                self.SOURCES['bigpara'],
                "https://bigpara.hurriyet.com.tr/"
            )
            
            if html and len(html) > 500:
                ipos = self._parse_bigpara_html(html)
                
        except Exception as e:
            logger.error(f"bigpara fetch error: {e}")
        
        return ipos
    
    def _parse_bigpara_html(self, html: str) -> List[Dict]:
        """bigpara HTML parse"""
        ipos = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Tablo parse
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:
                    ipo = self._parse_table_row(row, 'bigpara')
                    if ipo and ipo.get('name'):
                        ipos.append(ipo)
            
            # Card/div yapıları
            cards = soup.select('div.stock-card, div.ipo-item, article')
            for card in cards:
                ipo = self._extract_ipo_from_element(card, 'bigpara')
                if ipo and ipo.get('name'):
                    ipos.append(ipo)
                    
        except Exception as e:
            logger.error(f"bigpara parse error: {e}")
        
        return ipos
    
    async def _fetch_investing(self) -> List[Dict]:
        """investing.com'dan veri çek"""
        ipos = []
        
        loop = asyncio.get_event_loop()
        
        try:
            html = await loop.run_in_executor(
                self.executor,
                self._fetch_with_cloudscraper,
                self.SOURCES['investing'],
                "https://tr.investing.com/"
            )
            
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                # Hisse tablosu
                rows = soup.select('tr[data-id], table tr')
                for row in rows:
                    ipo = self._parse_table_row(row, 'investing')
                    if ipo and ipo.get('name'):
                        ipos.append(ipo)
                        
        except Exception as e:
            logger.error(f"investing fetch error: {e}")
        
        return ipos
    
    async def _fetch_rss_feeds(self) -> List[Dict]:
        """RSS Feed'lerden haber çek"""
        items = []
        
        if not HAS_FEEDPARSER:
            return items
        
        feeds = [
            self.SOURCES.get('kap_rss'),
            self.SOURCES.get('bloomberght_rss'),
            "https://www.dunya.com/rss/borsa",
        ]
        
        loop = asyncio.get_event_loop()
        
        for url in feeds:
            if not url:
                continue
            try:
                if feedparser is None:
                    continue
                feed = await loop.run_in_executor(
                    self.executor,
                    feedparser.parse,
                    url
                )
                
                for entry in feed.entries[:30]:
                    title_raw = entry.get('title', '')
                    summary_raw = entry.get('summary', '')
                    title = str(title_raw).lower() if title_raw else ''
                    summary = str(summary_raw).lower() if summary_raw else ''
                    
                    # Halka arz ile ilgili mi?
                    keywords = ['halka arz', 'halka açıl', 'ipo', 'borsa istanbul', 'bist', 'sermaye artırım']
                    if any(kw in title or kw in summary for kw in keywords):
                        summary_text = str(summary_raw) if summary_raw else ''
                        items.append({
                            'title': str(title_raw) if title_raw else '',
                            'summary': summary_text[:200] if summary_text else '',
                            'link': entry.get('link', ''),
                            'date': entry.get('published', ''),
                            'source': 'rss',
                        })
                        
            except Exception as e:
                logger.debug(f"RSS error for {url}: {e}")
        
        return items
    
    def _extract_ipo_from_element(self, element, source: str) -> Optional[Dict]:
        """HTML elementinden IPO bilgisi çıkar"""
        try:
            # Şirket adı
            name = None
            for selector in ['h2', 'h3', 'h4', '.title', '.name', '.company', 'a']:
                el = element.select_one(selector)
                if el:
                    text = el.get_text(strip=True)
                    if text and len(text) > 2 and len(text) < 100:
                        name = text
                        break
            
            if not name:
                name = element.get_text(strip=True)[:50]
            
            if not name or len(name) < 3:
                return None
            
            # Fiyat
            price_text = element.find(text=re.compile(r'[\d.,]+\s*(?:TL|₺)', re.I))
            price = self._parse_price(str(price_text)) if price_text else None
            
            # Tarih
            date_text = element.find(text=re.compile(r'\d{1,2}[./]\d{1,2}[./]\d{2,4}'))
            
            # Sembol
            symbol_match = re.search(r'\b([A-Z]{3,5})\b', element.get_text())
            symbol = symbol_match.group(1) if symbol_match else None
            
            return {
                'name': name,
                'symbol': symbol,
                'price': price,
                'date_text': str(date_text).strip() if date_text else None,
                'source': source,
            }
            
        except Exception:
            return None
    
    def _parse_table_row(self, row, source: str) -> Optional[Dict]:
        """Tablo satırından IPO bilgisi çıkar"""
        try:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                return None
            
            texts = [c.get_text(strip=True) for c in cells]
            
            # İlk hücre genellikle şirket adı
            name = texts[0] if texts else None
            if not name or len(name) < 3 or name.lower() in ['şirket', 'hisse', '#', 'sıra']:
                return None
            
            # Sembol ara
            symbol = None
            for text in texts:
                if re.match(r'^[A-Z]{3,5}$', text):
                    symbol = text
                    break
            
            # Fiyat ara
            price = None
            for text in texts:
                p = self._parse_price(text)
                if p:
                    price = p
                    break
            
            return {
                'name': name,
                'symbol': symbol,
                'price': price,
                'cells': texts,
                'source': source,
            }
            
        except Exception:
            return None
    
    def _parse_price(self, text: str) -> Optional[float]:
        """Fiyat metnini parse et"""
        if not text:
            return None
        try:
            clean = re.sub(r'[^\d.,]', '', str(text))
            clean = clean.replace(',', '.')
            # Birden fazla nokta varsa son noktayı decimal olarak al
            if clean.count('.') > 1:
                parts = clean.rsplit('.', 1)
                clean = parts[0].replace('.', '') + '.' + parts[1]
            return float(clean) if clean else None
        except:
            return None
    
    def _merge_results(self, results: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Farklı kaynaklardan gelen verileri birleştir"""
        merged = {}
        
        for source_name, items in results.items():
            for item in items:
                name = item.get('name', '')
                if not name or len(name) < 3:
                    continue
                
                ipo_id = self._generate_id(name)
                
                if ipo_id in merged:
                    # Mevcut veriyi güncelle (None olmayanları)
                    for k, v in item.items():
                        if v is not None and (k not in merged[ipo_id] or merged[ipo_id].get(k) is None):
                            merged[ipo_id][k] = v
                    merged[ipo_id].setdefault('sources', []).append(source_name)
                else:
                    item['id'] = ipo_id
                    item['sources'] = [source_name]
                    item['fetched_at'] = datetime.now().isoformat()
                    merged[ipo_id] = item
        
        return merged
    
    def _generate_id(self, name: str) -> str:
        """Benzersiz ID oluştur"""
        clean = re.sub(r'[^\w\s]', '', name.lower())
        clean = re.sub(r'\s+', '-', clean.strip())
        return f"ipo-{clean[:30]}-{datetime.now().strftime('%Y%m')}"
    
    def get_cached_data(self) -> Dict[str, Any]:
        """Cache'deki verileri döndür"""
        return self.cached_data
    
    def should_refresh(self, max_age_hours: int = 4) -> bool:
        """Verinin yenilenmesi gerekip gerekmediğini kontrol et"""
        if not self.last_fetch:
            return True
        age = datetime.now() - self.last_fetch
        return age > timedelta(hours=max_age_hours)
    
    async def close(self):
        """Kaynakları temizle"""
        if self.aio_session and not self.aio_session.closed:
            await self.aio_session.close()
        self.executor.shutdown(wait=False)


# Global fetcher instance
_fetcher: Optional[IPODataFetcher] = None

def get_fetcher() -> IPODataFetcher:
    """Global fetcher instance döndür"""
    global _fetcher
    if _fetcher is None:
        _fetcher = IPODataFetcher()
    return _fetcher


async def fetch_ipo_data() -> Dict[str, Any]:
    """IPO verilerini çek (async)"""
    fetcher = get_fetcher()
    return await fetcher.fetch_all_sources()


def get_cached_ipo_data() -> Dict[str, Any]:
    """Cache'deki IPO verilerini döndür"""
    fetcher = get_fetcher()
    return fetcher.get_cached_data()
