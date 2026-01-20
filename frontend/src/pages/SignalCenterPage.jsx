/**
 * Signal Center Page - Sinyal Merkezi
 * Tüm hisseler için alım/satım sinyalleri
 * Updated with Glassmorphism Design
 */
import React, { useState, useEffect } from "react";
import {
  Bell,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Filter,
  ArrowUp,
  ArrowDown,
  Minus,
  Target,
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart2,
  Sparkles,
  Radio,
} from "lucide-react";
import { useStore } from "../store";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

// BIST 30 hisseleri
const BIST_STOCKS = [
  "AKBNK",
  "ARCLK",
  "ASELS",
  "BIMAS",
  "EKGYO",
  "EREGL",
  "FROTO",
  "GARAN",
  "GUBRF",
  "HEKTS",
  "ISCTR",
  "KCHOL",
  "KONTR",
  "KRDMD",
  "MGROS",
  "ODAS",
  "OYAKC",
  "PETKM",
  "PGSUS",
  "SAHOL",
  "SASA",
  "SISE",
  "TAVHL",
  "TCELL",
  "THYAO",
  "TKFEN",
  "TOASO",
  "TUPRS",
  "VAKBN",
  "YKBNK",
  "TRALT",
];

const SignalCenterPage = () => {
  const { selectedTicker, setSelectedTicker } = useStore();
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [strategy, setStrategy] = useState("moderate");
  const [filter, setFilter] = useState("all"); // all, buy, sell, hold
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchSignals = async () => {
    setRefreshing(true);
    const results = [];

    // Paralel olarak tüm hisselerin sinyallerini al
    const promises = BIST_STOCKS.map(async (stock) => {
      try {
        const response = await fetch(
          `${API_URL}/signals/${stock}.IS?strategy=${strategy}&interval=1h&period=1mo`,
        );
        if (response.ok) {
          const data = await response.json();
          return { ticker: stock, ...data };
        }
        return null;
      } catch (error) {
        console.error(`Error fetching signal for ${stock}:`, error);
        return null;
      }
    });

    const allResults = await Promise.all(promises);
    const validResults = allResults.filter((r) => r !== null);

    // Sinyal gücüne göre sırala
    validResults.sort((a, b) => (b.strength || 0) - (a.strength || 0));

    setSignals(validResults);
    setLastUpdate(new Date());
    setLoading(false);
    setRefreshing(false);
  };

  useEffect(() => {
    fetchSignals();
    // Her 5 dakikada bir güncelle
    const interval = setInterval(fetchSignals, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [strategy]);

  const getSignalIcon = (signal) => {
    if (signal === "BUY" || signal === "STRONG_BUY") {
      return <TrendingUp className="w-5 h-5 text-green-500" />;
    } else if (signal === "SELL" || signal === "STRONG_SELL") {
      return <TrendingDown className="w-5 h-5 text-red-500" />;
    }
    return <Minus className="w-5 h-5 text-yellow-500" />;
  };

  const getSignalBadge = (signal) => {
    const badges = {
      STRONG_BUY: {
        text: "Güçlü AL",
        class:
          "bg-success/20 text-success border-success/30 shadow-lg shadow-success/10",
      },
      BUY: {
        text: "AL",
        class: "bg-success/10 text-success border-success/20",
      },
      HOLD: {
        text: "TUT",
        class: "bg-warning/10 text-warning border-warning/20",
      },
      SELL: {
        text: "SAT",
        class: "bg-danger/10 text-danger border-danger/20",
      },
      STRONG_SELL: {
        text: "Güçlü SAT",
        class:
          "bg-danger/20 text-danger border-danger/30 shadow-lg shadow-danger/10",
      },
    };
    const badge = badges[signal] || badges["HOLD"];
    return (
      <span
        className={`px-3 py-1.5 rounded-xl text-xs font-bold border ${badge.class}`}
      >
        {badge.text}
      </span>
    );
  };

  const getStrengthBar = (strength) => {
    const percentage = Math.min(Math.abs(strength || 0), 100);
    const isPositive = (strength || 0) >= 0;
    return (
      <div className="w-full glass rounded-full h-2.5 overflow-hidden">
        <div
          className={`h-2.5 rounded-full transition-all duration-500 ${
            isPositive
              ? "bg-gradient-to-r from-success to-emerald-400"
              : "bg-gradient-to-r from-danger to-red-400"
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    );
  };

  const filteredSignals = signals.filter((s) => {
    if (filter === "all") return true;
    if (filter === "buy")
      return s.signal === "BUY" || s.signal === "STRONG_BUY";
    if (filter === "sell")
      return s.signal === "SELL" || s.signal === "STRONG_SELL";
    if (filter === "hold") return s.signal === "HOLD";
    return true;
  });

  const stats = {
    buy: signals.filter((s) => s.signal === "BUY" || s.signal === "STRONG_BUY")
      .length,
    sell: signals.filter(
      (s) => s.signal === "SELL" || s.signal === "STRONG_SELL",
    ).length,
    hold: signals.filter((s) => s.signal === "HOLD").length,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="relative mb-6">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shadow-xl shadow-primary-500/30">
              <RefreshCw className="w-8 h-8 text-white animate-spin" />
            </div>
          </div>
          <p className="text-theme-muted font-medium">
            Sinyaller yükleniyor...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3 sm:space-y-4 md:space-y-6 animate-fade-in">
      {/* Header Stats - Glass Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-3 md:gap-4">
        <div className="card relative overflow-hidden group p-2.5 sm:p-3 md:p-4">
          <div className="absolute inset-0 bg-gradient-to-br from-success/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="relative flex items-center gap-2 sm:gap-3 md:gap-4">
            <div className="w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 rounded-lg sm:rounded-xl md:rounded-2xl bg-gradient-to-br from-success/20 to-success/5 flex items-center justify-center border border-success/20 group-hover:shadow-lg group-hover:shadow-success/20 transition-all flex-shrink-0">
              <TrendingUp className="w-5 h-5 sm:w-6 sm:h-6 md:w-7 md:h-7 text-success" />
            </div>
            <div>
              <p className="text-xl sm:text-2xl md:text-3xl font-bold text-success">{stats.buy}</p>
              <p className="text-[10px] sm:text-xs md:text-sm text-theme-muted font-medium">AL Sinyali</p>
            </div>
          </div>
        </div>
        <div className="card relative overflow-hidden group p-2.5 sm:p-3 md:p-4">
          <div className="absolute inset-0 bg-gradient-to-br from-warning/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="relative flex items-center gap-2 sm:gap-3 md:gap-4">
            <div className="w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 rounded-lg sm:rounded-xl md:rounded-2xl bg-gradient-to-br from-warning/20 to-warning/5 flex items-center justify-center border border-warning/20 group-hover:shadow-lg group-hover:shadow-warning/20 transition-all flex-shrink-0">
              <Minus className="w-5 h-5 sm:w-6 sm:h-6 md:w-7 md:h-7 text-warning" />
            </div>
            <div>
              <p className="text-xl sm:text-2xl md:text-3xl font-bold text-warning">{stats.hold}</p>
              <p className="text-[10px] sm:text-xs md:text-sm text-theme-muted font-medium">
                TUT Sinyali
              </p>
            </div>
          </div>
        </div>
        <div className="card relative overflow-hidden group p-2.5 sm:p-3 md:p-4">
          <div className="absolute inset-0 bg-gradient-to-br from-danger/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="relative flex items-center gap-2 sm:gap-3 md:gap-4">
            <div className="w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 rounded-lg sm:rounded-xl md:rounded-2xl bg-gradient-to-br from-danger/20 to-danger/5 flex items-center justify-center border border-danger/20 group-hover:shadow-lg group-hover:shadow-danger/20 transition-all flex-shrink-0">
              <TrendingDown className="w-5 h-5 sm:w-6 sm:h-6 md:w-7 md:h-7 text-danger" />
            </div>
            <div>
              <p className="text-xl sm:text-2xl md:text-3xl font-bold text-danger">{stats.sell}</p>
              <p className="text-[10px] sm:text-xs md:text-sm text-theme-muted font-medium">
                SAT Sinyali
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Controls - Glass Card */}
      <div className="card p-3 sm:p-4">
        <div className="flex flex-col gap-2 sm:gap-3">
          <div className="flex flex-wrap gap-1.5 sm:gap-2">
            <button
              onClick={() => setFilter("all")}
              className={`px-3 sm:px-4 md:px-5 py-1.5 sm:py-2 md:py-2.5 rounded-lg sm:rounded-xl text-xs sm:text-sm font-semibold transition-all duration-300 ${
                filter === "all"
                  ? "btn-primary"
                  : "glass border border-[var(--glass-border)] text-theme-text hover:border-primary-500/50"
              }`}
            >
              Tümü ({signals.length})
            </button>
            <button
              onClick={() => setFilter("buy")}
              className={`px-3 sm:px-4 md:px-5 py-1.5 sm:py-2 md:py-2.5 rounded-lg sm:rounded-xl text-xs sm:text-sm font-semibold transition-all duration-300 ${
                filter === "buy"
                  ? "bg-success text-white shadow-lg shadow-success/30"
                  : "glass border border-[var(--glass-border)] text-theme-text hover:border-success/50"
              }`}
            >
              AL ({stats.buy})
            </button>
            <button
              onClick={() => setFilter("hold")}
              className={`px-3 sm:px-4 md:px-5 py-1.5 sm:py-2 md:py-2.5 rounded-lg sm:rounded-xl text-xs sm:text-sm font-semibold transition-all duration-300 ${
                filter === "hold"
                  ? "bg-warning text-black shadow-lg shadow-warning/30"
                  : "glass border border-[var(--glass-border)] text-theme-text hover:border-warning/50"
              }`}
            >
              TUT ({stats.hold})
            </button>
            <button
              onClick={() => setFilter("sell")}
              className={`px-3 sm:px-4 md:px-5 py-1.5 sm:py-2 md:py-2.5 rounded-lg sm:rounded-xl text-xs sm:text-sm font-semibold transition-all duration-300 ${
                filter === "sell"
                  ? "bg-danger text-white shadow-lg shadow-danger/30"
                  : "glass border border-[var(--glass-border)] text-theme-text hover:border-danger/50"
              }`}
            >
              SAT ({stats.sell})
            </button>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
              className="px-4 py-2.5 rounded-xl glass border border-[var(--glass-border)] text-theme-text bg-transparent text-sm font-medium focus:border-primary-500/50 focus:outline-none transition-all cursor-pointer"
            >
              <option value="conservative">Muhafazakar</option>
              <option value="moderate">Dengeli</option>
              <option value="aggressive">Agresif</option>
            </select>

            <button
              onClick={fetchSignals}
              disabled={refreshing}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl glass border border-[var(--glass-border)] text-theme-text hover:border-primary-500/50 hover:text-primary-400 transition-all duration-300 font-medium disabled:opacity-50"
            >
              <RefreshCw
                className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`}
              />
              Yenile
            </button>
          </div>
        </div>

        {lastUpdate && (
          <div className="mt-4 flex items-center gap-2 text-xs text-theme-muted">
            <div className="live-indicator">
              <div className="live-dot" />
            </div>
            <Clock className="w-3.5 h-3.5" />
            Son güncelleme: {lastUpdate.toLocaleTimeString("tr-TR")}
          </div>
        )}
      </div>

      {/* Signals Grid - Glass Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 md:gap-5">
        {filteredSignals.map((item, i) => (
          <div
            key={item.ticker}
            onClick={() => setSelectedTicker(`${item.ticker}.IS`)}
            className={`card cursor-pointer hover:border-primary-500/50 transition-all duration-300 group relative overflow-hidden ${
              selectedTicker === `${item.ticker}.IS`
                ? "border-primary-500 shadow-lg shadow-primary-500/10"
                : ""
            }`}
            style={{ animationDelay: `${i * 30}ms` }}
          >
            {/* Background Glow */}
            <div
              className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 ${
                item.signal?.includes("BUY")
                  ? "bg-gradient-to-br from-success/5 to-transparent"
                  : item.signal?.includes("SELL")
                    ? "bg-gradient-to-br from-danger/5 to-transparent"
                    : "bg-gradient-to-br from-warning/5 to-transparent"
              }`}
            />

            <div className="relative flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center border transition-all group-hover:scale-110 ${
                    item.signal?.includes("BUY")
                      ? "bg-success/10 border-success/20"
                      : item.signal?.includes("SELL")
                        ? "bg-danger/10 border-danger/20"
                        : "bg-warning/10 border-warning/20"
                  }`}
                >
                  {getSignalIcon(item.signal)}
                </div>
                <div>
                  <h3 className="font-bold text-theme-text text-lg">
                    {item.ticker}
                  </h3>
                  <p className="text-xs text-theme-muted">
                    {item.strategy} strateji
                  </p>
                </div>
              </div>
              {getSignalBadge(item.signal)}
            </div>

            <div className="relative space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-theme-muted font-medium">
                    Sinyal Gücü
                  </span>
                  <span
                    className={`font-bold ${
                      (item.strength || 0) >= 50
                        ? "text-success"
                        : (item.strength || 0) >= 25
                          ? "text-warning"
                          : "text-danger"
                    }`}
                  >
                    {item.strength?.toFixed(1) || 0}%
                  </span>
                </div>
                {getStrengthBar(item.strength)}
              </div>

              {item.entry_price && (
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="glass border border-success/20 rounded-xl p-3">
                    <p className="text-theme-muted text-xs mb-1">Giriş</p>
                    <p className="font-bold text-success">
                      ₺{item.entry_price?.toFixed(2)}
                    </p>
                  </div>
                  <div className="glass border border-danger/20 rounded-xl p-3">
                    <p className="text-theme-muted text-xs mb-1">Stop Loss</p>
                    <p className="font-bold text-danger">
                      ₺{item.stop_loss?.toFixed(2)}
                    </p>
                  </div>
                </div>
              )}

              {item.targets && item.targets.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {item.targets.slice(0, 3).map((target, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold glass border border-primary-500/20 text-primary-400"
                    >
                      H{idx + 1}: ₺{target?.toFixed(2)}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {filteredSignals.length === 0 && (
        <div className="text-center py-16">
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-primary-500/10 to-accent-500/10 flex items-center justify-center border border-[var(--glass-border)]">
            <Bell className="w-10 h-10 text-theme-muted" />
          </div>
          <h3 className="text-lg font-bold text-theme-text mb-2">
            Sinyal Bulunamadı
          </h3>
          <p className="text-theme-muted">
            Bu filtreye uygun sinyal bulunamadı
          </p>
        </div>
      )}
    </div>
  );
};

export default SignalCenterPage;
