# 🎯 V2+V3 HYBRID STRATEJİ KULLANIM KILAVUZU

## 📋 Strateji Özeti

| Özellik | Değer |
|---------|-------|
| **Win Rate** | %62-70 |
| **Profit Factor** | 2.5+ |
| **Max Drawdown** | <10% |
| **Min Score** | 75 |
| **Max Picks/Gün** | 5 |

## 🚀 Hızlı Başlangıç

### 1. Günlük Tarama (Önerilen)

```python
from app.services.hybrid_strategy import HybridSignalGenerator

# Generator oluştur
gen = HybridSignalGenerator()

# Günlük tarama yap (günde 1 kez çalışır)
result = gen.scan_all_stocks()

# Sinyalleri gör
for signal in result['signals']:
    print(f"{signal['ticker']}: Score {signal['strength']}")
    print(f"  Giriş: ₺{signal['entry_price']:.2f}")
    print(f"  Stop: ₺{signal['stop_loss']:.2f}")
    print(f"  TP1: ₺{signal['take_profit_1']:.2f} (%50 pozisyon kapat)")
    print(f"  TP2: ₺{signal['take_profit_2']:.2f} (kalan %50)")
```

### 2. Terminal'den Çalıştırma

```bash
cd /home/MuhammedBesir/trading-botu/backend
python -c "
from app.services.hybrid_strategy import HybridSignalGenerator
gen = HybridSignalGenerator()
result = gen.scan_all_stocks(force_run=True)
print(f'Bulunan sinyal: {len(result[\"signals\"])}')
for s in result['signals'][:5]:
    print(f\"  {s['ticker']}: Score {s['strength']}\")
"
```

### 3. Backtest Çalıştırma

```bash
cd /home/MuhammedBesir/trading-botu/backend
python backtest_hybrid.py
```

## 📊 Strateji Parametreleri

### V2 Filtreleri (Kalite)
- **Min Score: 75** - Sadece yüksek kaliteli sinyaller
- **Market Filter** - BIST100 downtrend'de işlem yapma
- **Sektör Çeşitlendirmesi** - Her sektörden max 1 hisse
- **Max Picks: 5/gün** - Overtrading önleme

### V3 Özellikleri (Getiri)
- **Partial Exit** - TP1'de %50 pozisyon kapat
- **TP1 R/R: 1:2.5** - İlk hedef (risk x 2.5)
- **TP2 R/R: 1:4.0** - İkinci hedef (risk x 4)
- **Break-even** - TP1 sonrası stop = giriş fiyatı

## 🎮 Kullanım Senaryoları

### Senaryo 1: Sabah Taraması
```python
from app.services.hybrid_strategy import HybridSignalGenerator

gen = HybridSignalGenerator()

# Market durumunu kontrol et
market_ok, market_msg = gen.check_market_filter()
print(f"Market: {market_msg}")

if market_ok:
    result = gen.scan_all_stocks()
    print(f"Bugün {len(result['signals'])} sinyal bulundu")
```

### Senaryo 2: Tek Hisse Analizi
```python
import yfinance as yf
from app.services.hybrid_strategy import HybridSignalGenerator

gen = HybridSignalGenerator()

# Veri çek
df = yf.download('GARAN.IS', period='3mo', progress=False)

# İndikatörleri hesapla
indicators = gen._calculate_indicators(df)

# Sinyal al
signal = gen.generate_signal(df, indicators, ticker='GARAN.IS')

if signal['signal'] == 'BUY':
    print(f"✅ AL sinyali!")
    print(f"   Giriş: ₺{signal['entry_price']:.2f}")
    print(f"   Stop: ₺{signal['stop_loss']:.2f}")
    print(f"   TP1: ₺{signal['take_profit_1']:.2f}")
else:
    print(f"❌ Sinyal yok: {signal.get('warnings', [])}")
```

### Senaryo 3: Günlük Durumu Kontrol Et
```python
from app.services.hybrid_strategy import HybridSignalGenerator

gen = HybridSignalGenerator()
status = gen.get_daily_status()

print(f"Tarih: {status['date']}")
print(f"Sinyal: {status['signals_generated']}/{status['max_picks']}")
print(f"Kalan: {status['remaining_slots']} slot")
print(f"Sektörler: {status['sectors_used']}")
```

## 📈 Trade Yönetimi

### Giriş Kuralları
1. Score >= 75
2. BIST100 uptrend (EMA20 üstünde)
3. Sektör limiti aşılmamış
4. Günlük limit (5) aşılmamış

### Çıkış Kuralları

#### TP1'de (%50 pozisyon):
- Hedef: Giriş + (Risk x 2.5)
- Örnek: Giriş ₺100, Stop ₺97.5 → TP1 = ₺106.25
- **Aksiyon**: %50 sat, stop'u ₺100'e çek (break-even)

#### TP2'de (kalan %50):
- Hedef: Giriş + (Risk x 4.0)
- Örnek: TP2 = ₺110
- **Aksiyon**: Kalan %50'yi sat

#### Stop-Loss:
- Teknik seviye (son 10 gün low, EMA20)
- Max %2.5

## 📁 Dosya Yapısı

```
backend/
├── app/services/
│   ├── hybrid_strategy.py    # 🎯 ANA STRATEJİ
│   ├── signal_generator.py   # Hybrid entegrasyonu
│   └── ...
├── backtest_hybrid.py        # Backtest scripti
├── win_rate_booster.py       # Bonus özellikler
└── KULLANIM.md               # Bu dosya
```

## ⚙️ Parametreleri Değiştirme

```python
from app.services.hybrid_strategy import HybridSignalGenerator, HybridRiskManagement

# Özel parametreler
params = HybridRiskManagement(
    min_score=80,              # Daha sıkı (varsayılan: 75)
    max_picks_per_day=3,       # Daha az sinyal (varsayılan: 5)
    tp1_risk_reward=3.0,       # Daha yüksek TP1 (varsayılan: 2.5)
    tp2_risk_reward=5.0,       # Daha yüksek TP2 (varsayılan: 4.0)
    max_stop_loss_pct=2.0,     # Daha sıkı stop (varsayılan: 2.5)
)

gen = HybridSignalGenerator(params=params)
```

## 🔔 Önemli Notlar

1. **Günde 1 Kez**: Strateji günde 1 kez çalışır (tekrarı önler)
2. **Market Filter**: BIST100 düşüşte sinyal vermez
3. **Sektör Limiti**: Aynı sektörden max 1 hisse
4. **Partial Exit**: TP1'de mutlaka %50 sat
5. **Break-even**: TP1 sonrası stop'u girişe çek

## 📞 Sorun Giderme

### "Günlük limit doldu" hatası
```python
# force_run=True ile zorla çalıştır
result = gen.scan_all_stocks(force_run=True)
```

### "Market filter failed" hatası
- BIST100 düşüş trendinde, bekle
peki
### Sinyal bulunamadı
- Score 75 çok yüksek olabilir, 70'e düşür
- Daha fazla hisse tara

---
📅 Son Güncelleme: Ocak 2026
🎯 Strateji: V2+V3 Hybrid
