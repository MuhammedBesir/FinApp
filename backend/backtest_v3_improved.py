#!/usr/bin/env python3
"""
BACKTEST v3 - IMPROVED WIN RATE STRATEGY
=========================================
Win rate optimize edilmiş backtest

İyileştirmeler:
- Çoklu timeframe trend analizi
- Volume kalite kontrolü
- RSI optimal bölge filtreleri
- Market structure analizi
- Dinamik stop-loss ve take-profit
- Partial exit stratejisi
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Win Rate Booster Module
from win_rate_booster import apply_win_rate_boosters

# Hisse sektörleri
STOCK_SECTORS = {
    "AKBNK.IS": "Bankacılık",
    "AKSEN.IS": "Enerji",
    "ARCLK.IS": "Dayanıklı Tüketim",
    "ASELS.IS": "Savunma",
    "BIMAS.IS": "Perakende",
    "EKGYO.IS": "GYO",
    "ENKAI.IS": "İnşaat",
    "EREGL.IS": "Demir Çelik",
    "FROTO.IS": "Otomotiv",
    "GARAN.IS": "Bankacılık",
    "GUBRF.IS": "Kimya",
    "HEKTS.IS": "Kimya",
    "ISCTR.IS": "Bankacılık",
    "KCHOL.IS": "Holding",
    "KRDMD.IS": "Demir Çelik",
    "ODAS.IS": "Enerji",
    "PETKM.IS": "Petrokimya",
    "PGSUS.IS": "Havacılık",
    "SAHOL.IS": "Holding",
    "SASA.IS": "Petrokimya",
    "SISE.IS": "Cam",
    "TAVHL.IS": "Havacılık",
    "TCELL.IS": "Telekomünikasyon",
    "THYAO.IS": "Havacılık",
    "TKFEN.IS": "Holding",
    "TOASO.IS": "Otomotiv",
    "TRALT.IS": "Altın",
    "TUPRS.IS": "Enerji",
    "YKBNK.IS": "Bankacılık",
}

# Test için hisse listesi
TEST_TICKERS = [
    "THYAO.IS", "GARAN.IS", "AKBNK.IS", 
    "YKBNK.IS", "HALKB.IS", "VAKBN.IS",
    "SASA.IS", "PETKM.IS", "KOZAL.IS",
    "DOHOL.IS", "ARCLK.IS", "GUBRF.IS",
    "EKGYO.IS", "ENKAI.IS", "TAVHL.IS"
]


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """RSI hesapla"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-10)
    return 100 - (100 / (1 + rs))


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """EMA hesapla"""
    return prices.ewm(span=period, adjust=False).mean()


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """ATR hesapla"""
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def check_multi_timeframe_trend(df: pd.DataFrame, idx: int) -> Tuple[bool, float, List[str]]:
    """
    ÇOKLU TIMEFRAME TREND ANALİZİ
    
    Kısa, orta ve uzun vadeli trend uyumu kontrol edilir.
    Tüm timeframe'ler uyumlu olmalı!
    """
    reasons = []
    score = 0
    
    close = df['Close'].iloc[:idx+1]
    
    if len(close) < 50:
        return False, 0, ["❌ Yetersiz veri (min 50 gün)"]
    
    # Kısa vadeli: EMA 9 vs 21
    ema_9 = calculate_ema(close, 9).iloc[-1]
    ema_21 = calculate_ema(close, 21).iloc[-1]
    
    if ema_9 > ema_21:
        diff_pct = ((ema_9 - ema_21) / ema_21) * 100
        score += 30
        reasons.append(f"✅ Kısa vadeli yükseliş (EMA9 > EMA21, +%{diff_pct:.2f})")
    else:
        reasons.append("❌ Kısa vadeli düşüş")
        return False, score, reasons
    
    # Orta vadeli: EMA 21 vs 50
    ema_50 = calculate_ema(close, 50).iloc[-1]
    
    if ema_21 > ema_50:
        diff_pct = ((ema_21 - ema_50) / ema_50) * 100
        score += 35
        reasons.append(f"✅ Orta vadeli yükseliş (EMA21 > EMA50, +%{diff_pct:.2f})")
    else:
        reasons.append("❌ Orta vadeli düşüş")
        return False, score, reasons
    
    # Uzun vadeli: EMA 50 vs 200 (TAMAMEN OPSIYONEL)
    if len(close) >= 200:
        ema_200 = calculate_ema(close, 200).iloc[-1]
        if ema_50 > ema_200:
            score += 20
            reasons.append("✅ Uzun vadeli yükseliş (EMA50 > EMA200)")
        else:
            reasons.append("⚠️ Uzun vadeli düşüş (bonus yok)")
    else:
        score += 10  # Veri yoksa nötr bonus
        reasons.append("ℹ️ EMA200 verisi yok (nötr)")
    
    # Kısa ve orta vadeli uyumlu olmalı
    is_aligned = score >= 50  # Daha esnek
    
    return is_aligned, score, reasons


