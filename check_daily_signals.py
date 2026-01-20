
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Reuse functions from backtest_v3_improved.py
# (I will copy the necessary functions here to ensure it runs standalone)

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
    "TUPRS.IS": "Enerji", "YKBNK.IS": "Bankacılık", "HALKB.IS": "Bankacılık",
    "VAKBN.IS": "Bankacılık", "KOZAL.IS": "Madencilik", "DOHOL.IS": "Holding"
}

TEST_TICKERS = list(STOCK_SECTORS.keys())

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-10)
    return 100 - (100 / (1 + rs))

def calculate_ema(prices, period):
    return prices.ewm(span=period, adjust=False).mean()

def calculate_atr(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close']
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def generate_signal(df, idx, ticker):
    # Determine the date of the check
    check_date = df.index[idx]
    
    close = df['Close'].iloc[:idx+1]
    volumes = df['Volume'].iloc[:idx+1]
    highs = df['High'].iloc[:idx+1]
    lows = df['Low'].iloc[:idx+1]
    
    reasons = []
    total_score = 0
    
    # 1. Multi-timeframe Trend
    ema_9 = calculate_ema(close, 9).iloc[-1]
    ema_21 = calculate_ema(close, 21).iloc[-1]
    ema_50 = calculate_ema(close, 50).iloc[-1]
    
    # Short term
    if ema_9 > ema_21:
        total_score += 30
        reasons.append("✅ (Trend) Kısa vade Yükseliş (EMA9 > EMA21)")
    else:
        # Fail immediately for trend
        return None
        
    # Medium term
    if ema_21 > ema_50:
        total_score += 35
        reasons.append("✅ (Trend) Orta vade Yükseliş (EMA21 > EMA50)")
    else:
        # Fail immediately for trend
        return None

    # 2. Volume Quality
    current_vol = volumes.iloc[-1]
    avg_vol = volumes.tail(20).mean()
    if avg_vol > 0:
        vol_ratio = current_vol / avg_vol
        if vol_ratio >= 1.0:
            total_score += 25
            reasons.append(f"✅ (Hacim) Ortalamanın üzerinde ({vol_ratio:.1f}x)")
        elif vol_ratio >= 0.8:
            total_score += 15
            reasons.append(f"⚠️ (Hacim) Ortalamaya yakın ({vol_ratio:.1f}x)")
        else:
             reasons.append(f"❌ (Hacim) Düşük ({vol_ratio:.1f}x)")

    # 3. RSI Zone
    rsi = calculate_rsi(close, 14).iloc[-1]
    if 35 <= rsi <= 65:
        total_score += 20
        reasons.append(f"✅ (RSI) Optimal bölge ({rsi:.1f})")
    elif rsi > 70:
        reasons.append(f"❌ (RSI) Aşırı alım ({rsi:.1f})")
    elif rsi < 30:
        reasons.append(f"⚠️ (RSI) Aşırı satım ({rsi:.1f})")

    # 4. Market Structure (Distance to resistance)
    recent_high = highs.tail(20).max()
    current_price = close.iloc[-1]
    dist_to_high = ((recent_high - current_price) / current_price) * 100
    
    if dist_to_high > 2.0:
         total_score += 15
         reasons.append(f"✅ (Yapı) Dirence mesafe var (%{dist_to_high:.1f})")
    else:
         reasons.append(f"⚠️ (Yapı) Dirence yakın (%{dist_to_high:.1f})")

    # Final Check
    if total_score < 70:
        return None
        
    # Calculate Targets
    atr_val = calculate_atr(df.iloc[:idx+1]).iloc[-1]
    stop_loss = current_price - (1.5 * atr_val)
    risk = current_price - stop_loss
    tp1 = current_price + (risk * 2.2)
    tp2 = current_price + (risk * 3.5)
    
    return {
        'ticker': ticker,
        'date': check_date,
        'price': current_price,
        'score': total_score,
        'sl': stop_loss,
        'tp1': tp1,
        'tp2': tp2,
        'reasons': reasons
    }

def run_daily_check():
    print(" Veriler güncelleniyor (Period: 1y)...")
    end_date = datetime.now()
    
    all_signals = []
    
    for ticker in TEST_TICKERS:
        try:
            df = yf.download(ticker, period="1y", progress=False, timeout=10)
            if df.empty or len(df) < 50:
                continue
                
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Check LAST DAY (For Tomorrow's Suggestion)
            last_idx = len(df) - 1
            signal = generate_signal(df, last_idx, ticker)
            if signal:
                all_signals.append(signal)
            
            # Check PREVIOUS DAY (For Today's Action)
            # prev_idx = len(df) - 2
            # signal_prev = generate_signal(df, prev_idx, ticker)
                
        except Exception as e:
            continue
            
    # Sort by score
    all_signals.sort(key=lambda x: x['score'], reverse=True)
    
    print("\n" + "="*60)
    print(f"📢 STRATEJİ SİNYALLERİ ({datetime.now().strftime('%d.%m.%Y')})")
    print("="*60)
    
    if not all_signals:
        print("❌ Şu an için yeni bir 'ALIM' fırsatı bulunamadı.")
        print("💡 Piyasa koşulları veya strateji filtreleri (Trend, Hacim) şu an uygun değil.")
    else:
        print(f"✅ Toplam {len(all_signals)} hisse için potansiyel fırsat var:\n")
        
        for s in all_signals[:5]:
            print(f"🔹 {s['ticker']} (Skor: {s['score']})")
            print(f"   Fiyat: {s['price']:.2f} TL")
            print(f"   Hedef 1: {s['tp1']:.2f} TL | Hedef 2: {s['tp2']:.2f} TL")
            print(f"   Stop: {s['sl']:.2f} TL")
            print("   Nedenler:")
            for r in s['reasons']:
                print(f"   - {r}")
            print("-" * 40)

if __name__ == "__main__":
    run_daily_check()
