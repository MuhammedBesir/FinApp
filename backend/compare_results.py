#!/usr/bin/env python3
"""
V2 vs V3 Strateji Karşılaştırma
"""
import time

print("\n" + "="*80)
print("📊 V2 vs V3 KARŞILAŞTIRMA")
print("="*80)

# V2 sonuçları (test_results/v2_test.txt'den)
v2_results = {
    'name': 'V2 - Mevcut Strateji',
    'win_rate': 67.6,
    'profit_factor': 3.04,
    'total_return': 31.70,
    'total_trades': 37,
    'winners': 25,
    'losers': 12,
    'avg_trade': 0.86,
    'max_drawdown': 4.5,
    'alpha': 8.31,
    'min_score': 75,
    'max_picks': 5
}

print("\n🔵 V2 - MEVCUT STRATEJİ")
print("-" * 80)
print(f"  Win Rate: {v2_results['win_rate']}%")
print(f"  Profit Factor: {v2_results['profit_factor']}")
print(f"  Toplam Getiri: +{v2_results['total_return']}%")
print(f"  İşlem Sayısı: {v2_results['total_trades']} ({v2_results['winners']} kazanan, {v2_results['losers']} kaybeden)")
print(f"  Ortalama İşlem: +{v2_results['avg_trade']}%")
print(f"  Max Drawdown: {v2_results['max_drawdown']}%")
print(f"  Alpha: +{v2_results['alpha']}%")
print(f"  Min Score: {v2_results['min_score']}")
print(f"  Değerlendirme: ✅ GÜÇLÜ STRATEJİ")

# V3 testi bekleyelim
print("\n🟡 V3 - WIN RATE BOOSTER")
print("-" * 80)
print("  Test çalışıyor... Lütfen bekleyin.")
print(f"  Min Score: 55 (başarılı ayar korundu)")
print(f"  Booster: Candlestick + S/R + Momentum filtreleri aktif")
print(f"  Hedef: %70+ Win Rate, 3.0+ Profit Factor")

# Dosyayı bekle
for i in range(60):  # 60 saniye bekle
    try:
        with open('v3_final_test.txt', 'r') as f:
            content = f.read()
            if 'BACKTEST v3 SONUÇLARI' in content:
                print("\n✅ V3 testi tamamlandı!")
                # Parse results
                lines = content.split('\n')
                for line in lines:
                    if 'Kazanma Oranı:' in line:
                        wr = line.split(':')[-1].strip().replace('%', '')
                        print(f"\n  Win Rate: {wr}%")
                    elif 'Profit Factor:' in line:
                        pf = line.split(':')[-1].strip()
                        print(f"  Profit Factor: {pf}")
                    elif 'Toplam Getiri:' in line:
                        ret = line.split(':')[-1].strip()
                        print(f"  Toplam Getiri: {ret}")
                    elif 'Toplam İşlem:' in line:
                        trades = line.split(':')[-1].strip()
                        print(f"  İşlem Sayısı: {trades}")
                break
        time.sleep(2)
    except:
        time.sleep(2)
else:
    print("\n⏳ Test henüz tamamlanmadı. v3_final_test.txt dosyasını kontrol edin.")

print("\n" + "="*80)
print("💡 SONUÇ:")
print("="*80)
print("V2 stratejisi halihazırda çok güçlü (%67.6 WR, 3.04 PF)")
print("V3 booster ile hedefe ulaşıp ulaşmadığını yukarıdaki sonuçlardan görebilirsiniz.")
print("\nDetaylı analiz için:")
print("  - v2_test.txt")
print("  - v3_final_test.txt")
print("dosyalarına bakın.")
print("="*80)
