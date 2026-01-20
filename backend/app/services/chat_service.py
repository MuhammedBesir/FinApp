"""
Chat Service - Grup sohbet yönetimi
"""
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid
import asyncio

class MessageType(Enum):
    TEXT = "text"
    IMAGE = "image"
    TRADE_SHARE = "trade_share"
    STOCK_MENTION = "stock_mention"
    SYSTEM = "system"

@dataclass
class ChatUser:
    """Chat kullanıcısı"""
    id: str
    username: str
    avatar: str = "🐂"
    is_online: bool = True
    last_seen: datetime = field(default_factory=datetime.now)
    joined_at: datetime = field(default_factory=datetime.now)
    role: str = "member"  # admin, moderator, member

@dataclass
class ChatMessage:
    """Sohbet mesajı"""
    id: str
    room_id: str
    user_id: str
    username: str
    content: str
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime = field(default_factory=datetime.now)
    edited: bool = False
    reactions: Dict[str, List[str]] = field(default_factory=dict)  # emoji: [user_ids]
    reply_to: Optional[str] = None
    mentions: List[str] = field(default_factory=list)  # mentioned stock symbols
    
    def to_dict(self):
        return {
            "id": self.id,
            "room_id": self.room_id,
            "user_id": self.user_id,
            "username": self.username,
            "content": self.content,
            "message_type": self.message_type.value,
            "timestamp": self.timestamp.isoformat(),
            "edited": self.edited,
            "reactions": self.reactions,
            "reply_to": self.reply_to,
            "mentions": self.mentions
        }

@dataclass
class ChatRoom:
    """Sohbet odası"""
    id: str
    name: str
    description: str = ""
    icon: str = "💬"
    is_private: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    members: List[str] = field(default_factory=list)  # user_ids
    admins: List[str] = field(default_factory=list)  # user_ids
    pinned_messages: List[str] = field(default_factory=list)  # message_ids
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "is_private": self.is_private,
            "created_at": self.created_at.isoformat(),
            "member_count": len(self.members),
            "pinned_count": len(self.pinned_messages)
        }

class ChatService:
    """Chat servisi - bellek içi basit implementasyon"""
    
    def __init__(self):
        self.rooms: Dict[str, ChatRoom] = {}
        self.messages: Dict[str, List[ChatMessage]] = {}  # room_id -> messages
        self.users: Dict[str, ChatUser] = {}
        self.online_users: Dict[str, str] = {}  # user_id -> room_id (currently in)
        
        # Varsayılan odaları oluştur
        self._create_default_rooms()
        
    def _create_default_rooms(self):
        """Varsayılan sohbet odalarını oluştur"""
        default_rooms = [
            ("general", "Genel Sohbet", "Tüm konular için genel sohbet odası", "💬"),
            ("bist30", "BIST 30", "BIST 30 hisseleri hakkında tartışmalar", "📊"),
            ("teknik-analiz", "Teknik Analiz", "Teknik analiz ve grafikler", "📈"),
            ("haberler", "Haberler", "Piyasa haberleri ve duyurular", "📰"),
            ("halka-arz", "Halka Arz", "Yeni halka arzlar hakkında tartışmalar", "🚀"),
            ("yeni-baslayanlara", "Yeni Başlayanlara", "Borsa'ya yeni başlayanlar için", "🎓"),
        ]
        
        for room_id, name, desc, icon in default_rooms:
            self.rooms[room_id] = ChatRoom(
                id=room_id,
                name=name,
                description=desc,
                icon=icon
            )
            self.messages[room_id] = []
            
            # Hoşgeldin mesajı ekle
            welcome_msg = ChatMessage(
                id=str(uuid.uuid4()),
                room_id=room_id,
                user_id="system",
                username="Sistem",
                content=f"🎉 {name} odasına hoş geldiniz! {desc}",
                message_type=MessageType.SYSTEM
            )
            self.messages[room_id].append(welcome_msg)
    
    def get_rooms(self) -> List[Dict]:
        """Tüm odaları getir"""
        return [room.to_dict() for room in self.rooms.values()]
    
    def get_room(self, room_id: str) -> Optional[Dict]:
        """Belirli bir odayı getir"""
        room = self.rooms.get(room_id)
        if room:
            return room.to_dict()
        return None
    
    def get_messages(self, room_id: str, limit: int = 50, before: Optional[str] = None) -> List[Dict]:
        """Oda mesajlarını getir"""
        if room_id not in self.messages:
            return []
        
        messages = self.messages[room_id]
        
        if before:
            # before mesajından önceki mesajları getir
            before_idx = None
            for i, msg in enumerate(messages):
                if msg.id == before:
                    before_idx = i
                    break
            if before_idx:
                messages = messages[:before_idx]
        
        # Son 'limit' mesajı getir
        return [msg.to_dict() for msg in messages[-limit:]]
    
    def add_message(self, room_id: str, user_id: str, username: str, content: str, 
                    message_type: str = "text", reply_to: Optional[str] = None) -> Optional[Dict]:
        """Yeni mesaj ekle"""
        if room_id not in self.messages:
            return None
        
        # Hisse sembollerini bul
        mentions = self._extract_stock_mentions(content)
        
        msg_type = MessageType.TEXT
        try:
            msg_type = MessageType(message_type)
        except ValueError:
            pass
        
        message = ChatMessage(
            id=str(uuid.uuid4()),
            room_id=room_id,
            user_id=user_id,
            username=username,
            content=content,
            message_type=msg_type,
            reply_to=reply_to,
            mentions=mentions
        )
        
        self.messages[room_id].append(message)
        
        # Maksimum 1000 mesaj tut
        if len(self.messages[room_id]) > 1000:
            self.messages[room_id] = self.messages[room_id][-500:]
        
        return message.to_dict()
    
    def _extract_stock_mentions(self, content: str) -> List[str]:
        """Mesajdaki hisse sembollerini çıkar (örn: $THYAO)"""
        import re
        pattern = r'\$([A-Z]{3,5})'
        matches = re.findall(pattern, content.upper())
        return list(set(matches))
    
    def add_reaction(self, room_id: str, message_id: str, user_id: str, emoji: str) -> bool:
        """Mesaja tepki ekle"""
        if room_id not in self.messages:
            return False
        
        for msg in self.messages[room_id]:
            if msg.id == message_id:
                if emoji not in msg.reactions:
                    msg.reactions[emoji] = []
                if user_id not in msg.reactions[emoji]:
                    msg.reactions[emoji].append(user_id)
                return True
        return False
    
    def remove_reaction(self, room_id: str, message_id: str, user_id: str, emoji: str) -> bool:
        """Mesajdan tepki kaldır"""
        if room_id not in self.messages:
            return False
        
        for msg in self.messages[room_id]:
            if msg.id == message_id:
                if emoji in msg.reactions and user_id in msg.reactions[emoji]:
                    msg.reactions[emoji].remove(user_id)
                    if not msg.reactions[emoji]:
                        del msg.reactions[emoji]
                    return True
        return False
    
    def get_online_users(self, room_id: Optional[str] = None) -> int:
        """Online kullanıcı sayısı"""
        if room_id:
            return sum(1 for r in self.online_users.values() if r == room_id)
        return len(self.online_users)
    
    def user_join(self, user_id: str, username: str, room_id: str = "general"):
        """Kullanıcı odaya katıldı"""
        if user_id not in self.users:
            self.users[user_id] = ChatUser(id=user_id, username=username)
        self.users[user_id].is_online = True
        self.users[user_id].last_seen = datetime.now()
        self.online_users[user_id] = room_id
    
    def user_leave(self, user_id: str):
        """Kullanıcı ayrıldı"""
        if user_id in self.users:
            self.users[user_id].is_online = False
            self.users[user_id].last_seen = datetime.now()
        if user_id in self.online_users:
            del self.online_users[user_id]
    
    def share_trade(self, room_id: str, user_id: str, username: str, 
                    trade_data: Dict) -> Optional[Dict]:
        """İşlem paylaş"""
        symbol = trade_data.get("symbol", "")
        action = trade_data.get("action", "")  # BUY/SELL
        price = trade_data.get("price", 0)
        quantity = trade_data.get("quantity", 0)
        pnl = trade_data.get("pnl")
        
        emoji = "🟢" if action == "BUY" else "🔴"
        pnl_str = ""
        if pnl is not None:
            pnl_emoji = "📈" if pnl > 0 else "📉"
            pnl_str = f" | {pnl_emoji} PnL: %{pnl:.2f}"
        
        content = f"{emoji} {action} ${symbol} @ ₺{price:,.2f} x {quantity}{pnl_str}"
        
        return self.add_message(
            room_id=room_id,
            user_id=user_id,
            username=username,
            content=content,
            message_type="trade_share"
        )

# Global instance
chat_service = ChatService()
