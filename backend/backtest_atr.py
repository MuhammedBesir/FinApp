#!/usr/bin/env python3
"""
BACKTEST v3.0 - ATR-BAZLI ADAPTİF STRATEJİ
Her hisse için kendi volatilitesine göre SL/TP hesaplanır
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

# Hisse listesi
TICKERS = [
    "AKBNK.IS", "AKSEN.IS", "ARCLK.IS", "ASELS.IS", "BIMAS.IS",
    "EKGYO.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS",
    "GUBRF.IS", "HEKTS.IS", "ISCTR.IS", "KCHOL.IS", "KRDMD.IS",
    "PETKM.IS", "PGSUS.IS", "SAHOL.IS", "SISE.IS",
    "TAVHL.IS", "TCELL.IS", "THYAO.IS", "TKFEN.IS", "TOASO.IS",
    "TUPRS.IS", "YKBNK.IS"
]

# Sektör tanımları
STOCK_SECTORS = {
    "AKBNK.IS": "Bankacılık", "AKSEN.IS": "Enerji", "ARCLK.IS": "Dayanıklı Tüketim",
    "ASELS.IS": "Savunma", "BIMAS.IS": "Perakende", "EKGYO.IS": "GYO",
    "ENKAI.IS": "İnşaat", "EREGL.IS": "Demir Çelik", "FROTO.IS": "Otomotiv",
    "GARAN.IS": "Bankacılık", "GUBRF.IS": "Kimya", "HEKTS.IS": "Kimya",
    "ISCTR.IS": "Bankacılık", "KCHOL.IS": "Holding", "KRDMD.IS": "Demir Çelik",
    "ODAS.IS": "Enerji", "PETKM.IS": "Petrokimya", "PGSUS.IS": "Havacılık",
    "SAHOL.IS": "Holding", "SASA.IS": "Petrokimya", "SISE.IS": "Cam",
    "TAVHL.IS": "Havacılık", "TCELL.IS": "Telekomünikasyon", "THYAO.IS": "Havacılık",
    "TKFEN.IS": "Holding", "TOASO.IS": "Otomotiv", "TRALT.IS": "Altın",
    "TUPRS.IS": "Enerji", "YKBNK.IS": "Bankacılık",
}

# Sektör volatilite profilleri - ATR multiplier'ları
SECTOR_VOLATILITY_PROFILE = {
    "Havacılık": {"sl_atr_mult": 2.0, "tp_atr_mult": 4.0, "max_hold": 7},
    "Enerji": {"sl_atr_mult": 1.8, "tp_atr_mult": 3.5, "max_hold": 8},
    "GYO": {"sl_atr_mult": 1.5, "tp_atr_mult": 3.0, "max_hold": 10},
    "Petrokimya": {"sl_atr_mult": 1.8, "tp_atr_mult": 3.5, "max_hold": 8},
    "Demir Çelik": {"sl_atr_mult": 1.7, "tp_atr_mult": 3.5, "max_hold": 8},
    "Bankacılık": {"sl_atr_mult": 1.5, "tp_atr_mult": 3.0, "max_hold": 10},
    "Holding": {"sl_atr_mult": 1.4, "tp_atr_mult": 2.8, "max_hold": 12},
    "Perakende": {"sl_atr_mult": 1.3, "tp_atr_mult": 2.6, "max_hold": 12},
    "Telekomünikasyon": {"sl_atr_mult": 1.4, "tp_atr_mult": 2.8, "max_hold": 10},
    "Otomotiv": {"sl_atr_mult": 1.6, "tp_atr_mult": 3.2, "max_hold": 10},
    "Dayanıklı Tüketim": {"sl_atr_mult": 1.5, "tp_atr_mult": 3.0, "max_hold": 10},
    "Savunma": {"sl_atr_mult": 1.7, "tp_atr_mult": 3.5, "max_hold": 8},
    "İnşaat": {"sl_atr_mult": 1.6, "tp_atr_mult": 3.2, "max_hold": 10},
    "Kimya": {"sl_atr_mult": 1.6, "tp_atr_mult": 3.2, "max_hold": 10},
    "Cam": {"sl_atr_mult": 1.5, "tp_atr_mult": 3.0, "max_hold": 10},
    "Altın": {"sl_atr_mult": 1.2, "tp_atr_mult": 2.5, "max_hold": 15},
    "default": {"sl_atr_mult": 1.5, "tp_atr_mult": 3.0, "max_hold": 10},
}


def calculate_atr(df, period=14):
    """ATR hesapla"""
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def calculate_indicators(df):
    """Teknik indikatörleri hesapla"""
    df = df.copy()
    
    # EMAs
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # ATR
    df['ATR'] = calculate_atr(df)
    
    # Volatilite yüzdesi
    df['ATR_Percent'] = (df['ATR'] / df['Close']) * 100
    
    # Volume ortalaması
    df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
    df['Vol_Ratio'] = df['Volume'] / df['Vol_MA20']
    
    return df


def calculate_score(row, prev_row=None):
    """Hybrid score hesapla (0-100)"""
    score = 0
    
    price = row['Close']
    ema20 = row['EMA20']
    ema50 = row['EMA50']
    rsi = row['RSI']
    macd_hist = row['MACD_Hist']
    vol_ratio = row['Vol_Ratio']
    
    # 1. TREND (30 puan)
    if price > ema20 and ema20 > ema50:
        score += 30  # Güçlü uptrend
    elif price > ema50 and ema20 > ema50:
        score += 20  # Pullback
    elif ema20 > ema50:
        score += 10  # Zayıf uptrend
    
    # 2. MOMENTUM (25 puan)
    if 40 <= rsi <= 60:
        score += 15
    elif 30 <= rsi < 40:
        score += 10
    elif 60 < rsi <= 70:
        score += 5
    
    if macd_hist > 0:
        score += 10
    elif macd_hist > -0.1:
        score += 5
    
    # 3. SUPPORT (25 puan)
    dist_ema20 = abs(price - ema20) / price
    if dist_ema20 < 0.015:
        score += 25
    elif dist_ema20 < 0.03:
        score += 15
    else:
        score += 5
    
    # 4. VOLUME (20 puan)
    if vol_ratio > 1.5:
        score += 20
    elif vol_ratio > 1.0:
        score += 10
    
    return score


def get_atr_levels(ticker, row, prev_days_df):
    """
    ATR-BAZLI DİNAMİK SL/TP HESAPLA
    Her hisse için sektörüne göre farklı multiplier kullanır
    """
    sector = STOCK_SECTORS.get(ticker, "default")
    profile = SECTOR_VOLATILITY_PROFILE.get(sector, SECTOR_VOLATILITY_PROFILE["default"])
    
    price = row['Close']
    atr = row['ATR']
    
    if pd.isna(atr) or atr == 0:
        atr = price * 0.02
    
    atr_percent = (atr / price) * 100
    
    # Dinamik SL hesaplama
    sl_mult = profile['sl_atr_mult']
    tp_mult = profile['tp_atr_mult']
    max_hold = profile['max_hold']
    
    # SL: ATR * multiplier, min %1.5, max %5
    sl_distance = atr * sl_mult
    sl_distance = max(sl_distance, price * 0.015)  # Min %1.5
    sl_distance = min(sl_distance, price * 0.05)   # Max %5
    
    stop_loss = price - sl_distance
    
    # TP: ATR * multiplier veya min 1:2 R:R
    tp_distance = max(atr * tp_mult, sl_distance * 2)
    take_profit = price + tp_distance
    
    sl_pct = (sl_distance / price) * 100
    tp_pct = (tp_distance / price) * 100
    
    return {
        'entry': price,
        'stop_loss': stop_loss,
        'take_profit': take_profit,
        'sl_pct': sl_pct,
        'tp_pct': tp_pct,
        'atr': atr,
        'atr_percent': atr_percent,
        'max_hold': max_hold,
        'sector': sector,
        'sl_mult': sl_mult,
        'tp_mult': tp_mult
    }


def run_backtest_atr(days=90, min_score=70, max_picks=5):
    """ATR-bazlı adaptif backtest"""
    
    print("=" * 65)
    print("🚀 BACKTEST v3.0 - ATR-BAZLI ADAPTİF STRATEJİ")
    print("=" * 65)
    print(f"📅 Test Süresi: {days} gün")
    print(f"🎯 Min Score: {min_score}+")
    print(f"📊 Max Picks/Gün: {max_picks}")
    print(f"⛔ Stop-Loss: ATR-bazlı (sektöre göre %1.5-5)")
    print(f"🎯 Take-Profit: ATR-bazlı (sektöre göre 1:2-1:3 R:R)")
    print(f"⏱️ Max Holding: Sektöre göre 7-15 gün")
    print("=" * 65)
    
    # Veri çek
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days + 100)
    
    print(f"📥 Veri çekiliyor ({len(TICKERS)} hisse)...")
    
    stock_data = {}
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if len(df) >= 60:
                df = calculate_indicators(df)
                stock_data[ticker] = df
        except Exception as e:
            continue
    
    # BIST100 verisi
    print("📥 BIST100 verisi çekiliyor...")
    try:
        xu100 = yf.download("XU100.IS", start=start_date, end=end_date, progress=False)
        xu100['EMA20'] = xu100['Close'].ewm(span=20, adjust=False).mean()
        xu100['EMA50'] = xu100['Close'].ewm(span=50, adjust=False).mean()
    except:
        xu100 = None
    
    print(f"✅ {len(stock_data)} hisse yüklendi")
    
    # Backtest
    trades = []
    open_positions = []
    used_sectors_today = set()
    market_filter_blocks = 0
    no_signal_days = 0
    
    # Trade istatistikleri (sektör bazlı)
    sector_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'total_return': 0})
    
    # Ortak tarih aralığı bul
    common_dates = None
    for ticker, df in stock_data.items():
        dates = set(df.index)
        if common_dates is None:
            common_dates = dates
        else:
            common_dates = common_dates.intersection(dates)
    
    if not common_dates:
        print("❌ Ortak tarih bulunamadı!")
        return None
    
    common_dates = sorted(list(common_dates))[-days:]
    
    for date in common_dates:
        # Market filtresi
        market_uptrend = True
        if xu100 is not None and date in xu100.index:
            xu_row = xu100.loc[date]
            market_uptrend = xu_row['EMA20'] > xu_row['EMA50']
        
        if not market_uptrend:
            market_filter_blocks += 1
            # Açık pozisyonları kontrol et
            for pos in open_positions[:]:
                ticker = pos['ticker']
                if ticker in stock_data and date in stock_data[ticker].index:
                    row = stock_data[ticker].loc[date]
                    pos = check_exit(pos, row, date)
                    if pos.get('closed'):
                        trades.append(pos)
                        open_positions.remove(pos)
            continue
        
        # Açık pozisyonları kontrol et
        for pos in open_positions[:]:
            ticker = pos['ticker']
            if ticker in stock_data and date in stock_data[ticker].index:
                row = stock_data[ticker].loc[date]
                pos = check_exit(pos, row, date)
                if pos.get('closed'):
                    # Sektör istatistikleri güncelle
                    sector = pos.get('sector', 'default')
                    sector_stats[sector]['trades'] += 1
                    sector_stats[sector]['total_return'] += pos['return_pct']
                    if pos['return_pct'] > 0:
                        sector_stats[sector]['wins'] += 1
                    
                    trades.append(pos)
                    open_positions.remove(pos)
        
        # Yeni sinyal ara
        used_sectors_today = {pos['sector'] for pos in open_positions}
        signals = []
        
        for ticker, df in stock_data.items():
            if date not in df.index:
                continue
            
            sector = STOCK_SECTORS.get(ticker, 'default')
            
            # Sektör çeşitlendirmesi - aynı sektörden max 1
            if sector in used_sectors_today:
                continue
            
            # Aynı hissede açık pozisyon varsa atla
            if any(p['ticker'] == ticker for p in open_positions):
                continue
            
            row = df.loc[date]
            
            if pd.isna(row['RSI']) or pd.isna(row['ATR']):
                continue
            
            score = calculate_score(row)
            
            if score >= min_score:
                # ATR-bazlı seviyeler al
                levels = get_atr_levels(ticker, row, df)
                
                signals.append({
                    'ticker': ticker,
                    'score': score,
                    'sector': sector,
                    **levels
                })
        
        if not signals:
            no_signal_days += 1
            continue
        
        # En iyi sinyalleri seç (skor sıralaması)
        signals.sort(key=lambda x: x['score'], reverse=True)
        
        # Sektör çeşitliliği ile seç
        selected = []
        for sig in signals:
            if len(selected) >= max_picks:
                break
            if sig['sector'] not in used_sectors_today:
                selected.append(sig)
                used_sectors_today.add(sig['sector'])
        
        # Pozisyonları aç
        for sig in selected:
            pos = {
                'ticker': sig['ticker'],
                'entry_date': date,
                'entry_price': sig['entry'],
                'stop_loss': sig['stop_loss'],
                'take_profit': sig['take_profit'],
                'sl_pct': sig['sl_pct'],
                'tp_pct': sig['tp_pct'],
                'max_hold': sig['max_hold'],
                'sector': sig['sector'],
                'score': sig['score'],
                'atr': sig['atr'],
                'atr_percent': sig['atr_percent'],
                'days_held': 0
            }
            open_positions.append(pos)
    
    # Açık pozisyonları kapat (backtest sonu)
    final_date = common_dates[-1]
    for pos in open_positions:
        ticker = pos['ticker']
        if ticker in stock_data and final_date in stock_data[ticker].index:
            row = stock_data[ticker].loc[final_date]
            pos['exit_date'] = final_date
            pos['exit_price'] = row['Close']
            pos['return_pct'] = ((pos['exit_price'] - pos['entry_price']) / pos['entry_price']) * 100
            pos['exit_reason'] = 'OPEN'
            pos['closed'] = True
            
            # Sektör istatistikleri
            sector = pos.get('sector', 'default')
            sector_stats[sector]['trades'] += 1
            sector_stats[sector]['total_return'] += pos['return_pct']
            if pos['return_pct'] > 0:
                sector_stats[sector]['wins'] += 1
            
            trades.append(pos)
    
    # Sonuçları hesapla
    if not trades:
        print("❌ Hiç işlem yapılmadı!")
        return None
    
    # Genel istatistikler
    total_trades = len(trades)
    winners = [t for t in trades if t['return_pct'] > 0]
    losers = [t for t in trades if t['return_pct'] <= 0]
    
    win_rate = (len(winners) / total_trades) * 100 if total_trades > 0 else 0
    total_return = sum(t['return_pct'] for t in trades)
    avg_return = total_return / total_trades if total_trades > 0 else 0
    
    avg_win = sum(t['return_pct'] for t in winners) / len(winners) if winners else 0
    avg_loss = sum(t['return_pct'] for t in losers) / len(losers) if losers else 0
    
    # Profit factor
    gross_profit = sum(t['return_pct'] for t in winners) if winners else 0
    gross_loss = abs(sum(t['return_pct'] for t in losers)) if losers else 1
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    # Max drawdown
    cumulative = 0
    peak = 0
    max_dd = 0
    for t in trades:
        cumulative += t['return_pct']
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd
    
    # Exit reason analizi
    exit_reasons = defaultdict(list)
    for t in trades:
        exit_reasons[t['exit_reason']].append(t['return_pct'])
    
    # Holding süresi
    holding_days = [t['days_held'] for t in trades if 'days_held' in t]
    avg_hold = sum(holding_days) / len(holding_days) if holding_days else 0
    
    print("=" * 65)
    print("📊 BACKTEST v3.0 ATR-BAZLI SONUÇLAR")
    print("=" * 65)
    print("📈 GENEL İSTATİSTİKLER:")
    print(f"   Toplam İşlem: {total_trades}")
    print(f"   Kazanan: {len(winners)} | Kaybeden: {len(losers)}")
    print(f"   Kazanma Oranı: %{win_rate:.1f}")
    print("💰 KAR/ZARAR:")
    print(f"   Toplam Getiri: %{total_return:.2f}")
    print(f"   Ortalama İşlem: %{avg_return:.2f}")
    print(f"   Ort. Kazanç: %{avg_win:.2f} | Ort. Kayıp: %{avg_loss:.2f}")
    print("📈 PERFORMANS:")
    print(f"   Profit Factor: {profit_factor:.2f}")
    print(f"   Max Drawdown: %{max_dd:.1f}")
    print("🛡️ FİLTRE ETKİSİ:")
    print(f"   Market Filter Blocked: {market_filter_blocks} gün")
    print(f"   No Signal Days: {no_signal_days} gün")
    
    print("📊 ÇIKIŞ NEDENİ ANALİZİ:")
    for reason, returns in exit_reasons.items():
        total_r = sum(returns)
        avg_r = total_r / len(returns)
        print(f"   {reason}: {len(returns)} işlem, %{total_r:.1f} toplam, %{avg_r:.2f} ort.")
    
    print("⏱️ HOLDING SÜRESİ:")
    print(f"   Ortalama: {avg_hold:.1f} gün")
    if holding_days:
        print(f"   Min: {min(holding_days)} gün | Max: {max(holding_days)} gün")
    
    # Sektör bazlı analiz
    print("=" * 65)
    print("📈 SEKTÖR BAZLI PERFORMANS:")
    print("-" * 65)
    for sector, stats in sorted(sector_stats.items(), key=lambda x: x[1]['total_return'], reverse=True):
        if stats['trades'] > 0:
            sector_wr = (stats['wins'] / stats['trades']) * 100
            avg_ret = stats['total_return'] / stats['trades']
            print(f"   {sector:20} | {stats['trades']:2} işlem | WR: %{sector_wr:5.1f} | Toplam: %{stats['total_return']:+6.1f} | Ort: %{avg_ret:+5.2f}")
    
    print("=" * 65)
    
    # Strateji değerlendirmesi
    if profit_factor >= 1.5 and win_rate >= 50:
        print("   ✅ GÜÇLÜ STRATEJİ - Canlı kullanıma hazır")
    elif profit_factor >= 1.2 and win_rate >= 45:
        print("   🟡 KABUL EDİLEBİLİR - Dikkatli kullanın")
    else:
        print("   🔴 ZAYIF - Optimizasyon gerekli")
    
    # Benchmark karşılaştırma
    if xu100 is not None and len(xu100) >= days:
        xu100_start = xu100['Close'].iloc[-days]
        xu100_end = xu100['Close'].iloc[-1]
        xu100_return = ((xu100_end - xu100_start) / xu100_start) * 100
        alpha = total_return - xu100_return
        print(f"📊 BENCHMARK (BIST100): %{xu100_return:.2f}")
        print(f"📊 ALPHA: %{alpha:+.2f}")
    
    print("=" * 65)
    
    # Son 10 işlem
    print("📝 SON 10 İŞLEM (ATR-bazlı seviyeleri ile):")
    print("-" * 90)
    for t in trades[-10:]:
        entry_d = t['entry_date'].strftime('%Y-%m-%d') if hasattr(t['entry_date'], 'strftime') else str(t['entry_date'])[:10]
        exit_d = t['exit_date'].strftime('%Y-%m-%d') if hasattr(t['exit_date'], 'strftime') else 'EOD'
        ret = t['return_pct']
        symbol = "🟢" if ret > 0 else "🔴"
        sector = t.get('sector', '?')[:8]
        atr_pct = t.get('atr_percent', 0)
        sl_pct = t.get('sl_pct', 0)
        tp_pct = t.get('tp_pct', 0)
        print(f"   {entry_d} | {t['ticker']:10} | {sector:8} | ATR:{atr_pct:4.1f}% | SL:{sl_pct:4.1f}% | TP:{tp_pct:4.1f}% | {symbol} %{ret:+5.2f} | {t['exit_reason']:12}")
    
    return {
        'trades': trades,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'total_return': total_return,
        'profit_factor': profit_factor,
        'max_drawdown': max_dd,
        'sector_stats': dict(sector_stats)
    }


def check_exit(pos, row, date):
    """Çıkış koşullarını kontrol et"""
    pos['days_held'] = pos.get('days_held', 0) + 1
    
    high = row['High']
    low = row['Low']
    close = row['Close']
    
    # Stop-loss kontrolü
    if low <= pos['stop_loss']:
        pos['exit_date'] = date
        pos['exit_price'] = pos['stop_loss']
        pos['return_pct'] = ((pos['exit_price'] - pos['entry_price']) / pos['entry_price']) * 100
        pos['exit_reason'] = 'STOP_LOSS'
        pos['closed'] = True
        return pos
    
    # Take-profit kontrolü
    if high >= pos['take_profit']:
        pos['exit_date'] = date
        pos['exit_price'] = pos['take_profit']
        pos['return_pct'] = ((pos['exit_price'] - pos['entry_price']) / pos['entry_price']) * 100
        pos['exit_reason'] = 'TAKE_PROFIT'
        pos['closed'] = True
        return pos
    
    # Max holding kontrolü (sektöre göre dinamik)
    max_hold = pos.get('max_hold', 10)
    if pos['days_held'] >= max_hold:
        pos['exit_date'] = date
        pos['exit_price'] = close
        pos['return_pct'] = ((pos['exit_price'] - pos['entry_price']) / pos['entry_price']) * 100
        pos['exit_reason'] = 'MAX_DAYS'
        pos['closed'] = True
        return pos
    
    # Trailing stop (kar %4'ü geçince)
    current_profit_pct = ((close - pos['entry_price']) / pos['entry_price']) * 100
    if current_profit_pct >= 4:
        # Trailing stop: %2 geri çekilme
        trailing_stop = close * 0.98
        if trailing_stop > pos['stop_loss']:
            pos['stop_loss'] = trailing_stop
    
    return pos


if __name__ == "__main__":
    print("=" * 65)
    print("🔬 ATR-BAZLI ADAPTİF STRATEJİ TESTİ")
    print("🔬 Her hisse için volatilitesine göre farklı SL/TP")
    print("=" * 65)
    
    import time
    
    # Test 1: Konservatif (75+ score)
    print("\n📊 TEST 1: CONSERVATIVE (75+ score, max 3 pick)")
    results1 = run_backtest_atr(days=90, min_score=75, max_picks=3)
    
    print("\n" + "=" * 65)
    time.sleep(5)  # Kısa bekleme
    
    # Test 2: Balanced (70+ score)
    print("\n📊 TEST 2: BALANCED (70+ score, max 4 pick)")
    results2 = run_backtest_atr(days=90, min_score=70, max_picks=4)
    
    # Karşılaştırma özeti
    print("\n" + "=" * 65)
    print("📈 KARŞILAŞTIRMA ÖZETİ")
    print("=" * 65)
    print(f"{'Test':<20} {'Trades':<8} {'Win %':<8} {'PF':<8} {'Return':<10}")
    print("-" * 65)
    
    if results1:
        print(f"{'Conservative (75+)':<20} {results1['total_trades']:<8} {results1['win_rate']:.1f}%{'':<3} {results1['profit_factor']:.2f}{'':<4} {results1['total_return']:+.2f}%")
    if results2:
        print(f"{'Balanced (70+)':<20} {results2['total_trades']:<8} {results2['win_rate']:.1f}%{'':<3} {results2['profit_factor']:.2f}{'':<4} {results2['total_return']:+.2f}%")
    
    print("=" * 65)
    print("\n✅ ATR-bazlı adaptif sistem her hisse için:")
    print("   - Volatil hisselere (THYAO, PGSUS) geniş SL (%3-5)")
    print("   - Defansif hisselere (BIMAS, TCELL) dar SL (%1.5-2.5)")
    print("   - Sektöre göre optimal holding süresi (7-15 gün)")
