"""
WebSocket Routes for Real-time Data Streaming
Handles WebSocket connections for prices, signals, alerts, and notifications
"""
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional, List
from app.services.websocket_manager import ws_manager, ChannelType, WebSocketMessage
from app.services.data_fetcher import DataFetcher
from app.services.technical_analysis import TechnicalAnalysis
from app.services.signal_generator import SignalGenerator
from app.utils.logger import logger

router = APIRouter()

# Initialize services
data_fetcher = DataFetcher()
tech_analysis = TechnicalAnalysis()


@router.websocket("/ws/stream")
async def websocket_stream(
    websocket: WebSocket,
    channels: str = Query(default="all", description="Comma-separated channels: price,signal,alert,notification,all"),
    tickers: str = Query(default="", description="Comma-separated tickers to subscribe"),
    user_id: str = Query(default=None, description="User ID for targeted notifications")
):
    """
    Main WebSocket endpoint for real-time data streaming
    
    Channels:
    - price: Real-time price updates
    - signal: Trading signals
    - alert: Price alerts
    - notification: System notifications
    - all: All channels
    
    Usage:
    - ws://localhost:8000/ws/stream?channels=price,signal&tickers=THYAO.IS,GARAN.IS
    """
    # Parse channels and tickers
    channel_list = [c.strip() for c in channels.split(",") if c.strip()]
    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()] if tickers else []
    
    # Connect
    connected = await ws_manager.connect(
        websocket=websocket,
        channels=channel_list,
        tickers=ticker_list if ticker_list else [],
        user_id=user_id
    )
    
    if not connected:
        return
    
    # Initialize tasks list before try block
    tasks: List[asyncio.Task] = []
    
    try:
        # Start background tasks for subscribed channels
        
        if "price" in channel_list or "all" in channel_list:
            if ticker_list:
                for ticker in ticker_list:
                    tasks.append(asyncio.create_task(
                        price_update_loop(websocket, ticker)
                    ))
        
        # Handle incoming messages (subscribe/unsubscribe commands)
        while True:
            try:
                data = await websocket.receive_json()
                await handle_client_message(websocket, data)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket receive error: {e}")
                break
    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cancel all background tasks
        for task in tasks:
            task.cancel()
        ws_manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, data: dict):
    """Handle incoming messages from client"""
    action = data.get("action")
    
    if action == "subscribe":
        channels = data.get("channels", [])
        tickers = data.get("tickers", [])
        await ws_manager.subscribe(websocket, channels, tickers)
        
        # Start price updates for new tickers
        if tickers and ("price" in channels or not channels):
            for ticker in tickers:
                asyncio.create_task(price_update_loop(websocket, ticker))
    
    elif action == "unsubscribe":
        channels = data.get("channels", [])
        tickers = data.get("tickers", [])
        await ws_manager.unsubscribe(websocket, channels, tickers)
    
    elif action == "ping":
        await ws_manager.send_to_client(websocket, WebSocketMessage(
            channel="system",
            event="pong",
            data={"timestamp": data.get("timestamp")}
        ))
    
    elif action == "get_stats":
        stats = ws_manager.get_stats()
        await ws_manager.send_to_client(websocket, WebSocketMessage(
            channel="system",
            event="stats",
            data=stats
        ))


