#!/usr/bin/env python3
"""
İyileştirilmiş Strateji Backtest v2
Trailing Stop + Market Filter + Sektör Çeşitlendirmesi
"""

import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ========== SEKTÖR TANIMI ==========
SECTORS = {
    'BANKALAR': ['GARAN.IS', 'AKBNK.IS', 'YKBNK.IS', 'VAKBN.IS', 'ISCTR.IS'],
    'HOLDİNG': ['KCHOL.IS', 'SAHOL.IS'],
    'SANAYİ': ['EREGL.IS', 'ASELS.IS', 'TOASO.IS', 'FROTO.IS'],
    'ENERJİ': ['AKSEN.IS', 'TUPRS.IS', 'ENKAI.IS'],
    'DİĞER': ['BIMAS.IS', 'SISE.IS', 'TCELL.IS', 'TAVHL.IS', 'EKGYO.IS', 'GUBRF.IS', 'THYAO.IS']
}

ALL_STOCKS = [s for stocks in SECTORS.values() for s in stocks]

# ========== AYARLAR ==========
TRAILING_STOP = True      # Trailing stop kullan
MARKET_FILTER = True      # XU030 trend filtresi
SECTOR_LIMIT = 2          # Her sektörden max hisse

def get_sector(ticker):
    for sector, stocks in SECTORS.items():
        if ticker in stocks:
            return sector
    return 'DİĞER'

def ema(prices, period):
    if len(prices) < period:
        return prices[-1] if prices else 0
    mult = 2 / (period + 1)
    result = sum(prices[:period]) / period
    for p in prices[period:]:
        result = (p * mult) + (result * (1 - mult))
    return result

def rsi(prices, period=14):
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

