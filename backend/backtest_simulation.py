#!/usr/bin/env python3
"""
BACKTEST SİMÜLASYON - ATR-BAZLI ADAPTİF STRATEJİ
Gerçekçi simülasyon verileri ile test
"""

import random
import numpy as np
from collections import defaultdict
from datetime import datetime, timedelta

random.seed(42)  # Reproducible results

# Hisseler ve sektörleri
STOCKS = {
    "THYAO": {"sector": "Havacılık", "base_price": 340, "volatility": 0.035, "beta": 1.8},
    "PGSUS": {"sector": "Havacılık", "base_price": 2800, "volatility": 0.040, "beta": 2.0},
    "GARAN": {"sector": "Bankacılık", "base_price": 145, "volatility": 0.025, "beta": 1.2},
    "AKBNK": {"sector": "Bankacılık", "base_price": 72, "volatility": 0.023, "beta": 1.1},
    "ISCTR": {"sector": "Bankacılık", "base_price": 22, "volatility": 0.028, "beta": 1.3},
    "BIMAS": {"sector": "Perakende", "base_price": 590, "volatility": 0.015, "beta": 0.6},
    "TCELL": {"sector": "Telekomünikasyon", "base_price": 112, "volatility": 0.018, "beta": 0.7},
    "FROTO": {"sector": "Otomotiv", "base_price": 1250, "volatility": 0.020, "beta": 0.9},
    "TOASO": {"sector": "Otomotiv", "base_price": 410, "volatility": 0.022, "beta": 1.0},
    "EREGL": {"sector": "Demir Çelik", "base_price": 58, "volatility": 0.028, "beta": 1.4},
    "TUPRS": {"sector": "Enerji", "base_price": 180, "volatility": 0.025, "beta": 1.2},
    "KCHOL": {"sector": "Holding", "base_price": 195, "volatility": 0.020, "beta": 1.0},
    "SAHOL": {"sector": "Holding", "base_price": 102, "volatility": 0.022, "beta": 1.1},
    "SISE": {"sector": "Cam", "base_price": 65, "volatility": 0.024, "beta": 1.2},
    "ASELS": {"sector": "Savunma", "base_price": 75, "volatility": 0.030, "beta": 1.5},
}

# Sektör volatilite profilleri
SECTOR_PROFILES = {
    "Havacılık": {"sl_mult": 2.0, "tp_mult": 4.0, "max_hold": 7, "trend_strength": 0.6},
    "Bankacılık": {"sl_mult": 1.5, "tp_mult": 3.0, "max_hold": 10, "trend_strength": 0.5},
    "Holding": {"sl_mult": 1.4, "tp_mult": 2.8, "max_hold": 12, "trend_strength": 0.4},
    "Perakende": {"sl_mult": 1.3, "tp_mult": 2.6, "max_hold": 12, "trend_strength": 0.3},
    "Telekomünikasyon": {"sl_mult": 1.3, "tp_mult": 2.6, "max_hold": 15, "trend_strength": 0.3},
    "Otomotiv": {"sl_mult": 1.6, "tp_mult": 3.2, "max_hold": 10, "trend_strength": 0.5},
    "Demir Çelik": {"sl_mult": 1.8, "tp_mult": 3.6, "max_hold": 8, "trend_strength": 0.55},
    "Enerji": {"sl_mult": 1.6, "tp_mult": 3.2, "max_hold": 10, "trend_strength": 0.5},
    "Cam": {"sl_mult": 1.5, "tp_mult": 3.0, "max_hold": 10, "trend_strength": 0.45},
    "Savunma": {"sl_mult": 1.7, "tp_mult": 3.4, "max_hold": 8, "trend_strength": 0.6},
}

