/**
 * Stock Screener Page - Hisse Tarama
 * BIST 30 hisselerini momentum skoruna göre tarar
 */
import React, { useState, useEffect } from "react";
import {
  Search,
  Filter,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  BarChart2,
  ArrowUpRight,
  ArrowDownRight,
  Zap,
  Target,
  Clock,
  SlidersHorizontal,
  ChevronUp,
  ChevronDown,
} from "lucide-react";
import { useStore } from "../store";
import MobileScreenerPage from "./mobile/MobileScreenerPage";

const API_URL = import.meta.env.VITE_API_URL || "/api";

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

const ScreenerPage = () => {
  const isMobile = useIsMobile();
  
  // Early return for mobile view
  if (isMobile) {
    return <MobileScreenerPage />;
  }

  const { selectedTicker, setSelectedTicker } = useStore();
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState("score"); // score, ticker, change
  const [sortOrder, setSortOrder] = useState("desc");
  const [minScore, setMinScore] = useState(0);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchStocks = async () => {
    setRefreshing(true);
    try {
      const response = await fetch(
        `${API_URL}/screener/scan?interval=1d&period=3mo`
      );
      if (response.ok) {
        const data = await response.json();
        setStocks(data.stocks || []);
        setLastUpdate(new Date());
      }
    } catch (error) {
      console.error("Error fetching screener data:", error);
    }
    setLoading(false);
    setRefreshing(false);
  };

  useEffect(() => {
    fetchStocks();
    // Her 2 dakikada bir güncelle
    const interval = setInterval(fetchStocks, 2 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const getScoreColor = (score) => {
    if (score >= 70) return "text-green-500";
    if (score >= 50) return "text-yellow-500";
    if (score >= 30) return "text-orange-500";
    return "text-red-500";
  };

  const getScoreBg = (score) => {
    if (score >= 70) return "bg-green-500/10";
    if (score >= 50) return "bg-yellow-500/10";
    if (score >= 30) return "bg-orange-500/10";
    return "bg-red-500/10";
  };

  const getRecommendationBadge = (rec) => {
    const badges = {
      "GÜÇLÜ AL": { class: "bg-green-500 text-white", icon: TrendingUp },
      AL: {
        class: "bg-green-400/20 text-green-400 border border-green-400/30",
        icon: ArrowUpRight,
      },
      TUT: {
        class: "bg-yellow-400/20 text-yellow-400 border border-yellow-400/30",
        icon: Target,
      },
      SAT: {
        class: "bg-red-400/20 text-red-400 border border-red-400/30",
        icon: ArrowDownRight,
      },
      "GÜÇLÜ SAT": { class: "bg-red-500 text-white", icon: TrendingDown },
    };
    const badge = badges[rec] || badges["TUT"];
    const Icon = badge.icon;
    return (
      <span
        className={`px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${badge.class}`}
      >
        <Icon className="w-3 h-3" />
        {rec}
      </span>
    );
  };

  const filteredAndSortedStocks = stocks
    .filter((stock) => {
      const matchesSearch = stock.ticker
        ?.toLowerCase()
        .includes(searchTerm.toLowerCase());
      const matchesScore = (stock.momentum_score || 0) >= minScore;
      return matchesSearch && matchesScore;
    })
    .sort((a, b) => {
      let comparison = 0;
      if (sortBy === "score") {
        comparison = (a.momentum_score || 0) - (b.momentum_score || 0);
      } else if (sortBy === "ticker") {
        comparison = a.ticker?.localeCompare(b.ticker) || 0;
      } else if (sortBy === "change") {
        comparison = (a.change_percent || 0) - (b.change_percent || 0);
      }
      return sortOrder === "desc" ? -comparison : comparison;
    });

  const topPicks = filteredAndSortedStocks.filter(
    (s) => (s.momentum_score || 0) >= 60
  );

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === "desc" ? "asc" : "desc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
  };

  const SortIcon = ({ field }) => {
    if (sortBy !== field) return null;
    return sortOrder === "desc" ? (
      <ChevronDown className="w-4 h-4" />
    ) : (
      <ChevronUp className="w-4 h-4" />
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin text-primary mx-auto mb-4" />
          <p className="text-theme-muted">Hisseler taranıyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3 sm:space-y-4 md:space-y-6">
      {/* Top Picks Banner */}
      {topPicks.length > 0 && (
        <div className="card p-3 sm:p-4 border-l-4 border-l-green-500 bg-gradient-to-r from-green-500/5 to-transparent">
          <div className="flex items-center gap-2 sm:gap-3 mb-2 sm:mb-3">
            <Zap className="w-4 h-4 sm:w-5 sm:h-5 text-green-500" />
            <h3 className="text-xs sm:text-sm md:text-base font-semibold text-theme-text">
              Günün En İyi Fırsatları
            </h3>
            <span className="badge badge-success text-xs">{topPicks.length} hisse</span>
          </div>
          <div className="flex flex-wrap gap-1.5 sm:gap-2">
            {topPicks.slice(0, 8).map((stock) => (
              <button
                key={stock.ticker}
                onClick={() => setSelectedTicker(`${stock.ticker}.IS`)}
                className="px-3 py-2 rounded-lg bg-[var(--color-bg-secondary)] hover:bg-[var(--color-bg-tertiary)] transition-all flex items-center gap-2"
              >
                <span className="font-medium text-theme-text">
                  {stock.ticker?.replace(".IS", "")}
                </span>
                <span
                  className={`text-sm font-bold ${getScoreColor(
                    stock.momentum_score
                  )}`}
                >
                  {stock.momentum_score?.toFixed(0)}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card p-3 sm:p-4">
        <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 flex-1">
            <div className="relative flex-1 sm:max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-theme-muted" />
              <input
                type="text"
                placeholder="Hisse ara..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input-field pl-10 w-full text-sm"
              />
            </div>

            <div className="flex items-center gap-2">
              <SlidersHorizontal className="w-4 h-4 text-theme-muted" />
              <span className="text-sm text-theme-muted">Min Skor:</span>
              <input
                type="range"
                min="0"
                max="100"
                value={minScore}
                onChange={(e) => setMinScore(Number(e.target.value))}
                className="w-24 accent-primary"
              />
              <span className="text-sm font-medium text-theme-text w-8">
                {minScore}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {lastUpdate && (
              <div className="flex items-center gap-2 text-xs text-theme-muted">
                <Clock className="w-3 h-3" />
                {lastUpdate.toLocaleTimeString("tr-TR")}
              </div>
            )}
            <button
              onClick={fetchStocks}
              disabled={refreshing}
              className="btn-primary flex items-center gap-2"
            >
              <RefreshCw
                className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`}
              />
              Tara
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-theme-text">{stocks.length}</p>
          <p className="text-sm text-theme-muted">Toplam Hisse</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-green-500">{topPicks.length}</p>
          <p className="text-sm text-theme-muted">Yüksek Skor (60+)</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-primary">
            {stocks.length > 0
              ? (
                  stocks.reduce((sum, s) => sum + (s.momentum_score || 0), 0) /
                  stocks.length
                ).toFixed(0)
              : 0}
          </p>
          <p className="text-sm text-theme-muted">Ortalama Skor</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-theme-text">
            {filteredAndSortedStocks.length}
          </p>
          <p className="text-sm text-theme-muted">Filtreli Sonuç</p>
        </div>
      </div>

      {/* Stock Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[var(--color-bg-tertiary)]">
              <tr>
                <th
                  className="px-4 py-3 text-left cursor-pointer hover:bg-[var(--color-bg-secondary)]"
                  onClick={() => handleSort("ticker")}
                >
                  <div className="flex items-center gap-1 text-sm font-medium text-theme-muted">
                    Hisse <SortIcon field="ticker" />
                  </div>
                </th>
                <th
                  className="px-4 py-3 text-center cursor-pointer hover:bg-[var(--color-bg-secondary)]"
                  onClick={() => handleSort("score")}
                >
                  <div className="flex items-center justify-center gap-1 text-sm font-medium text-theme-muted">
                    Momentum Skor <SortIcon field="score" />
                  </div>
                </th>
                <th className="px-4 py-3 text-center">
                  <span className="text-sm font-medium text-theme-muted">
                    Öneri
                  </span>
                </th>
                <th className="px-4 py-3 text-right">
                  <span className="text-sm font-medium text-theme-muted">
                    Fiyat
                  </span>
                </th>
                <th
                  className="px-4 py-3 text-right cursor-pointer hover:bg-[var(--color-bg-secondary)]"
                  onClick={() => handleSort("change")}
                >
                  <div className="flex items-center justify-end gap-1 text-sm font-medium text-theme-muted">
                    Değişim <SortIcon field="change" />
                  </div>
                </th>
                <th className="px-4 py-3 text-right">
                  <span className="text-sm font-medium text-theme-muted">
                    Giriş/Stop
                  </span>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {filteredAndSortedStocks.map((stock) => (
                <tr
                  key={stock.ticker}
                  onClick={() => setSelectedTicker(`${stock.ticker}.IS`)}
                  className={`cursor-pointer hover:bg-[var(--color-bg-secondary)] transition-colors ${
                    selectedTicker === `${stock.ticker}.IS`
                      ? "bg-primary/5"
                      : ""
                  }`}
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-10 h-10 rounded-lg ${getScoreBg(
                          stock.momentum_score
                        )} flex items-center justify-center`}
                      >
                        <BarChart2
                          className={`w-5 h-5 ${getScoreColor(
                            stock.momentum_score
                          )}`}
                        />
                      </div>
                      <div>
                        <p className="font-semibold text-theme-text">
                          {stock.ticker?.replace(".IS", "")}
                        </p>
                        <p className="text-xs text-theme-muted">BIST</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-col items-center">
                      <span
                        className={`text-xl font-bold ${getScoreColor(
                          stock.momentum_score
                        )}`}
                      >
                        {stock.momentum_score?.toFixed(0) || 0}
                      </span>
                      <div className="w-16 bg-[var(--color-bg-tertiary)] rounded-full h-1.5 mt-1">
                        <div
                          className={`h-1.5 rounded-full ${
                            stock.momentum_score >= 60
                              ? "bg-green-500"
                              : stock.momentum_score >= 40
                              ? "bg-yellow-500"
                              : "bg-red-500"
                          }`}
                          style={{
                            width: `${Math.min(
                              stock.momentum_score || 0,
                              100
                            )}%`,
                          }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {getRecommendationBadge(stock.recommendation)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="font-medium text-theme-text">
                      ₺{stock.current_price?.toFixed(2) || "-"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span
                      className={`font-medium ${
                        (stock.change_percent || 0) >= 0
                          ? "text-green-500"
                          : "text-red-500"
                      }`}
                    >
                      {(stock.change_percent || 0) >= 0 ? "+" : ""}
                      {stock.change_percent?.toFixed(2) || 0}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex flex-col items-end text-xs">
                      <span className="text-green-500">
                        G: ₺{stock.entry_price?.toFixed(2) || "-"}
                      </span>
                      <span className="text-red-500">
                        S: ₺{stock.stop_loss?.toFixed(2) || "-"}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredAndSortedStocks.length === 0 && (
          <div className="text-center py-12">
            <Search className="w-12 h-12 text-theme-muted mx-auto mb-4" />
            <p className="text-theme-muted">
              Filtrelere uygun hisse bulunamadı
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScreenerPage;
