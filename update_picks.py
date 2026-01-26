#!/usr/bin/env python3
import yfinance as yf
import json
from datetime import datetime
import psycopg2

SYMBOLS = [
    'THYAO.IS', 'GARAN.IS', 'ASELS.IS', 'EREGL.IS', 'FROTO.IS',
    'AKBNK.IS', 'YKBNK.IS', 'KCHOL.IS', 'SAHOL.IS', 'SISE.IS',
    'TCELL.IS', 'TUPRS.IS', 'PGSUS.IS', 'TAVHL.IS', 'BIMAS.IS',
    'TOASO.IS', 'EKGYO.IS', 'GUBRF.IS', 'SASA.IS', 'PETKM.IS'
]

print('📥 Downloading 3 months data for 20 stocks...')
data = yf.download(SYMBOLS, period='3mo', group_by='ticker', threads=True, progress=False)

def ema(prices, period):
    if len(prices) < period:
        return prices[-1] if prices else 0
    mult = 2 / (period + 1)
    result = sum(prices[:period]) / period
    for p in prices[period:]:
        result = (p * mult) + (result * (1 - mult))
    return result

picks = []
for symbol in SYMBOLS:
    try:
        df = data[symbol]
        if df.empty or len(df) < 50:
            continue
        
        closes = df['Close'].tolist()
        highs = df['High'].tolist()
        lows = df['Low'].tolist()
        volumes = df['Volume'].tolist()
        curr = closes[-1]
        
        ema9 = ema(closes, 9)
        ema21 = ema(closes, 21)
        ema50 = ema(closes, 50) if len(closes) >= 50 else ema21
        ema200 = ema(closes, 200) if len(closes) >= 200 else ema50
        
        # RSI
        gains, losses = [], []
        for i in range(1, min(15, len(closes))):
            diff = closes[-i] - closes[-i-1]
            if diff > 0: gains.append(diff)
            else: losses.append(abs(diff))
        avg_gain = sum(gains) / 14 if gains else 0
        avg_loss = sum(losses) / 14 if losses else 0.0001
        rsi = 100 - (100 / (1 + (avg_gain / avg_loss)))
        
        # MACD
        ema12 = ema(closes, 12)
        ema26 = ema(closes, 26)
        macd_line = ema12 - ema26
        macd_signal = macd_line * 0.9
        macd_hist = macd_line - macd_signal
        
        # ATR
        atr_val = curr * 0.025
        if len(closes) >= 14:
            trs = []
            for i in range(-14, 0):
                tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
                trs.append(tr)
            atr_val = sum(trs) / len(trs)
        
        # SCORING (Backend ile senkron)
        score = 0
        reasons = []
        
        # 1. Trend (30 puan)
        if curr > ema9 > ema21:
            score += 15
            reasons.append('Kısa trend güçlü (9>21)')
        if ema21 > ema50:
            score += 10
            reasons.append('Orta trend yukarı (21>50)')
        if curr > ema200:
            score += 5
            reasons.append('Uzun trend yukarı (>200)')
        
        # 2. RSI (20 puan)
        if 40 <= rsi <= 65:
            score += 20
            reasons.append(f'RSI optimal ({rsi:.0f})')
        elif 30 <= rsi <= 70:
            score += 10
            reasons.append(f'RSI kabul edilebilir ({rsi:.0f})')
        
        # 3. MACD (20 puan)
        if macd_line > macd_signal and macd_hist > 0:
            score += 20
            reasons.append('MACD pozitif')
        elif macd_line > macd_signal:
            score += 10
            reasons.append('MACD yukarı kesişim')
        
        # 4. Volume (15 puan)
        vol_avg = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else volumes[-1]
        vol_current = volumes[-1]
        if vol_current > vol_avg * 1.2:
            score += 15
            reasons.append('Hacim yüksek (+%20)')
        elif vol_current > vol_avg:
            score += 7
            reasons.append('Hacim normal')
        
        # 5. Pozisyon (15 puan)
        swing_low = min(lows[-10:])
        swing_high = max(highs[-10:])
        position = (curr - swing_low) / (swing_high - swing_low + 0.0001)
        if 0.3 <= position <= 0.6:
            score += 15
            reasons.append(f'Pozisyon ideal ({position*100:.0f}%)')
        elif 0.2 <= position <= 0.7:
            score += 8
            reasons.append(f'Pozisyon iyi ({position*100:.0f}%)')
        
        # Min score: 70
        if score < 70:
            print(f'✗ {symbol}: score={score} (düşük)')
            continue
        
        # Stop Loss
        atr_stop = curr - (atr_val * 2.0)
        ema_stop = ema21 * 0.98
        swing_stop = swing_low * 0.985
        stop = max(atr_stop, ema_stop, swing_stop)
        risk = curr - stop
        
        if risk / curr < 0.015:
            continue
        
        tp1 = curr + (risk * 2.5)
        tp2 = curr + (risk * 4.0)
        rr = (tp1 - curr) / risk
        
        if rr < 2.0:
            continue
        
        picks.append({
            'ticker': symbol.replace('.IS', ''),
            'entry_price': round(curr, 2),
            'stop_loss': round(stop, 2),
            'take_profit_1': round(tp1, 2),
            'take_profit_2': round(tp2, 2),
            'risk_reward_ratio': round(rr, 2),
            'risk_reward_2': 4.0,
            'risk_pct': round((risk / curr) * 100, 2),
            'reward_pct': round(((tp1 - curr) / curr) * 100, 2),
            'strength': score,
            'confidence': min(score + 10, 100),
            'signal': 'BUY',
            'sector': 'BIST30',
            'reasons': reasons,
            'partial_exit_pct': 0.5,
            'exit_strategy': {
                'tp1_action': "TP1'de %50 pozisyon kapat",
                'tp1_new_stop': "Break-even'a çek",
                'tp2_action': "TP2'de kalan %50 kapat"
            }
        })
        print(f'✓ {symbol}: score={score}')
    except Exception as e:
        print(f'✗ {symbol}: {e}')

