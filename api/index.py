"""
Vercel Serverless API - Lightweight Version
Sadece AI Chat ve temel endpoint'ler - 250MB limit için optimize edildi
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Claude API
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    anthropic = None
    CLAUDE_AVAILABLE = False
    logger.warning("Anthropic SDK not installed")

# Create FastAPI app
app = FastAPI(
    title="Trading Bot API - Serverless",
    description="Lightweight API for Vercel deployment",
    version="2.0.0"
)

# CORS Configuration
cors_origins = os.getenv(
    "CORS_ORIGINS", 
    "http://localhost:5173,http://localhost:3000,https://fin-app-bay.vercel.app"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== Models ==========
class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    suggestions: List[str]
    timestamp: str

# ========== Trading System Prompt ==========
TRADING_SYSTEM_PROMPT = """Sen bir Profesyonel AI Trading Asistanısın. BIST (Borsa İstanbul) odaklı günlük trade tavsiyeleri veriyorsun. Türkçe yanıt veriyorsun.

📌 RİSK YÖNETİMİ (EN ÖNCELİKLİ!)
• Her işlemde portföyün maksimum %2-3'ünü riske at
• Günlük toplam kayıp limiti: Portföyün %5-8'i
• Risk/Ödül oranı minimum 1:2, tercihen 1:3
• Her zaman STOP-LOSS kullan!

📌 TEKNİK ANALİZ
• RSI (14 periyot): <30 aşırı satım, >70 aşırı alım
• MACD: Sinyal çizgisi kesişimleri
• Hareketli Ortalamalar: EMA 20, 50, 200
• Bollinger Bantları ve hacim analizi

📌 YANIT KURALLARI
• Her tavsiyen için risk/ödül oranını belirt
• Stop-loss seviyesi ver
• Pozisyon boyutu öner
• Türkçe ve net yanıtlar ver
• Emoji kullanarak görsel zenginlik kat
"""

# ========== Suggestions ==========
SUGGESTIONS = [
    "RSI nedir ve nasıl yorumlanır?",
    "MACD indikatörü nasıl çalışır?",
    "Stop-loss nasıl belirlenir?",
    "Bollinger Bantları ne anlama gelir?",
    "Pozisyon boyutlandırma nasıl yapılır?",
    "Risk/ödül oranı nasıl hesaplanır?",
    "Destek ve direnç seviyeleri nedir?",
    "Trend takibi nasıl yapılır?"
]

# ========== Knowledge Base for Fallback ==========
KNOWLEDGE_BASE = {
    "rsi": {
        "keywords": ["rsi", "relative strength", "göreceli güç", "aşırı alım", "aşırı satım"],
        "response": """📊 **RSI (Relative Strength Index)**

RSI momentum tabanlı bir teknik göstergedir (0-100 arası).

📈 **Yorumlama:**
• **70 üzeri**: Aşırı alım bölgesi - Satış sinyali olabilir
• **30 altı**: Aşırı satım bölgesi - Alış sinyali olabilir
• **50 seviyesi**: Nötr bölge

💡 **İpuçları:**
• RSI divergence güçlü sinyaller verir
• Trend yönünde işlem yaparken daha güvenilirdir
• Tek başına yeterli değildir, diğer göstergelerle teyit edin"""
    },
    "macd": {
        "keywords": ["macd", "moving average convergence"],
        "response": """📉 **MACD (Moving Average Convergence Divergence)**

Trend takip eden momentum göstergesidir.

📊 **Bileşenleri:**
• **MACD Çizgisi**: 12 günlük EMA - 26 günlük EMA
• **Sinyal Çizgisi**: MACD'nin 9 günlük EMA'sı
• **Histogram**: MACD - Sinyal farkı

📈 **Sinyaller:**
• **Alış**: MACD, sinyal çizgisini yukarı keser
• **Satış**: MACD, sinyal çizgisini aşağı keser
• **Divergence**: Fiyat ve MACD farklı yönde hareket ederse dikkat!"""
    },
    "stoploss": {
        "keywords": ["stop", "loss", "zarar", "kes", "koruma", "stop-loss", "stoploss"],
        "response": """🛡️ **Stop-Loss Stratejileri**

Kayıpları sınırlamak için kritik bir araçtır.

📍 **Belirleme Yöntemleri:**
• **Teknik Seviyeler**: Destek/direnç seviyelerinin altına/üstüne
• **ATR Bazlı**: Giriş ± (2 x ATR)
• **Yüzdelik**: Giriş fiyatından %2-3 uzakta

⚠️ **Altın Kurallar:**
• Asla portföyün %2'sinden fazlasını riske atma
• Stop-loss'u duygusal kararlarla değiştirme
• Kâra geçince stop'u başabaşa çek
• Trailing stop kullanarak kârı koru"""
    },
    "bollinger": {
        "keywords": ["bollinger", "bant", "band", "volatilite"],
        "response": """📊 **Bollinger Bantları**

