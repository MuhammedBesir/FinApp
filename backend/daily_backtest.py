#!/usr/bin/env python3
"""
Daily-Picks Backtest - Her Gün 5 Yeni Öneri
Her gün top 5 hisse önerilir, aynı hissede aktif pozisyon yoksa alınır.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

BIST30 = [
    'THYAO.IS', 'GARAN.IS', 'AKBNK.IS', 'YKBNK.IS', 'EREGL.IS',
    'BIMAS.IS', 'ASELS.IS', 'KCHOL.IS', 'SAHOL.IS', 'SISE.IS',
    'TCELL.IS', 'TUPRS.IS', 'PGSUS.IS', 'TAVHL.IS', 'ENKAI.IS',
    'FROTO.IS', 'TOASO.IS', 'EKGYO.IS', 'GUBRF.IS', 'AKSEN.IS',
    'ARCLK.IS', 'PETKM.IS', 'TKFEN.IS', 'SASA.IS', 'KRDMD.IS',
    'ISCTR.IS', 'VAKBN.IS'
]

def calc_ema(p, n): return p.ewm(span=n, adjust=False).mean()

def calc_rsi(p, n=14):
    d = p.diff()
    g = (d.where(d > 0, 0)).rolling(n).mean()
    l = (-d.where(d < 0, 0)).rolling(n).mean()
    return 100 - (100 / (1 + g / (l + 1e-10)))

def calc_atr(df, n=14):
    tr = pd.concat([df['High'] - df['Low'],
                    abs(df['High'] - df['Close'].shift()),
                    abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def gen_signal(df, idx):
    if idx < 50: return None
    c = df['Close'].iloc[:idx+1]
    h = df['High'].iloc[:idx+1]
    l = df['Low'].iloc[:idx+1]
    v = df['Volume'].iloc[:idx+1]
    curr = c.iloc[-1]
    
    ema9, ema21, ema50 = calc_ema(c, 9).iloc[-1], calc_ema(c, 21).iloc[-1], calc_ema(c, 50).iloc[-1]
    rsi, atr = calc_rsi(c).iloc[-1], calc_atr(df.iloc[:idx+1]).iloc[-1]
    
    score = 0
    if curr > ema9 > ema21: score += 20
    if ema21 > ema50: score += 15
    if 35 <= rsi <= 65: score += 20
    if v.iloc[-1] > v.iloc[-20:].mean(): score += 15
    
    sw_l, sw_h = l.iloc[-10:].min(), h.iloc[-10:].max()
    pos = (curr - sw_l) / (sw_h - sw_l + 1e-10)
    if 0.15 <= pos <= 0.55: score += 15
    
    if len(c) >= 5:
        mom = (c.iloc[-1] - c.iloc[-5]) / c.iloc[-5] * 100
        if 0 < mom < 5: score += 10
    
    if score < 60: return None
    
    stop = curr - (atr * 2.0)
    risk = curr - stop
    if risk / curr < 0.015: return None
    
    return {'entry': curr, 'stop': stop, 'tp1': curr + (risk * 2.5), 'score': score}

print("=" * 70)
print("🎯 DAILY-PICKS BACKTEST - Her Gün 5 Yeni Öneri")
print("=" * 70)
print("📅 Test: Son 90 gün | 🎯 Günlük: 5 öneri | ⏱️ Holding: 5 gün")
print("=" * 70)

# Veri indir
print("\n📥 Veri indiriliyor...")
end = datetime.now()
start = end - timedelta(days=400)

all_data = {}
for ticker in BIST30:
    try:
        df = yf.download(ticker, start=start, end=end, progress=False)
        if len(df) > 100:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0] for c in df.columns]
            all_data[ticker] = df.reset_index()
            print(f"  ✅ {ticker}: {len(df)} gün")
    except Exception as e:
        print(f"  ❌ {ticker}")

print(f"\n✅ {len(all_data)} hisse yüklendi")

if len(all_data) < 10:
    print("❌ Yeterli veri yok!")
    exit()

sample = list(all_data.values())[0]
days = 90
start_idx = len(sample) - days

print(f"\n🔄 Backtest: Gün {start_idx} -> {len(sample)-1} ({days} gün)")

trades = []
active = {}
daily_log = {}

for idx in range(start_idx, len(sample) - 1):
    date = sample['Date'].iloc[idx].strftime("%Y-%m-%d")
    
    # 1. Çıkış kontrol
    to_close = []
    for tk, pos in active.items():
        if tk not in all_data or idx >= len(all_data[tk]): continue
        df = all_data[tk]
        hi, lo, cl = df['High'].iloc[idx], df['Low'].iloc[idx], df['Close'].iloc[idx]
        held = idx - pos['idx']
        
        exit_price, exit_type = None, None
        
        if lo <= pos['stop']:
            exit_price, exit_type = pos['stop'], 'STOP'
        elif hi >= pos['tp']:
            exit_price, exit_type = pos['tp'], 'TP1'
        elif held >= 5:
            exit_price = cl
            exit_type = 'TIME_WIN' if cl > pos['entry'] else 'TIME_LOSS'
        
        if exit_price:
            pnl = ((exit_price - pos['entry']) / pos['entry']) * 100
            trades.append({
                'ticker': tk, 'entry_date': pos['entry_date'], 'exit_date': date,
                'entry': pos['entry'], 'exit': exit_price, 'pnl': pnl,
                'result': exit_type, 'days': held, 'score': pos['score']
            })
            to_close.append(tk)
    
    for tk in to_close: del active[tk]
    
    # 2. Günün TÜM sinyalleri
    signals = []
    for tk, df in all_data.items():
        if idx >= len(df): continue
        sig = gen_signal(df, idx)
        if sig: signals.append((tk, sig))
    
    signals.sort(key=lambda x: x[1]['score'], reverse=True)
    
    # 3. Top 5 seç (günün önerileri)
    top5 = signals[:5]
    if top5:
        daily_log[date] = [f"{t}({s['score']})" for t, s in top5]
    
    # 4. Pozisyon aç (aynı hissede yoksa)
    for tk, sig in top5:
        if tk not in active:
            active[tk] = {
                'entry': sig['entry'], 'stop': sig['stop'], 'tp': sig['tp1'],
                'idx': idx, 'entry_date': date, 'score': sig['score']
            }

# Açık pozisyonları kapat
last_date = sample['Date'].iloc[-1].strftime("%Y-%m-%d")
for tk, pos in active.items():
    if tk in all_data:
        cl = all_data[tk]['Close'].iloc[-1]
        pnl = ((cl - pos['entry']) / pos['entry']) * 100
        trades.append({
            'ticker': tk, 'entry_date': pos['entry_date'], 'exit_date': last_date,
            'entry': pos['entry'], 'exit': cl, 'pnl': pnl,
            'result': 'OPEN_WIN' if pnl > 0 else 'OPEN_LOSS',
            'days': len(sample) - 1 - pos['idx'], 'score': pos['score']
        })

# SONUÇLAR
print("\n" + "=" * 70)
print("📊 BACKTEST SONUÇLARI")
print("=" * 70)

if not trades:
    print("❌ Hiç trade yok!")
    exit()

wins = [t for t in trades if t['pnl'] > 0]
losses = [t for t in trades if t['pnl'] <= 0]
wr = len(wins) / len(trades) * 100
pnl = sum(t['pnl'] for t in trades)
gw = sum(t['pnl'] for t in wins) if wins else 0
gl = abs(sum(t['pnl'] for t in losses)) if losses else 0.01
pf = gw / gl

print(f"\n📈 GENEL İSTATİSTİKLER:")
print(f"   Toplam Trade: {len(trades)}")
print(f"   ✅ Kazançlı: {len(wins)} ({wr:.1f}%)")
print(f"   ❌ Kayıplı: {len(losses)}")
print(f"   📅 Öneri Yapılan Gün: {len(daily_log)}")

print(f"\n🎯 ÇIKIŞ TİPLERİ:")
for r in ['TP1', 'STOP', 'TIME_WIN', 'TIME_LOSS', 'OPEN_WIN', 'OPEN_LOSS']:
    cnt = len([t for t in trades if t['result'] == r])
    if cnt: print(f"   {r}: {cnt} ({cnt/len(trades)*100:.1f}%)")

print(f"\n💰 PERFORMANS:")
print(f"   Ort. Kazanç: +{np.mean([t['pnl'] for t in wins]):.2f}%" if wins else "")
print(f"   Ort. Kayıp: {np.mean([t['pnl'] for t in losses]):.2f}%" if losses else "")
print(f"   Toplam PnL: {pnl:+.2f}%")
print(f"   Profit Factor: {pf:.2f}")
print(f"   Ort. Holding: {np.mean([t['days'] for t in trades]):.1f} gün")

# Hisse bazlı
print(f"\n📋 HİSSE BAZLI PERFORMANS (Top 12):")
stats = {}
for t in trades:
    tk = t['ticker']
    if tk not in stats: stats[tk] = {'n': 0, 'w': 0, 'p': 0}
    stats[tk]['n'] += 1
    stats[tk]['p'] += t['pnl']
    if t['pnl'] > 0: stats[tk]['w'] += 1

for tk, s in sorted(stats.items(), key=lambda x: x[1]['p'], reverse=True)[:12]:
    emoji = "🟢" if s['p'] > 0 else "🔴"
    print(f"   {emoji} {tk}: {s['n']} trade, WR: {s['w']/s['n']*100:.0f}%, PnL: {s['p']:+.1f}%")

# Son 10 gün
print(f"\n📅 GÜNLÜK ÖNERİLER (Son 10 gün):")
for dt, picks in list(daily_log.items())[-10:]:
    print(f"   {dt}: {', '.join(picks)}")

# Özet
print("\n" + "=" * 70)
print("📌 ÖZET DEĞERLENDİRME:")
if wr >= 55 and pf >= 1.5:
    print("   ✅ Strateji İYİ")
elif wr >= 50 and pf >= 1.2:
    print("   ⚠️  Strateji KABUL EDİLEBİLİR")
else:
    print("   ❌ Strateji zayıf")
print(f"   Win Rate: {wr:.1f}% (Hedef: >55%)")
print(f"   Profit Factor: {pf:.2f} (Hedef: >1.5)")
print(f"   Toplam Getiri: {pnl:+.2f}%")
print("=" * 70)

# Tüm trade'ler
print(f"\n📝 TÜM TRADE'LER ({len(trades)} adet):")
print("-" * 100)
print(f"{'Giriş':<12} {'Çıkış':<12} {'Hisse':<12} {'Giriş':>8} {'Çıkış':>8} {'PnL':>8} {'Sonuç':<12} {'Gün':>3} {'Skor':>4}")
print("-" * 100)
for t in trades:
    print(f"{t['entry_date']:<12} {t['exit_date']:<12} {t['ticker']:<12} {t['entry']:>8.2f} {t['exit']:>8.2f} {t['pnl']:>+7.2f}% {t['result']:<12} {t['days']:>3} {t['score']:>4}")
print("-" * 100)
