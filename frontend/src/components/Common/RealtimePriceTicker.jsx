/**
 * Real-time Price Ticker Component
 * Shows live price updates with WebSocket
 */
import React from "react";
import { TrendingUp, TrendingDown, Minus, Wifi, WifiOff } from "lucide-react";
import { useRealtimePrice } from "../../hooks/useWebSocket";

/**
 * Single ticker price display
 */
export const RealtimePriceTicker = ({ ticker, showIndicators = false }) => {
  const { price, isLoading, isConnected } = useRealtimePrice(ticker);

  if (isLoading || !price) {
    return (
      <div className="flex items-center gap-2 animate-pulse">
        <div className="h-6 w-20 bg-white/10 rounded" />
        <div className="h-4 w-12 bg-white/10 rounded" />
      </div>
    );
  }

  const isPositive = price.change_percent >= 0;

  return (
    <div className="flex items-center gap-3">
      {/* Connection indicator */}
      <div className="relative">
        {isConnected ? (
          <Wifi className="w-3 h-3 text-green-500" />
        ) : (
          <WifiOff className="w-3 h-3 text-red-500" />
        )}
        {isConnected && (
          <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
        )}
      </div>

      {/* Price */}
      <div className="font-mono">
        <span className="text-lg font-bold text-white">
          ₺{price.close?.toFixed(2)}
        </span>
      </div>

      {/* Change */}
      <div
        className={`flex items-center gap-1 px-2 py-1 rounded-lg text-sm font-medium ${
          isPositive
            ? "bg-green-500/20 text-green-400"
            : "bg-red-500/20 text-red-400"
        }`}
      >
        {isPositive ? (
          <TrendingUp className="w-3 h-3" />
        ) : (
          <TrendingDown className="w-3 h-3" />
        )}
        <span>
          {isPositive ? "+" : ""}
          {price.change_percent?.toFixed(2)}%
        </span>
      </div>

      {/* Indicators (optional) */}
      {showIndicators && price.indicators && (
        <div className="flex items-center gap-2 text-xs text-slate-400">
          {price.indicators.rsi && (
            <span
              className={`px-2 py-0.5 rounded ${
                price.indicators.rsi > 70
                  ? "bg-red-500/20 text-red-400"
                  : price.indicators.rsi < 30
                    ? "bg-green-500/20 text-green-400"
                    : "bg-white/10"
              }`}
            >
              RSI: {price.indicators.rsi.toFixed(0)}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * Mini price badge for lists
 */
export const RealtimePriceBadge = ({ ticker }) => {
  const { price, isConnected } = useRealtimePrice(ticker);

  if (!price) {
    return <span className="text-slate-500">--</span>;
  }

  const isPositive = price.change_percent >= 0;

  return (
    <span
      className={`inline-flex items-center gap-1 font-mono text-sm ${
        isPositive ? "text-green-400" : "text-red-400"
      }`}
    >
      ₺{price.close?.toFixed(2)}
      <span className="text-xs">
        ({isPositive ? "+" : ""}
        {price.change_percent?.toFixed(1)}%)
      </span>
    </span>
  );
};

/**
 * Compact price card for dashboard
 */
export const RealtimePriceCard = ({ ticker, name }) => {
  const { price, isLoading, isConnected } = useRealtimePrice(ticker);

  if (isLoading) {
    return (
      <div className="glass-card p-4 rounded-xl border border-white/10 animate-pulse">
        <div className="h-4 w-16 bg-white/10 rounded mb-2" />
        <div className="h-6 w-24 bg-white/10 rounded mb-1" />
        <div className="h-4 w-12 bg-white/10 rounded" />
      </div>
    );
  }

  const isPositive = price?.change_percent >= 0;

  return (
    <div className="glass-card p-4 rounded-xl border border-white/10 hover:border-white/20 transition-all">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-slate-400">
          {ticker.replace(".IS", "")}
        </span>
        <div className="flex items-center gap-1">
          {isConnected ? (
            <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
          ) : (
            <span className="w-1.5 h-1.5 bg-red-500 rounded-full" />
          )}
        </div>
      </div>

      {/* Price */}
      <div className="font-mono">
        <span className="text-xl font-bold text-white">
          ₺{price?.close?.toFixed(2) || "--"}
        </span>
      </div>

      {/* Change */}
      <div
        className={`flex items-center gap-1 mt-1 text-sm ${
          isPositive ? "text-green-400" : "text-red-400"
        }`}
      >
        {isPositive ? (
          <TrendingUp className="w-3 h-3" />
        ) : price?.change_percent !== 0 ? (
          <TrendingDown className="w-3 h-3" />
        ) : (
          <Minus className="w-3 h-3" />
        )}
        <span>
          {isPositive ? "+" : ""}
          {price?.change_percent?.toFixed(2) || "0.00"}%
        </span>
      </div>

      {/* Name */}
      {name && <p className="text-xs text-slate-500 mt-2 truncate">{name}</p>}
    </div>
  );
};

/**
 * Multi-ticker price strip
 */
export const RealtimePriceStrip = ({ tickers }) => {
  const { prices, isConnected } = useRealtimePrice(tickers);

  return (
    <div className="flex items-center gap-4 overflow-x-auto py-2 scrollbar-hide">
      {/* Connection status */}
      <div className="flex items-center gap-1 px-3 py-1 rounded-full bg-white/5 flex-shrink-0">
        {isConnected ? (
          <>
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-xs text-green-400">CANLI</span>
          </>
        ) : (
          <>
            <span className="w-2 h-2 bg-red-500 rounded-full" />
            <span className="text-xs text-red-400">BAĞLANTI YOK</span>
          </>
        )}
      </div>

      {/* Tickers */}
      {tickers.map((ticker) => {
        const price = prices[ticker];
        const isPositive = price?.change_percent >= 0;

        return (
          <div
            key={ticker}
            className="flex items-center gap-2 px-3 py-1 rounded-lg bg-white/5 flex-shrink-0"
          >
            <span className="text-xs font-medium text-slate-300">
              {ticker.replace(".IS", "")}
            </span>
            <span className="text-sm font-mono text-white">
              ₺{price?.close?.toFixed(2) || "--"}
            </span>
            <span
              className={`text-xs ${
                isPositive ? "text-green-400" : "text-red-400"
              }`}
            >
              {isPositive ? "+" : ""}
              {price?.change_percent?.toFixed(1) || "0.0"}%
            </span>
          </div>
        );
      })}
    </div>
  );
};

export default RealtimePriceTicker;
