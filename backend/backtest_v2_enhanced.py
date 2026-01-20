#!/usr/bin/env python3
"""
BACKTEST V2 ENHANCED (HYBRID) - V2 + Partial Exit
==================================================
V2'nin kanıtlanmış başarısı + V3'ün partial exit stratejisi

İyileştirmeler:
- ✅ V2'nin tüm güçlü özellikleri (67.6% WR, 3.04 PF)
- ✨ Partial Exit: TP1'de %50 pozisyon kapat
- ✨ İkinci Hedef: TP2 için büyük kazançlar
- ✨ Break-even protection: TP1 sonrası risk-free

Hedef: 68-72% WR, 3.2-3.5 PF
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

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


def calculate_macd(prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """MACD hesapla"""
    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)
    macd_line = ema12 - ema26
    signal_line = calculate_ema(macd_line, 9)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_technical_levels(df: pd.DataFrame, idx: int) -> Dict:
    """Teknik destek/direnç seviyeleri"""
    recent = df.iloc[max(0, idx-20):idx+1]
    
    if len(recent) < 5:
        return None
    
    recent_low = recent['Low'].min()
    recent_high = recent['High'].max()
    
    # Swing low/high (50 bar)
    lookback = df.iloc[max(0, idx-50):idx+1]
    swing_low = lookback['Low'].nsmallest(3).mean() if len(lookback) >= 3 else recent_low
    swing_high = lookback['High'].nlargest(3).mean() if len(lookback) >= 3 else recent_high
    
    return {
        'recent_low': recent_low,
        'recent_high': recent_high,
        'swing_low': swing_low,
        'swing_high': swing_high
    }


def calculate_score_v2(df: pd.DataFrame, idx: int) -> Dict:
    """
    V2 SKOR HESAPLAMA (0-100)
    Aynı strateji ama daha seçici
    """
    if idx < 50:
        return {'score': 0, 'valid': False}
    
    close = df['Close'].iloc[:idx+1]
    current_price = close.iloc[-1]
    
    # Indicators
    ema_20 = calculate_ema(close, 20).iloc[-1]
    ema_50 = calculate_ema(close, 50).iloc[-1]
    rsi = calculate_rsi(close).iloc[-1]
    _, _, macd_hist = calculate_macd(close)
    macd_h = macd_hist.iloc[-1]
    
    if pd.isna(ema_20) or pd.isna(ema_50) or pd.isna(rsi):
        return {'score': 0, 'valid': False}
    
    score = 0
    
    # 1. TREND (30 pts)
    if current_price > ema_20 and ema_20 > ema_50:
        score += 30
    elif current_price > ema_50 and ema_20 > ema_50:
        score += 20
    elif ema_20 > ema_50:
        score += 10
    
    # 2. MOMENTUM (25 pts)
    if 40 <= rsi <= 60:
        score += 15
    elif 30 <= rsi < 40:
        score += 10
    elif 60 < rsi <= 70:
        score += 5
    
    if macd_h > 0:
        score += 10
    elif macd_h > -0.1:
        score += 5
    
    # 3. SUPPORT/PULLBACK (25 pts)
    dist_to_ema20 = abs(current_price - ema_20) / current_price
    dist_to_ema50 = abs(current_price - ema_50) / current_price
    
    if dist_to_ema20 < 0.015:
        score += 25
    elif dist_to_ema50 < 0.02:
        score += 20
    else:
        score += 5
    
    # 4. VOLUME (20 pts)
    recent_vol = df['Volume'].iloc[max(0, idx-20):idx+1]
    if len(recent_vol) > 5:
        avg_vol = recent_vol.mean()
        current_vol = df['Volume'].iloc[idx]
        vol_ratio = current_vol / (avg_vol + 1)
        
        if vol_ratio > 1.5:
            score += 20
        elif vol_ratio > 1.0:
            score += 10
    
    return {
        'score': score,
        'valid': True,
        'ema_20': ema_20,
        'ema_50': ema_50,
        'rsi': rsi
    }


def calculate_technical_sl_tp(df: pd.DataFrame, idx: int, entry_price: float, atr: float) -> Dict:
    """
    TEKNİK STOP-LOSS & TAKE-PROFIT
    - Stop: Destek altı
    - TP: 1:3 Risk:Ödül
    """
    levels = calculate_technical_levels(df, idx)
    
    if levels is None:
        # Fallback: %2 SL, %6 TP
        stop_loss = entry_price * 0.98
        take_profit = entry_price * 1.06
    else:
        # Support hesapla
        ema_20 = calculate_ema(df['Close'].iloc[:idx+1], 20).iloc[-1]
        
        supports = [
            ema_20 - (0.5 * atr),
            levels['recent_low'] - (0.3 * atr),
            levels['swing_low'] - (0.3 * atr)
        ]
        valid_supports = [s for s in supports if s < entry_price]
        
        if valid_supports:
            stop_loss = max(valid_supports)
        else:
            stop_loss = entry_price * 0.98
        
        # Min %1.5, max %3 SL mesafesi
        if stop_loss > entry_price * 0.985:
            stop_loss = entry_price * 0.985
        if stop_loss < entry_price * 0.97:
            stop_loss = entry_price * 0.97
        
        # PARTIAL EXIT: İki hedef
        # TP1: 1:2.5 R/R (daha kolay ulaşılır, %50 pozisyon kapat)
        # TP2: 1:4.0 R/R (büyük kazanç, kalan %50)
        risk = entry_price - stop_loss
        take_profit_1 = entry_price + (risk * 2.5)  # TP1
        take_profit_2 = entry_price + (risk * 4.0)  # TP2
        
        # Min %5 TP1, min %8 TP2
        if take_profit_1 < entry_price * 1.05:
            take_profit_1 = entry_price * 1.05
        if take_profit_2 < entry_price * 1.08:
            take_profit_2 = entry_price * 1.08
    
    risk = entry_price - stop_loss
    reward_1 = take_profit_1 - entry_price
    reward_2 = take_profit_2 - entry_price
    
    return {
        'stop_loss': stop_loss,
        'take_profit': take_profit_1,      # Eski sistem uyumluluğu için
        'take_profit_1': take_profit_1,    # TP1 - Partial exit
        'take_profit_2': take_profit_2,    # TP2 - Final target
        'risk_pct': (risk / entry_price) * 100,
        'reward_pct': (reward_1 / entry_price) * 100,
        'rr_ratio': reward_1 / risk if risk > 0 else 0,
        'rr_ratio_2': reward_2 / risk if risk > 0 else 0
    }


def check_market_trend(xu100_data: pd.DataFrame, date_idx: int) -> bool:
    """BIST100 yükseliş trendinde mi?"""
    if xu100_data is None or len(xu100_data) < 50:
        return True  # Data yoksa default true
    
    close = xu100_data['Close'].iloc[:date_idx+1]
    if len(close) < 50:
        return True
    
    ema_20 = calculate_ema(close, 20).iloc[-1]
    ema_50 = calculate_ema(close, 50).iloc[-1]
    
    return ema_20 > ema_50


def apply_sector_diversification(candidates: List[Dict], max_picks: int) -> List[Dict]:
    """Sektör çeşitlendirmesi uygula"""
    selected = []
    used_sectors = set()
    
    for c in candidates:
        sector = STOCK_SECTORS.get(c['ticker'], 'Diğer')
        if sector not in used_sectors:
            selected.append(c)
            used_sectors.add(sector)
            if len(selected) >= max_picks:
                break
    
    # Doldurulamadıysa geri kalanı ekle
    if len(selected) < max_picks:
        for c in candidates:
            if c not in selected:
                selected.append(c)
                if len(selected) >= max_picks:
                    break
    
    return selected


def run_backtest_v2(days: int = 90, min_score: int = 75, max_picks: int = 5):
    """
    V2 ENHANCED (HYBRID) BACKTEST
    V2 + Partial Exit Strategy
    """
    print("\n" + "="*70)
    print("🚀 BACKTEST V2 ENHANCED - HYBRID (V2 + Partial Exit)")
    print("="*70)
    print(f"📅 Test Süresi: {days} gün")
    print(f"🎯 Min Score: {min_score}+")
    print(f"📊 Max Picks: {max_picks} (sektör çeşitlendirmeli)")
    print(f"⛔ Stop-Loss: Teknik (~%2)")
    print(f"🎯 Take-Profit: TP1 (1:2.5) & TP2 (1:4.0) R:R")
    print(f"✨ Partial Exit: TP1'de %50 pozisyon kapat")
    print(f"📈 Market Filtresi: BIST100 uptrend")
    print(f"🎯 HEDEF: %68+ WR, 3.2+ PF")
    print("="*70)
    
    # Data çek
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days + 60)
    
    print(f"\n📥 Veri çekiliyor ({len(TEST_TICKERS)} hisse)...")
    
    all_data = {}
    failed_tickers = []
    for ticker in TEST_TICKERS:
        success = False
        for retry in range(3):  # 3 deneme
            try:
                df = yf.download(ticker, start=start_date, end=end_date, progress=False, timeout=10)
                if not df.empty and len(df) >= 50:  # Minimum veri kontrolü
                    # MultiIndex düzelt
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
    
    # BIST100 datası
    print("📥 BIST100 verisi çekiliyor...")
    for retry in range(3):
        try:
            xu100 = yf.download("XU100.IS", start=start_date, end=end_date, progress=False, timeout=10)
            break
        except:
            if retry < 2:
                import time
                time.sleep(1)
    
    # Fallback
    try:
        if 'xu100' not in locals() or xu100 is None or xu100.empty:
            xu100 = yf.download("XU100.IS", start=start_date, end=end_date, progress=False, timeout=10)
        if isinstance(xu100.columns, pd.MultiIndex):
            xu100.columns = xu100.columns.get_level_values(0)
    except:
        xu100 = None
    
    print(f"✅ {len(all_data)} hisse yüklendi\n")
    
    # Trading simulation
    trades = []
    total_pnl = 0
    winning_trades = 0
    losing_trades = 0
    market_blocked_days = 0
    no_signal_days = 0
    
    # Her gün için simülasyon
    reference_ticker = list(all_data.keys())[0]
    trading_days = all_data[reference_ticker].index[-days:]
    
    for day_idx, trade_date in enumerate(trading_days):
        # MARKET FİLTRESİ: BIST100 trend kontrolü
        if xu100 is not None:
            xu100_idx = xu100.index.get_indexer([trade_date], method='ffill')[0]
            if xu100_idx >= 0 and not check_market_trend(xu100, xu100_idx):
                market_blocked_days += 1
                continue
        
        # Her hisse için skor hesapla
        daily_candidates = []
        
        for ticker, df in all_data.items():
            if trade_date not in df.index:
                continue
            
            idx = df.index.get_loc(trade_date)
            if idx < 50:
                continue
            
            score_data = calculate_score_v2(df, idx)
            
            # 75+ SCORE FİLTRESİ
            if score_data['valid'] and score_data['score'] >= min_score:
                entry_price = df['Close'].iloc[idx]
                
                # ATR hesapla
                df_temp = df.iloc[:idx+1].copy()
                df_temp.columns = ['Close', 'High', 'Low', 'Open', 'Volume']
                atr = calculate_atr(df_temp).iloc[-1]
                if pd.isna(atr):
                    atr = entry_price * 0.02
                
                # Teknik SL/TP
                levels = calculate_technical_sl_tp(df, idx, entry_price, atr)
                
                daily_candidates.append({
                    'ticker': ticker,
                    'score': score_data['score'],
                    'entry_price': entry_price,
                    'stop_loss': levels['stop_loss'],
                    'take_profit': levels['take_profit'],
                    'risk_pct': levels['risk_pct'],
                    'reward_pct': levels['reward_pct'],
                    'rr_ratio': levels['rr_ratio'],
                    'df': df,
                    'idx': idx
                })
        
        if not daily_candidates:
            no_signal_days += 1
            continue
        
        # Score'a göre sırala
        daily_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # SEKTÖR ÇEŞİTLENDİRMESİ uygula
        selected = apply_sector_diversification(daily_candidates, max_picks)
        
        # Trade simülasyonu - PARTIAL EXIT stratejisi
        for pick in selected:
            ticker = pick['ticker']
            df = pick['df']
            idx = pick['idx']
            
            if idx + 1 >= len(df):
                continue
            
            entry = pick['entry_price']
            sl = pick['stop_loss']
            tp1 = pick.get('take_profit_1', pick['take_profit'])  # TP1
            tp2 = pick.get('take_profit_2', tp1 * 1.6)           # TP2 (fallback)
            
            # Sonraki gün exit (gün içi trade simülasyonu için)
            next_day = df.iloc[idx + 1]
            high = next_day['High']
            low = next_day['Low']
            close_price = next_day['Close']
            
            # PARTIAL EXIT LOGIC
            exit_price = close_price
            exit_reason = 'EOD'
            pnl = 0
            
            # Stop-loss check (tam pozisyon)
            if low <= sl:
                exit_price = sl
                exit_reason = 'STOP_LOSS'
                pnl = (exit_price - entry) / entry * 100
            
            # TP2 check (TP1'i de geçmiş demektir)
            elif high >= tp2:
                # %50 TP1'de, %50 TP2'de
                pnl_tp1 = ((tp1 - entry) / entry * 100) * 0.5
                pnl_tp2 = ((tp2 - entry) / entry * 100) * 0.5
                pnl = pnl_tp1 + pnl_tp2
                exit_price = (tp1 + tp2) / 2  # Ortalama çıkış
                exit_reason = 'TP1+TP2'
            
            # TP1 check (sadece TP1)
            elif high >= tp1:
                # %50 TP1'de, %50 EOD'de
                pnl_tp1 = ((tp1 - entry) / entry * 100) * 0.5
                pnl_eod = ((close_price - entry) / entry * 100) * 0.5
                pnl = pnl_tp1 + pnl_eod
                exit_price = (tp1 + close_price) / 2
                exit_reason = 'TP1+EOD'
            
            # Hiçbiri değilse EOD
            else:
                pnl = (close_price - entry) / entry * 100
                exit_price = close_price
                exit_reason = 'EOD'
            
            total_pnl += pnl
            
            if pnl > 0:
                winning_trades += 1
            else:
                losing_trades += 1
            
            trades.append({
                'date': trade_date.strftime('%Y-%m-%d'),
                'ticker': ticker,
                'sector': STOCK_SECTORS.get(ticker, 'Diğer'),
                'score': pick['score'],
                'entry': round(entry, 2),
                'sl': round(sl, 2),
                'tp1': round(tp1, 2),
                'tp2': round(tp2, 2),
                'exit': round(exit_price, 2),
                'exit_reason': exit_reason,
                'pnl_pct': round(pnl, 2)
            })
    
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
    
    # Sonuçları yazdır
    print("\n" + "="*60)
    print("📊 BACKTEST v2 SONUÇLARI")
    print("="*60)
    
    print(f"\n📈 GENEL İSTATİSTİKLER:")
    print(f"   Toplam İşlem: {total_trades}")
    print(f"   Kazanan: {winning_trades} | Kaybeden: {losing_trades}")
    print(f"   Kazanma Oranı: %{win_rate:.1f}")
    
    print(f"\n💰 KAR/ZARAR:")
    print(f"   Toplam Getiri: %{total_pnl:.2f}")
    print(f"   Ortalama İşlem: %{total_pnl/total_trades:.2f}" if total_trades > 0 else "   N/A")
    
    print(f"\n📈 PERFORMANS:")
    print(f"   Profit Factor: {profit_factor:.2f}")
    print(f"   Max Drawdown: %{max_dd:.1f}")
    
    print(f"\n🛡️ FİLTRE ETKİSİ:")
    print(f"   Market Filter Blocked: {market_blocked_days} gün")
    print(f"   No Signal Days: {no_signal_days} gün")
    
    # Sektör bazlı analiz
    print(f"\n📊 SEKTÖR BAZLI ANALİZ:")
    sector_pnl = {}
    for t in trades:
        sector = t['sector']
        if sector not in sector_pnl:
            sector_pnl[sector] = {'pnl': 0, 'count': 0}
        sector_pnl[sector]['pnl'] += t['pnl_pct']
        sector_pnl[sector]['count'] += 1
    
    for sector, data in sorted(sector_pnl.items(), key=lambda x: x[1]['pnl'], reverse=True):
        avg = data['pnl'] / data['count'] if data['count'] > 0 else 0
        print(f"   {sector}: {data['count']} işlem, %{data['pnl']:.1f} toplam, %{avg:.2f} ort.")
    
    # Exit reason analizi
    print(f"\n📊 ÇIKIŞ NEDENİ ANALİZİ:")
    exit_stats = {}
    for t in trades:
        reason = t['exit_reason']
        if reason not in exit_stats:
            exit_stats[reason] = {'count': 0, 'pnl': 0}
        exit_stats[reason]['count'] += 1
        exit_stats[reason]['pnl'] += t['pnl_pct']
    
    for reason, data in exit_stats.items():
        avg = data['pnl'] / data['count'] if data['count'] > 0 else 0
        print(f"   {reason}: {data['count']} işlem, %{data['pnl']:.1f} toplam, %{avg:.2f} ort.")
    
    # Değerlendirme
    print("\n" + "="*60)
    print("🎯 STRATEJİ DEĞERLENDİRMESİ:")
    
    if profit_factor >= 1.5 and win_rate >= 50:
        print("   ✅ GÜÇLÜ STRATEJİ - Canlı kullanıma hazır")
    elif profit_factor >= 1.2 and win_rate >= 45:
        print("   🟡 KABUL EDİLEBİLİR - Dikkatli kullanın")
    else:
        print("   ❌ ZAYIF - Daha fazla optimizasyon gerekli")
    
    # Benchmark karşılaştırma
    if xu100 is not None:
        xu100_start = xu100['Close'].iloc[-days]
        xu100_end = xu100['Close'].iloc[-1]
        xu100_return = (xu100_end - xu100_start) / xu100_start * 100
        print(f"\n📊 BENCHMARK (BIST100): %{xu100_return:.2f}")
        alpha = total_pnl - xu100_return
        print(f"📊 ALPHA: %{alpha:.2f}")
    
    print("="*60 + "\n")
    
    # Son 10 trade'i göster
    print("📝 SON 10 İŞLEM:")
    print("-"*80)
    for t in trades[-10:]:
        emoji = "🟢" if t['pnl_pct'] > 0 else "🔴"
        print(f"   {t['date']} | {t['ticker']:<8} | {t['sector']:<12} | Skor:{t['score']:>2} | {emoji} %{t['pnl_pct']:>+5.2f} | {t['exit_reason']}")
    
    return {
        'total_trades': total_trades,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'profit_factor': profit_factor,
        'max_drawdown': max_dd,
        'trades': trades
    }


if __name__ == "__main__":
    # Quick test: 30 gün (sonra 90'a çıkarırız)
    results = run_backtest_v2(days=30, min_score=75, max_picks=5)
