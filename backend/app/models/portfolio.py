"""
Portfolio Models
SQLAlchemy models for user portfolios and transactions
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    Text, Enum as SQLEnum, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
import enum


class TransactionType(str, enum.Enum):
    """Transaction types"""
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    SPLIT = "split"


class Portfolio(Base):
    """
    User portfolio model
    Tracks user's stock holdings
    """
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    
    # Portfolio info
    name = Column(String(100), nullable=False, default="Ana Portföy")
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    
    # Holdings summary (cached for performance)
    total_value = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    total_profit_loss = Column(Float, default=0.0)
    total_profit_loss_percent = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    transactions = relationship("PortfolioTransaction", back_populates="portfolio", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Portfolio {self.name} user_id={self.user_id}>"


class PortfolioTransaction(Base):
    """
    Portfolio transaction model
    Records buy/sell transactions
    """
    __tablename__ = "portfolio_transactions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), index=True)
    
    # Transaction details
    ticker = Column(String(20), nullable=False, index=True)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    
    # Additional info
    commission = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction {self.transaction_type} {self.ticker} qty={self.quantity}>"


class Watchlist(Base):
    """
    User watchlist model
    Tracks stocks user is watching
    """
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    
    # Watchlist info
    name = Column(String(100), nullable=False, default="Takip Listem")
    tickers = Column(Text, nullable=True)  # JSON array of tickers
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="watchlists")
    
    def __repr__(self):
        return f"<Watchlist {self.name} user_id={self.user_id}>"
