"""
Risk Management Module
Handles position sizing, stop loss, take profit, and risk validation
"""
from typing import Dict, Any, Optional
from app.utils.logger import logger


class RiskManager:
    """Risk management for trading operations"""
    
    def __init__(
        self, 
        max_risk_per_trade: float = 2.0,
        max_daily_loss: float = 5.0,
        max_positions: int = 5
    ):
        """
        Initialize risk manager
        
        Args:
            max_risk_per_trade: Maximum risk per trade as percentage of capital
            max_daily_loss: Maximum daily loss as percentage of capital
            max_positions: Maximum number of concurrent positions
        """
        self.max_risk_per_trade = max_risk_per_trade
        self.max_daily_loss = max_daily_loss
        self.max_positions = max_positions
        logger.info(f"RiskManager initialized (risk/trade: {max_risk_per_trade}%, daily loss: {max_daily_loss}%)")
    
    def calculate_position_size(
        self, 
        capital: float, 
        entry_price: float,
        stop_loss: float,
        risk_percent: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate position size based on risk parameters
        
        Formula: Position Size = (Capital * Risk%) / (Entry Price - Stop Loss)
        
        Args:
            capital: Total available capital
            entry_price: Planned entry price
            stop_loss: Stop loss price
            risk_percent: Risk percentage (uses max_risk_per_trade if None)
        
        Returns:
            Dictionary with position size details
        """
        if risk_percent is None:
            risk_percent = self.max_risk_per_trade
        
        # Calculate risk amount in currency
        risk_amount = capital * (risk_percent / 100)
        
        # Calculate price risk per share
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            logger.warning("Stop loss equals entry price, cannot calculate position size")
            return {
                "shares": 0,
                "position_value": 0,
                "risk_amount": risk_amount,
                "error": "Invalid stop loss"
            }
        
        # Calculate number of shares
        shares = int(risk_amount / price_risk)
        
        # Calculate position value
        position_value = shares * entry_price
        
        # Calculate position percentage of capital
        position_percent = (position_value / capital) * 100
        
        logger.info(f"Position size: {shares} shares (₺{position_value:.2f}, {position_percent:.1f}% of capital)")
        
        return {
            "shares": shares,
            "position_value": round(position_value, 2),
            "position_percent": round(position_percent, 2),
            "risk_amount": round(risk_amount, 2),
            "risk_per_share": round(price_risk, 2),
            "capital": capital
        }
    
    def calculate_stop_loss(
        self, 
        entry_price: float, 
        atr: float, 
        risk_multiplier: float = 2.0,
        is_long: bool = True
    ) -> float:
        """
        Calculate stop loss based on ATR
        
        Args:
            entry_price: Entry price
            atr: Average True Range value
            risk_multiplier: ATR multiplier for stop distance
            is_long: True for long position, False for short
        
        Returns:
            Stop loss price
        """
        stop_distance = atr * risk_multiplier
        
        if is_long:
            stop_loss = entry_price - stop_distance
        else:
            stop_loss = entry_price + stop_distance
        
        logger.debug(f"Stop loss calculated: ₺{stop_loss:.2f} (distance: ₺{stop_distance:.2f})")
        
        return round(stop_loss, 2)
    
    def calculate_take_profit(
        self, 
        entry_price: float, 
        stop_loss: float, 
        risk_reward: float = 2.0,
        is_long: bool = True
    ) -> float:
        """
        Calculate take profit based on risk/reward ratio
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_reward: Risk/reward ratio
            is_long: True for long position, False for short
        
        Returns:
            Take profit price
        """
        risk = abs(entry_price - stop_loss)
        reward = risk * risk_reward
        
        if is_long:
            take_profit = entry_price + reward
        else:
            take_profit = entry_price - reward
        
        logger.debug(f"Take profit calculated: ₺{take_profit:.2f} (R:R = 1:{risk_reward})")
        
        return round(take_profit, 2)
    
    def validate_trade(
        self, 
        position_value: float,
        capital: float,
        current_positions: int = 0,
        daily_pnl_percent: float = 0.0
    ) -> Dict[str, Any]:
        """
        Validate if trade meets risk requirements
        
        Args:
            position_value: Value of proposed position
            capital: Total capital
            current_positions: Number of current open positions
            daily_pnl_percent: Current daily P&L as percentage
        
        Returns:
            Dictionary with validation results
        """
        warnings = []
        can_trade = True
        
        # Check position limit
        if current_positions >= self.max_positions:
            can_trade = False
            warnings.append(f"Maximum positions limit reached ({self.max_positions})")
        
        # Check daily loss limit
        if daily_pnl_percent <= -self.max_daily_loss:
            can_trade = False
            warnings.append(f"Daily loss limit exceeded ({self.max_daily_loss}%)")
        
        # Check position size relative to capital
        position_percent = (position_value / capital) * 100
        if position_percent > 20:  # Max 20% in single position
            can_trade = False
            warnings.append(f"Position too large ({position_percent:.1f}% of capital)")
        
        # Calculate remaining daily loss capacity
        remaining_loss_capacity = self.max_daily_loss + daily_pnl_percent
        
        # Determine warning level
        if remaining_loss_capacity < 1:
            warning_level = "critical"
        elif remaining_loss_capacity < 2:
            warning_level = "high"
        elif remaining_loss_capacity < 3:
            warning_level = "medium"
        else:
            warning_level = "low"
        
        result = {
            "can_trade": can_trade,
            "warnings": warnings,
            "current_positions": current_positions,
            "max_positions": self.max_positions,
            "daily_pnl_percent": round(daily_pnl_percent, 2),
            "remaining_loss_capacity": round(remaining_loss_capacity, 2),
            "warning_level": warning_level
        }
        
        if can_trade:
            logger.info("Trade validation passed")
        else:
            logger.warning(f"Trade validation failed: {', '.join(warnings)}")
        
        return result
    
    def check_daily_limits(
        self, 
        daily_pnl_percent: float
    ) -> Dict[str, Any]:
        """
        Check daily trading limits
        
        Args:
            daily_pnl_percent: Current daily P&L as percentage
        
        Returns:
            Dictionary with limit status
        """
        remaining = self.max_daily_loss + daily_pnl_percent
        
        if remaining <= 0:
            can_trade = False
            status = "STOP TRADING - Daily loss limit reached"
        elif remaining < 1:
            can_trade = True
            status = "CRITICAL - Approaching daily loss limit"
        elif remaining < 2:
            can_trade = True
            status = "WARNING - Significant daily loss"
        else:
            can_trade = True
            status = "OK - Within safe limits"
        
        logger.info(f"Daily limit check: {status}")
        
        return {
            "can_trade": can_trade,
            "status": status,
            "daily_pnl_percent": round(daily_pnl_percent, 2),
            "max_daily_loss": self.max_daily_loss,
            "remaining_loss_capacity": round(remaining, 2)
        }
    
    def calculate_risk_metrics(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        shares: int
    ) -> Dict[str, Any]:
        """
        Calculate risk metrics for a trade
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            shares: Number of shares
        
        Returns:
            Dictionary with risk metrics
        """
        # Calculate amounts
        position_value = entry_price * shares
        risk_amount = abs(entry_price - stop_loss) * shares
        reward_amount = abs(take_profit - entry_price) * shares
        
        # Calculate percentages
        risk_percent = (risk_amount / position_value) * 100 if position_value > 0 else 0
        reward_percent = (reward_amount / position_value) * 100 if position_value > 0 else 0
        
        # Calculate risk/reward ratio
        risk_reward = reward_amount / risk_amount if risk_amount > 0 else 0
        
        return {
            "position_value": round(position_value, 2),
            "risk_amount": round(risk_amount, 2),
            "reward_amount": round(reward_amount, 2),
            "risk_percent": round(risk_percent, 2),
            "reward_percent": round(reward_percent, 2),
            "risk_reward_ratio": round(risk_reward, 2)
        }
