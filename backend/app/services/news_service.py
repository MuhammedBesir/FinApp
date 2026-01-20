"""
News Service - Fetches economy and general news from RSS feeds
"""
import aiohttp
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET
from loguru import logger
import re
import html

# RSS Feed kaynakları
ECONOMY_FEEDS = {
    "turkey": [
        {"name": "Bloomberg HT", "url": "https://www.bloomberght.com/rss"},
        {"name": "Dünya Gazetesi", "url": "https://www.dunya.com/rss/ekonomi.xml"},
        {"name": "Para Analiz", "url": "https://www.paraanaliz.com/feed/"},
    ],
    "world": [
        {"name": "Reuters Business", "url": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best"},
        {"name": "CNBC", "url": "https://www.cnbc.com/id/10001147/device/rss/rss.html"},
    ]
}

GENERAL_FEEDS = {
    "turkey": [
        {"name": "NTV", "url": "https://www.ntv.com.tr/son-dakika.rss"},
        {"name": "Hürriyet", "url": "https://www.hurriyet.com.tr/rss/gundem"},
        {"name": "Sözcü", "url": "https://www.sozcu.com.tr/rss/gundem.xml"},
    ],
    "world": [
        {"name": "BBC Türkçe", "url": "https://feeds.bbci.co.uk/turkce/rss.xml"},
        {"name": "DW Türkçe", "url": "https://rss.dw.com/xml/rss-tur-all"},
    ]
}


def clean_html(raw_html: str) -> str:
    """HTML taglarını ve özel karakterleri temizle"""
    if not raw_html:
        return ""
    # HTML taglarını kaldır
    clean = re.sub(r'<[^>]+>', '', raw_html)
    # HTML entities decode
    clean = html.unescape(clean)
    # Fazla boşlukları temizle
    clean = ' '.join(clean.split())
    return clean[:500]  # Max 500 karakter


def parse_rss_date(date_str: str) -> Optional[datetime]:
    """RSS tarih formatlarını parse et"""
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%d %b %Y %H:%M:%S %z",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


async def fetch_rss_feed(session: aiohttp.ClientSession, feed: Dict) -> List[Dict]:
    """Tek bir RSS feed'i çek ve parse et"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        async with session.get(feed["url"], headers=headers, timeout=10) as response:
            if response.status != 200:
                logger.warning(f"Failed to fetch {feed['name']}: {response.status}")
                return []
            
            content = await response.text()
            root = ET.fromstring(content)
            
            items = []
            # RSS 2.0 format
            for item in root.findall(".//item")[:10]:  # Max 10 haber per feed
                title = item.find("title")
                link = item.find("link")
                description = item.find("description")
                pub_date = item.find("pubDate")
                
                if title is not None and title.text:
                    parsed_date = None
                    if pub_date is not None and pub_date.text:
                        parsed_date = parse_rss_date(pub_date.text)
                    
                    items.append({
                        "title": clean_html(title.text),
                        "link": link.text if link is not None else "",
                        "description": clean_html(description.text if description is not None else ""),
                        "source": feed["name"],
                        "published": parsed_date.isoformat() if parsed_date else datetime.now().isoformat(),
                        "timestamp": parsed_date.timestamp() if parsed_date else datetime.now().timestamp()
                    })
            
            # Atom format fallback
            if not items:
                for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry")[:10]:
                    title = entry.find("{http://www.w3.org/2005/Atom}title")
                    link = entry.find("{http://www.w3.org/2005/Atom}link")
                    summary = entry.find("{http://www.w3.org/2005/Atom}summary")
                    updated = entry.find("{http://www.w3.org/2005/Atom}updated")
                    
                    if title is not None and title.text:
                        parsed_date = None
                        if updated is not None and updated.text:
                            parsed_date = parse_rss_date(updated.text)
                        
                        items.append({
                            "title": clean_html(title.text),
                            "link": link.get("href") if link is not None else "",
                            "description": clean_html(summary.text if summary is not None else ""),
                            "source": feed["name"],
                            "published": parsed_date.isoformat() if parsed_date else datetime.now().isoformat(),
                            "timestamp": parsed_date.timestamp() if parsed_date else datetime.now().timestamp()
                        })
            
            logger.info(f"Fetched {len(items)} items from {feed['name']}")
            return items
            
    except asyncio.TimeoutError:
        logger.warning(f"Timeout fetching {feed['name']}")
        return []
    except ET.ParseError as e:
        logger.warning(f"XML parse error for {feed['name']}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching {feed['name']}: {e}")
        return []


async def fetch_all_news(feeds: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """Tüm feed'lerden haberleri çek"""
    async with aiohttp.ClientSession() as session:
        result = {"turkey": [], "world": []}
        
        for region, feed_list in feeds.items():
            tasks = [fetch_rss_feed(session, feed) for feed in feed_list]
            feed_results = await asyncio.gather(*tasks)
            
            # Tüm sonuçları birleştir
            all_items = []
            for items in feed_results:
                all_items.extend(items)
            
            # Tarihe göre sırala (en yeni önce)
            all_items.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
            
            # Duplicate başlıkları kaldır
            seen_titles = set()
            unique_items = []
            for item in all_items:
                title_key = item["title"][:50].lower()
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    unique_items.append(item)
            
            result[region] = unique_items[:20]  # Max 20 haber per region
        
        return result


async def get_economy_news() -> Dict:
    """Ekonomi haberlerini getir"""
    news = await fetch_all_news(ECONOMY_FEEDS)
    return {
        "type": "economy",
        "turkey": news["turkey"],
        "world": news["world"],
        "last_updated": datetime.now().isoformat()
    }


async def get_general_news() -> Dict:
    """Genel haberleri getir"""
    news = await fetch_all_news(GENERAL_FEEDS)
    return {
        "type": "general",
        "turkey": news["turkey"],
        "world": news["world"],
        "last_updated": datetime.now().isoformat()
    }


# Demo data for fallback
DEMO_ECONOMY_NEWS = {
    "type": "economy",
    "turkey": [
        {
            "title": "Merkez Bankası faiz kararını açıkladı",
            "description": "TCMB, para politikası kurulu toplantısında politika faizini yüzde 45'te sabit tuttu.",
            "source": "Bloomberg HT",
            "link": "#",
            "published": datetime.now().isoformat()
        },
        {
            "title": "Borsa İstanbul rekor kırdı",
            "description": "BIST 100 endeksi tarihi zirvesini güncelleyerek 12.500 puan seviyesini aştı.",
            "source": "Dünya Gazetesi",
            "link": "#",
            "published": datetime.now().isoformat()
        },
        {
            "title": "Dolar/TL hareketliliği sürüyor",
            "description": "Dolar/TL paritesi küresel gelişmeler ve iç piyasa dinamikleriyle dalgalı seyrini sürdürüyor.",
            "source": "Para Analiz",
            "link": "#",
            "published": datetime.now().isoformat()
        },
    ],
    "world": [
        {
            "title": "Fed faiz kararı bekleniyor",
            "description": "ABD Merkez Bankası'nın bu haftaki toplantısında faiz indirimi beklentileri artıyor.",
            "source": "Reuters",
            "link": "#",
            "published": datetime.now().isoformat()
        },
        {
            "title": "Altın fiyatları yükselişte",
            "description": "Ons altın küresel belirsizlikler nedeniyle 2.100 dolar seviyesine yaklaştı.",
            "source": "CNBC",
            "link": "#",
            "published": datetime.now().isoformat()
        },
    ],
    "last_updated": datetime.now().isoformat()
}

DEMO_GENERAL_NEWS = {
    "type": "general",
    "turkey": [
        {
            "title": "Meteoroloji'den kar uyarısı",
            "description": "İç Anadolu ve Doğu Anadolu bölgelerinde yoğun kar yağışı bekleniyor.",
            "source": "NTV",
            "link": "#",
            "published": datetime.now().isoformat()
        },
        {
            "title": "Deprem bölgesinde yeni konutlar teslim edildi",
            "description": "Kahramanmaraş'ta inşa edilen 5.000 konut hak sahiplerine teslim edildi.",
            "source": "Hürriyet",
            "link": "#",
            "published": datetime.now().isoformat()
        },
        {
            "title": "Türkiye-AB ilişkilerinde yeni dönem",
            "description": "Dışişleri Bakanı, AB heyetiyle kritik görüşmeler gerçekleştirdi.",
            "source": "Sözcü",
            "link": "#",
            "published": datetime.now().isoformat()
        },
    ],
    "world": [
        {
            "title": "BM Güvenlik Konseyi toplandı",
            "description": "Orta Doğu'daki gelişmeler BM Güvenlik Konseyi'nde ele alındı.",
            "source": "BBC Türkçe",
            "link": "#",
            "published": datetime.now().isoformat()
        },
        {
            "title": "AB'de enerji krizi tartışmaları",
            "description": "Avrupa Birliği ülkeleri enerji politikalarını yeniden değerlendiriyor.",
            "source": "DW Türkçe",
            "link": "#",
            "published": datetime.now().isoformat()
        },
    ],
    "last_updated": datetime.now().isoformat()
}