def check_volume_quality(df: pd.DataFrame, idx: int) -> Tuple[bool, float, List[str]]:
    """
    VOLUME KALİTE KONTROLÜ
    
    1. Volume ratio (son vs ortalama)
    2. Volume trend (artış var mı?)
    3. Fiyat-volume konfirmasyonu
    """
    reasons = []
    score = 0
    
    volumes = df['Volume'].iloc[:idx+1]
    prices = df['Close'].iloc[:idx+1]
    
    if len(volumes) < 20:
        return False, 0, ["❌ Yetersiz volume verisi"]
    
    # 1. Volume Ratio
    current_vol = volumes.iloc[-1]
    avg_vol = volumes.tail(20).mean()
    vol_ratio = current_vol / avg_vol if avg_vol > 0 else 0
    
    if vol_ratio >= 2.0:
        score += 40
        reasons.append(f"🔥 Çok yüksek volume ({vol_ratio:.2f}x ortalama)")
    elif vol_ratio >= 1.5:
        score += 35
        reasons.append(f"✅ Yüksek volume ({vol_ratio:.2f}x)")
    elif vol_ratio >= 1.2:
        score += 30
        reasons.append(f"✅ Normal üstü volume ({vol_ratio:.2f}x)")
    elif vol_ratio >= 1.0:
        score += 25
        reasons.append(f"✅ Normal volume ({vol_ratio:.2f}x)")
    elif vol_ratio >= 0.8:
        score += 20
        reasons.append(f"⚠️ Normal altı volume ({vol_ratio:.2f}x)")
    else:
        reasons.append(f"❌ Çok düşük volume ({vol_ratio:.2f}x)")
        return False, score, reasons
    
    # 2. Volume Trend (son 5 gün vs önceki 5 gün)
    if len(volumes) >= 10:
        recent_vol = volumes.tail(5).mean()
        prev_vol = volumes.iloc[-10:-5].mean()
        
        if prev_vol > 0:
            vol_trend = recent_vol / prev_vol
            
            if vol_trend >= 1.3:
                score += 30
                reasons.append(f"🔥 Volume artış trendi (+%{(vol_trend-1)*100:.1f})")
            elif vol_trend >= 1.1:
                score += 20
                reasons.append(f"✅ Volume artıyor (+%{(vol_trend-1)*100:.1f})")
            elif vol_trend >= 0.9:
                score += 10
                reasons.append("⚠️ Volume stabil")
            else:
                reasons.append("❌ Volume azalıyor")
    
    # 3. Fiyat-Volume Konfirmasyonu
    if len(prices) >= 2 and len(volumes) >= 2:
        price_change = (prices.iloc[-1] - prices.iloc[-2]) / prices.iloc[-2]
        vol_change = (volumes.iloc[-1] - volumes.iloc[-2]) / volumes.iloc[-2]
        
        if price_change > 0 and vol_change > 0:
            score += 30
            reasons.append("✅ Fiyat-Volume uyumu")
        elif price_change > 0 and vol_change < 0:
            score -= 15
            reasons.append("⚠️ Fiyat yukarı ama volume düşük (şüpheli)")
    
    is_quality = score >= 60
    
    return is_quality, score, reasons


