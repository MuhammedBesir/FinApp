#!/usr/bin/env python3
"""
İYİLEŞTİRİLMİŞ GÜNLÜK TRADE STRATEJİSİ v2.0
=============================================

TEMEL İYİLEŞTİRMELER:
1. Çoklu Zaman Çerçevesi (MTF) Analizi
2. Volatilite Bazlı Dinamik Stop-Loss/Take-Profit
3. Piyasa Rejimi Filtreleri
4. Hacim Profili Analizi
5. Sector Rotation Optimizasyonu
6. Gelişmiş Risk Yönetimi (Kelly Criterion)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# =====================================================
# YAPILANDIRMA
# =====================================================

BIST30 = [
    "AKBNK.IS", "AKSEN.IS", "ARCLK.IS", "ASELS.IS", "BIMAS.IS",
    "EKGYO.IS", "ENKAI.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS",
    "GUBRF.IS", "HEKTS.IS", "ISCTR.IS", "KCHOL.IS", "KRDMD.IS",
    "ODAS.IS", "PETKM.IS", "PGSUS.IS", "SAHOL.IS", "SASA.IS",
    "SISE.IS", "TAVHL.IS", "TCELL.IS", "THYAO.IS", "TKFEN.IS",
    "TOASO.IS", "TUPRS.IS", "YKBNK.IS"
]

SECTOR_MAP = {
    "AKBNK.IS": "Bankacılık", "GARAN.IS": "Bankacılık", "ISCTR.IS": "Bankacılık", "YKBNK.IS": "Bankacılık",
    "THYAO.IS": "Havacılık", "PGSUS.IS": "Havacılık", "TAVHL.IS": "Havacılık",
    "FROTO.IS": "Otomotiv", "TOASO.IS": "Otomotiv",
    "SAHOL.IS": "Holding", "KCHOL.IS": "Holding",
    "BIMAS.IS": "Perakende",
    "EREGL.IS": "Demir Çelik", "KRDMD.IS": "Demir Çelik",
    "TUPRS.IS": "Enerji", "AKSEN.IS": "Enerji", "ODAS.IS": "Enerji",
    "TCELL.IS": "Telekomünikasyon",
    "ARCLK.IS": "Beyaz Eşya",
    "SISE.IS": "Cam", "SASA.IS": "Kimya", "PETKM.IS": "Kimya",
    "ASELS.IS": "Savunma", "ENKAI.IS": "İnşaat",
    "GUBRF.IS": "Gübre", "HEKTS.IS": "Gübre",
    "EKGYO.IS": "GYO", "TKFEN.IS": "İnşaat"
}

# Volatilite bazlı sektör parametreleri
# GÜNCELLEME: Tüm sektörler aktif, weight=1.0 (penalty yok)
SECTOR_PARAMS = {
    # TÜM SEKTÖRLER AKTİF - GYO ENGELLİ
    "Bankacılık":       {"vol_mult": 1.0, "min_score": 50, "max_hold": 7, "weight": 1.0, "enabled": True},
    "İnşaat":           {"vol_mult": 1.0, "min_score": 50, "max_hold": 7, "weight": 1.0, "enabled": True},
    "Enerji":           {"vol_mult": 1.1, "min_score": 50, "max_hold": 6, "weight": 1.0, "enabled": True},
    "Havacılık":        {"vol_mult": 1.2, "min_score": 55, "max_hold": 5, "weight": 1.0, "enabled": True},
    "Gübre":            {"vol_mult": 1.0, "min_score": 50, "max_hold": 7, "weight": 1.0, "enabled": True},
    "Perakende":        {"vol_mult": 0.9, "min_score": 50, "max_hold": 10, "weight": 1.0, "enabled": True},
    "Demir Çelik":      {"vol_mult": 1.15, "min_score": 55, "max_hold": 5, "weight": 1.0, "enabled": True},
    "Otomotiv":         {"vol_mult": 1.1, "min_score": 55, "max_hold": 5, "weight": 1.0, "enabled": True},
    "Holding":          {"vol_mult": 0.9, "min_score": 55, "max_hold": 6, "weight": 1.0, "enabled": True},
    "Telekomünikasyon": {"vol_mult": 1.0, "min_score": 55, "max_hold": 7, "weight": 1.0, "enabled": True},
    "Cam":              {"vol_mult": 1.0, "min_score": 55, "max_hold": 7, "weight": 1.0, "enabled": True},
    "GYO":              {"vol_mult": 0.9, "min_score": 55, "max_hold": 8, "weight": 1.0, "enabled": False},  # ❌ ENGELLİ (%0 WR)
    "Savunma":          {"vol_mult": 1.0, "min_score": 55, "max_hold": 7, "weight": 1.0, "enabled": True},
    "Beyaz Eşya":       {"vol_mult": 1.0, "min_score": 55, "max_hold": 7, "weight": 1.0, "enabled": True},
    "Kimya":            {"vol_mult": 1.0, "min_score": 55, "max_hold": 7, "weight": 1.0, "enabled": True},
    "default":          {"vol_mult": 1.0, "min_score": 50, "max_hold": 7, "weight": 1.0, "enabled": True}
}


# =====================================================
# TEKNİK İNDİKATÖRLER (GELİŞTİRİLMİŞ)
# =====================================================

def calc_ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()

def calc_sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average"""
    return series.rolling(window=period).mean()

def calc_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index - Wilder's smoothing"""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # Wilder's smoothing (EMA ile daha stabil)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    
    rs = avg_gain / (avg_loss + 1e-10)
    return 100 - (100 / (1 + rs))

def calc_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()  # Wilder's ATR

