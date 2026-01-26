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

# ========== Auth Endpoints (Stub - LocalStorage Based) ==========
# Simple auth that stores data in memory (resets on cold start)
# For production, use a real database

import hashlib
import secrets

# In-memory user storage (for demo purposes)
users_db: Dict[str, dict] = {}
tokens_db: Dict[str, str] = {}  # token -> email mapping

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str
    remember_me: bool = False

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_urlsafe(32)

@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    """Register new user"""
    email = request.email.lower().strip()
    
    if email in users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Create user
    user_id = f"user_{len(users_db) + 1}"
    users_db[email] = {
        "id": user_id,
        "email": email,
        "full_name": request.full_name,
        "password_hash": hash_password(request.password),
        "created_at": datetime.now().isoformat()
    }
    
    # Generate token
    token = generate_token()
    tokens_db[token] = email
    
    return {
        "success": True,
        "message": "Registration successful",
        "data": {
            "access_token": token,
            "refresh_token": generate_token(),
            "user": {
                "id": user_id,
                "email": email,
                "full_name": request.full_name
            }
        }
    }

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Login user"""
    email = request.email.lower().strip()
    
    if email not in users_db:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user = users_db[email]
    if user["password_hash"] != hash_password(request.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Generate new token
    token = generate_token()
    tokens_db[token] = email
    
    return {
        "success": True,
        "message": "Login successful",
        "data": {
            "access_token": token,
            "refresh_token": generate_token(),
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"]
            }
        }
    }

@app.post("/api/auth/logout")
async def logout(request: Request):
    """Logout user"""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        tokens_db.pop(token, None)
    
    return {"success": True, "message": "Logged out successfully"}

@app.get("/api/auth/verify")
async def verify_token(request: Request):
    """Verify token"""
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        return {"success": False, "message": "No token provided"}
    
    token = auth_header[7:]
    email = tokens_db.get(token)
    
    if not email or email not in users_db:
        return {"success": False, "message": "Invalid token"}
    
    user = users_db[email]
    return {
        "success": True,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"]
        }
    }

@app.post("/api/auth/refresh")
async def refresh_token(request: Request):
    """Refresh token"""
    # For simplicity, just generate a new token
    token = generate_token()
    return {
        "success": True,
        "data": {
            "access_token": token
        }
    }

@app.get("/api/auth/me")
async def get_me(request: Request):
    """Get current user"""
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header[7:]
    email = tokens_db.get(token)
    
    if not email or email not in users_db:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = users_db[email]
    return {
        "success": True,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"]
        }
    }

@app.put("/api/auth/me")
async def update_me(request: Request):
    """Update current user"""
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header[7:]
    email = tokens_db.get(token)
    
    if not email or email not in users_db:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    body = await request.json()
    user = users_db[email]
    
    if "full_name" in body:
        user["full_name"] = body["full_name"]
    
    return {
        "success": True,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"]
        }
    }

@app.post("/api/auth/change-password")
async def change_password(request: Request):
    """Change password"""
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header[7:]
    email = tokens_db.get(token)
    
    if not email or email not in users_db:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    body = await request.json()
    user = users_db[email]
    
    if user["password_hash"] != hash_password(body.get("current_password", "")):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    if len(body.get("new_password", "")) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    
    user["password_hash"] = hash_password(body["new_password"])
    
    return {"success": True, "message": "Password changed successfully"}

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

@app.get("/api/alerts/check")
async def check_alerts():
    """Stub: Check alerts"""
    return {
        "checked": 0,
        "triggered": [],
        "message": "No alerts to check"
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

# ========== MOCK DATA for BIST30 (Fallback when Yahoo fails) ==========
MOCK_STOCK_DATA = {
    "THYAO.IS": {"name": "Türk Hava Yolları", "price": 298.50, "change": 3.20, "changePercent": 1.08},
    "GARAN.IS": {"name": "Garanti BBVA", "price": 151.00, "change": 1.50, "changePercent": 1.00},
    "AKBNK.IS": {"name": "Akbank", "price": 52.80, "change": 0.45, "changePercent": 0.86},
    "YKBNK.IS": {"name": "Yapı Kredi", "price": 37.90, "change": 0.38, "changePercent": 1.01},
    "EREGL.IS": {"name": "Ereğli Demir Çelik", "price": 58.20, "change": -0.30, "changePercent": -0.51},
    "BIMAS.IS": {"name": "BİM", "price": 620.00, "change": 5.50, "changePercent": 0.89},
    "ASELS.IS": {"name": "Aselsan", "price": 320.00, "change": 8.75, "changePercent": 2.81},
    "KCHOL.IS": {"name": "Koç Holding", "price": 188.50, "change": 1.20, "changePercent": 0.64},
    "SAHOL.IS": {"name": "Sabancı Holding", "price": 78.50, "change": 0.65, "changePercent": 0.83},
    "SISE.IS": {"name": "Şişecam", "price": 52.40, "change": -0.15, "changePercent": -0.29},
    "TCELL.IS": {"name": "Turkcell", "price": 101.50, "change": 0.80, "changePercent": 0.79},
    "TUPRS.IS": {"name": "Tüpraş", "price": 185.00, "change": 2.10, "changePercent": 1.15},
    "PGSUS.IS": {"name": "Pegasus", "price": 980.00, "change": 12.00, "changePercent": 1.24},
    "TAVHL.IS": {"name": "TAV Havalimanları", "price": 145.00, "change": 1.80, "changePercent": 1.26},
    "ENKAI.IS": {"name": "Enka İnşaat", "price": 83.50, "change": 0.95, "changePercent": 1.15},
    "FROTO.IS": {"name": "Ford Otosan", "price": 1250.00, "change": 15.00, "changePercent": 1.21},
    "TOASO.IS": {"name": "Tofaş", "price": 268.00, "change": 3.50, "changePercent": 1.32},
    "EKGYO.IS": {"name": "Emlak Konut GYO", "price": 22.50, "change": 0.35, "changePercent": 1.58},
    "GUBRF.IS": {"name": "Gübre Fabrikaları", "price": 410.00, "change": 6.25, "changePercent": 1.55},
    "HEKTS.IS": {"name": "Hektaş", "price": 95.00, "change": 1.10, "changePercent": 1.17},
    "ISCTR.IS": {"name": "İş Bankası C", "price": 18.20, "change": 0.15, "changePercent": 0.83},
    "ODAS.IS": {"name": "Odaş Elektrik", "price": 8.50, "change": 0.08, "changePercent": 0.95},
    "AKSEN.IS": {"name": "Aksa Enerji", "price": 68.00, "change": 0.75, "changePercent": 1.12},
    "ARCLK.IS": {"name": "Arçelik", "price": 180.00, "change": 2.00, "changePercent": 1.12},
    "PETKM.IS": {"name": "Petkim", "price": 22.00, "change": 0.18, "changePercent": 0.82},
    "TKFEN.IS": {"name": "Tekfen Holding", "price": 185.00, "change": 1.90, "changePercent": 1.04},
    "SASA.IS": {"name": "Sasa Polyester", "price": 65.00, "change": 0.55, "changePercent": 0.85},
    "KRDMD.IS": {"name": "Kardemir D", "price": 29.00, "change": 0.32, "changePercent": 1.12},
    "VAKBN.IS": {"name": "Vakıfbank", "price": 25.50, "change": 0.28, "changePercent": 1.11},
    "TRALT.IS": {"name": "Türk Alüminyum", "price": 42.00, "change": 0.45, "changePercent": 1.08},
}

def get_mock_data(symbol: str) -> dict:
    """Generate mock stock data for demo purposes"""
    import random
    from datetime import datetime, timedelta
    
    base = MOCK_STOCK_DATA.get(symbol, {
        "name": symbol.replace(".IS", ""),
        "price": 100.0,
        "change": 1.0,
        "changePercent": 1.0
    })
    
    # Add some randomness
    price_var = base["price"] * random.uniform(-0.02, 0.02)
    current_price = round(base["price"] + price_var, 2)
    prev_close = round(current_price - base["change"], 2)
    
    # Generate mock candles
    candles = []
    now = datetime.now()
    for i in range(30):
        day = now - timedelta(days=30-i)
        daily_var = base["price"] * random.uniform(-0.03, 0.03)
        o = round(base["price"] + daily_var, 2)
        h = round(o * random.uniform(1.0, 1.02), 2)
        l = round(o * random.uniform(0.98, 1.0), 2)
        c = round(random.uniform(l, h), 2)
        v = int(random.uniform(1000000, 5000000))
        candles.append({
            "timestamp": day.strftime("%Y-%m-%dT09:30:00"),
            "open": o, "high": h, "low": l, "close": c, "volume": v
        })
    
    return {
        "symbol": symbol,
        "name": base["name"],
        "price": current_price,
        "open": candles[-1]["open"],
        "high": candles[-1]["high"],
        "low": candles[-1]["low"],
        "volume": candles[-1]["volume"],
        "previousClose": prev_close,
        "change": base["change"],
        "changePercent": base["changePercent"],
        "currency": "TRY",
        "exchange": "IST",
        "timestamp": now.isoformat(),
        "candles": candles,
        "isMockData": True
    }

# ========== Stock Data Endpoints (Yahoo Finance via requests) ==========
import httpx

async def fetch_yahoo_quote(symbol: str) -> dict:
    """Fetch stock quote from Yahoo Finance API with mock fallback"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {"interval": "1d", "range": "1mo"}
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params, headers=headers)
            
            if response.status_code != 200:
                logger.warning(f"Yahoo returned {response.status_code} for {symbol}, using mock data")
                return get_mock_data(symbol)
            
            data = response.json()
            result = data.get("chart", {}).get("result", [])
            
            if not result:
                logger.warning(f"No chart result for {symbol}, using mock data")
                return get_mock_data(symbol)
            
            meta = result[0].get("meta", {})
            quote = result[0].get("indicators", {}).get("quote", [{}])[0]
            timestamps = result[0].get("timestamp", [])
            
            # Get latest values
            closes = quote.get("close", [])
            opens = quote.get("open", [])
            highs = quote.get("high", [])
            lows = quote.get("low", [])
            volumes = quote.get("volume", [])
            
            if not closes:
                logger.warning(f"No close data for {symbol}, using mock data")
                return get_mock_data(symbol)
            
            # Filter None values and get last valid
            valid_closes = [c for c in closes if c is not None]
            valid_opens = [o for o in opens if o is not None]
            valid_highs = [h for h in highs if h is not None]
            valid_lows = [l for l in lows if l is not None]
            valid_volumes = [v for v in volumes if v is not None]
            
            if not valid_closes:
                logger.warning(f"No valid closes for {symbol}, using mock data")
                return get_mock_data(symbol)
            
            current_price = valid_closes[-1]
            prev_close = meta.get("previousClose", current_price)
            change = current_price - prev_close if prev_close else 0
            change_percent = (change / prev_close * 100) if prev_close else 0
            
            return {
                "symbol": symbol,
                "name": meta.get("shortName", symbol),
                "price": round(current_price, 2),
                "open": round(valid_opens[-1], 2) if valid_opens else 0,
                "high": round(valid_highs[-1], 2) if valid_highs else 0,
                "low": round(valid_lows[-1], 2) if valid_lows else 0,
                "volume": valid_volumes[-1] if valid_volumes else 0,
                "previousClose": round(prev_close, 2),
                "change": round(change, 2),
                "changePercent": round(change_percent, 2),
                "currency": meta.get("currency", "TRY"),
                "exchange": meta.get("exchangeName", "IST"),
                "timestamp": timestamps[-1] if timestamps else None,
                "candles": [
                    {
                        "timestamp": timestamps[i] if i < len(timestamps) else None,
                        "open": valid_opens[i] if i < len(valid_opens) else None,
                        "high": valid_highs[i] if i < len(valid_highs) else None,
                        "low": valid_lows[i] if i < len(valid_lows) else None,
                        "close": valid_closes[i] if i < len(valid_closes) else None,
                        "volume": valid_volumes[i] if i < len(valid_volumes) else None,
                    }
                    for i in range(len(valid_closes))
                ],
                "isMockData": False
            }
    except Exception as e:
        logger.error(f"Yahoo Finance error for {symbol}: {e}")
        logger.info(f"Falling back to mock data for {symbol}")
        return get_mock_data(symbol)

