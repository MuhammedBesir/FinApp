"""
Portfolio Routes
API endpoints for user portfolio management
"""
from typing import List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.models.base import get_db
from app.models.portfolio import Portfolio, PortfolioTransaction, Watchlist, TransactionType
from app.api.routes.auth import get_current_user_required
from app.utils.logger import logger
import json

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


# ============ Helper Functions ============

def safe_get(obj: Any, attr: str, default: Any = None) -> Any:
    """Safely get attribute from SQLAlchemy model"""
    val = getattr(obj, attr, default)
    return val if val is not None else default


def safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert to float"""
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def safe_str(val: Any, default: str = "") -> str:
    """Safely convert to string"""
    if val is None:
        return default
    return str(val)


def safe_datetime_iso(val: Any) -> Optional[str]:
    """Safely convert datetime to ISO string"""
    if val is None:
        return None
    try:
        if hasattr(val, 'isoformat'):
            return val.isoformat()
        return str(val)
    except Exception:
        return None


# ============ Pydantic Schemas ============

class PortfolioCreate(BaseModel):
    """Create portfolio schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_default: bool = False


class PortfolioResponse(BaseModel):
    """Portfolio response schema"""
    id: int
    name: str
    description: Optional[str]
    is_default: bool
    total_value: float
    total_cost: float
    total_profit_loss: float
    total_profit_loss_percent: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class TransactionCreate(BaseModel):
    """Create transaction schema"""
    ticker: str = Field(..., min_length=1, max_length=20)
    transaction_type: str = Field(..., pattern="^(buy|sell|dividend|split)$")
    quantity: float = Field(..., gt=0)
    price: float = Field(..., ge=0)
    commission: float = Field(default=0.0, ge=0)
    notes: Optional[str] = None
    transaction_date: datetime


class TransactionResponse(BaseModel):
    """Transaction response schema"""
    id: int
    ticker: str
    transaction_type: str
    quantity: float
    price: float
    total_amount: float
    commission: float
    notes: Optional[str]
    transaction_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class WatchlistCreate(BaseModel):
    """Create watchlist schema"""
    name: str = Field(..., min_length=1, max_length=100)
    tickers: List[str] = []


class WatchlistResponse(BaseModel):
    """Watchlist response schema"""
    id: int
    name: str
    tickers: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AddTickerRequest(BaseModel):
    """Add ticker to watchlist"""
    ticker: str


# ============ Portfolio Endpoints ============