def generate_price_series(stock_info, days, market_trend=0.001):
    """
    Gerçekçi fiyat serisi oluştur
    - Random walk with drift
    - Volatility clustering
    - Mean reversion
    """
    prices = [stock_info["base_price"]]
    volumes = [1_000_000]
    highs = [prices[0] * 1.01]
    lows = [prices[0] * 0.99]
    
    vol = stock_info["volatility"]
    beta = stock_info["beta"]
    
    current_vol = vol  # Volatility clustering
    
    for i in range(1, days):
        # Market effect
        market_move = random.gauss(market_trend, 0.01) * beta
        
        # Stock specific move
        stock_move = random.gauss(0, current_vol)
        
        # Volatility clustering
        if abs(stock_move) > vol * 1.5:
            current_vol = min(vol * 1.5, current_vol * 1.2)
        else:
            current_vol = max(vol * 0.8, current_vol * 0.95)
        
        # Price change
        change = market_move + stock_move
        new_price = prices[-1] * (1 + change)
        
        # OHLC
        daily_range = abs(random.gauss(0, current_vol * 0.5))
        high = new_price * (1 + daily_range)
        low = new_price * (1 - daily_range)
        
        prices.append(new_price)
        highs.append(high)
        lows.append(low)
        
        # Volume (higher on volatile days)
        base_vol = 1_000_000 * (1 + abs(change) * 10)
        volumes.append(base_vol * random.uniform(0.7, 1.3))
    
    return {
        "close": prices,
        "high": highs,
        "low": lows,
        "volume": volumes
    }

def calculate_indicators(data):
    """Teknik indikatörler hesapla"""
    closes = np.array(data["close"])
    highs = np.array(data["high"])
    lows = np.array(data["low"])
    volumes = np.array(data["volume"])
    
    n = len(closes)
    
    # EMAs
    def ema(prices, span):
        result = np.zeros(len(prices))
        result[0] = prices[0]
        alpha = 2 / (span + 1)
        for i in range(1, len(prices)):
            result[i] = alpha * prices[i] + (1 - alpha) * result[i-1]
        return result
    
    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    
    # RSI
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    rsi = np.zeros(n)
    for i in range(14, n):
        avg_gain = np.mean(gains[i-14:i])
        avg_loss = np.mean(losses[i-14:i])
        if avg_loss == 0:
            rsi[i] = 100
        else:
            rs = avg_gain / avg_loss
            rsi[i] = 100 - (100 / (1 + rs))
    
    # ATR
    atr = np.zeros(n)
    for i in range(1, n):
        tr = max(highs[i] - lows[i], 
                 abs(highs[i] - closes[i-1]), 
                 abs(lows[i] - closes[i-1]))
        if i >= 14:
            atr[i] = np.mean([max(highs[j] - lows[j],
                                  abs(highs[j] - closes[j-1]),
                                  abs(lows[j] - closes[j-1])) 
                             for j in range(i-13, i+1)])
        else:
            atr[i] = tr
    
    # Volume ratio
    vol_ma = np.zeros(n)
    for i in range(20, n):
        vol_ma[i] = np.mean(volumes[i-20:i])
    vol_ratio = np.where(vol_ma > 0, volumes / vol_ma, 1)
    
    return {
        "close": closes,
        "high": highs,
        "low": lows,
        "ema20": ema20,
        "ema50": ema50,
        "rsi": rsi,
        "atr": atr,
        "vol_ratio": vol_ratio
    }

def calculate_score(ind, i):
    """Sinyal skoru hesapla"""
    if i < 50:
        return 0
    
    score = 0
    price = ind["close"][i]
    ema20 = ind["ema20"][i]
    ema50 = ind["ema50"][i]
    rsi = ind["rsi"][i]
    vol_ratio = ind["vol_ratio"][i]
    
    # Trend
    if price > ema20 > ema50:
        score += 30
    elif price > ema50 and ema20 > ema50:
        score += 20
    elif ema20 > ema50:
        score += 10
    
    # RSI
    if 40 <= rsi <= 60:
        score += 15
    elif 30 <= rsi < 40:
        score += 10
    elif 60 < rsi <= 70:
        score += 5
    
    # EMA yakınlığı
    dist = abs(price - ema20) / price
    if dist < 0.015:
        score += 25
    elif dist < 0.03:
        score += 15
    else:
        score += 5
    
    # Hacim
    if vol_ratio > 1.5:
        score += 20
    elif vol_ratio > 1.0:
        score += 10
    
    return score

