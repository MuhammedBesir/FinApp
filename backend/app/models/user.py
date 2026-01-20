"""
User Model
SQLAlchemy model for user authentication and profile
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, 
    Text, Enum as SQLEnum, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
import enum


class MembershipType(str, enum.Enum):
    """User membership types"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    PREMIUM = "premium"


class User(Base):
    """
    User model for authentication
    Stores user credentials and basic info
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    
    # Membership
    membership = Column(
        SQLEnum(MembershipType), 
        default=MembershipType.FREE,
        nullable=False
    )
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email}>"


class UserProfile(Base):
    """
    Extended user profile information
    Stores preferences and settings
    """
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    
    # Profile info
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(20), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Trading preferences
    default_ticker = Column(String(20), default="THYAO.IS")
    default_interval = Column(String(10), default="5m")
    risk_tolerance = Column(String(20), default="moderate")  # conservative, moderate, aggressive
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    
    # Alert preferences
    price_alert_enabled = Column(Boolean, default=True)
    signal_alert_enabled = Column(Boolean, default=True)
    news_alert_enabled = Column(Boolean, default=False)
    
    # UI preferences
    theme = Column(String(20), default="dark")
    language = Column(String(10), default="tr")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<UserProfile user_id={self.user_id}>"