Volatilite tabanlı güçlü bir göstergedir.

📈 **Bileşenleri:**
• **Üst Bant**: SMA + (2 x Standart Sapma)
• **Orta Bant**: 20 günlük SMA
• **Alt Bant**: SMA - (2 x Standart Sapma)

💡 **Yorumlama:**
• Fiyat üst banda yakınsa → Aşırı alım olabilir
• Fiyat alt banda yakınsa → Aşırı satım olabilir
• Bantlar daralırsa → Düşük volatilite, büyük hareket beklentisi (squeeze)
• Bantlar genişlerse → Yüksek volatilite"""
    },
    "pozisyon": {
        "keywords": ["pozisyon", "boyut", "lot", "adet", "ne kadar"],
        "response": """💰 **Pozisyon Boyutlandırma**

Risk yönetiminin en kritik parçasıdır.

📊 **Formül:**
Pozisyon = Risk Edilecek Tutar / (Giriş - Stop Loss)

📈 **Örnek:**
• Portföy: 100.000₺
• Risk: %2 = 2.000₺
• Giriş: 50₺, Stop: 47₺
• Pozisyon = 2.000 / 3 = 666 adet

⚠️ **Kurallar:**
• Tek işlemde max %2-3 risk
• Tek sektörde max %30-40 yoğunlaşma
• Kademeli giriş yapın (%50 → %30 → %20)"""
    },
    "destek": {
        "keywords": ["destek", "direnç", "seviye", "support", "resistance"],
        "response": """📐 **Destek ve Direnç Seviyeleri**

Fiyatın duraklamaya veya dönmeye eğilimli olduğu önemli seviyeler.

📊 **Destek:**
• Fiyatın düşüşte durduğu seviye
• Alıcıların güçlü olduğu bölge
• Kırılırsa direnç olur

📈 **Direnç:**
• Fiyatın yükselişte durduğu seviye
• Satıcıların güçlü olduğu bölge
• Kırılırsa destek olur

💡 **İpuçları:**
• Yatay çizgiler en basit yöntem
• Fibonacci seviyeleri kullanın
• Hacim profili ile teyit edin"""
    },
    "trend": {
        "keywords": ["trend", "yükseliş", "düşüş", "yön", "takip"],
        "response": """📈 **Trend Takibi**

"Trend senin dostundur" - en önemli trading kuralı.

📊 **Trend Türleri:**
• **Yükseliş Trendi**: Yükselen dipler ve tepeler
• **Düşüş Trendi**: Alçalan dipler ve tepeler
• **Yatay Trend**: Belli bir aralıkta hareket

💡 **Trend Belirleme:**
• EMA 20 > EMA 50 > EMA 200 → Güçlü yükseliş
• Fiyat EMA 20 üzerinde → Kısa vadeli yükseliş
• ADX > 25 → Güçlü trend var

⚠️ **Kural:** Trende karşı işlem yapma!"""
    },
    "risk": {
        "keywords": ["risk", "ödül", "oran", "reward", "rr"],
        "response": """⚖️ **Risk/Ödül Oranı**

Her işlemde mutlaka hesaplanmalıdır.

📊 **Formül:**
R/R = (Hedef Fiyat - Giriş) / (Giriş - Stop Loss)

📈 **Örnek:**
• Giriş: 100₺
• Stop Loss: 95₺ (Risk: 5₺)
• Hedef: 115₺ (Ödül: 15₺)
• R/R = 15/5 = 1:3

💡 **Minimum Oranlar:**
• Scalping: 1:1.5
• Swing: 1:2 minimum
• Pozisyon: 1:3 ve üzeri

⚠️ **Kural:** 1:2'nin altında işlem açma!"""
    }
}

# ========== In-memory conversations ==========
conversations: Dict[str, List[Dict]] = {}

# ========== Helper Functions ==========
def find_topic(message: str) -> Optional[Dict]:
    """Find matching topic from knowledge base"""
    msg_lower = message.lower()
    best_match = None
    best_score = 0
    
    for topic_data in KNOWLEDGE_BASE.values():
        score = sum(len(kw) for kw in topic_data["keywords"] if kw in msg_lower)
        if score > best_score:
            best_score = score
            best_match = topic_data
    
    return best_match if best_score > 0 else None