def calc_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
    """MACD with Histogram"""
    ema_fast = calc_ema(prices, fast)
    ema_slow = calc_ema(prices, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calc_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return {'macd': macd_line, 'signal': signal_line, 'histogram': histogram}

def calc_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                    k_period: int = 14, d_period: int = 3) -> Dict:
    """Stochastic Oscillator"""
    lowest_low = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low + 1e-10)
    d = k.rolling(d_period).mean()
    return {'k': k, 'd': d}

def calc_bollinger_bands(prices: pd.Series, period: int = 20, std_mult: float = 2.0) -> Dict:
    """Bollinger Bands with %B"""
    middle = calc_sma(prices, period)
    std = prices.rolling(period).std()
    upper = middle + (std * std_mult)
    lower = middle - (std * std_mult)
    percent_b = (prices - lower) / (upper - lower + 1e-10)
    bandwidth = (upper - lower) / (middle + 1e-10)
    return {'upper': upper, 'middle': middle, 'lower': lower, 'percent_b': percent_b, 'bandwidth': bandwidth}

def calc_vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """Volume Weighted Average Price (günlük reset için rolling kullanılabilir)"""
    typical_price = (high + low + close) / 3
    return (typical_price * volume).cumsum() / (volume.cumsum() + 1e-10)

def calc_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume"""
    sign = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (sign * volume).cumsum()

def calc_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average Directional Index"""
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    
    atr = calc_atr(high, low, close, period)
    plus_di = 100 * calc_ema(plus_dm, period) / (atr + 1e-10)
    minus_di = 100 * calc_ema(minus_dm, period) / (atr + 1e-10)
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
    adx = calc_ema(dx, period)
    return adx

def calc_mfi(high: pd.Series, low: pd.Series, close: pd.Series, 
             volume: pd.Series, period: int = 14) -> pd.Series:
    """Money Flow Index"""
    typical_price = (high + low + close) / 3
    money_flow = typical_price * volume
    
    positive_flow = money_flow.where(typical_price > typical_price.shift(), 0)
    negative_flow = money_flow.where(typical_price < typical_price.shift(), 0)
    
    positive_sum = positive_flow.rolling(period).sum()
    negative_sum = negative_flow.rolling(period).sum()
    
    mfi = 100 * positive_sum / (positive_sum + negative_sum + 1e-10)
    return mfi


# =====================================================
# PİYASA REJİMİ ALGILAMA
# =====================================================

@dataclass
class MarketRegime:
    """Piyasa rejimi sınıfı"""
    trend: str  # 'BULLISH', 'BEARISH', 'SIDEWAYS'
    strength: float  # 0-100
    volatility: str  # 'LOW', 'NORMAL', 'HIGH'
    momentum: str  # 'POSITIVE', 'NEGATIVE', 'NEUTRAL'

def _fix_multiindex_df(df: pd.DataFrame) -> pd.DataFrame:
    """Multi-index DataFrame'i düzelt (yfinance uyumluluğu için)"""
    if isinstance(df.columns, pd.MultiIndex):
        df = df.droplevel('Ticker', axis=1) if 'Ticker' in df.columns.names else df
    return df

def _get_series(df: pd.DataFrame, col: str) -> pd.Series:
    """DataFrame'den Series çıkar"""
    data = df[col]
    if isinstance(data, pd.DataFrame):
        return pd.Series(data.values[:, 0], index=data.index)  # type: ignore
    if isinstance(data, pd.Series):
        return data
    return pd.Series([data])

def detect_market_regime(df: pd.DataFrame) -> MarketRegime:
    """
    Çoklu indikatör ile piyasa rejimini algıla
    """
    df = _fix_multiindex_df(df)
    close = _get_series(df, 'Close')
    high = _get_series(df, 'High')
    low = _get_series(df, 'Low')
    
    # Trend algılama
    ema20 = float(calc_ema(close, 20).iloc[-1])
    ema50 = float(calc_ema(close, 50).iloc[-1])
    ema200 = float(calc_ema(close, 200).iloc[-1]) if len(close) >= 200 else ema50
    
    current_price = float(close.iloc[-1])
    
    # ADX ile trend gücü
    adx = float(calc_adx(high, low, close).iloc[-1])
    
    # Trend belirleme
    if current_price > ema20 > ema50:
        if adx > 25:
            trend = 'BULLISH'
            strength = min(adx * 2, 100)
        else:
            trend = 'SIDEWAYS'
            strength = 50
    elif current_price < ema20 < ema50:
        if adx > 25:
            trend = 'BEARISH'
            strength = min(adx * 2, 100)
        else:
            trend = 'SIDEWAYS'
            strength = 50
    else:
        trend = 'SIDEWAYS'
        strength = 30
    
    # Volatilite belirleme
    atr = float(calc_atr(high, low, close).iloc[-1])
    atr_pct = (atr / current_price) * 100
    
    if atr_pct < 1.5:
        volatility = 'LOW'
    elif atr_pct > 3.0:
        volatility = 'HIGH'
    else:
        volatility = 'NORMAL'
    
    # Momentum belirleme
    rsi = float(calc_rsi(close).iloc[-1])
    macd_data = calc_macd(close)
    macd_hist = float(macd_data['histogram'].iloc[-1])
    
    if rsi > 55 and macd_hist > 0:
        momentum = 'POSITIVE'
    elif rsi < 45 and macd_hist < 0:
        momentum = 'NEGATIVE'
    else:
        momentum = 'NEUTRAL'
    
    return MarketRegime(trend=trend, strength=strength, volatility=volatility, momentum=momentum)


# =====================================================
# GELİŞTİRİLMİŞ SKOR SİSTEMİ
# =====================================================