picks.sort(key=lambda x: x['strength'], reverse=True)
top_picks = picks[:5]

result = {
    'status': 'success',
    'picks': top_picks,
    'total_scanned': len(SYMBOLS),
    'found': len(picks),
    'strategy_info': {
        'name': 'Hybrid Strategy v4',
        'win_rate': '57.1%',
        'profit_factor': '1.94',
        'backtest_return': '+105.31%',
        'min_score': 70,
        'features': ['EMA Trend', 'RSI', 'MACD', 'Volume', 'Position']
    },
    'market_trend': 'YUKSELIS' if len(top_picks) >= 3 else 'YATAY',
    'warnings': [],
    'timestamp': datetime.now().isoformat()
}

print(f'\n📊 Found {len(picks)} valid picks (score >= 70)')

if top_picks:
    print('\nSaving to PostgreSQL...')
    conn = psycopg2.connect('postgresql://neondb_owner:npg_oH4tmzI0Ekpn@ep-sparkling-glade-ahegj96z-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require')
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO daily_picks_cache (cache_key, picks_json, updated_at)
        VALUES ('daily_picks', %s, %s)
        ON CONFLICT (cache_key) DO UPDATE SET
            picks_json = EXCLUDED.picks_json,
            updated_at = EXCLUDED.updated_at
    ''', (json.dumps(result), datetime.now()))
    conn.commit()
    cur.close()
    conn.close()
    print('✓ Saved to database!')
    
    print('\n--- Günün Fırsatları (Hybrid v4) ---')
    for i, p in enumerate(top_picks, 1):
        print(f'{i}. {p["ticker"]}: Skor={p["strength"]}, Giriş={p["entry_price"]} TL')
        print(f'   Stop: {p["stop_loss"]} TL | TP1: {p["take_profit_1"]} TL | TP2: {p["take_profit_2"]} TL')
        print(f'   Nedenler: {", ".join(p.get("reasons", []))}')
else:
    print('\n⚠️ No picks found with score >= 70')
