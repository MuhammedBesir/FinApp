#!/usr/bin/env python3
"""
BACKTEST v3.0 SIMPLE - ATR-BAZLI ADAPTİF STRATEJİ (TEK TEST)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

# Sadece 10 likit hisse (hızlı test için)
TICKERS = [
    "THYAO.IS", "GARAN.IS", "AKBNK.IS", "ISCTR.IS", "BIMAS.IS",
    "FROTO.IS", "KCHOL.IS", "EREGL.IS", "SAHOL.IS", "TOASO.IS"
]

STOCK_SECTORS = {
    "AKBNK.IS": "Bankacılık", "BIMAS.IS": "Perakende", "EREGL.IS": "Demir Çelik",
    "FROTO.IS": "Otomotiv", "GARAN.IS": "Bankacılık", "ISCTR.IS": "Bankacılık",
    "KCHOL.IS": "Holding", "SAHOL.IS": "Holding", "THYAO.IS": "Havacılık",
    "TOASO.IS": "Otomotiv",
}

SECTOR_VOL = {
    "Havacılık": {"sl_mult": 2.0, "tp_mult": 4.0, "max_hold": 7},
    "Bankacılık": {"sl_mult": 1.5, "tp_mult": 3.0, "max_hold": 10},
    "Holding": {"sl_mult": 1.4, "tp_mult": 2.8, "max_hold": 12},
    "Perakende": {"sl_mult": 1.3, "tp_mult": 2.6, "max_hold": 12},
    "Otomotiv": {"sl_mult": 1.6, "tp_mult": 3.2, "max_hold": 10},
    "Demir Çelik": {"sl_mult": 1.7, "tp_mult": 3.5, "max_hold": 8},
    "default": {"sl_mult": 1.5, "tp_mult": 3.0, "max_hold": 10},
}

def calc_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def calc_indicators(df):
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['ATR'] = calc_atr(df)
    df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
    df['Vol_Ratio'] = df['Volume'] / df['Vol_MA20']
    return df

def calc_score(row):
    score = 0
    price, ema20, ema50 = row['Close'], row['EMA20'], row['EMA50']
    rsi, vol_ratio = row['RSI'], row['Vol_Ratio']
    
    if price > ema20 and ema20 > ema50: score += 30
    elif price > ema50 and ema20 > ema50: score += 20
    elif ema20 > ema50: score += 10
    
    if 40 <= rsi <= 60: score += 15
    elif 30 <= rsi < 40: score += 10
    elif 60 < rsi <= 70: score += 5
    
    dist = abs(price - ema20) / price
    if dist < 0.015: score += 25
    elif dist < 0.03: score += 15
    else: score += 5
    
    if vol_ratio > 1.5: score += 20
    elif vol_ratio > 1.0: score += 10
    
    return score

def get_atr_levels(ticker, row):
    sector = STOCK_SECTORS.get(ticker, "default")
    profile = SECTOR_VOL.get(sector, SECTOR_VOL["default"])
    
    price = row['Close']
    atr = row['ATR'] if not pd.isna(row['ATR']) else price * 0.02
    
    sl_dist = max(atr * profile['sl_mult'], price * 0.015)
    sl_dist = min(sl_dist, price * 0.05)
    stop_loss = price - sl_dist
    
    tp_dist = max(atr * profile['tp_mult'], sl_dist * 2)
    take_profit = price + tp_dist
    
    return {
        'entry': price, 'stop_loss': stop_loss, 'take_profit': take_profit,
        'sl_pct': (sl_dist / price) * 100, 'tp_pct': (tp_dist / price) * 100,
        'atr_pct': (atr / price) * 100, 'max_hold': profile['max_hold'], 'sector': sector
    }

def run_test(days=90, min_score=70, max_picks=3):
    print("=" * 60)
    print(f"🚀 ATR-BAZLI TEST | {days} gün | Score {min_score}+ | Max {max_picks}")
    print("=" * 60)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days + 80)
    
    print(f"📥 Veri çekiliyor...")
    stock_data = {}
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if len(df) >= 50:
                stock_data[ticker] = calc_indicators(df)
        except: pass
    print(f"✅ {len(stock_data)} hisse yüklendi")
    
    # Ortak tarihler
    common = None
    for df in stock_data.values():
        dates = set(df.index)
        common = dates if common is None else common.intersection(dates)
    common = sorted(list(common))[-days:]
    
    trades = []
    open_pos = []
    sector_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'total': 0})
    
    for date in common:
        # Açık pozisyonları kontrol et
        for pos in open_pos[:]:
            ticker = pos['ticker']
            if ticker in stock_data and date in stock_data[ticker].index:
                row = stock_data[ticker].loc[date]
                pos['days_held'] = pos.get('days_held', 0) + 1
                
                ret_pct = ((row['Close'] - pos['entry']) / pos['entry']) * 100
                
                # Exit kontrolü
                closed = False
                if row['Low'] <= pos['stop_loss']:
                    pos['exit'] = pos['stop_loss']
                    pos['ret'] = ((pos['stop_loss'] - pos['entry']) / pos['entry']) * 100
                    pos['reason'] = 'STOP_LOSS'
                    closed = True
                elif row['High'] >= pos['take_profit']:
                    pos['exit'] = pos['take_profit']
                    pos['ret'] = ((pos['take_profit'] - pos['entry']) / pos['entry']) * 100
                    pos['reason'] = 'TAKE_PROFIT'
                    closed = True
                elif pos['days_held'] >= pos['max_hold']:
                    pos['exit'] = row['Close']
                    pos['ret'] = ret_pct
                    pos['reason'] = 'MAX_DAYS'
                    closed = True
                elif ret_pct >= 4:  # Trailing stop
                    pos['stop_loss'] = max(pos['stop_loss'], row['Close'] * 0.98)
                
                if closed:
                    pos['exit_date'] = date
                    trades.append(pos)
                    open_pos.remove(pos)
                    sector_stats[pos['sector']]['trades'] += 1
                    sector_stats[pos['sector']]['total'] += pos['ret']
                    if pos['ret'] > 0:
                        sector_stats[pos['sector']]['wins'] += 1
        
        # Yeni sinyal ara
        used_sectors = {p['sector'] for p in open_pos}
        signals = []
        
        for ticker, df in stock_data.items():
            if date not in df.index: continue
            sector = STOCK_SECTORS.get(ticker, 'default')
            if sector in used_sectors: continue
            if any(p['ticker'] == ticker for p in open_pos): continue
            
            row = df.loc[date]
            if pd.isna(row['RSI']) or pd.isna(row['ATR']): continue
            
            score = calc_score(row)
            if score >= min_score:
                levels = get_atr_levels(ticker, row)
                signals.append({'ticker': ticker, 'score': score, **levels})
        
        signals.sort(key=lambda x: x['score'], reverse=True)
        
        for sig in signals[:max_picks]:
            if sig['sector'] not in used_sectors:
                open_pos.append({
                    'ticker': sig['ticker'], 'entry_date': date, 'entry': sig['entry'],
                    'stop_loss': sig['stop_loss'], 'take_profit': sig['take_profit'],
                    'sl_pct': sig['sl_pct'], 'tp_pct': sig['tp_pct'],
                    'atr_pct': sig['atr_pct'], 'max_hold': sig['max_hold'],
                    'sector': sig['sector'], 'score': sig['score'], 'days_held': 0
                })
                used_sectors.add(sig['sector'])
    
    # Açık pozisyonları kapat
    for pos in open_pos:
        ticker = pos['ticker']
        if ticker in stock_data:
            last_row = stock_data[ticker].iloc[-1]
            pos['exit'] = last_row['Close']
            pos['ret'] = ((pos['exit'] - pos['entry']) / pos['entry']) * 100
            pos['reason'] = 'OPEN'
            pos['exit_date'] = common[-1]
            trades.append(pos)
            sector_stats[pos['sector']]['trades'] += 1
            sector_stats[pos['sector']]['total'] += pos['ret']
            if pos['ret'] > 0:
                sector_stats[pos['sector']]['wins'] += 1
    
    # Sonuçlar
    if not trades:
        print("❌ İşlem yok!")
        return None
    
    total = len(trades)
    winners = [t for t in trades if t['ret'] > 0]
    losers = [t for t in trades if t['ret'] <= 0]
    
    win_rate = len(winners) / total * 100
    total_ret = sum(t['ret'] for t in trades)
    avg_ret = total_ret / total
    
    avg_win = sum(t['ret'] for t in winners) / len(winners) if winners else 0
    avg_loss = sum(t['ret'] for t in losers) / len(losers) if losers else 0
    
    gross_profit = sum(t['ret'] for t in winners) if winners else 0
    gross_loss = abs(sum(t['ret'] for t in losers)) if losers else 1
    pf = gross_profit / gross_loss if gross_loss > 0 else 0
    
    print("=" * 60)
    print("📊 SONUÇLAR:")
    print(f"   İşlem: {total} | Kazanan: {len(winners)} | Kaybeden: {len(losers)}")
    print(f"   Win Rate: %{win_rate:.1f}")
    print(f"   Toplam: %{total_ret:.2f} | Ortalama: %{avg_ret:.2f}")
    print(f"   Ort.Kazanç: %{avg_win:.2f} | Ort.Kayıp: %{avg_loss:.2f}")
    print(f"   Profit Factor: {pf:.2f}")
    
    # Çıkış nedeni
    reasons = defaultdict(list)
    for t in trades:
        reasons[t['reason']].append(t['ret'])
    
    print("\n📈 ÇIKIŞ NEDENİ:")
    for reason, rets in reasons.items():
        print(f"   {reason}: {len(rets)} işlem, %{sum(rets):.1f} toplam, %{sum(rets)/len(rets):.2f} ort.")
    
    # Sektör analizi
    print("\n📊 SEKTÖR BAZLI:")
    for sector, s in sorted(sector_stats.items(), key=lambda x: x[1]['total'], reverse=True):
        if s['trades'] > 0:
            wr = s['wins'] / s['trades'] * 100
            avg = s['total'] / s['trades']
            print(f"   {sector:15} | {s['trades']:2} işlem | WR:%{wr:5.1f} | Tot:%{s['total']:+6.1f} | Avg:%{avg:+5.2f}")
    
    # Son işlemler
    print("\n📝 SON İŞLEMLER (ATR-bazlı):")
    for t in trades[-8:]:
        sym = "🟢" if t['ret'] > 0 else "🔴"
        print(f"   {t['ticker']:10} | {t['sector']:10} | SL:{t['sl_pct']:4.1f}% | TP:{t['tp_pct']:4.1f}% | {sym} %{t['ret']:+5.2f} | {t['reason']}")
    
    print("=" * 60)
    
    if pf >= 1.5 and win_rate >= 50:
        print("✅ GÜÇLÜ STRATEJİ")
    elif pf >= 1.2 and win_rate >= 45:
        print("🟡 KABUL EDİLEBİLİR")
    else:
        print("🔴 GELİŞTİRME GEREKLİ")
    
    return {'trades': total, 'win_rate': win_rate, 'total_return': total_ret, 'pf': pf}

if __name__ == "__main__":
    print("\n🔬 ATR-BAZLI ADAPTİF TEST (Hızlı versiyon)\n")
    result = run_test(days=60, min_score=70, max_picks=3)
    
    print("\n" + "=" * 60)
    print("✅ Her hisse için volatilitesine göre farklı SL/TP:")
    print("   THYAO (Havacılık): ~%4 SL, ~%8 TP, 7 gün max")
    print("   BIMAS (Perakende): ~%2 SL, ~%5 TP, 12 gün max")
    print("   GARAN (Bankacılık): ~%3 SL, ~%6 TP, 10 gün max")
