#!/usr/bin/env python3
"""
A/B Karşılaştırma Backtest
Farklı konfigürasyonları test et
"""

import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

STOCKS = [
    'GARAN.IS', 'AKBNK.IS', 'YKBNK.IS', 'VAKBN.IS', 'ISCTR.IS',
    'KCHOL.IS', 'SAHOL.IS', 'ASELS.IS', 'TOASO.IS', 'FROTO.IS',
    'AKSEN.IS', 'TUPRS.IS', 'ENKAI.IS', 'BIMAS.IS', 'SISE.IS',
    'TCELL.IS', 'TAVHL.IS', 'EKGYO.IS', 'GUBRF.IS', 'THYAO.IS', 'YKBNK.IS'
]

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

def backtest(all_data, xu030, config):
    """Tek backtest çalıştır"""
    TRAILING = config.get('trailing', False)
    TRAIL_TRIGGER = config.get('trail_trigger', 3)  # % kar sonrası trailing aktif
    MARKET_FILTER = config.get('market_filter', False)
    TP_MULT = config.get('tp_mult', 2.5)
    
    sample_len = len(list(all_data.values())[0]['closes'])
    start_day = sample_len - 90
    
    trades = []
    active = {}
    market_skips = 0
    trail_triggers = 0
    
    for day in range(start_day, sample_len):
        # Market filter
        market_ok = True
        if MARKET_FILTER and xu030 and day < len(xu030):
            xu_closes = xu030[:day+1]
            if len(xu_closes) >= 50:
                xu_curr = xu_closes[-1]
                xu_ema50 = ema(xu_closes, 50)
                if xu_curr < xu_ema50:
                    market_ok = False
                    market_skips += 1
        
        # Pozisyonları kontrol
        to_close = []
        for ticker, pos in active.items():
            data = all_data.get(ticker)
            if not data or day >= len(data['closes']):
                continue
            
            hi = data['highs'][day]
            lo = data['lows'][day]
            cl = data['closes'][day]
            days_held = day - pos['entry_day']
            
            # Trailing stop
            if hi > pos['high_since']:
                pos['high_since'] = hi
                if TRAILING:
                    pct_up = (hi - pos['entry']) / pos['entry'] * 100
                    if pct_up >= TRAIL_TRIGGER:
                        # Trail: current high - ATR
                        new_stop = hi - pos['atr']
                        if new_stop > pos['stop']:
                            pos['stop'] = new_stop
                            pos['trail_active'] = True
            
            # Çıkış
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
                trades.append({'pnl': pnl, 'result': result})
                to_close.append(ticker)
        
        for t in to_close:
            del active[t]
        
        if not market_ok:
            continue
        
        # Sinyal üret
        signals = []
        for ticker, data in all_data.items():
            if ticker in active or day >= len(data['closes']) or day < 50:
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
            
            score = 0
            if curr > ema9 > ema21: score += 20
            if ema21 > ema50: score += 15
            if 35 <= rsi_val <= 65: score += 20
            
            vol_avg = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else volumes[-1]
            if volumes[-1] > vol_avg: score += 15
            
            if len(lows) >= 10:
                pos_pct = (curr - min(lows[-10:])) / (max(highs[-10:]) - min(lows[-10:]) + 0.0001)
                if 0.15 <= pos_pct <= 0.55: score += 15
            
            if len(closes) >= 5:
                mom = (closes[-1] - closes[-5]) / closes[-5] * 100
                if 0 < mom < 5: score += 10
            
            if score >= 60:
                atr = curr * 0.025
                if len(closes) >= 14:
                    trs = []
                    for i in range(-14, 0):
                        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
                        trs.append(tr)
                    atr = sum(trs) / len(trs)
                
                stop = curr - (atr * 2.0)
                risk = curr - stop
                
                if risk / curr >= 0.015:
                    tp1 = curr + (risk * TP_MULT)
                    signals.append((ticker, score, curr, stop, tp1, atr))
        
        signals.sort(key=lambda x: x[1], reverse=True)
        
        for ticker, score, entry, stop, tp1, atr in signals[:5]:
            if ticker not in active:
                active[ticker] = {
                    'entry': entry, 'stop': stop, 'tp1': tp1, 'atr': atr,
                    'entry_day': day, 'score': score, 'high_since': entry,
                    'trail_active': False
                }
    
    # Açık pozisyonları kapat
    for ticker, pos in active.items():
        data = all_data.get(ticker)
        if data:
            cl = data['closes'][-1]
            pnl = ((cl - pos['entry']) / pos['entry']) * 100
            trades.append({'pnl': pnl, 'result': 'OPEN'})
    
    if not trades:
        return None
    
    wins = [t for t in trades if t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] <= 0]
    
    wr = len(wins) / len(trades) * 100
    total_pnl = sum(t['pnl'] for t in trades)
    
    gross_win = sum(t['pnl'] for t in wins)
    gross_loss = abs(sum(t['pnl'] for t in losses)) if losses else 0.01
    pf = gross_win / gross_loss
    
    return {
        'trades': len(trades),
        'wins': len(wins),
        'wr': wr,
        'pnl': total_pnl,
        'pf': pf,
        'market_skips': market_skips,
        'trail_triggers': trail_triggers
    }

