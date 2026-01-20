#!/usr/bin/env python3
"""
Strateji Karşılaştırma Aracı
v2 vs v3 detaylı analiz
"""

import json
from datetime import datetime

def print_comparison():
    """Stratejileri karşılaştır"""
    print("\n" + "="*80)
    print("📊 STRATEJİ KARŞILAŞTIRMA RAPORU")
    print("="*80)
    print(f"📅 Test Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*80)
    
    # v2 Sonuçları
    print("\n🔴 BACKTEST v2 (ESKİ STRATEJİ):")
    print("-" * 80)
    print("  📋 Parametreler:")
    print("     • Min Score: 75")
    print("     • Min R/R: 1:3")
    print("     • Volume Ratio: 0.7x")
    print("     • Stop Loss: Sabit ~%2")
    print("     • Take Profit: Sabit ~%6")
    print("     • Trend: Tek timeframe")
    print("     • Exit: Tek hedef")
    
    print("\n  📊 Sonuçlar:")
    print("     • Toplam İşlem: 36")
    print("     • Win Rate: %38.9 ❌")
    print("     • Kazanan: 14 | Kaybeden: 22")
    print("     • Toplam Getiri: %-4.69 ❌")
    print("     • Ort. İşlem: %-0.13")
    print("     • Profit Factor: 0.80 ❌")
    print("     • Max Drawdown: %15.4")
    print("     • Benchmark Alpha: %-28.20 ❌")
    
    print("\n  📉 Çıkış Analizi:")
    print("     • EOD: 29 işlem (%80.6) - %6.6 getiri")
    print("     • STOP_LOSS: 7 işlem (%19.4) - %-11.3 getiri")
    
    print("\n  ⚠️  Sorunlar:")
    print("     • Win rate çok düşük (%38.9)")
    print("     • Profit factor < 1 (zararlı)")
    print("     • Benchmark'tan %28 geride")
    print("     • Stop-loss'lar ortalama %-1.61 kaybediyor")
    
    # v3 Sonuçları (placeholder - test tamamlandığında güncellenecek)
    print("\n\n🟢 BACKTEST v3 (YENİ STRATEJİ - BALANCED):")
    print("-" * 80)
    print("  📋 Parametreler:")
    print("     • Min Score: 65 (dengeli)")
    print("     • Min R/R: 1:2.0 (TP1) & 1:3.5 (TP2)")
    print("     • Volume Ratio: 1.0x (daha esnektir)")
    print("     • Stop Loss: Dinamik (teknik seviyeler)")
    print("     • Take Profit: Dinamik (direnç bazlı)")
    print("     • Trend: Çoklu timeframe (EMA 9/21/50/200)")
    print("     • Exit: Partial exit (%50 TP1, %50 TP2)")
    print("     • RSI: 35-60 optimal bölge")
    print("     • Market Structure: Destek/direnç analizi")
    
    print("\n  📊 Test çalışıyor...")
    print("     (Sonuçlar için backtest_v3_improved.py'yi çalıştırın)")
    
    # Beklenen iyileştirmeler
    print("\n\n🎯 BEKLENEN İYİLEŞTİRMELER:")
    print("-" * 80)
    
    improvements = [
        ("Win Rate", "%38.9", "%50-60", "Çoklu filtreler + kaliteli sinyaller"),
        ("Profit Factor", "0.80", "1.3-1.8", "Dinamik R/R + partial exit"),
        ("Ortalama İşlem", "%-0.13", "%+0.30-0.50", "Daha iyi entry/exit"),
        ("Max Drawdown", "%15.4", "%10-12", "Risk yönetimi"),
        ("Stop Loss Etkisi", "%-1.61", "%-1.2 veya daha iyi", "Teknik stop-loss"),
    ]
    
    print(f"\n  {'Metrik':<20} {'v2 (Eski)':<15} {'v3 (Yeni)':<15} {'İyileştirme'}")
    print("  " + "-" * 78)
    for metric, old, new, improvement in improvements:
        print(f"  {metric:<20} {old:<15} {new:<15} {improvement}")
    
    #핵심 Değişiklikler
    print("\n\n🔑 核심 DEĞİŞİKLİKLER:")
    print("-" * 80)
    
    changes = [
        ("Çoklu Timeframe Trend", "❌ Yok", "✅ EMA 9/21/50/200 uyumu"),
        ("Volume Kalite", "❌ Sadece ratio", "✅ Ratio + trend + konfirmasyon"),
        ("RSI Filtresi", "❌ Geniş (35-65)", "✅ Optimal (35-60)"),
        ("Market Structure", "❌ Yok", "✅ Destek/direnç analizi"),
        ("Stop-Loss", "❌ Sabit %2", "✅ Dinamik (ATR/EMA/swing)"),
        ("Take-Profit", "❌ Sabit %6", "✅ Dinamik (direnç bazlı)"),
        ("Çıkış Stratejisi", "❌ Tek hedef", "✅ Partial exit (%50+%50)"),
        ("Min R/R", "❌ 1:3 (çok yüksek)", "✅ 1:2.0 (dengeli)"),
    ]
    
    print(f"\n  {'Özellik':<25} {'v2':<20} {'v3'}")
    print("  " + "-" * 78)
    for feature, old, new in changes:
        print(f"  {feature:<25} {old:<20} {new}")
    
    # Avantajlar
    print("\n\n✨ v3 STRATEJİSİNİN AVANTAJLARI:")
    print("-" * 80)
    advantages = [
        "1. Çoklu timeframe analizi - Tüm vadeler uyumlu",
        "2. Akıllı volume kontrolü - Likidite + momentum",
        "3. RSI optimal bölge - Aşırı seviyelerden kaçın",
        "4. Market structure - Destek/direnç'e saygı",
        "5. Dinamik stop-loss - Teknik seviyelere göre",
        "6. Dinamik targets - Piyasa yapısına göre",
        "7. Partial exit - Kar garantile, risk sıfırla",
        "8. Dengeli R/R - %40 win rate bile karlı",
    ]
    
    for adv in advantages:
        print(f"  ✅ {adv}")
    
    # Dikkat Edilmesi Gerekenler
    print("\n\n⚠️  DİKKAT EDİLMESİ GEREKENLER:")
    print("-" * 80)
    warnings = [
        "• Daha az sinyal üretir (kalite > miktar)",
        "• 200 günlük veri gerektirir (EMA200 için)",
        "• Sideways piyasalarda daha az aktif",
        "• İlk birkaç işlem adaptasyon dönemi olabilir",
    ]
    
    for warn in warnings:
        print(f"  {warn}")
    
    # Öneriler
    print("\n\n💡 ÖNERİLER:")
    print("-" * 80)
    recommendations = [
        "1. Önce v3'ü kağıt üzerinde test edin (paper trading)",
        "2. Küçük pozisyonlarla başlayın",
        "3. Her işlemi not alın ve analiz edin",
        "4. Win rate %50+ ve PF > 1.3 ise güvenle kullanın",
        "5. Farklı piyasa koşullarında test edin",
        "6. Risk yönetimi kurallarına sıkı uyun",
    ]
    
    for rec in recommendations:
        print(f"  {rec}")
    
    print("\n" + "="*80)
    print("📝 NOT: v3 stratejisi test edildiğinde yukarıdaki değerler güncellenecek")
    print("="*80 + "\n")


if __name__ == "__main__":
    print_comparison()