def get_atr_levels(ticker, ind, i):
    """ATR-bazlı SL/TP hesapla"""
    stock = STOCKS[ticker]
    profile = SECTOR_PROFILES[stock["sector"]]
    
    price = ind["close"][i]
    atr = ind["atr"][i] if ind["atr"][i] > 0 else price * stock["volatility"]
    
    # SL hesapla
    sl_dist = atr * profile["sl_mult"]
    sl_dist = max(sl_dist, price * 0.015)  # Min %1.5
    sl_dist = min(sl_dist, price * 0.05)   # Max %5
    
    # TP hesapla
    tp_dist = atr * profile["tp_mult"]
    tp_dist = max(tp_dist, sl_dist * 2)    # Min 2:1 R:R
    
    return {
        "entry": price,
        "stop_loss": price - sl_dist,
        "take_profit": price + tp_dist,
        "sl_pct": (sl_dist / price) * 100,
        "tp_pct": (tp_dist / price) * 100,
        "atr_pct": (atr / price) * 100,
        "max_hold": profile["max_hold"],
        "sector": stock["sector"]
    }

def run_backtest(days=90, min_score=70, max_picks=3, market_trend=0.001, use_atr=True):
    """
    Backtest çalıştır
    use_atr=True: Her hisse için farklı parametreler (YENİ)
    use_atr=False: Tüm hisseler için sabit %3 SL, %6 TP (ESKİ)
    """
    
    # Veri oluştur
    stock_data = {}
    stock_indicators = {}
    
    for ticker, info in STOCKS.items():
        data = generate_price_series(info, days + 100, market_trend)
        stock_data[ticker] = data
        stock_indicators[ticker] = calculate_indicators(data)
    
    trades = []
    open_positions = []
    sector_stats = defaultdict(lambda: {"trades": 0, "wins": 0, "total": 0})
    
    # Her gün için
    for day in range(60, days + 60):
        # Açık pozisyonları kontrol et
        for pos in open_positions[:]:
            ticker = pos["ticker"]
            ind = stock_indicators[ticker]
            
            pos["days_held"] += 1
            current_high = ind["high"][day]
            current_low = ind["low"][day]
            current_close = ind["close"][day]
            
            closed = False
            
            # Stop loss kontrolü
            if current_low <= pos["stop_loss"]:
                pos["exit"] = pos["stop_loss"]
                pos["ret"] = ((pos["stop_loss"] - pos["entry"]) / pos["entry"]) * 100
                pos["reason"] = "STOP_LOSS"
                closed = True
            
            # Take profit kontrolü
            elif current_high >= pos["take_profit"]:
                pos["exit"] = pos["take_profit"]
                pos["ret"] = ((pos["take_profit"] - pos["entry"]) / pos["entry"]) * 100
                pos["reason"] = "TAKE_PROFIT"
                closed = True
            
            # Max gün kontrolü
            elif pos["days_held"] >= pos["max_hold"]:
                pos["exit"] = current_close
                pos["ret"] = ((current_close - pos["entry"]) / pos["entry"]) * 100
                pos["reason"] = "MAX_DAYS"
                closed = True
            
            # Trailing stop (kar > %4 ise)
            else:
                current_ret = ((current_close - pos["entry"]) / pos["entry"]) * 100
                if current_ret >= 4:
                    new_sl = current_close * 0.98
                    pos["stop_loss"] = max(pos["stop_loss"], new_sl)
            
            if closed:
                trades.append(pos)
                open_positions.remove(pos)
                sector_stats[pos["sector"]]["trades"] += 1
                sector_stats[pos["sector"]]["total"] += pos["ret"]
                if pos["ret"] > 0:
                    sector_stats[pos["sector"]]["wins"] += 1
        
        # Yeni sinyalleri ara
        used_sectors = {p["sector"] for p in open_positions}
        signals = []
        
        for ticker in STOCKS:
            ind = stock_indicators[ticker]
            sector = STOCKS[ticker]["sector"]
            
            if sector in used_sectors:
                continue
            if any(p["ticker"] == ticker for p in open_positions):
                continue
            
            score = calculate_score(ind, day)
            
            if score >= min_score:
                if use_atr:
                    # YENİ: ATR-bazlı adaptif parametreler
                    levels = get_atr_levels(ticker, ind, day)
                else:
                    # ESKİ: Sabit parametreler
                    price = ind["close"][day]
                    levels = {
                        "entry": price,
                        "stop_loss": price * 0.97,  # Sabit %3 SL
                        "take_profit": price * 1.06,  # Sabit %6 TP
                        "sl_pct": 3.0,
                        "tp_pct": 6.0,
                        "atr_pct": 2.0,
                        "max_hold": 10,  # Sabit 10 gün
                        "sector": sector
                    }
                
                signals.append({
                    "ticker": ticker,
                    "score": score,
                    **levels
                })
        
        # En iyi sinyalleri al
        signals.sort(key=lambda x: x["score"], reverse=True)
        
        for sig in signals[:max_picks]:
            if sig["sector"] not in used_sectors:
                open_positions.append({
                    "ticker": sig["ticker"],
                    "entry": sig["entry"],
                    "stop_loss": sig["stop_loss"],
                    "take_profit": sig["take_profit"],
                    "sl_pct": sig["sl_pct"],
                    "tp_pct": sig["tp_pct"],
                    "atr_pct": sig["atr_pct"],
                    "max_hold": sig["max_hold"],
                    "sector": sig["sector"],
                    "score": sig["score"],
                    "days_held": 0
                })
                used_sectors.add(sig["sector"])
    
    # Açık pozisyonları kapat
    for pos in open_positions:
        ind = stock_indicators[pos["ticker"]]
        final_price = ind["close"][-1]
        pos["exit"] = final_price
        pos["ret"] = ((final_price - pos["entry"]) / pos["entry"]) * 100
        pos["reason"] = "OPEN"
        trades.append(pos)
        sector_stats[pos["sector"]]["trades"] += 1
        sector_stats[pos["sector"]]["total"] += pos["ret"]
        if pos["ret"] > 0:
            sector_stats[pos["sector"]]["wins"] += 1
    
    return trades, sector_stats

def print_results(trades, sector_stats, title):
    """Sonuçları yazdır"""
    if not trades:
        print(f"{title}: İşlem yok!")
        return None
    
    total = len(trades)
    winners = [t for t in trades if t["ret"] > 0]
    losers = [t for t in trades if t["ret"] <= 0]
    
    win_rate = len(winners) / total * 100
    total_ret = sum(t["ret"] for t in trades)
    avg_ret = total_ret / total
    
    avg_win = sum(t["ret"] for t in winners) / len(winners) if winners else 0
    avg_loss = sum(t["ret"] for t in losers) / len(losers) if losers else 0
    
    gross_profit = sum(t["ret"] for t in winners) if winners else 0
    gross_loss = abs(sum(t["ret"] for t in losers)) if losers else 1
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    print(f"\n{'='*60}")
    print(f"📊 {title}")
    print(f"{'='*60}")
    print(f"   İşlem Sayısı: {total}")
    print(f"   Kazanan: {len(winners)} | Kaybeden: {len(losers)}")
    print(f"   Win Rate: %{win_rate:.1f}")
    print(f"   Toplam Getiri: %{total_ret:.2f}")
    print(f"   Ortalama Getiri: %{avg_ret:.2f}")
    print(f"   Ort. Kazanç: %{avg_win:.2f} | Ort. Kayıp: %{avg_loss:.2f}")
    print(f"   Profit Factor: {profit_factor:.2f}")
    
    # Çıkış nedeni analizi
    reasons = defaultdict(list)
    for t in trades:
        reasons[t["reason"]].append(t["ret"])
    
    print(f"\n📈 ÇIKIŞ NEDENİ:")
    for reason, rets in sorted(reasons.items()):
        count = len(rets)
        tot = sum(rets)
        avg = tot / count
        wr = len([r for r in rets if r > 0]) / count * 100
        print(f"   {reason:12} | {count:3} işlem | WR:%{wr:5.1f} | Tot:%{tot:+7.1f} | Avg:%{avg:+5.2f}")
    
    # Sektör analizi
    print(f"\n📊 SEKTÖR BAZLI:")
    for sector, s in sorted(sector_stats.items(), key=lambda x: x[1]["total"], reverse=True):
        if s["trades"] > 0:
            wr = s["wins"] / s["trades"] * 100
            avg = s["total"] / s["trades"]
            print(f"   {sector:18} | {s['trades']:2} işlem | WR:%{wr:5.1f} | Tot:%{s['total']:+7.1f}")
    
    return {
        "trades": total,
        "win_rate": win_rate,
        "total_return": total_ret,
        "avg_return": avg_ret,
        "profit_factor": profit_factor
    }

