"""
Professional Trading Rules Engine
Profesyonel trading bot kuralları ve risk yönetimi
"""
import pandas as pd
import numpy as np
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from app.utils.logger import logger


class MarketPhase(Enum):
    """Piyasa fazları"""
    PRE_MARKET = "pre_market"
    OPENING = "opening"  # İlk 15 dakika - İşlem yapma
    ACTIVE = "active"  # Normal işlem saatleri
    CLOSING = "closing"  # Son 15 dakika
    CLOSED = "closed"


class RiskLevel(Enum):
    """Risk seviyeleri"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class RiskParameters:
    """Risk parametreleri"""
    max_position_risk_pct: float = 2.0  # Tek işlem max risk %
    max_daily_loss_pct: float = 5.0  # Günlük max kayıp %
    min_risk_reward: float = 2.0  # Minimum risk/ödül oranı
    max_open_positions: int = 3  # Max açık pozisyon
    max_sector_concentration: float = 40.0  # Sektör konsantrasyon limiti %
    trailing_stop_activation: float = 5.0  # Trailing stop aktivasyon %
    

@dataclass
class TradeSignal:
    """İşlem sinyali"""
    ticker: str
    signal_type: str  # "BUY" or "SELL"
    entry_price: float
    stop_loss: float
    target_1: float
    target_2: float
    risk_reward_ratio: float
    position_size_pct: float
    max_risk_amount: float
    potential_profit: float
    confidence: float  # 0-100
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validity_hours: int = 8
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MarketAnalysis:
    """Piyasa analizi"""
    trend: str  # "BULLISH", "BEARISH", "SIDEWAYS"
    strength: float  # 0-100
    volume_status: str  # "LOW", "NORMAL", "HIGH"
    volatility: str  # "LOW", "NORMAL", "HIGH"
    risk_level: RiskLevel = RiskLevel.MEDIUM
    tradeable: bool = True
    warnings: List[str] = field(default_factory=list)


class TradingRulesEngine:
    """
    Profesyonel Trading Kuralları Motoru
    
    Temel Prensipler:
    1. Risk Yönetimi (EN ÖNCELİKLİ)
    2. İşlem Kuralları
    3. Teknik Analiz Yaklaşımı
    4. Pozisyon Yönetimi
    """
    
    def __init__(self, risk_params: Optional[RiskParameters] = None):
        self.risk_params = risk_params or RiskParameters()
        self.daily_pnl = 0.0
        self.daily_trades = []
        self.open_positions = []
        logger.info("TradingRulesEngine initialized with professional rules")
    
    # ==================== MARKET PHASE DETECTION ====================
    
    def get_market_phase(self, current_time: Optional[datetime] = None) -> MarketPhase:
        """
        Piyasa fazını belirle
        
        BIST Saatleri:
        - 10:00 - 10:15: Açılış (İşlem yapma!)
        - 10:15 - 17:45: Aktif
        - 17:45 - 18:00: Kapanış
        """
        if current_time is None:
            current_time = datetime.now()
        
        current = current_time.time()
        
        # Hafta sonu kontrolü
        if current_time.weekday() >= 5:
            return MarketPhase.CLOSED
        
        # BIST saatleri
        market_open = time(10, 0)
        opening_end = time(10, 15)
        closing_start = time(17, 45)
        market_close = time(18, 0)
        
        if current < market_open:
            return MarketPhase.PRE_MARKET
        elif market_open <= current < opening_end:
            return MarketPhase.OPENING  # ⚠️ İşlem yapma!
        elif opening_end <= current < closing_start:
            return MarketPhase.ACTIVE
        elif closing_start <= current < market_close:
            return MarketPhase.CLOSING
        else:
            return MarketPhase.CLOSED
    
    def is_tradeable_time(self) -> Tuple[bool, str]:
        """İşlem yapılabilir zaman mı?"""
        phase = self.get_market_phase()
        
        if phase == MarketPhase.OPENING:
            return False, "⚠️ Piyasa açılışının ilk 15 dakikası - Volatilite yüksek, işlem yapma!"
        elif phase == MarketPhase.CLOSED:
            return False, "❌ Piyasa kapalı"
        elif phase == MarketPhase.PRE_MARKET:
            return False, "⏰ Piyasa henüz açılmadı"
        elif phase == MarketPhase.CLOSING:
            return True, "⚠️ Kapanış saatleri - Dikkatli ol, yeni pozisyon açma"
        else:
            return True, "✅ Aktif işlem saatleri"
    
    # ==================== RISK MANAGEMENT ====================
    
    def calculate_position_size(
        self, 
        portfolio_value: float,
        entry_price: float,
        stop_loss: float,
        max_risk_pct: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Pozisyon boyutu hesapla (Kelly Criterion benzeri)
        
        Formül: Pozisyon = Risk Edilecek Tutar / (Giriş - Stop Loss)
        """
        max_risk_pct = max_risk_pct or self.risk_params.max_position_risk_pct
        
        # Risk tutarı (portföyün %2-3'ü)
        risk_amount = portfolio_value * (max_risk_pct / 100)
        
        # Hisse başına risk
        risk_per_share = abs(entry_price - stop_loss)
        
        if risk_per_share <= 0:
            return {"error": 0.0, "shares": 0.0, "position_value": 0.0, "position_pct": 0.0, "risk_amount": 0.0}
        
        # Pozisyon boyutu (lot)
        position_shares = int(risk_amount / risk_per_share)
        
        # Pozisyon değeri
        position_value = position_shares * entry_price
        position_pct = (position_value / portfolio_value) * 100
        
        return {
            "shares": position_shares,
            "position_value": round(position_value, 2),
            "position_pct": round(position_pct, 2),
            "risk_amount": round(risk_amount, 2),
            "risk_per_share": round(risk_per_share, 2),
            "max_loss": round(position_shares * risk_per_share, 2)
        }
    
    def check_daily_loss_limit(self, portfolio_value: float) -> Tuple[bool, str]:
        """Günlük kayıp limiti kontrolü"""
        max_daily_loss = portfolio_value * (self.risk_params.max_daily_loss_pct / 100)
        
        if self.daily_pnl <= -max_daily_loss:
            return False, f"⛔ GÜNLÜK KAYIP LİMİTİ AŞILDI! (₺{abs(self.daily_pnl):.2f} > ₺{max_daily_loss:.2f}) - Bugün işlem yapma!"
        
        remaining = max_daily_loss + self.daily_pnl
        return True, f"✅ Günlük limit içinde (Kalan risk: ₺{remaining:.2f})"
    
    # ==================== TREND VALIDATION (ZORUNLU) ====================
    
    def check_uptrend(self, indicators: Dict[str, Any], price: float) -> Tuple[bool, str, int, List[str]]:
        """
        Yükseliş trendi kontrolü - ZORUNLU ŞART!
        
        Yükseliş Trendi Kriterleri:
        1. Fiyat > EMA20 (kısa vadeli trend yukarı)
        2. EMA20 > EMA50 (orta vadeli trend yukarı)
        3. ADX > 20 (trend güçlü)
        4. MACD > Signal veya Histogram > 0 (momentum pozitif)
        
        Returns:
            (is_uptrend, message, trend_score, reasons)
        """
        trend_score = 0
        reasons: List[str] = []
        
        ema_9 = indicators.get('ema_9', indicators.get('ema_20', price))
        ema_20 = indicators.get('ema_20', indicators.get('ema_21', price))
        ema_50 = indicators.get('ema_50', price)
        adx = indicators.get('adx', 0)
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        macd_hist = indicators.get('macd_histogram', indicators.get('macd_hist', 0))
        
        # 1. Fiyat > EMA20 (30 puan)
        if price > ema_20:
            trend_score += 30
            reasons.append(f"✅ Fiyat EMA20 üzerinde ({price:.2f} > {ema_20:.2f})")
        else:
            reasons.append(f"❌ Fiyat EMA20 altında ({price:.2f} < {ema_20:.2f})")
        
        # 2. EMA20 > EMA50 (30 puan)
        if ema_20 > ema_50:
            trend_score += 30
            reasons.append(f"✅ EMA20 > EMA50 (orta vadeli yükseliş)")
        else:
            reasons.append(f"❌ EMA20 < EMA50 (orta vadeli düşüş)")
        
        # 3. ADX > 20 (20 puan) - Trend gücü
        if adx > 25:
            trend_score += 20
            reasons.append(f"✅ Güçlü trend (ADX: {adx:.1f} > 25)")
        elif adx > 20:
            trend_score += 10
            reasons.append(f"⚠️ Orta trend gücü (ADX: {adx:.1f})")
        else:
            reasons.append(f"❌ Zayıf trend (ADX: {adx:.1f} < 20)")
        
        # 4. MACD Momentum (20 puan)
        if macd > macd_signal and macd_hist > 0:
            trend_score += 20
            reasons.append("✅ MACD pozitif momentum")
        elif macd_hist > 0:
            trend_score += 10
            reasons.append("⚠️ MACD histogram pozitif")
        else:
            reasons.append("❌ MACD negatif momentum")
        
        # Yükseliş trendi için minimum 60 puan gerekli
        is_uptrend = trend_score >= 60
        
        if is_uptrend:
            message = f"📈 YÜKSELİŞ TRENDİ DOĞRULANDI (Skor: {trend_score}/100)"
        else:
            message = f"⚠️ Yükseliş trendi YOK (Skor: {trend_score}/100) - İşlem yapma!"
        
        return is_uptrend, message, trend_score, reasons
    
    def check_volatility_preference(
        self,
        df: pd.DataFrame,
        indicators: Dict[str, Any],
        price: float
    ) -> Tuple[bool, str, int, List[str]]:
        """
        YÜKSEK VOLATİLİTE TERCİHİ - Günlük Trade için!
        
        Yüksek volatilite = Daha fazla kar fırsatı
        
        Volatilite Kriterleri:
        1. ATR/Fiyat oranı (ATR%) - Günlük hareket potansiyeli
        2. Bollinger Band genişliği - Volatilite göstergesi
        3. Son 20 günlük fiyat aralığı - Historical volatility
        4. Günlük ortalama hareket - Average True Range
        
        Sınıflandırma:
        - DÜŞÜK: ATR% < 1.5% (Tercih edilmez)
        - ORTA: ATR% 1.5-3% (Kabul edilebilir)
        - YÜKSEK: ATR% > 3% (Tercih edilir! ⭐)
        
        Returns:
            (is_high_volatility, message, volatility_score, reasons)
        """
        volatility_score = 0
        reasons = []
        
        # Get ATR and other volatility metrics
        atr = indicators.get('atr', 0)
        bb_upper = indicators.get('bb_upper', 0)
        bb_lower = indicators.get('bb_lower', 0)
        bb_middle = indicators.get('bb_middle', price)
        
        # 1. ATR/Fiyat Oranı (40 puan) - En önemli metrik
        atr_pct = (atr / price) * 100 if price > 0 else 0
        
        if atr_pct >= 4.0:
            volatility_score += 40
            reasons.append(f"🔥 ÇOKK YÜKSEK volatilite (ATR: %{atr_pct:.2f})")
        elif atr_pct >= 3.0:
            volatility_score += 35
            reasons.append(f"⭐ YÜKSEK volatilite (ATR: %{atr_pct:.2f})")
        elif atr_pct >= 2.0:
            volatility_score += 25
            reasons.append(f"✅ ORTA volatilite (ATR: %{atr_pct:.2f})")
        elif atr_pct >= 1.5:
            volatility_score += 15
            reasons.append(f"⚠️ DÜŞÜK volatilite (ATR: %{atr_pct:.2f})")
        else:
            reasons.append(f"❌ ÇOK DÜŞÜK volatilite (ATR: %{atr_pct:.2f})")
        
        # 2. Bollinger Band Genişliği (25 puan)
        if bb_upper > 0 and bb_lower > 0 and bb_middle > 0:
            bb_width_pct = ((bb_upper - bb_lower) / bb_middle) * 100
            
            if bb_width_pct >= 10:
                volatility_score += 25
                reasons.append(f"🔥 Geniş BB bandı (%{bb_width_pct:.1f})")
            elif bb_width_pct >= 6:
                volatility_score += 20
                reasons.append(f"⭐ Normal BB bandı (%{bb_width_pct:.1f})")
            elif bb_width_pct >= 4:
                volatility_score += 10
                reasons.append(f"⚠️ Dar BB bandı (%{bb_width_pct:.1f})")
            else:
                reasons.append(f"❌ Çok dar BB bandı (%{bb_width_pct:.1f})")
        
        # 3. DataFrame'den son 20 günlük fiyat aralığı (20 puan)
        if df is not None and len(df) >= 20:
            high_20 = df['high'].tail(20).max()
            low_20 = df['low'].tail(20).min()
            range_pct = ((high_20 - low_20) / low_20) * 100 if low_20 > 0 else 0
            
            if range_pct >= 20:
                volatility_score += 20
                reasons.append(f"🔥 Geniş 20-gün aralığı (%{range_pct:.1f})")
            elif range_pct >= 12:
                volatility_score += 15
                reasons.append(f"⭐ Normal 20-gün aralığı (%{range_pct:.1f})")
            elif range_pct >= 8:
                volatility_score += 10
                reasons.append(f"⚠️ Dar 20-gün aralığı (%{range_pct:.1f})")
            else:
                reasons.append(f"❌ Çok dar 20-gün aralığı (%{range_pct:.1f})")
        
        # 4. Günlük ortalama hareket (15 puan)
        if df is not None and len(df) >= 10:
            daily_moves = ((df['high'] - df['low']) / df['low']).tail(10) * 100
            avg_daily_move = daily_moves.mean()
            
            if avg_daily_move >= 4:
                volatility_score += 15
                reasons.append(f"🔥 Yüksek günlük hareket (%{avg_daily_move:.2f})")
            elif avg_daily_move >= 2.5:
                volatility_score += 12
                reasons.append(f"⭐ Normal günlük hareket (%{avg_daily_move:.2f})")
            elif avg_daily_move >= 1.5:
                volatility_score += 8
                reasons.append(f"⚠️ Düşük günlük hareket (%{avg_daily_move:.2f})")
            else:
                reasons.append(f"❌ Çok düşük günlük hareket (%{avg_daily_move:.2f})")
        
        # Volatilite sınıflandırması
        is_high_volatility = volatility_score >= 50
        
        if volatility_score >= 80:
            message = f"🔥 MÜKEMMEL VOLATİLİTE (Skor: {volatility_score}/100) - Günlük trade için ideal!"
        elif volatility_score >= 65:
            message = f"⭐ YÜKSEK VOLATİLİTE (Skor: {volatility_score}/100) - Tercih edilen!"
        elif volatility_score >= 50:
            message = f"✅ ORTA VOLATİLİTE (Skor: {volatility_score}/100) - Kabul edilebilir"
        elif volatility_score >= 30:
            message = f"⚠️ DÜŞÜK VOLATİLİTE (Skor: {volatility_score}/100) - Dikkatli ol"
        else:
            message = f"❌ ÇOK DÜŞÜK VOLATİLİTE (Skor: {volatility_score}/100) - Tercih etme!"
        
        return is_high_volatility, message, volatility_score, reasons
    
    def validate_risk_reward(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float
    ) -> Tuple[bool, float, str]:
        """Risk/Ödül oranı kontrolü"""
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if risk <= 0:
            return False, 0, "❌ Geçersiz stop loss"
        
        rr_ratio = reward / risk
        
        if rr_ratio < self.risk_params.min_risk_reward:
            return False, rr_ratio, f"⚠️ Risk/Ödül oranı yetersiz ({rr_ratio:.2f} < {self.risk_params.min_risk_reward})"
        
        return True, rr_ratio, f"✅ Risk/Ödül: 1:{rr_ratio:.2f}"
    
    # ==================== SIGNAL VALIDATION ====================
    
    def validate_buy_signal(
        self,
        ticker: str,
        indicators: Dict[str, Any],
        price: float,
        volume: float,
        avg_volume: float
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Alış sinyali doğrulama
        
        Kriterler:
        - En az 2-3 teknik gösterge uyumlu olmalı
        - Hacim artışı ile desteklenmeli
        - Trend yönünde işlem
        """
        confirmations = []
        warnings = []
        score = 0
        
        # 1. RSI Kontrolü
        rsi = indicators.get('rsi', 50)
        if rsi < 30:
            confirmations.append(f"✅ RSI aşırı satım ({rsi:.1f} < 30)")
            score += 2
        elif 30 <= rsi <= 50:
            confirmations.append(f"✅ RSI alım bölgesinde ({rsi:.1f})")
            score += 1
        elif rsi > 70:
            warnings.append(f"⚠️ RSI aşırı alım ({rsi:.1f} > 70) - Dikkat!")
            score -= 1
        
        # 2. MACD Kontrolü
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        macd_hist = indicators.get('macd_histogram', 0)
        
        if macd > macd_signal and macd_hist > 0:
            confirmations.append("✅ MACD pozitif kesişim")
            score += 2
        elif macd_hist > 0:
            confirmations.append("✅ MACD histogram pozitif")
            score += 1
        else:
            warnings.append("⚠️ MACD negatif")
        
        # 3. Trend Kontrolü (EMA)
        ema_20 = indicators.get('ema_20', price)
        ema_50 = indicators.get('ema_50', price)
        
        if price > ema_20 > ema_50:
            confirmations.append("✅ Güçlü yükseliş trendi (Fiyat > EMA20 > EMA50)")
            score += 2
        elif price > ema_20:
            confirmations.append("✅ Fiyat EMA20 üzerinde")
            score += 1
        else:
            warnings.append("⚠️ Fiyat EMA20 altında - Trend zayıf")
        
        # 4. Hacim Kontrolü
        if avg_volume > 0:
            vol_ratio = volume / avg_volume
            if vol_ratio > 1.5:
                confirmations.append(f"✅ Yüksek hacim ({vol_ratio:.1f}x ortalama)")
                score += 2
            elif vol_ratio > 1.0:
                confirmations.append(f"✅ Hacim ortalamanın üzerinde ({vol_ratio:.1f}x)")
                score += 1
            elif vol_ratio < 0.5:
                warnings.append(f"⚠️ Düşük hacim ({vol_ratio:.1f}x) - Likidite riski!")
                score -= 1
        
        # 5. Bollinger Bands
        bb_lower = indicators.get('bb_lower', price * 0.95)
        bb_upper = indicators.get('bb_upper', price * 1.05)
        
        if price <= bb_lower * 1.01:
            confirmations.append("✅ Fiyat alt Bollinger bandına yakın")
            score += 1
        elif price >= bb_upper * 0.99:
            warnings.append("⚠️ Fiyat üst Bollinger bandında - Aşırı alım")
        
        # 6. Stochastic
        stoch_k = indicators.get('stoch_k', 50)
        if stoch_k < 20:
            confirmations.append(f"✅ Stochastic aşırı satım ({stoch_k:.1f})")
            score += 1
        elif stoch_k > 80:
            warnings.append(f"⚠️ Stochastic aşırı alım ({stoch_k:.1f})")
        
        # Minimum 2-3 onay gerekli
        is_valid = len(confirmations) >= 3 and score >= 4
        
        if not is_valid:
            warnings.append(f"❌ Yetersiz onay sayısı ({len(confirmations)}/3 minimum)")
        
        return is_valid, confirmations, warnings
    
    def validate_sell_signal(
        self,
        ticker: str,
        indicators: Dict[str, Any],
        price: float,
        volume: float,
        avg_volume: float
    ) -> Tuple[bool, List[str], List[str]]:
        """Satış sinyali doğrulama"""
        confirmations = []
        warnings = []
        score = 0
        
        # 1. RSI Kontrolü
        rsi = indicators.get('rsi', 50)
        if rsi > 70:
            confirmations.append(f"✅ RSI aşırı alım ({rsi:.1f} > 70)")
            score += 2
        elif 50 <= rsi <= 70:
            confirmations.append(f"✅ RSI satım bölgesinde ({rsi:.1f})")
            score += 1
        elif rsi < 30:
            warnings.append(f"⚠️ RSI aşırı satım ({rsi:.1f}) - Dipte satış?")
        
        # 2. MACD
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        macd_hist = indicators.get('macd_histogram', 0)
        
        if macd < macd_signal and macd_hist < 0:
            confirmations.append("✅ MACD negatif kesişim")
            score += 2
        elif macd_hist < 0:
            confirmations.append("✅ MACD histogram negatif")
            score += 1
        
        # 3. Trend (EMA)
        ema_20 = indicators.get('ema_20', price)
        ema_50 = indicators.get('ema_50', price)
        
        if price < ema_20 < ema_50:
            confirmations.append("✅ Düşüş trendi (Fiyat < EMA20 < EMA50)")
            score += 2
        elif price < ema_20:
            confirmations.append("✅ Fiyat EMA20 altında")
            score += 1
        
        # 4. Hacim
        if avg_volume > 0:
            vol_ratio = volume / avg_volume
            if vol_ratio > 1.5:
                confirmations.append(f"✅ Satış baskısı ile yüksek hacim ({vol_ratio:.1f}x)")
                score += 1
        
        is_valid = len(confirmations) >= 2 and score >= 3
        
        return is_valid, confirmations, warnings
    
    # ==================== TRADE SIGNAL GENERATION ====================
    
    def generate_trade_signal(
        self,
        ticker: str,
        df: pd.DataFrame,
        indicators: Dict[str, Any],
        portfolio_value: float
    ) -> Optional[TradeSignal]:
        """
        Tam işlem sinyali üret
        """
        if df.empty:
            return None
        
        price = float(df['Close'].iloc[-1])
        volume = float(df['Volume'].iloc[-1])
        avg_volume = float(df['Volume'].rolling(20).mean().iloc[-1]) if len(df) >= 20 else volume
        
        # Zaman kontrolü
        tradeable, time_msg = self.is_tradeable_time()
        warnings = []
        if not tradeable:
            warnings.append(time_msg)
        
        # Alış sinyali kontrolü
        is_buy, buy_confirms, buy_warns = self.validate_buy_signal(
            ticker, indicators, price, volume, avg_volume
        )
        
        if is_buy:
            # ATR bazlı stop loss ve hedef
            atr = indicators.get('atr', price * 0.02)
            
            # Stop Loss: 2 ATR altı
            stop_loss = price - (2 * atr)
            
            # Hedefler: Risk/Ödül 1:2 ve 1:3
            risk = price - stop_loss
            target_1 = price + (risk * 2)  # 1:2
            target_2 = price + (risk * 3)  # 1:3
            
            # Risk/Ödül kontrolü
            rr_valid, rr_ratio, rr_msg = self.validate_risk_reward(price, stop_loss, target_1)
            
            # Pozisyon boyutu
            pos_info = self.calculate_position_size(portfolio_value, price, stop_loss)
            
            return TradeSignal(
                ticker=ticker,
                signal_type="BUY",
                entry_price=round(price, 2),
                stop_loss=round(stop_loss, 2),
                target_1=round(target_1, 2),
                target_2=round(target_2, 2),
                risk_reward_ratio=rr_ratio,
                position_size_pct=pos_info.get('position_pct', 0),
                max_risk_amount=pos_info.get('max_loss', 0),
                potential_profit=round(pos_info.get('shares', 0) * (target_1 - price), 2),
                confidence=min(len(buy_confirms) * 20, 100),
                reasons=buy_confirms,
                warnings=buy_warns + warnings,
                validity_hours=8
            )
        
        return None
    
    # ==================== MARKET ANALYSIS ====================
    
    def analyze_market_conditions(
        self,
        bist100_data: Optional[pd.DataFrame] = None,
        usd_try: Optional[float] = None
    ) -> MarketAnalysis:
        """
        Genel piyasa koşullarını analiz et
        """
        warnings = []
        tradeable = True
        
        # Zaman kontrolü
        time_ok, time_msg = self.is_tradeable_time()
        if not time_ok:
            warnings.append(time_msg)
            tradeable = False
        
        # Günlük kayıp kontrolü
        # (Bu normalde portfolio_value ile çağrılmalı)
        
        trend = "SIDEWAYS"
        strength = 50
        volume_status = "NORMAL"
        volatility = "NORMAL"
        risk_level = RiskLevel.MEDIUM
        
        if bist100_data is not None and not bist100_data.empty:
            close = bist100_data['Close']
            
            # EMA trend analizi
            if len(close) >= 50:
                ema20 = close.ewm(span=20).mean().iloc[-1]
                ema50 = close.ewm(span=50).mean().iloc[-1]
                current = close.iloc[-1]
                
                if current > ema20 > ema50:
                    trend = "BULLISH"
                    strength = 70
                elif current < ema20 < ema50:
                    trend = "BEARISH"
                    strength = 30
                    warnings.append("⚠️ Piyasa düşüş trendinde - Dikkatli ol")
            
            # Volatilite
            if len(close) >= 20:
                returns = close.pct_change().dropna()
                vol = returns.std() * np.sqrt(252) * 100
                
                if vol > 30:
                    volatility = "HIGH"
                    risk_level = RiskLevel.HIGH
                    warnings.append(f"⚠️ Yüksek volatilite (%{vol:.1f})")
                elif vol < 15:
                    volatility = "LOW"
        
        # USD/TRY kontrolü
        if usd_try and usd_try > 35:  # Örnek eşik
            warnings.append(f"⚠️ Dolar/TL yüksek ({usd_try:.2f}) - Piyasa baskı altında olabilir")
        
        return MarketAnalysis(
            trend=trend,
            strength=strength,
            volume_status=volume_status,
            volatility=volatility,
            risk_level=risk_level,
            tradeable=tradeable,
            warnings=warnings
        )
    
    # ==================== REPORT GENERATORS ====================
    
    def generate_trade_report(self, signal: TradeSignal) -> str:
        """İşlem önerisi raporu oluştur"""
        stop_loss_pct = abs((signal.stop_loss - signal.entry_price) / signal.entry_price * 100)
        target1_pct = abs((signal.target_1 - signal.entry_price) / signal.entry_price * 100)
        target2_pct = abs((signal.target_2 - signal.entry_price) / signal.entry_price * 100)
        
        report = f"""🎯 İŞLEM ÖNERİSİ: {signal.ticker.replace('.IS', '')}

📊 DURUM ANALİZİ:
"""
        for reason in signal.reasons:
            report += f"• {reason}\n"
        
        report += f"""
💰 İŞLEM DETAYI:
• Yön: {'📈 AL' if signal.signal_type == 'BUY' else '📉 SAT'}
• Giriş: ₺{signal.entry_price:.2f}
• Stop Loss: ₺{signal.stop_loss:.2f} (%{stop_loss_pct:.1f})
• Hedef 1: ₺{signal.target_1:.2f} (%{target1_pct:.1f})
• Hedef 2: ₺{signal.target_2:.2f} (%{target2_pct:.1f})
• Risk/Ödül: 1:{signal.risk_reward_ratio:.1f}

⚠️ RİSK YÖNETİMİ:
• Önerilen pozisyon: Portföyün %{signal.position_size_pct:.1f}'i
• Maksimum risk: ₺{signal.max_risk_amount:.2f}
• Potansiyel kazanç: ₺{signal.potential_profit:.2f}
• Güven skoru: {signal.confidence:.0f}/100
"""
        
        if signal.warnings:
            report += "\n⚠️ UYARILAR:\n"
            for warning in signal.warnings:
                report += f"• {warning}\n"
        
        report += f"\n⏰ GEÇERLİLİK: {signal.validity_hours} saat"
        
        return report
    
    def generate_daily_report(
        self,
        market_analysis: MarketAnalysis,
        top_picks: List[TradeSignal],
        date: Optional[datetime] = None
    ) -> str:
        """Günlük piyasa raporu oluştur"""
        if date is None:
            date = datetime.now()
        
        report = f"""📅 GÜNLÜK PİYASA RAPORU - {date.strftime('%d.%m.%Y')}

📊 BIST DURUM:
• Genel trend: {market_analysis.trend} (Güç: {market_analysis.strength}/100)
• Volatilite: {market_analysis.volatility}
• Risk seviyesi: {market_analysis.risk_level.value.upper()}
• İşlem yapılabilir: {'✅ Evet' if market_analysis.tradeable else '❌ Hayır'}
"""
        
        if market_analysis.warnings:
            report += "\n⚠️ BUGÜN DİKKAT:\n"
            for warning in market_analysis.warnings:
                report += f"• {warning}\n"
        
        if top_picks:
            report += "\n🔥 GÜNÜN EN İYİ FIRSATLARİ:\n"
            for i, pick in enumerate(top_picks[:5], 1):
                report += f"{i}. {pick.ticker.replace('.IS', '')} - "
                report += f"₺{pick.entry_price:.2f} | "
                report += f"Hedef: ₺{pick.target_1:.2f} | "
                report += f"R/R: 1:{pick.risk_reward_ratio:.1f}\n"
        
        report += f"""
💡 GÜNÜN STRATEJİSİ:
"""
        if market_analysis.trend == "BULLISH":
            report += "• Trend yönünde (AL) pozisyonları değerlendir\n"
            report += "• Pullback'lerde (geri çekilmelerde) alım fırsatı ara\n"
        elif market_analysis.trend == "BEARISH":
            report += "• Dikkatli ol, yeni pozisyon açma\n"
            report += "• Mevcut pozisyonları korumaya al\n"
        else:
            report += "• Yatay piyasada destek/direnç seviyelerini izle\n"
            report += "• Kırılım bekle, sabırlı ol\n"
        
        report += "• Stop-loss seviyelerini asla ihmal etme!\n"
        report += "• Portföyün %2-3'ünden fazlasını riske atma!\n"
        
        return report


# Singleton instance
_trading_rules_engine: Optional[TradingRulesEngine] = None

def get_trading_rules_engine() -> TradingRulesEngine:
    """Trading rules engine singleton"""
    global _trading_rules_engine
    if _trading_rules_engine is None:
        _trading_rules_engine = TradingRulesEngine()
    return _trading_rules_engine
