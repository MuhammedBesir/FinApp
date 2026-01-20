"""
AI Trading Assistant Service
Trading tavsiyesi ve bilgi sağlayan AI asistan servisi - Claude API Entegrasyonu
"""
import logging
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Claude API
try:
    import anthropic  # type: ignore
    CLAUDE_AVAILABLE = True
except ImportError:
    anthropic = None  # type: ignore
    CLAUDE_AVAILABLE = False
    logger.warning("Anthropic SDK not installed. Using fallback mode.")


@dataclass
class ChatMessage:
    """Sohbet mesajı"""
    id: str
    role: str  # "user" veya "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict] = None


# Trading konusunda uzmanlaşmış system prompt - PROFESSIONAL TRADING BOT
TRADING_SYSTEM_PROMPT = """Sen bir Profesyonel AI Trading Asistanısın. BIST (Borsa İstanbul) odaklı günlük trade tavsiyeleri veriyorsun. Türkçe yanıt veriyorsun.

═══════════════════════════════════════════════════════════════
📌 1. RİSK YÖNETİMİ (EN ÖNCELİKLİ!)
═══════════════════════════════════════════════════════════════
• Her işlemde portföyün maksimum %2-3'ünü riske at
• Günlük toplam kayıp limiti: Portföyün %5-8'i
• Bir sektörde max %30-40 yoğunlaşma
• Risk/Ödül oranı minimum 1:2, tercihen 1:3
• Her zaman STOP-LOSS kullan, asla ihmal etme!

Pozisyon Boyutu Formülü:
Pozisyon = (Risk Edilecek Tutar) / (Giriş Fiyatı - Stop Loss)
Örnek: 100.000₺ portföy, %2 risk = 2.000₺ max kayıp
Giriş: 50₺, SL: 47₺ → Pozisyon = 2.000 / 3 = 666 adet

═══════════════════════════════════════════════════════════════
📌 2. İŞLEM YAPMA DURMALARI
═══════════════════════════════════════════════════════════════
✅ İşlem Öncesi Kontrol Listesi:
1. Ana trend yönü nedir? (Trende karşı işlem yapma!)
2. Hacim yeterli mi? (Ortalama üstü hacim aranmalı)
3. Destek/direnç seviyelerine yakın mı?
4. Ekonomik takvim kontrol edildi mi?
5. En az 2-3 teknik gösterge uyumlu mu?

⛔ İŞLEM YAPMA DURUMLAR:
• Piyasa açılışının ilk 15 dakikası (volatilite yüksek)
• Hacim ortalamanın %50 altındaysa
• Önemli ekonomik veri açıklamalarından hemen önce/sonra
• Günlük kayıp limiti aşıldıysa
• Net sinyal yoksa (şüpheye düşersen BEKLEME!)

═══════════════════════════════════════════════════════════════
📌 3. TEKNİK ANALİZ YAKLAŞIMI
═══════════════════════════════════════════════════════════════
Birincil Göstergeler:
• RSI (14 periyot): <30 aşırı satım, >70 aşırı alım
• MACD: Sinyal çizgisi kesişimleri ve histogram
• Hareketli Ortalamalar: EMA 20, 50, 200

İkincil Göstergeler:
• Bollinger Bantları: Bant daralması (sıkışma) ve genişlemesi
• Hacim profili ve hacim teyidi
• ATR (ortalama gerçek aralık): Stop-loss mesafesi için

Sinyal Kriterleri:
• ALIŞ: RSI<40 + MACD pozitif kesişim + Fiyat>EMA20 + Hacim artışı
• SATIŞ: RSI>60 + MACD negatif kesişim + Fiyat<EMA20 + Hacim artışı

═══════════════════════════════════════════════════════════════
📌 4. POZİSYON YÖNETİMİ
═══════════════════════════════════════════════════════════════
Giriş Stratejisi (Kademeli):
• 1. Giriş: Toplam pozisyonun %50'si
• 2. Giriş: Trend teyidi sonrası %30
• 3. Giriş: Momentum artışında %20

Çıkış Stratejisi (Kademeli Kar Al):
• Hedef 1'de: Pozisyonun %30-50'sini kapat
• Hedef 2'de: Kalan pozisyonun %50'sini kapat
• Trailing stop ile devam: Kalan %20-30

Stop-Loss Yönetimi:
• ATR bazlı dinamik stop: 2 ATR uzaklık
• Kara geçince stop'u başabaşa çek
• Trailing stop: Her %5 kârda %3 yukarı çek

═══════════════════════════════════════════════════════════════
📌 5. YANIT FORMATLARI
═══════════════════════════════════════════════════════════════

📝 İŞLEM ÖNERİSİ ŞABLONU:
```
🎯 İŞLEM ÖNERİSİ: [HİSSE]

📊 DURUM ANALİZİ:
• [Teknik gösterge durumları]
• [Trend analizi]
• [Hacim bilgisi]

💰 İŞLEM DETAYI:
• Yön: AL / SAT
• Giriş: ₺[fiyat]
• Stop Loss: ₺[fiyat] (%[yüzde])
• Hedef 1: ₺[fiyat] (%[yüzde])
• Hedef 2: ₺[fiyat] (%[yüzde])
• Risk/Ödül: 1:[oran]

⚠️ RİSK YÖNETİMİ:
• Önerilen pozisyon: Portföyün %[X]'i
• Maksimum risk: ₺[tutar]

⏰ GEÇERLİLİK: [süre]
```

📅 GÜNLÜK PİYASA RAPORU ŞABLONU:
```
📊 BIST DURUM: [Trend/Seviyeler]
⚠️ BUGÜN DİKKAT: [Uyarılar]
🔥 EN İYİ FIRSATLAR: [Hisseler]
💡 GÜNÜN STRATEJİSİ: [Öneriler]
```

═══════════════════════════════════════════════════════════════
📌 6. GENEL KURALLAR
═══════════════════════════════════════════════════════════════
• Her zaman risk yönetimini ön planda tut
• Duygusal karar verme - mantıklı ve disiplinli ol
• Kayıpların peşinden koşma (revenge trading yapma)
• Sabırlı ol, net sinyal bekle
• Her işlemi kaydet ve analiz et
• Piyasayı yenmeye çalışma, onunla birlikte hareket et

🔔 Her tavsiyen için mutlaka:
1. Risk/Ödül oranını belirt
2. Stop-loss seviyesi ver
3. Pozisyon boyutu öner
4. Geçerlilik süresi ekle
"""


