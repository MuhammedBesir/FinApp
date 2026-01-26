#!/usr/bin/env python3
"""
Gerçekçi Backtest - Daily-Picks Stratejisi
API'deki stratejiyle birebir aynı mantık
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# BIST30 Hisseler
BIST30 = [
    'THYAO.IS', 'GARAN.IS', 'AKBNK.IS', 'YKBNK.IS', 'EREGL.IS',
    'BIMAS.IS', 'ASELS.IS', 'KCHOL.IS', 'SAHOL.IS', 'SISE.IS',
    'TCELL.IS', 'TUPRS.IS', 'PGSUS.IS', 'TAVHL.IS', 'ENKAI.IS',
    'FROTO.IS', 'TOASO.IS', 'EKGYO.IS', 'GUBRF.IS', 'AKSEN.IS',
    'ARCLK.IS', 'PETKM.IS', 'TKFEN.IS', 'SASA.IS', 'KRDMD.IS',
    'ISCTR.IS', 'VAKBN.IS', 'ODAS.IS', 'HEKTS.IS'
]

def calc_ema(prices, period):
    """EMA hesapla - API ile aynı"""
    return prices.ewm(span=period, adjust=False).mean()

def calc_rsi(prices, period=14):
    """RSI hesapla"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-10)
    return 100 - (100 / (1 + rs))

def calc_atr(df, period=14):
    """ATR hesapla"""
    tr1 = df['High'] - df['Low']
    tr2 = abs(df['High'] - df['Close'].shift())
    tr3 = abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def generate_signal(df, idx):
    """
    Sinyal üret - API'deki daily-picks stratejisi ile BİREBİR AYNI
    
    Skor Kriterleri:
    1. EMA Trend (curr > ema9 > ema21) = +20
    2. Uzun Vadeli Trend (ema21 > ema50) = +15
    3. RSI Nötr (35-65) = +20
    4. Hacim > Ortalama = +15
    5. Pozisyon (%15-55) = +15
    6. Momentum (0-5%) = +10 (bonus)
    
    Min Score: 60
    """
    if idx < 50:
        return None
    
    close = df['Close'].iloc[:idx+1]
    high = df['High'].iloc[:idx+1]
    low = df['Low'].iloc[:idx+1]
    vol = df['Volume'].iloc[:idx+1]
    
    curr = close.iloc[-1]
    
    # EMA hesapla
    ema9 = calc_ema(close, 9).iloc[-1]
    ema21 = calc_ema(close, 21).iloc[-1]
    ema50 = calc_ema(close, 50).iloc[-1] if len(close) >= 50 else ema21
    
    # RSI
    rsi = calc_rsi(close).iloc[-1]
    
    # ATR
    atr = calc_atr(df.iloc[:idx+1]).iloc[-1]
    
    # Skor hesapla
    score = 0
    reasons = []
    
    # 1. EMA Trend (+20)
    if curr > ema9 > ema21:
        score += 20
        reasons.append("EMA trend (9>21)")
    
    # 2. Uzun Vadeli Trend (+15)
    if ema21 > ema50:
        score += 15
        reasons.append("Uzun trend (21>50)")
    
    # 3. RSI Nötr (+20)
    if 35 <= rsi <= 65:
        score += 20
        reasons.append(f"RSI nötr ({rsi:.0f})")
    
    # 4. Hacim (+15)
    vol_avg = vol.iloc[-20:].mean()
    if vol.iloc[-1] > vol_avg:
        score += 15
        reasons.append("Hacim↑")
    
    # 5. Pozisyon (+15)
    swing_low = low.iloc[-10:].min()
    swing_high = high.iloc[-10:].max()
    pos = (curr - swing_low) / (swing_high - swing_low + 1e-10)
    if 0.15 <= pos <= 0.55:
        score += 15
        reasons.append(f"Poz ({pos*100:.0f}%)")
    
    # 6. Momentum (+10 bonus)
    if len(close) >= 5:
        momentum = (close.iloc[-1] - close.iloc[-5]) / close.iloc[-5] * 100
        if 0 < momentum < 5:
            score += 10
            reasons.append(f"Mom +{momentum:.1f}%")
    
    # Min skor kontrolü
    if score < 60:
        return None
    
    # Stop ve TP hesapla
    stop = curr - (atr * 2.0)
    risk = curr - stop
    
    # Min risk kontrolü
    if risk / curr < 0.015:
        return None
    
    tp1 = curr + (risk * 2.5)
    tp2 = curr + (risk * 4.0)
    
    return {
        'entry': curr,
        'stop': stop,
        'tp1': tp1,
        'tp2': tp2,
        'score': score,
        'reasons': reasons,
        'atr': atr
    }

