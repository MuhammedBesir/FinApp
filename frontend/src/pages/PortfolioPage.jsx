/**
 * Portfolio Page - Enhanced Version
 * Gelişmiş portföy yönetimi ve takibi
 */
import React, { useState, useEffect, useMemo } from "react";
import {
  Plus,
  TrendingUp,
  TrendingDown,
  Trash2,
  RefreshCw,
  Edit2,
  Briefcase,
  DollarSign,
  Percent,
  Check,
  X,
  Eye,
  EyeOff,
  ArrowUpRight,
  ArrowDownRight,
  LayoutList,
  LayoutGrid,
  XCircle,
  Shield,
} from "lucide-react";
import { usePortfolioStore } from "../store/portfolioStore";
import { formatCurrency, formatPercent } from "../utils/formatters";
import PositionCard from "../components/Portfolio/PositionCard";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
  AreaChart,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
} from "recharts";
import { BIST30_STOCKS } from "../config/stocks";
import MobilePortfolioPage from "./mobile/MobilePortfolioPage";

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
  "#0ea5e9",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
  "#06b6d4",
  "#84cc16",
];

const PortfolioPage = () => {
  const isMobile = useIsMobile();
  const storeData = usePortfolioStore();

  // Early return for mobile view
  if (isMobile) {
    return <MobilePortfolioPage />;
  }
  
  // Store verilerini güvenli şekilde çek
  const {
    holdings = [],
    addHolding,
    removeHolding,
    updateHolding,
    getTotalValue,
    getTotalCost,
    getTotalProfitLoss,
    getTotalProfitLossPercent,
    trades = [],
    getRealizedPnL,
    addTrade,
    reorderHoldings,
    clearHoldings,
    bulkUpdateStopLoss,
    enableTrailingStop,
    updateTrailingStop,
    equityHistory = [],
    takeEquitySnapshot,
    getDrawdownData,
    getMaxDrawdown,
  } = storeData || {};
  
  // Eğer store yüklenmediyse veya bozuksa
  useEffect(() => {
    if (!storeData) {
      console.error("Portfolio store yüklenemedi!");
      // localStorage'ı temizle ve sayfayı yenile
      if (typeof window !== 'undefined' && window.localStorage) {
        localStorage.removeItem('portfolio-storage');
        window.location.reload();
      }
    }
    
    // Bozuk holdings'leri temizle
    if (holdings && holdings.length > 0) {
      const invalidHoldings = holdings.filter(h => !h || !h.ticker);
      if (invalidHoldings.length > 0) {
        console.warn(`${invalidHoldings.length} bozuk pozisyon bulundu, temizleniyor...`);
        invalidHoldings.forEach(h => {
          if (h && h.id) removeHolding?.(h.id);
        });
      }
    }
  }, [storeData, holdings]);

  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [newHolding, setNewHolding] = useState({
    ticker: "",
    quantity: "",
    buyPrice: "",
    currentPrice: "",
    buyDate: new Date().toISOString().split("T")[0],
    stopLoss: "",
    takeProfit: "",
  });
  const [loadingPrice, setLoadingPrice] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [showValues, setShowValues] = useState(true);
  const [sortBy, setSortBy] = useState("value");
  const [sortOrder, setSortOrder] = useState("desc");
  const [viewMode, setViewMode] = useState("table");
  const [pnlRange, setPnlRange] = useState("daily");
  const [draggingId, setDraggingId] = useState(null);

  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState("");
  const [toastType, setToastType] = useState("success");
  const [trailingStopModal, setTrailingStopModal] = useState(null);
  const [chartView, setChartView] = useState("equity"); // equity, drawdown

  // Toast notification helper
  const showNotification = (message, type = "success") => {
    setToastMessage(message);
    setToastType(type);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  // Fetch current price when ticker changes
  useEffect(() => {
    const fetchCurrentPrice = async () => {
      if (!newHolding.ticker) {
        setNewHolding((prev) => ({ ...prev, currentPrice: "" }));
        return;
      }

      setLoadingPrice(true);
      try {
        const response = await fetch(
          `/api/stocks/${newHolding.ticker}/current-price`
        );
        if (response.ok) {
          const data = await response.json();
          setNewHolding((prev) => ({
            ...prev,
            currentPrice: data.price.toFixed(2),
          }));
        }
      } catch (error) {
        console.error("Error fetching current price:", error);
      } finally {
        setLoadingPrice(false);
      }
    };

    fetchCurrentPrice();
  }, [newHolding.ticker]);

  // Auto-refresh prices
  useEffect(() => {
    const refreshPrices = async () => {
      if (holdings.length === 0) return;

      setRefreshing(true);
      try {
        for (const holding of holdings) {
          const response = await fetch(
            `/api/stocks/${holding.ticker}/current-price`
          );
          if (response.ok) {
            const data = await response.json();
            updateHolding(holding.id, { currentPrice: data.price });
            
            // Update trailing stop if enabled
            if (holding.trailingStop) {
              updateTrailingStop(holding.id, data.price);
            }
          }
        }
        setLastUpdate(new Date());
        takeEquitySnapshot(); // Snapshot al
      } catch (error) {
        console.error("Error refreshing prices:", error);
      } finally {
        setRefreshing(false);
      }
    };

    refreshPrices();
    const interval = setInterval(refreshPrices, 30000);
    return () => clearInterval(interval);
  }, [holdings.length]);

  // Manual refresh
  const handleManualRefresh = async () => {
    if (holdings.length === 0) return;

    setRefreshing(true);
    try {
      for (const holding of holdings) {
        const response = await fetch(
          `/api/stocks/${holding.ticker}/current-price`
        );
        if (response.ok) {
          const data = await response.json();
          updateHolding(holding.id, { currentPrice: data.price });
        }
      }
      setLastUpdate(new Date());
    } catch (error) {
      console.error("Error refreshing prices:", error);
    } finally {
      setRefreshing(false);
    }
  };

  // Handle form submit
  const handleSubmit = (e) => {
    e.preventDefault();

    const holdingData = {
      ticker: newHolding.ticker,
      quantity: parseFloat(newHolding.quantity),
      buyPrice: parseFloat(newHolding.buyPrice),
      currentPrice: parseFloat(newHolding.currentPrice),
      buyDate: newHolding.buyDate,
      stopLoss: newHolding.stopLoss
        ? parseFloat(newHolding.stopLoss)
        : undefined,
      takeProfit: newHolding.takeProfit
        ? parseFloat(newHolding.takeProfit)
        : undefined,
    };

    if (editingId) {
      updateHolding(editingId, holdingData);
      setEditingId(null);
    } else {
      addHolding(holdingData);
      addTrade({
        ticker: newHolding.ticker,
        type: "BUY",
        quantity: parseFloat(newHolding.quantity),
        buyPrice: parseFloat(newHolding.buyPrice),
        status: "open",
        date: newHolding.buyDate,
      });
    }

    setNewHolding({
      ticker: "",
      quantity: "",
      buyPrice: "",
      currentPrice: "",
      buyDate: new Date().toISOString().split("T")[0],
      stopLoss: "",
      takeProfit: "",
    });
    setShowAddForm(false);
  };

  // Handle edit
  const handleEdit = (holding) => {
    setEditingId(holding.id);
    setNewHolding({
      ticker: holding.ticker,
      quantity: holding.quantity.toString(),
      buyPrice: holding.buyPrice.toString(),
      currentPrice: holding.currentPrice.toString(),
      buyDate: holding.buyDate || new Date().toISOString().split("T")[0],
      stopLoss: holding.stopLoss?.toString() || "",
      takeProfit: holding.takeProfit?.toString() || "",
    });
    setShowAddForm(true);
  };

  // Handle sell
  const handleSell = async (holding) => {
    const sellQuantity = prompt(
      "Satmak istediğiniz miktar:",
      holding.quantity.toString()
    );
    if (!sellQuantity || parseFloat(sellQuantity) <= 0) return;

    const qty = Math.min(parseFloat(sellQuantity), holding.quantity);

    try {
      const response = await fetch(
        `/api/stocks/${holding.ticker}/current-price`
      );
      if (response.ok) {
        const data = await response.json();
        const sellPrice = data.price;
        const pnl = (sellPrice - holding.buyPrice) * qty;

        addTrade({
          ticker: holding.ticker,
          type: "SELL",
          quantity: qty,
          buyPrice: holding.buyPrice,
          sellPrice: sellPrice,
          pnl: pnl,
          status: "closed",
          closedAt: new Date().toISOString(),
        });

        if (qty >= holding.quantity) {
          removeHolding(holding.id);
        } else {
          updateHolding(holding.id, {
            quantity: holding.quantity - qty,
          });
        }

        alert(
          `${qty} adet ${holding.ticker?.replace(
            ".IS",
            ""
          ) || "Unknown"} satıldı!\nPnL: ${formatCurrency(pnl)}`
        );
      }
    } catch (error) {
      console.error("Error selling:", error);
      alert("Satış işlemi sırasında hata oluştu");
    }
  };

  const handleBulkClose = () => {
    if (holdings.length === 0) return;
    if (!confirm("Tüm pozisyonları kapatmak istediğinize emin misiniz?"))
      return;

    const now = new Date().toISOString();
    holdings.forEach((holding) => {
      const pnl =
        (holding.currentPrice - holding.buyPrice) * holding.quantity || 0;

      addTrade({
        ticker: holding.ticker,
        type: "SELL",
        quantity: holding.quantity,
        buyPrice: holding.buyPrice,
        sellPrice: holding.currentPrice,
        pnl,
        status: "closed",
        closedAt: now,
      });
    });

    clearHoldings();
    showNotification(`${holdings.length} pozisyon kapatıldı`, "success");
  };

  const handleBulkStopLoss = () => {
    if (holdings.length === 0) return;
    const input = prompt("Stop-loss yüzdesi (%)", "5");
    const percent = parseFloat(input);
    if (!percent || percent <= 0) return;
    bulkUpdateStopLoss(percent);
    showNotification(
      `Tüm stop-loss seviyeleri %${percent} altında güncellendi`,
      "success"
    );
  };

  const handleTrailingStopEnable = (holding) => {
    const percent = prompt("Trailing stop yüzdesi (%)", "5");
    const trailPercent = parseFloat(percent);
    if (!trailPercent || trailPercent <= 0) return;
    enableTrailingStop(holding.id, trailPercent);
    showNotification(
      `${holding.ticker?.replace(
        ".IS",
        ""
      ) || "Unknown"} için trailing stop (%${trailPercent}) aktif`,
      "success"
    );
  };

  const handleDragStart = (id) => setDraggingId(id);
  const handleDragOver = (e) => e.preventDefault();
  const handleDrop = (targetId) => {
    if (!draggingId || draggingId === targetId) return;
    const fromIndex = holdings.findIndex((h) => h.id === draggingId);
    const toIndex = holdings.findIndex((h) => h.id === targetId);
    if (fromIndex === -1 || toIndex === -1) return;
    reorderHoldings(fromIndex, toIndex);
    setDraggingId(null);
  };

  // Calculations
  const totalValue = getTotalValue?.() || 0;
  const totalCost = getTotalCost?.() || 0;
  const profitLoss = getTotalProfitLoss?.() || 0;
  const profitLossPercent = getTotalProfitLossPercent?.() || 0;
  const realizedPnL = getRealizedPnL?.() || 0;

  const closedTrades = useMemo(
    () => trades.filter((t) => t.status === "closed"),
    [trades]
  );

  const dailyPnL = useMemo(() => {
    const days = 30;
    const today = new Date();
    const series = [];

    for (let i = days - 1; i >= 0; i--) {
      const date = new Date();
      date.setDate(today.getDate() - i);
      const isoDay = date.toISOString().split("T")[0];
      const label = date.toLocaleDateString("tr-TR", {
        day: "2-digit",
        month: "short",
      });

      const pnlForDay = closedTrades.reduce((sum, trade) => {
        const closedAt = trade.closedAt || trade.date;
        if (!closedAt) return sum;
        return closedAt.startsWith(isoDay) ? sum + (trade.pnl || 0) : sum;
      }, 0);

      series.push({ label, pnl: pnlForDay });
    }

    return series;
  }, [closedTrades]);

  const monthlyPnL = useMemo(() => {
    const series = [];
    const base = new Date();

    for (let i = 11; i >= 0; i--) {
      const date = new Date(base.getFullYear(), base.getMonth() - i, 1);
      const month = date.getMonth();
      const year = date.getFullYear();
      const label = date.toLocaleDateString("tr-TR", {
        month: "short",
        year: "2-digit",
      });

      const pnlForMonth = closedTrades.reduce((sum, trade) => {
        const closedDate = trade.closedAt
          ? new Date(trade.closedAt)
          : trade.date
          ? new Date(trade.date)
          : null;
        if (!closedDate) return sum;
        if (
          closedDate.getFullYear() === year &&
          closedDate.getMonth() === month
        ) {
          return sum + (trade.pnl || 0);
        }
        return sum;
      }, 0);

      series.push({ label, pnl: pnlForMonth });
    }

    return series;
  }, [closedTrades]);

  const pnlSeries = pnlRange === "daily" ? dailyPnL : monthlyPnL;

  // Equity curve data
  const equityCurve = useMemo(() => {
    if (!equityHistory || equityHistory.length === 0) return [];
    return equityHistory.map((point) => ({
      label: new Date(point.timestamp).toLocaleDateString("tr-TR", {
        day: "2-digit",
        month: "short",
      }),
      value: point.value,
    }));
  }, [equityHistory]);

  // Drawdown data
  const drawdownData = useMemo(() => {
    if (!getDrawdownData) return [];
    const data = getDrawdownData();
    return data.map((point) => ({
      label: new Date(point.timestamp).toLocaleDateString("tr-TR", {
        day: "2-digit",
        month: "short",
      }),
      drawdown: point.drawdown,
    }));
  }, [equityHistory, getDrawdownData]);

  const maxDrawdown = getMaxDrawdown?.() || 0;

  // Sort holdings
  const sortedHoldings = useMemo(() => {
    if (!holdings || holdings.length === 0) return [];
    return [...holdings].sort((a, b) => {
      let aVal, bVal;

      switch (sortBy) {
        case "value":
          aVal = a.quantity * a.currentPrice;
          bVal = b.quantity * b.currentPrice;
          break;
        case "pnl":
          aVal = (a.currentPrice - a.buyPrice) * a.quantity;
          bVal = (b.currentPrice - b.buyPrice) * b.quantity;
          break;
        default:
          aVal = a.quantity * a.currentPrice;
          bVal = b.quantity * b.currentPrice;
      }

      return sortOrder === "desc" ? bVal - aVal : aVal - bVal;
    });
  }, [holdings, sortBy, sortOrder]);

  // Pie chart data - filter valid holdings
  const validHoldings = (holdings || []).filter(h => h && h.ticker && h.quantity && h.currentPrice);
  
  const pieData = validHoldings.map((h) => ({
    name: h.ticker.replace(".IS", ""),
    value: h.quantity * h.currentPrice,
  }));

  // Best and worst performers
  const holdingsWithPnL = validHoldings.map((h) => ({
    ...h,
    pnl: (h.currentPrice - h.buyPrice) * h.quantity,
    pnlPercent: ((h.currentPrice - h.buyPrice) / h.buyPrice) * 100,
  }));

  const bestPerformer =
    holdingsWithPnL.length > 0
      ? holdingsWithPnL.reduce((best, current) =>
          current.pnlPercent > best.pnlPercent ? current : best
        )
      : null;

  const worstPerformer =
    holdingsWithPnL.length > 0
      ? holdingsWithPnL.reduce((worst, current) =>
          current.pnlPercent < worst.pnlPercent ? current : worst
        )
      : null;

  return (
    <div className="space-y-3 sm:space-y-4 md:space-y-6 animate-fade-in">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 sm:gap-3 md:gap-4">
        <div className="stat-card col-span-1 p-2 sm:p-3">
          <div className="stat-icon primary w-7 h-7 sm:w-8 sm:h-8">
            <Briefcase className="w-3.5 h-3.5 sm:w-4 sm:h-4 md:w-5 md:h-5" />
          </div>
          <div>
            <p className="text-[9px] sm:text-[10px] md:text-xs text-theme-muted">Portföy Değeri</p>
            <p className="text-sm sm:text-base md:text-xl font-bold text-theme-text">
              {showValues ? formatCurrency(totalValue) : "••••••"}
            </p>
          </div>
        </div>

        <div className="stat-card col-span-1 p-2 sm:p-3">
          <div className="stat-icon warning w-7 h-7 sm:w-8 sm:h-8">
            <DollarSign className="w-3.5 h-3.5 sm:w-4 sm:h-4 md:w-5 md:h-5" />
          </div>
          <div>
            <p className="text-[9px] sm:text-[10px] md:text-xs text-theme-muted">Toplam Maliyet</p>
            <p className="text-sm sm:text-base md:text-xl font-bold text-theme-text">
              {showValues ? formatCurrency(totalCost) : "••••••"}
            </p>
          </div>
        </div>

        <div
          className={`stat-card col-span-1 p-2 sm:p-3 ${
            profitLoss >= 0 ? "border-green-500/30" : "border-red-500/30"
          }`}
        >
          <div
            className={`stat-icon w-7 h-7 sm:w-8 sm:h-8 ${profitLoss >= 0 ? "success" : "danger"}`}
          >
            {profitLoss >= 0 ? (
              <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5" />
            ) : (
              <TrendingDown className="w-4 h-4 sm:w-5 sm:h-5" />
            )}
          </div>
          <div>
            <p className="text-[9px] sm:text-[10px] md:text-xs text-theme-muted">Açık PnL</p>
            <p
              className={`text-sm sm:text-base md:text-xl font-bold ${
                profitLoss >= 0 ? "text-green-500" : "text-red-500"
              }`}
            >
              {showValues
                ? `${profitLoss >= 0 ? "+" : ""}${formatCurrency(profitLoss)}`
                : "••••••"}
            </p>
          </div>
        </div>

        <div
          className={`stat-card col-span-1 p-2 sm:p-3 ${
            profitLossPercent >= 0 ? "border-green-500/30" : "border-red-500/30"
          }`}
        >
          <div
            className={`stat-icon w-7 h-7 sm:w-8 sm:h-8 ${
              profitLossPercent >= 0 ? "success" : "danger"
            }`}
          >
            <Percent className="w-4 h-4 sm:w-5 sm:h-5" />
          </div>
          <div>
            <p className="text-[9px] sm:text-[10px] md:text-xs text-theme-muted">Getiri</p>
            <p
              className={`text-sm sm:text-base md:text-xl font-bold ${
                profitLossPercent >= 0 ? "text-green-500" : "text-red-500"
              }`}
            >
              {profitLossPercent >= 0 ? "+" : ""}
              {formatPercent(profitLossPercent)}
            </p>
          </div>
        </div>

        <div
          className={`stat-card col-span-1 p-2 sm:p-3 ${
            realizedPnL >= 0 ? "border-green-500/30" : "border-red-500/30"
          }`}
        >
          <div
            className={`stat-icon w-7 h-7 sm:w-8 sm:h-8 ${realizedPnL >= 0 ? "success" : "danger"}`}
          >
            <Check className="w-4 h-4 sm:w-5 sm:h-5" />
          </div>
          <div>
            <p className="text-[9px] sm:text-[10px] md:text-xs text-theme-muted">Gerçekleşmiş</p>
            <p
              className={`text-sm sm:text-base md:text-xl font-bold ${
                realizedPnL >= 0 ? "text-green-500" : "text-red-500"
              }`}
            >
              {showValues
                ? `${realizedPnL >= 0 ? "+" : ""}${formatCurrency(realizedPnL)}`
                : "••••••"}
            </p>
          </div>
        </div>

        <div className="stat-card col-span-1 p-2 sm:p-3 border-orange-500/30">
          <div className="stat-icon w-7 h-7 sm:w-8 sm:h-8" style={{ backgroundColor: "#f97316" + "20" }}>
            <ArrowDownRight className="w-4 h-4 sm:w-5 sm:h-5" style={{ color: "#f97316" }} />
          </div>
          <div>
            <p className="text-[9px] sm:text-[10px] md:text-xs text-theme-muted">Max Drawdown</p>
            <p className="text-sm sm:text-base md:text-xl font-bold" style={{ color: "#f97316" }}>
              {formatPercent(maxDrawdown)}
            </p>
          </div>
        </div>
      </div>

      {/* Toast Notification */}
      {showToast && (
        <div
          className={`fixed top-4 right-4 z-50 px-6 py-4 rounded-xl shadow-2xl border animate-fade-in ${
            toastType === "success"
              ? "bg-green-500/20 border-green-500/50 text-green-500"
              : "bg-red-500/20 border-red-500/50 text-red-500"
          }`}
        >
          <div className="flex items-center gap-3">
            {toastType === "success" ? (
              <Check className="w-5 h-5" />
            ) : (
              <X className="w-5 h-5" />
            )}
            <p className="font-medium">{toastMessage}</p>
          </div>
        </div>
      )}

      {/* Best/Worst Performers */}
      {holdings.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {bestPerformer && (
            <div className="card p-4 border-green-500/30">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-green-500/20 flex items-center justify-center">
                    <ArrowUpRight className="w-5 h-5 text-green-500" />
                  </div>
                  <div>
                    <p className="text-xs text-theme-muted">
                      En İyi Performans
                    </p>
                    <p className="font-semibold text-theme-text">
                      {bestPerformer.ticker?.replace(".IS", "") || "Unknown"}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-green-500 font-bold">
                    +{formatPercent(bestPerformer.pnlPercent)}
                  </p>
                  <p className="text-xs text-green-500/70">
                    +{formatCurrency(bestPerformer.pnl)}
                  </p>
                </div>
              </div>
            </div>
          )}

          {worstPerformer && (
            <div className="card p-4 border-red-500/30">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-red-500/20 flex items-center justify-center">
                    <ArrowDownRight className="w-5 h-5 text-red-500" />
                  </div>
                  <div>
                    <p className="text-xs text-theme-muted">
                      En Kötü Performans
                    </p>
                    <p className="font-semibold text-theme-text">
                      {worstPerformer.ticker?.replace(".IS", "") || "Unknown"}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-red-500 font-bold">
                    {formatPercent(worstPerformer.pnlPercent)}
                  </p>
                  <p className="text-xs text-red-500/70">
                    {formatCurrency(worstPerformer.pnl)}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Holdings List */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 border-b border-theme-border">
              <div className="flex items-center gap-3">
                <h2 className="text-lg font-semibold">Hisselerim</h2>
                <span className="badge badge-primary">
                  {holdings.length} hisse
                </span>
                {lastUpdate && (
                  <span className="text-xs text-theme-muted">
                    {lastUpdate.toLocaleTimeString("tr-TR")}
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowValues(!showValues)}
                  className="p-2 hover:bg-[var(--color-bg-secondary)] rounded-lg transition-colors"
                  title={showValues ? "Değerleri Gizle" : "Değerleri Göster"}
                >
                  {showValues ? (
                    <EyeOff className="w-4 h-4 text-theme-muted" />
                  ) : (
                    <Eye className="w-4 h-4 text-theme-muted" />
                  )}
                </button>

                <button
                  onClick={handleManualRefresh}
                  disabled={refreshing || holdings.length === 0}
                  className="btn btn-secondary"
                >
                  <RefreshCw
                    className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`}
                  />
                </button>

                <button
                  onClick={() => {
                    setEditingId(null);
                    setNewHolding({
                      ticker: "",
                      quantity: "",
                      buyPrice: "",
                      currentPrice: "",
                      buyDate: new Date().toISOString().split("T")[0],
                      stopLoss: "",
                      takeProfit: "",
                    });
                    setShowAddForm(!showAddForm);
                  }}
                  className="btn btn-primary"
                >
                  <Plus className="w-4 h-4" />
                  Hisse Ekle
                </button>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 px-5 pb-4">
              <div className="flex items-center gap-2">
                <div className="flex rounded-lg bg-[var(--color-bg-secondary)] p-1">
                  <button
                    onClick={() => setViewMode("table")}
                    className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-sm transition-colors ${
                      viewMode === "table"
                        ? "bg-primary text-white"
                        : "text-theme-muted"
                    }`}
                  >
                    <LayoutList className="w-4 h-4" />
                    Tablo
                  </button>
                  <button
                    onClick={() => setViewMode("cards")}
                    className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-sm transition-colors ${
                      viewMode === "cards"
                        ? "bg-primary text-white"
                        : "text-theme-muted"
                    }`}
                  >
                    <LayoutGrid className="w-4 h-4" />
                    Kart
                  </button>
                </div>

                {viewMode === "cards" && (
                  <span className="text-xs text-theme-muted">
                    Kartları sürükleyip bırakın, sıralama kaydedilsin.
                  </span>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={handleBulkStopLoss}
                  className="btn btn-secondary"
                  disabled={holdings.length === 0}
                >
                  <Shield className="w-4 h-4" />
                  Toplu SL
                </button>
                <button
                  onClick={handleBulkClose}
                  className="btn bg-red-500/15 text-red-500 hover:bg-red-500/25"
                  disabled={holdings.length === 0}
                >
                  <XCircle className="w-4 h-4" />
                  Hepsini Kapat
                </button>
              </div>
            </div>

            {/* Add/Edit Form */}
            {showAddForm && (
              <div className="p-5 border-b border-theme-border bg-[var(--color-bg-secondary)] animate-fade-in">
                <form onSubmit={handleSubmit} className="space-y-5">
                  {/* Hisse Bilgileri */}
                  <div>
                    <h4 className="text-sm font-semibold text-theme-text mb-3 flex items-center gap-2">
                      <Briefcase className="w-4 h-4" />
                      Hisse Bilgileri
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      <div className="col-span-2 md:col-span-1">
                        <label className="block text-sm text-theme-muted mb-1">
                          Hisse
                        </label>
                        <select
                          value={newHolding.ticker}
                          onChange={(e) =>
                            setNewHolding({
                              ...newHolding,
                              ticker: e.target.value,
                            })
                          }
                          className="input"
                          required
                        >
                          <option value="">Seçin...</option>
                          {BIST30_STOCKS.map((stock) => (
                            <option key={stock.symbol} value={stock.symbol}>
                              {stock.symbol.replace(".IS", "")} - {stock.name}
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
                          value={newHolding.quantity}
                          onChange={(e) =>
                            setNewHolding({
                              ...newHolding,
                              quantity: e.target.value,
                            })
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
                          value={newHolding.buyPrice}
                          onChange={(e) =>
                            setNewHolding({
                              ...newHolding,
                              buyPrice: e.target.value,
                            })
                          }
                          className="input"
                          placeholder="0.00"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-sm text-theme-muted mb-1">
                          Güncel Fiyat{" "}
                          {loadingPrice && (
                            <span className="text-primary text-xs">
                              (Yükleniyor...)
                            </span>
                          )}
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          value={newHolding.currentPrice}
                          onChange={(e) =>
                            setNewHolding({
                              ...newHolding,
                              currentPrice: e.target.value,
                            })
                          }
                          className="input"
                          placeholder="Otomatik"
                          required
                          disabled={loadingPrice}
                        />
                      </div>

                      <div>
                        <label className="block text-sm text-theme-muted mb-1">
                          Alış Tarihi
                        </label>
                        <input
                          type="date"
                          value={newHolding.buyDate}
                          onChange={(e) =>
                            setNewHolding({
                              ...newHolding,
                              buyDate: e.target.value,
                            })
                          }
                          className="input"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Risk Yönetimi */}
                  <div>
                    <h4 className="text-sm font-semibold text-theme-text mb-3 flex items-center gap-2">
                      <Shield className="w-4 h-4" />
                      Risk Yönetimi
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm text-theme-muted mb-1">
                          Stop-Loss (opsiyonel)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          value={newHolding.stopLoss}
                          onChange={(e) =>
                            setNewHolding({
                              ...newHolding,
                              stopLoss: e.target.value,
                            })
                          }
                          className="input"
                          placeholder="SL fiyatı"
                        />
                      </div>

                      <div>
                        <label className="block text-sm text-theme-muted mb-1">
                          Take-Profit (opsiyonel)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          value={newHolding.takeProfit}
                          onChange={(e) =>
                            setNewHolding({
                              ...newHolding,
                              takeProfit: e.target.value,
                            })
                          }
                          className="input"
                          placeholder="TP fiyatı"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-3 pt-2 border-t border-theme-border">
                    <button type="submit" className="btn btn-primary flex-1">
                      <Check className="w-4 h-4" />
                      {editingId ? "Pozisyonu Güncelle" : "Pozisyon Ekle"}
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

            {/* Holdings Table */}
            <div className={viewMode === "table" ? "overflow-x-auto" : "p-5"}>
              {viewMode === "table" ? (
                sortedHoldings.length > 0 ? (
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-theme-border">
                        <th className="text-left p-4 text-sm font-medium text-theme-muted">
                          Hisse
                        </th>
                        <th className="text-right p-4 text-sm font-medium text-theme-muted">
                          Adet
                        </th>
                        <th className="text-right p-4 text-sm font-medium text-theme-muted">
                          Alış
                        </th>
                        <th className="text-right p-4 text-sm font-medium text-theme-muted">
                          Güncel
                        </th>
                        <th
                          className="text-right p-4 text-sm font-medium text-theme-muted cursor-pointer hover:text-primary"
                          onClick={() => {
                            if (sortBy === "value") {
                              setSortOrder(sortOrder === "desc" ? "asc" : "desc");
                            } else {
                              setSortBy("value");
                              setSortOrder("desc");
                            }
                          }}
                        >
                          Değer {sortBy === "value" && (sortOrder === "desc" ? "↓" : "↑")}
                        </th>
                        <th
                          className="text-right p-4 text-sm font-medium text-theme-muted cursor-pointer hover:text-primary"
                          onClick={() => {
                            if (sortBy === "pnl") {
                              setSortOrder(sortOrder === "desc" ? "asc" : "desc");
                            } else {
                              setSortBy("pnl");
                              setSortOrder("desc");
                            }
                          }}
                        >
                          PnL {sortBy === "pnl" && (sortOrder === "desc" ? "↓" : "↑")}
                        </th>
                        <th className="text-right p-4 text-sm font-medium text-theme-muted">
                          İşlem
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedHoldings.map((holding) => {
                        const value = holding.quantity * holding.currentPrice;
                        const pnl =
                          (holding.currentPrice - holding.buyPrice) *
                          holding.quantity;
                        const pnlPercent =
                          ((holding.currentPrice - holding.buyPrice) /
                            holding.buyPrice) *
                          100;

                        return (
                          <tr
                            key={holding.id}
                            className="border-b border-theme-border hover:bg-[var(--color-bg-secondary)] transition-colors"
                          >
                            <td className="p-4">
                              <span className="font-semibold text-theme-text">
                                {holding.ticker?.replace(".IS", "")}
                              </span>
                            </td>
                            <td className="p-4 text-right text-theme-text">
                              {holding.quantity}
                            </td>
                            <td className="p-4 text-right text-theme-text">
                              {showValues
                                ? formatCurrency(holding.buyPrice)
                                : "••••"}
                            </td>
                            <td className="p-4 text-right text-theme-text">
                              {showValues
                                ? formatCurrency(holding.currentPrice)
                                : "••••"}
                            </td>
                            <td className="p-4 text-right text-theme-text font-medium">
                              {showValues ? formatCurrency(value) : "••••"}
                            </td>
                            <td className="p-4 text-right">
                              <div
                                className={`font-semibold ${
                                  pnl >= 0 ? "text-green-500" : "text-red-500"
                                }`}
                              >
                                {showValues ? (
                                  <>
                                    {pnl >= 0 ? "+" : ""}
                                    {formatCurrency(pnl)}
                                    <span className="text-xs ml-1">
                                      ({pnl >= 0 ? "+" : ""}
                                      {formatPercent(pnlPercent)})
                                    </span>
                                  </>
                                ) : (
                                  "••••"
                                )}
                              </div>
                            </td>
                            <td className="p-4">
                              <div className="flex items-center justify-end gap-1">
                                {!holding.trailingStop && (
                                  <button
                                    onClick={() => handleTrailingStopEnable(holding)}
                                    className="p-2 hover:bg-blue-500/20 rounded-lg transition-colors text-blue-500"
                                    title="Trailing Stop Aktif Et"
                                  >
                                    <TrendingUp className="w-4 h-4" />
                                  </button>
                                )}
                                {holding.trailingStop && (
                                  <div className="px-2 py-1 rounded bg-blue-500/20 text-blue-500 text-xs font-medium">
                                    TS {holding.trailPercent}%
                                  </div>
                                )}
                                <button
                                  onClick={() => handleSell(holding)}
                                  className="p-2 hover:bg-green-500/20 rounded-lg transition-colors text-green-500"
                                  title="Sat"
                                >
                                  <DollarSign className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => handleEdit(holding)}
                                  className="p-2 hover:bg-primary/20 rounded-lg transition-colors text-primary"
                                  title="Düzenle"
                                >
                                  <Edit2 className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => {
                                    if (
                                      confirm(
                                        "Bu hisseyi portföyden kaldırmak istiyor musunuz?"
                                      )
                                    ) {
                                      removeHolding(holding.id);
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
                        );
                      })}
                    </tbody>
                  </table>
                ) : (
                  <div className="p-16 text-center animate-fade-in">
                    <div className="inline-block p-6 rounded-2xl bg-primary/10 mb-4">
                      <Briefcase className="w-16 h-16 text-primary" />
                    </div>
                    <p className="text-xl font-bold text-theme-text mb-2">
                      Portföyünüz henüz boş
                    </p>
                    <p className="text-sm text-theme-muted mb-6 max-w-md mx-auto">
                      İlk hissenizi ekleyerek yatırım portföyünüzü oluşturun ve
                      kazançlarınızı takip etmeye başlayın
                    </p>
                    <button
                      onClick={() => setShowAddForm(true)}
                      className="btn btn-primary"
                    >
                      <Plus className="w-4 h-4" />
                      İlk Hisseyi Ekle
                    </button>
                  </div>
                )
              ) : holdings.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {holdings.map((holding) => (
                    <div
                      key={holding.id}
                      draggable
                      onDragStart={() => handleDragStart(holding.id)}
                      onDragOver={handleDragOver}
                      onDrop={() => handleDrop(holding.id)}
                      className={`cursor-grab ${
                        draggingId === holding.id ? "opacity-70" : ""
                      }`}
                    >
                      <PositionCard
                        position={holding}
                        onUpdate={handleEdit}
                        onRemove={(id) => removeHolding(id)}
                      />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-16 text-center animate-fade-in">
                  <div className="inline-block p-6 rounded-2xl bg-primary/10 mb-4">
                    <LayoutGrid className="w-16 h-16 text-primary" />
                  </div>
                  <p className="text-xl font-bold text-theme-text mb-2">
                    Kart görünümünde hisse yok
                  </p>
                  <p className="text-sm text-theme-muted mb-6 max-w-md mx-auto">
                    Hisse ekleyerek detaylı kart görünümünde portföyünüzü takip edin
                  </p>
                  <button
                    onClick={() => setShowAddForm(true)}
                    className="btn btn-primary"
                  >
                    <Plus className="w-4 h-4" />
                    Hisse Ekle
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Equity Curve & Drawdown Chart */}
          <div className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Performans</h3>
              <div className="flex rounded-lg bg-[var(--color-bg-secondary)] p-1">
                <button
                  onClick={() => setChartView("equity")}
                  className={`px-3 py-1.5 rounded-md text-sm ${
                    chartView === "equity"
                      ? "bg-primary text-white"
                      : "text-theme-muted"
                  }`}
                >
                  Equity
                </button>
                <button
                  onClick={() => setChartView("drawdown")}
                  className={`px-3 py-1.5 rounded-md text-sm ${
                    chartView === "drawdown"
                      ? "bg-primary text-white"
                      : "text-theme-muted"
                  }`}
                >
                  Drawdown
                </button>
              </div>
            </div>

            {chartView === "equity" ? (
              equityCurve.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={equityCurve} margin={{ top: 10, right: 0, left: -10, bottom: 0 }}>
                    <defs>
                      <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.45} />
                        <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0.05} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="label" tick={{ fontSize: 10 }} tickMargin={8} />
                    <YAxis
                      tickFormatter={(v) => (showValues ? formatCurrency(v) : "••••")}
                      tick={{ fontSize: 10 }}
                    />
                    <Tooltip
                      formatter={(value) => [
                        showValues ? formatCurrency(value) : "••••",
                        "Değer",
                      ]}
                      contentStyle={{
                        backgroundColor: "var(--color-card)",
                        border: "1px solid var(--color-border)",
                        borderRadius: "8px",
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#0ea5e9"
                      fill="url(#equityGradient)"
                      strokeWidth={2}
                      isAnimationActive={false}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-48 text-theme-muted">
                  Henüz yeterli veri yok
                </div>
              )
            ) : (
              drawdownData.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={drawdownData} margin={{ top: 10, right: 0, left: -10, bottom: 0 }}>
                    <defs>
                      <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.45} />
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0.05} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="label" tick={{ fontSize: 10 }} tickMargin={8} />
                    <YAxis
                      tickFormatter={(v) => formatPercent(v)}
                      tick={{ fontSize: 10 }}
                    />
                    <Tooltip
                      formatter={(value) => [formatPercent(value), "Drawdown"]}
                      contentStyle={{
                        backgroundColor: "var(--color-card)",
                        border: "1px solid var(--color-border)",
                        borderRadius: "8px",
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="drawdown"
                      stroke="#ef4444"
                      fill="url(#drawdownGradient)"
                      strokeWidth={2}
                      isAnimationActive={false}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-48 text-theme-muted">
                  Henüz yeterli veri yok
                </div>
              )
            )}
          </div>

          {/* P&L Chart */}
          <div className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">P&L Grafiği</h3>
              <div className="flex rounded-lg bg-[var(--color-bg-secondary)] p-1">
                <button
                  onClick={() => setPnlRange("daily")}
                  className={`px-3 py-1.5 rounded-md text-sm ${
                    pnlRange === "daily"
                      ? "bg-primary text-white"
                      : "text-theme-muted"
                  }`}
                >
                  Günlük
                </button>
                <button
                  onClick={() => setPnlRange("monthly")}
                  className={`px-3 py-1.5 rounded-md text-sm ${
                    pnlRange === "monthly"
                      ? "bg-primary text-white"
                      : "text-theme-muted"
                  }`}
                >
                  Aylık
                </button>
              </div>
            </div>

            {pnlSeries && pnlSeries.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <AreaChart data={pnlSeries} margin={{ top: 10, right: 0, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.45} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis dataKey="label" tick={{ fontSize: 10 }} tickMargin={8} />
                  <YAxis
                    tickFormatter={(v) => (showValues ? formatCurrency(v) : "••••")}
                    tick={{ fontSize: 10 }}
                  />
                  <Tooltip
                    formatter={(value) => [
                      showValues ? formatCurrency(value) : "••••",
                      "PnL",
                    ]}
                    contentStyle={{
                      backgroundColor: "var(--color-card)",
                      border: "1px solid var(--color-border)",
                      borderRadius: "8px",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="pnl"
                    stroke="#10b981"
                    fill="url(#pnlGradient)"
                    strokeWidth={2}
                    isAnimationActive={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-48 text-theme-muted">
                Kapalı işlem bulunmuyor
              </div>
            )}
          </div>

          {/* Distribution Chart */}
          <div className="card p-5">
            <h3 className="text-lg font-semibold mb-4">Portföy Dağılımı</h3>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value) => [
                      showValues ? formatCurrency(value) : "••••",
                      "",
                    ]}
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
                Veri yok
              </div>
            )}
          </div>

          {/* Quick Stats */}
          <div className="card p-5">
            <h3 className="text-lg font-semibold mb-4">Hızlı Bakış</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 rounded-xl bg-[var(--color-bg-secondary)]">
                <span className="text-theme-muted">Toplam Hisse</span>
                <span className="font-semibold text-theme-text">
                  {holdings.length}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 rounded-xl bg-[var(--color-bg-secondary)]">
                <span className="text-theme-muted">Karlı Hisse</span>
                <span className="font-semibold text-green-500">
                  {holdingsWithPnL.filter((h) => h.pnl > 0).length}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 rounded-xl bg-[var(--color-bg-secondary)]">
                <span className="text-theme-muted">Zararlı Hisse</span>
                <span className="font-semibold text-red-500">
                  {holdingsWithPnL.filter((h) => h.pnl < 0).length}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 rounded-xl bg-[var(--color-bg-secondary)]">
                <span className="text-theme-muted">Kapatılan İşlem</span>
                <span className="font-semibold text-theme-text">
                  {trades.filter((t) => t.status === "closed").length}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioPage;
