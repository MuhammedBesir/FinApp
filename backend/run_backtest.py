"""
Günlük Öneriler Stratejisi - Backtest Scripti
Bu script, sabah 2 hisse alıp akşam satma stratejisini test eder.

NOT: Günlük öneriler her gün değiştiği için, bu backtest belirli 
kurallarla çalışır:
- Her gün en yüksek skorlu 2-3 hisseden birini seçer (rotasyon)
- Market yükseliş trendinde olmalı
- Score >= 60 (güçlü sinyaller)
"""
import sys
import os
sys.path.insert(0, '/home/MuhammedBesir/trading-botu/backend')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf

# BIST30 hisseleri (GLDTR hariç - altın sertifikası)
BIST30 = [
    "AKBNK.IS", "AKSEN.IS", "ARCLK.IS", "ASELS.IS", "BIMAS.IS",
    "EKGYO.IS", "ENKAI.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS",
    "GUBRF.IS", "HEKTS.IS", "ISCTR.IS", "KCHOL.IS", "KRDMD.IS",
    "ODAS.IS", "PETKM.IS", "PGSUS.IS", "SAHOL.IS", "SASA.IS",
    "SISE.IS", "TAVHL.IS", "TCELL.IS", "THYAO.IS", "TKFEN.IS",
    "TOASO.IS", "TRALT.IS", "TUPRS.IS", "YKBNK.IS"
]

def calculate_rsi(prices, period=14):
    """RSI hesapla"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_ema(prices, period):
    """EMA hesapla"""
    return prices.ewm(span=period, adjust=False).mean()

def calculate_atr(high, low, close, period=14):
    """ATR hesapla"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def calculate_score(df):
    """
    Hybrid Trend-Following + Pullback Score
    - Trend (30 puan): EMA20 > EMA50
    - Momentum (25 puan): RSI 30-70 bandında
    - Pullback (25 puan): Fiyat EMA20'ye yakın
    - Volume (20 puan): Hacim ortalamanın üzerinde
    """
    if len(df) < 50:
        return 0
    
    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']
    
    # Indicators
    ema20 = calculate_ema(close, 20)
    ema50 = calculate_ema(close, 50)
    rsi = calculate_rsi(close, 14)
    vol_avg = volume.rolling(20).mean()
    
    score = 0
    current_price = close.iloc[-1]
    
    # 1. Trend Score (30 puan)
    if ema20.iloc[-1] > ema50.iloc[-1]:
        score += 30
    elif ema20.iloc[-1] > ema50.iloc[-1] * 0.98:  # Yakın
        score += 15
    
    # 2. Momentum Score (25 puan)
    current_rsi = rsi.iloc[-1]
    if 40 <= current_rsi <= 60:  # Ideal zone
        score += 25
    elif 30 <= current_rsi <= 70:  # OK zone
        score += 15
    elif current_rsi < 30:  # Oversold - potential bounce
        score += 20
    
    # 3. Pullback Score (25 puan)
    ema20_val = ema20.iloc[-1]
    pullback_pct = abs(current_price - ema20_val) / ema20_val * 100
    if pullback_pct < 2:  # Very close to EMA20
        score += 25
    elif pullback_pct < 5:  # Reasonable pullback
        score += 15
    
    # 4. Volume Score (20 puan)
    if volume.iloc[-1] > vol_avg.iloc[-1]:
        score += 20
    elif volume.iloc[-1] > vol_avg.iloc[-1] * 0.8:
        score += 10
    
    return score

def run_backtest(days=180, initial_capital=10000, commission_pct=0.001):
    """
    Ana Backtest Fonksiyonu
    
    Strateji:
    - Her gün en yüksek skorlu hisseyi seç (score >= 60)
    - Sabah al, akşam sat (gün içi işlem)
    - Stop-loss: %3, Take-profit: %5 (veya gün sonu)
    - Komisyon: %0.1 (alış + satış)
    """
    print(f"\n{'='*60}")
    print(f"GÜNLÜK ÖNERİLER STRATEJİSİ - BACKTEST")
    print(f"{'='*60}")
    print(f"Tarih Aralığı: Son {days} gün")
    print(f"Başlangıç Sermayesi: ₺{initial_capital:,.0f}")
    print(f"Komisyon: %{commission_pct*100}")
    print(f"{'='*60}\n")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days + 60)  # Extra for indicators
    
    # Tüm hisseler için veri çek
    print("Veriler çekiliyor...")
    all_data = {}
    for ticker in BIST30:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if len(df) > 50:
                all_data[ticker] = df
        except Exception as e:
            continue
    
    print(f"✓ {len(all_data)} hisse için veri alındı\n")
    
    # BIST100 trend kontrolü - skip if no data
    print("BIST100 trend analizi...")
    try:
        xu100 = yf.download("XU100.IS", start=start_date, end=end_date, progress=False)
        if len(xu100) > 50:
            xu100_ema20 = calculate_ema(xu100['Close'], 20)
            xu100_ema50 = calculate_ema(xu100['Close'], 50)
            use_market_filter = True
        else:
            use_market_filter = False
            print("⚠️ BIST100 verisi alınamadı, market filter devre dışı")
    except:
        use_market_filter = False
        print("⚠️ BIST100 verisi alınamadı, market filter devre dışı")
    
    # Trading simulation
    capital = initial_capital
    trades = []
    equity_curve = [capital]
    
    # Her işlem günü için
    trading_days = pd.date_range(start=end_date - timedelta(days=days), end=end_date, freq='B')
    
    print(f"Backtest başlıyor ({len(trading_days)} işlem günü)...\n")
    
    winning_trades = 0
    losing_trades = 0
    total_profit = 0
    total_loss = 0
    
    for i, date in enumerate(trading_days):
        date_str = date.strftime('%Y-%m-%d')
        
        # Market trend kontrolü (opsiyonel)
        if use_market_filter:
            try:
                xu100_date = xu100.loc[:date]
                if len(xu100_date) >= 50:
                    ema20_val = xu100_ema20.loc[:date].iloc[-1]
                    ema50_val = xu100_ema50.loc[:date].iloc[-1]
                    
                    if ema20_val < ema50_val:  # Düşüş trendi
                        continue
            except:
                pass  # Market filter başarısız olursa devam et
        
        # Her hisse için skor hesapla
        scores = []
        for ticker, df in all_data.items():
            try:
                df_until_date = df.loc[:date]
                if len(df_until_date) < 50:
                    continue
                
                score = calculate_score(df_until_date)
                if score >= 60:  # Minimum skor
                    scores.append({
                        'ticker': ticker,
                        'score': score,
                        'price': df_until_date['Close'].iloc[-1],
                        'high': df_until_date['High'].iloc[-1],
                        'low': df_until_date['Low'].iloc[-1],
                        'atr': calculate_atr(
                            df_until_date['High'], 
                            df_until_date['Low'], 
                            df_until_date['Close']
                        ).iloc[-1]
                    })
            except Exception as e:
                continue
        
        if not scores:
            continue
        
        # En yüksek skorlu hisseyi seç (rotasyon için mod kullan)
        scores.sort(key=lambda x: x['score'], reverse=True)
        pick_idx = i % min(3, len(scores))  # Top 3 arasında rotasyon
        selected = scores[pick_idx]
        
        # Trade simülasyonu
        entry_price = selected['price'] * 1.001  # Slippage
        atr = selected['atr'] if selected['atr'] > 0 else entry_price * 0.02
        
        stop_loss = entry_price - (atr * 1.5)  # 1.5 ATR stop
        take_profit = entry_price + (atr * 3)  # 3 ATR target (2:1 RR)
        
        # Position size: %10 of capital max
        position_value = min(capital * 0.10, capital * 0.95)
        shares = int(position_value / entry_price)
        
        if shares <= 0:
            continue
        
        position_value = shares * entry_price
        commission = position_value * commission_pct * 2  # Buy + Sell
        
        # Sonraki günün fiyatını kontrol et (gün sonu çıkış)
        try:
            next_day = date + timedelta(days=1)
            while next_day.weekday() >= 5:  # Skip weekend
                next_day += timedelta(days=1)
            
            ticker_df = all_data[selected['ticker']]
            next_data = ticker_df.loc[next_day:next_day + timedelta(days=5)]
            
            if len(next_data) == 0:
                continue
            
            day_high = next_data['High'].iloc[0]
            day_low = next_data['Low'].iloc[0]
            day_close = next_data['Close'].iloc[0]
            
            # Exit logic
            if day_low <= stop_loss:
                exit_price = stop_loss
                result = 'LOSS'
            elif day_high >= take_profit:
                exit_price = take_profit * 0.999  # Slippage
                result = 'WIN'
            else:
                exit_price = day_close * 0.999  # Slippage
                result = 'WIN' if exit_price > entry_price else 'LOSS'
            
            profit = (exit_price - entry_price) * shares - commission
            profit_pct = (profit / position_value) * 100
            
            capital += profit
            equity_curve.append(capital)
            
            trade = {
                'date': date_str,
                'ticker': selected['ticker'],
                'score': selected['score'],
                'entry': round(entry_price, 2),
                'exit': round(exit_price, 2),
                'shares': shares,
                'profit': round(profit, 2),
                'profit_pct': round(profit_pct, 2),
                'result': result,
                'capital': round(capital, 2)
            }
            trades.append(trade)
            
            if result == 'WIN':
                winning_trades += 1
                total_profit += profit
            else:
                losing_trades += 1
                total_loss += abs(profit)
                
        except Exception as e:
            continue
    
    # Sonuçları hesapla
    total_trades = len(trades)
    if total_trades == 0:
        print("❌ Hiç trade yapılamadı!")
        return
    
    win_rate = (winning_trades / total_trades) * 100
    avg_win = total_profit / winning_trades if winning_trades > 0 else 0
    avg_loss = total_loss / losing_trades if losing_trades > 0 else 0
    profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
    total_return = ((capital - initial_capital) / initial_capital) * 100
    
    # Max Drawdown
    peak = equity_curve[0]
    max_dd = 0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100
        if dd > max_dd:
            max_dd = dd
    
    print(f"\n{'='*60}")
    print(f"BACKTEST SONUÇLARI")
    print(f"{'='*60}")
    print(f"\n📊 GENEL İSTATİSTİKLER:")
    print(f"   Toplam Trade: {total_trades}")
    print(f"   Kazanan: {winning_trades} | Kaybeden: {losing_trades}")
    print(f"   Kazanma Oranı: %{win_rate:.1f}")
    print(f"\n💰 KAR/ZARAR:")
    print(f"   Başlangıç Sermaye: ₺{initial_capital:,.0f}")
    print(f"   Final Sermaye: ₺{capital:,.0f}")
    print(f"   Toplam Getiri: %{total_return:.1f}")
    print(f"   Net Kar/Zarar: ₺{capital - initial_capital:,.0f}")
    print(f"\n📈 PERFORMANS METRİKLERİ:")
    print(f"   Ortalama Kazanç: ₺{avg_win:.0f}")
    print(f"   Ortalama Kayıp: ₺{avg_loss:.0f}")
    print(f"   Profit Factor: {profit_factor:.2f}")
    print(f"   Max Drawdown: %{max_dd:.1f}")
    
    # Risk/Reward analizi
    if avg_loss > 0:
        rr_ratio = avg_win / avg_loss
        print(f"   Risk/Reward Ratio: {rr_ratio:.2f}")
    
    print(f"\n{'='*60}")
    print(f"STRATEJİ DEĞERLENDİRMESİ")
    print(f"{'='*60}")
    
    if win_rate >= 50 and profit_factor >= 1.5:
        print("✅ GÜÇLÜ STRATEJİ - Kazanma oranı ve kar faktörü iyi")
    elif win_rate >= 45 and profit_factor >= 1.2:
        print("⚠️ ORTA STRATEJİ - Dikkatli kullanılmalı")
    else:
        print("❌ ZAYIF STRATEJİ - İyileştirme gerekli")
    
    print(f"\n🎯 ÖNERİLER:")
    if win_rate < 50:
        print("   - Score eşiğini yükselt (>70)")
    if profit_factor < 1.5:
        print("   - Take-profit/Stop-loss oranını gözden geçir")
    if max_dd > 20:
        print("   - Position size'ı küçült")
    
    # Son 10 trade
    print(f"\n📋 SON 10 TRADE:")
    print(f"{'Tarih':<12} {'Hisse':<10} {'Skor':<6} {'Giriş':<10} {'Çıkış':<10} {'Kar%':<8} {'Sonuç':<6}")
    print("-" * 70)
    for t in trades[-10:]:
        print(f"{t['date']:<12} {t['ticker'].replace('.IS',''):<10} {t['score']:<6} {t['entry']:<10.2f} {t['exit']:<10.2f} {t['profit_pct']:<8.1f} {t['result']:<6}")
    
    return {
        'trades': trades,
        'metrics': {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_return': total_return,
            'max_drawdown': max_dd
        }
    }

if __name__ == "__main__":
    run_backtest(days=180)  # 6 aylık backtest
