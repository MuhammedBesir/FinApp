"""
Rate Limiting Middleware for FastAPI
Prevents API abuse with configurable limits
"""
import time
from collections import defaultdict
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import logger


class RateLimiter:
    """
    Token bucket rate limiter implementation
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10
    ):
        """
        Initialize rate limiter
        
        Args:
            requests_per_minute: Maximum requests allowed per minute
            requests_per_hour: Maximum requests allowed per hour
            burst_limit: Maximum burst requests allowed
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit
        
        # Storage for tracking requests: {ip: [(timestamp, count), ...]}
        self.minute_requests: Dict[str, list] = defaultdict(list)
        self.hour_requests: Dict[str, list] = defaultdict(list)
        self.burst_requests: Dict[str, Tuple[float, int]] = {}
        
        # Whitelist for trusted IPs/paths
        self.whitelist_ips = {"127.0.0.1", "::1"}
        self.whitelist_paths = {"/health", "/docs", "/redoc", "/openapi.json"}
        
        # Stricter limits for auth endpoints (prevent brute force)
        self.auth_paths = {
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/login/form"
        }
        self.auth_limit_per_minute = 5  # Only 5 login attempts per minute
        
    def _clean_old_requests(self, requests: list, window_seconds: int) -> list:
        """Remove requests older than the time window"""
        current_time = time.time()
        return [r for r in requests if current_time - r < window_seconds]
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def is_allowed(self, request: Request) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check if request is allowed based on rate limits
        
        Returns:
            Tuple of (is_allowed, error_message, retry_after_seconds)
        """
        client_ip = self._get_client_ip(request)
        path = request.url.path
        current_time = time.time()
        
        # Check whitelist
        if client_ip in self.whitelist_ips:
            return True, None, None
        
        if path in self.whitelist_paths:
            return True, None, None
        
        # Stricter rate limiting for auth endpoints (brute force protection)
        if path in self.auth_paths:
            auth_key = f"auth:{client_ip}"
            self.minute_requests[auth_key] = self._clean_old_requests(
                self.minute_requests.get(auth_key, []), 60
            )
            if len(self.minute_requests[auth_key]) >= self.auth_limit_per_minute:
                oldest = min(self.minute_requests[auth_key])
                retry_after = int(60 - (current_time - oldest)) + 1
                logger.warning(f"Auth rate limit exceeded for IP: {client_ip}")
                return False, "Çok fazla giriş denemesi. Lütfen bekleyin.", retry_after
            self.minute_requests[auth_key].append(current_time)
        
        # Check burst limit (10 requests per second)
        if client_ip in self.burst_requests:
            last_time, count = self.burst_requests[client_ip]
            if current_time - last_time < 1:  # Within 1 second
                if count >= self.burst_limit:
                    logger.warning(f"Burst limit exceeded for IP: {client_ip}")
                    return False, "Çok hızlı istek gönderiyorsunuz. Lütfen bekleyin.", 1
                self.burst_requests[client_ip] = (last_time, count + 1)
            else:
                self.burst_requests[client_ip] = (current_time, 1)
        else:
            self.burst_requests[client_ip] = (current_time, 1)
        
        # Check minute limit
        self.minute_requests[client_ip] = self._clean_old_requests(
            self.minute_requests[client_ip], 60
        )
        if len(self.minute_requests[client_ip]) >= self.requests_per_minute:
            oldest = min(self.minute_requests[client_ip])
            retry_after = int(60 - (current_time - oldest)) + 1
            logger.warning(f"Minute rate limit exceeded for IP: {client_ip}")
            return False, "Dakikalık istek limitine ulaştınız.", retry_after
        
        # Check hour limit
        self.hour_requests[client_ip] = self._clean_old_requests(
            self.hour_requests[client_ip], 3600
        )
        if len(self.hour_requests[client_ip]) >= self.requests_per_hour:
            oldest = min(self.hour_requests[client_ip])
            retry_after = int(3600 - (current_time - oldest)) + 1
            logger.warning(f"Hourly rate limit exceeded for IP: {client_ip}")
            return False, "Saatlik istek limitine ulaştınız.", retry_after
        
        # Record request
        self.minute_requests[client_ip].append(current_time)
        self.hour_requests[client_ip].append(current_time)
        
        return True, None, None
    
    def get_remaining(self, request: Request) -> Dict[str, int]:
        """Get remaining requests for client"""
        client_ip = self._get_client_ip(request)
        
        minute_used = len(self.minute_requests.get(client_ip, []))
        hour_used = len(self.hour_requests.get(client_ip, []))
        
        return {
            "minute_remaining": max(0, self.requests_per_minute - minute_used),
            "hour_remaining": max(0, self.requests_per_hour - hour_used),
            "minute_limit": self.requests_per_minute,
            "hour_limit": self.requests_per_hour
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI Middleware for rate limiting
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10,
        enabled: bool = True
    ):
        super().__init__(app)
        self.enabled = enabled
        self.rate_limiter = RateLimiter(
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour,
            burst_limit=burst_limit
        )
    
    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiter"""
        
        if not self.enabled:
            return await call_next(request)
        
        # Check rate limit
        is_allowed, error_message, retry_after = self.rate_limiter.is_allowed(request)
        
        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": error_message,
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.rate_limiter.requests_per_minute),
                    "X-RateLimit-Remaining": "0"
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        remaining = self.rate_limiter.get_remaining(request)
        response.headers["X-RateLimit-Limit"] = str(remaining["minute_limit"])
        response.headers["X-RateLimit-Remaining"] = str(remaining["minute_remaining"])
        
        return response


# Route-specific rate limiter decorator
class RouteRateLimiter:
    """
    Rate limiter for specific routes with custom limits
    """
    
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
    
    def __call__(self, request: Request):
        """Check if request is allowed"""
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Clean old requests
        self.requests[client_ip] = [
            r for r in self.requests[client_ip]
            if current_time - r < 60
        ]
        
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Too Many Requests",
                    "message": f"Bu endpoint için dakikada maksimum {self.requests_per_minute} istek yapabilirsiniz."
                }
            )
        
        self.requests[client_ip].append(current_time)
        return True
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


# Pre-configured limiters for different endpoint types
api_limiter = RouteRateLimiter(requests_per_minute=60)  # Normal API endpoints
auth_limiter = RouteRateLimiter(requests_per_minute=10)  # Auth endpoints (login, register)
heavy_limiter = RouteRateLimiter(requests_per_minute=5)   # Heavy operations (backtest, screener)