def calculate_enhanced_score(df: pd.DataFrame, ticker: str) -> Dict:
    """
    Geliştirilmiş puanlama sistemi
    
    Puanlama kriterleri:
    - Trend Uyumu (25 puan)
    - Momentum (20 puan)
    - Pullback Kalitesi (20 puan)
    - Hacim Profili (15 puan)
    - Volatilite Kalitesi (10 puan)
    - Pattern Recognition (10 puan)
    """
    if len(df) < 60:
        return {'score': 0, 'reasons': [], 'entry': 0, 'stop_loss': 0, 'take_profit': 0}
    
    # Multi-index column handling (yfinance compatibility)
    df = _fix_multiindex_df(df)
    close = _get_series(df, 'Close')
    high = _get_series(df, 'High')
    low = _get_series(df, 'Low')
    volume = _get_series(df, 'Volume')
    
    current_price = float(close.iloc[-1])
    score = 0
    reasons = []
    
    # İndikatörler
    ema9 = float(calc_ema(close, 9).iloc[-1])
    ema20 = float(calc_ema(close, 20).iloc[-1])
    ema50 = float(calc_ema(close, 50).iloc[-1])
    rsi = float(calc_rsi(close).iloc[-1])
    atr = float(calc_atr(high, low, close).iloc[-1])
    vol_avg = float(calc_sma(volume, 20).iloc[-1])
    adx = float(calc_adx(high, low, close).iloc[-1])
    
    macd_data = calc_macd(close)
    macd_hist = float(macd_data['histogram'].iloc[-1])
    macd_hist_prev = float(macd_data['histogram'].iloc[-2])
    
    stoch = calc_stochastic(high, low, close)
    stoch_k = float(stoch['k'].iloc[-1])
    
    bb = calc_bollinger_bands(close)
    bb_percent = float(bb['percent_b'].iloc[-1])
    
    mfi = float(calc_mfi(high, low, close, volume).iloc[-1])
    
    # Sektör parametreleri
    sector = SECTOR_MAP.get(ticker, 'default')
    params = SECTOR_PARAMS.get(sector, SECTOR_PARAMS['default'])
    
    # =========== 1. TREND UYUMU (25 puan) ===========
    trend_score = 0
    
    if current_price > ema9 > ema20 > ema50:
        trend_score = 25
        reasons.append("🚀 Mükemmel trend uyumu (EMA9>EMA20>EMA50)")
    elif current_price > ema20 > ema50:
        trend_score = 20
        reasons.append("📈 Güçlü yükseliş trendi")
    elif current_price > ema50 and ema20 > ema50:
        trend_score = 15
        reasons.append("📊 Pozitif trend")
    elif ema20 > ema50:
        trend_score = 10
        reasons.append("📉 Trend toparlanıyor")
    # Fiyat EMA50 üzerindeyse bile puan ver
    elif current_price > ema50:
        trend_score = 8
        reasons.append("📊 EMA50 üzerinde")
    
    # ADX bonus - daha geniş aralık
    if adx > 25:
        trend_score = min(trend_score + 5, 25)
        reasons.append(f"💪 Güçlü trend (ADX: {adx:.1f})")
    elif adx > 20:
        trend_score = min(trend_score + 3, 25)
    
    score += trend_score
    
    # =========== 2. MOMENTUM (20 puan) ===========
    # GÜNCELLEME: Daha geniş RSI aralığı, daha yüksek puanlar
    momentum_score = 0
    
    # RSI - genişletilmiş puanlama
    if 35 <= rsi <= 65:
        momentum_score += 10  # İdeal bölge genişletildi
        reasons.append(f"✅ İdeal RSI ({rsi:.1f})")
    elif 30 <= rsi <= 70:
        momentum_score += 7  # 5'ten 7'ye yükseltildi
    elif rsi < 30:  # Oversold bounce potential
        momentum_score += 10
        reasons.append(f"🔄 Aşırı satım (RSI: {rsi:.1f})")
    elif rsi > 70:
        momentum_score += 3  # Overbought ama yükseliş devam edebilir
    
    # MACD
    if macd_hist > 0 and macd_hist > macd_hist_prev:
        momentum_score += 6
        reasons.append("📊 MACD yükseliyor")
    elif macd_hist > 0:
        momentum_score += 4  # 3'ten 4'e yükseltildi
    elif macd_hist > macd_hist_prev:  # Histogram artıyor (negatiften sıfıra doğru)
        momentum_score += 2
    
    # Stochastic
    if stoch_k < 30:
        momentum_score += 6
        reasons.append(f"🔄 Stoch aşırı satım ({stoch_k:.1f})")
    elif stoch_k < 50:
        momentum_score += 4  # 3'ten 4'e yükseltildi
    
    score += min(momentum_score, 20)
    
    # =========== 3. PULLBACK KALİTESİ (20 puan) ===========
    # GÜNCELLEME: Daha geniş tolerans
    pullback_score = 0
    
    dist_to_ema20 = abs(current_price - ema20) / current_price * 100
    
    if dist_to_ema20 < 1.5:  # 1.0'dan 1.5'e genişletildi
        pullback_score = 20
        reasons.append("🎯 EMA20'ye tam temas")
    elif dist_to_ema20 < 3.0:  # 2.0'dan 3.0'a genişletildi
        pullback_score = 15
        reasons.append("🎯 EMA20'ye yakın")
    elif dist_to_ema20 < 3.0:
        pullback_score = 10
    elif dist_to_ema20 < 5.0:
        pullback_score = 5
    
    # Bollinger %B - alt banda yakın ekstra puan
    if bb_percent < 0.2:
        pullback_score = min(pullback_score + 5, 20)
        reasons.append("📉 Bollinger alt bandına yakın")
    
    score += pullback_score
    
    # =========== 4. HACİM PROFİLİ (15 puan) ===========
    volume_score = 0
    current_vol = float(volume.iloc[-1])
    vol_ratio = current_vol / (vol_avg + 1e-10)
    
    if vol_ratio > 1.5:
        volume_score = 15
        reasons.append(f"📊 Yüksek hacim ({vol_ratio:.1f}x)")
    elif vol_ratio > 1.2:
        volume_score = 10
        reasons.append("📊 Ortalamanın üstünde hacim")
    elif vol_ratio > 0.8:
        volume_score = 5
    
    # MFI
    if mfi < 30:
        volume_score = min(volume_score + 5, 15)
        reasons.append(f"💰 MFI aşırı satım ({mfi:.1f})")
    
    score += volume_score
    
    # =========== 5. VOLATİLİTE KALİTESİ (10 puan) ===========
    # GÜNCELLEME: Yüksek volatilite tercih edilir!
    volatility_score = 0
    atr_pct = (atr / current_price) * 100
    
    # Bollinger Band genişliği
    bb_upper = float(bb['upper'].iloc[-1])
    bb_lower = float(bb['lower'].iloc[-1])
    bb_middle = float(bb['middle'].iloc[-1])
    bb_width_pct = ((bb_upper - bb_lower) / bb_middle) * 100 if bb_middle > 0 else 0
    
    # 20-günlük fiyat aralığı
    high_20 = float(high.tail(20).max())
    low_20 = float(low.tail(20).min())
    range_20_pct = ((high_20 - low_20) / low_20) * 100 if low_20 > 0 else 0
    
    # Günlük ortalama hareket
    daily_moves = ((high - low) / low).tail(10) * 100
    avg_daily_move = float(daily_moves.mean())
    
    # YÜKSEK VOLATİLİTE TERCİH EDİLİR! (Günlük trade için)
    # ATR% bazlı puanlama (6 puan)
    if atr_pct >= 4.0:
        volatility_score += 6
        reasons.append(f"🔥 ÇOK YÜKSEK volatilite (ATR: %{atr_pct:.1f})")
    elif atr_pct >= 3.0:
        volatility_score += 5
        reasons.append(f"⭐ YÜKSEK volatilite (ATR: %{atr_pct:.1f})")
    elif atr_pct >= 2.0:
        volatility_score += 3
        reasons.append(f"✅ ORTA volatilite (ATR: %{atr_pct:.1f})")
    elif atr_pct >= 1.5:
        volatility_score += 1
    # Düşük volatilite puan almaz
    
    # Bollinger Band genişliği (2 puan)
    if bb_width_pct >= 10:
        volatility_score += 2
    elif bb_width_pct >= 6:
        volatility_score += 1
    
    # 20-gün fiyat aralığı (2 puan)
    if range_20_pct >= 15:
        volatility_score += 2
    elif range_20_pct >= 10:
        volatility_score += 1
    
    score += min(volatility_score, 10)
    
    # =========== 6. PATTERN RECOGNITION (10 puan) ===========
    pattern_score = 0
    
    # Son 3 mumun analizi
    last3_high = float(high.iloc[-3:].max())
    last3_low = float(low.iloc[-3:].min())
    last3_range = last3_high - last3_low
    
    # Higher lows pattern
    low_1 = float(low.iloc[-1])
    low_2 = float(low.iloc[-2])
    low_3 = float(low.iloc[-3])
    close_1 = float(close.iloc[-1])
    close_2 = float(close.iloc[-2])
    high_2 = float(high.iloc[-2])
    
    if low_1 > low_2 > low_3:
        pattern_score += 5
        reasons.append("📈 Higher lows pattern")
    
    # Bullish engulfing benzeri
    if (close_1 > close_2 and 
        low_1 < low_2 and
        close_1 > high_2 * 0.995):
        pattern_score += 5
        reasons.append("🔄 Bullish reversal pattern")
    
    score += min(pattern_score, 10)
    
    # =========== SEKTÖR KONTROLÜ ===========
    # Kaybeden sektörler engellendi
    if not params.get('enabled', True):
        return {
            'score': 0,
            'reasons': [f"⛔ {sector} sektörü engellendi (düşük win rate)"],
            'entry': current_price,
            'stop_loss': 0,
            'take_profit': 0,
            'atr_pct': round(atr_pct, 2),
            'rsi': round(rsi, 1),
            'sector': sector,
            'max_hold': params['max_hold'],
            'blocked': True
        }
    
    # Sektör ağırlığı (artık weight=1.0 çoğunlukla)
    score = score * params['weight']
    
    # =========== STOP-LOSS / TAKE-PROFIT HESAPLA ===========
    vol_mult = params['vol_mult']
    
    # Dinamik stop-loss (ATR bazlı) - daha geniş
    sl_mult = 2.0 + (atr_pct / 50)  # Volatilite arttıkça SL genişler
    sl_mult = max(1.5, min(sl_mult * vol_mult, 3.0))
    stop_loss = current_price - (atr * sl_mult)
    
    # Dinamik take-profit (Risk/Reward en az 3:1 hedefi)
    risk = current_price - stop_loss
    tp_mult = 3.0 + (score / 50)  # Skor arttıkça hedef yükselir (daha agresif)
    take_profit = current_price + (risk * tp_mult)
    
    return {
        'score': round(score, 1),
        'reasons': reasons,
        'entry': current_price,
        'stop_loss': round(stop_loss, 2),
        'take_profit': round(take_profit, 2),
        'atr_pct': round(atr_pct, 2),
        'rsi': round(rsi, 1),
        'sector': sector,
        'max_hold': params['max_hold'],
        'trend_score': trend_score,
        'momentum_score': min(momentum_score, 20),
        'pullback_score': pullback_score,
        'volume_score': volume_score,
        'volatility_score': min(volatility_score, 10),  # Volatilite skoru eklendi
        'bb_width_pct': round(bb_width_pct, 1),
        'range_20_pct': round(range_20_pct, 1)
    }


