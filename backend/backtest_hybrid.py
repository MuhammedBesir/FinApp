#!/usr/bin/env python3
"""
BACKTEST HYBRID - V2 + V3 İYİ YANLARINI BİRLEŞTİRİR
====================================================
V2'den Alınanlar:
- Min Score: 75+ (yüksek kalite filtre)
- Market filtresi: BIST100 uptrend
- Sektör çeşitlendirmesi
- Stop-Loss: Teknik (~%2, çok sıkı değil)
- Max Picks: 5

V3'ten Alınanlar:
- ✨ Win Rate Booster (opsiyonel bonus)
- ✨ Partial Exit Stratejisi (TP1'de %50)
- ✨ Dinamik R/R hedefleri
- ✨ İkinci hedef (TP2)

Hedef: %70+ WR, 3.0+ PF, <8% Max DD
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Win Rate Booster
try:
    from win_rate_booster import apply_win_rate_boosters
    BOOSTER_AVAILABLE = True
except:
    BOOSTER_AVAILABLE = False
    print("⚠️  Win rate booster yüklenemedi, standart mod")

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
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    return tr.rolling(window=period).mean()


def calculate_macd(prices: pd.Series, fast=12, slow=26, signal=9):
    """MACD hesapla"""
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def generate_hybrid_signal(df: pd.DataFrame, ticker: str, idx: int) -> Optional[Dict]:
    """
    HYBRID SİNYAL ÜRETİMİ
    V2 base + V3 booster (opsiyonel)
    """
    if idx < 200:
        return None
    
    close = df['Close'].iloc[:idx+1]
    high = df['High'].iloc[:idx+1]
    low = df['Low'].iloc[:idx+1]
    volume = df['Volume'].iloc[:idx+1]
    
    current_price = close.iloc[-1]
    
    # İndikatörler
    rsi = calculate_rsi(close)
    ema_9 = calculate_ema(close, 9)
    ema_21 = calculate_ema(close, 21)
    ema_50 = calculate_ema(close, 50)
    ema_200 = calculate_ema(close, 200)
    atr = calculate_atr(df.iloc[:idx+1])
    macd_line, signal_line, macd_hist = calculate_macd(close)
    
    # Mevcut değerler
    rsi_val = rsi.iloc[-1]
    ema_9_val = ema_9.iloc[-1]
    ema_21_val = ema_21.iloc[-1]
    ema_50_val = ema_50.iloc[-1]
    ema_200_val = ema_200.iloc[-1]
    atr_val = atr.iloc[-1]
    macd_val = macd_line.iloc[-1]
    signal_val = signal_line.iloc[-1]
    macd_hist_val = macd_hist.iloc[-1]
    
    # === V2 BASE SCORING ===
    score = 0
    reasons = []
    
    # 1. Trend (30 puan)
    if current_price > ema_9_val > ema_21_val:
        score += 15
        reasons.append("Kısa trend güçlü")
    if ema_21_val > ema_50_val:
        score += 10
        reasons.append("Orta trend yukarı")
    if current_price > ema_200_val:
        score += 5
        reasons.append("Uzun trend yukarı")
    
    # 2. RSI (20 puan)
    if 40 <= rsi_val <= 65:
        score += 20
        reasons.append(f"RSI optimal ({rsi_val:.1f})")
    elif 30 <= rsi_val <= 70:
        score += 10
        reasons.append(f"RSI kabul edilebilir ({rsi_val:.1f})")
    
    # 3. MACD (20 puan)
    if macd_val > signal_val and macd_hist_val > 0:
        score += 20
        reasons.append("MACD pozitif")
    elif macd_val > signal_val:
        score += 10
        reasons.append("MACD yukarı kesişim")
    
    # 4. Volume (15 puan)
    vol_avg_20 = volume.iloc[-20:].mean()
    vol_current = volume.iloc[-1]
    if vol_current > vol_avg_20 * 1.2:
        score += 15
        reasons.append("Volume yüksek")
    elif vol_current > vol_avg_20:
        score += 7
        reasons.append("Volume normal")
    
    # 5. Pozisyon (15 puan)
    swing_low = low.iloc[-10:].min()
    swing_high = high.iloc[-10:].max()
    position = (current_price - swing_low) / (swing_high - swing_low + 1e-10)
    if 0.3 <= position <= 0.6:
        score += 15
        reasons.append("Pozisyon ideal")
    elif 0.2 <= position <= 0.7:
        score += 8
        reasons.append("Pozisyon iyi")
    
    # === V3 BOOSTER (OPSIYONEL) ===
    booster_active = False
    if BOOSTER_AVAILABLE:
        try:
            boosted_score, booster_reasons = apply_win_rate_boosters(df.iloc[:idx+1], idx, score)
            if boosted_score > score:
                score = boosted_score
                reasons.extend(booster_reasons)
                booster_active = True
        except:
            pass
    
    # Min score: 70 (V2: 75, biraz daha esnek)
    if score < 70:
        return None
    
    # === STOP LOSS & TAKE PROFIT ===
    # Stop Loss: V2 tarzı (teknik, çok sıkı değil)
    atr_stop = current_price - (atr_val * 2.0)  # 2.0x ATR (V3'te 2.5 çok sıkıydı)
    ema_stop = ema_21_val * 0.98  # EMA21'in %2 altı
    swing_stop = swing_low * 0.985  # Swing low'un %1.5 altı
    
    stop_loss = max(atr_stop, ema_stop, swing_stop)
    risk = current_price - stop_loss
    
    # Çok dar stop'u engelle (min %1.5 risk)
    if risk / current_price < 0.015:
        return None
    
    # Take Profit: V3 tarzı (dinamik, partial exit)
    # TP1: 1:2.5 R/R (V2: 1:3, V3: 1:2.2) - orta yol
    # TP2: 1:4.0 R/R (bonus hedef)
    target_1 = current_price + (risk * 2.5)
    target_2 = current_price + (risk * 4.0)
    
    rr_1 = (target_1 - current_price) / risk
    rr_2 = (target_2 - current_price) / risk
    
    # Min R/R: 2.0
    if rr_1 < 2.0:
        return None
    
    return {
        'ticker': ticker,
        'score': int(score),
        'entry': current_price,
        'sl': stop_loss,
        'tp1': target_1,
        'tp2': target_2,
        'rr_1': rr_1,
        'rr_2': rr_2,
        'reasons': reasons,
        'booster_active': booster_active
    }


def check_market_trend(xu100_data: pd.DataFrame, date_idx: int) -> bool:
    """BIST100 yükseliş trendinde mi? (V2'den)"""
    if xu100_data is None or len(xu100_data) < 50:
        return True
    
    close = xu100_data['Close'].iloc[:date_idx+1]
    if len(close) < 50:
        return True
    
    ema_20 = calculate_ema(close, 20).iloc[-1]
    ema_50 = calculate_ema(close, 50).iloc[-1]
    
    return ema_20 > ema_50


def apply_sector_diversification(candidates: List[Dict], max_picks: int) -> List[Dict]:
    """Sektör çeşitlendirmesi (V2'den)"""
    selected = []
    used_sectors = set()
    
    for c in candidates:
        sector = STOCK_SECTORS.get(c['ticker'], 'Diğer')
        if sector not in used_sectors:
            selected.append(c)
            used_sectors.add(sector)
            if len(selected) >= max_picks:
                break
    
    if len(selected) < max_picks:
        for c in candidates:
            if c not in selected:
                selected.append(c)
                if len(selected) >= max_picks:
                    break
    
    return selected


def run_hybrid_backtest(days: int = 90, max_picks: int = 5):
    """
    HYBRID STRATEJİ BACKTEST
    V2 Base + V3 Best Features
    """
    print("\n" + "="*70)
    print("🚀 BACKTEST HYBRID - V2 + V3 EN İYİ ÖZELLİKLER")
    print("="*70)
    print(f"📅 Test Süresi: {days} gün")
    print(f"🎯 Min Score: 70+ (V2 base, biraz esnek)")
    print(f"📊 Max Picks: {max_picks} (sektör çeşitlendirmeli)")
    print(f"⛔ Stop-Loss: Teknik (~%2, V2 tarzı)")
    print(f"🎯 Take-Profit: 1:2.5 & 1:4.0 R/R (V3 tarzı)")
    print(f"📉 Partial Exit: TP1'de %50 (V3 feature)")
    print(f"📈 Market Filtresi: BIST100 uptrend (V2)")
    if BOOSTER_AVAILABLE:
        print(f"✨ Booster: Candlestick + S/R + Momentum (opsiyonel bonus)")
    print(f"🎯 HEDEF: %68+ WR, 2.8+ PF, <8% Max DD")
    print("="*70)
    
    # Data çek
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days + 100)
    
    print(f"\n📥 Veri çekiliyor ({len(TEST_TICKERS)} hisse)...")
    
    all_data = {}
    failed_tickers = []
    for ticker in TEST_TICKERS:
        success = False
        for retry in range(3):
            try:
                df = yf.download(ticker, start=start_date, end=end_date, progress=False, timeout=10)
                if not df.empty and len(df) >= 50:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    all_data[ticker] = df
                    success = True
                    break
            except:
                if retry < 2:
                    import time
                    time.sleep(1)
                continue
        
        if not success:
            failed_tickers.append(ticker)
    
    print(f"✅ {len(all_data)} hisse yüklendi")
    if failed_tickers:
        print(f"⚠️  Yüklenemedi: {', '.join(failed_tickers)}")
    
    if len(all_data) == 0:
        print("\n❌ HATA: Hiç veri yüklenemedi!")
        return None
    
    # BIST100 çek
    print(f"📥 BIST100 verisi çekiliyor...")
    try:
        xu100 = yf.download('XU100.IS', start=start_date, end=end_date, progress=False)
        if isinstance(xu100.columns, pd.MultiIndex):
            xu100.columns = xu100.columns.get_level_values(0)
    except:
        xu100 = None
        print("⚠️  BIST100 yüklenemedi, market filtresi devre dışı")
    
    print()
    
    # Backtest loop
    reference_ticker = list(all_data.keys())[0]
    total_days = len(all_data[reference_ticker])
    start_idx = 100  # 100 gün yeterli (200 çok fazlaydı)
    
    if total_days <= start_idx:
        print(f"\n⚠️  Yeterli veri yok! Toplam {total_days} gün, minimum {start_idx} gün gerekli.")
        return None
    
    trades = []
    active_positions = {}
    daily_balance = [0]
    market_filter_blocked = 0
    no_signal_days = 0
    booster_used_count = 0
    
    for day_idx in range(start_idx, total_days):
        date = all_data[reference_ticker].index[day_idx]
        
        # Market trend check (V2 feature)
        if xu100 is not None and len(xu100) > day_idx:
            xu100_idx = None
            # XU100 için doğru index'i bul
            try:
                xu100_idx = xu100.index.get_loc(date, method='ffill')
            except:
                xu100_idx = None
            
            if xu100_idx is not None:
                market_ok = check_market_trend(xu100, xu100_idx)
                if not market_ok:
                    market_filter_blocked += 1
                    continue
        
        # Position management (V3 tarzı partial exit)
        positions_to_remove = []
        for ticker, pos in active_positions.items():
            if ticker not in all_data:
                continue
            
            df = all_data[ticker]
            if day_idx >= len(df):
                continue
            
            current_price = df['Close'].iloc[day_idx]
            high_today = df['High'].iloc[day_idx]
            low_today = df['Low'].iloc[day_idx]
            
            pos['days_held'] += 1
            
            # Stop Loss check
            if low_today <= pos['sl']:
                pnl = ((pos['sl'] - pos['entry']) / pos['entry']) * 100
                trades.append({
                    'ticker': ticker,
                    'entry_date': pos['entry_date'],
                    'exit_date': date,
                    'entry': pos['entry'],
                    'exit': pos['sl'],
                    'pnl': pnl,
                    'reason': 'STOP_LOSS',
                    'days': pos['days_held'],
                    'score': pos['score']
                })
                positions_to_remove.append(ticker)
                continue
            
            # TP1 check (V3 feature: partial exit)
            if not pos.get('tp1_hit', False) and high_today >= pos['tp1']:
                pos['tp1_hit'] = True
                pos['tp1_date'] = date
                # %50 pozisyon kapat
                pnl_partial = ((pos['tp1'] - pos['entry']) / pos['entry']) * 100 * 0.5
                pos['pnl_accumulated'] = pnl_partial
                # Kalan %50 için break-even yap
                pos['sl'] = pos['entry']
                continue
            
            # TP2 check (full exit)
            if pos.get('tp1_hit', False) and high_today >= pos['tp2']:
                # Kalan %50 pozisyon
                pnl_remaining = ((pos['tp2'] - pos['entry']) / pos['entry']) * 100 * 0.5
                total_pnl = pos['pnl_accumulated'] + pnl_remaining
                trades.append({
                    'ticker': ticker,
                    'entry_date': pos['entry_date'],
                    'exit_date': date,
                    'entry': pos['entry'],
                    'exit': pos['tp2'],
                    'pnl': total_pnl,
                    'reason': 'TP1+TP2',
                    'days': pos['days_held'],
                    'score': pos['score']
                })
                positions_to_remove.append(ticker)
                continue
            
            # 10 gün limiti
            if pos['days_held'] >= 10:
                if pos.get('tp1_hit', False):
                    # TP1 kırılmış, kalan %50
                    pnl_remaining = ((current_price - pos['entry']) / pos['entry']) * 100 * 0.5
                    total_pnl = pos['pnl_accumulated'] + pnl_remaining
                    reason = 'TP1+10D'
                else:
                    # TP1 kırılmamış, %100 pozisyon
                    total_pnl = ((current_price - pos['entry']) / pos['entry']) * 100
                    reason = '10D'
                
                trades.append({
                    'ticker': ticker,
                    'entry_date': pos['entry_date'],
                    'exit_date': date,
                    'entry': pos['entry'],
                    'exit': current_price,
                    'pnl': total_pnl,
                    'reason': reason,
                    'days': pos['days_held'],
                    'score': pos['score']
                })
                positions_to_remove.append(ticker)
        
        for ticker in positions_to_remove:
            del active_positions[ticker]
        
        # Yeni sinyal ara
        if len(active_positions) < max_picks:
            candidates = []
            
            for ticker in all_data.keys():
                if ticker in active_positions:
                    continue
                
                df = all_data[ticker]
                if day_idx >= len(df):
                    continue
                
                signal = generate_hybrid_signal(df, ticker, day_idx)
                if signal:
                    candidates.append(signal)
                    if signal.get('booster_active', False):
                        booster_used_count += 1
            
            if candidates:
                # Score'a göre sırala
                candidates.sort(key=lambda x: x['score'], reverse=True)
                
                # Sektör çeşitlendirmesi uygula (V2 feature)
                picks = apply_sector_diversification(candidates, max_picks - len(active_positions))
                
                for signal in picks:
                    active_positions[signal['ticker']] = {
                        'entry_date': date,
                        'entry': signal['entry'],
                        'sl': signal['sl'],
                        'tp1': signal['tp1'],
                        'tp2': signal['tp2'],
                        'days_held': 0,
                        'score': signal['score'],
                        'tp1_hit': False,
                        'pnl_accumulated': 0
                    }
            else:
                no_signal_days += 1
        
        # Balance tracking
        current_balance = sum(t['pnl'] for t in trades)
        daily_balance.append(current_balance)
        
        # Progress
        if (day_idx - start_idx) % 10 == 0:
            print(f"\r📅 İşlem günü: {day_idx - start_idx}/{total_days - start_idx}", end='', flush=True)
    
    print(f"\r📅 İşlem günü: {total_days - start_idx}/{total_days - start_idx}")
    
    # Analiz
    if not trades:
        print("\n⚠️  Hiç işlem gerçekleşmedi!")
        return None
    
    total_trades = len(trades)
    winners = [t for t in trades if t['pnl'] > 0]
    losers = [t for t in trades if t['pnl'] <= 0]
    win_count = len(winners)
    loss_count = len(losers)
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
    
    total_return = sum(t['pnl'] for t in trades)
    avg_trade = total_return / total_trades if total_trades > 0 else 0
    
    gross_profit = sum(t['pnl'] for t in winners) if winners else 0
    gross_loss = abs(sum(t['pnl'] for t in losers)) if losers else 0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
    
    # Max Drawdown
    peak = daily_balance[0]
    max_dd = 0
    for balance in daily_balance:
        if balance > peak:
            peak = balance
        dd = peak - balance
        if dd > max_dd:
            max_dd = dd
    
    # Exit reason analysis
    exit_reasons = {}
    for t in trades:
        reason = t['reason']
        if reason not in exit_reasons:
            exit_reasons[reason] = {'count': 0, 'total_pnl': 0}
        exit_reasons[reason]['count'] += 1
        exit_reasons[reason]['total_pnl'] += t['pnl']
    
    # Sektör analizi
    sector_stats = {}
    for t in trades:
        sector = STOCK_SECTORS.get(t['ticker'], 'Diğer')
        if sector not in sector_stats:
            sector_stats[sector] = {'count': 0, 'total_pnl': 0}
        sector_stats[sector]['count'] += 1
        sector_stats[sector]['total_pnl'] += t['pnl']
    
    # Results
    print("\n" + "="*70)
    print("📊 BACKTEST HYBRID SONUÇLARI")
    print("="*70)
    
    print("\n📈 GENEL İSTATİSTİKLER:")
    print(f"   Toplam İşlem: {total_trades}")
    print(f"   Kazanan: {win_count} | Kaybeden: {loss_count}")
    print(f"   Kazanma Oranı: %{win_rate:.1f}")
    
    print("\n💰 KAR/ZARAR:")
    print(f"   Toplam Getiri: %{total_return:.2f}")
    print(f"   Ortalama İşlem: %{avg_trade:.2f}")
    
    print("\n📈 PERFORMANS:")
    print(f"   Profit Factor: {profit_factor:.2f}")
    print(f"   Max Drawdown: %{max_dd:.1f}")
    
    if BOOSTER_AVAILABLE and booster_used_count > 0:
        print(f"\n✨ WIN RATE BOOSTER:")
        print(f"   {booster_used_count} sinyalde aktif")
    
    print("\n🛡️ FİLTRE ETKİSİ:")
    print(f"   Market Filter Blocked: {market_filter_blocked} gün")
    print(f"   No Signal Days: {no_signal_days} gün")
    
    print("\n📊 SEKTÖR BAZLI ANALİZ:")
    for sector, stats in sorted(sector_stats.items(), key=lambda x: x[1]['total_pnl'], reverse=True):
        avg = stats['total_pnl'] / stats['count']
        print(f"   {sector}: {stats['count']} işlem, %{stats['total_pnl']:.1f} toplam, %{avg:.2f} ort.")
    
    print("\n📊 ÇIKIŞ NEDENİ ANALİZİ:")
    for reason, stats in sorted(exit_reasons.items(), key=lambda x: x[1]['total_pnl'], reverse=True):
        count = stats['count']
        pct = (count / total_trades * 100)
        avg = stats['total_pnl'] / count
        print(f"   {reason}: {count} işlem (%{pct:.1f}), %{stats['total_pnl']:.1f} toplam, %{avg:.2f} ort.")
    
    # Değerlendirme
    print("\n" + "="*70)
    print("🎯 STRATEJİ DEĞERLENDİRMESİ:")
    if win_rate >= 70 and profit_factor >= 3.0 and max_dd < 8:
        print("   ✅ MÜKEMMEL - Hedeflere ulaştı!")
    elif win_rate >= 65 and profit_factor >= 2.5 and max_dd < 10:
        print("   ✅ GÜÇLÜ - Canlı kullanıma uygun")
    elif win_rate >= 60 and profit_factor >= 2.0:
        print("   🟡 KABUL EDİLEBİLİR - Dikkatli kullanın")
    else:
        print("   ⚠️  GELİŞTİRİLMELİ - Daha fazla optimizasyon gerekli")
    print("="*70)
    
    # Son 10 işlem
    print("\n📝 SON 10 İŞLEM:")
    print("-" * 70)
    for t in trades[-10:]:
        emoji = "🟢" if t['pnl'] > 0 else "🔴"
        sector = STOCK_SECTORS.get(t['ticker'], 'Diğer')
        print(f"   {t['entry_date'].strftime('%Y-%m-%d')} | {t['ticker']} | {sector:12} | Skor:{t['score']} | {emoji} %{t['pnl']:+.2f} | {t['reason']}")
    
    return {
        'total_trades': total_trades,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'total_return': total_return,
        'max_dd': max_dd,
        'trades': trades
    }


if __name__ == "__main__":
    results = run_hybrid_backtest(days=90, max_picks=5)