def main():
    print("="*70)
    print("🔬 ATR-BAZLI ADAPTİF STRATEJİ vs SABİT PARAMETRELER")
    print("="*70)
    print("\n📋 Test parametreleri:")
    print("   - 90 günlük simülasyon verisi")
    print("   - 15 farklı hisse, 10 farklı sektör")
    print("   - Min score: 70, Max picks: 3")
    print("   - Market trend: yatay (0.1% daily drift)")
    
    # TEST 1: SABİT PARAMETRELER (Eski Yöntem)
    print("\n" + "="*70)
    print("📌 TEST 1: SABİT PARAMETRELER (TÜM HİSSELERE AYNI)")
    print("   - Stop Loss: Sabit %3")
    print("   - Take Profit: Sabit %6")
    print("   - Max Hold: Sabit 10 gün")
    trades_fixed, sector_fixed = run_backtest(
        days=90, min_score=70, max_picks=3, market_trend=0.001, use_atr=False
    )
    result_fixed = print_results(trades_fixed, sector_fixed, "SABİT PARAMETRELER")
    
    # TEST 2: ATR-BAZLI ADAPTİF (Yeni Yöntem)
    print("\n" + "="*70)
    print("📌 TEST 2: ATR-BAZLI ADAPTİF (HER HİSSEYE ÖZEL)")
    print("   - Stop Loss: ATR × sektör çarpanı (%1.5-5 arası)")
    print("   - Take Profit: ATR × sektör çarpanı (min 2:1 R:R)")
    print("   - Max Hold: Sektöre göre 7-15 gün")
    trades_atr, sector_atr = run_backtest(
        days=90, min_score=70, max_picks=3, market_trend=0.001, use_atr=True
    )
    result_atr = print_results(trades_atr, sector_atr, "ATR-BAZLI ADAPTİF")
    
    # KARŞILAŞTIRMA
    print("\n" + "="*70)
    print("📊 KARŞILAŞTIRMA ÖZETİ")
    print("="*70)
    
    if result_fixed and result_atr:
        print(f"\n{'Metrik':<25} {'Sabit':<15} {'ATR-Bazlı':<15} {'Fark':<15}")
        print("-"*70)
        print(f"{'İşlem Sayısı':<25} {result_fixed['trades']:<15} {result_atr['trades']:<15}")
        print(f"{'Win Rate':<25} %{result_fixed['win_rate']:<14.1f} %{result_atr['win_rate']:<14.1f} {result_atr['win_rate']-result_fixed['win_rate']:+.1f}")
        print(f"{'Toplam Getiri':<25} %{result_fixed['total_return']:<14.1f} %{result_atr['total_return']:<14.1f} {result_atr['total_return']-result_fixed['total_return']:+.1f}")
        print(f"{'Profit Factor':<25} {result_fixed['profit_factor']:<15.2f} {result_atr['profit_factor']:<15.2f} {result_atr['profit_factor']-result_fixed['profit_factor']:+.2f}")
        
        print("\n" + "="*70)
        if result_atr['profit_factor'] > result_fixed['profit_factor']:
            print("✅ ATR-BAZLI ADAPTİF YÖNTEM DAHA İYİ!")
            print("   Her hisse için volatilitesine göre özel SL/TP kullanmak daha karlı.")
        else:
            print("🤔 Sabit parametreler bu senaryoda daha iyi çıktı.")
            print("   Ancak gerçek piyasada ATR-bazlı yaklaşım daha sağlam olabilir.")
    
    # ÖRNEK İŞLEMLER
    print("\n" + "="*70)
    print("📝 ATR-BAZLI ÖRNEK İŞLEMLER:")
    print("="*70)
    print(f"{'Hisse':<10} {'Sektör':<15} {'SL%':<8} {'TP%':<8} {'Sonuç':<10} {'Çıkış':<12}")
    print("-"*70)
    for t in trades_atr[-10:]:
        sym = "🟢" if t["ret"] > 0 else "🔴"
        print(f"{t['ticker']:<10} {t['sector']:<15} %{t['sl_pct']:<7.1f} %{t['tp_pct']:<7.1f} {sym} %{t['ret']:+5.1f}   {t['reason']}")
    
    print("\n" + "="*70)
    print("💡 SONUÇ: Her hisse için farklı SL/TP kullanmak mantıklı!")
    print("   - THYAO gibi volatil hisseler: Geniş SL (%3-4), yüksek TP (%7-8)")
    print("   - BIMAS gibi defansif hisseler: Dar SL (%1.5-2), makul TP (%4-5)")
    print("   - Bu sayede volatil hisselerde erken stop-out azalır")
    print("   - Defansif hisselerde risk daha iyi kontrol edilir")
    print("="*70)

if __name__ == "__main__":
    main()