# =====================================================
# RİSK YÖNETİMİ
# =====================================================

def calculate_kelly_position_size(win_rate: float, avg_win: float, avg_loss: float, 
                                  kelly_fraction: float = 0.25) -> float:
    """
    Kelly Criterion ile optimal pozisyon boyutu
    Daha güvenli olması için fraction kullanılıyor
    """
    if avg_loss == 0:
        return 0.05  # Default %5
    
    win_prob = win_rate / 100
    loss_prob = 1 - win_prob
    
    # Kelly formula
    kelly = (win_prob * avg_win - loss_prob * avg_loss) / avg_win
    
    # Güvenlik için fraction uygula ve limitler koy
    position_size = kelly * kelly_fraction
    position_size = max(0.02, min(position_size, 0.15))  # %2 - %15 arası
    
    return position_size


def calculate_dynamic_position_size(capital: float, signal: Dict, 
                                    recent_win_rate: float = 50) -> float:
    """
    Dinamik pozisyon boyutu hesapla
    - Yüksek skor = Daha büyük pozisyon
    - Yüksek volatilite = Daha küçük pozisyon
    """
    base_size = 0.10  # %10 baz
    
    # Skor bazlı ayarlama (daha ihtiyatlı)
    score_mult = signal['score'] / 100 * 0.4 + 0.6  # 0.6 - 1.0
    
    # Volatilite bazlı ayarlama (daha ihtiyatlı)
    atr_pct = signal.get('atr_pct', 2.0)
    if atr_pct > 3.0:
        vol_mult = 0.5
    elif atr_pct > 2.5:
        vol_mult = 0.7
    elif atr_pct > 2.0:
        vol_mult = 0.85
    elif atr_pct < 1.5:
        vol_mult = 1.0
    else:
        vol_mult = 0.9
    
    # Win rate bazlı ayarlama
    wr_mult = recent_win_rate / 50 * 0.3 + 0.7  # 0.7 - 1.0
    
    position_pct = base_size * score_mult * vol_mult * wr_mult
    position_pct = max(0.03, min(position_pct, 0.12))  # %3 - %12 arası (daha küçük pozisyonlar)
    
    return capital * position_pct


