/**
 * Price Card Component - Mobile Responsive
 * Displays current price and basic stats
 */
import React from "react";
import { TrendingUp, TrendingDown } from "lucide-react";
import {
  formatCurrency,
  formatNumber,
  getValueColor,
} from "../../utils/formatters";

const PriceCard = ({
  ticker,
  price,
  change,
  changePercent,
  volume,
  high,
  low,
}) => {
  const isPositive = change >= 0;

  return (
    <div className="bg-theme-card rounded-lg p-3 sm:p-4 md:p-6 border border-theme-border">
      {/* Mobile-first flex layout */}
      <div className="flex flex-col xs:flex-row xs:items-start xs:justify-between gap-2 xs:gap-0">
        <div className="flex items-center xs:items-start gap-3 xs:block">
          <h1 className="text-xl sm:text-2xl md:text-3xl font-bold">
            {ticker || "TRALT.IS"}
          </h1>
          <div className="flex items-center gap-1.5 sm:gap-2 xs:mt-1">
            {isPositive ? (
              <TrendingUp className="w-4 h-4 text-green-500" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-500" />
            )}
            <span
              className={`text-xs sm:text-sm font-medium ${getValueColor(
                change
              )}`}
            >
              {formatCurrency(Math.abs(change))} (
              {changePercent >= 0 ? "+" : ""}
              {changePercent?.toFixed(2)}%)
            </span>
          </div>
        </div>

        <div className="text-left xs:text-right">
          <div className="text-2xl sm:text-3xl md:text-4xl font-bold">
            {formatCurrency(price)}
          </div>
          <div className="text-[10px] sm:text-xs text-theme-muted mt-0.5 sm:mt-1">
            Anlık Fiyat
          </div>
        </div>
      </div>

      {/* Stats grid - responsive columns */}
      <div className="grid grid-cols-3 gap-2 sm:gap-3 md:gap-4 mt-3 sm:mt-4 md:mt-6 pt-3 sm:pt-4 md:pt-6 border-t border-theme-border">
        <div className="text-center xs:text-left">
          <div className="text-[10px] sm:text-xs text-theme-muted mb-0.5 sm:mb-1">
            Yüksek
          </div>
          <div className="text-sm sm:text-base md:text-lg font-semibold text-green-400">
            {formatCurrency(high)}
          </div>
        </div>
        <div className="text-center xs:text-left">
          <div className="text-[10px] sm:text-xs text-theme-muted mb-0.5 sm:mb-1">
            Düşük
          </div>
          <div className="text-sm sm:text-base md:text-lg font-semibold text-red-400">
            {formatCurrency(low)}
          </div>
        </div>
        <div className="text-center xs:text-left">
          <div className="text-[10px] sm:text-xs text-theme-muted mb-0.5 sm:mb-1">
            Hacim
          </div>
          <div className="text-sm sm:text-base md:text-lg font-semibold">
            {formatNumber(volume)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PriceCard;
