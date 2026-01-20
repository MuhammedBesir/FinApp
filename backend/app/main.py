"""
FastAPI Main Application
Trading Bot API Server
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import stocks, signals, backtest, indicators, screener, alerts, news, chat, ipo, ai, market
from app.api.routes import auth, portfolio
from app.api.routes import websocket as ws_routes
from app.middleware.rate_limiter import RateLimitMiddleware
from app.models.base import init_db
from app.services.data_fetcher import DataFetcher
from app.services.technical_analysis import TechnicalAnalysis
from app.services.ipo_service import ipo_service
from app.services.ipo_scheduler import setup_ipo_scheduler, start_ipo_scheduler, stop_ipo_scheduler
from app.services.websocket_manager import ws_manager
from app.utils.logger import logger
from datetime import datetime, timezone
import asyncio
import json

# Create FastAPI app
app = FastAPI(
    title="Trading Bot API",
    description="Algorithmic Trading Bot for BIST stocks with real-time technical analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Rate Limiting
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.rate_limit_per_minute,
    requests_per_hour=settings.rate_limit_per_hour,
    burst_limit=settings.rate_limit_burst,
    enabled=settings.rate_limit_enabled
)

# Include routers
app.include_router(auth.router, prefix="/api")  # Auth routes first
app.include_router(portfolio.router, prefix="/api")  # Portfolio routes
app.include_router(stocks.router, prefix="/api")
app.include_router(signals.router, prefix="/api")
app.include_router(backtest.router, prefix="/api")
app.include_router(indicators.router, prefix="/api")
app.include_router(screener.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(news.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(ipo.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(market.router, prefix="/api")

# Include WebSocket routes
app.include_router(ws_routes.router, tags=["WebSocket"])

# Initialize services
data_fetcher = DataFetcher()
tech_analysis = TechnicalAnalysis()


# IPO Auto-update callback
async def ipo_update_callback():
    """IPO verilerini güncelle (scheduler tarafından çağrılır)"""
    try:
        logger.info("IPO Scheduler: Running automatic update...")
        result = await ipo_service.refresh_data_async()
        logger.info(f"IPO Scheduler: Update completed - {result}")
        return result
    except Exception as e:
        logger.error(f"IPO Scheduler: Update failed - {e}")
        raise


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("=" * 50)
    logger.info("Trading Bot API Starting...")
    logger.info(f"Environment: {settings.log_level}")
    logger.info(f"CORS Origins: {settings.cors_origins_list}")
    logger.info("=" * 50)
    
    # Initialize database tables
    try:
        init_db()
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    # IPO Scheduler'ı başlat
    try:
        setup_ipo_scheduler(ipo_update_callback)
        start_ipo_scheduler()
        logger.info("IPO Auto-Update Scheduler started")
    except Exception as e:
        logger.error(f"Failed to start IPO Scheduler: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Trading Bot API Shutting down...")
    
    # IPO Scheduler'ı durdur
    try:
        stop_ipo_scheduler()
        logger.info("IPO Scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping IPO Scheduler: {e}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Trading Bot API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with database status"""
    from app.models.base import check_db_connection
    
    db_healthy = check_db_connection()
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "service": "trading-bot-api",
        "version": "1.0.0",
        "database": "connected" if db_healthy else "disconnected",
        "timestamp": datetime.now(timezone.utc).isoformat() if 'datetime' in dir() else None
    }


@app.get("/api/market-status")
async def get_market_status():
    """Get market status"""
    try:
        status = data_fetcher.get_market_status()
        return status
    except Exception as e:
        logger.error(f"Error getting market status: {e}")
        return {"error": str(e)}


# WebSocket endpoint for real-time data
class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, ticker: str):
        """Accept new connection"""
        await websocket.accept()
        if ticker not in self.active_connections:
            self.active_connections[ticker] = []
        self.active_connections[ticker].append(websocket)
        logger.info(f"WebSocket connected for {ticker}, total: {len(self.active_connections[ticker])}")
    
    def disconnect(self, websocket: WebSocket, ticker: str):
        """Remove connection"""
        if ticker in self.active_connections:
            self.active_connections[ticker].remove(websocket)
            logger.info(f"WebSocket disconnected for {ticker}, remaining: {len(self.active_connections[ticker])}")
    
    async def broadcast(self, ticker: str, data: dict):
        """Broadcast data to all connections for a ticker"""
        if ticker in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[ticker]:
                try:
                    await connection.send_json(data)
                except:
                    dead_connections.append(connection)
            
            # Remove dead connections
            for conn in dead_connections:
                self.active_connections[ticker].remove(conn)


manager = ConnectionManager()


@app.websocket("/ws/realtime/{ticker}")
async def websocket_endpoint(websocket: WebSocket, ticker: str):
    """
    WebSocket endpoint for real-time data streaming
    
    Args:
        ticker: Stock ticker symbol
    """
    await manager.connect(websocket, ticker)
    
    # Validate ticker first
    if not data_fetcher.validate_ticker(ticker):
        await websocket.send_json({"error": f"Invalid ticker: {ticker}"})
        await websocket.close()
        manager.disconnect(websocket, ticker)
        return
    
    consecutive_errors = 0
    max_consecutive_errors = 3
    
    try:
        while True:
            # Fetch latest data
            try:
                df = data_fetcher.fetch_realtime_data(ticker, interval="1m", period="1d")
                
                if not df.empty:
                    # Reset error counter on success
                    consecutive_errors = 0
                    
                    # Calculate indicators
                    df_with_indicators = tech_analysis.calculate_all_indicators(df)
                    latest_indicators = tech_analysis.get_latest_indicators(df_with_indicators)
                    
                    # Get latest price data
                    latest = df.iloc[-1]
                    
                    # Prepare data
                    data = {
                        "ticker": ticker,
                        "timestamp": str(df.index[-1]),
                        "price": {
                            "open": float(latest['open']),
                            "high": float(latest['high']),
                            "low": float(latest['low']),
                            "close": float(latest['close']),
                            "volume": int(latest['volume'])
                        },
                        "indicators": latest_indicators
                    }
                    
                    # Check if websocket is still connected before sending
                    if websocket.client_state.name == "CONNECTED":
                        await websocket.send_json(data)
                    else:
                        break
                else:
                    # No data available
                    consecutive_errors += 1
                    logger.warning(f"No data for {ticker}, consecutive errors: {consecutive_errors}")
                    
                    if consecutive_errors >= max_consecutive_errors:
                        if websocket.client_state.name == "CONNECTED":
                            await websocket.send_json({"error": f"No data available for {ticker} after {max_consecutive_errors} attempts"})
                        break
                    
                    if websocket.client_state.name == "CONNECTED":
                        await websocket.send_json({"status": "waiting", "message": f"No data available for {ticker}"})
                    else:
                        break
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in WebSocket data fetch for {ticker}: {e}, consecutive errors: {consecutive_errors}")
                
                # Check connection before sending error
                if websocket.client_state.name != "CONNECTED":
                    break
                
                if consecutive_errors >= max_consecutive_errors:
                    try:
                        await websocket.send_json({"error": f"Too many errors for {ticker}: {str(e)}"})
                    except:
                        pass
                    break
                
                try:
                    await websocket.send_json({"error": str(e), "retry": consecutive_errors})
                except:
                    break
            
            # Wait 3 seconds before next update for better responsiveness
            await asyncio.sleep(3)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, ticker)
        logger.info(f"WebSocket disconnected for {ticker}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, ticker)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )
