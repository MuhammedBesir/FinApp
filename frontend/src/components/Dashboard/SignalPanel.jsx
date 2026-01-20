/**
 * Signal Panel Component - Mobile Optimized
 * Displays current trading signal with entry/exit levels
 */
import React from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import {
  formatCurrency,
  formatPercent,
  getSignalBgColor,
  getSignalTextColor,
} from "../../utils/formatters";

const SignalPanel = ({ signal }) => {
  if (!signal) {
    return (
      <div className="bg-theme-card rounded-lg p-4 sm:p-6 border border-theme-border">
        <div className="text-center text-theme-muted">
          <Minus className="w-10 h-10 sm:w-12 sm:h-12 mx-auto mb-2 opacity-50" />
          <p className="text-sm sm:text-base">Sinyal bekleniyor...</p>
        </div>
      </div>
    );
  }

  const SignalIcon =
    signal.signal === "BUY"
      ? TrendingUp
      : signal.signal === "SELL"
      ? TrendingDown
      : Minus;

  return (
    <div
      className={`bg-theme-card rounded-lg p-4 sm:p-6 border-2 ${getSignalBgColor(
        signal.signal
      )}`}
    >
      {/* Signal Header - Responsive layout */}
      <div className="flex items-center justify-between mb-3 sm:mb-4">
        <div className="flex items-center gap-2 sm:gap-3">
          <SignalIcon
            className={`w-6 h-6 sm:w-8 sm:h-8 ${getSignalTextColor(
              signal.signal
            )}`}
          />
          <div>
            <h2
              className={`text-2xl sm:text-3xl font-bold ${getSignalTextColor(
                signal.signal
              )}`}
            >
              {signal.signal}
            </h2>
            <p className="text-xs sm:text-sm text-theme-muted">
              {signal.strategy?.toUpperCase()} Strateji
            </p>
          </div>
        </div>

        {/* Signal Strength */}
        <div className="text-right">
          <div className="text-xl sm:text-2xl font-bold">
            {signal.strength}/100
          </div>
          <div className="text-xs sm:text-sm text-theme-muted">Güç</div>
        </div>
      </div>

      {/* Strength Bar */}
      <div className="mb-4 sm:mb-6">
        <div className="w-full bg-gray-700 rounded-full h-2 sm:h-3">
          <div
            className={`h-2 sm:h-3 rounded-full transition-all duration-500 ${
              signal.strength >= 75
                ? "bg-green-500"
                : signal.strength >= 50
                ? "bg-yellow-500"
                : signal.strength >= 25
                ? "bg-orange-500"
                : "bg-red-500"
            }`}
            style={{ width: `${signal.strength}%` }}
          />
        </div>
      </div>

      {/* Price Levels - Responsive grid */}
      <div className="grid grid-cols-3 gap-2 sm:gap-4 mb-4 sm:mb-6">
        <div className="bg-theme-bg rounded-lg p-2 sm:p-3">
          <div className="text-[10px] sm:text-xs text-theme-muted mb-0.5 sm:mb-1">
            Giriş
          </div>
          <div className="text-sm sm:text-lg font-semibold truncate">
            {formatCurrency(signal.entry_price)}
          </div>
        </div>

        <div className="bg-theme-bg rounded-lg p-2 sm:p-3">
          <div className="text-[10px] sm:text-xs text-theme-muted mb-0.5 sm:mb-1">
            Stop Loss
          </div>
          <div className="text-sm sm:text-lg font-semibold text-red-400 truncate">
            {formatCurrency(signal.stop_loss)}
          </div>
        </div>

        <div className="bg-theme-bg rounded-lg p-2 sm:p-3">
          <div className="text-[10px] sm:text-xs text-theme-muted mb-0.5 sm:mb-1">
            Hedef
          </div>
          <div className="text-sm sm:text-lg font-semibold text-green-400 truncate">
            {formatCurrency(signal.take_profit)}
          </div>
        </div>
      </div>

      {/* Risk/Reward and Confidence */}
      <div className="grid grid-cols-2 gap-2 sm:gap-4 mb-4 sm:mb-6">
        <div className="bg-theme-bg rounded-lg p-2 sm:p-3">
          <div className="text-[10px] sm:text-xs text-theme-muted mb-0.5 sm:mb-1">
            Risk/Ödül
          </div>
          <div className="text-base sm:text-xl font-semibold">
            1:{signal.risk_reward_ratio}
          </div>
        </div>

        <div className="bg-theme-bg rounded-lg p-2 sm:p-3">
          <div className="text-[10px] sm:text-xs text-theme-muted mb-0.5 sm:mb-1">
            Güven
          </div>
          <div className="text-base sm:text-xl font-semibold">
            {signal.confidence}/100
          </div>
        </div>
      </div>

      {/* Reasons - Collapsible on mobile */}
      {signal.reasons && signal.reasons.length > 0 && (
        <div>
          <h3 className="text-xs sm:text-sm font-semibold text-theme-muted mb-2">
            Sinyal Sebepleri:
          </h3>
          <div className="space-y-1 sm:space-y-1.5 max-h-32 sm:max-h-none overflow-y-auto">
            {signal.reasons.map((reason, index) => (
              <div
                key={index}
                className="flex items-start gap-1.5 sm:gap-2 text-xs sm:text-sm"
              >
                <span className="text-green-400 mt-0.5 flex-shrink-0">✓</span>
                <span className="text-theme-text">{reason}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Timestamp */}
      {signal.timestamp && (
        <div className="mt-3 sm:mt-4 pt-3 sm:pt-4 border-t border-theme-border">
          <div className="text-[10px] sm:text-xs text-gray-500">
            Son güncelleme: {new Date(signal.timestamp).toLocaleString("tr-TR")}
          </div>
        </div>
      )}
    </div>
  );
};

export default SignalPanel;
