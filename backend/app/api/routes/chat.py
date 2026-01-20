"""
Chat API Routes - Grup sohbet endpointleri
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict
from app.services.chat_service import chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])

class SendMessageRequest(BaseModel):
    user_id: str
    username: str
    content: str
    message_type: str = "text"
    reply_to: Optional[str] = None

class ReactionRequest(BaseModel):
    user_id: str
    emoji: str

class ShareTradeRequest(BaseModel):
    user_id: str
    username: str
    symbol: str
    action: str  # BUY/SELL
    price: float
    quantity: int
    pnl: Optional[float] = None

class JoinRoomRequest(BaseModel):
    user_id: str
    username: str

@router.get("/rooms")
async def get_rooms():
    """Tüm sohbet odalarını getir"""
    rooms = chat_service.get_rooms()
    return {
        "success": True,
        "rooms": rooms,
        "total_online": chat_service.get_online_users()
    }

@router.get("/rooms/{room_id}")
async def get_room(room_id: str):
    """Belirli bir odayı getir"""
    room = chat_service.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")
    
    return {
        "success": True,
        "room": room,
        "online_count": chat_service.get_online_users(room_id)
    }

@router.get("/rooms/{room_id}/messages")
async def get_messages(
    room_id: str,
    limit: int = Query(50, ge=1, le=100),
    before: Optional[str] = None
):
    """Oda mesajlarını getir"""
    messages = chat_service.get_messages(room_id, limit, before)
    return {
        "success": True,
        "room_id": room_id,
        "messages": messages,
        "count": len(messages)
    }

@router.post("/rooms/{room_id}/messages")
async def send_message(room_id: str, request: SendMessageRequest):
    """Mesaj gönder"""
    message = chat_service.add_message(
        room_id=room_id,
        user_id=request.user_id,
        username=request.username,
        content=request.content,
        message_type=request.message_type,
        reply_to=request.reply_to
    )
    
    if not message:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")
    
    return {
        "success": True,
        "message": message
    }

@router.post("/rooms/{room_id}/messages/{message_id}/reactions")
async def add_reaction(room_id: str, message_id: str, request: ReactionRequest):
    """Mesaja tepki ekle"""
    success = chat_service.add_reaction(room_id, message_id, request.user_id, request.emoji)
    
    if not success:
        raise HTTPException(status_code=404, detail="Mesaj bulunamadı")
    
    return {"success": True}

@router.delete("/rooms/{room_id}/messages/{message_id}/reactions")
async def remove_reaction(room_id: str, message_id: str, request: ReactionRequest):
    """Mesajdan tepki kaldır"""
    success = chat_service.remove_reaction(room_id, message_id, request.user_id, request.emoji)
    
    if not success:
        raise HTTPException(status_code=404, detail="Mesaj veya tepki bulunamadı")
    
    return {"success": True}

@router.post("/rooms/{room_id}/share-trade")
async def share_trade(room_id: str, request: ShareTradeRequest):
    """İşlem paylaş"""
    trade_data = {
        "symbol": request.symbol,
        "action": request.action,
        "price": request.price,
        "quantity": request.quantity,
        "pnl": request.pnl
    }
    
    message = chat_service.share_trade(
        room_id=room_id,
        user_id=request.user_id,
        username=request.username,
        trade_data=trade_data
    )
    
    if not message:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")
    
    return {
        "success": True,
        "message": message
    }

@router.post("/rooms/{room_id}/join")
async def join_room(room_id: str, request: JoinRoomRequest):
    """Odaya katıl"""
    if room_id not in [r["id"] for r in chat_service.get_rooms()]:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")
    
    chat_service.user_join(request.user_id, request.username, room_id)
    
    return {
        "success": True,
        "room_id": room_id,
        "online_count": chat_service.get_online_users(room_id)
    }

@router.post("/rooms/{room_id}/leave")
async def leave_room(room_id: str, user_id: str):
    """Odadan ayrıl"""
    chat_service.user_leave(user_id)
    
    return {
        "success": True,
        "room_id": room_id
    }

@router.get("/online")
async def get_online_stats():
    """Online kullanıcı istatistikleri"""
    rooms = chat_service.get_rooms()
    room_stats = {}
    
    for room in rooms:
        room_stats[room["id"]] = chat_service.get_online_users(room["id"])
    
    return {
        "success": True,
        "total_online": chat_service.get_online_users(),
        "by_room": room_stats
    }
