/**
 * Technical Indicators Display Component - Mobile Optimized
 * Shows all technical indicators in organized cards
 */
import React from "react";
import { TrendingUp, Activity, BarChart3, Volume2 } from "lucide-react";

const IndicatorCard = ({ icon: Icon, label, value, status }) => {
  const getStatusColor = () => {
    if (status === "bullish") return "text-green-400";
    if (status === "bearish") return "text-red-400";
    return "text-gray-400";
  };

  const formatValue = (val) => {
    if (val === null || val === undefined || isNaN(val)) return "-";
    return Number(val).toFixed(2);
  };

  return (
    <div className="bg-theme-card rounded-lg p-2.5 sm:p-4 border border-theme-border hover:border-primary-600 transition-colors">
      <div className="flex items-center gap-1.5 sm:gap-2 mb-1 sm:mb-2">
        <Icon className="w-3 h-3 sm:w-4 sm:h-4 text-primary-500" />
        <span className="text-[10px] sm:text-xs text-theme-muted uppercase tracking-wide truncate">
          {label}
        </span>
      </div>
      <div
        className={`text-lg sm:text-2xl font-bold ${getStatusColor()} truncate`}
      >
        {formatValue(value)}
      </div>
    </div>
  );
};

const TechnicalIndicators = ({ indicators }) => {
  if (!indicators) {
    return (
      <div className="bg-theme-card rounded-lg p-4 sm:p-6 border border-theme-border">
        <div className="text-center text-theme-muted text-sm sm:text-base">
          Göstergeler yükleniyor...
        </div>
      </div>
    );
  }

  const {
    trend = {},
    momentum = {},
    volatility = {},
    volume = {},
  } = indicators;

  // Determine RSI status
  const getRSIStatus = (rsi) => {
    if (rsi < 30) return "bullish"; // Oversold
    if (rsi > 70) return "bearish"; // Overbought
    return "neutral";
  };

  // Determine MACD status
  const getMACDStatus = (macd, signal) => {
    if (macd > signal) return "bullish";
    if (macd < signal) return "bearish";
    return "neutral";
  };

  // Determine trend status
  const getTrendStatus = (ema9, ema21) => {
    if (ema9 > ema21) return "bullish";
    if (ema9 < ema21) return "bearish";
    return "neutral";
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Trend Indicators */}
      <div>
        <div className="flex items-center gap-2 mb-2 sm:mb-3">
          <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 text-primary-500" />
          <h3 className="text-base sm:text-lg font-semibold">
            Trend Göstergeleri
          </h3>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
          <IndicatorCard
            icon={TrendingUp}
            label="EMA 9"
            value={trend.ema_9}
            status={getTrendStatus(trend.ema_9, trend.ema_21)}
          />
          <IndicatorCard
            icon={TrendingUp}
            label="EMA 21"
            value={trend.ema_21}
            status="neutral"
          />
          <IndicatorCard
            icon={TrendingUp}
            label="EMA 50"
            value={trend.ema_50}
            status="neutral"
          />
          <IndicatorCard
            icon={Activity}
            label="ADX"
            value={trend.adx}
            status={trend.adx > 25 ? "bullish" : "neutral"}
          />
        </div>
      </div>

      {/* Momentum Indicators */}
      <div>
        <div className="flex items-center gap-2 mb-2 sm:mb-3">
          <Activity className="w-4 h-4 sm:w-5 sm:h-5 text-primary-500" />
          <h3 className="text-base sm:text-lg font-semibold">
            Momentum Göstergeleri
          </h3>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
          <IndicatorCard
            icon={Activity}
            label="RSI"
            value={momentum.rsi}
            status={getRSIStatus(momentum.rsi)}
          />
          <IndicatorCard
            icon={Activity}
            label="MACD"
            value={momentum.macd}
            status={getMACDStatus(momentum.macd, momentum.macd_signal)}
          />
          <IndicatorCard
            icon={Activity}
            label="MACD Signal"
            value={momentum.macd_signal}
            status="neutral"
          />
          <IndicatorCard
            icon={Activity}
            label="Stochastic K"
            value={momentum.stoch_k}
            status={
              momentum.stoch_k < 20
                ? "bullish"
                : momentum.stoch_k > 80
                ? "bearish"
                : "neutral"
            }
          />
        </div>
      </div>

      {/* Volatility Indicators */}
      <div>
        <div className="flex items-center gap-2 mb-2 sm:mb-3">
          <BarChart3 className="w-4 h-4 sm:w-5 sm:h-5 text-primary-500" />
          <h3 className="text-base sm:text-lg font-semibold">
            Volatilite Göstergeleri
          </h3>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
          <IndicatorCard
            icon={BarChart3}
            label="BB Upper"
            value={volatility.bb_upper}
            status="neutral"
          />
          <IndicatorCard
            icon={BarChart3}
            label="BB Middle"
            value={volatility.bb_middle}
            status="neutral"
          />
          <IndicatorCard
            icon={BarChart3}
            label="BB Lower"
            value={volatility.bb_lower}
            status="neutral"
          />
          <IndicatorCard
            icon={BarChart3}
            label="ATR"
            value={volatility.atr}
            status="neutral"
          />
        </div>
      </div>

      {/* Volume Indicators */}
      <div>
        <div className="flex items-center gap-2 mb-2 sm:mb-3">
          <Volume2 className="w-4 h-4 sm:w-5 sm:h-5 text-primary-500" />
          <h3 className="text-base sm:text-lg font-semibold">
            Hacim Göstergeleri
          </h3>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 sm:gap-3">
          <IndicatorCard
            icon={Volume2}
            label="VWAP"
            value={volume.vwap}
            status="neutral"
          />
          <IndicatorCard
            icon={Volume2}
            label="MFI"
            value={volume.mfi}
            status={
              volume.mfi < 20
                ? "bullish"
                : volume.mfi > 80
                ? "bearish"
                : "neutral"
            }
          />
          <IndicatorCard
            icon={Volume2}
            label="OBV"
            value={volume.obv}
            status="neutral"
          />
        </div>
      </div>
    </div>
  );
};

export default TechnicalIndicators;