def get_fallback_response(message: str) -> str:
    """Generate fallback response when Claude is not available"""
    msg_lower = message.lower()
    
    # Greeting
    if any(w in msg_lower for w in ["merhaba", "selam", "hey", "naber"]):
        return """Merhaba! 👋 Ben AI Trading Asistanınızım.

Size şu konularda yardımcı olabilirim:
• 📊 Teknik göstergeler (RSI, MACD, Bollinger)
• 📈 Destek/direnç seviyeleri
• 🛡️ Risk yönetimi ve stop-loss
• 💰 Pozisyon boyutlandırma

Öneri sorularından seçebilir veya kendi sorunuzu sorabilirsiniz! 🎯"""
    
    # Check knowledge base
    topic = find_topic(message)
    if topic:
        return topic["response"]
    
    return """🤔 Bu konuda detaylı bilgi veremiyorum. Şu konularda yardımcı olabilirim:

• **RSI**: "RSI nedir?" diye sorun
• **MACD**: "MACD nasıl yorumlanır?"
• **Stop-Loss**: "Stop-loss nasıl belirlenir?"
• **Bollinger**: "Bollinger bantları ne anlama gelir?"
• **Pozisyon**: "Pozisyon boyutu nasıl hesaplanır?"
• **Risk/Ödül**: "Risk ödül oranı nedir?"

Lütfen bu konulardan birini seçin! 💡"""

async def get_claude_response(message: str, history: List[Dict]) -> Optional[str]:
    """Get response from Claude API"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not CLAUDE_AVAILABLE or not anthropic or not api_key:
        logger.warning("Claude not available")
        return None
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        # Build messages
        messages = [{"role": m["role"], "content": m["content"]} for m in history[-10:]]
        messages.append({"role": "user", "content": message})
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2048,
            system=TRADING_SYSTEM_PROMPT,
            messages=messages
        )
        
        return response.content[0].text
        
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return None

# ========== Routes ==========
@app.get("/")
async def root():
    return {
        "status": "online",
        "name": "Trading Bot API",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "claude_available": CLAUDE_AVAILABLE and bool(os.getenv("ANTHROPIC_API_KEY")),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/ai/suggestions")
async def get_suggestions():
    return {"suggestions": SUGGESTIONS}

@app.post("/api/ai/chat", response_model=ChatResponse)
async def chat(request: ChatMessage):
    """AI Chat endpoint"""
    message = request.message.strip()
    conv_id = request.conversation_id or f"conv_{datetime.now().timestamp()}"
    
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Get or create conversation history
    if conv_id not in conversations:
        conversations[conv_id] = []
    
    history = conversations[conv_id]
    
    # Try Claude first, fallback to knowledge base
    response_text = await get_claude_response(message, history)
    
    if not response_text:
        response_text = get_fallback_response(message)
    
    # Save to history
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": response_text})
    
    # Keep only last 20 messages
    conversations[conv_id] = history[-20:]
    
    return ChatResponse(
        response=response_text,
        conversation_id=conv_id,
        suggestions=SUGGESTIONS[:4],
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/ai/knowledge/{topic}")
async def get_knowledge(topic: str):
    """Get knowledge base entry"""
    topic_lower = topic.lower()
    
    if topic_lower in KNOWLEDGE_BASE:
        return {
            "topic": topic,
            "content": KNOWLEDGE_BASE[topic_lower]["response"]
        }
    
    raise HTTPException(status_code=404, detail="Topic not found")

# ========== Stub Endpoints (Frontend compatibility) ==========
# These return empty/mock data since heavy dependencies are removed

@app.get("/api/alerts/statistics")
async def alerts_statistics():
    """Stub: Alert statistics"""
    return {
        "total": 0,
        "active": 0,
        "triggered": 0,
        "by_type": {}
    }

@app.get("/api/alerts")
async def get_alerts():
    """Stub: Get alerts list"""
    return {"alerts": [], "total": 0}

@app.post("/api/alerts")
async def create_alert():
    """Stub: Create alert"""
    return {"message": "Alerts feature coming soon", "id": None}

@app.get("/api/portfolio")
async def get_portfolio():
    """Stub: Get portfolio"""
    return {"holdings": [], "total_value": 0, "daily_change": 0}

@app.get("/api/stocks/{symbol}")
async def get_stock(symbol: str):
    """Stub: Get stock data"""
    return {
        "symbol": symbol,
        "price": 0,
        "change": 0,
        "message": "Stock data feature coming soon"
    }

@app.get("/api/signals")
async def get_signals():
    """Stub: Get trading signals"""
    return {"signals": [], "message": "Signals feature coming soon"}

@app.get("/api/screener")
async def get_screener():
    """Stub: Stock screener"""
    return {"results": [], "message": "Screener feature coming soon"}

@app.get("/api/news")
async def get_news():
    """Stub: Market news"""
    return {"news": [], "message": "News feature coming soon"}

@app.get("/api/ipo")
async def get_ipo():
    """Stub: IPO calendar"""
    return {"upcoming": [], "recent": [], "message": "IPO feature coming soon"}

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )




