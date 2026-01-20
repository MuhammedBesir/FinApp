"""
Advanced WebSocket Manager for Real-time Trading Data
Supports multiple channels: prices, signals, alerts, notifications
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Set, Optional, Any, Callable
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum
from dataclasses import dataclass, asdict, field
from app.utils.logger import logger


class ChannelType(str, Enum):
    """WebSocket channel types"""
    PRICE = "price"           # Real-time price updates
    SIGNAL = "signal"         # Trading signals
    ALERT = "alert"           # Price alerts
    NOTIFICATION = "notification"  # System notifications
    SCREENER = "screener"     # Screener updates
    ALL = "all"               # All channels


@dataclass
class WebSocketMessage:
    """Standard WebSocket message format"""
    channel: str
    event: str
    data: Any
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


@dataclass
class Subscription:
    """Client subscription info"""
    websocket: WebSocket
    channels: Set[str]
    tickers: Set[str]
    user_id: Optional[str] = None
    connected_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.connected_at is None:
            self.connected_at = datetime.now()


class AdvancedWebSocketManager:
    """
    Advanced WebSocket Manager with multi-channel support
    
    Features:
    - Multiple channel subscriptions (price, signal, alert, notification)
    - Ticker-specific subscriptions
    - Broadcast to specific channels/tickers
    - Connection health monitoring
    - Automatic cleanup of dead connections
    """
    
    def __init__(self):
        # All active connections: websocket -> Subscription
        self.connections: Dict[WebSocket, Subscription] = {}
        
        # Index by channel for fast broadcast
        self.channel_connections: Dict[str, Set[WebSocket]] = {
            channel.value: set() for channel in ChannelType
        }
        
        # Index by ticker for fast broadcast
        self.ticker_connections: Dict[str, Set[WebSocket]] = {}
        
        # Message queue for async processing
        self.message_queue: asyncio.Queue = asyncio.Queue()
        
        # Stats
        self.stats = {
            "total_connections": 0,
            "total_messages_sent": 0,
            "total_broadcasts": 0
        }
        
        logger.info("AdvancedWebSocketManager initialized")
    
    async def connect(
        self, 
        websocket: WebSocket, 
        channels: Optional[List[str]] = None,
        tickers: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Accept and register a new WebSocket connection
        
        Args:
            websocket: The WebSocket connection
            channels: List of channels to subscribe (default: all)
            tickers: List of tickers to subscribe (default: none - global)
            user_id: Optional user identifier
        """
        try:
            await websocket.accept()
            
            # Default to all channels if none specified
            if not channels:
                channels = [ChannelType.ALL.value]
            
            # Create subscription
            subscription = Subscription(
                websocket=websocket,
                channels=set(channels),
                tickers=set(tickers) if tickers else set(),
                user_id=user_id
            )
            
            # Register connection
            self.connections[websocket] = subscription
            
            # Add to channel indexes
            for channel in channels:
                if channel not in self.channel_connections:
                    self.channel_connections[channel] = set()
                self.channel_connections[channel].add(websocket)
            
            # Add to ticker indexes
            if tickers:
                for ticker in tickers:
                    if ticker not in self.ticker_connections:
                        self.ticker_connections[ticker] = set()
                    self.ticker_connections[ticker].add(websocket)
            
            self.stats["total_connections"] += 1
            
            logger.info(f"WebSocket connected: channels={channels}, tickers={tickers}, user={user_id}")
            
            # Send welcome message
            await self.send_to_client(websocket, WebSocketMessage(
                channel="system",
                event="connected",
                data={
                    "message": "Connected to Trading Bot WebSocket",
                    "subscribed_channels": list(channels),
                    "subscribed_tickers": list(tickers) if tickers else []
                }
            ))
            
            return True
            
        except Exception as e:
            logger.error(f"WebSocket connect error: {e}")
            return False
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket not in self.connections:
            return
        
        subscription = self.connections[websocket]
        
        # Remove from channel indexes
        for channel in subscription.channels:
            if channel in self.channel_connections:
                self.channel_connections[channel].discard(websocket)
        
        # Remove from ticker indexes
        for ticker in subscription.tickers:
            if ticker in self.ticker_connections:
                self.ticker_connections[ticker].discard(websocket)
        
        # Remove connection
        del self.connections[websocket]
        
        logger.info(f"WebSocket disconnected: user={subscription.user_id}")
    
    async def subscribe(self, websocket: WebSocket, channels: Optional[List[str]] = None, tickers: Optional[List[str]] = None):
        """Add subscriptions to an existing connection"""
        if websocket not in self.connections:
            return
        
        subscription = self.connections[websocket]
        
        if channels:
            for channel in channels:
                subscription.channels.add(channel)
                if channel not in self.channel_connections:
                    self.channel_connections[channel] = set()
                self.channel_connections[channel].add(websocket)
        
        if tickers:
            for ticker in tickers:
                subscription.tickers.add(ticker)
                if ticker not in self.ticker_connections:
                    self.ticker_connections[ticker] = set()
                self.ticker_connections[ticker].add(websocket)
        
        await self.send_to_client(websocket, WebSocketMessage(
            channel="system",
            event="subscribed",
            data={
                "channels": list(subscription.channels),
                "tickers": list(subscription.tickers)
            }
        ))
    
    async def unsubscribe(self, websocket: WebSocket, channels: Optional[List[str]] = None, tickers: Optional[List[str]] = None):
        """Remove subscriptions from a connection"""
        if websocket not in self.connections:
            return
        
        subscription = self.connections[websocket]
        
        if channels:
            for channel in channels:
                subscription.channels.discard(channel)
                if channel in self.channel_connections:
                    self.channel_connections[channel].discard(websocket)
        
        if tickers:
            for ticker in tickers:
                subscription.tickers.discard(ticker)
                if ticker in self.ticker_connections:
                    self.ticker_connections[ticker].discard(websocket)
        
        await self.send_to_client(websocket, WebSocketMessage(
            channel="system",
            event="unsubscribed",
            data={
                "channels": list(subscription.channels),
                "tickers": list(subscription.tickers)
            }
        ))
    
    async def send_to_client(self, websocket: WebSocket, message: WebSocketMessage) -> bool:
        """Send message to a specific client"""
        try:
            await websocket.send_text(message.to_json())
            self.stats["total_messages_sent"] += 1
            return True
        except Exception as e:
            logger.error(f"Error sending to client: {e}")
            self.disconnect(websocket)
            return False
    
    async def broadcast_to_channel(self, channel: str, message: WebSocketMessage, ticker: Optional[str] = None):
        """
        Broadcast message to all subscribers of a channel
        
        Args:
            channel: The channel to broadcast to
            message: The message to send
            ticker: Optional ticker filter
        """
        # Get connections subscribed to this channel
        connections = self.channel_connections.get(channel, set()).copy()
        
        # Also include "all" channel subscribers
        connections.update(self.channel_connections.get(ChannelType.ALL.value, set()))
        
        # Filter by ticker if specified
        if ticker:
            ticker_connections = self.ticker_connections.get(ticker, set())
            # Include connections that have no ticker filter OR are subscribed to this ticker
            filtered_connections = set()
            for ws in connections:
                if ws in self.connections:
                    sub = self.connections[ws]
                    if not sub.tickers or ticker in sub.tickers:
                        filtered_connections.add(ws)
            connections = filtered_connections
        
        # Send to all matching connections
        dead_connections = []
        for websocket in connections:
            try:
                await websocket.send_text(message.to_json())
                self.stats["total_messages_sent"] += 1
            except Exception:
                dead_connections.append(websocket)
        
        # Cleanup dead connections
        for ws in dead_connections:
            self.disconnect(ws)
        
        self.stats["total_broadcasts"] += 1
    
    async def broadcast_price_update(self, ticker: str, price_data: dict):
        """Broadcast price update for a ticker"""
        message = WebSocketMessage(
            channel=ChannelType.PRICE.value,
            event="price_update",
            data={
                "ticker": ticker,
                **price_data
            }
        )
        await self.broadcast_to_channel(ChannelType.PRICE.value, message, ticker)
    
    async def broadcast_signal(self, ticker: str, signal_data: dict):
        """Broadcast trading signal"""
        message = WebSocketMessage(
            channel=ChannelType.SIGNAL.value,
            event="new_signal",
            data={
                "ticker": ticker,
                **signal_data
            }
        )
        await self.broadcast_to_channel(ChannelType.SIGNAL.value, message, ticker)
        
        # Also send as notification
        await self.broadcast_notification(
            title=f"Yeni Sinyal: {ticker}",
            body=f"{signal_data.get('signal', 'HOLD')} - Güç: {signal_data.get('strength', 0)}%",
            type="signal",
            data={"ticker": ticker, "signal": signal_data}
        )
    
    async def broadcast_alert(self, ticker: str, alert_data: dict):
        """Broadcast price alert"""
        message = WebSocketMessage(
            channel=ChannelType.ALERT.value,
            event="alert_triggered",
            data={
                "ticker": ticker,
                **alert_data
            }
        )
        await self.broadcast_to_channel(ChannelType.ALERT.value, message, ticker)
    
    async def broadcast_notification(
        self, 
        title: str, 
        body: str, 
        type: str = "info",
        data: Optional[dict] = None,
        user_id: Optional[str] = None
    ):
        """
        Broadcast notification to clients
        
        Args:
            title: Notification title
            body: Notification body
            type: Notification type (info, success, warning, error, signal)
            data: Additional data
            user_id: Target specific user (None = all users)
        """
        message = WebSocketMessage(
            channel=ChannelType.NOTIFICATION.value,
            event="notification",
            data={
                "title": title,
                "body": body,
                "type": type,
                "data": data or {}
            }
        )
        
        if user_id:
            # Send to specific user
            for ws, sub in self.connections.items():
                if sub.user_id == user_id:
                    await self.send_to_client(ws, message)
        else:
            # Broadcast to all
            await self.broadcast_to_channel(ChannelType.NOTIFICATION.value, message)
    
    async def broadcast_screener_update(self, screener_data: dict):
        """Broadcast screener results update"""
        message = WebSocketMessage(
            channel=ChannelType.SCREENER.value,
            event="screener_update",
            data=screener_data
        )
        await self.broadcast_to_channel(ChannelType.SCREENER.value, message)
    
    def get_connection_count(self) -> int:
        """Get total active connections"""
        return len(self.connections)
    
    def get_channel_stats(self) -> dict:
        """Get statistics by channel"""
        return {
            channel: len(connections) 
            for channel, connections in self.channel_connections.items()
        }
    
    def get_ticker_stats(self) -> dict:
        """Get statistics by ticker"""
        return {
            ticker: len(connections) 
            for ticker, connections in self.ticker_connections.items()
        }
    
    def get_stats(self) -> dict:
        """Get overall statistics"""
        return {
            **self.stats,
            "active_connections": self.get_connection_count(),
            "channels": self.get_channel_stats(),
            "tickers": self.get_ticker_stats()
        }


# Global instance
ws_manager = AdvancedWebSocketManager()
