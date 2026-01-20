"""
JWT Authentication Middleware
Handles token validation for protected routes
"""
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.auth_service import decode_token, get_user_by_id
from app.models.base import SessionLocal
from app.utils.logger import logger


class JWTMiddleware(BaseHTTPMiddleware):
    """
    JWT Authentication Middleware
    Validates tokens and attaches user info to request state
    """
    
    # Paths that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/auth/login",
        "/api/auth/login/form",
        "/api/auth/register",
        "/api/auth/refresh",
        # Public API endpoints
        "/api/stocks",
        "/api/signals",
        "/api/news",
        "/api/ipo",
        "/api/screener",
        "/api/indicators",
    }
    
    # Path prefixes that don't require authentication
    PUBLIC_PREFIXES = [
        "/api/stocks/",
        "/api/signals/",
        "/api/news/",
        "/api/ipo/",
        "/api/screener/",
        "/api/indicators/",
        "/api/backtest/",
        "/api/chat/",
        "/api/ai/",
        "/api/alerts/",
        "/ws/",
    ]
    
    def __init__(self, app, strict_mode: bool = False):
        """
        Initialize middleware
        
        Args:
            app: FastAPI application
            strict_mode: If True, reject requests without valid token for protected routes
                        If False, allow but don't set user info
        """
        super().__init__(app)
        self.strict_mode = strict_mode
    
    def is_public_path(self, path: str) -> bool:
        """Check if path is public (doesn't require auth)"""
        if path in self.PUBLIC_PATHS:
            return True
        
        for prefix in self.PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return True
        
        return False
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and validate JWT if present"""
        path = request.url.path
        
        # Skip authentication for public paths
        if self.is_public_path(path):
            return await call_next(request)
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        token = None
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        
        # If no token and strict mode, reject
        if not token and self.strict_mode:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "detail": "Oturum açmanız gerekiyor",
                    "code": "UNAUTHORIZED"
                }
            )
        
        # Validate token if present
        if token:
            token_data = decode_token(token)
            
            if token_data and token_data.user_id:
                # Attach user info to request state
                request.state.user_id = token_data.user_id
                request.state.user_email = token_data.email
                request.state.is_authenticated = True
            else:
                request.state.is_authenticated = False
                
                # If strict mode and invalid token, reject
                if self.strict_mode:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "success": False,
                            "detail": "Geçersiz veya süresi dolmuş token",
                            "code": "INVALID_TOKEN"
                        }
                    )
        else:
            request.state.is_authenticated = False
        
        response = await call_next(request)
        return response


def get_optional_user(request: Request) -> Optional[dict]:
    """
    Get user from request state if authenticated
    Use this for endpoints where auth is optional
    """
    if hasattr(request.state, 'is_authenticated') and request.state.is_authenticated:
        return {
            "id": request.state.user_id,
            "email": request.state.user_email
        }
    return None
