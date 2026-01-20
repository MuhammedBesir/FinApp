"""
AI Assistant API Routes
AI Trading Asistan endpointleri
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.services.ai_assistant import get_ai_assistant

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    context: Optional[Dict[str, Any]] = None


class PortfolioAnalysisRequest(BaseModel):
    holdings: List[Dict[str, Any]] = []
    trades: List[Dict[str, Any]] = []
    stats: Dict[str, Any] = {}


class TradeAnalysisRequest(BaseModel):
    ticker: str
    entryPrice: float
    exitPrice: float = 0
    quantity: int
    type: str = "long"


class ChatResponse(BaseModel):
    success: bool
    response: dict
    

@router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    """AI asistan ile sohbet"""
    try:
        assistant = get_ai_assistant()
        response = await assistant.chat(request.user_id, request.message, request.context)
        
        return {
            "success": True,
            "response": {
                "id": response.id,
                "role": response.role,
                "content": response.content,
                "timestamp": response.timestamp.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI yanıt hatası: {str(e)}")


@router.post("/portfolio-analysis")
async def analyze_portfolio(request: PortfolioAnalysisRequest):
    """Portföy analizi yap"""
    try:
        assistant = get_ai_assistant()
        analysis = await assistant.analyze_portfolio({
            "holdings": request.holdings,
            "trades": request.trades,
            "stats": request.stats
        })
        
        return {
            "success": True,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portföy analiz hatası: {str(e)}")


@router.post("/trade-analysis")
async def analyze_trade(request: TradeAnalysisRequest):
    """İşlem analizi yap"""
    try:
        assistant = get_ai_assistant()
        analysis = await assistant.analyze_trade({
            "ticker": request.ticker,
            "entryPrice": request.entryPrice,
            "exitPrice": request.exitPrice,
            "quantity": request.quantity,
            "type": request.type
        })
        
        return {
            "success": True,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"İşlem analiz hatası: {str(e)}")


@router.get("/market-summary")
async def get_market_summary():
    """Piyasa özeti al"""
    try:
        assistant = get_ai_assistant()
        summary = await assistant.get_market_summary()
        
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Piyasa özeti hatası: {str(e)}")


@router.get("/suggestions")
async def get_suggestions():
    """Öneri sorularını getir"""
    assistant = get_ai_assistant()
    suggestions = assistant.get_suggestions()
    
    return {
        "success": True,
        "suggestions": suggestions
    }


@router.get("/quick-actions")
async def get_quick_actions():
    """Hızlı eylemler listesi"""
    return {
        "success": True,
        "actions": [
            {"id": "portfolio", "label": "Portföyümü Analiz Et", "icon": "briefcase", "color": "blue"},
            {"id": "market", "label": "Piyasa Özeti", "icon": "trending-up", "color": "green"},
            {"id": "rsi", "label": "RSI Nedir?", "icon": "bar-chart", "color": "purple"},
            {"id": "stoploss", "label": "Stop-Loss Stratejileri", "icon": "shield", "color": "red"},
            {"id": "macd", "label": "MACD Nasıl Kullanılır?", "icon": "activity", "color": "orange"},
            {"id": "risk", "label": "Risk Yönetimi", "icon": "alert-triangle", "color": "yellow"},
        ]
    }


@router.get("/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 20):
    """Sohbet geçmişini getir"""
    assistant = get_ai_assistant()
    history = assistant.get_conversation_history(user_id, limit)
    
    return {
        "success": True,
        "messages": history,
        "count": len(history)
    }


@router.delete("/history/{user_id}")
async def clear_chat_history(user_id: str):
    """Sohbet geçmişini temizle"""
    assistant = get_ai_assistant()
    assistant.clear_conversation(user_id)
    
    return {
        "success": True,
        "message": "Sohbet geçmişi temizlendi"
    }


@router.get("/analysis/{ticker}")
async def get_stock_analysis(ticker: str):
    """Hisse için AI analizi"""
    try:
        assistant = get_ai_assistant()
        analysis = await assistant.get_stock_analysis(ticker.upper())
        
        return {
            "success": True,
            "ticker": ticker.upper(),
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analiz hatası: {str(e)}")
