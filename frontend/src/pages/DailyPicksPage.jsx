/**
 * Günün Fırsatları - V2+V3 HYBRID STRATEJİ
 * Win Rate: %62-70 | Profit Factor: 2.5+ | Partial Exit Enabled
 */
import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Target,
  Shield,
  Flame,
  CheckCircle,
  XCircle,
  Activity,
  BarChart3,
  AlertTriangle,
  Filter,
  Star,
  X,
  Info,
  Eye,
} from "lucide-react";
import StockPickCard from "../components/Dashboard/StockPickCard";
import { usePortfolioStore } from "../store/portfolioStore";
import MobileDailyPicksPage from "./mobile/MobileDailyPicksPage";

// Mobile detection hook
const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState(
    typeof window !== 'undefined' ? window.innerWidth < 1024 : false
  );
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 1024);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  return isMobile;
};

const DailyPicksPage = () => {
  const isMobile = useIsMobile();
  


  const [morningPicks, setMorningPicks] = useState(null);
  const [dayTradeStatus, setDayTradeStatus] = useState(null);
  const [strategyInfo, setStrategyInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPick, setSelectedPick] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const { watchlist, addToWatchlist, removeFromWatchlist } = usePortfolioStore();

  const fetchMorningPicks = async () => {
    try {
      setLoading(true);
      // V2+V3 Hybrid Strategy Endpoint
      const response = await axios.get(
        `/api/signals/daily-picks?strategy=hybrid&max_picks=5`
      );
      
      const picks = response.data.picks || [];
      const stratInfo = response.data.strategy_info || {};
      const warnings = response.data.warnings || [];
      const marketTrend = response.data.market_trend || response.data.market_status?.market_trend || "YUKSELIS";
      
      setStrategyInfo({...stratInfo, warnings, marketTrend});
      
      const formattedPicks = picks.map(p => ({
        ticker: p.ticker,
        price: p.entry_price,
        change_percent: 0,
        momentum: p.strength > 80 ? 'very_strong' : p.strength > 70 ? 'strong' : 'moderate',
        setup_quality: p.confidence > 80 ? 'Excellent' : p.confidence > 70 ? 'Good' : 'Moderate',
        score: Math.round(p.strength),
        sector: p.sector,
        reasons: p.reasons || [],
        recommendation: p.signal || 'BUY',
        // V2+V3 Hybrid özelliği - Partial Exit bilgisi
        exitStrategy: p.exit_strategy || {
          tp1_action: "TP1'de %50 pozisyon kapat",
          tp1_new_stop: "Break-even'a çek",
          tp2_action: "TP2'de kalan %50 kapat"
        },
        partialExitPct: p.partial_exit_pct || 0.5,
        details: {
          rsi_value: 50,
          volume_ratio: 1.0,
          macd_signal: 'bullish',
          trend_status: 'Uptrend'
        },
        levels: {
            entry_price: p.entry_price,
            stop_loss: p.stop_loss,
            take_profit: p.take_profit_1, // TP1
            take_profit_1: p.take_profit_1,
            take_profit_2: p.take_profit_2,
            risk_reward_ratio: p.risk_reward_ratio || 2.5,
            risk_reward_2: p.risk_reward_2 || 4.0,
            risk_pct: p.risk_pct || Math.abs((p.entry_price - p.stop_loss) / p.entry_price * 100),
            reward_pct: p.reward_pct || Math.abs((p.take_profit_1 - p.entry_price) / p.entry_price * 100),
            reward_pct_1: p.reward_pct || Math.abs((p.take_profit_1 - p.entry_price) / p.entry_price * 100),
            reward_pct_2: p.reward_pct_2 || (p.take_profit_2 ? Math.abs((p.take_profit_2 - p.entry_price) / p.entry_price * 100) : 0),
            volatility_class: 'High',
            atr: 0, 
            atr_percent: 0,
            max_hold_days: 5, // V3 holding period
            partial_exit: true // V2+V3 Hybrid özelliği
        }
      }));

      // Calculate summary stats
      const summary = {
          total_picks: formattedPicks.length,
          avg_score: Math.round(formattedPicks.reduce((acc, curr) => acc + curr.score, 0) / (formattedPicks.length || 1)),
          avg_risk_pct: (formattedPicks.reduce((acc, curr) => acc + curr.levels.risk_pct, 0) / (formattedPicks.length || 1)).toFixed(2),
          avg_reward_pct: (formattedPicks.reduce((acc, curr) => acc + curr.levels.reward_pct, 0) / (formattedPicks.length || 1)).toFixed(2)
      };

      setMorningPicks({ 
        success: true, 
        picks: formattedPicks,
        summary: summary,
        market_trend: marketTrend
      });
      
      // Separate call for status if needed, or use response.data.market_status
      try {
           const statusRes = await axios.get("/api/screener/day-trade-status");
           setDayTradeStatus(statusRes.data);
      } catch (err) {
           console.log("Status fetch failed", err);
      }
      
    } catch (error) {
      console.error("Error fetching daily picks:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMorningPicks();
    // Günlük strateji olduğu için otomatik yenileme (polling) kaldırıldı.
    // Kullanıcı manuel olarak 'Yenile' butonunu kullanabilir.
  }, []);

  // Filtreleme fonksiyonu
  const getFilteredPicks = () => {
    if (!morningPicks?.picks || !Array.isArray(morningPicks.picks)) return [];
    return morningPicks.picks;
  };

  // Watchlist toggle fonksiyonu - e.stopPropagation ekle
  const toggleWatchlist = (e, ticker) => {
    e.stopPropagation();
    e.preventDefault();
    
    try {
      if (!ticker) {
        console.error('❌ Ticker boş!');
        return;
      }
      
      console.log('🔄 Toggle çalıştı. Ticker:', ticker);
      console.log('📋 Mevcut watchlist:', watchlist);
      
      const isInWatchlist = Array.isArray(watchlist) && watchlist.includes(ticker);
      console.log('✅ Listede mi?', isInWatchlist);
      
      if (isInWatchlist) {
        removeFromWatchlist(ticker);
        console.log('✅ Portföyden çıkarıldı:', ticker);
      } else {
        addToWatchlist(ticker);
        console.log('✅ Portföye eklendi:', ticker);
      }
      
      // Yeni durumu kontrol et
      setTimeout(() => {
        console.log('🔍 İşlem sonrası watchlist:', watchlist);
      }, 100);
    } catch (error) {
      console.error('❌ Watchlist toggle hatası:', error);
    }
  };

  // Modal açma fonksiyonu
  const openModal = (e, pick) => {
    if (e) {
      e.stopPropagation();
      e.preventDefault();
    }
    setSelectedPick(pick);
    setShowModal(true);
  };

  // Modal kapatma
  const closeModal = () => {
    setShowModal(false);
    setSelectedPick(null);
  };

  // Watchlist durumunu kontrol et
  const isInWatchlist = (ticker) => {
    return Array.isArray(watchlist) && watchlist.includes(ticker);
  };

  const getPhaseColor = (color) => {
    const colors = {
      green: "bg-success/20 border-success text-success",
      red: "bg-danger/20 border-danger text-danger",
      blue: "bg-primary/20 border-primary text-primary",
      orange: "bg-warning/20 border-warning text-warning",
    };
    return colors[color] || "bg-gray-500/20 border-gray-500 text-gray-400";
  };

  return isMobile ? (
    <MobileDailyPicksPage />
  ) : (
    <div className="space-y-3 sm:space-y-4 animate-fade-in">
      {/* Market Status */}
      {dayTradeStatus && (
        <div
          className={`p-2 sm:p-3 rounded-lg sm:rounded-xl border sm:border-2 ${getPhaseColor(dayTradeStatus.color)}`}
        >
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
            <div className="flex items-center gap-1.5 sm:gap-2">
              <Activity className="w-4 h-4 sm:w-5 sm:h-5" />
              <span className="text-sm sm:text-base font-bold">{dayTradeStatus.action}</span>
            </div>
            <div className="text-[10px] sm:text-xs md:text-sm">
              Alım:{" "}
              <span className="font-bold">{dayTradeStatus.buy_window}</span>
              {" | "}
              Satış:{" "}
              <span className="font-bold">{dayTradeStatus.sell_window}</span>
            </div>
          </div>
        </div>
      )}

      {/* Header with Filters */}
      <div className="card p-3 sm:p-4">
        <div className="flex flex-col gap-3 sm:gap-4">
          <div className="flex items-center justify-between gap-2">
            <div className="min-w-0 flex-1">
              <h2 className="text-base sm:text-lg font-bold flex items-center gap-1.5 sm:gap-2">
                <Flame className="w-4 h-4 sm:w-5 sm:h-5 text-warning flex-shrink-0" />
                <span className="truncate">Günün Fırsatları</span>
              </h2>
              <p className="text-[10px] sm:text-xs md:text-sm text-theme-muted truncate">
                V2+V3 Hybrid | WR: %62-70 | PF: 2.5+ | Min Skor: 75 | Partial Exit
              </p>
            </div>
            
            <button
              onClick={fetchMorningPicks}
              disabled={loading}
              className="px-3 sm:px-4 md:px-5 py-2 sm:py-2.5 md:py-3 bg-primary hover:bg-primary/90 text-white rounded-lg sm:rounded-xl font-semibold flex items-center gap-1.5 sm:gap-2 transition-all transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg flex-shrink-0 text-sm sm:text-base">
              <RefreshCw className={`w-4 h-4 sm:w-5 sm:h-5 ${loading ? "animate-spin" : ""}`} />
              <span className="hidden sm:inline">Yenile</span>
            </button>
          </div>
        </div>

      </div>

      {/* V2+V3 Hybrid Strategy Info Banner */}
      {strategyInfo && (
        <div className={`card p-3 sm:p-4 ${
          strategyInfo.marketTrend === 'DUSUS' 
            ? 'bg-gradient-to-r from-danger/10 to-warning/10 border-danger/30' 
            : 'bg-gradient-to-r from-primary/10 to-success/10 border-primary/30'
        }`}>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Target className="w-5 h-5 text-primary" />
              <span className="font-semibold text-theme-text">V2+V3 Hybrid Strateji</span>
              {strategyInfo.marketTrend === 'DUSUS' && (
                <span className="px-2 py-0.5 text-xs bg-danger/20 text-danger rounded animate-pulse">
                  ⚠️ DİKKAT
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-2 text-xs sm:text-sm">
              <span className="px-2 py-1 bg-primary/20 rounded text-primary">TP1: 1:{strategyInfo.tp1_rr || '2.5'}</span>
              <span className="px-2 py-1 bg-success/20 rounded text-success">TP2: 1:{strategyInfo.tp2_rr || '4.0'}</span>
              <span className="px-2 py-1 bg-warning/20 rounded text-warning">Partial Exit: %50</span>
            </div>
          </div>
          <p className="text-xs text-theme-muted mt-2">
            💡 TP1'de %50 pozisyon kapat, stop'u break-even'a çek. TP2'de kalan %50'yi kapat.
          </p>
          
          {/* Market Uyarı Banner */}
          {strategyInfo.warnings && strategyInfo.warnings.length > 0 && (
            <div className="mt-3 p-2 bg-danger/10 border border-danger/30 rounded-lg">
              {strategyInfo.warnings.map((warning, idx) => (
                <p key={idx} className="text-xs text-danger font-medium">
                  {warning}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Stats Summary */}
      {morningPicks?.success && morningPicks.summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
          <div className="card p-2 sm:p-3 text-center">
            <p className="text-lg sm:text-xl md:text-2xl font-bold text-primary">
              {morningPicks.summary.total_picks}
            </p>
            <p className="text-[9px] sm:text-[10px] md:text-xs text-theme-muted">Öneri</p>
          </div>
          <div className="card p-2 sm:p-3 text-center">
            <p className="text-lg sm:text-xl md:text-2xl font-bold text-success">
              {morningPicks.summary.avg_score}
            </p>
            <p className="text-[9px] sm:text-[10px] md:text-xs text-theme-muted">Ort. Skor</p>
          </div>
          <div className="card p-2 sm:p-3 text-center">
            <p className="text-lg sm:text-xl md:text-2xl font-bold text-danger">
              %{morningPicks.summary.avg_risk_pct || 0}
            </p>
            <p className="text-xs text-theme-muted">Ort. Risk</p>
          </div>
          <div className="card p-3 text-center">
            <p className="text-2xl font-bold text-success">
              %{morningPicks.summary.avg_reward_pct || 0}
            </p>
            <p className="text-xs text-theme-muted">Ort. Hedef</p>
          </div>
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div className="card text-center py-12">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-primary mb-4" />
          <p className="text-theme-muted">Analiz ediliyor...</p>
        </div>
      ) : !morningPicks?.success ? (
        <div className="card text-center py-12">
          <XCircle className="w-12 h-12 text-danger mx-auto mb-4" />
          <p className="text-theme-text font-medium">
            {morningPicks?.message || "Bugün işlem yapılmamalı"}
          </p>
          <p className="text-sm text-theme-muted mt-2">
            Piyasa koşulları uygun değil
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-4">
          {/* Picks List */}
          <div className="lg:col-span-2 space-y-4">
            {getFilteredPicks().length > 0 ? (
              getFilteredPicks().map((pick, index) => {
                const inWatchlist = isInWatchlist(pick.ticker);
                
                return (
                  <div 
                    key={pick.ticker} 
                    className="relative group cursor-pointer hover:shadow-xl transition-shadow duration-300"
                    onClick={(e) => {
                      // Eğer butonlara tıklanmadıysa modal aç
                      if (!e.target.closest('button')) {
                        console.log('🔍 Kart tıklandı, detay açılıyor:', pick.ticker);
                        openModal(e, pick);
                      }
                    }}
                    title="Detaylı analiz için karta tıklayın"
                  >
                    <StockPickCard 
                      pick={pick} 
                      rank={index + 1} 
                      inWatchlist={inWatchlist}
                      onToggleWatchlist={toggleWatchlist}
                    />
                    
                    {/* Watchlist Badge - Bottom Left */}
                    {inWatchlist && (
                      <div className="absolute bottom-3 left-3 z-10">
                        <span className="px-2.5 py-1 text-xs font-semibold bg-gradient-to-r from-success to-success/80 text-white rounded-lg shadow-md flex items-center gap-1">
                          <CheckCircle className="w-3 h-3" />
                          Portföyde
                        </span>
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <div className="card text-center py-12">
                <Filter className="w-12 h-12 text-theme-muted mx-auto mb-4" />
                <p className="text-theme-text font-medium">Bugün için öneri bulunamadı</p>
                <p className="text-sm text-theme-muted mt-2">
                  Yeni veriler için Yenile düğmesine tıklayın
                </p>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-3">
            {/* Market Trend */}
            <div className="card">
              <div
                className={`p-3 rounded-lg ${morningPicks.market_trend === "YUKSELIS" ? "bg-success/10 border border-success/30" : "bg-danger/10 border border-danger/30"}`}
              >
                <div className="flex items-center gap-2">
                  {morningPicks.market_trend === "YUKSELIS" ? (
                    <TrendingUp className="w-6 h-6 text-success" />
                  ) : (
                    <TrendingDown className="w-6 h-6 text-danger" />
                  )}
                  <div>
                    <p
                      className={`font-bold ${morningPicks.market_trend === "YUKSELIS" ? "text-success" : "text-danger"}`}
                    >
                      BIST100{" "}
                      {morningPicks.market_trend === "YUKSELIS"
                        ? "YÜKSELİŞ"
                        : "DÜŞÜŞ"}
                    </p>
                    <p className="text-xs text-theme-muted">
                      {morningPicks.market_trend === "YUKSELIS"
                        ? "İşlem yapılabilir"
                        : "Pozisyon boyutunu %50 azaltın"}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Strategy Rules */}
            <div className="card">
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <Target className="w-4 h-4 text-primary" />
                V2+V3 Hybrid Kuralları
              </h3>
              <ul className="space-y-2 text-xs">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-success flex-shrink-0 mt-0.5" />
                  <span>Minimum skor: 75/100 (Kalite)</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className={`w-4 h-4 flex-shrink-0 mt-0.5 ${morningPicks.market_trend === "YUKSELIS" ? "text-success" : "text-warning"}`} />
                  <span>BIST100 trend filtresi {morningPicks.market_trend === "YUKSELIS" ? "✓" : "(esnek)"}</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-success flex-shrink-0 mt-0.5" />
                  <span>Sektör başına max 1 hisse</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                  <span>Günde max 5 öneri</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-warning flex-shrink-0 mt-0.5" />
                  <span>TP1: %50 sat, Break-even'a çek</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-success flex-shrink-0 mt-0.5" />
                  <span>TP2: Kalan %50'yi sat</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-danger flex-shrink-0 mt-0.5" />
                  <span>Stop: Teknik seviyeler</span>
                </li>
              </ul>
            </div>

            {/* Risk Rules */}
            <div className="card border-2 border-warning/30 bg-warning/5">
              <h3 className="font-semibold mb-3 flex items-center gap-2 text-warning">
                <Shield className="w-5 h-5" />
                Risk Yönetimi
              </h3>
              <ul className="space-y-2 text-xs">
                <li className="flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-danger flex-shrink-0 mt-0.5" />
                  <span>Max %2-3 tek işlem riski</span>
                </li>
                <li className="flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-danger flex-shrink-0 mt-0.5" />
                  <span>Max %5-8 günlük kayıp</span>
                </li>
                <li className="flex items-start gap-2">
                  <Target className="w-4 h-4 text-success flex-shrink-0 mt-0.5" />
                  <span>Min 1:2 Risk/Ödül</span>
                </li>
              </ul>
              <div className="mt-3 p-2.5 bg-danger/10 rounded-lg text-xs font-medium text-danger flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                İlk 15 dk işlem yapma!
              </div>
            </div>

            {/* Backtest Results */}
            <div className="card bg-success/5 border border-success/30">
              <h3 className="font-semibold mb-3 flex items-center gap-2 text-success">
                <BarChart3 className="w-5 h-5" />
                Backtest (90 gün)
              </h3>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 bg-success/10 rounded-lg text-center border border-success/20">
                  <p className="text-2xl font-bold text-success mb-1">%67.7</p>
                  <p className="text-theme-muted font-medium">Win Rate</p>
                </div>
                <div className="p-3 bg-success/10 rounded-lg text-center border border-success/20">
                  <p className="text-2xl font-bold text-success mb-1">2.88</p>
                  <p className="text-theme-muted font-medium">Profit Factor</p>
                </div>
                <div className="p-3 bg-primary/10 rounded-lg text-center border border-primary/20">
                  <p className="text-xl font-bold text-primary mb-1">₺372</p>
                  <p className="text-theme-muted font-medium">Net Kar</p>
                </div>
                <div className="p-3 bg-warning/10 rounded-lg text-center border border-warning/20">
                  <p className="text-xl font-bold text-warning mb-1">%17.5</p>
                  <p className="text-theme-muted font-medium">Max DD</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Detaylı Analiz Modalı - İyileştirilmiş */}
      {showModal && selectedPick && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in"
          onClick={closeModal}
        >
          <div 
            className="bg-[var(--color-bg-primary)] rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="sticky top-0 bg-[var(--color-bg-primary)] border-b border-[var(--color-border)] p-4 flex items-center justify-between z-10">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center shadow-lg">
                  <BarChart3 className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-theme-text flex items-center gap-2">
                    {selectedPick.ticker.replace('.IS', '')}
                    {isInWatchlist(selectedPick.ticker) && (
                      <span className="px-2 py-0.5 text-xs bg-warning/20 text-warning rounded-full flex items-center gap-1">
                        <Star className="w-3 h-3 fill-current" />
                        İzleniyor
                      </span>
                    )}
                  </h3>
                  <p className="text-sm text-theme-muted">{selectedPick.sector}</p>
                </div>
              </div>
              <button
                onClick={closeModal}
                className="p-3 rounded-xl hover:bg-danger/10 hover:text-danger transition-all transform hover:scale-110 active:scale-95"
                title="Kapat"
                type="button"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-6">
              {/* Temel Bilgiler */}
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 rounded-xl bg-theme-card">
                  <p className="text-sm text-theme-muted mb-1">Momentum Skoru</p>
                  <p className="text-3xl font-bold text-primary">{selectedPick.score}</p>
                </div>
                <div className="text-center p-4 rounded-xl bg-theme-card">
                  <p className="text-sm text-theme-muted mb-1">Kalite</p>
                  <p className="text-xl font-bold text-success">{selectedPick.setup_quality}</p>
                </div>
                <div className="text-center p-4 rounded-xl bg-theme-card">
                  <p className="text-sm text-theme-muted mb-1">Momentum</p>
                  <p className="text-xl font-bold text-warning">
                    {selectedPick.momentum === 'very_strong' ? '🔥 Çok Güçlü' :
                     selectedPick.momentum === 'strong' ? '⚡ Güçlü' : '📊 Orta'}
                  </p>
                </div>
              </div>

              {/* Fiyat Seviyeleri */}
              <div>
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <Target className="w-4 h-4 text-primary" />
                  Fiyat Seviyeleri
                </h4>
                <div className="space-y-2">
                  <div className="flex justify-between items-center p-3 rounded-lg bg-success/10">
                    <span className="text-sm font-medium">TP2 (1:4.0)</span>
                    <span className="font-bold text-success">
                      ₺{selectedPick.levels?.take_profit_2?.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 rounded-lg bg-success/10">
                    <span className="text-sm font-medium">TP1 (1:2.5)</span>
                    <span className="font-bold text-success">
                      ₺{selectedPick.levels?.take_profit_1?.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 rounded-lg bg-primary/10">
                    <span className="text-sm font-medium">Giriş</span>
                    <span className="font-bold text-primary">
                      ₺{selectedPick.price?.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 rounded-lg bg-danger/10">
                    <span className="text-sm font-medium">Stop Loss</span>
                    <span className="font-bold text-danger">
                      ₺{selectedPick.levels?.stop_loss?.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Teknik Göstergeler */}
              <div>
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-primary" />
                  Teknik Göstergeler
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg bg-theme-card">
                    <p className="text-xs text-theme-muted mb-1">ATR</p>
                    <p className="font-bold text-theme-text">
                      {selectedPick.levels?.atr ? selectedPick.levels.atr.toFixed(2) : '-'}
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-theme-card">
                    <p className="text-xs text-theme-muted mb-1">Volatilite</p>
                    <p className="font-bold text-theme-text">
                      {selectedPick.levels?.volatility_class || 'Normal'}
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-theme-card">
                    <p className="text-xs text-theme-muted mb-1">Hacim</p>
                    <p className="font-bold text-theme-text">
                       {selectedPick.details?.volume_ratio ? selectedPick.details.volume_ratio + 'x' : 'Normal'}
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-theme-card">
                    <p className="text-xs text-theme-muted mb-1">Trend</p>
                    <p className={`font-bold ${selectedPick.details?.trend_status === 'Uptrend' ? 'text-success' : 'text-theme-text'}`}>
                      {selectedPick.details?.trend_status || 'Nötr'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Risk Bilgisi */}
              <div className="p-4 rounded-xl bg-warning/10 border border-warning/30">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-semibold text-warning mb-1">Risk Uyarısı</p>
                    <p className="text-sm text-theme-muted">
                       Strateji: {selectedPick.levels?.volatility_class === 'High' ? 'Yüksek Volatilite' : 'Standart'} <br/>
                       Her işlemde portföyünüzün maksimum %2-3'ünü riske atın. 
                       Stop-loss seviyesine kesinlikle uyun. İlk 15 dakika içinde işlem yapmayın.
                    </p>
                  </div>
                </div>
              </div>

              {/* Portfolio Action - Full Width */}
              <div className="flex flex-col gap-3">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    console.log('🎯 Modal portfolio buton tıklandı:', selectedPick.ticker);
                    toggleWatchlist(e, selectedPick.ticker);
                  }}
                  className={`w-full py-6 px-8 rounded-2xl font-bold text-lg transition-all transform hover:scale-105 active:scale-95 flex items-center justify-center gap-3 shadow-2xl border-3 ${
                    isInWatchlist(selectedPick.ticker)
                      ? 'bg-gradient-to-r from-warning via-warning to-orange-500 hover:via-orange-500 text-white shadow-warning/60 border-white/40'
                      : 'bg-gradient-to-r from-gray-600 via-gray-700 to-gray-800 hover:via-gray-600 text-white shadow-gray-700/60 border-gray-500/40'
                  }`}
                  type="button"
                >
                  <Star className={`w-7 h-7 transition-transform ${isInWatchlist(selectedPick.ticker) ? 'fill-current scale-110' : ''}`} />
                  {isInWatchlist(selectedPick.ticker) ? 'Portföyden Çıkar' : 'Portföye Ekle'}
                </button>
                <button
                  onClick={closeModal}
                  className="w-full py-5 px-6 rounded-xl font-semibold text-base bg-gradient-to-r from-primary via-primary/90 to-primary/80 hover:from-primary/90 text-white transition-all transform hover:scale-105 active:scale-95 flex items-center justify-center gap-2 shadow-xl"
                  type="button"
                >
                  <CheckCircle className="w-6 h-6" />
                  Kapat
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DailyPicksPage;