def check_rsi_optimal_zone(df: pd.DataFrame, idx: int) -> Tuple[bool, float, List[str]]:
    """
    RSI OPTIMAL BÖLGE KONTROLÜ
    
    RSI optimal bölgede olmalı (40-55 arası).
    Çok aşırı seviyelerden kaçın!
    """
    reasons = []
    score = 0
    
    close = df['Close'].iloc[:idx+1]
    
    if len(close) < 14:
        return False, 0, ["❌ Yetersiz RSI verisi"]
    
    rsi = calculate_rsi(close, 14).iloc[-1]
    
    # Optimal bölge: 30-65 (genişletildi - başarılı ayar)
    if 35 <= rsi <= 60:
        score = 100
        reasons.append(f"✅ RSI optimal bölgede ({rsi:.1f})")
    elif 30 <= rsi < 35:
        score = 80
        reasons.append(f"✅ RSI düşük ama kabul edilebilir ({rsi:.1f})")
    elif 60 < rsi <= 65:
        score = 80
        reasons.append(f"✅ RSI yüksek ama kabul edilebilir ({rsi:.1f})")
    elif 25 <= rsi < 30:
        score = 60
        reasons.append(f"⚠️ RSI çok düşük ({rsi:.1f})")
    elif 65 < rsi <= 70:
        score = 60
        reasons.append(f"⚠️ RSI çok yüksek ({rsi:.1f})")
    else:
        score = 0
        reasons.append(f"❌ RSI aşırı ({rsi:.1f})")
    
    is_optimal = score >= 60
    
    return is_optimal, score, reasons


def check_market_structure(df: pd.DataFrame, idx: int) -> Tuple[bool, float, List[str]]:
    """
    MARKET STRUCTURE ANALİZİ
    
    1. Dirence mesafe kontrolü (min %3)
    2. Destek üzerinde olma
    3. Higher Lows pattern
    """
    reasons = []
    score = 0
    
    if len(df) < 20:
        return False, 0, ["❌ Yetersiz veri"]
    
    current_price = df['Close'].iloc[idx]
    highs = df['High'].iloc[:idx+1]
    lows = df['Low'].iloc[:idx+1]
    
    # 1. Dirence Mesafe Kontrolü (esnek)
    recent_high = highs.tail(20).max()
    distance_to_high_pct = ((recent_high - current_price) / current_price) * 100
    
    if distance_to_high_pct >= 5.0:
        score += 40
        reasons.append(f"✅ Dirence uzak (%{distance_to_high_pct:.1f})")
    elif distance_to_high_pct >= 3.0:
        score += 35
        reasons.append(f"✅ Dirence orta mesafe (%{distance_to_high_pct:.1f})")
    elif distance_to_high_pct >= 2.0:
        score += 30
        reasons.append(f"✅ Dirence yakın ama kabul edilebilir (%{distance_to_high_pct:.1f})")
    elif distance_to_high_pct >= 1.5:
        score += 25
        reasons.append(f"⚠️ Dirence yakın (%{distance_to_high_pct:.1f})")
    else:
        score += 15
        reasons.append(f"⚠️ Dirence çok yakın (%{distance_to_high_pct:.1f})")
    
    # 2. Destek Üzerinde Olma
    recent_low = lows.tail(20).min()
    distance_to_low_pct = ((current_price - recent_low) / current_price) * 100
    
    if 2.0 <= distance_to_low_pct <= 8.0:
        score += 30
        reasons.append(f"✅ Destek üzerinde optimal (%{distance_to_low_pct:.1f})")
    elif distance_to_low_pct > 8.0:
        score += 20
        reasons.append(f"⚠️ Destekten uzak (%{distance_to_low_pct:.1f})")
    else:
        score += 10
        reasons.append(f"⚠️ Desteğe çok yakın (%{distance_to_low_pct:.1f})")
    
    # 3. Higher Lows Pattern
    if len(lows) >= 15:
        low_vals = lows.tail(15).values
        if len(low_vals) >= 9:
            low1 = min(low_vals[0:5])
            low2 = min(low_vals[5:10])
            low3 = min(low_vals[10:])
            
            if low3 > low2 > low1:
                score += 30
                reasons.append("✅ Yükselen dipler (bullish structure)")
            elif low3 > low1:
                score += 15
                reasons.append("⚠️ Dipler karışık")
    
    is_favorable = score >= 60
    
    return is_favorable, score, reasons


