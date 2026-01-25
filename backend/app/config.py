"""
Configuration management using pydantic-settings
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database - Neon PostgreSQL for production, SQLite for development
    # On Vercel (Lambda), use /tmp for SQLite if not using Postgres
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:////tmp/trading_bot.db" if os.getenv("VERCEL") else "sqlite:///./trading_bot.db"
    )
    
    # Neon PostgreSQL specific settings
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_timeout: int = 30
    database_pool_recycle: int = 1800
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_enabled: bool = False
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:3000,https://fin-app-bay.vercel.app"
    
    # Trading
    default_ticker: str = "TRALT.IS"
    default_interval: str = "5m"
    default_period: str = "1d"
    
    # Risk Management
    max_risk_per_trade: float = 2.0
    max_daily_loss: float = 5.0
    max_positions: int = 5
    
    # Caching
    cache_ttl_realtime: int = 60
    cache_ttl_historical: int = 3600
    
    # Notifications
    email_enabled: bool = False
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    
    # Logging
    log_level: str = "INFO"
    
    # AI/LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    
    # Rate Limiting - Relaxed for serverless
    rate_limit_enabled: bool = not os.getenv("VERCEL", False)  # Disable on Vercel
    rate_limit_per_minute: int = 120
    rate_limit_per_hour: int = 3000
    rate_limit_burst: int = 30
    
    # Security - Must change in production
    secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    jwt_refresh_days: int = 30
    
    # Password hashing
    bcrypt_rounds: int = 12
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.log_level.upper() == "WARNING" or "neon" in self.database_url.lower()
    
    @property
    def database_is_postgres(self) -> bool:
        """Check if using PostgreSQL database"""
        return self.database_url.startswith("postgresql")


# Global settings instance
settings = Settings()