async def price_update_loop(websocket: WebSocket, ticker: str, interval: float = 2.0):
    """
    Background task to send price updates for a ticker
    
    Args:
        websocket: Client WebSocket
        ticker: Stock ticker
        interval: Update interval in seconds
    """
    consecutive_errors = 0
    max_errors = 5
    
    while True:
        try:
            # Check if connection is still active
            if websocket not in ws_manager.connections:
                break
            
            # Check if still subscribed to this ticker
            subscription = ws_manager.connections.get(websocket)
            if subscription and ticker not in subscription.tickers:
                break
            
            # Fetch data
            df = data_fetcher.fetch_realtime_data(ticker, interval="1m", period="1d")
            
            if not df.empty:
                consecutive_errors = 0
                
                # Calculate indicators
                df_with_indicators = tech_analysis.calculate_all_indicators(df)
                latest_indicators = tech_analysis.get_latest_indicators(df_with_indicators)
                
                # Get latest price
                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest
                
                # Calculate change
                change = float(latest['close']) - float(prev['close'])
                change_percent = (change / float(prev['close'])) * 100 if float(prev['close']) > 0 else 0
                
                # Broadcast price update
                await ws_manager.broadcast_price_update(ticker, {
                    "timestamp": str(df.index[-1]),
                    "open": float(latest['open']),
                    "high": float(latest['high']),
                    "low": float(latest['low']),
                    "close": float(latest['close']),
                    "volume": int(latest['volume']),
                    "change": round(change, 4),
                    "change_percent": round(change_percent, 2),
                    "indicators": latest_indicators
                })
            else:
                consecutive_errors += 1
                if consecutive_errors >= max_errors:
                    logger.warning(f"Too many errors for {ticker}, stopping updates")
                    break
            
            await asyncio.sleep(interval)
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"Price update error for {ticker}: {e}")
            if consecutive_errors >= max_errors:
                break
            await asyncio.sleep(interval)


@router.websocket("/ws/signals/{ticker}")
async def websocket_signals(websocket: WebSocket, ticker: str):
    """
    WebSocket endpoint for real-time trading signals
    Sends signal updates every 5 seconds
    """
    connected = await ws_manager.connect(
        websocket=websocket,
        channels=[ChannelType.SIGNAL.value],
        tickers=[ticker]
    )
    
    if not connected:
        return
    
    signal_generator = SignalGenerator(strategy_type="moderate")
    last_signal = None
    
    try:
        while True:
            try:
                # Fetch data and generate signal
                df = data_fetcher.fetch_realtime_data(ticker, interval="5m", period="1d")
                
                if not df.empty:
                    df_with_indicators = tech_analysis.calculate_all_indicators(df)
                    latest_indicators = tech_analysis.get_latest_indicators(df_with_indicators)
                    signal = signal_generator.generate_signal(df_with_indicators, latest_indicators)
                    
                    # Check if signal changed
                    current_signal = signal.get("signal") if signal else None
                    
                    if signal and current_signal != last_signal:
                        last_signal = current_signal
                        
                        # Broadcast signal
                        await ws_manager.broadcast_signal(ticker, {
                            "signal": signal.get("signal"),
                            "strength": signal.get("strength"),
                            "confidence": signal.get("confidence"),
                            "entry_price": signal.get("entry_price"),
                            "stop_loss": signal.get("stop_loss"),
                            "take_profit": signal.get("take_profit"),
                            "reasons": signal.get("reasons", [])
                        })
                
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Signal update error for {ticker}: {e}")
                await asyncio.sleep(5)
    
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket)


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: str = Query(default=None)
):
    """
    WebSocket endpoint for receiving notifications
    """
    connected = await ws_manager.connect(
        websocket=websocket,
        channels=[ChannelType.NOTIFICATION.value],
        user_id=user_id
    )
    
    if not connected:
        return
    
    try:
        while True:
            # Keep connection alive, handle ping/pong
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0
                )
                await handle_client_message(websocket, data)
            except asyncio.TimeoutError:
                # Send heartbeat
                await ws_manager.send_to_client(websocket, WebSocketMessage(
                    channel="system",
                    event="heartbeat",
                    data={}
                ))
            except WebSocketDisconnect:
                break
    except Exception as e:
        logger.error(f"Notification WebSocket error: {e}")
    finally:
        ws_manager.disconnect(websocket)


# HTTP endpoints for broadcasting (admin/internal use)
@router.post("/ws/broadcast/notification")
async def broadcast_notification(
    title: str,
    body: str,
    type: str = "info",
    user_id: Optional[str] = None
):
    """
    Send a notification to all connected clients (or specific user)
    """
    await ws_manager.broadcast_notification(
        title=title,
        body=body,
        type=type,
        user_id=user_id
    )
    return {"status": "sent", "connections": ws_manager.get_connection_count()}


@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return ws_manager.get_stats()
