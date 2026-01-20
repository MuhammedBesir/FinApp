/**
 * Main Dashboard Component - Professional Trading Platform
 * 🎨 Modern Design | 📊 Real-time Data | 💰 Portfolio Tracking | ✨ Advanced Features
 */
import React, { useEffect, useRef, useState } from "react";
import { useStockData } from "../../hooks/useStockData";
import { useStore } from "../../store";
import { usePortfolioStore } from "../../store/portfolioStore";
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
  ChevronDown,
  ChevronUp,
  Settings,
  Activity,
  Zap,
  DollarSign,
  Percent,
  Target,
  Sparkles,
  Clock,
  Award,
  Shield,
  LineChart,
} from "lucide-react";
import MiniChart from "../Charts/MiniChart";
import StockChart from "../Charts/StockChart";
import IndicatorSelector from "../Charts/IndicatorSelector";
import LoadingSpinner from "../Common/LoadingSpinner";
import TopMovers from "./TopMovers";
import RecentTrades from "./RecentTrades";
import MarketOverview from "./MarketOverview";
import MobileDashboard from "./MobileDashboard";

// Custom hook for responsive detection
const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 1024);
  
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 1024);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  return isMobile;
};

const Dashboard = () => {
  const isMobile = useIsMobile();
  useStockData();

  const {
    selectedTicker,
    stockData,
    stockInfo,
    signal,
    isLoading,
    error,
    realtimeData,
    getLatestIndicators,
  } = useStore();

  const { trades } = usePortfolioStore();

  const [selectedIndicators, setSelectedIndicators] = useState({
    ichimoku: { enabled: false },
    fibonacci: { enabled: false },
    bollinger: { enabled: false, period: 20, stdDev: 2.0 },
    linreg: { enabled: false, period: 14 },
    trendChannel: { enabled: false },
  });

  const [showAdvancedIndicators, setShowAdvancedIndicators] = useState(false);
  const [showTechnicalIndicators, setShowTechnicalIndicators] = useState(true);
  const [chartHeight, setChartHeight] = useState(null);
  const sidebarRef = useRef(null);

  useEffect(() => {
    if (!sidebarRef.current) return;

    const computeHeight = () => {
      const sidebarH = sidebarRef.current?.offsetHeight || 0;
      if (sidebarH) {
        const desired = Math.max(320, sidebarH - 200);
        const clamped = Math.min(desired, 420);
        setChartHeight(clamped);
      }
    };

    computeHeight();

    const observer = new ResizeObserver(() => computeHeight());
    observer.observe(sidebarRef.current);
    window.addEventListener("resize", computeHeight);

    return () => {
      observer.disconnect();
      window.removeEventListener("resize", computeHeight);
    };
  }, []);

  const latestData =
    realtimeData?.price || stockData?.data?.[stockData.data.length - 1];
  const indicatorData = getLatestIndicators();

  // Price calculations
  const currentPrice = latestData?.close || stockInfo?.current_price || 0;
  const previousClose =
    stockInfo?.previous_close || latestData?.open || currentPrice;
  const change = currentPrice - previousClose;
  const changePercent = previousClose ? (change / previousClose) * 100 : 0;
  const isPositive = change >= 0;

  // Format helpers
  const formatCurrency = (value) => {
    if (value === undefined || value === null) return "—";
    return new Intl.NumberFormat("tr-TR", {
      style: "currency",
      currency: "TRY",
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatVolume = (vol) => {
    if (!vol) return "—";
    if (vol >= 1e9) return (vol / 1e9).toFixed(2) + "B";
    if (vol >= 1e6) return (vol / 1e6).toFixed(2) + "M";
    if (vol >= 1e3) return (vol / 1e3).toFixed(1) + "K";
    return vol.toString();
  };

  // Recent trades
  const recentTrades = (trades || [])
    .slice(-4)
    .reverse()
    .map((trade) => ({
      symbol: trade.ticker?.split(".")[0] || trade.symbol,
      type: trade.type === "buy" ? "AL" : "SAT",
      date: new Date(trade.createdAt).toLocaleDateString("tr-TR"),
      price: trade.price?.toFixed(2) || "0.00",
      profit: trade.pnl
        ? `${trade.pnl >= 0 ? "+" : ""}${((trade.pnl / (trade.price * trade.quantity)) * 100).toFixed(1)}%`
        : "—",
      isProfit: trade.pnl >= 0,
    }));

  if (error) {
    return (
      <div className="p-6">
        <div className="card border-danger/30 bg-danger/5">
          <h3 className="text-lg font-semibold text-danger mb-2">Hata</h3>
          <p className="text-theme-muted">{error}</p>
        </div>
      </div>
    );
  }

  // Mobile Layout - completely different design
  if (isMobile) {
    return <MobileDashboard />;
  }

  // Desktop Layout
  return (
    <div className="space-y-4 md:space-y-6 animate-fade-in">
      {/* Market Overview - Otomatik Güncellenen */}
      <MarketOverview />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 sm:gap-4 md:gap-6">
        {/* Left Column - Price & Chart */}
        <div className="lg:col-span-2 space-y-3 sm:space-y-4 md:space-y-6">
          {/* Current Price Card */}
          <div className="card p-3 sm:p-4 md:p-6 bg-gradient-to-br from-theme-card to-theme-card/50">
            <div className="flex flex-col gap-3 sm:gap-4">
              <div className="flex-1 w-full">
                <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 md:gap-3 mb-2">
                  <span className="px-2 sm:px-3 md:px-4 py-1 sm:py-1.5 md:py-2 rounded-lg sm:rounded-xl bg-primary-500/20 text-primary-400 font-bold text-sm sm:text-xl md:text-2xl border border-primary-500/30 ticker-badge">
                    {selectedTicker?.split(".")[0] || "THYAO"}
                  </span>
                  <span className="flex items-center gap-1 sm:gap-2 text-[10px] sm:text-xs md:text-sm text-success bg-success/10 px-1.5 sm:px-2 md:px-3 py-0.5 sm:py-1 md:py-1.5 rounded-md sm:rounded-lg">
                    <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-success animate-pulse" />
                    Canlı
                  </span>
                </div>
                
                <div className="flex flex-wrap items-baseline gap-1.5 sm:gap-2 md:gap-4 mb-2">
                  <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-theme-text price-display">
                    {formatCurrency(currentPrice)}
                  </h2>
                  <div
                    className={`flex items-center gap-1 sm:gap-1.5 md:gap-2 px-2 sm:px-2.5 md:px-4 py-1 sm:py-1.5 md:py-2 rounded-lg sm:rounded-xl text-xs sm:text-sm md:text-lg font-bold ${
                      isPositive
                        ? "bg-success/15 text-success"
                        : "bg-danger/15 text-danger"
                    }`}
                  >
                    {isPositive ? (
                      <ArrowUpRight className="w-3.5 h-3.5 sm:w-4 sm:h-4 md:w-5 md:h-5" />
                    ) : (
                      <ArrowDownRight className="w-3.5 h-3.5 sm:w-4 sm:h-4 md:w-5 md:h-5" />
                    )}
                    {changePercent >= 0 ? "+" : ""}
                    {changePercent.toFixed(2)}%
                  </div>
                </div>
                
                <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 md:gap-6 text-[10px] sm:text-xs md:text-sm text-theme-muted">
                  <span>
                    Değişim: <span className={isPositive ? "text-success" : "text-danger"}>
                      {formatCurrency(Math.abs(change))}
                    </span>
                  </span>
                  <span className="hidden sm:inline">•</span>
                  <span>Hacim: {formatVolume(latestData?.volume || stockInfo?.volume)}</span>
                </div>
              </div>
              
              {/* Signal Badge */}
              <div className="flex justify-center sm:justify-start">
                <div
                  className={`inline-flex flex-col items-center px-3 sm:px-4 md:px-6 py-2 sm:py-3 md:py-4 rounded-xl sm:rounded-2xl signal-badge ${
                    signal?.signal === "BUY"
                      ? "bg-success/15 border border-success/30 sm:border-2"
                      : signal?.signal === "SELL"
                        ? "bg-danger/15 border border-danger/30 sm:border-2"
                        : "bg-warning/15 border border-warning/30 sm:border-2"
                  }`}
                >
                  <Zap
                    className={`w-5 h-5 sm:w-6 sm:h-6 md:w-8 md:h-8 mb-1 sm:mb-2 ${
                      signal?.signal === "BUY"
                        ? "text-success"
                        : signal?.signal === "SELL"
                          ? "text-danger"
                          : "text-warning"
                    }`}
                  />
                  <p
                    className={`text-lg sm:text-xl md:text-2xl font-bold ${
                      signal?.signal === "BUY"
                        ? "text-success"
                        : signal?.signal === "SELL"
                          ? "text-danger"
                          : "text-warning"
                    }`}
                  >
                    {signal?.signal === "BUY"
                      ? "AL"
                      : signal?.signal === "SELL"
                        ? "SAT"
                        : "BEKLE"}
                  </p>
                  <p className="text-[10px] sm:text-xs text-theme-muted mt-0.5 sm:mt-1">
                    {signal?.confidence
                      ? `%${signal.confidence.toFixed(0)} Güven`
                      : "Hesaplanıyor"}
                  </p>
                </div>
              </div>
            </div>

            {/* Mini Chart */}
            <div className="h-20 mt-4 rounded-lg overflow-hidden bg-theme-card/50 p-2">
              {stockData?.data && (
                <MiniChart
                  data={stockData.data.slice(-50).map((d) => d.close)}
                  color={isPositive ? "#10b981" : "#ef4444"}
                  height={64}
                />
              )}
            </div>
          </div>

          {/* Chart Section */}
          <div className="card flex flex-col gap-3 sm:gap-4">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 sm:gap-3 min-w-0">
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-primary-500/10 flex items-center justify-center flex-shrink-0">
                  <LineChart className="w-4 h-4 sm:w-5 sm:h-5 text-primary-400" />
                </div>
                <div className="min-w-0">
                  <h3 className="font-bold text-sm sm:text-base md:text-lg text-theme-text truncate">Fiyat Grafiği</h3>
                  <p className="text-[10px] sm:text-xs text-theme-muted hidden sm:block">Teknik analiz ve indikatörler</p>
                </div>
              </div>
              <button
                onClick={() => setShowAdvancedIndicators(!showAdvancedIndicators)}
                className={`flex items-center gap-1 sm:gap-2 px-2 sm:px-3 md:px-4 py-1.5 sm:py-2 rounded-lg sm:rounded-xl text-xs sm:text-sm font-medium transition-all flex-shrink-0 ${
                  showAdvancedIndicators
                    ? "bg-primary-500 text-white shadow-lg shadow-primary-500/30"
                    : "bg-theme-card hover:bg-theme-card-hover text-theme-text border border-[var(--glass-border)]"
                }`}
              >
                <Settings className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                <span className="hidden sm:inline">İndikatörler</span>
                {showAdvancedIndicators ? (
                  <ChevronUp className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                ) : (
                  <ChevronDown className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                )}
              </button>
            </div>

            {showAdvancedIndicators && (
              <div className="p-3 sm:p-4 rounded-xl bg-theme-card/50 border border-[var(--glass-border)]">
                <IndicatorSelector
                  selectedIndicators={selectedIndicators}
                  onIndicatorsChange={setSelectedIndicators}
                />
              </div>
            )}

            {isLoading && !stockData?.data ? (
              <div className="flex items-center justify-center py-16">
                <LoadingSpinner message="Grafik yükleniyor..." />
              </div>
            ) : (
              <div className="chart-container !p-0 border-none bg-transparent">
                <StockChart
                  height={chartHeight || 400}
                  data={stockData?.data || []}
                  indicators={indicatorData}
                  selectedIndicators={selectedIndicators}
                />
              </div>
            )}
          </div>

          {/* Key Indicators Grid */}
          <div className="card">
            <div className="flex items-center justify-between gap-2 mb-3 sm:mb-4 md:mb-5">
              <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-accent-500/10 flex items-center justify-center flex-shrink-0">
                  <Target className="w-4 h-4 sm:w-5 sm:h-5 text-accent-400" />
                </div>
                <div className="min-w-0">
                  <h4 className="font-bold text-sm sm:text-base md:text-lg text-theme-text">Teknik Göstergeler</h4>
                  <p className="text-[10px] sm:text-xs text-theme-muted hidden sm:block">Anlık piyasa sinyalleri</p>
                </div>
              </div>
              <button
                onClick={() => setShowTechnicalIndicators(!showTechnicalIndicators)}
                className="lg:hidden flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium bg-theme-card hover:bg-theme-card-hover border border-[var(--glass-border)] transition-all flex-shrink-0"
              >
                {showTechnicalIndicators ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </button>
            </div>
            
            {showTechnicalIndicators && (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2 sm:gap-3 md:gap-4">
              {[
                {
                  name: "RSI",
                  value:
                    indicatorData?.rsi_14?.toFixed(1) ||
                    indicatorData?.rsi?.toFixed(1) ||
                    "—",
                  status:
                    (indicatorData?.rsi_14 || indicatorData?.rsi) > 70
                      ? "danger"
                      : (indicatorData?.rsi_14 || indicatorData?.rsi) < 30
                        ? "success"
                        : "neutral",
                  hint:
                    (indicatorData?.rsi_14 || indicatorData?.rsi) > 70
                      ? "Aşırı Alım"
                      : (indicatorData?.rsi_14 || indicatorData?.rsi) < 30
                        ? "Aşırı Satım"
                        : "Nötr",
                },
                {
                  name: "MACD",
                  value: indicatorData?.macd?.toFixed(2) || "—",
                  status:
                    indicatorData?.macd > 0
                      ? "success"
                      : indicatorData?.macd < 0
                        ? "danger"
                        : "neutral",
                  hint:
                    indicatorData?.macd > 0
                      ? "Yükseliş"
                      : indicatorData?.macd < 0
                        ? "Düşüş"
                        : "Nötr",
                },
                {
                  name: "ADX",
                  value: indicatorData?.adx?.toFixed(1) || "—",
                  status: indicatorData?.adx > 25 ? "success" : "neutral",
                  hint: indicatorData?.adx > 25 ? "Güçlü Trend" : "Zayıf Trend",
                },
                {
                  name: "ATR",
                  value: indicatorData?.atr?.toFixed(2) || "—",
                  status: "neutral",
                  hint: "Volatilite",
                },
                {
                  name: "Stoch %K",
                  value:
                    indicatorData?.stoch_k?.toFixed(1) ||
                    indicatorData?.stochastic_k?.toFixed(1) ||
                    "—",
                  status:
                    (indicatorData?.stoch_k || indicatorData?.stochastic_k) > 80
                      ? "danger"
                      : (indicatorData?.stoch_k || indicatorData?.stochastic_k) < 20
                        ? "success"
                        : "neutral",
                  hint:
                    (indicatorData?.stoch_k || indicatorData?.stochastic_k) > 80
                      ? "Aşırı Alım"
                      : (indicatorData?.stoch_k || indicatorData?.stochastic_k) < 20
                        ? "Aşırı Satım"
                        : "Nötr",
                },
                {
                  name: "MFI",
                  value: indicatorData?.mfi?.toFixed(1) || "—",
                  status:
                    indicatorData?.mfi > 80
                      ? "danger"
                      : indicatorData?.mfi < 20
                        ? "success"
                        : "neutral",
                  hint:
                    indicatorData?.mfi > 80
                      ? "Aşırı Alım"
                      : indicatorData?.mfi < 20
                        ? "Aşırı Satım"
                        : "Nötr",
                },
                {
                  name: "EMA 20",
                  value:
                    indicatorData?.ema_20?.toFixed(2) ||
                    indicatorData?.ema_9?.toFixed(2) ||
                    "—",
                  status:
                    latestData?.close > (indicatorData?.ema_20 || indicatorData?.ema_9)
                      ? "success"
                      : "danger",
                  hint:
                    latestData?.close > (indicatorData?.ema_20 || indicatorData?.ema_9)
                      ? "Fiyat Üstünde"
                      : "Fiyat Altında",
                },
                {
                  name: "VWAP",
                  value: indicatorData?.vwap?.toFixed(2) || "—",
                  status:
                    latestData?.close > indicatorData?.vwap
                      ? "success"
                      : latestData?.close < indicatorData?.vwap
                        ? "danger"
                        : "neutral",
                  hint:
                    latestData?.close > indicatorData?.vwap
                      ? "Fiyat Üstünde"
                      : "Fiyat Altında",
                },
              ].map((ind, i) => (
                <div
                  key={i}
                  className="group relative p-2 sm:p-3 md:p-4 rounded-lg sm:rounded-xl bg-gradient-to-br from-theme-card to-theme-card/50 border border-[var(--glass-border)] hover:border-primary-500/50 hover:shadow-lg hover:shadow-primary-500/10 transition-all duration-300"
                >
                  <div className="flex items-center justify-between mb-1 sm:mb-2">
                    <p className="text-[10px] sm:text-xs font-medium text-theme-muted uppercase tracking-wider">
                      {ind.name}
                    </p>
                    <span
                      className={`w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full ${
                        ind.status === "success"
                          ? "bg-success animate-pulse"
                          : ind.status === "danger"
                            ? "bg-danger animate-pulse"
                            : "bg-theme-muted"
                      }`}
                    />
                  </div>
                  <p
                    className={`text-base sm:text-lg md:text-2xl font-bold mb-0.5 sm:mb-1 ${
                      ind.status === "success"
                        ? "text-success"
                        : ind.status === "danger"
                          ? "text-danger"
                          : "text-theme-text"
                    }`}
                  >
                    {ind.value}
                  </p>
                  <p className="text-[9px] sm:text-xs text-theme-muted">{ind.hint}</p>
                </div>
              ))}
            </div>
            )}
          </div>
        </div>

        {/* Right Sidebar - Hidden on mobile, shows on lg+ */}
        <div ref={sidebarRef} className="hidden lg:block lg:col-span-1 space-y-4 md:space-y-6">
          {/* Trading Stats */}
          <div className="card p-5">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-success/10 flex items-center justify-center">
                <DollarSign className="w-5 h-5 text-success" />
              </div>
              <div>
                <h4 className="font-bold text-theme-text">Günlük İstatistikler</h4>
                <p className="text-xs text-theme-muted">Piyasa performansı</p>
              </div>
            </div>
            
            <div className="space-y-3">
              {[
                {
                  label: "En Yüksek",
                  value: formatCurrency(latestData?.high),
                  color: "text-success",
                  icon: ArrowUpRight,
                  bg: "bg-success/10",
                },
                {
                  label: "En Düşük",
                  value: formatCurrency(latestData?.low),
                  color: "text-danger",
                  icon: ArrowDownRight,
                  bg: "bg-danger/10",
                },
                {
                  label: "Açılış",
                  value: formatCurrency(latestData?.open),
                  color: "text-theme-text",
                  icon: Clock,
                  bg: "bg-primary-500/10",
                },
                {
                  label: "Önceki Kapanış",
                  value: formatCurrency(stockInfo?.previous_close),
                  color: "text-theme-muted",
                  icon: Shield,
                  bg: "bg-theme-card",
                },
              ].map((stat, i) => {
                const Icon = stat.icon;
                return (
                  <div
                    key={i}
                    className="flex items-center justify-between p-3 rounded-xl bg-theme-card/50 border border-[var(--glass-border)] hover:border-primary-500/30 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-lg ${stat.bg} flex items-center justify-center`}>
                        <Icon className={`w-4 h-4 ${stat.color}`} />
                      </div>
                      <span className="text-sm font-medium text-theme-muted">
                        {stat.label}
                      </span>
                    </div>
                    <span className={`font-bold ${stat.color}`}>
                      {stat.value}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Top Movers */}
          <TopMovers refreshInterval={30000} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
