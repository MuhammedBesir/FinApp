# BACKTEST SONUÇ KARŞILAŞTIRMASI
*Test Tarihi: 19 Ocak 2026*
*Test Süresi: 90 gün*
*Test Hisseleri: 15 BIST hissesi*

---

## 📊 V2 (Baseline) - GÜÇLÜ STRATEJİ

### Ana Metrikler
- **Kazanma Oranı**: **67.6%** ✅
- **Profit Factor**: **3.04** ✅
- **Toplam Getiri**: **+31.70%** ✅
- **Toplam İşlem**: 37
- **Kazanan**: 25 | **Kaybeden**: 12

### Detaylar
- **Max Drawdown**: 4.5%
- **Ortalama İşlem**: +0.86%
- **Alpha (BIST100'e karşı)**: +8.31%
- **Min Score**: 75+
- **Max Picks**: 5 (sektör çeşitli)
- **Stop-Loss**: Teknik (~2%)
- **Take-Profit**: 1:3 R/R (~6%)

### Çıkış Analizi
- **EOD**: 32 işlem (+41.5% toplam, +1.30% ort.)
- **STOP_LOSS**: 5 işlem (-9.8% toplam, -1.96% ort.)

### Filtre Etkisi
- **Market Filter Blocked**: 22 gün
- **No Signal Days**: 46 gün

### Sektör Performansı
- **Havacılık**: 3 işlem, +7.5% toplam, +2.49% ort. 🏆
- **Bankacılık**: 10 işlem, +8.5% toplam, +0.85% ort.
- **İnşaat**: 4 işlem, +3.8% toplam, +0.96% ort.
- **GYO**: 7 işlem, +3.6% toplam, +0.51% ort.
- **Diğer**: 12 işlem, +8.6% toplam, +0.72% ort.
- **Kimya**: 1 işlem, -0.3% toplam

### Değerlendirme
✅ **GÜÇLÜ STRATEJİ - Canlı kullanıma hazır**

---

## 🚀 V3 (Win Rate Booster) - SORUNLU TEST

### Test Durumu
⚠️ **Veri çekme sorunu nedeniyle tam sonuç alınamadı**

### İlk Test Sonucu (3 hisse ile)
- **Kazanma Oranı**: 50.0% ❌ (Hedef: 75-80%)
- **Profit Factor**: 1.40 ❌ (Hedef: 3.5-4.5)
- **Toplam Getiri**: +1.99%
- **Toplam İşlem**: 4 (çok az!)
- **Kazanan**: 2 | **Kaybeden**: 2

### Sorun Analizi
1. **Veri Sorunu**: 12/15 hisse yüklenemedi
   - Yüklenemeyenler: EREGL.IS, ASELS.IS, BIMAS.IS, FROTO.IS, KCHOL.IS, SISE.IS, TCELL.IS, TUPRS.IS, SAHOL.IS, ISCTR.IS, PGSUS.IS, TOASO.IS
   - Yüklenenler: THYAO.IS, GARAN.IS, AKBNK.IS

2. **Minimum Score Çok Yüksek**: 65+ 
   - V2'de 75+ bile 37 işlem üretmişti
   - V3'te 65+ sadece 4 işlem üretti
   - Booster filtreler çok sıkı çalışıyor

3. **Yeterli Test Yapılamadı**
   - 4 işlem istatistiksel olarak anlamlı değil
   - En az 30+ işlem gerekli

---

## 🎯 KARŞILAŞTIRMA SONUÇLARI

### V2 vs V3
| Metrik | V2 | V3 | Fark | Durum |
|--------|----|----|------|-------|
| **Win Rate** | 67.6% | 50.0% | -17.6% | ❌ Kötüleşti |
| **Profit Factor** | 3.04 | 1.40 | -1.64 | ❌ Düştü |
| **Toplam İşlem** | 37 | 4 | -33 | ❌ Çok az |
| **Getiri** | +31.7% | +1.99% | -29.7% | ❌ Çok düşük |
| **Max DD** | 4.5% | 2.5% | -2.0% | ✅ İyileşti |

### Sonuç
⚠️ **V3 TESTİ GEÇERSİZ**

**Nedenler:**
1. ✅ V2 halihazırda güçlü: 67.6% WR, 3.04 PF
2. ❌ V3 tam test edilemedi (veri sorunu)
3. ❌ V3'teki 4 işlem anlamlı değil
4. ❌ Min score 65 çok yüksek

---

## 💡 ÖNERİLER

### 1. V2 Stratejisini Kullan ✅
**V2 halihazırda mükemmel performans gösteriyor:**
- Win Rate: 67.6% (Hedef: 75% - fark sadece 7.4%)
- Profit Factor: 3.04 (Hedef: 3.5 - fark sadece 0.46)
- Canlı kullanıma hazır
- Risk/ödül dengesi iyi

### 2. V3'ü Yeniden Ayarla (İsteğe Bağlı)
Eğer 75-80% win rate hedefi önemliyse:

**a) Min Score Düşür:**
```python
if overall_score < 55:  # 65 yerine 55
    return None
```