@router.get("/", response_model=dict)
async def get_portfolios(
    current_user: dict = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Get all portfolios for current user"""
    portfolios = db.query(Portfolio).filter(
        Portfolio.user_id == current_user["id"]
    ).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": p.id,
                "name": safe_str(p.name),
                "description": safe_str(p.description) or None,
                "isDefault": bool(safe_get(p, 'is_default', False)),
                "totalValue": safe_float(p.total_value),
                "totalCost": safe_float(p.total_cost),
                "totalProfitLoss": safe_float(p.total_profit_loss),
                "totalProfitLossPercent": safe_float(p.total_profit_loss_percent),
                "createdAt": safe_datetime_iso(p.created_at)
            }
            for p in portfolios
        ]
    }


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    current_user: dict = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Create a new portfolio"""
    # If setting as default, unset other defaults
    if portfolio_data.is_default:
        db.query(Portfolio).filter(
            Portfolio.user_id == current_user["id"],
            Portfolio.is_default == True
        ).update({"is_default": False})
    
    portfolio = Portfolio(
        user_id=current_user["id"],
        name=portfolio_data.name,
        description=portfolio_data.description,
        is_default=portfolio_data.is_default
    )
    
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    
    return {
        "success": True,
        "message": "Portföy oluşturuldu",
        "data": {
            "id": portfolio.id,
            "name": portfolio.name,
            "description": portfolio.description,
            "isDefault": portfolio.is_default
        }
    }


@router.get("/{portfolio_id}", response_model=dict)
async def get_portfolio(
    portfolio_id: int,
    current_user: dict = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Get portfolio by ID with transactions"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user["id"]
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portföy bulunamadı"
        )
    
    # Get transactions
    transactions = db.query(PortfolioTransaction).filter(
        PortfolioTransaction.portfolio_id == portfolio_id
    ).order_by(PortfolioTransaction.transaction_date.desc()).all()
    
    # Calculate holdings
    holdings = {}
    for t in transactions:
        ticker_str = safe_str(t.ticker)
        if ticker_str not in holdings:
            holdings[ticker_str] = {"quantity": 0, "avgCost": 0, "totalCost": 0}
        
        # Compare transaction type as string value
        tx_type = t.transaction_type.value if hasattr(t.transaction_type, 'value') else str(t.transaction_type)
        
        if tx_type == "buy":
            old_qty = holdings[ticker_str]["quantity"]
            old_cost = holdings[ticker_str]["totalCost"]
            holdings[ticker_str]["quantity"] += safe_float(t.quantity)
            holdings[ticker_str]["totalCost"] = old_cost + safe_float(t.total_amount)
            if holdings[ticker_str]["quantity"] > 0:
                holdings[ticker_str]["avgCost"] = holdings[ticker_str]["totalCost"] / holdings[ticker_str]["quantity"]
        elif tx_type == "sell":
            holdings[ticker_str]["quantity"] -= safe_float(t.quantity)
            if holdings[ticker_str]["quantity"] > 0:
                holdings[ticker_str]["totalCost"] = holdings[ticker_str]["avgCost"] * holdings[ticker_str]["quantity"]
            else:
                holdings[ticker_str]["totalCost"] = 0
                holdings[ticker_str]["avgCost"] = 0
    
    # Filter out zero holdings
    holdings = {k: v for k, v in holdings.items() if v["quantity"] > 0}
    
    return {
        "success": True,
        "data": {
            "portfolio": {
                "id": portfolio.id,
                "name": safe_str(portfolio.name),
                "description": safe_str(portfolio.description) or None,
                "isDefault": bool(safe_get(portfolio, 'is_default', False)),
                "totalValue": safe_float(portfolio.total_value),
                "totalCost": safe_float(portfolio.total_cost),
                "totalProfitLoss": safe_float(portfolio.total_profit_loss),
                "totalProfitLossPercent": safe_float(portfolio.total_profit_loss_percent)
            },
            "holdings": holdings,
            "transactions": [
                {
                    "id": t.id,
                    "ticker": safe_str(t.ticker),
                    "type": t.transaction_type.value if hasattr(t.transaction_type, 'value') else str(t.transaction_type),
                    "quantity": safe_float(t.quantity),
                    "price": safe_float(t.price),
                    "totalAmount": safe_float(t.total_amount),
                    "commission": safe_float(t.commission),
                    "notes": safe_str(t.notes) or None,
                    "date": safe_datetime_iso(t.transaction_date)
                }
                for t in transactions
            ]
        }
    }


@router.delete("/{portfolio_id}", response_model=dict)
async def delete_portfolio(
    portfolio_id: int,
    current_user: dict = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Delete a portfolio"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user["id"]
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portföy bulunamadı"
        )
    
    db.delete(portfolio)
    db.commit()
    
    return {
        "success": True,
        "message": "Portföy silindi"
    }


# ============ Transaction Endpoints ============

@router.post("/{portfolio_id}/transactions", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_transaction(
    portfolio_id: int,
    transaction_data: TransactionCreate,
    current_user: dict = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Add a transaction to portfolio"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user["id"]
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portföy bulunamadı"
        )
    
    total_amount = transaction_data.quantity * transaction_data.price + transaction_data.commission
    
    transaction = PortfolioTransaction(
        portfolio_id=portfolio_id,
        ticker=transaction_data.ticker.upper(),
        transaction_type=TransactionType(transaction_data.transaction_type),
        quantity=transaction_data.quantity,
        price=transaction_data.price,
        total_amount=total_amount,
        commission=transaction_data.commission,
        notes=transaction_data.notes,
        transaction_date=transaction_data.transaction_date
    )
    
    db.add(transaction)
    
    # Update portfolio totals
    if transaction_data.transaction_type == "buy":
        current_cost = safe_float(portfolio.total_cost)
        portfolio.total_cost = current_cost + total_amount  # type: ignore
    
    db.commit()
    db.refresh(transaction)
    
    return {
        "success": True,
        "message": "İşlem eklendi",
        "data": {
            "id": transaction.id,
            "ticker": transaction.ticker,
            "type": transaction.transaction_type.value,
            "quantity": transaction.quantity,
            "price": transaction.price,
            "totalAmount": transaction.total_amount
        }
    }


@router.delete("/{portfolio_id}/transactions/{transaction_id}", response_model=dict)
async def delete_transaction(
    portfolio_id: int,
    transaction_id: int,
    current_user: dict = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Delete a transaction"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user["id"]
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portföy bulunamadı"
        )
    
    transaction = db.query(PortfolioTransaction).filter(
        PortfolioTransaction.id == transaction_id,
        PortfolioTransaction.portfolio_id == portfolio_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İşlem bulunamadı"
        )
    
    db.delete(transaction)
    db.commit()
    
    return {
        "success": True,
        "message": "İşlem silindi"
    }


# ============ Watchlist Endpoints ============

@router.get("/watchlists/all", response_model=dict)
async def get_watchlists(
    current_user: dict = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Get all watchlists for current user"""
    watchlists = db.query(Watchlist).filter(
        Watchlist.user_id == current_user["id"]
    ).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": w.id,
                "name": safe_str(w.name),
                "tickers": json.loads(safe_str(w.tickers, "[]")),
                "createdAt": safe_datetime_iso(w.created_at)
            }
            for w in watchlists
        ]
    }


@router.post("/watchlists", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_watchlist(
    watchlist_data: WatchlistCreate,
    current_user: dict = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Create a new watchlist"""
    watchlist = Watchlist(
        user_id=current_user["id"],
        name=watchlist_data.name,
        tickers=json.dumps(watchlist_data.tickers)
    )
    
    db.add(watchlist)
    db.commit()
    db.refresh(watchlist)
    
    return {
        "success": True,
        "message": "Takip listesi oluşturuldu",
        "data": {
            "id": watchlist.id,
            "name": watchlist.name,
            "tickers": watchlist_data.tickers
        }
    }


@router.post("/watchlists/{watchlist_id}/add", response_model=dict)
async def add_to_watchlist(
    watchlist_id: int,
    request: AddTickerRequest,
    current_user: dict = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Add a ticker to watchlist"""
    watchlist = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == current_user["id"]
    ).first()
    
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Takip listesi bulunamadı"
        )
    
    tickers = json.loads(safe_str(watchlist.tickers, "[]"))
    ticker = request.ticker.upper()
    
    if ticker not in tickers:
        tickers.append(ticker)
        watchlist.tickers = json.dumps(tickers)  # type: ignore
        db.commit()
    
    return {
        "success": True,
        "message": f"{ticker} takip listesine eklendi",
        "data": {"tickers": tickers}
    }


@router.delete("/watchlists/{watchlist_id}/remove/{ticker}", response_model=dict)
async def remove_from_watchlist(
    watchlist_id: int,
    ticker: str,
    current_user: dict = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Remove a ticker from watchlist"""
    watchlist = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == current_user["id"]
    ).first()
    
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Takip listesi bulunamadı"
        )
    
    tickers = json.loads(safe_str(watchlist.tickers, "[]"))
    ticker = ticker.upper()
    
    if ticker in tickers:
        tickers.remove(ticker)
        watchlist.tickers = json.dumps(tickers)  # type: ignore
        db.commit()
    
    return {
        "success": True,
        "message": f"{ticker} takip listesinden çıkarıldı",
        "data": {"tickers": tickers}
    }


@router.delete("/watchlists/{watchlist_id}", response_model=dict)
async def delete_watchlist(
    watchlist_id: int,
    current_user: dict = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Delete a watchlist"""
    watchlist = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == current_user["id"]
    ).first()
    
    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Takip listesi bulunamadı"
        )
    
    db.delete(watchlist)
    db.commit()
    
    return {
        "success": True,
        "message": "Takip listesi silindi"
    }