def run_backtest():
    print("="*70)
    print("🚀 İYİLEŞTİRİLMİŞ STRATEJİ BACKTEST")
    print("="*70)
    print(f"🎯 Trailing Stop: {'AÇIK' if TRAILING_STOP else 'KAPALI'}")
    print(f"📈 Market Filter: {'AÇIK' if MARKET_FILTER else 'KAPALI'}")
    print(f"🏢 Sektör Limiti: {SECTOR_LIMIT}/sektör")
    print("="*70)
    
    # Veri indir - toplu
    end = datetime.now()
    start = end - timedelta(days=400)
    
    print("📥 Veri indiriliyor...")
    
    # Tüm hisseleri + XU030'u toplu indir
    tickers = ALL_STOCKS + ['XU030.IS']
    raw = yf.download(tickers, start=start, end=end, progress=False, threads=True)
    
    if raw.empty:
        print("❌ Veri indirilemedi!")
        return
    
    # DataFrame'i düzenle
    all_data = {}
    xu030_closes = None
    
    for ticker in tickers:
        try:
            closes = raw['Close'][ticker].dropna().tolist()
            highs = raw['High'][ticker].dropna().tolist()
            lows = raw['Low'][ticker].dropna().tolist()
            volumes = raw['Volume'][ticker].dropna().tolist()
            
            if len(closes) > 100:
                all_data[ticker] = {
                    'closes': closes,
                    'highs': highs,
                    'lows': lows,
                    'volumes': volumes
                }
                if ticker == 'XU030.IS':
                    xu030_closes = closes
                else:
                    print(f"  ✅ {ticker}: {len(closes)} gün")
        except:
            pass
    
    if 'XU030.IS' in all_data:
        del all_data['XU030.IS']
        print(f"  ✅ XU030.IS: {len(xu030_closes)} gün (Market Filter)")
    
    print(f"✅ {len(all_data)} hisse yüklendi")
    
    if not all_data:
        print("❌ Yeterli veri yok!")
        return
    
    # Backtest
    sample_len = len(list(all_data.values())[0]['closes'])
    start_day = sample_len - 90
    
    print(f"🔄 Backtest: {start_day} -> {sample_len-1} (90 gün)")
    
    trades = []
    active = {}  # ticker -> {entry, stop, tp1, entry_day, score, high_since}
    daily_recs = {}
    market_skips = 0
    sector_skips = 0
    trail_triggers = 0
    
    for day in range(start_day, sample_len):
        # Market filter
        market_ok = True
        if MARKET_FILTER and xu030_closes and day < len(xu030_closes):
            xu_closes = xu030_closes[:day+1]
            if len(xu_closes) >= 50:
                xu_curr = xu_closes[-1]
                xu_ema20 = ema(xu_closes, 20)
                xu_ema50 = ema(xu_closes, 50)
                if xu_curr < xu_ema50:
                    market_ok = False
                    market_skips += 1
        
        # Pozisyonları kontrol et
        to_close = []
        for ticker, pos in active.items():
            data = all_data.get(ticker)
            if not data or day >= len(data['closes']):
                continue
            
            hi = data['highs'][day]
            lo = data['lows'][day]
            cl = data['closes'][day]
            days_held = day - pos['entry_day']
            
            # Trailing stop güncelle
            if hi > pos['high_since']:
                pos['high_since'] = hi
                if TRAILING_STOP:
                    pct_up = (hi - pos['entry']) / pos['entry'] * 100
                    if pct_up >= 7:
                        new_stop = pos['entry'] * 1.04
                    elif pct_up >= 5:
                        new_stop = pos['entry'] * 1.02
                    elif pct_up >= 3:
                        new_stop = pos['entry']
                    else:
                        new_stop = pos['stop']
                    
                    if new_stop > pos['stop']:
                        if new_stop > pos['original_stop']:
                            pos['trail_active'] = True
                        pos['stop'] = new_stop
            
            # Çıkış kontrol
            result = None
            exit_price = None
            
            if lo <= pos['stop']:
                exit_price = pos['stop']
                if pos.get('trail_active'):
                    result = 'TRAIL'
                    trail_triggers += 1
                else:
                    result = 'STOP'
            elif hi >= pos['tp1']:
                exit_price = pos['tp1']
                result = 'TP1'
            elif days_held >= 5:
                exit_price = cl
                result = 'TIME_WIN' if cl > pos['entry'] else 'TIME_LOSS'
            
            if result:
                pnl = ((exit_price - pos['entry']) / pos['entry']) * 100
                trades.append({
                    'ticker': ticker,
                    'pnl': pnl,
                    'result': result,
                    'days': days_held,
                    'score': pos['score']
                })
                to_close.append(ticker)
        
        for t in to_close:
            del active[t]
        
        # Yeni sinyal (market filter geçerse)
        if not market_ok:
            continue
        
        signals = []
        for ticker, data in all_data.items():
            if ticker in active or day >= len(data['closes']):
                continue
            
            if day < 50:
                continue
            
            closes = data['closes'][:day+1]
            highs = data['highs'][:day+1]
            lows = data['lows'][:day+1]
            volumes = data['volumes'][:day+1]
            
            curr = closes[-1]
            ema9 = ema(closes, 9)
            ema21 = ema(closes, 21)
            ema50 = ema(closes, 50)
            rsi_val = rsi(closes)
            
            # Skor hesapla
            score = 0
            if curr > ema9 > ema21:
                score += 20
            if ema21 > ema50:
                score += 15
            if 35 <= rsi_val <= 65:
                score += 20
            
            vol_avg = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else volumes[-1]
            if volumes[-1] > vol_avg:
                score += 15
            
            if len(lows) >= 10 and len(highs) >= 10:
                swing_lo = min(lows[-10:])
                swing_hi = max(highs[-10:])
                pos_pct = (curr - swing_lo) / (swing_hi - swing_lo + 0.0001)
                if 0.15 <= pos_pct <= 0.55:
                    score += 15
            
            if len(closes) >= 5:
                mom = (closes[-1] - closes[-5]) / closes[-5] * 100
                if 0 < mom < 5:
                    score += 10
            
            if score >= 60:
                # ATR hesapla
                atr = curr * 0.025
                if len(closes) >= 14:
                    trs = []
                    for i in range(-14, 0):
                        tr = max(highs[i] - lows[i], 
                                abs(highs[i] - closes[i-1]),
                                abs(lows[i] - closes[i-1]))
                        trs.append(tr)
                    atr = sum(trs) / len(trs)
                
                stop = curr - (atr * 2.0)
                risk = curr - stop
                
                if risk / curr >= 0.015:
                    tp1 = curr + (risk * 2.5)
                    signals.append((ticker, score, curr, stop, tp1))
        
        # Score'a göre sırala
        signals.sort(key=lambda x: x[1], reverse=True)
        
        # Sektör limiti ile seç
        picks = []
        sector_count = {}
        
        for ticker, score, entry, stop, tp1 in signals:
            if len(picks) >= 5:
                break
            
            sector = get_sector(ticker)
            if sector_count.get(sector, 0) >= SECTOR_LIMIT:
                sector_skips += 1
                continue
            
            picks.append((ticker, score, entry, stop, tp1))
            sector_count[sector] = sector_count.get(sector, 0) + 1
        
        # Pozisyon aç
        for ticker, score, entry, stop, tp1 in picks:
            if ticker not in active:
                active[ticker] = {
                    'entry': entry,
                    'stop': stop,
                    'original_stop': stop,
                    'tp1': tp1,
                    'entry_day': day,
                    'score': score,
                    'high_since': entry,
                    'trail_active': False
                }
        
        if picks:
            daily_recs[day] = [(t, s) for t, s, _, _, _ in picks]
    
    # Açık pozisyonları kapat
    for ticker, pos in active.items():
        data = all_data.get(ticker)
        if data:
            cl = data['closes'][-1]
            pnl = ((cl - pos['entry']) / pos['entry']) * 100
            trades.append({
                'ticker': ticker,
                'pnl': pnl,
                'result': 'OPEN_WIN' if pnl > 0 else 'OPEN_LOSS',
                'days': sample_len - 1 - pos['entry_day'],
                'score': pos['score']
            })
    
    # SONUÇLAR
    print("\n" + "="*70)
    print("📊 BACKTEST SONUÇLARI")
    print("="*70)
    
    if not trades:
        print("❌ Hiç trade yok!")
        return
    
    wins = [t for t in trades if t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] <= 0]
    
    wr = len(wins) / len(trades) * 100
    avg_win = np.mean([t['pnl'] for t in wins]) if wins else 0
    avg_loss = np.mean([t['pnl'] for t in losses]) if losses else 0
    total_pnl = sum(t['pnl'] for t in trades)
    
    gross_win = sum(t['pnl'] for t in wins)
    gross_loss = abs(sum(t['pnl'] for t in losses)) if losses else 0.01
    pf = gross_win / gross_loss
    
    print(f"📈 GENEL İSTATİSTİKLER:")
    print(f"   Toplam Trade: {len(trades)}")
    print(f"   ✅ Kazançlı: {len(wins)} ({wr:.1f}%)")
    print(f"   ❌ Kayıplı: {len(losses)}")
    
    exit_types = {}
    for t in trades:
        exit_types[t['result']] = exit_types.get(t['result'], 0) + 1
    
    print(f"\n🎯 ÇIKIŞ TİPLERİ:")
    for et, cnt in sorted(exit_types.items(), key=lambda x: -x[1]):
        print(f"   {et}: {cnt} ({cnt/len(trades)*100:.1f}%)")
    
    print(f"\n💰 PERFORMANS:")
    print(f"   Ort. Kazanç: +{avg_win:.2f}%")
    print(f"   Ort. Kayıp: {avg_loss:.2f}%")
    print(f"   Toplam PnL: {total_pnl:+.2f}%")
    print(f"   Profit Factor: {pf:.2f}")
    
    print(f"\n🛡️ FİLTRE ETKİSİ:")
    print(f"   Market Filter atlanan: {market_skips} gün")
    print(f"   Sektör limiti atlanan: {sector_skips}")
    print(f"   Trailing Stop tetiklenen: {trail_triggers}")
    
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
    
    print(f"\n📋 HİSSE BAZLI (Top 10):")
    for ticker, perf in sorted_tickers[:10]:
        wr_t = perf['wins'] / perf['trades'] * 100
        emoji = "🟢" if perf['pnl'] > 0 else "🔴"
        print(f"   {emoji} {ticker}: {perf['trades']} trade, WR: {wr_t:.0f}%, PnL: {perf['pnl']:+.1f}%")
    
    print("\n" + "="*70)
    print("📌 ÖZET DEĞERLENDİRME:")
    
    if wr >= 60 and pf >= 1.8:
        print("   ✅ Strateji MÜKEMMEL")
    elif wr >= 55 and pf >= 1.5:
        print("   ✅ Strateji İYİ")
    else:
        print("   ⚠️ Strateji geliştirilebilir")
    
    print(f"   Win Rate: {wr:.1f}%")
    print(f"   Profit Factor: {pf:.2f}")
    print(f"   Toplam Getiri: {total_pnl:+.2f}%")
    print("="*70)

if __name__ == "__main__":
    run_backtest()