def run_backtest(days=90, max_daily_picks=5, max_holding=5):
    """Gerçekçi backtest - her gün top 5 seç"""
    
    print("=" * 70)
    print("🎯 GERÇEKÇİ BACKTEST - Daily-Picks Stratejisi")
    print("=" * 70)
    print(f"📅 Test: Son {days} gün")
    print(f"📊 Evren: {len(BIST30)} hisse (BIST30)")
    print(f"🎯 Günlük Max Öneri: {max_daily_picks}")
    print(f"⏱️  Max Holding: {max_holding} gün")
    print(f"🎯 Min Score: 60")
    print("=" * 70)
    
    # Veri indir
    print("\n📥 Veri indiriliyor...")
    end = datetime.now()
    start = end - timedelta(days=400)  # 400 gün veri (EMA50 için yeterli)
    
    all_data = {}
    for ticker in BIST30:
        try:
            df = yf.download(ticker, start=start, end=end, progress=False)
            if len(df) > 100:
                # MultiIndex column fix
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [col[0] for col in df.columns]
                all_data[ticker] = df.reset_index()
                print(f"  ✅ {ticker}: {len(df)} gün")
        except Exception as e:
            print(f"  ❌ {ticker}: {e}")
    
    print(f"\n✅ {len(all_data)} hisse yüklendi")
    
    if not all_data:
        print("❌ Veri yüklenemedi!")
        return
    
    # Backtest
    sample_df = list(all_data.values())[0]
    total_days = len(sample_df)
    start_idx = total_days - days
    
    print(f"\n🔄 Backtest başlıyor (Gün {start_idx} -> {total_days-1})...")
    
    trades = []
    active_positions = {}
    daily_recommendations = {}
    
    for day_idx in range(start_idx, total_days - 1):
        current_date = sample_df['Date'].iloc[day_idx].strftime("%Y-%m-%d")
        
        # 1. Mevcut pozisyonları kontrol et
        positions_to_close = []
        for ticker, pos in active_positions.items():
            if ticker not in all_data:
                continue
            
            df = all_data[ticker]
            if day_idx >= len(df):
                continue
            
            high = df['High'].iloc[day_idx]
            low = df['Low'].iloc[day_idx]
            close = df['Close'].iloc[day_idx]
            days_held = day_idx - pos['entry_idx']
            
            # Stop Loss check
            if low <= pos['stop']:
                pnl = ((pos['stop'] - pos['entry']) / pos['entry']) * 100
                trades.append({
                    'ticker': ticker,
                    'entry_date': pos['entry_date'],
                    'exit_date': current_date,
                    'entry': pos['entry'],
                    'exit': pos['stop'],
                    'pnl': pnl,
                    'result': 'STOP',
                    'days': days_held,
                    'score': pos['score']
                })
                positions_to_close.append(ticker)
            
            # TP1 check
            elif high >= pos['tp1']:
                pnl = ((pos['tp1'] - pos['entry']) / pos['entry']) * 100
                trades.append({
                    'ticker': ticker,
                    'entry_date': pos['entry_date'],
                    'exit_date': current_date,
                    'entry': pos['entry'],
                    'exit': pos['tp1'],
                    'pnl': pnl,
                    'result': 'TP1',
                    'days': days_held,
                    'score': pos['score']
                })
                positions_to_close.append(ticker)
            
            # Zaman çıkışı
            elif days_held >= max_holding:
                pnl = ((close - pos['entry']) / pos['entry']) * 100
                result = 'TIME_WIN' if pnl > 0 else 'TIME_LOSS'
                trades.append({
                    'ticker': ticker,
                    'entry_date': pos['entry_date'],
                    'exit_date': current_date,
                    'entry': pos['entry'],
                    'exit': close,
                    'pnl': pnl,
                    'result': result,
                    'days': days_held,
                    'score': pos['score']
                })
                positions_to_close.append(ticker)
        
        # Pozisyonları kapat
        for ticker in positions_to_close:
            del active_positions[ticker]
        
        # 2. Yeni sinyaller üret
        signals = []
        for ticker, df in all_data.items():
            if ticker in active_positions:
                continue
            if day_idx >= len(df):
                continue
            
            signal = generate_signal(df, day_idx)
            if signal:
                signals.append((ticker, signal))
        
        # Score'a göre sırala
        signals.sort(key=lambda x: x[1]['score'], reverse=True)
        
        # Top N seç (boş pozisyon kadar)
        available_slots = max_daily_picks - len(active_positions)
        top_signals = signals[:available_slots]
        
        if top_signals:
            daily_recommendations[current_date] = [
                f"{t}({s['score']})" for t, s in top_signals
            ]
        
        # Pozisyon aç
        for ticker, signal in top_signals:
            active_positions[ticker] = {
                'entry': signal['entry'],
                'stop': signal['stop'],
                'tp1': signal['tp1'],
                'tp2': signal['tp2'],
                'entry_idx': day_idx,
                'entry_date': current_date,
                'score': signal['score']
            }
    
    # Açık pozisyonları kapat (son gün)
    last_date = sample_df['Date'].iloc[-1].strftime("%Y-%m-%d")
    for ticker, pos in active_positions.items():
        if ticker in all_data:
            df = all_data[ticker]
            close = df['Close'].iloc[-1]
            pnl = ((close - pos['entry']) / pos['entry']) * 100
            days_held = total_days - 1 - pos['entry_idx']
            trades.append({
                'ticker': ticker,
                'entry_date': pos['entry_date'],
                'exit_date': last_date,
                'entry': pos['entry'],
                'exit': close,
                'pnl': pnl,
                'result': 'OPEN_WIN' if pnl > 0 else 'OPEN_LOSS',
                'days': days_held,
                'score': pos['score']
            })
    
    # Sonuçları hesapla
    print_results(trades, daily_recommendations)