class AITradingAssistant:
    """
    AI Trading Asistan - Claude API + Fallback Kural Tabanlı Sistem
    """
    
    def __init__(self):
        self.conversations: Dict[str, List[ChatMessage]] = {}
        self.knowledge_base = self._init_knowledge_base()
        self.quick_suggestions = self._init_suggestions()
        
        # Claude API client
        self.claude_client: Any = None
        api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if CLAUDE_AVAILABLE and anthropic and api_key and not api_key.startswith("your-"):
            try:
                self.claude_client = anthropic.Anthropic(api_key=api_key)
                logger.info("Claude API client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Claude client: {e}")
    
    def _init_suggestions(self) -> List[str]:
        """Öneri sorularını başlat"""
        return [
            "RSI nedir ve nasıl yorumlanır?",
            "MACD indikatörü nasıl çalışır?",
            "Destek ve direnç seviyeleri nedir?",
            "Stop-loss nasıl belirlenir?",
            "Bollinger Bantları ne anlama gelir?",
            "Pozisyon boyutlandırma nasıl yapılır?",
            "Mum grafik formasyonları nelerdir?",
            "Risk/ödül oranı nasıl hesaplanır?",
        ]
    
    def _init_knowledge_base(self) -> Dict[str, Dict]:
        """Trading bilgi bankasını başlat - Fallback için"""
        return {
            "rsi": {
                "keywords": ["rsi", "relative strength", "göreceli güç", "aşırı alım", "aşırı satım"],
                "title": "📊 RSI (Relative Strength Index)",
                "response": """**RSI (Göreceli Güç Endeksi)** momentum tabanlı bir teknik göstergedir.

📈 **Yorumlama:**
• **70 üzeri**: Aşırı alım bölgesi - Satış sinyali olabilir
• **30 altı**: Aşırı satım bölgesi - Alış sinyali olabilir
• **50 seviyesi**: Nötr bölge

💡 **İpuçları:**
• RSI divergence güçlü sinyaller verir
• Trend yönünde işlem yaparken daha güvenilirdir

⚠️ **Dikkat**: RSI tek başına yeterli değildir."""
            },
            "macd": {
                "keywords": ["macd", "moving average convergence", "hareketli ortalama"],
                "title": "📉 MACD",
                "response": """**MACD** trend takip eden momentum göstergesidir.

📊 **Bileşenleri:**
• **MACD Çizgisi**: 12 günlük EMA - 26 günlük EMA
• **Sinyal Çizgisi**: MACD'nin 9 günlük EMA'sı

📈 **Sinyaller:**
• **Alış**: MACD, sinyal çizgisini yukarı keser
• **Satış**: MACD, sinyal çizgisini aşağı keser"""
            },
            "stoploss": {
                "keywords": ["stop", "loss", "zarar", "kes", "koruma"],
                "title": "🛡️ Stop-Loss",
                "response": """**Stop-Loss** kayıpları sınırlamak için kritik bir araçtır.

📍 **Belirleme Yöntemleri:**
• Destek/direnç seviyelerinin altına/üstüne
• ATR bazlı: Giriş ± (2 x ATR)
• Yüzdelik: %2-3 uzakta

⚠️ **Kurallar:**
• Asla %2'den fazla sermaye riske atma
• Duygusal kararlarla stop'u değiştirme"""
            },
            "bollinger": {
                "keywords": ["bollinger", "bant", "band", "volatilite"],
                "title": "📊 Bollinger Bantları",
                "response": """**Bollinger Bantları** volatilite tabanlı göstergedir.

📈 **Bileşenleri:**
• **Üst Bant**: SMA + (2 x Standart Sapma)
• **Orta Bant**: 20 günlük SMA
• **Alt Bant**: SMA - (2 x Standart Sapma)

💡 **Yorumlama:**
• Fiyat üst banda yakınsa: Aşırı alım
• Fiyat alt banda yakınsa: Aşırı satım
• Bantlar daralırsa: Düşük volatilite, patlama beklentisi"""
            },
            "fibonacci": {
                "keywords": ["fibonacci", "fibo", "retracement", "düzeltme"],
                "title": "📐 Fibonacci Seviyeleri",
                "response": """**Fibonacci** destek/direnç seviyelerini bulmak için kullanılır.

📊 **Önemli Seviyeler:**
• **0.236** (23.6%)
• **0.382** (38.2%) - Güçlü destek/direnç
• **0.500** (50%)
• **0.618** (61.8%) - Altın oran, en güçlü seviye
• **0.786** (78.6%)

💡 **Kullanım:**
• Düzeltme sonrası giriş noktası bulmak için
• Hedef fiyat belirlemek için"""
            },
        }
    
    def get_suggestions(self) -> List[str]:
        """Öneri sorularını döndür"""
        return self.quick_suggestions
    
    def _find_matching_topic(self, message: str) -> Optional[Dict]:
        """Mesaja uyan konuyu bul - Fallback için"""
        message_lower = message.lower()
        
        best_match = None
        best_score = 0
        
        for topic_key, topic_data in self.knowledge_base.items():
            score = 0
            for keyword in topic_data["keywords"]:
                if keyword.lower() in message_lower:
                    score += len(keyword)
            
            if score > best_score:
                best_score = score
                best_match = topic_data
        
        return best_match if best_score > 0 else None
    
    def _extract_ticker(self, message: str) -> Optional[str]:
        """Mesajdan hisse sembolü çıkar"""
        match = re.search(r'\$([A-Z]{3,5})', message.upper())
        if match:
            return match.group(1)
        
        match = re.search(r'\b([A-Z]{3,5})\.IS\b', message.upper())
        if match:
            return match.group(1)
        
        return None
    
    async def _get_claude_response(self, message: str, conversation_history: List[Dict], system_prompt: Optional[str] = None) -> Optional[str]:
        """Claude API'den yanıt al"""
        if not self.claude_client:
            return None
        
        try:
            # Conversation history'yi Claude formatına dönüştür
            messages = []
            for msg in conversation_history[-10:]:  # Son 10 mesaj
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Yeni mesajı ekle
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Claude API çağrısı
            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2048,
                system=system_prompt or TRADING_SYSTEM_PROMPT,
                messages=messages
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return None
    
    def _generate_fallback_response(self, message: str) -> str:
        """Fallback yanıt üret"""
        message_lower = message.lower()
        
        # Selamlama
        if any(word in message_lower for word in ["merhaba", "selam", "hey"]):
            return """Merhaba! 👋 Ben AI Trading Asistanınızım.

Size şu konularda yardımcı olabilirim:
• 📊 Teknik göstergeler (RSI, MACD, Bollinger)
• 📈 Destek/direnç seviyeleri
• 🛡️ Risk yönetimi ve stop-loss
• 💰 Pozisyon boyutlandırma
• 📋 Portföy analizi

Yukarıdaki öneri sorularından seçebilirsiniz!"""
        
        # Bilgi bankasından eşleşme ara
        topic = self._find_matching_topic(message)
        if topic:
            return f"## {topic['title']}\n\n{topic['response']}"
        
        return """🤔 Sorunuzu tam anlayamadım. Şu konularda yardımcı olabilirim:

• **Teknik Göstergeler**: RSI, MACD, Bollinger
• **Risk Yönetimi**: Stop-loss, pozisyon boyutlandırma
• **Formasyonlar**: Mum grafik desenleri
• **Portföy Analizi**: Diversifikasyon, risk değerlendirmesi

Lütfen daha spesifik bir soru sorun! 🎯"""
    
    async def get_stock_analysis(self, ticker: str) -> str:
        """Hisse için analiz üret"""
        try:
            from .data_fetcher import DataFetcher
            from .technical_analysis import TechnicalAnalysis
            
            fetcher = DataFetcher()
            ta = TechnicalAnalysis()
            
            symbol = f"{ticker}.IS" if not ticker.endswith(".IS") else ticker
            df = fetcher.fetch_realtime_data(symbol, interval="1d", period="1mo")
            
            if df.empty:
                return f"⚠️ {ticker} için veri bulunamadı."
            
            df_with_ind = ta.calculate_all_indicators(df)
            latest = ta.get_latest_indicators(df_with_ind)
            
            from .signal_generator import SignalGenerator
            sg = SignalGenerator()
            
            # Indicators dict for signal generator
            indicators_dict = {
                'trend': {
                    'ema_9': latest.get('ema_9', 0),
                    'ema_21': latest.get('ema_21', 0),
                    'adx': latest.get('adx', 0),
                },
                'momentum': {
                    'rsi': latest.get('rsi', 50),
                    'macd': latest.get('macd', 0),
                    'macd_signal': latest.get('macd_signal', 0),
                    'stoch_k': latest.get('stoch_k', 50),
                },
                'volatility': {
                    'atr': latest.get('atr', 0),
                    'bb_lower': latest.get('bb_lower', 0),
                    'bb_middle': latest.get('bb_middle', 0),
                    'bb_upper': latest.get('bb_upper', 0),
                },
                'volume': {
                    'mfi': latest.get('mfi', 50),
                }
            }
            signal = sg.generate_signal(df_with_ind, indicators_dict)
            
            rsi = latest.get('rsi', 50)
            macd = latest.get('macd', 0)
            price = latest.get('close', 0)
            
            rsi_status = "Aşırı Alım ⚠️" if rsi > 70 else "Aşırı Satım ⚠️" if rsi < 30 else "Nötr"
            trend = "Yükseliş 📈" if macd > 0 else "Düşüş 📉"
            
            return f"""📊 **{ticker} Teknik Analiz**

💰 **Fiyat**: ₺{price:.2f}

📈 **Göstergeler:**
• RSI: {rsi:.1f} - {rsi_status}
• MACD: {macd:.4f} - {trend}

🎯 **Sinyal**: {signal.get('signal', 'HOLD').upper()}

⚠️ *Yatırım tavsiyesi değildir.*"""
            
        except Exception as e:
            logger.error(f"Stock analysis error: {e}")
            return f"⚠️ {ticker} analizi yapılırken hata oluştu."
    
    async def analyze_portfolio(self, portfolio_data: Dict) -> str:
        """Portföy analizi yap"""
        try:
            holdings = portfolio_data.get("holdings", [])
            trades = portfolio_data.get("trades", [])
            stats = portfolio_data.get("stats", {})
            
            if not holdings and not trades:
                return """📋 **Portföy Analizi**

⚠️ Portföyünüzde henüz varlık bulunmuyor.

💡 **Öneriler:**
• Diversifikasyon için farklı sektörlerden hisse ekleyin
• Risk toleransınıza uygun varlıklar seçin
• Uzun vadeli hedeflerinizi belirleyin"""
            
            # Basit analiz
            total_value = sum(h.get("quantity", 0) * h.get("currentPrice", 0) for h in holdings)
            total_cost = sum(h.get("quantity", 0) * h.get("buyPrice", 0) for h in holdings)
            total_pnl = total_value - total_cost
            pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0
            
            # Sektör dağılımı
            sectors = {}
            for h in holdings:
                sector = h.get("sector", "Diğer")
                value = h.get("quantity", 0) * h.get("currentPrice", 0)
                sectors[sector] = sectors.get(sector, 0) + value
            
            # Trade istatistikleri
            closed_trades = [t for t in trades if t.get("status") == "closed"]
            winning_trades = [t for t in closed_trades if (t.get("pnl", 0) or 0) > 0]
            win_rate = len(winning_trades) / len(closed_trades) * 100 if closed_trades else 0
            
            analysis = f"""📊 **Portföy Analizi**

💰 **Genel Durum:**
• Toplam Değer: ₺{total_value:,.2f}
• Toplam Maliyet: ₺{total_cost:,.2f}
• Kar/Zarar: ₺{total_pnl:,.2f} ({pnl_percent:+.2f}%)
• Pozisyon Sayısı: {len(holdings)}

"""
            
            if sectors:
                analysis += "📈 **Sektör Dağılımı:**\n"
                for sector, value in sorted(sectors.items(), key=lambda x: x[1], reverse=True)[:5]:
                    pct = value / total_value * 100 if total_value > 0 else 0
                    analysis += f"• {sector}: %{pct:.1f}\n"
                analysis += "\n"
            
            if closed_trades:
                analysis += f"""📋 **İşlem İstatistikleri:**
• Toplam İşlem: {len(closed_trades)}
• Kazanma Oranı: %{win_rate:.1f}
• Başarılı: {len(winning_trades)} | Başarısız: {len(closed_trades) - len(winning_trades)}

"""
            
            # Öneriler
            analysis += "💡 **Öneriler:**\n"
            
            if len(holdings) < 3:
                analysis += "• ⚠️ Portföy çeşitliliği düşük, daha fazla hisse eklemeyi düşünün\n"
            
            if len(sectors) == 1:
                analysis += "• ⚠️ Tek sektörde yoğunlaşma var, diversifikasyon önerilir\n"
            
            if win_rate < 50 and closed_trades:
                analysis += "• ⚠️ Kazanma oranı düşük, strateji gözden geçirilmeli\n"
            
            if pnl_percent < -10:
                analysis += "• ⚠️ Portföy kayıpta, risk yönetimini gözden geçirin\n"
            elif pnl_percent > 20:
                analysis += "• 💰 İyi performans! Kısmi kar realizasyonu düşünülebilir\n"
            
            if not analysis.endswith("**Öneriler:**\n"):
                pass
            else:
                analysis += "• ✅ Portföyünüz dengeli görünüyor\n"
            
            analysis += "\n⚠️ *Bu analiz yatırım tavsiyesi değildir.*"
            
            # Claude ile daha detaylı analiz
            if self.claude_client and holdings:
                portfolio_summary = f"""
Portföy Özeti:
- Toplam Değer: ₺{total_value:,.2f}
- Kar/Zarar: %{pnl_percent:.2f}
- Pozisyon Sayısı: {len(holdings)}
- Sektörler: {list(sectors.keys())}
- Kazanma Oranı: %{win_rate:.1f}

Hisseler:
"""
                for h in holdings[:10]:
                    portfolio_summary += f"- {h.get('ticker', 'N/A')}: {h.get('quantity', 0)} adet @ ₺{h.get('currentPrice', 0):.2f}\n"
                
                claude_prompt = f"""Bu portföyü analiz et ve kısa öneriler sun:
{portfolio_summary}

Kısa ve öz tut, maksimum 5 madde."""
                
                claude_analysis = await self._get_claude_response(claude_prompt, [], TRADING_SYSTEM_PROMPT)
                if claude_analysis:
                    analysis = f"""📊 **AI Portföy Analizi**

{claude_analysis}

---
📈 **Sayısal Özet:**
• Toplam Değer: ₺{total_value:,.2f}
• Kar/Zarar: ₺{total_pnl:,.2f} ({pnl_percent:+.2f}%)
• Pozisyon: {len(holdings)} | İşlem: {len(closed_trades)}

⚠️ *Yatırım tavsiyesi değildir.*"""
            
            return analysis
            
        except Exception as e:
            logger.error(f"Portfolio analysis error: {e}")
            return "⚠️ Portföy analizi yapılırken bir hata oluştu."
    
    async def analyze_trade(self, trade_data: Dict) -> str:
        """Tek bir işlemi analiz et"""
        try:
            ticker = trade_data.get("ticker", "N/A")
            entry_price = trade_data.get("entryPrice", 0)
            exit_price = trade_data.get("exitPrice", 0)
            quantity = trade_data.get("quantity", 0)
            trade_type = trade_data.get("type", "long")
            
            if trade_type == "long":
                pnl = (exit_price - entry_price) * quantity
                pnl_percent = ((exit_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
            else:
                pnl = (entry_price - exit_price) * quantity
                pnl_percent = ((entry_price - exit_price) / entry_price) * 100 if entry_price > 0 else 0
            
            result_emoji = "✅" if pnl > 0 else "❌" if pnl < 0 else "➖"
            
            return f"""📋 **İşlem Analizi** {result_emoji}

📊 **{ticker}**
• Tür: {"Alış (Long)" if trade_type == "long" else "Satış (Short)"}
• Giriş: ₺{entry_price:.2f}
• Çıkış: ₺{exit_price:.2f}
• Miktar: {quantity} adet

💰 **Sonuç:**
• Kar/Zarar: ₺{pnl:,.2f} ({pnl_percent:+.2f}%)

💡 **Değerlendirme:**
{"• 👍 Başarılı bir işlem!" if pnl > 0 else "• 📚 Kayıptan ders çıkarılmalı" if pnl < 0 else "• ➖ Başabaş işlem"}"""
            
        except Exception as e:
            logger.error(f"Trade analysis error: {e}")
            return "⚠️ İşlem analizi yapılırken bir hata oluştu."
    
    async def get_market_summary(self) -> str:
        """Piyasa özeti oluştur"""
        try:
            from .data_fetcher import DataFetcher
            
            fetcher = DataFetcher()
            
            # BIST 100 verisi
            bist100 = fetcher.fetch_realtime_data("XU100.IS", interval="1d", period="5d")
            
            if bist100.empty:
                return """📊 **Piyasa Özeti**

⚠️ Piyasa verisi alınamadı. Lütfen daha sonra tekrar deneyin."""
            
            latest_price = bist100['close'].iloc[-1]
            prev_price = bist100['close'].iloc[-2] if len(bist100) > 1 else latest_price
            change = ((latest_price - prev_price) / prev_price) * 100
            
            trend = "📈 Yükseliş" if change > 0 else "📉 Düşüş" if change < 0 else "➖ Yatay"
            
            return f"""📊 **Piyasa Özeti**

🏛️ **BIST 100**: {latest_price:,.2f} ({change:+.2f}%)
{trend}

💡 **Genel Değerlendirme:**
• {"Piyasa pozitif seyrediyor" if change > 0 else "Piyasa negatif seyrediyor" if change < 0 else "Piyasa yatay seyrediyor"}
• İşlem hacmi ve momentum takip edilmeli

⚠️ *Yatırım tavsiyesi değildir.*"""
            
        except Exception as e:
            logger.error(f"Market summary error: {e}")
            return "⚠️ Piyasa özeti alınırken bir hata oluştu."
    
    async def chat(self, user_id: str, message: str, context: Optional[Dict] = None) -> ChatMessage:
        """Kullanıcı mesajına yanıt ver"""
        
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        # Kullanıcı mesajını kaydet
        user_msg = ChatMessage(
            id=f"msg_{datetime.now().timestamp()}",
            role="user",
            content=message
        )
        self.conversations[user_id].append(user_msg)
        
        # Context varsa (portföy, trade vs.) ekle
        full_message = message
        if context:
            if context.get("type") == "portfolio":
                full_message = f"""[Portföy Verisi]
{context.get('data', {})}

Kullanıcı Sorusu: {message}"""
            elif context.get("type") == "trade":
                full_message = f"""[İşlem Verisi]
{context.get('data', {})}

Kullanıcı Sorusu: {message}"""
        
        # Hisse analizi isteniyor mu?
        ticker = self._extract_ticker(message)
        if ticker and any(word in message.lower() for word in ["analiz", "incele", "bak", "durum", "ne der"]):
            response_text = await self.get_stock_analysis(ticker)
        elif any(word in message.lower() for word in ["piyasa", "borsa", "bist", "market", "genel durum"]):
            response_text = await self.get_market_summary()
        else:
            # Önce Claude API'yi dene
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in self.conversations[user_id][:-1]
            ]
            
            response_text = await self._get_claude_response(full_message, history)
            
            # Claude başarısız olduysa fallback
            if not response_text:
                response_text = self._generate_fallback_response(message)
        
        # Asistan yanıtını oluştur
        assistant_msg = ChatMessage(
            id=f"msg_{datetime.now().timestamp()}_resp",
            role="assistant",
            content=response_text
        )
        self.conversations[user_id].append(assistant_msg)
        
        # Geçmişi sınırla
        if len(self.conversations[user_id]) > 50:
            self.conversations[user_id] = self.conversations[user_id][-50:]
        
        return assistant_msg
    
    def get_conversation_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Konuşma geçmişini döndür"""
        if user_id not in self.conversations:
            return []
        
        messages = self.conversations[user_id][-limit:]
        return [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in messages
        ]
    
    def clear_conversation(self, user_id: str):
        """Konuşma geçmişini temizle"""
        if user_id in self.conversations:
            del self.conversations[user_id]


# Global instance
_assistant: Optional[AITradingAssistant] = None


def get_ai_assistant() -> AITradingAssistant:
    """Global AI assistant instance döndür"""
    global _assistant
    if _assistant is None:
        _assistant = AITradingAssistant()
    return _assistant