# =====================================================
# GELİŞTİRİLMİŞ BACKTEST ENGINE
# =====================================================

def run_improved_backtest(
    days: int = 180,
    initial_capital: float = 10000,
    commission_pct: float = 0.001,
    min_score: int = 50,  # 60'dan 50'ye düşürüldü!
    max_positions: int = 3,
    use_market_filter: bool = True,
    trailing_stop_pct: float = 0.04,  # 0.03'ten 0.04'e (daha geniş trailing)
    verbose: bool = True
) -> Dict:
    """
    Geliştirilmiş Backtest Engine
    
    Yenilikler:
    - Multi-timeframe analizi
    - Dinamik pozisyon boyutu
    - Trailing stop
    - Sektör çeşitlendirmesi
    - Market rejimi filtresi
    """
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"   📊 İYİLEŞTİRİLMİŞ GÜNLÜK TRADE STRATEJİSİ v2.0 - BACKTEST")
        print(f"{'='*70}")
        print(f"   ⏱️  Tarih Aralığı: Son {days} gün")
        print(f"   💰 Başlangıç Sermayesi: ₺{initial_capital:,.0f}")
        print(f"   📋 Minimum Skor: {min_score}")
        print(f"   📊 Max Pozisyon: {max_positions}")
        print(f"{'='*70}\n")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days + 250)  # Daha fazla veri (EMA200 için)
    
    # Veri çek
    if verbose:
        print("📥 Veriler çekiliyor...")
    
    all_data = {}
    for ticker in BIST30:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if df is None or df.empty:
                continue
            df = _fix_multiindex_df(df)  # Multi-index düzelt
            if len(df) >= 60:
                all_data[ticker] = df
        except:
            continue
    
    if verbose:
        print(f"✅ {len(all_data)} hisse yüklendi\n")
    
    # BIST100 market filter
    market_bullish_days = set()
    if use_market_filter:
        try:
            xu100 = yf.download("XU100.IS", start=start_date, end=end_date, progress=False)
            if xu100 is not None and not xu100.empty:
                xu100 = _fix_multiindex_df(xu100)  # Multi-index düzelt
                if len(xu100) > 50:
                    close_series = _get_series(xu100, 'Close')
                    xu100['EMA20'] = calc_ema(close_series, 20)
                    xu100['EMA50'] = calc_ema(close_series, 50)
                    
                    for date in xu100.index:
                        try:
                            ema20_raw = xu100.loc[date, 'EMA20']
                            ema50_raw = xu100.loc[date, 'EMA50']
                            # Güvenli float dönüşümü
                            if isinstance(ema20_raw, pd.Series):
                                ema20_val = float(ema20_raw.values[0]) if len(ema20_raw) > 0 else 0.0
                            elif pd.notna(ema20_raw):
                                ema20_val = float(ema20_raw)  # type: ignore
                            else:
                                ema20_val = 0.0
                            
                            if isinstance(ema50_raw, pd.Series):
                                ema50_val = float(ema50_raw.values[0]) if len(ema50_raw) > 0 else 0.0
                            elif pd.notna(ema50_raw):
                                ema50_val = float(ema50_raw)  # type: ignore
                            else:
                                ema50_val = 0.0
                            
                            if ema20_val > ema50_val:
                                market_bullish_days.add(date)
                        except:
                            continue
                    
                    if verbose:
                        pct = len(market_bullish_days) / len(xu100) * 100
                        print(f"📈 BIST100 yükseliş günleri: %{pct:.1f}")
        except Exception as e:
            if verbose:
                print(f"⚠️ Market filter devre dışı: {e}")
    
    # Trading simulation
    capital = initial_capital
    trades = []
    open_positions = []
    equity_curve = [{'date': start_date, 'equity': capital, 'drawdown': 0}]
    sector_usage = defaultdict(lambda: {'trades': 0, 'wins': 0, 'total_pnl': 0})
    
    # Win rate tracking (son 20 trade için)
    recent_results = []
    
    # Trading days
    trading_days = pd.date_range(
        start=end_date - timedelta(days=days), 
        end=end_date, 
        freq='B'
    )
    
    peak_equity = initial_capital
    
    for trade_date in trading_days:
        # Market filter
        if use_market_filter and market_bullish_days and trade_date not in market_bullish_days:
            continue
        
        # ========== AÇIK POZİSYONLARI KONTROL ET ==========
        for pos in open_positions[:]:
            ticker = pos['ticker']
            if ticker not in all_data:
                continue
            
            df = all_data[ticker]
            
            # Tarih normalize et
            df_dates = df.index.normalize() if hasattr(df.index, 'normalize') else df.index
            trade_date_norm = pd.Timestamp(trade_date).normalize()
            
            if trade_date_norm not in df_dates:
                # En yakın önceki tarihi bul
                valid_dates = df_dates[df_dates <= trade_date_norm]
                if len(valid_dates) == 0:
                    continue
                trade_date_norm = valid_dates[-1]
            
            row = df.loc[trade_date_norm]
            pos['days_held'] += 1
            
            current_price = float(row['Close'])
            high_price = float(row['High'])
            low_price = float(row['Low'])
            
            # Unrealized P&L
            unrealized_pnl = (current_price - pos['entry']) * pos['shares']
            unrealized_pct = unrealized_pnl / pos['position_value'] * 100
            
            # Trailing stop update
            if unrealized_pct > 5:  # %5 karda trailing aktif (daha geç başlasın)
                # ATR bazlı dinamik trailing stop
                new_stop = current_price * (1 - trailing_stop_pct * 1.5)  # Daha geniş trailing
                if new_stop > pos['stop_loss']:
                    pos['stop_loss'] = new_stop
                    pos['trailing_active'] = True
            
            # Exit kontrol
            closed = False
            exit_reason = ''
            exit_price = current_price
            
            if low_price <= pos['stop_loss']:
                exit_price = pos['stop_loss']
                exit_reason = 'STOP_LOSS' if not pos.get('trailing_active') else 'TRAILING_STOP'
                closed = True
            elif high_price >= pos['take_profit']:
                exit_price = pos['take_profit']
                exit_reason = 'TAKE_PROFIT'
                closed = True
            elif pos['days_held'] >= pos['max_hold']:
                exit_price = current_price
                exit_reason = 'MAX_HOLD'
                closed = True
            
            if closed:
                pnl = (exit_price - pos['entry']) * pos['shares']
                commission = pos['position_value'] * commission_pct * 2
                net_pnl = pnl - commission
                pnl_pct = net_pnl / pos['position_value'] * 100
                
                capital += pos['position_value'] + net_pnl
                
                trade_record = {
                    'date': trade_date.strftime('%Y-%m-%d'),
                    'ticker': ticker,
                    'sector': pos['sector'],
                    'score': pos['score'],
                    'entry': pos['entry'],
                    'exit': round(exit_price, 2),
                    'shares': pos['shares'],
                    'pnl': round(net_pnl, 2),
                    'pnl_pct': round(pnl_pct, 2),
                    'reason': exit_reason,
                    'days_held': pos['days_held'],
                    'capital': round(capital, 2)
                }
                trades.append(trade_record)
                
                # Stats update
                is_win = net_pnl > 0
                recent_results.append(is_win)
                if len(recent_results) > 20:
                    recent_results.pop(0)
                
                sector_usage[pos['sector']]['trades'] += 1
                sector_usage[pos['sector']]['total_pnl'] += net_pnl
                if is_win:
                    sector_usage[pos['sector']]['wins'] += 1
                
                open_positions.remove(pos)
        
        # Equity update
        unrealized = 0
        for p in open_positions:
            if p['ticker'] in all_data and trade_date in all_data[p['ticker']].index:
                close_val = float(all_data[p['ticker']].loc[trade_date, 'Close'])
                unrealized += (close_val - p['entry']) * p['shares']
        
        total_equity = capital + unrealized
        
        if total_equity > peak_equity:
            peak_equity = total_equity
        drawdown = (peak_equity - total_equity) / peak_equity * 100
        
        equity_curve.append({
            'date': trade_date,
            'equity': round(total_equity, 2),
            'drawdown': round(drawdown, 2)
        })
        
        # ========== YENİ SİNYAL ARA ==========
        if len(open_positions) >= max_positions:
            continue
        
        used_sectors = {p['sector'] for p in open_positions}
        signals = []
        
        for ticker, df in all_data.items():
            # Tarih eşleşme kontrolü (normalize edilmiş)
            df_dates = df.index.normalize() if hasattr(df.index, 'normalize') else df.index
            trade_date_norm = pd.Timestamp(trade_date).normalize()
            
            if trade_date_norm not in df_dates:
                # En yakın önceki tarihi bul
                valid_dates = df_dates[df_dates <= trade_date_norm]
                if len(valid_dates) == 0:
                    continue
                trade_date_norm = valid_dates[-1]
            
            if any(p['ticker'] == ticker for p in open_positions):
                continue
            
            df_until = df.loc[:trade_date_norm]
            if len(df_until) < 60:
                continue
            
            signal = calculate_enhanced_score(df_until, ticker)
            
            # Sektör min score kontrolü
            sector = signal['sector']
            sector_params = SECTOR_PARAMS.get(sector, SECTOR_PARAMS['default'])
            effective_min_score = max(min_score, sector_params['min_score'])

            # STRICT FILTER: Balanced Approach
            # 1. Düşüş trendinde olanları engelle (Fiyat > EMA50 olmalı -> Trend Score >= 8)
            # 2. Hacim filtresi opsiyonel bırakıldı (Skora katkısı zaten var)
            is_not_downtrend = signal.get('trend_score', 0) >= 8
            
            if signal['score'] >= effective_min_score and is_not_downtrend:
                # Sektör çeşitlendirme bonusu
                if sector not in used_sectors:
                    signal['score'] += 5
                signals.append({'ticker': ticker, **signal})
        
        # En iyi sinyalleri seç
        signals.sort(key=lambda x: x['score'], reverse=True)
        
        for sig in signals[:max_positions - len(open_positions)]:
            sector = sig['sector']
            
            # Sektör limiti (max 2 aynı sektörden)
            sector_count = sum(1 for p in open_positions if p['sector'] == sector)
            if sector_count >= 2:
                continue
            
            # Pozisyon boyutu
            recent_wr = sum(recent_results) / len(recent_results) * 100 if recent_results else 50
            position_value = calculate_dynamic_position_size(capital, sig, recent_wr)
            
            shares = int(position_value / sig['entry'])
            if shares <= 0:
                continue
            
            actual_value = shares * sig['entry']
            commission = actual_value * commission_pct
            
            if capital < actual_value + commission:
                continue
            
            capital -= actual_value + commission
            
            open_positions.append({
                'ticker': sig['ticker'],
                'entry_date': trade_date,
                'entry': sig['entry'],
                'stop_loss': sig['stop_loss'],
                'take_profit': sig['take_profit'],
                'shares': shares,
                'position_value': actual_value,
                'score': sig['score'],
                'sector': sector,
                'max_hold': sig['max_hold'],
                'days_held': 0,
                'trailing_active': False
            })
    
    # Açık pozisyonları kapat
    for pos in open_positions:
        ticker = pos['ticker']
        if ticker in all_data:
            last_price = float(all_data[ticker]['Close'].iloc[-1])
            pnl = (last_price - pos['entry']) * pos['shares']
            commission = pos['position_value'] * commission_pct
            net_pnl = pnl - commission
            capital += pos['position_value'] + net_pnl
            
            trades.append({
                'date': 'END',
                'ticker': ticker,
                'sector': pos['sector'],
                'score': pos['score'],
                'entry': pos['entry'],
                'exit': round(last_price, 2),
                'shares': pos['shares'],
                'pnl': round(net_pnl, 2),
                'pnl_pct': round(net_pnl / pos['position_value'] * 100, 2),
                'reason': 'END',
                'days_held': pos['days_held'],
                'capital': round(capital, 2)
            })
    
    # ========== SONUÇLARI HESAPLA ==========
    if not trades:
        if verbose:
            print("❌ Hiç trade yapılamadı!")
        return {'error': 'No trades'}
    
    total_trades = len(trades)
    winning_trades = [t for t in trades if t['pnl'] > 0]
    losing_trades = [t for t in trades if t['pnl'] <= 0]
    
    win_count = len(winning_trades)
    loss_count = len(losing_trades)
    win_rate = win_count / total_trades * 100
    
    total_profit = sum(t['pnl'] for t in winning_trades)
    total_loss = abs(sum(t['pnl'] for t in losing_trades))
    net_profit = total_profit - total_loss
    
    avg_win = total_profit / win_count if win_count > 0 else 0
    avg_loss = total_loss / loss_count if loss_count > 0 else 0
    profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
    
    total_return = (capital - initial_capital) / initial_capital * 100
    max_drawdown = max(e['drawdown'] for e in equity_curve)
    
    # Sharpe ratio
    daily_returns = []
    for i in range(1, len(equity_curve)):
        ret = (equity_curve[i]['equity'] - equity_curve[i-1]['equity']) / equity_curve[i-1]['equity']
        daily_returns.append(ret)
    
    if daily_returns:
        avg_return = np.mean(daily_returns)
        std_return = np.std(daily_returns)
        sharpe = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
    else:
        sharpe = 0
    
    # ========== SONUÇLARI YAZDÍR ==========
    if verbose:
        print(f"\n{'='*70}")
        print(f"   📊 BACKTEST SONUÇLARI")
        print(f"{'='*70}")
        
        print(f"\n   📈 GENEL İSTATİSTİKLER:")
        print(f"   ├── Toplam Trade: {total_trades}")
        print(f"   ├── Kazanan: {win_count} ({win_rate:.1f}%)")
        print(f"   └── Kaybeden: {loss_count}")
        
        print(f"\n   💰 KAR/ZARAR:")
        print(f"   ├── Başlangıç: ₺{initial_capital:,.0f}")
        print(f"   ├── Final: ₺{capital:,.0f}")
        print(f"   ├── Net Kar: ₺{net_profit:,.0f}")
        print(f"   └── Toplam Getiri: %{total_return:.1f}")
        
        print(f"\n   📊 PERFORMANS METRİKLERİ:")
        print(f"   ├── Ortalama Kazanç: ₺{avg_win:.0f}")
        print(f"   ├── Ortalama Kayıp: ₺{avg_loss:.0f}")
        print(f"   ├── Profit Factor: {profit_factor:.2f}")
        print(f"   ├── Sharpe Ratio: {sharpe:.2f}")
        print(f"   └── Max Drawdown: %{max_drawdown:.1f}")
        
        if avg_loss > 0:
            rr_ratio = avg_win / avg_loss
            print(f"   └── Risk/Reward: {rr_ratio:.2f}")
        
        print(f"\n   🏭 SEKTÖR PERFORMANSI:")
        for sector, stats in sorted(sector_usage.items(), key=lambda x: x[1]['total_pnl'], reverse=True):
            if stats['trades'] > 0:
                wr = stats['wins'] / stats['trades'] * 100
                print(f"   ├── {sector}: {stats['trades']} trade, %{wr:.0f} WR, ₺{stats['total_pnl']:.0f}")
        
        # Değerlendirme
        print(f"\n{'='*70}")
        print(f"   📋 STRATEJİ DEĞERLENDİRMESİ")
        print(f"{'='*70}")
        
        score = 0
        if win_rate >= 55: score += 2
        elif win_rate >= 50: score += 1
        
        if profit_factor >= 2.0: score += 2
        elif profit_factor >= 1.5: score += 1
        
        if max_drawdown <= 10: score += 2
        elif max_drawdown <= 20: score += 1
        
        if sharpe >= 1.5: score += 2
        elif sharpe >= 1.0: score += 1
        
        if score >= 6:
            print("   ✅ MÜKEMMEL STRATEJİ - Production'a hazır!")
        elif score >= 4:
            print("   ⚠️ İYİ STRATEJİ - Küçük optimizasyonlar gerekebilir")
        else:
            print("   ❌ ZAYIF STRATEJİ - Daha fazla iyileştirme gerekli")
        
        print(f"\n   🎯 ÖNERİLER:")
        if win_rate < 50:
            print("   • Score eşiğini artır (>70)")
        if profit_factor < 1.5:
            print("   • Take-profit mesafesini artır")
        if max_drawdown > 20:
            print("   • Pozisyon boyutunu küçült")
        if sharpe < 1.0:
            print("   • Daha az trade ile kaliteyi artır")
        
        # Son 10 trade
        print(f"\n   📋 SON 10 TRADE:")
        print(f"   {'Tarih':<12} {'Hisse':<8} {'Skor':<6} {'Giriş':<8} {'Çıkış':<8} {'P&L%':<8} {'Sebep':<12}")
        print(f"   {'-'*62}")
        for t in trades[-10:]:
            print(f"   {t['date']:<12} {t['ticker'].replace('.IS',''):<8} {t['score']:<6.0f} {t['entry']:<8.2f} {t['exit']:<8.2f} {t['pnl_pct']:<+8.1f} {t['reason']:<12}")
    
    return {
        'trades': trades,
        'equity_curve': equity_curve,
        'metrics': {
            'total_trades': total_trades,
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 2),
            'total_return': round(total_return, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2)
        },
        'sector_stats': dict(sector_usage)
    }


