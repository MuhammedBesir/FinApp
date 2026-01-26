#!/usr/bin/env python3
"""
İyileştirilmiş Strateji Backtest
Trailing Stop + Market Filter + Sektör Çeşitlendirmesi
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ========== SEKTÖR TANIMI ==========
SECTORS = {
    'BANKALAR': ['GARAN.IS', 'AKBNK.IS', 'YKBNK.IS', 'VAKBN.IS', 'ISCTR.IS'],
    'HOLDİNG': ['KCHOL.IS', 'SAHOL.IS'],
    'HAVACILIK': ['THYAO.IS', 'PGSUS.IS'],
    'SANAYİ': ['EREGL.IS', 'ASELS.IS', 'TOASO.IS', 'FROTO.IS', 'ARCLK.IS'],
    'ENERJİ': ['AKSEN.IS', 'TUPRS.IS', 'ENKAI.IS', 'PETKM.IS'],
    'DİĞER': ['BIMAS.IS', 'SISE.IS', 'TCELL.IS', 'TAVHL.IS', 'EKGYO.IS', 'GUBRF.IS', 'TKFEN.IS', 'KRDMD.IS', 'SASA.IS']
}

ALL_STOCKS = [s for stocks in SECTORS.values() for s in stocks]

# ========== AYARLAR ==========
TRAILING_STOP_ENABLED = True   # Trailing stop kullan
MARKET_FILTER_ENABLED = True   # XU030 trend filtresi
SECTOR_LIMIT = 2               # Her sektörden max hisse
MAX_HOLD_DAYS = 5
MIN_SCORE = 60
TP_MULT = 2.5                  # TP çarpanı
STOP_ATR_MULT = 2.0            # Stop ATR çarpanı

def get_sector(ticker):
    """Hissenin sektörünü bul"""
    for sector, stocks in SECTORS.items():
        if ticker in stocks:
            return sector
    return 'DİĞER'

def calc_ema(prices, period):
    if len(prices) < period:
        return prices[-1] if len(prices) > 0 else 0
    mult = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for p in prices[period:]:
        ema = (p * mult) + (ema * (1 - mult))
    return ema

def calc_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    gains, losses = [], []
    for i in range(1, period + 1):
        diff = prices[-i] - prices[-i-1]
        if diff > 0:
            gains.append(diff)
        else:
            losses.append(abs(diff))
    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 0.0001
    return 100 - (100 / (1 + (avg_gain / avg_loss)))

def calc_atr(df, idx, period=14):
    if idx < period:
        return float(df['Close'].iloc[idx]) * 0.025
    trs = []
    for i in range(idx - period, idx):
        hi = float(df['High'].iloc[i])
        lo = float(df['Low'].iloc[i])
        prev_cl = float(df['Close'].iloc[i-1]) if i > 0 else lo
        tr = max(hi - lo, abs(hi - prev_cl), abs(lo - prev_cl))
        trs.append(tr)
    return sum(trs) / len(trs) if trs else float(df['Close'].iloc[idx]) * 0.025

def generate_signal(df, idx):
    """Sinyal üret (min 60 puan gerekli)"""
    if idx < 50:
        return None
    
    closes = df['Close'].iloc[:idx+1].tolist()
    highs = df['High'].iloc[:idx+1].tolist()
    lows = df['Low'].iloc[:idx+1].tolist()
    volumes = df['Volume'].iloc[:idx+1].tolist()
    
    curr = closes[-1]
    ema9 = calc_ema(closes, 9)
    ema21 = calc_ema(closes, 21)
    ema50 = calc_ema(closes, 50)
    rsi = calc_rsi(closes)
    atr = calc_atr(df, idx)
    
    # Skor hesapla
    score = 0
    
    # EMA Trend (curr > ema9 > ema21)
    if curr > ema9 > ema21:
        score += 20
    
    # Uzun vadeli trend (ema21 > ema50)
    if ema21 > ema50:
        score += 15
    
    # RSI nötr bölge (35-65)
    if 35 <= rsi <= 65:
        score += 20
    
    # Hacim kontrolü
    vol_avg = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else volumes[-1]
    if volumes[-1] > vol_avg:
        score += 15
    
    # Pozisyon analizi
    swing_low = min(lows[-10:])
    swing_high = max(highs[-10:])
    pos = (curr - swing_low) / (swing_high - swing_low + 0.0001)
    if 0.15 <= pos <= 0.55:
        score += 15
    
    # Momentum (opsiyonel bonus)
    if len(closes) >= 5:
        momentum = (closes[-1] - closes[-5]) / closes[-5] * 100
        if 0 < momentum < 5:
            score += 10
    
    if score < MIN_SCORE:
        return None
    
    stop = curr - (atr * STOP_ATR_MULT)
    risk = curr - stop
    
    if risk / curr < 0.015:
        return None
    
    tp1 = curr + (risk * TP_MULT)
    
    return {
        'entry': curr,
        'stop': stop,
        'tp1': tp1,
        'atr': atr,
        'score': score
    }

def check_market_trend(xu030_data, idx):
    """XU030 trend kontrolü"""
    if not MARKET_FILTER_ENABLED or xu030_data is None or idx >= len(xu030_data):
        return 1.0  # Tam pozisyon
    
    closes = xu030_data['Close'].iloc[:idx+1].tolist()
    if len(closes) < 50:
        return 1.0
    
    curr = closes[-1]
    ema20 = calc_ema(closes, 20)
    ema50 = calc_ema(closes, 50)
    
    if curr > ema20:
        return 1.0      # Boğa trendi - Tam pozisyon
    elif curr > ema50:
        return 0.5      # Nötr - %50 pozisyon
    else:
        return 0.0      # Ayı trendi - Sinyal verme

def apply_trailing_stop(entry, current_high, atr, original_stop):
    """Trailing stop hesapla"""
    if not TRAILING_STOP_ENABLED:
        return original_stop
    
    pct_change = (current_high - entry) / entry * 100
    
    if pct_change >= 7:
        # +7% kar: Stop = Entry + %4
        return entry * 1.04
    elif pct_change >= 5:
        # +5% kar: Stop = Entry + %2
        return entry * 1.02
    elif pct_change >= 3:
        # +3% kar: Stop = Break-even
        return entry
    else:
        return original_stop

def run_backtest():
    print("="*70)
    print("🚀 İYİLEŞTİRİLMİŞ STRATEJİ BACKTEST")
    print("="*70)
    print(f"📅 Test: Son 90 gün")
    print(f"📊 Evren: {len(ALL_STOCKS)} hisse")
    print(f"🎯 Trailing Stop: {'AÇIK' if TRAILING_STOP_ENABLED else 'KAPALI'}")
    print(f"📈 Market Filter: {'AÇIK' if MARKET_FILTER_ENABLED else 'KAPALI'}")
    print(f"🏢 Sektör Limiti: {SECTOR_LIMIT} hisse/sektör")
    print("="*70)
    
    # Veri indir
    end = datetime.now()
    start = end - timedelta(days=400)
    
    print("📥 Veri indiriliyor...")
    
    all_data = {}
    for ticker in ALL_STOCKS:
        try:
            df = yf.download(ticker, start=start, end=end, progress=False)
            if len(df) > 100:
                df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
                df = df.reset_index()
                all_data[ticker] = df
                print(f"  ✅ {ticker}: {len(df)} gün")
        except Exception as e:
            pass
    
    # XU030 (BIST30 endeksi) indir
    xu030_data = None
    if MARKET_FILTER_ENABLED:
        try:
            xu030 = yf.download('XU030.IS', start=start, end=end, progress=False)
            if len(xu030) > 100:
                xu030.columns = [c[0] if isinstance(c, tuple) else c for c in xu030.columns]
                xu030_data = xu030.reset_index()
                print(f"  ✅ XU030.IS: {len(xu030_data)} gün (Market Filter)")
        except:
            print("  ⚠️ XU030 yüklenemedi, market filter devre dışı")
    
    print(f"✅ {len(all_data)} hisse yüklendi")
    
    if not all_data:
        print("❌ Veri yüklenemedi!")
        return
    
    # Backtest
    sample_df = list(all_data.values())[0]
    total_days = len(sample_df)
    start_day = total_days - 90
    
    print(f"🔄 Backtest: Gün {start_day} -> {total_days-1} (90 gün)")
    
    trades = []
    active_positions = {}
    daily_recommendations = {}
    skipped_by_market = 0
    skipped_by_sector = 0
    trailing_stop_triggers = 0
    
    for day in range(start_day, total_days):
        date = sample_df['Date'].iloc[day].strftime('%Y-%m-%d')
        
        # Market trend kontrolü
        market_weight = check_market_trend(xu030_data, day)
        if market_weight == 0:
            skipped_by_market += 1
        
        # Aktif pozisyonları kontrol et
        to_close = []
        for ticker, pos in active_positions.items():
            if ticker not in all_data:
                continue
            df = all_data[ticker]
            if day >= len(df):
                continue
            
            hi = df['High'].iloc[day]
            lo = df['Low'].iloc[day]
            cl = df['Close'].iloc[day]
            days_held = day - pos['entry_day']
            
            # Trailing stop güncelle
            if hi > pos.get('high_since_entry', pos['entry']):
                pos['high_since_entry'] = hi
                new_stop = apply_trailing_stop(pos['entry'], hi, pos['atr'], pos['original_stop'])
                if new_stop > pos['stop']:
                    if new_stop > pos['original_stop']:
                        pos['trailing_triggered'] = True
                    pos['stop'] = new_stop
            
            # Çıkış kontrolleri
            result = None
            exit_price = None
            
            if lo <= pos['stop']:
                exit_price = pos['stop']
                if pos.get('trailing_triggered'):
                    result = 'TRAIL_STOP'
                    trailing_stop_triggers += 1
                else:
                    result = 'STOP'
            elif hi >= pos['tp1']:
                exit_price = pos['tp1']
                result = 'TP1'
            elif days_held >= MAX_HOLD_DAYS:
                exit_price = cl
                result = 'TIME_WIN' if cl > pos['entry'] else 'TIME_LOSS'
            
            if result:
                pnl = ((exit_price - pos['entry']) / pos['entry']) * 100
                trades.append({
                    'entry_date': pos['entry_date'],
                    'exit_date': date,
                    'ticker': ticker,
                    'entry': pos['entry'],
                    'exit': exit_price,
                    'pnl': pnl,
                    'result': result,
                    'days': days_held,
                    'score': pos['score']
                })
                to_close.append(ticker)
        
        for ticker in to_close:
            del active_positions[ticker]
        
        # Yeni sinyal üret (market filter geçerse)
        if market_weight > 0:
            signals = []
            for ticker, df in all_data.items():
                if ticker in active_positions or day >= len(df):
                    continue
                sig = generate_signal(df, day)
                if sig:
                    signals.append((ticker, sig))
            
            # Score'a göre sırala
            signals.sort(key=lambda x: x[1]['score'], reverse=True)
            
            # Sektör kontrolü ile seç
            daily_picks = []
            sector_count = {}
            
            for ticker, sig in signals:
                if len(daily_picks) >= 5:
                    break
                
                sector = get_sector(ticker)
                current_count = sector_count.get(sector, 0)
                
                if current_count >= SECTOR_LIMIT:
                    skipped_by_sector += 1
                    continue
                
                daily_picks.append((ticker, sig))
                sector_count[sector] = current_count + 1
            
            # Pozisyon aç
            for ticker, sig in daily_picks:
                if ticker not in active_positions:
                    active_positions[ticker] = {
                        'entry': sig['entry'],
                        'stop': sig['stop'],
                        'original_stop': sig['stop'],
                        'tp1': sig['tp1'],
                        'atr': sig['atr'],
                        'score': sig['score'],
                        'entry_day': day,
                        'entry_date': date,
                        'high_since_entry': sig['entry'],
                        'trailing_triggered': False
                    }
            
            if daily_picks:
                daily_recommendations[date] = [(t, s['score']) for t, s in daily_picks]
    
    # Açık pozisyonları kapat
    for ticker, pos in active_positions.items():
        if ticker in all_data:
            df = all_data[ticker]
            cl = df['Close'].iloc[-1]
            pnl = ((cl - pos['entry']) / pos['entry']) * 100
            trades.append({
                'entry_date': pos['entry_date'],
                'exit_date': sample_df['Date'].iloc[-1].strftime('%Y-%m-%d'),
                'ticker': ticker,
                'entry': pos['entry'],
                'exit': cl,
                'pnl': pnl,
                'result': 'OPEN_WIN' if pnl > 0 else 'OPEN_LOSS',
                'days': total_days - 1 - pos['entry_day'],
                'score': pos['score']
            })
    
    # SONUÇLAR
    print("\n" + "="*70)
    print("📊 BACKTEST SONUÇLARI")
    print("="*70)
    
    if not trades:
        print("❌ Hiç trade bulunamadı!")
        return
    
    wins = [t for t in trades if t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] <= 0]
    
    win_rate = len(wins) / len(trades) * 100
    avg_win = np.mean([t['pnl'] for t in wins]) if wins else 0
    avg_loss = np.mean([t['pnl'] for t in losses]) if losses else 0
    total_pnl = sum(t['pnl'] for t in trades)
    
    gross_win = sum(t['pnl'] for t in wins)
    gross_loss = abs(sum(t['pnl'] for t in losses)) if losses else 0.01
    profit_factor = gross_win / gross_loss
    
    avg_days = np.mean([t['days'] for t in trades])
    
    print(f"📈 GENEL İSTATİSTİKLER:")
    print(f"   Toplam Trade: {len(trades)}")
    print(f"   ✅ Kazançlı: {len(wins)} ({win_rate:.1f}%)")
    print(f"   ❌ Kayıplı: {len(losses)}")
    print(f"   📅 Öneri Yapılan Gün: {len(daily_recommendations)}")
    
    # Çıkış tipleri
    exit_types = {}
    for t in trades:
        exit_types[t['result']] = exit_types.get(t['result'], 0) + 1
    
    print(f"\n🎯 ÇIKIŞ TİPLERİ:")
    for exit_type, count in sorted(exit_types.items(), key=lambda x: -x[1]):
        pct = count / len(trades) * 100
        print(f"   {exit_type}: {count} ({pct:.1f}%)")
    
    print(f"\n💰 PERFORMANS:")
    print(f"   Ort. Kazanç: +{avg_win:.2f}%")
    print(f"   Ort. Kayıp: {avg_loss:.2f}%")
    print(f"   Toplam PnL: {total_pnl:+.2f}%")
    print(f"   Profit Factor: {profit_factor:.2f}")
    print(f"   Ort. Holding: {avg_days:.1f} gün")
    
    print(f"\n🛡️ FİLTRE ETKİSİ:")
    print(f"   Market Filter ile atlanan gün: {skipped_by_market}")
    print(f"   Sektör limiti ile atlanan: {skipped_by_sector}")
    print(f"   Trailing Stop tetiklenen: {trailing_stop_triggers}")
    
    # Hisse bazlı
    ticker_perf = {}
    for t in trades:
        tk = t['ticker']
        if tk not in ticker_perf:
            ticker_perf[tk] = {'trades': 0, 'wins': 0, 'pnl': 0}
        ticker_perf[tk]['trades'] += 1
        if t['pnl'] > 0:
            ticker_perf[tk]['wins'] += 1
        ticker_perf[tk]['pnl'] += t['pnl']
    
    sorted_tickers = sorted(ticker_perf.items(), key=lambda x: x[1]['pnl'], reverse=True)
    
    print(f"\n📋 HİSSE BAZLI PERFORMANS (Top 10):")
    for ticker, perf in sorted_tickers[:10]:
        wr = perf['wins'] / perf['trades'] * 100
        emoji = "🟢" if perf['pnl'] > 0 else "🔴"
        print(f"   {emoji} {ticker}: {perf['trades']} trade, WR: {wr:.0f}%, PnL: {perf['pnl']:+.1f}%")
    
    # Son 5 gün öneriler
    print(f"\n📅 GÜNLÜK ÖNERİLER (Son 5 gün):")
    recent_dates = sorted(daily_recommendations.keys())[-5:]
    for date in recent_dates:
        picks = daily_recommendations[date]
        picks_str = ", ".join([f"{t.replace('.IS','')}({s})" for t, s in picks])
        print(f"   {date}: {picks_str}")
    
    # Değerlendirme
    print("\n" + "="*70)
    print("📌 ÖZET DEĞERLENDİRME:")
    
    if win_rate >= 60 and profit_factor >= 1.8:
        print("   ✅ Strateji MÜKEMMEL")
    elif win_rate >= 55 and profit_factor >= 1.5:
        print("   ✅ Strateji İYİ")
    else:
        print("   ⚠️ Strateji geliştirilebilir")
    
    print(f"   Win Rate: {win_rate:.1f}% (Hedef: >55%)")
    print(f"   Profit Factor: {profit_factor:.2f} (Hedef: >1.5)")
    print(f"   Toplam Getiri: {total_pnl:+.2f}%")
    print("="*70)

if __name__ == "__main__":
    run_backtest()