def calculate_technical_stop_loss(
    entry_price: float,
    df: pd.DataFrame,
    idx: int,
    atr: float
) -> float:
    """
    TEKNİK STOP-LOSS
    
    Sabit %2 yerine teknik destek seviyelerine göre
    """
    close = df['Close'].iloc[:idx+1]
    lows = df['Low'].iloc[:idx+1]
    
    # EMA20
    ema_20 = calculate_ema(close, 20).iloc[-1]
    
    candidates = []
    
    # 1. ATR-based
    if atr > 0:
        atr_stop = entry_price - (1.5 * atr)
        candidates.append(atr_stop)
    
    # 2. EMA20-based
    if ema_20 > 0 and ema_20 < entry_price:
        ema_stop = ema_20 * 0.99
        candidates.append(ema_stop)
    
    # 3. Recent low
    recent_low = lows.tail(10).min()
    if recent_low < entry_price:
        recent_stop = recent_low * 0.98
        candidates.append(recent_stop)
    
    # 4. Swing low
    if len(lows) >= 20:
        swing_low = lows.tail(20).min()
        if swing_low < entry_price:
            swing_stop = swing_low * 0.97
            candidates.append(swing_stop)
    
    # En yakın uygun stop'u seç (max %2.5)
    valid_stops = [s for s in candidates if s < entry_price]
    
    if valid_stops:
        stop_loss = max(valid_stops)
        min_stop = entry_price * 0.975  # Max %2.5
        stop_loss = max(stop_loss, min_stop)
    else:
        stop_loss = entry_price * 0.98
    
    return stop_loss


def calculate_dynamic_targets(
    entry_price: float,
    stop_loss: float,
    df: pd.DataFrame,
    idx: int
) -> Dict:
    """
    DİNAMİK HEDEF FİYATLAR
    
    Target 1: %50 pozisyon çıkışı (conservative)
    Target 2: Geri kalan %50 (aggressive)
    """
    risk = entry_price - stop_loss
    
    # Yakın direnç
    recent_high = df['High'].iloc[:idx+1].tail(20).max()
    
    # Target 1: 1:2.2 R/R veya yakın direnç (başarılı ayar)
    target_1_rr = entry_price + (risk * 2.2)
    target_1_tech = recent_high * 0.98
    target_1 = min(target_1_rr, target_1_tech) if target_1_tech > entry_price else target_1_rr
    
    # Target 2: 1:3.5 R/R veya uzak direnç (dengeli)
    if len(df) >= 50:
        far_high = df['High'].iloc[:idx+1].tail(50).max()
        target_2_tech = far_high * 0.99
    else:
        target_2_tech = target_1 * 1.1
    
    target_2_rr = entry_price + (risk * 3.5)
    target_2 = max(target_2_rr, target_2_tech) if target_2_tech > target_1 else target_2_rr
    
    return {
        'stop_loss': round(stop_loss, 2),
        'target_1': round(target_1, 2),
        'target_2': round(target_2, 2),
        'rr_1': round((target_1 - entry_price) / risk, 2),
        'rr_2': round((target_2 - entry_price) / risk, 2)
    }


def generate_signal(df: pd.DataFrame, idx: int, ticker: str) -> Optional[Dict]:
    """
    İYİLEŞTİRİLMİŞ SİNYAL ÜRETİCİ
    
    Tüm filtreleri uygular ve geçenleri döndürür
    """
    # 1. Multi-timeframe Trend
    mtf_pass, mtf_score, mtf_reasons = check_multi_timeframe_trend(df, idx)
    if not mtf_pass:
        return None  # Trend uyumu yoksa direkt red
    
    # 2. Volume Quality
    vol_pass, vol_score, vol_reasons = check_volume_quality(df, idx)
    if not vol_pass:
        return None  # Volume yetersizse red
    
    # 3. RSI Optimal Zone
    rsi_pass, rsi_score, rsi_reasons = check_rsi_optimal_zone(df, idx)
    if not rsi_pass:
        return None  # RSI uygun değilse red
    
    # 4. Market Structure
    struct_pass, struct_score, struct_reasons = check_market_structure(df, idx)
    if not struct_pass:
        return None  # Market structure uygun değilse red
    
    # Overall score
    overall_score = int(
        mtf_score * 0.35 +
        vol_score * 0.25 +
        rsi_score * 0.20 +
        struct_score * 0.20
    )
    
    # === WIN RATE BOOSTER - YENİ! ===
    # Candlestick patterns, S/R quality, Momentum alignment ekle
    try:
        boosted_score, booster_reasons = apply_win_rate_boosters(df, idx, overall_score)
        overall_score = boosted_score
        all_reasons = mtf_reasons + vol_reasons + rsi_reasons + struct_reasons + booster_reasons
    except Exception as e:
        # Booster hata verirse normal devam et
        all_reasons = mtf_reasons + vol_reasons + rsi_reasons + struct_reasons
    
    # Minimum 55 skor (başarılı ayar)
    if overall_score < 55:
        return None
    
    # Entry price
    entry_price = df['Close'].iloc[idx]
    
    # ATR
    atr_values = calculate_atr(df.iloc[:idx+1], 14)
    atr = atr_values.iloc[-1] if len(atr_values) > 0 else entry_price * 0.02
    
    # Stop-loss ve Targets
    stop_loss = calculate_technical_stop_loss(entry_price, df, idx, atr)
    targets = calculate_dynamic_targets(entry_price, stop_loss, df, idx)
    
    # Min R/R: 1.8 (esnek - başarılı ayar)
    if targets['rr_1'] < 1.8:
        return None
    
    return {
        'ticker': ticker,
        'score': overall_score,
        'entry': entry_price,
        'sl': targets['stop_loss'],
        'tp1': targets['target_1'],
        'tp2': targets['target_2'],
        'rr_1': targets['rr_1'],
        'rr_2': targets['rr_2'],
        'reasons': all_reasons
    }