def print_results(trades, daily_recommendations):
    """Sonuçları yazdır"""
    
    print("\n" + "=" * 70)
    print("📊 BACKTEST SONUÇLARI")
    print("=" * 70)
    
    if not trades:
        print("❌ Hiç trade bulunamadı!")
        return
    
    # İstatistikler
    total = len(trades)
    wins = [t for t in trades if t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] <= 0]
    win_rate = len(wins) / total * 100
    
    tp1_hits = len([t for t in trades if t['result'] == 'TP1'])
    stop_hits = len([t for t in trades if t['result'] == 'STOP'])
    time_wins = len([t for t in trades if t['result'] == 'TIME_WIN'])
    time_losses = len([t for t in trades if t['result'] == 'TIME_LOSS'])
    open_wins = len([t for t in trades if t['result'] == 'OPEN_WIN'])
    open_losses = len([t for t in trades if t['result'] == 'OPEN_LOSS'])
    
    total_pnl = sum(t['pnl'] for t in trades)
    avg_win = np.mean([t['pnl'] for t in wins]) if wins else 0
    avg_loss = np.mean([t['pnl'] for t in losses]) if losses else 0
    avg_days = np.mean([t['days'] for t in trades])
    
    gross_win = sum(t['pnl'] for t in wins) if wins else 0
    gross_loss = abs(sum(t['pnl'] for t in losses)) if losses else 0.01
    profit_factor = gross_win / gross_loss
    
    print(f"\n📈 GENEL İSTATİSTİKLER:")
    print(f"   Toplam Trade: {total}")
    print(f"   ✅ Kazançlı: {len(wins)} ({win_rate:.1f}%)")
    print(f"   ❌ Kayıplı: {len(losses)}")
    print(f"   📅 Günlük Öneri Sayısı: {len(daily_recommendations)}")
    
    print(f"\n🎯 ÇIKIŞ TİPLERİ:")
    print(f"   TP1 Hit: {tp1_hits} ({tp1_hits/total*100:.1f}%)")
    print(f"   Stop Hit: {stop_hits} ({stop_hits/total*100:.1f}%)")
    print(f"   Zaman Çıkış (Kâr): {time_wins}")
    print(f"   Zaman Çıkış (Zarar): {time_losses}")
    print(f"   Açık Pozisyon (Kâr): {open_wins}")
    print(f"   Açık Pozisyon (Zarar): {open_losses}")
    
    print(f"\n💰 PERFORMANS:")
    print(f"   Ort. Kazanç: +{avg_win:.2f}%")
    print(f"   Ort. Kayıp: {avg_loss:.2f}%")
    print(f"   Toplam PnL: {total_pnl:+.2f}%")
    print(f"   Profit Factor: {profit_factor:.2f}")
    print(f"   Ort. Holding: {avg_days:.1f} gün")
    
    # Hisse bazlı performans
    ticker_stats = {}
    for t in trades:
        ticker = t['ticker']
        if ticker not in ticker_stats:
            ticker_stats[ticker] = {'trades': 0, 'wins': 0, 'pnl': 0}
        ticker_stats[ticker]['trades'] += 1
        ticker_stats[ticker]['pnl'] += t['pnl']
        if t['pnl'] > 0:
            ticker_stats[ticker]['wins'] += 1
    
    print(f"\n📋 HİSSE BAZLI PERFORMANS:")
    sorted_tickers = sorted(ticker_stats.items(), key=lambda x: x[1]['pnl'], reverse=True)
    for ticker, stats in sorted_tickers[:10]:
        wr = stats['wins'] / stats['trades'] * 100
        emoji = "🟢" if stats['pnl'] > 0 else "🔴"
        print(f"   {emoji} {ticker}: {stats['trades']} trade, WR: {wr:.0f}%, PnL: {stats['pnl']:+.2f}%")
    
    # Son 5 günlük öneriler
    print(f"\n📅 ÖRNEK GÜNLÜK ÖNERİLER (Son 5 gün):")
    recent_days = list(daily_recommendations.items())[-5:]
    for date, picks in recent_days:
        print(f"   {date}: {', '.join(picks)}")
    
    # Özet değerlendirme
    print("\n" + "=" * 70)
    print("📌 ÖZET DEĞERLENDİRME:")
    
    if win_rate >= 55 and profit_factor >= 1.5:
        print("   ✅ Strateji İYİ, küçük iyileştirmeler yapılabilir")
    elif win_rate >= 50 and profit_factor >= 1.2:
        print("   ⚠️  Strateji KABUL EDİLEBİLİR ama geliştirilebilir")
    else:
        print("   ❌ Strateji zayıf, revize edilmeli")
    
    print(f"   Win Rate: {win_rate:.1f}% (Hedef: >55%)")
    print(f"   Profit Factor: {profit_factor:.2f} (Hedef: >1.5)")
    print(f"   Toplam Getiri: {total_pnl:+.2f}%")
    print("=" * 70)
    
    # Son trade'ler
    print("\n📝 SON 20 TRADE:")
    print("-" * 90)
    print(f"{'Tarih':<12} {'Hisse':<12} {'Giriş':>8} {'Çıkış':>8} {'PnL':>8} {'Sonuç':<12} {'Gün':>4} {'Skor':>4}")
    print("-" * 90)
    for t in trades[-20:]:
        print(f"{t['entry_date']:<12} {t['ticker']:<12} {t['entry']:>8.2f} {t['exit']:>8.2f} {t['pnl']:>+7.2f}% {t['result']:<12} {t['days']:>4} {t['score']:>4}")
    print("-" * 90)

if __name__ == "__main__":
    run_backtest(days=90, max_daily_picks=5, max_holding=5)
