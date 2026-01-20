# 🎯 HYBRID STRATEJİ: V2 + V3 EN İYİ ÖZELLİKLER

## Konsept

Hybrid strateji, V2'nin güçlü base yapısını korurken V3'ün başarılı özelliklerini entegre eder.

---

## 📋 V2'DEN ALINAN ÖZELLİKLER (Base)

### 1. ✅ Min Score: 75+
- **Neden:** V2'de %67.6 win rate sağladı
- **Avantaj:** Yüksek kalite filtre
- **V3'te sorun:** Min score 55 kullanıldı, win rate düştü

### 2. ✅ Stop Loss: Teknik (~%2)
- **Neden:** V2'de sadece %13.5 stop loss oranı
- **Avantaj:** Çok sıkı değil, işlemlere nefes aldırır
- **V3'te sorun:** %47.4 stop loss oranı (çok dar!)

### 3. ✅ Market Filtresi: BIST100 Uptrend
- **Neden:** Piyasa yükselişte daha başarılı
- **Avantaj:** 22 günde filtre engelledi, risksiz günleri atladı
- **V3'te:** Market filtresi yoktu

### 4. ✅ Sektör Çeşitlendirmesi
- **Neden:** Risk yönetimi
- **Avantaj:** Her sektörden max 1 hisse
- **V3'te:** Vardı ama max 3 pick ile sınırlıydı

### 5. ✅ Max Picks: 5
- **Neden:** Daha fazla fırsat
- **Avantaj:** Çeşitlendirilmiş portföy
- **V3'te:** 3 pick kullanıldı (daha az fırsat)

---

## 🚀 V3'TEN ALINAN ÖZELLİKLER (Improvements)

### 1. ✨ Partial Exit Stratejisi
```python
# TP1'de %50 pozisyon kapat
if high_today >= pos['tp1']:
    pos['tp1_hit'] = True
    pnl_partial = ((pos['tp1'] - pos['entry']) / pos['entry']) * 100 * 0.5
    # Kalan %50 için break-even yap
    pos['sl'] = pos['entry']
```
- **Avantaj:** Kârı garantile, risk-free continuation
- **V3'te sonuç:** TP1+TP2 işlemler +8.06% ortalama kazandı!
- **V2'de sorun:** Ya hep ya hiç mantığı

### 2. ✨ İkinci Hedef (TP2)
```python
target_1 = current_price + (risk * 2.5)  # TP1: 1:2.5 R/R
target_2 = current_price + (risk * 4.0)  # TP2: 1:4.0 R/R
```
- **Avantaj:** Büyük trendleri yakalamak
- **V3'te sonuç:** 8 işlem full hedeflere ulaştı
- **V2'de:** Sadece tek hedef (~1:3)

### 3. ✨ Dinamik R/R Hedefleri
- **V2:** Fixed 1:3 R/R (~%6 hedef)
- **V3:** Dinamik 1:2.2 & 1:3.5
- **Hybrid:** Orta yol - 1:2.5 & 1:4.0
- **Avantaj:** Hem ulaşılabilir hem büyük kazanç potansiyeli

### 4. ✨ Win Rate Booster (Opsiyonel Bonus)
```python
if BOOSTER_AVAILABLE:
    try:
        boosted_score, booster_reasons = apply_win_rate_boosters(df, idx, score)
        if boosted_score > score:
            score = boosted_score
            reasons.extend(booster_reasons)
    except:
        pass
```
- **Özellikler:**
  - Candlestick Pattern Recognition
  - Support/Resistance Quality Check
  - Momentum Alignment Filter
- **Kullanım:** Opsiyonel bonus (zorunlu değil!)
- **Avantaj:** İyi sinyalleri daha da güçlendirir
- **Güvenlik:** Hata verse bile strateji devam eder

---

## 🎯 HYBRID STRATEJİNİN AVANTAJLARI

### 1. V2'nin Güçlü Taraflarını Korur
- ✅ Yüksek win rate (min score 75)
- ✅ Düşük risk (teknik stop loss)
- ✅ Market ve sektör filtreleri
- ✅ Daha fazla fırsat (5 picks)

### 2. V3'ün En İyi Özelliklerini Ekler
- ✨ Partial exit (kâr garantisi)
- ✨ İkinci hedef (büyük kazançlar)
- ✨ Dinamik hedefler
- ✨ Win rate booster (bonus)

### 3. V3'ün Zayıf Taraflarını Düzeltir
- ❌ V3 min score 55 → ✅ Hybrid 75
- ❌ V3 çok dar stop → ✅ Hybrid teknik stop
- ❌ V3 market filtresi yok → ✅ Hybrid BIST100 filtresi
- ❌ V3 sadece 3 picks → ✅ Hybrid 5 picks

---

## 📊 BEKLENEN PERFORMANS

### Hedefler
- **Win Rate:** %70-75 (V2: %67.6 → Booster ile +2-7%)
- **Profit Factor:** 3.0-3.5 (V2: 3.04, partial exit ile artış)
- **Max Drawdown:** <8% (V2: 4.5%, benzer bekleniyor)
- **Ortalama İşlem:** +1.0% to +1.2% (V2: +0.86%, TP2 ile artış)

### Neden Bu Hedefler Gerçekçi?
1. **Win Rate +2-7%:**
   - V2 base: %67.6
   - Booster opsiyonel bonus: +2-5%
   - Partial exit psikolojik avantaj: +1-2%

