"""
Trading Signal Generator - PROFESSIONAL TRADING RULES
Generates buy/sell/hold signals based on technical indicators
Professional risk management and position sizing integrated

HYBRID STRATEGY INTEGRATED:
- V2 Filters (min score 75, technical stop-loss)
- V3 Exit Strategy (partial exit, TP1/TP2)
- Win Rate Booster (optional bonus)
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, time
from app.utils.logger import logger

# Hybrid Strategy Import
try:
    from app.services.hybrid_strategy import HybridSignalGenerator, HybridRiskManagement
    HYBRID_AVAILABLE = True
except ImportError:
    HYBRID_AVAILABLE = False
    logger.warning("Hybrid strategy modülü yüklenemedi")

class SignalType(Enum):
    """Signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class StrategyType(Enum):
    """Trading strategy profiles"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class MarketPhase(Enum):
    """Market trading phases"""
    PRE_MARKET = "pre_market"
    OPENING = "opening"  # First 15 mins - NO TRADING!
    ACTIVE = "active"
    CLOSING = "closing"
    CLOSED = "closed"

@dataclass
class RiskManagement:
    """Professional risk management parameters - OPTIMIZED!"""
    max_position_risk_pct: float = 2.0  # Max 2-3% per trade
    max_daily_loss_pct: float = 5.0  # Max 5-8% daily loss
    min_risk_reward: float = 1.8  # Minimum 1:1.8 R/R (Verified)
    preferred_risk_reward: float = 2.5  # Preferred 1:2.5+ R/R
    max_sector_concentration: float = 40.0
    trailing_stop_activation: float = 4.0
    trailing_stop_pct: float = 4.0
    min_volume_ratio: float = 0.8  # Minimum volume vs average
    min_indicators_aligned: int = 3
    min_score: float = 55.0  # Minimum signal score
    optimal_rsi_range: tuple = (35, 65)  # Optimal RSI range

@dataclass
class TradingSignal:
    """Trading signal data class"""
    signal: SignalType
    strength: float  # 0-100
    confidence: float  # 0-100
    entry_price: float
    stop_loss: float
    take_profit: float
    take_profit_2: float = 0
    risk_reward_ratio: float = 0
    position_size_pct: float = 0
    max_risk_amount: float = 0
    potential_profit: float = 0
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = ""
    validity_hours: int = 24  # Valid for daily timeframe

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "signal": self.signal.value,
            "strength": round(self.strength, 2),
            "confidence": round(self.confidence, 2),
            "entry_price": round(self.entry_price, 2),
            "stop_loss": round(self.stop_loss, 2),
            "take_profit": round(self.take_profit, 2),
            "take_profit_2": round(self.take_profit_2, 2),
            "risk_reward_ratio": round(self.risk_reward_ratio, 2),
            "position_size_pct": round(self.position_size_pct, 2),
            "max_risk_amount": round(self.max_risk_amount, 2),
            "potential_profit": round(self.potential_profit, 2),
            "reasons": self.reasons,
            "warnings": self.warnings,
            "timestamp": self.timestamp,
            "validity_hours": self.validity_hours
        }

class ImprovedFilters:
    """Improved Strategy Filters (From Backtest v3)"""
    
    @staticmethod
    def multi_timeframe_trend_filter(indicators: Dict) -> Tuple[bool, float, List[str]]:
        reasons = []
        score = 0
        trend = indicators.get('trend', {})
        
        ema_9 = trend.get('ema_9', 0)
        ema_21 = trend.get('ema_21', 0)
        ema_50 = trend.get('ema_50', 0)
        
        # Short term
        if ema_9 > ema_21:
            score += 30
            reasons.append("✅ (Trend) Kısa vade Yükseliş (EMA9 > EMA21)")
        else:
            reasons.append("❌ (Trend) Kısa vade Düşüş")
            
        # Medium term
        if ema_21 > ema_50:
            score += 35
            reasons.append("✅ (Trend) Orta vade Yükseliş (EMA21 > EMA50)")
        else:
             reasons.append("⚠️ (Trend) Orta vade Düşüş/Zayıf")

        is_aligned = score >= 30 # At least short term bullish
        return is_aligned, score, reasons

    @staticmethod
    def volume_quality_filter(df: pd.DataFrame, indicators: Dict) -> Tuple[bool, float, List[str]]:
        reasons = []
        score = 0
        
        if len(df) < 20:
             return True, 0, ["⚠️ Yetersiz Hacim Verisi"]

        current_vol = df['volume'].iloc[-1]
        avg_vol = df['volume'].tail(20).mean()
        
        vol_ratio = current_vol / avg_vol if avg_vol > 0 else 0
        
        if vol_ratio >= 1.5:
            score += 35
            reasons.append(f"🔥 (Hacim) Çok Yüksek ({vol_ratio:.1f}x)")
        elif vol_ratio >= 1.0:
            score += 25
            reasons.append(f"✅ (Hacim) Ortalamanın Üzerinde ({vol_ratio:.1f}x)")
        elif vol_ratio >= 0.8:
            score += 15
            reasons.append(f"⚠️ (Hacim) Ortalama ({vol_ratio:.1f}x)")
        else:
            reasons.append(f"❌ (Hacim) Düşük ({vol_ratio:.1f}x)")
            
        return True, score, reasons # Pass regardless, just score

    @staticmethod
    def market_structure_filter(df: pd.DataFrame, indicators: Dict) -> Tuple[bool, float, List[str]]:
        reasons = []
        score = 0
        
        if len(df) < 20:
            return True, 0, []
            
        current_price = df['close'].iloc[-1]
        recent_high = df['high'].tail(20).max()
        
        if recent_high == 0: return True, 0, []

        dist_to_high = ((recent_high - current_price) / current_price) * 100
        
        if dist_to_high >= 3.0:
            score += 30
            reasons.append(f"✅ (Yapı) Dirence Mesafe Uygun (%{dist_to_high:.1f})")
        elif dist_to_high >= 1.5:
             score += 15
             reasons.append(f"⚠️ (Yapı) Dirence Yakın (%{dist_to_high:.1f})")
        else:
             reasons.append(f"❌ (Yapı) Dirençte (%{dist_to_high:.1f})")
             
        return True, score, reasons

class SignalGenerator:
    """
    Generate trading signals based on technical analysis
    PROFESSIONAL TRADING RULES INTEGRATED
    
    Now with HYBRID STRATEGY support:
    - use_hybrid=True: V2 filters + V3 exit + Win Rate Booster
    - use_hybrid=False: Original strategy
    """
    
    def __init__(self, strategy_type: str = "moderate", use_hybrid: bool = True):
        self.strategy_type = StrategyType(strategy_type)
        self.risk_mgmt = RiskManagement()
        self.use_hybrid = use_hybrid and HYBRID_AVAILABLE
        
        # Hybrid strateji aktifse onu kullan
        if self.use_hybrid:
            self.hybrid_generator = HybridSignalGenerator()
            logger.info(f"SignalGenerator initialized with HYBRID strategy (V2+V3)")
        else:
            self.hybrid_generator = None
            logger.info(f"SignalGenerator initialized with {strategy_type} strategy")
        
    def get_market_phase(self, current_time: Optional[datetime] = None) -> MarketPhase:
        if current_time is None:
            current_time = datetime.now()
        
        # Simple implementation for backend check (assuming script manages timing)
        # Detailed phase logic can be kept if needed
        return MarketPhase.ACTIVE 

    def is_tradeable_time(self) -> tuple[bool, str]:
        # For daily picks (updated once a day), we usually consider it tradeable "for tomorrow/next session"
        return True, "✅ Analiz Zamanı"

    def calculate_position_size(
        self, 
        portfolio_value: float,
        entry_price: float,
        stop_loss: float
    ) -> Dict[str, float]:
        risk_pct = self.risk_mgmt.max_position_risk_pct
        risk_amount = portfolio_value * (risk_pct / 100)
        risk_per_share = abs(entry_price - stop_loss)
        
        if risk_per_share <= 0:
            return {"shares": 0, "max_loss": 0, "position_pct": 0}
        
        position_shares = int(risk_amount / risk_per_share)
        position_value = position_shares * entry_price
        position_pct = (position_value / portfolio_value) * 100
        
        return {
            "shares": position_shares,
            "position_value": round(position_value, 2),
            "position_pct": round(position_pct, 2),
            "max_loss": round(risk_amount, 2)
        }

    def generate_signal(self, df: pd.DataFrame, indicators: Dict) -> Dict[str, Any]:
        """
        Generate signal using IMPROVED STRATEGY LOGIC
        
        If use_hybrid=True, uses Hybrid Strategy (V2 + V3 best features)
        """
        # Default empty signal
        empty_signal = {
            "signal": "HOLD",
            "strength": 0,
            "confidence": 0,
            "reasons": [],
            "warnings": [],
            "risk_reward_ratio": 0
        }

        if df.empty or len(df) < 50:
            return empty_signal

        # === HYBRID STRATEGY (Önerilen) ===
        if self.use_hybrid and self.hybrid_generator:
            try:
                hybrid_result = self.hybrid_generator.generate_signal(
                    df, indicators, apply_booster=True
                )
                
                # Hybrid format'ı standart format'a dönüştür
                if hybrid_result.get("signal") == "BUY":
                    # Add position sizing
                    pos_info = self.calculate_position_size(
                        100000,  # Default portfolio
                        hybrid_result.get("entry_price", 0),
                        hybrid_result.get("stop_loss", 0)
                    )
                    hybrid_result["position_size_pct"] = pos_info["position_pct"]
                    hybrid_result["max_risk_amount"] = pos_info["max_loss"]
                    hybrid_result["shares"] = pos_info["shares"]
                    
                    # Add hybrid marker
                    hybrid_result["strategy"] = "HYBRID_V2_V3"
                    hybrid_result["risk_reward_ratio"] = hybrid_result.get("risk_reward_1", 0)
                    hybrid_result["take_profit"] = hybrid_result.get("take_profit_1", 0)
                    hybrid_result["take_profit_2"] = hybrid_result.get("take_profit_2", 0)
                    
                return hybrid_result
            except Exception as e:
                logger.error(f"Hybrid strategy error: {e}, falling back to original")
                # Hata durumunda orijinal stratejiye geri dön

        # === ORIGINAL STRATEGY (Fallback) ===

        # === ORIGINAL STRATEGY (Fallback) ===
        
        # 1. Filters
        mtf_pass, mtf_score, mtf_reasons = ImprovedFilters.multi_timeframe_trend_filter(indicators)
        vol_pass, vol_score, vol_reasons = ImprovedFilters.volume_quality_filter(df, indicators)
        struct_pass, struct_score, struct_reasons = ImprovedFilters.market_structure_filter(df, indicators)
        
        # RSI Check
        rsi = indicators['momentum'].get('rsi', 50)
        rsi_score = 0
        rsi_reasons = []
        if 35 <= rsi <= 65:
            rsi_score = 20
            rsi_reasons.append(f"✅ (RSI) Optimal ({rsi:.1f})")
        elif rsi > 70:
            rsi_reasons.append(f"❌ (RSI) Aşırı Alım ({rsi:.1f})")
        
        # Total Score
        total_score = mtf_score + vol_score + struct_score + rsi_score
        
        # Combine reasons
        all_reasons = mtf_reasons + vol_reasons + struct_reasons + rsi_reasons
        
        # Decision Logic (Min Score 70)
        if total_score >= 70 and mtf_pass:
             signal_type = SignalType.BUY
             confidence = min(total_score, 99)
             strength = min(total_score, 99)
             
             # Calculate Levels
             current_price = df['close'].iloc[-1]
             atr = indicators['volatility'].get('atr', current_price * 0.03)
             
             stop_loss = current_price - (1.5 * atr)
             risk = current_price - stop_loss
             tp1 = current_price + (risk * 2.2)
             tp2 = current_price + (risk * 3.5)
             
             rr_ratio = 2.2 # conservative base
             
             # Calculate position
             pos_info = self.calculate_position_size(100000, current_price, stop_loss)
             
             signal = TradingSignal(
                signal=signal_type,
                strength=strength,
                confidence=confidence,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=tp1,
                take_profit_2=tp2,
                risk_reward_ratio=rr_ratio,
                position_size_pct=pos_info['position_pct'],
                max_risk_amount=pos_info['max_loss'],
                potential_profit=(tp1 - current_price) * pos_info['shares'],
                reasons=all_reasons,
                warnings=[],
                timestamp=datetime.now().isoformat()
             )
             return signal.to_dict()
        
        return empty_signal