@app.get("/api/stocks/{symbol}")
async def get_stock(symbol: str):
    """Get stock data from Yahoo Finance (with mock fallback)"""
    # Add .IS suffix if not present (for BIST stocks)
    if not symbol.endswith(".IS") and not "." in symbol:
        symbol = f"{symbol}.IS"
    
    data = await fetch_yahoo_quote(symbol)
    return data  # Always returns data (real or mock)

@app.get("/api/stocks/{symbol}/data")
async def get_stock_data(symbol: str, interval: str = "1d", period: str = "1mo"):
    """Get stock OHLCV data - Frontend compatible endpoint"""
    if not symbol.endswith(".IS") and not "." in symbol:
        symbol = f"{symbol}.IS"
    
    data = await fetch_yahoo_quote(symbol)
    
    # Convert candles to frontend expected format
    candles = data.get("candles", [])
    result = []
    for c in candles:
        ts = c.get("timestamp") or c.get("time")
        if ts:
            result.append({
                "timestamp": ts,
                "open": c.get("open"),
                "high": c.get("high"),
                "low": c.get("low"),
                "close": c.get("close"),
                "volume": c.get("volume")
            })
    
    return {
        "symbol": data["symbol"],
        "interval": interval,
        "period": period,
        "data": result,
        "isMockData": data.get("isMockData", False)
    }

