#!/usr/bin/env python3
"""
Hızlı Test - Win Rate Karşılaştırması
"""
import yfinance as yf
from datetime import datetime, timedelta

print("\n" + "="*60)
print("🧪 HIZLI TEST - Veri Çekme Kontrolü")
print("="*60)

# Test ticker'ları
TEST_TICKERS = ["THYAO.IS", "GARAN.IS", "AKBNK.IS", "EREGL.IS", "ASELS.IS"]

end_date = datetime.now()
start_date = end_date - timedelta(days=150)

print(f"\n📅 Tarih: {start_date.date()} → {end_date.date()}")
print(f"📊 Test Hisseler: {len(TEST_TICKERS)} adet\n")

successful = []
failed = []

for ticker in TEST_TICKERS:
    try:
        print(f"  Çekiliyor: {ticker}...", end=" ")
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if not df.empty:
            print(f"✅ {len(df)} gün")
            successful.append((ticker, len(df)))
        else:
            print("❌ Boş veri")
            failed.append(ticker)
    except Exception as e:
        print(f"❌ Hata: {str(e)[:50]}")
        failed.append(ticker)

print("\n" + "="*60)
print(f"✅ Başarılı: {len(successful)}/{len(TEST_TICKERS)}")
if failed:
    print(f"❌ Başarısız: {', '.join(failed)}")

if successful:
    print("\n📊 Veri Detayları:")
    for ticker, days in successful:
        print(f"  {ticker}: {days} gün veri")
    
    print("\n✅ Veri çekme çalışıyor! Backtest'e devam edebilirsiniz.")
    
    # Basit bir backtest örneği
    print("\n" + "="*60)
    print("🚀 MİNİ BACKTEST - Son 10 Gün")
    print("="*60)
    
    ticker = successful[0][0]
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    print(f"\n{ticker} - Son 10 Gün:")
    print(df[['Open', 'High', 'Low', 'Close', 'Volume']].tail(10).to_string())
    
else:
    print("\n❌ Hiç veri çekilemedi!")
    print("\n💡 Çözüm önerileri:")
    print("  1. İnternet bağlantınızı kontrol edin")
    print("  2. yfinance güncelleyin: pip install --upgrade yfinance")
    print("  3. Farklı ticker'lar deneyin (örn: AAPL, TSLA)")

print("="*60 + "\n")