def run_improved_backtest(days: int = 90, max_picks: int = 5):
    """
    İYİLEŞTİRİLMİŞ BACKTEST - BAŞARILI AYARLAR + WIN RATE BOOSTER
    """
    print("\n" + "="*70)
    print("🚀 BACKTEST v3 - WIN RATE BOOSTER (Optimized)")
    print("="*70)
    print(f"📅 Test Süresi: {days} gün")
    print(f"📊 Max Picks: {max_picks} (sektör çeşitlendirmeli)")
    print(f"🎯 Min Score: 55+ (başarılı ayar korundu)")
    print(f"⛔ Stop-Loss: Teknik (dinamik)")
    print(f"🎯 Targets: 1:2.2 & 1:3.5 R/R (dinamik)")
    print(f"📉 Partial Exit: TP1'de %50 pozisyon")
    print(f"🔥 BOOSTER: Candlestick + S/R + Momentum")
    print(f"🎯 HEDEF: %70+ Win Rate, 3.0+ Profit Factor")
    print("="*70)
    
    # Data çek
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days + 100)  # Daha fazla veri çek
    
    print(f"\n📥 Veri çekiliyor ({len(TEST_TICKERS)} hisse)...")
    
    all_data = {}
    failed_tickers = []
    for ticker in TEST_TICKERS:
        success = False
        for retry in range(3):  # 3 deneme
            try:
                df = yf.download(ticker, period="1y", progress=False, timeout=20)
                if not df.empty and len(df) >= 50:  # 50 gün yeterli
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    all_data[ticker] = df
                    success = True
                    break
            except Exception as e:
                if retry < 2:
                    import time
                    time.sleep(1)  # 1 saniye bekle
                continue
        
        if not success:
            failed_tickers.append(ticker)
    
    print(f"✅ {len(all_data)} hisse yüklendi")
    if failed_tickers:
        print(f"⚠️  Yüklenemedi: {', '.join(failed_tickers)}")
    
    if len(all_data) == 0:
        print("\n❌ HATA: Hiç veri yüklenemedi!")
        print("💡 İnternet bağlantınızı kontrol edin ve tekrar deneyin.")
        return None
    
    print()
    
    # Trading simulation
    trades = []
    total_pnl = 0
    winning_trades = 0
    losing_trades = 0
    
    if not all_data:
        print("\n❌ HATA: Hiç veri yüklenemedi!")
        print("💡 Çözümler:")
        print("   1. İnternet bağlantınızı kontrol edin")
        print("   2. yfinance güncel mi: pip install --upgrade yfinance")
        print("   3. Ticker'lar doğru mu kontrol edin")
        return {'total_trades': 0, 'win_rate': 0, 'total_pnl': 0, 'profit_factor': 0, 'max_drawdown': 0, 'trades': []}
    
    # Trading days
    reference_ticker = list(all_data.keys())[0]
    trading_days = all_data[reference_ticker].index[-days:]
    
    for day_idx, trade_date in enumerate(trading_days):
        print(f"\r📅 İşlem günü: {day_idx+1}/{len(trading_days)}", end="", flush=True)
        
        # Her hisse için sinyal kontrol et
        candidates = []
        
        for ticker, df in all_data.items():
            df_idx = df.index.get_indexer([trade_date], method='ffill')[0]
            
            if df_idx < 50:  # Min 50 gün veri gerekli
                continue
            
            signal = generate_signal(df, df_idx, ticker)
            
            if signal:
                candidates.append(signal)
        
        if not candidates:
            continue
        
        # Score'a göre sırala
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Sektör çeşitlendirmesi
        selected = []
        used_sectors = set()
        
        for c in candidates:
            sector = STOCK_SECTORS.get(c['ticker'], 'Diğer')
            if sector not in used_sectors:
                selected.append(c)
                used_sectors.add(sector)
                if len(selected) >= max_picks:
                    break
        
        # Seçilen hisseleri trade'e sok
        for signal in selected:
            ticker = signal['ticker']
            df = all_data[ticker]
            entry_idx = df.index.get_indexer([trade_date], method='ffill')[0]
            
            # Çıkış simülasyonu (sonraki 10 günde)
            exit_price = None
            exit_reason = None
            exit_idx = None
            position_pnl = 0
            
            for future_idx in range(entry_idx + 1, min(entry_idx + 11, len(df))):
                high = df['High'].iloc[future_idx]
                low = df['Low'].iloc[future_idx]
                close = df['Close'].iloc[future_idx]
                
                # Stop-loss check
                if low <= signal['sl']:
                    exit_price = signal['sl']
                    exit_reason = "SL"
                    exit_idx = future_idx
                    position_pnl = ((exit_price - signal['entry']) / signal['entry']) * 100
                    break
                
                # Target 1 check (%50 pozisyon)
                if high >= signal['tp1']:
                    # %50 TP1'de kapat
                    pnl_tp1 = ((signal['tp1'] - signal['entry']) / signal['entry']) * 100 * 0.5
                    
                    # Geri kalan %50 için devam et
                    for future_idx2 in range(future_idx + 1, min(entry_idx + 11, len(df))):
                        high2 = df['High'].iloc[future_idx2]
                        low2 = df['Low'].iloc[future_idx2]
                        close2 = df['Close'].iloc[future_idx2]
                        
                        # Geri kalan için trailing stop (%4 aktivasyon)
                        # %4 karda trailing başlat
                        trailing_stop = signal['entry'] * 1.04 if close2 >= signal['entry'] * 1.04 else signal['entry']
                        
                        if low2 <= trailing_stop:
                            # %50 break-even'de kapat
                            position_pnl = pnl_tp1  # Sadece TP1 karı
                            exit_price = (signal['tp1'] + signal['entry']) / 2  # Ortalama
                            exit_reason = "TP1+BE"
                            exit_idx = future_idx2
                            break
                        
                        # Target 2 check
                        if high2 >= signal['tp2']:
                            pnl_tp2 = ((signal['tp2'] - signal['entry']) / signal['entry']) * 100 * 0.5
                            position_pnl = pnl_tp1 + pnl_tp2
                            exit_price = (signal['tp1'] + signal['tp2']) / 2
                            exit_reason = "TP1+TP2"
                            exit_idx = future_idx2
                            break
                    
                    if exit_price:
                        break
                    else:
                        # 10 gün bitti, %50 TP1, %50 son fiyat
                        last_close = df['Close'].iloc[min(entry_idx + 10, len(df) - 1)]
                        pnl_remaining = ((last_close - signal['entry']) / signal['entry']) * 100 * 0.5
                        position_pnl = pnl_tp1 + pnl_remaining
                        exit_price = (signal['tp1'] + last_close) / 2
                        exit_reason = "TP1+10D"
                        exit_idx = min(entry_idx + 10, len(df) - 1)
                        break
            
            # 10 gün doldu ama hiçbir şey olmadı
            if exit_price is None:
                exit_idx = min(entry_idx + 10, len(df) - 1)
                exit_price = df['Close'].iloc[exit_idx]
                exit_reason = "10D"
                position_pnl = ((exit_price - signal['entry']) / signal['entry']) * 100
            
            # Trade kaydet
            total_pnl += position_pnl
            
            if position_pnl > 0:
                winning_trades += 1
            else:
                losing_trades += 1
            
            trades.append({
                'date': trade_date.strftime('%Y-%m-%d'),
                'ticker': ticker,
                'sector': STOCK_SECTORS.get(ticker, 'Diğer'),
                'score': signal['score'],
                'entry': round(signal['entry'], 2),
                'sl': signal['sl'],
                'tp1': signal['tp1'],
                'tp2': signal['tp2'],
                'exit': round(exit_price, 2),
                'exit_reason': exit_reason,
                'pnl_pct': round(position_pnl, 2),
                'rr_1': signal['rr_1'],
                'rr_2': signal['rr_2']
            })
    
    print("\n")  # Clear progress line
    
    # Sonuçları hesapla
    total_trades = len(trades)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    # Profit Factor
    gross_profit = sum(t['pnl_pct'] for t in trades if t['pnl_pct'] > 0)
    gross_loss = abs(sum(t['pnl_pct'] for t in trades if t['pnl_pct'] < 0))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    # Max Drawdown
    cumulative = 0
    peak = 0
    max_dd = 0
    for t in trades:
        cumulative += t['pnl_pct']
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd
    
    # Average R/R
    avg_rr = sum(t['rr_1'] for t in trades) / len(trades) if trades else 0
    
    # Sonuçları yazdır
    print("\n" + "="*70)
    print("📊 BACKTEST v3 SONUÇLARI")
    print("="*70)
    
    print(f"\n📈 GENEL İSTATİSTİKLER:")
    print(f"   Toplam İşlem: {total_trades}")
    print(f"   Kazanan: {winning_trades} | Kaybeden: {losing_trades}")
    print(f"   ⭐ Kazanma Oranı: %{win_rate:.1f}")
    
    print(f"\n💰 KAR/ZARAR:")
    print(f"   Toplam Getiri: %{total_pnl:.2f}")
    print(f"   Ortalama İşlem: %{total_pnl/total_trades:.2f}" if total_trades > 0 else "   N/A")
    print(f"   Gross Profit: %{gross_profit:.2f}")
    print(f"   Gross Loss: %{gross_loss:.2f}")
    
    print(f"\n📈 PERFORMANS:")
    print(f"   ⭐ Profit Factor: {profit_factor:.2f}")
    print(f"   Max Drawdown: %{max_dd:.1f}")
    print(f"   Avg Risk/Reward: 1:{avg_rr:.2f}")
    
    # Çıkış nedeni analizi
    print(f"\n📊 ÇIKIŞ NEDENİ ANALİZİ:")
    exit_stats = {}
    for t in trades:
        reason = t['exit_reason']
        if reason not in exit_stats:
            exit_stats[reason] = {'count': 0, 'pnl': 0}
        exit_stats[reason]['count'] += 1
        exit_stats[reason]['pnl'] += t['pnl_pct']
    
    for reason, data in sorted(exit_stats.items(), key=lambda x: x[1]['count'], reverse=True):
        avg = data['pnl'] / data['count'] if data['count'] > 0 else 0
        pct = (data['count'] / total_trades * 100) if total_trades > 0 else 0
        print(f"   {reason}: {data['count']} işlem (%{pct:.1f}), %{data['pnl']:.1f} toplam, %{avg:.2f} ort.")
    
    # Değerlendirme
    print("\n" + "="*70)
    print("🎯 STRATEJİ DEĞERLENDİRMESİ:")
    
    if profit_factor >= 1.8 and win_rate >= 60:
        print("   ✅ MÜKEMMEL STRATEJİ - Canlı kullanıma hazır!")
    elif profit_factor >= 1.5 and win_rate >= 55:
        print("   ✅ GÜÇLÜ STRATEJİ - Canlı kullanıma hazır")
    elif profit_factor >= 1.3 and win_rate >= 50:
        print("   🟡 KABUL EDİLEBİLİR - Dikkatli kullanın")
    else:
        print("   ⚠️ İYİLEŞTİRME GEREKLİ - Daha fazla optimizasyon")
    
    print("="*70 + "\n")
    
    # Son 10 işlem
    print("📝 SON 10 İŞLEM:")
    print("-"*80)
    for t in trades[-10:]:
        emoji = "🟢" if t['pnl_pct'] > 0 else "🔴"
        print(f"   {t['date']} | {t['ticker']:<8} | Skor:{t['score']:>2} | R/R:1:{t['rr_1']:.1f} | {emoji} %{t['pnl_pct']:>+6.2f} | {t['exit_reason']}")
    
    return {
        'total_trades': total_trades,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'profit_factor': profit_factor,
        'max_drawdown': max_dd,
        'trades': trades
    }


if __name__ == "__main__":
    results = run_improved_backtest(days=90, max_picks=3)
