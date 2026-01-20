"""
Backtesting Engine
Test trading strategies on historical data
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from app.utils.logger import logger


@dataclass
class Trade:
    """Individual trade record"""
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    shares: int
    trade_type: str  # "LONG" or "SHORT"
    profit: float
    profit_percent: float
    duration_hours: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Backtester:
    """Backtesting engine for trading strategies"""
    
    def __init__(
        self, 
        initial_capital: float = 100000,
        commission: float = 0.001  # 0.1%
    ):
        """
        Initialize backtester
        
        Args:
            initial_capital: Starting capital
            commission: Commission rate per trade
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict[str, Any]] = []
        
        logger.info(f"Backtester initialized (capital: ₺{initial_capital}, commission: {commission*100}%)")
    
    def run_backtest(
        self,
        df: pd.DataFrame,
        signals: pd.DataFrame,
        stop_loss_pct: float = 3.0,
        take_profit_pct: float = 5.0
    ) -> Dict[str, Any]:
        """
        Run backtest on historical data
        
        Args:
            df: DataFrame with OHLC data
            signals: DataFrame with trading signals (columns: signal, strength, entry_price, stop_loss, take_profit)
            stop_loss_pct: Stop loss percentage (if not in signals)
            take_profit_pct: Take profit percentage (if not in signals)
        
        Returns:
            Dictionary with backtest results
        """
        logger.info(f"Running backtest from {df.index[0]} to {df.index[-1]}")
        
        capital = self.initial_capital
        position = None  # Current open position
        trades = []
        equity = []
        
        for i in range(len(df)):
            current_date = df.index[i]
            current = df.iloc[i]
            
            # Record equity
            equity.append({
                "date": str(current_date),
                "equity": capital,
                "drawdown": ((capital - max([e['equity'] for e in equity] + [self.initial_capital])) / 
                            max([e['equity'] for e in equity] + [self.initial_capital]) * 100)
            })
            
            # If we have an open position, check for exit
            if position is not None:
                should_exit = False
                exit_price = current['close']
                exit_reason = ""
                
                if position['type'] == 'LONG':
                    # Check stop loss
                    if current['low'] <= position['stop_loss']:
                        should_exit = True
                        exit_price = position['stop_loss']
                        exit_reason = "Stop Loss"
                    # Check take profit
                    elif current['high'] >= position['take_profit']:
                        should_exit = True
                        exit_price = position['take_profit']
                        exit_reason = "Take Profit"
                
                if should_exit:
                    # Close position
                    profit = (exit_price - position['entry_price']) * position['shares']
                    commission_cost = position['position_value'] * self.commission * 2  # Entry + exit
                    net_profit = profit - commission_cost
                    
                    capital += position['position_value'] + net_profit
                    
                    # Calculate duration
                    entry_dt = pd.to_datetime(position['entry_date'])
                    exit_dt = pd.to_datetime(current_date)
                    duration = (exit_dt - entry_dt).total_seconds() / 3600
                    
                    # Record trade
                    trade = Trade(
                        entry_date=position['entry_date'],
                        exit_date=str(current_date),
                        entry_price=position['entry_price'],
                        exit_price=exit_price,
                        shares=position['shares'],
                        trade_type=position['type'],
                        profit=round(net_profit, 2),
                        profit_percent=round((net_profit / position['position_value']) * 100, 2),
                        duration_hours=round(duration, 2)
                    )
                    trades.append(trade)
                    
                    logger.debug(f"Closed position: {exit_reason}, P&L: ₺{net_profit:.2f}")
                    position = None
            
            # Check for new entry signal
            if position is None and i < len(signals):
                signal = signals.iloc[i]
                
                if signal.get('signal') == 'BUY' and signal.get('strength', 0) >= 60:
                    # Calculate position size (use 95% of capital to keep some reserve)
                    available_capital = capital * 0.95
                    entry_price = signal.get('entry_price', current['close'])
                    stop_loss = signal.get('stop_loss', entry_price * (1 - stop_loss_pct/100))
                    take_profit = signal.get('take_profit', entry_price * (1 + take_profit_pct/100))
                    
                    # Simple position sizing: use all available capital
                    shares = int(available_capital / entry_price)
                    
                    if shares > 0:
                        position_value = shares * entry_price
                        commission_cost = position_value * self.commission
                        
                        capital -= (position_value + commission_cost)
                        
                        position = {
                            'entry_date': str(current_date),
                            'entry_price': entry_price,
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'shares': shares,
                            'position_value': position_value,
                            'type': 'LONG'
                        }
                        
                        logger.debug(f"Opened position: {shares} shares @ ₺{entry_price:.2f}")
        
        # Close any remaining position at last price
        if position is not None:
            exit_price = df.iloc[-1]['close']
            profit = (exit_price - position['entry_price']) * position['shares']
            commission_cost = position['position_value'] * self.commission
            net_profit = profit - commission_cost
            capital += position['position_value'] + net_profit
            
            trade = Trade(
                entry_date=position['entry_date'],
                exit_date=str(df.index[-1]),
                entry_price=position['entry_price'],
                exit_price=exit_price,
                shares=position['shares'],
                trade_type=position['type'],
                profit=round(net_profit, 2),
                profit_percent=round((net_profit / position['position_value']) * 100, 2),
                duration_hours=0
            )
            trades.append(trade)
        
        # Calculate performance metrics
        results = self.calculate_performance_metrics(trades, equity)
        results['equity_curve'] = equity
        results['trades'] = [t.to_dict() for t in trades]
        
        self.trades = trades
        self.equity_curve = equity
        
        logger.info(f"Backtest completed: {len(trades)} trades, {results['summary']['total_return']:.2f}% return")
        
        return results
    
    def calculate_performance_metrics(
        self, 
        trades: List[Trade],
        equity: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate performance metrics from trades
        
        Args:
            trades: List of trades
            equity: Equity curve data
        
        Returns:
            Dictionary with performance metrics
        """
        if not trades:
            return {"error": "No trades to analyze"}
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.profit > 0]
        losing_trades = [t for t in trades if t.profit <= 0]
        
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        
        # P&L metrics
        total_profit = sum(t.profit for t in trades)
        avg_win = np.mean([t.profit for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.profit for t in losing_trades]) if losing_trades else 0
        largest_win = max([t.profit for t in winning_trades]) if winning_trades else 0
        largest_loss = min([t.profit for t in losing_trades]) if losing_trades else 0
        
        # Profit factor
        gross_profit = sum(t.profit for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t.profit for t in losing_trades)) if losing_trades else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Return metrics
        final_capital = equity[-1]['equity'] if equity else self.initial_capital
        total_return = ((final_capital - self.initial_capital) / self.initial_capital) * 100
        
        # Drawdown
        max_drawdown = min([e['drawdown'] for e in equity]) if equity else 0
        
        # Sharpe ratio (simplified - assuming daily returns)
        returns = [trades[i].profit_percent for i in range(len(trades))]
        sharpe_ratio = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if len(returns) > 1 and np.std(returns) > 0 else 0
        
        # Average trade duration
        avg_duration = np.mean([t.duration_hours for t in trades]) if trades else 0
        
        summary = {
            "initial_capital": self.initial_capital,
            "final_capital": round(final_capital, 2),
            "total_return": round(total_return, 2),
            "total_profit": round(total_profit, 2),
            "total_trades": total_trades,
            "winning_trades": win_count,
            "losing_trades": loss_count,
            "win_rate": round(win_rate, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "largest_win": round(largest_win, 2),
            "largest_loss": round(largest_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown, 2),
            "avg_trade_duration_hours": round(avg_duration, 2)
        }
        
        return {"summary": summary}
    
    def analyze_drawdowns(self, equity_curve: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze drawdown periods
        
        Args:
            equity_curve: Equity curve data
        
        Returns:
            List of drawdown periods
        """
        drawdowns = []
        in_drawdown = False
        dd_start = None
        dd_max = 0
        
        for i, point in enumerate(equity_curve):
            if point['drawdown'] < -0.5 and not in_drawdown:
                in_drawdown = True
                dd_start = i
                dd_max = point['drawdown']
            elif in_drawdown:
                if point['drawdown'] < dd_max:
                    dd_max = point['drawdown']
                if point['drawdown'] >= 0:
                    drawdowns.append({
                        "start_date": equity_curve[dd_start]['date'],
                        "end_date": point['date'],
                        "max_drawdown": round(dd_max, 2),
                        "duration_days": i - dd_start
                    })
                    in_drawdown = False
        
        return drawdowns