@app.get("/api/stocks/{symbol}/current-price")
async def get_current_price(symbol: str):
    """Get current stock price"""
    if not symbol.endswith(".IS") and not "." in symbol:
        symbol = f"{symbol}.IS"
    
    data = await fetch_yahoo_quote(symbol)
    
    return {
        "symbol": data["symbol"],
        "price": data["price"],
        "change": data["change"],
        "changePercent": data["changePercent"],
        "timestamp": datetime.now().isoformat(),
        "isMockData": data.get("isMockData", False)
    }

@app.get("/api/stocks/{symbol}/info")
async def get_stock_info(symbol: str):
    """Get stock info"""
    if not symbol.endswith(".IS") and not "." in symbol:
        symbol = f"{symbol}.IS"
    
    data = await fetch_yahoo_quote(symbol)
    
    return {
        "symbol": data["symbol"],
        "name": data["name"],
        "currency": data["currency"],
        "exchange": data["exchange"],
        "price": data["price"],
        "change": data["change"],
        "changePercent": data["changePercent"],
        "isMockData": data.get("isMockData", False)
    }

@app.get("/api/stocks/{symbol}/indicators")
async def get_stock_indicators(symbol: str, interval: str = "1d", period: str = "1mo"):
    """Get basic indicators (simplified without pandas/numpy)"""
    if not symbol.endswith(".IS") and not "." in symbol:
        symbol = f"{symbol}.IS"
    
    data = await fetch_yahoo_quote(symbol)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    candles = data.get("candles", [])
    closes = [c["close"] for c in candles if c.get("close")]
    
    # Simple RSI calculation (14 period)
    rsi = 50  # Default neutral
    if len(closes) >= 15:
        gains = []
        losses = []
        for i in range(1, min(15, len(closes))):
            diff = closes[i] - closes[i-1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))
        
        avg_gain = sum(gains) / 14 if gains else 0
        avg_loss = sum(losses) / 14 if losses else 0.0001
        rs = avg_gain / avg_loss if avg_loss else 100
        rsi = 100 - (100 / (1 + rs))
    
    # Simple moving averages
    sma_20 = sum(closes[-20:]) / min(20, len(closes)) if closes else 0
    sma_50 = sum(closes[-50:]) / min(50, len(closes)) if closes else 0
    
    return {
        "symbol": symbol,
        "rsi": round(rsi, 2),
        "sma_20": round(sma_20, 2),
        "sma_50": round(sma_50, 2),
        "price": data["price"],
        "trend": "bullish" if data["price"] > sma_20 else "bearish",
        "rsi_signal": "oversold" if rsi < 30 else ("overbought" if rsi > 70 else "neutral")
    }