**b) Booster'ları Opsiyonel Yap:**
```python
# Sıkı filtre yerine puan ekleyici sistem
boosted_score = overall_score + bonus_points
# En az 55 puan olsun ama booster zorunlu olmasın
```

**c) Veri Sorununu Çöz:**
- Yahoo Finance yerine farklı data provider dene
- Daha güvenilir ticker'lar kullan
- API key'li servis kullan (Alpha Vantage, Investing.com)

### 3. İkili Strateji Yaklaşımı
```
IF market_condition == "güçlü_trend":
    USE V2 (daha agresif, 5 picks, score 75+)
ELIF market_condition == "belirsiz":
    USE V3 (daha seçici, 3 picks, score 65+)
```

### 4. V2'yi İnce Ayar Yap
V2 halihazırda çok iyi, küçük optimizasyonlar:
- Min score: 75 → 72 (biraz daha fazla işlem)
- Take profit: 1:3 → 1:2.5 (daha erken kârı al)
- Trailing stop ekle (kârları koru)

---

## 📋 SONUÇ VE TAVSİYE

### Şu Anda En İyi Seçenek: **V2 Stratejisi**

**Kanıt:**
✅ 67.6% win rate (çok iyi)
✅ 3.04 profit factor (mükemmel)
✅ +31.7% getiri (90 günde)
✅ BIST100'den +8.31% alpha
✅ Düşük drawdown (4.5%)
✅ 37 işlem (yeterli sample size)

**V2 ile Devam Etme Nedenleri:**
1. Halihazırda güçlü performans
2. Canlı kulanıma hazır
3. Risk yönetimi dengeli
4. Hedeflere yakın (67.6% vs 75% hedef)

**V3 ile İlgili:**
- Veri sorunu çözülmeden test edilemez
- Min score çok yüksek (işlem sayısını düşürüyor)
- Mevcut haliyle kullanıma hazır değil

---

## 🎯 AKSİYON PLANI

### Hemen Yapılacaklar:
1. ✅ **V2'yi canlıda kullan**
2. ✅ Paper trading ile doğrula (7 gün)
3. ✅ Küçük pozisyonlarla başla

### İsteğe Bağlı (Gelecek):
1. ⏳ V3 veri sorununu çöz
2. ⏳ V3 min score'u 55'e düşür
3. ⏳ V3'ü tekrar test et (en az 30 işlem)
4. ⏳ V2 vs V3'ü karşılaştır

### Performans İzleme:
```python
# Haftalık takip
weekly_win_rate = monitor_strategy("v2")
if weekly_win_rate < 60%:
    alert("Win rate düşüyor, parametreleri gözden geçir")
```

---

**📌 ÖZET:** V2 stratejisi şu anda mükemmel çalışıyor. Win rate 67.6% ile hedefimize çok yakın. V3'teki booster'lar teoride iyi ama pratikte veri sorunu ve çok sıkı filtreler yüzünden test edilemedi. **Tavsiyem: V2 ile devam et.**