2. **Profit Factor artacak:**
   - V2: 3.04
   - TP2 büyük kazançlar: +0.2-0.5 PF
   - Partial exit loss'ları sınırlar

3. **Max DD düşük kalacak:**
   - V2 stop loss stratejisi korundu
   - Market filtresi korundu
   - Sektör çeşitlendirmesi korundu

---

## 🔧 TEKNİK DETAYLAR

### Stop Loss Hesaplama
```python
# 3 farklı stop seviyesi hesapla
atr_stop = current_price - (atr_val * 2.0)      # ATR-based
ema_stop = ema_21_val * 0.98                     # EMA21'in %2 altı
swing_stop = swing_low * 0.985                   # Swing low'un %1.5 altı

# En yükseği al (en az riskli)
stop_loss = max(atr_stop, ema_stop, swing_stop)

# Çok dar stop'u engelle (min %1.5 risk)
if risk / current_price < 0.015:
    return None
```
- **V2 benzeri:** Teknik seviyeler
- **V3'ten farklı:** 2.0x ATR (V3: 2.5x çok sıkıydı)
- **Güvenlik:** Min %1.5 risk garantisi

### Take Profit Hesaplama
```python
target_1 = current_price + (risk * 2.5)  # TP1: 1:2.5
target_2 = current_price + (risk * 4.0)  # TP2: 1:4.0
```
- **TP1 (1:2.5):** V2 (1:3) ile V3 (1:2.2) arası
- **TP2 (1:4.0):** Büyük trendler için
- **Ulaşılabilirlik:** TP1 daha kolay, TP2 bonus

### Partial Exit Mantığı
1. **TP1 kırılırsa:**
   - %50 pozisyon kapat → Kâr garantile
   - Stop loss'u break-even'a taşı
   - Kalan %50 risk-free devam eder

2. **TP2 kırılırsa:**
   - Kalan %50 pozisyon kapat
   - Total PNL = (TP1 * 0.5) + (TP2 * 0.5)

3. **10 gün limiti:**
   - TP1 kırılmışsa: Kalan %50'yi kapat
   - TP1 kırılmamışsa: %100'ü kapat

---

## 📈 V2 vs V3 vs HYBRID KARŞILAŞTIRMA

| Metrik | V2 | V3 | HYBRID |
|--------|----|----|--------|
| **Win Rate** | 67.6% | 50.0% | 70-75% (beklenen) |
| **Profit Factor** | 3.04 | 2.06 | 3.0-3.5 (beklenen) |
| **Max Drawdown** | 4.5% | 17.3% | <8% (beklenen) |
| **Ortalama İşlem** | +0.86% | +1.23% | +1.0-1.2% (beklenen) |
| **Stop Loss Oranı** | 13.5% | 47.4% | ~15-20% (beklenen) |
| **Min Score** | 75 | 55 | 75 ✅ |
| **Market Filtresi** | ✅ | ❌ | ✅ |
| **Partial Exit** | ❌ | ✅ | ✅ |
| **İkinci Hedef** | ❌ | ✅ | ✅ |
| **Win Rate Booster** | ❌ | ✅ (zorunlu) | ✅ (opsiyonel) |
| **Max Picks** | 5 | 3 | 5 ✅ |

---

## 💡 NEDEN HYBRID?

### V2'yi Tek Başına Kullanma Sorunu
- ✅ Çok güçlü (%67.6 WR, 3.04 PF)
- ❌ Ama büyük trendleri tam yakalayamıyor
- ❌ Ya hep ya hiç mantığı
- ❌ Ortalama işlem düşük (+0.86%)

### V3'ü Tek Başına Kullanma Sorunu
- ✅ Büyük kazançlar (+8.06% TP1+TP2'de)
- ✅ İyi fikirler (partial exit, booster)
- ❌ Win rate çok düşük (%50)
- ❌ Stop loss çok sıkı (%47.4)
- ❌ Max DD çok yüksek (%17.3)

### Hybrid'in Çözümü
- ✅ V2'nin tutarlılığı
- ✅ V3'ün büyük kazanç potansiyeli
- ✅ Her ikisinin de zayıf yanlarını düzeltir
- ✅ Risk-reward optimal

---

## 🚀 KULLANIM

```bash
cd /home/MuhammedBesir/trading-botu/backend
python backtest_hybrid.py
```

### Özelleştirme
```python
# Test süresi ve max picks ayarla
results = run_hybrid_backtest(days=90, max_picks=5)
```

---

## 📝 SONUÇ

Hybrid strateji, V2'nin kanıtlanmış güçlü yapısını koruyarak V3'ün en başarılı özelliklerini entegre eder:

1. **Tutarlılık** (V2'den): Yüksek win rate, düşük risk
2. **Büyük Kazançlar** (V3'ten): Partial exit, TP2, dinamik hedefler
3. **Güvenlik** (V2'den): Market filtresi, teknik stop loss
4. **Bonus** (V3'ten): Win rate booster (opsiyonel)

**Beklenen Sonuç:**
- Win Rate: %70-75
- Profit Factor: 3.0-3.5
- Max Drawdown: <8%
- Ortalama İşlem: +1.0-1.2%

**Strateji:** En iyi ikisi birleşir! 🎯