def main():
    print("="*70)
    print("🔬 A/B KARŞILAŞTIRMA TESTİ")
    print("="*70)
    
    # Veri indir
    end = datetime.now()
    start = end - timedelta(days=400)
    
    print("📥 Veri indiriliyor...")
    tickers = list(set(STOCKS)) + ['XU030.IS']
    raw = yf.download(tickers, start=start, end=end, progress=False, threads=True)
    
    all_data = {}
    xu030 = None
    
    for ticker in tickers:
        try:
            closes = raw['Close'][ticker].dropna().tolist()
            highs = raw['High'][ticker].dropna().tolist()
            lows = raw['Low'][ticker].dropna().tolist()
            volumes = raw['Volume'][ticker].dropna().tolist()
            
            if len(closes) > 100:
                if ticker == 'XU030.IS':
                    xu030 = closes
                else:
                    all_data[ticker] = {'closes': closes, 'highs': highs, 'lows': lows, 'volumes': volumes}
        except:
            pass
    
    print(f"✅ {len(all_data)} hisse yüklendi\n")
    
    # Test konfigürasyonları
    configs = [
        {'name': 'MEVCUT (Baseline)', 'trailing': False, 'market_filter': False, 'tp_mult': 2.5},
        {'name': 'Sadece Market Filter', 'trailing': False, 'market_filter': True, 'tp_mult': 2.5},
        {'name': 'Sadece Trailing (%3)', 'trailing': True, 'trail_trigger': 3, 'market_filter': False, 'tp_mult': 2.5},
        {'name': 'Trailing (%5) Geç', 'trailing': True, 'trail_trigger': 5, 'market_filter': False, 'tp_mult': 2.5},
        {'name': 'Market + Trailing(%5)', 'trailing': True, 'trail_trigger': 5, 'market_filter': True, 'tp_mult': 2.5},
        {'name': 'TP 2.0x', 'trailing': False, 'market_filter': False, 'tp_mult': 2.0},
        {'name': 'TP 2.0x + Market', 'trailing': False, 'market_filter': True, 'tp_mult': 2.0},
        {'name': 'FULL (Market+Trail+TP2)', 'trailing': True, 'trail_trigger': 5, 'market_filter': True, 'tp_mult': 2.0},
    ]
    
    print("="*70)
    print(f"{'Strateji':<25} {'Trade':>6} {'WR':>7} {'PF':>6} {'PnL':>10}")
    print("-"*70)
    
    results = []
    for config in configs:
        result = backtest(all_data, xu030, config)
        if result:
            results.append((config['name'], result))
            print(f"{config['name']:<25} {result['trades']:>6} {result['wr']:>6.1f}% {result['pf']:>6.2f} {result['pnl']:>+9.1f}%")
    
    print("="*70)
    
    # En iyi sonuç
    best = max(results, key=lambda x: x[1]['pnl'])
    print(f"\n🏆 EN İYİ SONUÇ: {best[0]}")
    print(f"   PnL: {best[1]['pnl']:+.1f}%")
    print(f"   Win Rate: {best[1]['wr']:.1f}%")
    print(f"   Profit Factor: {best[1]['pf']:.2f}")
    print(f"   Trade Sayısı: {best[1]['trades']}")
    
    # Baseline vs Best
    baseline = results[0][1]
    print(f"\n📊 BASELINE vs EN İYİ:")
    print(f"   PnL Farkı: {best[1]['pnl'] - baseline['pnl']:+.1f}%")
    print(f"   WR Farkı: {best[1]['wr'] - baseline['wr']:+.1f}%")
    print(f"   PF Farkı: {best[1]['pf'] - baseline['pf']:+.2f}")

if __name__ == "__main__":
    main()