@app.get("/api/signals/{symbol}")
async def get_stock_signals(symbol: str, strategy: str = "hybrid"):
    """Get trading signals for a stock"""
    if not symbol.endswith(".IS") and not "." in symbol:
        symbol = f"{symbol}.IS"
    
    data = await fetch_yahoo_quote(symbol)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    # Simple signal based on price action
    change_pct = data.get("changePercent", 0)
    
    if change_pct > 2:
        signal = "STRONG_BUY"
        action = "AL"
    elif change_pct > 0.5:
        signal = "BUY"
        action = "AL"
    elif change_pct < -2:
        signal = "STRONG_SELL"
        action = "SAT"
    elif change_pct < -0.5:
        signal = "SELL"
        action = "SAT"
    else:
        signal = "HOLD"
        action = "BEKLE"
    
    return {
        "symbol": symbol,
        "signal": signal,
        "action": action,
        "price": data["price"],
        "change": data["change"],
        "changePercent": data["changePercent"],
        "confidence": min(abs(change_pct) * 10, 100),
        "strategy": strategy,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/signals")
async def get_signals():
    """Stub: Get trading signals"""
    return {"signals": [], "message": "Use /api/signals/{symbol} for specific stock signals"}

@app.get("/api/screener")
async def get_screener():
    """
    Stock screener - Backtest stratejisiyle günlük fırsatları tara
    BIST30 hisselerini analiz edip score >= 60 olanları döndürür
    """
    import random
    
    # BIST30 hisseleri
    BIST30 = [
        'THYAO.IS', 'GARAN.IS', 'AKBNK.IS', 'YKBNK.IS', 'EREGL.IS',
        'BIMAS.IS', 'ASELS.IS', 'KCHOL.IS', 'SAHOL.IS', 'SISE.IS',
        'TCELL.IS', 'TUPRS.IS', 'PGSUS.IS', 'TAVHL.IS', 'ENKAI.IS',
        'FROTO.IS', 'TOASO.IS', 'EKGYO.IS', 'GUBRF.IS', 'ODAS.IS',
        'AKSEN.IS', 'ARCLK.IS', 'PETKM.IS', 'TKFEN.IS', 'SASA.IS',
        'KRDMD.IS', 'ISCTR.IS', 'VAKBN.IS', 'HEKTS.IS'
    ]
    
    opportunities = []
    
    for symbol in BIST30:
        try:
            data = await fetch_yahoo_quote(symbol)
            if not data or data.get("isMockData"):
                continue
            
            candles = data.get("candles", [])
            if len(candles) < 50:
                continue
            
            # Son kapanışları al
            closes = [c["close"] for c in candles if c.get("close")]
            highs = [c["high"] for c in candles if c.get("high")]
            lows = [c["low"] for c in candles if c.get("low")]
            volumes = [c["volume"] for c in candles if c.get("volume")]
            
            if len(closes) < 50:
                continue
            
            curr = closes[-1]
            
            # EMA hesapla (basit)
            def ema(data, period):
                if len(data) < period:
                    return data[-1] if data else 0
                mult = 2 / (period + 1)
                result = sum(data[:period]) / period
                for price in data[period:]:
                    result = (price * mult) + (result * (1 - mult))
                return result
            
            ema9 = ema(closes, 9)
            ema21 = ema(closes, 21)
            ema50 = ema(closes, 50)
            
            # RSI hesapla
            gains = []
            losses = []
            for i in range(1, min(15, len(closes))):
                diff = closes[-i] - closes[-i-1]
                if diff > 0:
                    gains.append(diff)
                else:
                    losses.append(abs(diff))
            
            avg_gain = sum(gains) / 14 if gains else 0
            avg_loss = sum(losses) / 14 if losses else 0.0001
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            # ATR hesapla
            trs = []
            for i in range(-14, 0):
                if i-1 >= -len(closes):
                    tr = max(
                        highs[i] - lows[i],
                        abs(highs[i] - closes[i-1]),
                        abs(lows[i] - closes[i-1])
                    )
                    trs.append(tr)
            atr = sum(trs) / len(trs) if trs else curr * 0.02
            
            # SKOR HESAPLA (Backtest stratejisiyle aynı)
            score = 0
            
            # Trend skoru
            if curr > ema9 > ema21:
                score += 20
            if ema21 > ema50:
                score += 15
            
            # RSI skoru
            if 35 <= rsi <= 65:
                score += 20
            
            # Hacim skoru
            vol_avg = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else volumes[-1]
            if volumes[-1] > vol_avg:
                score += 15
            
            # Pozisyon skoru
            swing_low = min(lows[-10:])
            swing_high = max(highs[-10:])
            pos = (curr - swing_low) / (swing_high - swing_low + 0.0001)
            if 0.15 <= pos <= 0.55:
                score += 15
            
            # Momentum bonus
            if len(closes) >= 5:
                momentum = (closes[-1] - closes[-5]) / closes[-5] * 100
                if 0 < momentum < 5:
                    score += 10
            
            # Minimum skor kontrolü
            if score < 60:
                continue
            
            # Stop ve TP hesapla
            stop = curr - (atr * 2.0)
            risk = curr - stop
            
            if risk / curr < 0.015:  # Çok düşük risk
                continue
            
            tp1 = curr + (risk * 2.5)
            
            opportunities.append({
                "symbol": symbol,
                "name": data.get("name", symbol.replace(".IS", "")),
                "price": round(curr, 2),
                "score": score,
                "signal": "STRONG_BUY" if score >= 80 else "BUY",
                "action": "AL",
                "entry": round(curr, 2),
                "stop": round(stop, 2),
                "tp1": round(tp1, 2),
                "risk_percent": round((risk / curr) * 100, 2),
                "reward_percent": round(((tp1 - curr) / curr) * 100, 2),
                "rsi": round(rsi, 1),
                "trend": "UP" if curr > ema21 else "DOWN",
                "change": data.get("change", 0),
                "changePercent": data.get("changePercent", 0),
                "volume": data.get("volume", 0)
            })
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            continue
    
    # Score'a göre sırala, en yüksek 5 tanesini al
    opportunities.sort(key=lambda x: x["score"], reverse=True)
    top_opportunities = opportunities[:5]
    
    return {
        "results": top_opportunities,
        "total_scanned": len(BIST30),
        "opportunities_found": len(opportunities),
        "top_picks": len(top_opportunities),
        "strategy": "Hybrid Strategy v4",
        "min_score": 60,
        "timestamp": datetime.now().isoformat(),
        "disclaimer": "Bu veriler yatırım tavsiyesi değildir. Backtest sonuçları: WR 57.1%, PF 1.94"
    }

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