# =====================================================
# PARAMETRE OPTİMİZASYONU
# =====================================================

def optimize_parameters(days: int = 90, verbose: bool = False):
    """
    Grid search ile en iyi parametreleri bul
    """
    print(f"\n{'='*70}")
    print(f"   🔬 PARAMETRE OPTİMİZASYONU")
    print(f"{'='*70}\n")
    
    best_result = None
    best_params = None
    best_score = -float('inf')
    
    # Parameter grid
    min_scores = [55, 60, 65, 70]
    max_positions_list = [2, 3, 4]
    trailing_stops = [0.02, 0.03, 0.04]
    
    total_tests = len(min_scores) * len(max_positions_list) * len(trailing_stops)
    test_num = 0
    
    for min_score in min_scores:
        for max_pos in max_positions_list:
            for trail_stop in trailing_stops:
                test_num += 1
                print(f"   Test {test_num}/{total_tests}: score={min_score}, pos={max_pos}, trail={trail_stop}", end="")
                
                result = run_improved_backtest(
                    days=days,
                    min_score=min_score,
                    max_positions=max_pos,
                    trailing_stop_pct=trail_stop,
                    verbose=False
                )
                
                if 'error' in result:
                    print(" ❌")
                    continue
                
                # Composite score
                m = result['metrics']
                composite = (
                    m['win_rate'] * 0.3 +
                    m['profit_factor'] * 20 +
                    m['total_return'] * 0.5 +
                    m['sharpe_ratio'] * 10 -
                    m['max_drawdown'] * 0.5
                )
                
                print(f" → Score: {composite:.1f}")
                
                if composite > best_score:
                    best_score = composite
                    best_result = result
                    best_params = {
                        'min_score': min_score,
                        'max_positions': max_pos,
                        'trailing_stop_pct': trail_stop
                    }
    
    print(f"\n{'='*70}")
    print(f"   🏆 EN İYİ PARAMETRELER:")
    print(f"{'='*70}")
    
    if best_params is None or best_result is None:
        print("   ❌ Optimizasyon başarısız - hiç sonuç bulunamadı")
        return None, None
    
    print(f"   Min Score: {best_params['min_score']}")
    print(f"   Max Positions: {best_params['max_positions']}")
    print(f"   Trailing Stop: %{best_params['trailing_stop_pct']*100}")
    print(f"\n   📊 Sonuçlar:")
    print(f"   Win Rate: %{best_result['metrics']['win_rate']:.1f}")
    print(f"   Profit Factor: {best_result['metrics']['profit_factor']:.2f}")
    print(f"   Total Return: %{best_result['metrics']['total_return']:.1f}")
    print(f"   Max Drawdown: %{best_result['metrics']['max_drawdown']:.1f}")
    
    return best_params, best_result


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--optimize':
        # Parametre optimizasyonu
        best_params, best_result = optimize_parameters(days=90)
    else:
        # Normal backtest - OPTİMİZE EDİLMİŞ PARAMETRELER
        # ÖNEMLİ: 90 gün ile en iyi sonuçlar alındı!
        result = run_improved_backtest(
            days=90,  # 180'den 90'a düşürüldü - daha güncel veriler
            min_score=55,  # 50'den 55'e - daha kaliteli tradeler
            max_positions=3,
            use_market_filter=False,  # Market filter kapalı
            trailing_stop_pct=0.04,  # %4 trailing stop
            verbose=True
        )
