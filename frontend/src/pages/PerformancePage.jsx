/**
 * Performance Page - Comprehensive Performance Analytics
 * Equity curve, drawdown, win rate analysis, risk metrics, and BIST100 comparison
 */
import React, { useState, useMemo, useEffect } from "react";
import {
  TrendingUp,
  TrendingDown,
  Target,
  Award,
  BarChart3,
  Plus,
  Trash2,
  Edit2,
  DollarSign,
  Percent,
  Calendar,
  Clock,
  Filter,
  Download,
  RefreshCw,
  X,
  Check,
  AlertTriangle,
  Activity,
  Shield,
  PieChart as PieChartIcon,
  LineChart as LineChartIcon,
} from "lucide-react";
import { usePortfolioStore } from "../store/portfolioStore";
import { formatCurrency, formatPercent } from "../utils/formatters";
import { BIST30_STOCKS } from "../config/stocks";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
  Area,
  AreaChart,
  ComposedChart,
} from "recharts";
import MobilePerformancePage from "./mobile/MobilePerformancePage";

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

const COLORS = [
  "#10b981",
  "#ef4444",
  "#f59e0b",
  "#0ea5e9",
  "#8b5cf6",
  "#ec4899",
];

const PerformancePage = () => {
  const isMobile = useIsMobile();
  
  // Early return for mobile view
  if (isMobile) {
    return <MobilePerformancePage />;
  }

  const {
    trades,
    addTrade,
    removeTrade,
    updateTrade,
    clearAllTrades,
    getTradeStats,
    getRealizedPnL,
    getUnrealizedPnL,
    getTotalPnL,
    getDailyPnL,
    getWeeklyPnL,
    getMonthlyPnL,
    getTopPerformers,
    holdings,
    equityHistory,
    getDrawdownData,
    getMaxDrawdown,
  } = usePortfolioStore();

  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [filterPeriod, setFilterPeriod] = useState("all");
  const [filterType, setFilterType] = useState("all");
  const [chartView, setChartView] = useState("equity"); // equity, drawdown, comparison
  const [timeframe, setTimeframe] = useState("all"); // 1D, 1W, 1M, 3M, 1Y, all
  const [newTrade, setNewTrade] = useState({
    ticker: "",
    type: "BUY",
    quantity: "",
    buyPrice: "",
    sellPrice: "",
    status: "open",
    date: new Date().toISOString().split("T")[0],
    notes: "",
  });

  const stats = getTradeStats();
  const realizedPnL = getRealizedPnL();
  const unrealizedPnL = getUnrealizedPnL();
  const totalPnL = getTotalPnL();
  const dailyPnL = getDailyPnL();
  const weeklyPnL = getWeeklyPnL();
  const monthlyPnL = getMonthlyPnL();
  const topPerformers = getTopPerformers();
  const drawdownData = getDrawdownData();
  const maxDrawdown = getMaxDrawdown();

  // Filter trades based on period and type
  const filteredTrades = useMemo(() => {
    let filtered = [...trades];

    // Filter by period
    if (filterPeriod !== "all") {
      const now = new Date();
      let startDate = new Date();

      switch (filterPeriod) {
        case "today":
          startDate.setHours(0, 0, 0, 0);
          break;
        case "week":
          startDate.setDate(now.getDate() - 7);
          break;
        case "month":
          startDate.setMonth(now.getMonth() - 1);
          break;
        case "3months":
          startDate.setMonth(now.getMonth() - 3);
          break;
      }

      filtered = filtered.filter((t) => new Date(t.createdAt) >= startDate);
    }

    // Filter by type
    if (filterType !== "all") {
      filtered = filtered.filter((t) => t.status === filterType);
    }

    return filtered.sort(
      (a, b) => new Date(b.createdAt) - new Date(a.createdAt)
    );
  }, [trades, filterPeriod, filterType]);

  // Calculate PnL for a trade
  const calculatePnL = (trade) => {
    if (trade.status === "closed" && trade.sellPrice) {
      return (trade.sellPrice - trade.buyPrice) * trade.quantity;
    }
    return 0;
  };

  // Handle form submit
  const handleSubmit = (e) => {
    e.preventDefault();

    const tradeData = {
      ...newTrade,
      quantity: parseFloat(newTrade.quantity),
      buyPrice: parseFloat(newTrade.buyPrice),
      sellPrice: newTrade.sellPrice ? parseFloat(newTrade.sellPrice) : null,
      pnl:
        newTrade.status === "closed" && newTrade.sellPrice
          ? (parseFloat(newTrade.sellPrice) - parseFloat(newTrade.buyPrice)) *
            parseFloat(newTrade.quantity)
          : 0,
      closedAt: newTrade.status === "closed" ? new Date().toISOString() : null,
    };

    if (editingId) {
      updateTrade(editingId, tradeData);
      setEditingId(null);
    } else {
      addTrade(tradeData);
    }

    setNewTrade({
      ticker: "",
      type: "BUY",
      quantity: "",
      buyPrice: "",
      sellPrice: "",
      status: "open",
      date: new Date().toISOString().split("T")[0],
      notes: "",
    });
    setShowAddForm(false);
  };

  // Handle edit
  const handleEdit = (trade) => {
    setEditingId(trade.id);
    setNewTrade({
      ticker: trade.ticker,
      type: trade.type || "BUY",
      quantity: trade.quantity.toString(),
      buyPrice: trade.buyPrice.toString(),
      sellPrice: trade.sellPrice?.toString() || "",
      status: trade.status,
      date: trade.date || new Date().toISOString().split("T")[0],
      notes: trade.notes || "",
    });
    setShowAddForm(true);
  };

  // Close trade (sell)
  const handleCloseTrade = async (trade) => {
    const sellPrice = prompt(
      "Satış fiyatını girin:",
      trade.buyPrice.toString()
    );
    if (sellPrice) {
      const pnl = (parseFloat(sellPrice) - trade.buyPrice) * trade.quantity;
      updateTrade(trade.id, {
        status: "closed",
        sellPrice: parseFloat(sellPrice),
        pnl,
        closedAt: new Date().toISOString(),
      });
    }
  };

  // Prepare chart data
  const pnlDistributionData = [
    { name: "Kazançlı", value: stats.winningTrades, color: "#10b981" },
    { name: "Zararlı", value: stats.losingTrades, color: "#ef4444" },
  ].filter((d) => d.value > 0);

  // Equity curve data with timeframe filter
  const equityCurveData = useMemo(() => {
    if (!equityHistory || equityHistory.length === 0) {
      return [{ date: new Date().toLocaleDateString("tr-TR"), equity: 0 }];
    }

    let filtered = [...equityHistory];
    const now = new Date();

    switch (timeframe) {
      case "1D":
        filtered = filtered.filter(
          (point) => new Date(point.timestamp) >= new Date(now.setDate(now.getDate() - 1))
        );
        break;
      case "1W":
        filtered = filtered.filter(
          (point) => new Date(point.timestamp) >= new Date(now.setDate(now.getDate() - 7))
        );
        break;
      case "1M":
        filtered = filtered.filter(
          (point) => new Date(point.timestamp) >= new Date(now.setMonth(now.getMonth() - 1))
        );
        break;
      case "3M":
        filtered = filtered.filter(
          (point) => new Date(point.timestamp) >= new Date(now.setMonth(now.getMonth() - 3))
        );
        break;
      case "1Y":
        filtered = filtered.filter(
          (point) => new Date(point.timestamp) >= new Date(now.setFullYear(now.getFullYear() - 1))
        );
        break;
    }

    return filtered.map((point) => ({
      date: new Date(point.timestamp).toLocaleDateString("tr-TR", {
        day: "2-digit",
        month: "2-digit",
      }),
      equity: point.value,
    }));
  }, [equityHistory, timeframe]);

  // Drawdown chart data
  const drawdownChartData = useMemo(() => {
    if (!drawdownData || drawdownData.length === 0) return [];

    return drawdownData.map((point) => ({
      date: new Date(point.timestamp).toLocaleDateString("tr-TR", {
        day: "2-digit",
        month: "2-digit",
      }),
      drawdown: point.drawdown,
      peak: point.peak,
    }));
  }, [drawdownData]);

  // Win rate breakdown by period
  const winRateBreakdown = useMemo(() => {
    const getWinRate = (startDate) => {
      const filtered = trades.filter(
        (t) => t.status === "closed" && new Date(t.closedAt) >= startDate
      );
      const winning = filtered.filter((t) => (t.pnl || 0) > 0).length;
      return filtered.length > 0 ? (winning / filtered.length) * 100 : 0;
    };

    const now = new Date();
    return [
      {
        period: "Günlük",
        winRate: getWinRate(new Date(now.setDate(now.getDate() - 1))),
      },
      {
        period: "Haftalık",
        winRate: getWinRate(new Date(now.setDate(now.getDate() - 7))),
      },
      {
        period: "Aylık",
        winRate: getWinRate(new Date(now.setMonth(now.getMonth() - 1))),
      },
    ];
  }, [trades]);

  // Risk metrics
  const riskMetrics = useMemo(() => {
    const closedTrades = trades.filter((t) => t.status === "closed");
    if (closedTrades.length === 0)
      return {
        sharpeRatio: 0,
        sortinoRatio: 0,
        maxDrawdown: 0,
        recoveryFactor: 0,
        winLossRatio: 0,
      };

    const returns = closedTrades.map((t) => (t.pnl || 0) / (t.buyPrice * t.quantity));
    const avgReturn = returns.reduce((a, b) => a + b, 0) / returns.length;
    const stdDev = Math.sqrt(
      returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length
    );

    const downside = returns.filter((r) => r < 0);
    const downsideStdDev =
      downside.length > 0
        ? Math.sqrt(
            downside.reduce((sum, r) => sum + Math.pow(r, 2), 0) / downside.length
          )
        : 0;

    return {
      sharpeRatio: stdDev !== 0 ? avgReturn / stdDev : 0,
      sortinoRatio: downsideStdDev !== 0 ? avgReturn / downsideStdDev : 0,
      maxDrawdown: maxDrawdown,
      recoveryFactor: maxDrawdown !== 0 ? realizedPnL / Math.abs(maxDrawdown) : 0,
      winLossRatio: stats.avgLoss !== 0 ? stats.avgWin / stats.avgLoss : 0,
    };
  }, [trades, maxDrawdown, realizedPnL, stats]);

  // Monthly PnL chart data
  const monthlyChartData = useMemo(() => {
    const monthlyData = {};
    trades
      .filter((t) => t.status === "closed")
      .forEach((t) => {
        const month = new Date(t.closedAt || t.createdAt).toLocaleString(
          "tr-TR",
          { month: "short", year: "2-digit" }
        );
        if (!monthlyData[month]) {
          monthlyData[month] = { month, pnl: 0, trades: 0 };
        }
        monthlyData[month].pnl += t.pnl || 0;
        monthlyData[month].trades += 1;
      });
    return Object.values(monthlyData).slice(-6);
  }, [trades]);

  return (
    <div className="space-y-3 sm:space-y-4 md:space-y-6 animate-fade-in">
      {/* PnL Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-3 md:gap-4">
        {/* Toplam PnL */}
        <div
          className={`stat-card p-2 sm:p-3 ${
            totalPnL >= 0 ? "border-green-500/30" : "border-red-500/30"
          }`}
        >
          <div className={`stat-icon w-7 h-7 sm:w-8 sm:h-8 ${totalPnL >= 0 ? "success" : "danger"}`}>
            <DollarSign className="w-3.5 h-3.5 sm:w-4 sm:h-4 md:w-5 md:h-5" />
          </div>
          <div>
            <p className="text-[9px] sm:text-[10px] md:text-xs text-theme-muted">Toplam PnL</p>
            <p
              className={`text-sm sm:text-base md:text-xl font-bold ${
                totalPnL >= 0 ? "text-green-500" : "text-red-500"
              }`}
            >
              {totalPnL >= 0 ? "+" : ""}
              {formatCurrency(totalPnL)}
            </p>
          </div>
        </div>

        {/* Gerçekleşmiş PnL */}
        <div
          className={`stat-card p-2 sm:p-3 ${
            realizedPnL >= 0 ? "border-green-500/30" : "border-red-500/30"
          }`}
        >
          <div
            className={`stat-icon w-7 h-7 sm:w-8 sm:h-8 ${realizedPnL >= 0 ? "success" : "danger"}`}
          >
            <Check className="w-3.5 h-3.5 sm:w-4 sm:h-4 md:w-5 md:h-5" />
          </div>
          <div>
            <p className="text-[9px] sm:text-[10px] md:text-xs text-theme-muted">Gerçekleşmiş</p>
            <p
              className={`text-sm sm:text-base md:text-xl font-bold ${
                realizedPnL >= 0 ? "text-green-500" : "text-red-500"
              }`}
            >
              {realizedPnL >= 0 ? "+" : ""}
              {formatCurrency(realizedPnL)}
            </p>
          </div>
        </div>

        {/* Gerçekleşmemiş PnL */}
        <div
          className={`stat-card p-2 sm:p-3 ${
            unrealizedPnL >= 0 ? "border-green-500/30" : "border-red-500/30"
          }`}
        >
          <div
            className={`stat-icon w-7 h-7 sm:w-8 sm:h-8 ${unrealizedPnL >= 0 ? "warning" : "danger"}`}
          >
            <Clock className="w-4 h-4 sm:w-5 sm:h-5" />
          </div>
          <div>
            <p className="text-[9px] sm:text-[10px] md:text-xs text-theme-muted">Açık Pozisyon</p>
            <p
              className={`text-sm sm:text-base md:text-xl font-bold ${
                unrealizedPnL >= 0 ? "text-green-500" : "text-red-500"
              }`}
            >
              {unrealizedPnL >= 0 ? "+" : ""}
              {formatCurrency(unrealizedPnL)}
            </p>
          </div>
        </div>

        {/* Kazanma Oranı */}
        <div className="stat-card p-2 sm:p-3">
          <div className="stat-icon primary w-7 h-7 sm:w-8 sm:h-8">
            <Target className="w-4 h-4 sm:w-5 sm:h-5" />
          </div>
          <div>
            <p className="text-[9px] sm:text-[10px] md:text-xs text-theme-muted">Kazanma Oranı</p>
            <p className="text-sm sm:text-base md:text-xl font-bold text-theme-text">
              %{stats.winRate.toFixed(1)}
            </p>
          </div>
        </div>
      </div>

      {/* Period PnL Cards */}
      <div className="grid grid-cols-3 gap-2 sm:gap-3 md:gap-4">
        <div
          className={`card p-2 sm:p-3 md:p-4 ${
            dailyPnL >= 0 ? "border-green-500/20" : "border-red-500/20"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] sm:text-xs md:text-sm text-theme-muted">Bugün</span>
            <Calendar className="w-3 h-3 sm:w-4 sm:h-4 text-theme-muted" />
          </div>
          <p
            className={`text-sm sm:text-base md:text-lg font-bold mt-1 ${
              dailyPnL >= 0 ? "text-green-500" : "text-red-500"
            }`}
          >
            {dailyPnL >= 0 ? "+" : ""}
            {formatCurrency(dailyPnL)}
          </p>
        </div>

        <div
          className={`card p-2 sm:p-3 md:p-4 ${
            weeklyPnL >= 0 ? "border-green-500/20" : "border-red-500/20"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] sm:text-xs md:text-sm text-theme-muted">Bu Hafta</span>
            <Calendar className="w-3 h-3 sm:w-4 sm:h-4 text-theme-muted" />
          </div>
          <p
            className={`text-sm sm:text-base md:text-lg font-bold mt-1 ${
              weeklyPnL >= 0 ? "text-green-500" : "text-red-500"
            }`}
          >
            {weeklyPnL >= 0 ? "+" : ""}
            {formatCurrency(weeklyPnL)}
          </p>
        </div>

        <div
          className={`card p-2 sm:p-3 md:p-4 ${
            monthlyPnL >= 0 ? "border-green-500/20" : "border-red-500/20"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] sm:text-xs md:text-sm text-theme-muted">Bu Ay</span>
            <Calendar className="w-3 h-3 sm:w-4 sm:h-4 text-theme-muted" />
          </div>
          <p
            className={`text-sm sm:text-base md:text-lg font-bold mt-1 ${
              monthlyPnL >= 0 ? "text-green-500" : "text-red-500"
            }`}
          >
            {monthlyPnL >= 0 ? "+" : ""}
            {formatCurrency(monthlyPnL)}
          </p>
        </div>
      </div>

      {/* Equity Curve & Analytics Section */}
      <div className="card p-3 sm:p-4 md:p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <LineChartIcon className="w-5 h-5 text-primary" />
            Performans Analizi
          </h3>
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setChartView("equity")}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                chartView === "equity"
                  ? "bg-primary text-white"
                  : "bg-[var(--color-bg-secondary)] text-theme-muted hover:text-theme-text"
              }`}
            >
              Equity Curve
            </button>
            <button
              onClick={() => setChartView("drawdown")}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                chartView === "drawdown"
                  ? "bg-primary text-white"
                  : "bg-[var(--color-bg-secondary)] text-theme-muted hover:text-theme-text"
              }`}
            >
              Drawdown
            </button>
            <button
              onClick={() => setChartView("winrate")}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                chartView === "winrate"
                  ? "bg-primary text-white"
                  : "bg-[var(--color-bg-secondary)] text-theme-muted hover:text-theme-text"
              }`}
            >
              Win Rate
            </button>
          </div>
        </div>

        {/* Timeframe Selector */}
        <div className="flex gap-1 sm:gap-2 mb-4 overflow-x-auto pb-2 scrollbar-hide">
          {["1D", "1W", "1M", "3M", "1Y", "all"].map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-3 py-1 rounded text-xs transition-colors ${
                timeframe === tf
                  ? "bg-primary/20 text-primary"
                  : "bg-[var(--color-bg-secondary)] text-theme-muted hover:text-theme-text"
              }`}
            >
              {tf === "all" ? "Tümü" : tf}
            </button>
          ))}
        </div>

        {/* Chart Display */}
        <div className="h-48 sm:h-64 md:h-80">
          <ResponsiveContainer width="100%" height="100%">
            {chartView === "equity" ? (
              <AreaChart data={equityCurveData}>
                <defs>
                  <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="date" stroke="var(--color-text-muted)" fontSize={12} />
                <YAxis stroke="var(--color-text-muted)" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--color-bg-secondary)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "8px",
                  }}
                  formatter={(value) => formatCurrency(value)}
                />
                <Area
                  type="monotone"
                  dataKey="equity"
                  stroke="#10b981"
                  strokeWidth={2}
                  fill="url(#colorEquity)"
                />
              </AreaChart>
            ) : chartView === "drawdown" ? (
              <ComposedChart data={drawdownChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="date" stroke="var(--color-text-muted)" fontSize={12} />
                <YAxis stroke="var(--color-text-muted)" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--color-bg-secondary)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "8px",
                  }}
                  formatter={(value) => `${value.toFixed(2)}%`}
                />
                <Line
                  type="monotone"
                  dataKey="peak"
                  stroke="#10b981"
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  dot={false}
                  name="Peak"
                />
                <Area
                  type="monotone"
                  dataKey="drawdown"
                  fill="#ef4444"
                  stroke="#ef4444"
                  fillOpacity={0.3}
                  name="Drawdown"
                />
              </ComposedChart>
            ) : (
              <BarChart data={winRateBreakdown}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="period" stroke="var(--color-text-muted)" fontSize={12} />
                <YAxis stroke="var(--color-text-muted)" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--color-bg-secondary)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "8px",
                  }}
                  formatter={(value) => `${value.toFixed(1)}%`}
                />
                <Bar dataKey="winRate" fill="#10b981" radius={[8, 8, 0, 0]} />
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
      </div>

      {/* Risk Metrics Dashboard */}
      <div className="card p-3 sm:p-4 md:p-6">
        <h3 className="text-sm sm:text-base md:text-lg font-semibold mb-3 sm:mb-4 flex items-center gap-2">
          <Shield className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />
          Risk Metrikleri
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2 sm:gap-3 md:gap-4">
          <div className="p-2 sm:p-3 md:p-4 rounded-lg sm:rounded-xl bg-[var(--color-bg-secondary)]">
            <p className="text-[10px] sm:text-xs text-theme-muted mb-1">Sharpe Ratio</p>
            <p className="text-sm sm:text-base md:text-lg font-bold text-theme-text">
              {riskMetrics.sharpeRatio.toFixed(2)}
            </p>
          </div>
          <div className="p-4 rounded-xl bg-[var(--color-bg-secondary)]">
            <p className="text-xs text-theme-muted mb-1">Sortino Ratio</p>
            <p className="text-lg font-bold text-theme-text">
              {riskMetrics.sortinoRatio.toFixed(2)}
            </p>
          </div>
          <div className="p-4 rounded-xl bg-[var(--color-bg-secondary)]">
            <p className="text-xs text-theme-muted mb-1">Max Drawdown</p>
            <p className="text-lg font-bold text-red-500">
              {riskMetrics.maxDrawdown.toFixed(2)}%
            </p>
          </div>
          <div className="p-4 rounded-xl bg-[var(--color-bg-secondary)]">
            <p className="text-xs text-theme-muted mb-1">Recovery Factor</p>
            <p className="text-lg font-bold text-theme-text">
              {riskMetrics.recoveryFactor.toFixed(2)}
            </p>
          </div>
          <div className="p-4 rounded-xl bg-[var(--color-bg-secondary)]">
            <p className="text-xs text-theme-muted mb-1">Win/Loss Ratio</p>
            <p className="text-lg font-bold text-theme-text">
              {riskMetrics.winLossRatio.toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      {/* Stats & Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trade Statistics */}
        <div className="card p-5">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-primary" />
            İşlem İstatistikleri
          </h3>

          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 rounded-xl bg-[var(--color-bg-secondary)]">
              <span className="text-theme-muted">Toplam İşlem</span>
              <span className="font-semibold text-theme-text">
                {stats.totalTrades}
              </span>
            </div>

            <div className="flex justify-between items-center p-3 rounded-xl bg-green-500/10">
              <span className="text-green-500">Kazançlı</span>
              <span className="font-semibold text-green-500">
                {stats.winningTrades}
              </span>
            </div>

            <div className="flex justify-between items-center p-3 rounded-xl bg-red-500/10">
              <span className="text-red-500">Zararlı</span>
              <span className="font-semibold text-red-500">
                {stats.losingTrades}
              </span>
            </div>

            <div className="flex justify-between items-center p-3 rounded-xl bg-[var(--color-bg-secondary)]">
              <span className="text-theme-muted">Profit Factor</span>
              <span
                className={`font-semibold ${
                  stats.profitFactor >= 1.5
                    ? "text-green-500"
                    : "text-yellow-500"
                }`}
              >
                {stats.profitFactor === Infinity
                  ? "∞"
                  : stats.profitFactor.toFixed(2)}
              </span>
            </div>

            <div className="flex justify-between items-center p-3 rounded-xl bg-[var(--color-bg-secondary)]">
              <span className="text-theme-muted">Ort. Kazanç</span>
              <span className="font-semibold text-green-500">
                +{formatCurrency(stats.avgWin)}
              </span>
            </div>

            <div className="flex justify-between items-center p-3 rounded-xl bg-[var(--color-bg-secondary)]">
              <span className="text-theme-muted">Ort. Kayıp</span>
              <span className="font-semibold text-red-500">
                -{formatCurrency(stats.avgLoss)}
              </span>
            </div>
          </div>
        </div>

        {/* Win/Loss Distribution */}
        <div className="card p-5">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-primary" />
            Kazanç/Kayıp Dağılımı
          </h3>

          {pnlDistributionData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={pnlDistributionData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pnlDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value) => [`${value} işlem`, ""]}
                  contentStyle={{
                    backgroundColor: "var(--color-card)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "8px",
                  }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-theme-muted">
              Henüz kapatılmış işlem yok
            </div>
          )}
        </div>

        {/* Top Performers */}
        <div className="card p-5">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Award className="w-5 h-5 text-primary" />
            En İyi Hisseler
          </h3>

          {topPerformers.length > 0 ? (
            <div className="space-y-3">
              {topPerformers.slice(0, 5).map((item, index) => (
                <div
                  key={item.ticker}
                  className="flex items-center justify-between p-3 rounded-xl bg-[var(--color-bg-secondary)]"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                        index === 0
                          ? "bg-yellow-500/20 text-yellow-500"
                          : index === 1
                          ? "bg-gray-400/20 text-gray-400"
                          : index === 2
                          ? "bg-orange-500/20 text-orange-500"
                          : "bg-[var(--color-bg-secondary)] text-theme-muted"
                      }`}
                    >
                      {index + 1}
                    </span>
                    <span className="font-medium text-theme-text">
                      {item.ticker}
                    </span>
                  </div>
                  <div className="text-right">
                    <p
                      className={`font-semibold ${
                        item.pnl >= 0 ? "text-green-500" : "text-red-500"
                      }`}
                    >
                      {item.pnl >= 0 ? "+" : ""}
                      {formatCurrency(item.pnl)}
                    </p>
                    <p className="text-xs text-theme-muted">
                      {item.trades} işlem
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-48 text-theme-muted">
              Henüz işlem yok
            </div>
          )}
        </div>
      </div>

      {/* Monthly PnL Chart */}
      {monthlyChartData.length > 0 && (
        <div className="card p-5">
          <h3 className="text-lg font-semibold mb-4">Aylık PnL Grafiği</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={monthlyChartData}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--color-border)"
              />
              <XAxis dataKey="month" stroke="var(--color-muted)" />
              <YAxis stroke="var(--color-muted)" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "var(--color-card)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "8px",
                }}
                formatter={(value) => [formatCurrency(value), "PnL"]}
              />
              <Bar dataKey="pnl" fill="#0ea5e9" radius={[4, 4, 0, 0]}>
                {monthlyChartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.pnl >= 0 ? "#10b981" : "#ef4444"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Trade List */}
      <div className="card">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 border-b border-theme-border">
          <h3 className="text-lg font-semibold">İşlem Geçmişi</h3>

          <div className="flex flex-wrap items-center gap-3">
            {/* Period Filter */}
            <select
              value={filterPeriod}
              onChange={(e) => setFilterPeriod(e.target.value)}
              className="input py-2 px-3 w-auto text-sm"
            >
              <option value="all">Tüm Zamanlar</option>
              <option value="today">Bugün</option>
              <option value="week">Bu Hafta</option>
              <option value="month">Bu Ay</option>
              <option value="3months">Son 3 Ay</option>
            </select>

            {/* Status Filter */}
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="input py-2 px-3 w-auto text-sm"
            >
              <option value="all">Tüm İşlemler</option>
              <option value="open">Açık</option>
              <option value="closed">Kapalı</option>
            </select>

            {/* Add Trade Button */}
            <button
              onClick={() => {
                setEditingId(null);
                setNewTrade({
                  ticker: "",
                  type: "BUY",
                  quantity: "",
                  buyPrice: "",
                  sellPrice: "",
                  status: "open",
                  date: new Date().toISOString().split("T")[0],
                  notes: "",
                });
                setShowAddForm(true);
              }}
              className="btn btn-primary"
            >
              <Plus className="w-4 h-4" />
              Yeni İşlem
            </button>
          </div>
        </div>

        {/* Add/Edit Form */}
        {showAddForm && (
          <div className="p-5 border-b border-theme-border bg-[var(--color-bg-secondary)]">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm text-theme-muted mb-1">
                    Hisse
                  </label>
                  <select
                    value={newTrade.ticker}
                    onChange={(e) =>
                      setNewTrade({ ...newTrade, ticker: e.target.value })
                    }
                    className="input"
                    required
                  >
                    <option value="">Seçin...</option>
                    {BIST30_STOCKS.map((stock) => (
                      <option key={stock.ticker} value={stock.ticker}>
                        {stock.ticker.replace(".IS", "")} - {stock.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-theme-muted mb-1">
                    Adet
                  </label>
                  <input
                    type="number"
                    value={newTrade.quantity}
                    onChange={(e) =>
                      setNewTrade({ ...newTrade, quantity: e.target.value })
                    }
                    className="input"
                    placeholder="0"
                    required
                    min="1"
                  />
                </div>

                <div>
                  <label className="block text-sm text-theme-muted mb-1">
                    Alış Fiyatı
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={newTrade.buyPrice}
                    onChange={(e) =>
                      setNewTrade({ ...newTrade, buyPrice: e.target.value })
                    }
                    className="input"
                    placeholder="0.00"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm text-theme-muted mb-1">
                    Durum
                  </label>
                  <select
                    value={newTrade.status}
                    onChange={(e) =>
                      setNewTrade({ ...newTrade, status: e.target.value })
                    }
                    className="input"
                  >
                    <option value="open">Açık (Beklemede)</option>
                    <option value="closed">Kapalı (Satıldı)</option>
                  </select>
                </div>
              </div>

              {newTrade.status === "closed" && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm text-theme-muted mb-1">
                      Satış Fiyatı
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={newTrade.sellPrice}
                      onChange={(e) =>
                        setNewTrade({ ...newTrade, sellPrice: e.target.value })
                      }
                      className="input"
                      placeholder="0.00"
                      required
                    />
                  </div>

                  {newTrade.buyPrice &&
                    newTrade.sellPrice &&
                    newTrade.quantity && (
                      <div className="col-span-3 flex items-center">
                        <div
                          className={`p-3 rounded-xl ${
                            (parseFloat(newTrade.sellPrice) -
                              parseFloat(newTrade.buyPrice)) *
                              parseFloat(newTrade.quantity) >=
                            0
                              ? "bg-green-500/10 text-green-500"
                              : "bg-red-500/10 text-red-500"
                          }`}
                        >
                          Tahmini PnL:{" "}
                          {formatCurrency(
                            (parseFloat(newTrade.sellPrice) -
                              parseFloat(newTrade.buyPrice)) *
                              parseFloat(newTrade.quantity)
                          )}
                        </div>
                      </div>
                    )}
                </div>
              )}

              <div>
                <label className="block text-sm text-theme-muted mb-1">
                  Not (Opsiyonel)
                </label>
                <input
                  type="text"
                  value={newTrade.notes}
                  onChange={(e) =>
                    setNewTrade({ ...newTrade, notes: e.target.value })
                  }
                  className="input"
                  placeholder="İşlem hakkında not..."
                />
              </div>

              <div className="flex gap-3">
                <button type="submit" className="btn btn-primary">
                  <Check className="w-4 h-4" />
                  {editingId ? "Güncelle" : "Ekle"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowAddForm(false);
                    setEditingId(null);
                  }}
                  className="btn btn-secondary"
                >
                  <X className="w-4 h-4" />
                  İptal
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Trade List */}
        <div className="overflow-x-auto">
          {filteredTrades.length > 0 ? (
            <table className="w-full">
              <thead>
                <tr className="border-b border-theme-border">
                  <th className="text-left p-4 text-sm font-medium text-theme-muted">
                    Hisse
                  </th>
                  <th className="text-left p-4 text-sm font-medium text-theme-muted">
                    Adet
                  </th>
                  <th className="text-left p-4 text-sm font-medium text-theme-muted">
                    Alış
                  </th>
                  <th className="text-left p-4 text-sm font-medium text-theme-muted">
                    Satış
                  </th>
                  <th className="text-left p-4 text-sm font-medium text-theme-muted">
                    PnL
                  </th>
                  <th className="text-left p-4 text-sm font-medium text-theme-muted">
                    Durum
                  </th>
                  <th className="text-left p-4 text-sm font-medium text-theme-muted">
                    Tarih
                  </th>
                  <th className="text-right p-4 text-sm font-medium text-theme-muted">
                    İşlem
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredTrades.map((trade) => (
                  <tr
                    key={trade.id}
                    className="border-b border-theme-border hover:bg-[var(--color-bg-secondary)] transition-colors"
                  >
                    <td className="p-4">
                      <span className="font-semibold text-theme-text">
                        {trade.ticker?.replace(".IS", "")}
                      </span>
                    </td>
                    <td className="p-4 text-theme-text">{trade.quantity}</td>
                    <td className="p-4 text-theme-text">
                      {formatCurrency(trade.buyPrice)}
                    </td>
                    <td className="p-4 text-theme-text">
                      {trade.sellPrice ? formatCurrency(trade.sellPrice) : "-"}
                    </td>
                    <td className="p-4">
                      {trade.status === "closed" ? (
                        <span
                          className={`font-semibold ${
                            (trade.pnl || 0) >= 0
                              ? "text-green-500"
                              : "text-red-500"
                          }`}
                        >
                          {(trade.pnl || 0) >= 0 ? "+" : ""}
                          {formatCurrency(trade.pnl || 0)}
                        </span>
                      ) : (
                        <span className="text-theme-muted">-</span>
                      )}
                    </td>
                    <td className="p-4">
                      <span
                        className={`badge ${
                          trade.status === "closed"
                            ? "badge-success"
                            : "badge-warning"
                        }`}
                      >
                        {trade.status === "closed" ? "Kapalı" : "Açık"}
                      </span>
                    </td>
                    <td className="p-4 text-sm text-theme-muted">
                      {new Date(trade.createdAt).toLocaleDateString("tr-TR")}
                    </td>
                    <td className="p-4">
                      <div className="flex items-center justify-end gap-2">
                        {trade.status === "open" && (
                          <button
                            onClick={() => handleCloseTrade(trade)}
                            className="p-2 hover:bg-green-500/20 rounded-lg transition-colors text-green-500"
                            title="Kapat (Sat)"
                          >
                            <Check className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => handleEdit(trade)}
                          className="p-2 hover:bg-primary/20 rounded-lg transition-colors text-primary"
                          title="Düzenle"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            if (
                              confirm(
                                "Bu işlemi silmek istediğinize emin misiniz?"
                              )
                            ) {
                              removeTrade(trade.id);
                            }
                          }}
                          className="p-2 hover:bg-red-500/20 rounded-lg transition-colors text-red-500"
                          title="Sil"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-12 text-center">
              <BarChart3 className="w-12 h-12 text-theme-muted mx-auto mb-4 opacity-50" />
              <p className="text-theme-text font-medium mb-2">
                Henüz işlem kaydı yok
              </p>
              <p className="text-sm text-theme-muted mb-4">
                İşlem ekleyerek performansınızı takip etmeye başlayın
              </p>
              <button
                onClick={() => setShowAddForm(true)}
                className="btn btn-primary"
              >
                <Plus className="w-4 h-4" />
                İlk İşlemi Ekle
              </button>
            </div>
          )}
        </div>

        {/* Clear All */}
        {trades.length > 0 && (
          <div className="p-4 border-t border-theme-border flex justify-between items-center">
            <span className="text-sm text-theme-muted">
              Toplam {trades.length} işlem
            </span>
            <button
              onClick={() => {
                if (
                  confirm(
                    "Tüm işlem geçmişini silmek istediğinize emin misiniz? Bu işlem geri alınamaz."
                  )
                ) {
                  clearAllTrades();
                }
              }}
              className="text-sm text-red-500 hover:text-red-400 flex items-center gap-1"
            >
              <Trash2 className="w-4 h-4" />
              Tümünü Sil
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default PerformancePage;
