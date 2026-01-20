"""
Hızlı Backtest - 30 Günlük Test
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf

# BIST30 (populer 10 hisse)
STOCKS = ["THYAO.IS", "GARAN.IS", "AKBNK.IS", "ISCTR.IS", "SISE.IS", 
          "TUPRS.IS", "EREGL.IS", "KCHOL.IS", "SAHOL.IS", "FROTO.IS"]

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_ema(prices, period):
    return prices.ewm(span=period, adjust=False).mean()

def calculate_score(df):
    if len(df) < 50:
        return 0
    close = df['Close']
    volume = df['Volume']
    
    ema20 = calculate_ema(close, 20)
    ema50 = calculate_ema(close, 50)
    rsi = calculate_rsi(close, 14)
    vol_avg = volume.rolling(20).mean()
    
    score = 0
    current_price = close.iloc[-1]
    
    # Trend (30 puan)
    if ema20.iloc[-1] > ema50.iloc[-1]:
        score += 30
    elif ema20.iloc[-1] > ema50.iloc[-1] * 0.98:
        score += 15
    
    # Momentum (25 puan)
    current_rsi = rsi.iloc[-1]
    if 40 <= current_rsi <= 60:
        score += 25
    elif 30 <= current_rsi <= 70:
        score += 15
    elif current_rsi < 30:
        score += 20
    
    # Pullback (25 puan)
    ema20_val = ema20.iloc[-1]
    pullback_pct = abs(current_price - ema20_val) / ema20_val * 100
    if pullback_pct < 2:
        score += 25
    elif pullback_pct < 5:
        score += 15
    
    # Volume (20 puan)
    if volume.iloc[-1] > vol_avg.iloc[-1]:
        score += 20
    elif volume.iloc[-1] > vol_avg.iloc[-1] * 0.8:
        score += 10
    
    return score

print("="*60)
print("GÜNLÜK ÖNERİLER STRATEJİSİ - HIZLI BACKTEST")
print("="*60)
print("Tarih: Son 90 gün | Sermaye: ₺10,000")
print("="*60)

end_date = datetime.now()
start_date = end_date - timedelta(days=150)

# Veri çek
print("\nVeriler çekiliyor...")
all_data = {}
for ticker in STOCKS:
    try:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        # Multi-level column fix
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if len(df) > 50 and 'Close' in df.columns:
            all_data[ticker] = df
            print(f"  ✓ {ticker}: {len(df)} gün")
    except Exception as e:
        print(f"  ✗ {ticker}: {e}")

print(f"\n{len(all_data)} hisse yüklendi")

# Backtest
capital = 10000
trades = []
equity = [capital]

trading_days = pd.date_range(start=end_date - timedelta(days=90), end=end_date, freq='B')
print(f"\nBacktest: {len(trading_days)} işlem günü\n")

for i, date in enumerate(trading_days):
    # Her hisse için skor
    scores = []
    for ticker, df in all_data.items():
        try:
            df_date = df.loc[:date]
            if len(df_date) < 50:
                continue
            score = calculate_score(df_date)
            if score >= 60:
                close_price = df_date['Close'].iloc[-1]
                scores.append({'ticker': ticker, 'score': score, 'price': close_price})
        except:
            continue
    
    if not scores:
        continue
    
    # En iyi hisse (rotasyon)
    scores.sort(key=lambda x: x['score'], reverse=True)
    selected = scores[i % min(3, len(scores))]
    
    # Trade
    entry = selected['price'] * 1.001
    stop_loss = entry * 0.97  # %3 stop
    take_profit = entry * 1.05  # %5 target
    
    position_value = min(capital * 0.10, capital * 0.95)
    shares = int(position_value / entry)
    if shares <= 0:
        continue
    
    position_value = shares * entry
    commission = position_value * 0.002
    
    # Sonraki gün
    try:
        next_day = date + timedelta(days=1)
        while next_day.weekday() >= 5:
            next_day += timedelta(days=1)
        
        ticker_df = all_data[selected['ticker']]
        next_data = ticker_df.loc[next_day:next_day + timedelta(days=7)]
        if len(next_data) == 0:
            continue
        
        day_high = next_data['High'].iloc[0]
        day_low = next_data['Low'].iloc[0]
        day_close = next_data['Close'].iloc[0]
        
        if day_low <= stop_loss:
            exit_price = stop_loss
            result = 'LOSS'
        elif day_high >= take_profit:
            exit_price = take_profit * 0.999
            result = 'WIN'
        else:
            exit_price = day_close * 0.999
            result = 'WIN' if exit_price > entry else 'LOSS'
        
        profit = (exit_price - entry) * shares - commission
        capital += profit
        equity.append(capital)
        
        trades.append({
            'date': date.strftime('%Y-%m-%d'),
            'ticker': selected['ticker'].replace('.IS',''),
            'score': selected['score'],
            'entry': entry,
            'exit': exit_price,
            'profit': profit,
            'result': result
        })
    except:
        continue

# Sonuçlar
if trades:
    wins = [t for t in trades if t['result'] == 'WIN']
    losses = [t for t in trades if t['result'] == 'LOSS']
    
    total = len(trades)
    win_rate = len(wins) / total * 100
    total_profit = sum(t['profit'] for t in wins)
    total_loss = abs(sum(t['profit'] for t in losses))
    profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
    total_return = (capital - 10000) / 10000 * 100
    
    # Max Drawdown
    peak = equity[0]
    max_dd = 0
    for eq in equity:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100
        if dd > max_dd:
            max_dd = dd
    
    print("="*60)
    print("BACKTEST SONUÇLARI")
    print("="*60)
    print(f"\n📊 GENEL İSTATİSTİKLER:")
    print(f"   Toplam Trade: {total}")
    print(f"   Kazanan: {len(wins)} | Kaybeden: {len(losses)}")
    print(f"   Kazanma Oranı: %{win_rate:.1f}")
    print(f"\n💰 KAR/ZARAR:")
    print(f"   Başlangıç: ₺10,000")
    print(f"   Final: ₺{capital:,.0f}")
    print(f"   Toplam Getiri: %{total_return:.1f}")
    print(f"   Net Kar/Zarar: ₺{capital - 10000:,.0f}")
    print(f"\n📈 PERFORMANS:")
    print(f"   Profit Factor: {profit_factor:.2f}")
    print(f"   Max Drawdown: %{max_dd:.1f}")
    
    print(f"\n🎯 DEĞERLENDİRME:")
    if win_rate >= 50 and profit_factor >= 1.5:
        print("   ✅ GÜÇLÜ STRATEJİ")
    elif win_rate >= 45 and profit_factor >= 1.2:
        print("   ⚠️ ORTA STRATEJİ")
    else:
        print("   ❌ ZAYIF STRATEJİ")
    
    print(f"\n📋 SON 10 TRADE:")
    print(f"{'Tarih':<12} {'Hisse':<8} {'Skor':<6} {'Kar':<10} {'Sonuç':<6}")
    print("-"*50)
    for t in trades[-10:]:
        print(f"{t['date']:<12} {t['ticker']:<8} {t['score']:<6} ₺{t['profit']:<9.0f} {t['result']:<6}")
else:
    print("❌ Hiç trade yapılamadı!")
