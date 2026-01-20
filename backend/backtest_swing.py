#!/usr/bin/env python3
"""
BACKTEST v2.1 - SWING TRADİNG VERSİYONU
=======================================
- Score eşiği: 75+ 
- Stop-Loss: Teknik destek (~%3)
- Take-Profit: 1:2 R:R (%6-9)
- Holding süresi: 5-10 gün (swing)
- Market filtresi: BIST100 yükselişteyken
- Sektör çeşitlendirmesi
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Hisse sektörleri
STOCK_SECTORS = {
    "AKBNK.IS": "Bankacılık",
    "AKSEN.IS": "Enerji",
    "ARCLK.IS": "Dayanıklı Tüketim",
    "ASELS.IS": "Savunma",
    "BIMAS.IS": "Perakende",
    "EKGYO.IS": "GYO",
    "ENKAI.IS": "İnşaat",
    "EREGL.IS": "Demir Çelik",
    "FROTO.IS": "Otomotiv",
    "GARAN.IS": "Bankacılık",
    "GUBRF.IS": "Kimya",
    "HEKTS.IS": "Kimya",
    "ISCTR.IS": "Bankacılık",
    "KCHOL.IS": "Holding",
    "KRDMD.IS": "Demir Çelik",
    "ODAS.IS": "Enerji",
    "PETKM.IS": "Petrokimya",
    "PGSUS.IS": "Havacılık",
    "SAHOL.IS": "Holding",
    "SASA.IS": "Petrokimya",
    "SISE.IS": "Cam",
    "TAVHL.IS": "Havacılık",
    "TCELL.IS": "Telekomünikasyon",
    "THYAO.IS": "Havacılık",
    "TKFEN.IS": "Holding",
    "TOASO.IS": "Otomotiv",
    "TRALT.IS": "Altın",
    "TUPRS.IS": "Enerji",
    "YKBNK.IS": "Bankacılık",
}

# Test için hisse listesi
TEST_TICKERS = [
    "THYAO.IS", "GARAN.IS", "AKBNK.IS", "EREGL.IS", "ASELS.IS",
    "BIMAS.IS", "FROTO.IS", "KCHOL.IS", "SISE.IS", "TCELL.IS",
    "TUPRS.IS", "SAHOL.IS", "ISCTR.IS", "PGSUS.IS", "TOASO.IS"
]


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-10)
    return 100 - (100 / (1 + rs))


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    return prices.ewm(span=period, adjust=False).mean()


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def calculate_macd(prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)
    macd_line = ema12 - ema26
    signal_line = calculate_ema(macd_line, 9)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_score_v2(df: pd.DataFrame, idx: int) -> Dict:
    """
    V2 SKOR - SWING TRADING İÇİN OPTİMİZE
    """
    if idx < 50:
        return {'score': 0, 'valid': False}
    
    close = df['Close'].iloc[:idx+1]
    current_price = close.iloc[-1]
    
    ema_20 = calculate_ema(close, 20).iloc[-1]
    ema_50 = calculate_ema(close, 50).iloc[-1]
    rsi = calculate_rsi(close).iloc[-1]
    macd_line, signal_line, macd_hist = calculate_macd(close)
    macd_h = macd_hist.iloc[-1]
    
    if pd.isna(ema_20) or pd.isna(ema_50) or pd.isna(rsi):
        return {'score': 0, 'valid': False}
    
    score = 0
    signals = []
    
    # 1. TREND (35 pts) - Daha yüksek ağırlık
    if current_price > ema_20 and ema_20 > ema_50:
        score += 35
        signals.append("Güçlü Trend")
    elif current_price > ema_50 and ema_20 > ema_50:
        score += 25
        signals.append("Orta Trend")
    elif ema_20 > ema_50:
        score += 15
    
    # 2. RSI MOMENTUM (25 pts)
    if 45 <= rsi <= 65:  # Optimal bölge
        score += 25
        signals.append("RSI Optimal")
    elif 35 <= rsi < 45:  # Oversold'dan çıkış
        score += 20
        signals.append("RSI Toparlanma")
    elif 65 < rsi <= 75:
        score += 10
    
    # 3. MACD (20 pts)
    if macd_h > 0 and macd_line.iloc[-1] > macd_line.iloc[-2]:
        score += 20
        signals.append("MACD Pozitif")
    elif macd_h > 0:
        score += 10
    elif macd_h > macd_hist.iloc[-2]:  # Histogram artıyor
        score += 5
    
    # 4. EMA YAKINLIĞI (20 pts) - Pullback trade
    dist_to_ema20 = abs(current_price - ema_20) / current_price
    if current_price > ema_20 and dist_to_ema20 < 0.02:
        score += 20
        signals.append("EMA Yakın")
    elif current_price > ema_50 and dist_to_ema20 < 0.03:
        score += 15
    
    return {
        'score': score,
        'valid': True,
        'ema_20': ema_20,
        'ema_50': ema_50,
        'rsi': rsi,
        'signals': signals
    }


def check_market_trend(xu100_data: pd.DataFrame, date_idx: int) -> Tuple[bool, float]:
    """BIST100 trend ve güç"""
    if xu100_data is None or len(xu100_data) < 50:
        return True, 0
    
    close = xu100_data['Close'].iloc[:date_idx+1]
    if len(close) < 50:
        return True, 0
    
    ema_20 = calculate_ema(close, 20).iloc[-1]
    ema_50 = calculate_ema(close, 50).iloc[-1]
    current = close.iloc[-1]
    
    is_uptrend = ema_20 > ema_50
    strength = (current - ema_50) / ema_50 * 100  # % mesafe
    
    return is_uptrend, strength


def apply_sector_diversification(candidates: List[Dict], max_picks: int) -> List[Dict]:
    selected = []
    used_sectors = set()
    
    for c in candidates:
        sector = STOCK_SECTORS.get(c['ticker'], 'Diğer')
        if sector not in used_sectors:
            selected.append(c)
            used_sectors.add(sector)
            if len(selected) >= max_picks:
                break
    
    if len(selected) < max_picks:
        for c in candidates:
            if c not in selected:
                selected.append(c)
                if len(selected) >= max_picks:
                    break
    
    return selected


def simulate_swing_trade(df: pd.DataFrame, entry_idx: int, entry_price: float, 
                          stop_loss: float, take_profit: float, 
                          max_days: int = 10) -> Dict:
    """
    SWING TRADE SİMÜLASYONU
    - Max 10 gün holding
    - Trailing stop aktivasyonu
    """
    for day_offset in range(1, min(max_days + 1, len(df) - entry_idx)):
        current_idx = entry_idx + day_offset
        if current_idx >= len(df):
            break
        
        day_data = df.iloc[current_idx]
        high = day_data['High']
        low = day_data['Low']
        close = day_data['Close']
        
        # Stop-loss kontrolü (önce)
        if low <= stop_loss:
            return {
                'exit_price': stop_loss,
                'exit_reason': 'STOP_LOSS',
                'holding_days': day_offset,
                'pnl_pct': (stop_loss - entry_price) / entry_price * 100
            }
        
        # Take-profit kontrolü
        if high >= take_profit:
            return {
                'exit_price': take_profit,
                'exit_reason': 'TAKE_PROFIT',
                'holding_days': day_offset,
                'pnl_pct': (take_profit - entry_price) / entry_price * 100
            }
        
        # Trailing stop: %4+ kar'da, stop'u breakeven'a taşı
        current_pnl = (close - entry_price) / entry_price * 100
        if current_pnl >= 4.0:
            stop_loss = max(stop_loss, entry_price * 1.001)  # Breakeven + komisyon
    
    # Max gün doldu - EOD çıkış
    final_close = df['Close'].iloc[min(entry_idx + max_days, len(df) - 1)]
    return {
        'exit_price': final_close,
        'exit_reason': 'MAX_DAYS',
        'holding_days': max_days,
        'pnl_pct': (final_close - entry_price) / entry_price * 100
    }


def run_backtest_swing(days: int = 90, min_score: int = 75, max_picks: int = 3):
    """
    SWING TRADING BACKTEST
    """
    print("\n" + "="*65)
    print("🚀 BACKTEST v2.1 - SWING TRADING STRATEJİSİ")
    print("="*65)
    print(f"📅 Test Süresi: {days} gün")
    print(f"🎯 Min Score: {min_score}+")
    print(f"📊 Max Picks/Hafta: {max_picks}")
    print(f"⛔ Stop-Loss: %3 (teknik)")
    print(f"🎯 Take-Profit: %6-9 (1:2 R:R)")
    print(f"⏱️ Max Holding: 10 gün")
    print(f"📈 Market Filtresi: BIST100 uptrend")
    print("="*65)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days + 60)
    
    print(f"\n📥 Veri çekiliyor ({len(TEST_TICKERS)} hisse)...")
    
    all_data = {}
    for ticker in TEST_TICKERS:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                all_data[ticker] = df
        except Exception as e:
            print(f"  ❌ {ticker}: {e}")
    
    print("📥 BIST100 verisi çekiliyor...")
    try:
        xu100 = yf.download("XU100.IS", start=start_date, end=end_date, progress=False)
        if isinstance(xu100.columns, pd.MultiIndex):
            xu100.columns = xu100.columns.get_level_values(0)
    except:
        xu100 = None
    
    print(f"✅ {len(all_data)} hisse yüklendi\n")
    
    # Trading state
    trades = []
    active_positions = {}  # {ticker: {entry_idx, entry_price, sl, tp}}
    market_blocked_days = 0
    no_signal_days = 0
    
    reference_ticker = list(all_data.keys())[0]
    trading_days = all_data[reference_ticker].index[-days:]
    
    for day_idx, trade_date in enumerate(trading_days):
        # Aktif pozisyonları kontrol et
        closed_tickers = []
        for ticker, pos in list(active_positions.items()):
            df = all_data[ticker]
            if trade_date not in df.index:
                continue
            
            current_idx = df.index.get_loc(trade_date)
            days_held = current_idx - pos['entry_idx']
            
            if days_held >= 10:  # Max holding
                exit_price = df['Close'].iloc[current_idx]
                pnl = (exit_price - pos['entry_price']) / pos['entry_price'] * 100
                trades.append({
                    'date': pos['entry_date'],
                    'exit_date': trade_date.strftime('%Y-%m-%d'),
                    'ticker': ticker,
                    'sector': STOCK_SECTORS.get(ticker, 'Diğer'),
                    'score': pos['score'],
                    'entry': round(pos['entry_price'], 2),
                    'sl': round(pos['stop_loss'], 2),
                    'tp': round(pos['take_profit'], 2),
                    'exit': round(exit_price, 2),
                    'exit_reason': 'MAX_DAYS',
                    'holding_days': days_held,
                    'pnl_pct': round(pnl, 2)
                })
                closed_tickers.append(ticker)
                continue
            
            day_data = df.iloc[current_idx]
            
            # Stop-loss check
            if day_data['Low'] <= pos['stop_loss']:
                pnl = (pos['stop_loss'] - pos['entry_price']) / pos['entry_price'] * 100
                trades.append({
                    'date': pos['entry_date'],
                    'exit_date': trade_date.strftime('%Y-%m-%d'),
                    'ticker': ticker,
                    'sector': STOCK_SECTORS.get(ticker, 'Diğer'),
                    'score': pos['score'],
                    'entry': round(pos['entry_price'], 2),
                    'sl': round(pos['stop_loss'], 2),
                    'tp': round(pos['take_profit'], 2),
                    'exit': round(pos['stop_loss'], 2),
                    'exit_reason': 'STOP_LOSS',
                    'holding_days': days_held,
                    'pnl_pct': round(pnl, 2)
                })
                closed_tickers.append(ticker)
                continue
            
            # Take-profit check
            if day_data['High'] >= pos['take_profit']:
                pnl = (pos['take_profit'] - pos['entry_price']) / pos['entry_price'] * 100
                trades.append({
                    'date': pos['entry_date'],
                    'exit_date': trade_date.strftime('%Y-%m-%d'),
                    'ticker': ticker,
                    'sector': STOCK_SECTORS.get(ticker, 'Diğer'),
                    'score': pos['score'],
                    'entry': round(pos['entry_price'], 2),
                    'sl': round(pos['stop_loss'], 2),
                    'tp': round(pos['take_profit'], 2),
                    'exit': round(pos['take_profit'], 2),
                    'exit_reason': 'TAKE_PROFIT',
                    'holding_days': days_held,
                    'pnl_pct': round(pnl, 2)
                })
                closed_tickers.append(ticker)
                continue
            
            # Trailing stop: %4+ kar'da breakeven
            current_pnl = (day_data['Close'] - pos['entry_price']) / pos['entry_price'] * 100
            if current_pnl >= 4.0:
                pos['stop_loss'] = max(pos['stop_loss'], pos['entry_price'] * 1.005)
        
        for t in closed_tickers:
            del active_positions[t]
        
        # Haftalık yeni pozisyon açma (pazartesi veya pozisyon boşsa)
        if len(active_positions) >= max_picks:
            continue
        
        # Market filtresi
        if xu100 is not None:
            xu100_idx = xu100.index.get_indexer([trade_date], method='ffill')[0]
            if xu100_idx >= 0:
                is_uptrend, strength = check_market_trend(xu100, xu100_idx)
                if not is_uptrend:
                    market_blocked_days += 1
                    continue
        
        # Sinyal ara
        daily_candidates = []
        
        for ticker, df in all_data.items():
            if ticker in active_positions:
                continue
            
            if trade_date not in df.index:
                continue
            
            idx = df.index.get_loc(trade_date)
            if idx < 50:
                continue
            
            score_data = calculate_score_v2(df, idx)
            
            if score_data['valid'] and score_data['score'] >= min_score:
                entry_price = df['Close'].iloc[idx]
                
                # %3 SL, %6 TP (1:2 R:R)
                stop_loss = entry_price * 0.97
                take_profit = entry_price * 1.06
                
                daily_candidates.append({
                    'ticker': ticker,
                    'score': score_data['score'],
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'signals': score_data.get('signals', []),
                    'idx': idx
                })
        
        if not daily_candidates:
            no_signal_days += 1
            continue
        
        daily_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Sektör çeşitlendirmesi
        slots_available = max_picks - len(active_positions)
        selected = apply_sector_diversification(daily_candidates, slots_available)
        
        # Pozisyon aç
        for pick in selected:
            ticker = pick['ticker']
            active_positions[ticker] = {
                'entry_idx': pick['idx'],
                'entry_date': trade_date.strftime('%Y-%m-%d'),
                'entry_price': pick['entry_price'],
                'stop_loss': pick['stop_loss'],
                'take_profit': pick['take_profit'],
                'score': pick['score']
            }
    
    # Kalan açık pozisyonları kapat
    for ticker, pos in active_positions.items():
        df = all_data[ticker]
        exit_price = df['Close'].iloc[-1]
        pnl = (exit_price - pos['entry_price']) / pos['entry_price'] * 100
        trades.append({
            'date': pos['entry_date'],
            'exit_date': 'EOD',
            'ticker': ticker,
            'sector': STOCK_SECTORS.get(ticker, 'Diğer'),
            'score': pos['score'],
            'entry': round(pos['entry_price'], 2),
            'sl': round(pos['stop_loss'], 2),
            'tp': round(pos['take_profit'], 2),
            'exit': round(exit_price, 2),
            'exit_reason': 'OPEN',
            'holding_days': 0,
            'pnl_pct': round(pnl, 2)
        })
    
    # Sonuçlar
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t['pnl_pct'] > 0)
    losing_trades = sum(1 for t in trades if t['pnl_pct'] <= 0)
    
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    total_pnl = sum(t['pnl_pct'] for t in trades)
    
    gross_profit = sum(t['pnl_pct'] for t in trades if t['pnl_pct'] > 0)
    gross_loss = abs(sum(t['pnl_pct'] for t in trades if t['pnl_pct'] < 0))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    avg_win = gross_profit / winning_trades if winning_trades > 0 else 0
    avg_loss = gross_loss / losing_trades if losing_trades > 0 else 0
    
    # Max Drawdown
    cumulative = 0
    peak = 0
    max_dd = 0
    for t in trades:
        cumulative += t['pnl_pct']
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd
    
    print("\n" + "="*65)
    print("📊 BACKTEST v2.1 SWING TRADING SONUÇLARI")
    print("="*65)
    
    print(f"\n📈 GENEL İSTATİSTİKLER:")
    print(f"   Toplam İşlem: {total_trades}")
    print(f"   Kazanan: {winning_trades} | Kaybeden: {losing_trades}")
    print(f"   Kazanma Oranı: %{win_rate:.1f}")
    
    print(f"\n💰 KAR/ZARAR:")
    print(f"   Toplam Getiri: %{total_pnl:.2f}")
    print(f"   Ortalama İşlem: %{total_pnl/total_trades:.2f}" if total_trades > 0 else "   N/A")
    print(f"   Ort. Kazanç: %{avg_win:.2f} | Ort. Kayıp: %{avg_loss:.2f}")
    
    print(f"\n📈 PERFORMANS:")
    print(f"   Profit Factor: {profit_factor:.2f}")
    print(f"   Max Drawdown: %{max_dd:.1f}")
    
    print(f"\n🛡️ FİLTRE ETKİSİ:")
    print(f"   Market Filter Blocked: {market_blocked_days} gün")
    print(f"   No Signal Days: {no_signal_days} gün")
    
    # Exit reason analizi
    print(f"\n📊 ÇIKIŞ NEDENİ ANALİZİ:")
    exit_stats = {}
    for t in trades:
        reason = t['exit_reason']
        if reason not in exit_stats:
            exit_stats[reason] = {'count': 0, 'pnl': 0}
        exit_stats[reason]['count'] += 1
        exit_stats[reason]['pnl'] += t['pnl_pct']
    
    for reason, data in sorted(exit_stats.items(), key=lambda x: x[1]['pnl'], reverse=True):
        avg = data['pnl'] / data['count'] if data['count'] > 0 else 0
        print(f"   {reason}: {data['count']} işlem, %{data['pnl']:.1f} toplam, %{avg:.2f} ort.")
    
    # Holding days analizi
    holding_days = [t['holding_days'] for t in trades if t['holding_days'] > 0]
    if holding_days:
        print(f"\n⏱️ HOLDING SÜRESİ:")
        print(f"   Ortalama: {np.mean(holding_days):.1f} gün")
        print(f"   Min: {min(holding_days)} gün | Max: {max(holding_days)} gün")
    
    # Değerlendirme
    print("\n" + "="*65)
    print("🎯 STRATEJİ DEĞERLENDİRMESİ:")
    
    if profit_factor >= 1.5 and win_rate >= 50:
        print("   ✅ GÜÇLÜ STRATEJİ - Canlı kullanıma hazır")
    elif profit_factor >= 1.2 and win_rate >= 45:
        print("   🟡 KABUL EDİLEBİLİR - Dikkatli kullanın")
    else:
        print("   ❌ ZAYIF - Daha fazla optimizasyon gerekli")
    
    # Benchmark
    if xu100 is not None:
        xu100_start = xu100['Close'].iloc[-days]
        xu100_end = xu100['Close'].iloc[-1]
        xu100_return = (xu100_end - xu100_start) / xu100_start * 100
        print(f"\n📊 BENCHMARK (BIST100): %{xu100_return:.2f}")
        alpha = total_pnl - xu100_return
        print(f"📊 ALPHA: %{alpha:.2f}")
    
    print("="*65 + "\n")
    
    # Son işlemler
    print("📝 SON 10 İŞLEM:")
    print("-"*90)
    for t in trades[-10:]:
        emoji = "🟢" if t['pnl_pct'] > 0 else "🔴"
        print(f"   {t['date']} → {t.get('exit_date','?'):<10} | {t['ticker']:<8} | {emoji} %{t['pnl_pct']:>+5.2f} | {t['exit_reason']:<10} | {t['holding_days']}d")
    
    return {
        'total_trades': total_trades,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'profit_factor': profit_factor,
        'max_drawdown': max_dd,
        'trades': trades
    }


if __name__ == "__main__":
    # Farklı parametrelerle test
    print("\n" + "🔬 "*20)
    print("PARAMETRE OPTİMİZASYONU")
    print("🔬 "*20)
    
    # Test 1: Conservative (75 score, 3 picks)
    print("\n\n📊 TEST 1: CONSERVATIVE (75+ score, 3 picks)")
    results1 = run_backtest_swing(days=90, min_score=75, max_picks=3)
    
    # Test 2: Balanced (70 score, 3 picks)
    print("\n\n📊 TEST 2: BALANCED (70+ score, 3 picks)")
    results2 = run_backtest_swing(days=90, min_score=70, max_picks=3)
    
    # Test 3: Aggressive (65 score, 5 picks)
    print("\n\n📊 TEST 3: AGGRESSIVE (65+ score, 5 picks)")
    results3 = run_backtest_swing(days=90, min_score=65, max_picks=5)
    
    # Karşılaştırma
    print("\n" + "="*65)
    print("📊 PARAMETRE KARŞILAŞTIRMASI")
    print("="*65)
    print(f"{'Strateji':<15} | {'İşlem':<6} | {'Win%':<6} | {'Getiri':<8} | {'PF':<5} | {'DD':<5}")
    print("-"*65)
    print(f"{'CONSERVATIVE':<15} | {results1['total_trades']:<6} | {results1['win_rate']:<5.1f}% | {results1['total_pnl']:<7.1f}% | {results1['profit_factor']:<5.2f} | {results1['max_drawdown']:<4.1f}%")
    print(f"{'BALANCED':<15} | {results2['total_trades']:<6} | {results2['win_rate']:<5.1f}% | {results2['total_pnl']:<7.1f}% | {results2['profit_factor']:<5.2f} | {results2['max_drawdown']:<4.1f}%")
    print(f"{'AGGRESSIVE':<15} | {results3['total_trades']:<6} | {results3['win_rate']:<5.1f}% | {results3['total_pnl']:<7.1f}% | {results3['profit_factor']:<5.2f} | {results3['max_drawdown']:<4.1f}%")
    print("="*65)
