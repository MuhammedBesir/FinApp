/**
 * Top Movers Component - En Çok Hareket Eden BIST30 Hisseleri
 * Günlük en çok yükselen ve düşen hisseleri gösterir
 */
import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Flame,
  ArrowUpRight,
  ArrowDownRight,
  BarChart2,
  Volume2,
} from "lucide-react";

const TopMovers = ({ refreshInterval = 60000 }) => {
  const [movers, setMovers] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchTopMovers = useCallback(async () => {
    try {
      setLoading(true);
      // Use relative path explicitly, assuming proxy or same-domain handling
      const response = await axios.get(
        "/api/screener/top-movers?top_n=5",
      );
      setMovers(response.data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error("Error fetching top movers:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTopMovers();
    // Her dakika güncelle
    const interval = setInterval(fetchTopMovers, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchTopMovers, refreshInterval]);

  const formatVolume = (volume) => {
    if (volume >= 1000000000) return `${(volume / 1000000000).toFixed(1)}B`;
    if (volume >= 1000000) return `${(volume / 1000000).toFixed(1)}M`;
    if (volume >= 1000) return `${(volume / 1000).toFixed(1)}K`;
    return volume.toString();
  };

  const MoverCard = ({ stock, type }) => {
    const isGainer = type === "gainer";
    const colorClass = isGainer ? "text-success" : "text-danger";
    const bgClass = isGainer ? "bg-success/10" : "bg-danger/10";
    const borderClass = isGainer ? "border-success/30" : "border-danger/30";

    return (
      <div
        className={`p-3 rounded-xl ${bgClass} border ${borderClass} hover:scale-[1.01] transition-all cursor-pointer group`}
      >
        <div className="flex items-start justify-between gap-3">
          {/* Left Section */}
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <div
              className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${bgClass} group-hover:scale-110 transition-transform`}
            >
              {isGainer ? (
                <ArrowUpRight className={`w-4 h-4 ${colorClass}`} />
              ) : (
                <ArrowDownRight className={`w-4 h-4 ${colorClass}`} />
              )}
            </div>
            <div className="min-w-0 flex-1 overflow-hidden">
              <p className="font-bold text-theme-text text-sm truncate">{stock.symbol}</p>
              <p className="text-xs text-theme-muted truncate">{stock.sector}</p>
            </div>
          </div>
          
          {/* Right Section - Fixed Width */}
          <div className="text-right flex-shrink-0 w-[70px]">
            <p className="font-bold text-theme-text text-sm">₺{stock.price.toFixed(2)}</p>
            <p className={`text-xs font-bold ${colorClass}`}>
              {stock.change_percent > 0 ? "+" : ""}
              {stock.change_percent.toFixed(1)}%
            </p>
          </div>
        </div>
        
        {/* Volume bar - Separate Row */}
        <div className="mt-2.5 pt-2 border-t border-[var(--glass-border)] flex items-center justify-between text-xs text-theme-muted">
          <span className="flex items-center gap-1">
            <Volume2 className="w-3 h-3" />
            {formatVolume(stock.volume)}
          </span>
          <span className="text-xs font-medium">x{stock.volume_ratio.toFixed(1)}</span>
        </div>
      </div>
    );
  };

  if (loading && !movers) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Flame className="w-5 h-5 text-warning" />
          <h3 className="font-bold text-theme-text">En Çok Hareket</h3>
        </div>
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-6 h-6 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  if (!movers?.success) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Flame className="w-5 h-5 text-warning" />
          <h3 className="font-bold text-theme-text">En Çok Hareket</h3>
        </div>
        <p className="text-center text-theme-muted py-4">Veri yüklenemiyor</p>
      </div>
    );
  }

  const hasGainers = movers.gainers && movers.gainers.length > 0;
  const hasLosers = movers.losers && movers.losers.length > 0;

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Flame className="w-5 h-5 text-warning" />
          <div>
            <h3 className="font-bold text-theme-text">En Çok Hareket</h3>
            <p className="text-xs text-theme-muted">BIST30 Günlük</p>
          </div>
        </div>
        <button
          onClick={fetchTopMovers}
          disabled={loading}
          className="p-2 rounded-lg hover:bg-[var(--color-bg-secondary)] transition-colors"
        >
          <RefreshCw
            className={`w-4 h-4 text-theme-muted ${loading ? "animate-spin" : ""}`}
          />
        </button>
      </div>

      {/* Market Sentiment */}
      <div className="flex items-center justify-between p-2 rounded-lg bg-[var(--color-bg-secondary)] mb-4 text-xs">
        <span className="text-theme-muted">Piyasa:</span>
        <span
          className={`font-semibold ${
            movers.market_sentiment === "YUKSELIS"
              ? "text-success"
              : movers.market_sentiment === "DUSUS"
                ? "text-danger"
                : "text-warning"
          }`}
        >
          {movers.market_sentiment === "YUKSELIS"
            ? "📈 Yükseliş"
            : movers.market_sentiment === "DUSUS"
              ? "📉 Düşüş"
              : "➡️ Yatay"}
        </span>
        <span className="text-theme-muted">
          {movers.stats?.positive}↑ / {movers.stats?.negative}↓
        </span>
      </div>

      {/* Gainers & Losers - Single Column */}
      <div className="space-y-4">
        {/* Top Gainers */}
        {hasGainers && (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-4 h-4 text-success" />
              <span className="text-sm font-semibold text-success">
                En Çok Yükselenler
              </span>
            </div>
            <div className="space-y-2">
              {movers.gainers.slice(0, 3).map((stock) => (
                <MoverCard key={stock.ticker} stock={stock} type="gainer" />
              ))}
            </div>
          </div>
        )}

        {/* Top Losers */}
        {hasLosers && (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <TrendingDown className="w-4 h-4 text-danger" />
              <span className="text-sm font-semibold text-danger">
                En Çok Düşenler
              </span>
            </div>
            <div className="space-y-2">
              {movers.losers.slice(0, 3).map((stock) => (
                <MoverCard key={stock.ticker} stock={stock} type="loser" />
              ))}
            </div>
          </div>
        )}

        {!hasGainers && !hasLosers && (
          <p className="text-center text-theme-muted text-sm py-8">
            Henüz veri yok
          </p>
        )}
      </div>

      {/* Last Update */}
      {lastUpdate && (
        <div className="mt-4 pt-3 border-t border-[var(--color-border)] text-xs text-theme-muted text-center">
          Son güncelleme: {lastUpdate.toLocaleTimeString("tr-TR")}
        </div>
      )}
    </div>
  );
};

export default TopMovers;
