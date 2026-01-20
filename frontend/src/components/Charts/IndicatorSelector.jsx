/**
 * Indicator Selector Component - Modern & Minimalist (Optimized)
 * Allows users to toggle advanced technical indicators on/off
 */
import React, { useState, useCallback, useMemo } from "react";
import {
  TrendingUp,
  GitMerge,
  Activity,
  LineChart,
  ChevronUp,
  Check,
  Settings2,
} from "lucide-react";

const IndicatorSelector = ({ selectedIndicators, onIndicatorsChange }) => {
  const [expandedId, setExpandedId] = useState(null);

  // Bollinger Bands settings
  const [bbPeriod, setBbPeriod] = useState(
    selectedIndicators?.bollinger?.period || 20,
  );
  const [bbStdDev, setBbStdDev] = useState(
    selectedIndicators?.bollinger?.stdDev || 2.0,
  );

  // Memoized toggle handler
  const handleToggle = useCallback(
    (indicator) => {
      const newIndicators = { ...selectedIndicators };

      if (indicator === "bollinger") {
        newIndicators.bollinger = {
          enabled: !selectedIndicators.bollinger?.enabled,
          period: bbPeriod,
          stdDev: bbStdDev,
        };
      } else if (indicator === "linreg") {
        newIndicators.linreg = {
          enabled: !selectedIndicators.linreg?.enabled,
          period: 100,
          offset: 2,
        };
      } else {
        newIndicators[indicator] = {
          enabled: !selectedIndicators[indicator]?.enabled,
        };
      }

      onIndicatorsChange(newIndicators);
    },
    [selectedIndicators, bbPeriod, bbStdDev, onIndicatorsChange],
  );

  const handleBollingerSettings = useCallback(
    (period, stdDev) => {
      setBbPeriod(period);
      setBbStdDev(stdDev);

      if (selectedIndicators.bollinger?.enabled) {
        onIndicatorsChange({
          ...selectedIndicators,
          bollinger: {
            enabled: true,
            period,
            stdDev,
          },
        });
      }
    },
    [selectedIndicators, onIndicatorsChange],
  );

  // Memoized indicators config
  const indicators = useMemo(
    () => [
      {
        id: "ichimoku",
        name: "Ichimoku Cloud",
        shortName: "Ichimoku",
        icon: TrendingUp,
        description: "Trend, momentum ve destek/direnç analizi",
        color: "blue",
        bgColor: "bg-blue-500/10",
        textColor: "text-blue-400",
        borderColor: "border-blue-500/30",
      },
      {
        id: "fibonacci",
        name: "Fibonacci Retracements",
        shortName: "Fibonacci",
        icon: GitMerge,
        description: "Kritik geri çekilme seviyeleri",
        color: "amber",
        bgColor: "bg-amber-500/10",
        textColor: "text-amber-400",
        borderColor: "border-amber-500/30",
      },
      {
        id: "bollinger",
        name: "Bollinger Bands",
        shortName: "Bollinger",
        icon: Activity,
        description: "Volatilite bantları",
        color: "green",
        bgColor: "bg-green-500/10",
        textColor: "text-green-400",
        borderColor: "border-green-500/30",
        hasSettings: true,
      },
      {
        id: "linreg",
        name: "Linear Regression",
        shortName: "LinReg (100)",
        icon: LineChart,
        description: "LinReg (100, close, 2, 2)",
        color: "purple",
        bgColor: "bg-purple-500/10",
        textColor: "text-purple-400",
        borderColor: "border-purple-500/30",
        hasSettings: false, // Sabit ayarlar
      },
      {
        id: "trendChannel",
        name: "Trend Kanalı",
        shortName: "Trend Kanal",
        icon: TrendingUp,
        description: "Yükselen/Düşen kanal ve AL/SAT sinyalleri",
        color: "cyan",
        bgColor: "bg-cyan-500/10",
        textColor: "text-cyan-400",
        borderColor: "border-cyan-500/30",
        hasSettings: false,
      },
    ],
    [],
  );

  // Memoized active count
  const activeCount = useMemo(
    () =>
      Object.values(selectedIndicators).filter((ind) => ind?.enabled).length,
    [selectedIndicators],
  );

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Settings2 className="w-4 h-4 text-primary" />
          <span className="text-sm font-medium text-theme-text">
            İleri Seviye Göstergeler
          </span>
        </div>
        <span className="text-xs text-theme-muted px-2 py-1 rounded-full bg-theme-bg">
          {activeCount} aktif
        </span>
      </div>

      {/* Indicator Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {indicators.map((indicator) => {
          const Icon = indicator.icon;
          const isEnabled = selectedIndicators[indicator.id]?.enabled || false;
          const isExpanded = expandedId === indicator.id;

          return (
            <div key={indicator.id} className="relative">
              {/* Main Toggle Button */}
              <button
                onClick={() => handleToggle(indicator.id)}
                className={`w-full p-3 rounded-xl transition-all duration-200 border ${
                  isEnabled
                    ? `${indicator.bgColor} ${indicator.borderColor} shadow-sm`
                    : "bg-theme-bg border-theme-border hover:border-theme-muted"
                }`}
              >
                <div className="flex flex-col items-center gap-2">
                  {/* Icon with checkbox */}
                  <div className="relative">
                    <div
                      className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        isEnabled ? indicator.bgColor : "bg-theme-border/50"
                      }`}
                    >
                      <Icon
                        className={`w-5 h-5 ${
                          isEnabled ? indicator.textColor : "text-theme-muted"
                        }`}
                      />
                    </div>
                    {isEnabled && (
                      <div className="absolute -top-1 -right-1 w-4 h-4 bg-success rounded-full flex items-center justify-center">
                        <Check className="w-2.5 h-2.5 text-white" />
                      </div>
                    )}
                  </div>

                  {/* Name */}
                  <span
                    className={`text-xs font-medium ${
                      isEnabled ? indicator.textColor : "text-theme-muted"
                    }`}
                  >
                    {indicator.shortName}
                  </span>
                </div>
              </button>

              {/* Settings Button (if has settings and enabled) */}
              {indicator.hasSettings && isEnabled && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setExpandedId(isExpanded ? null : indicator.id);
                  }}
                  className="absolute -bottom-1 left-1/2 -translate-x-1/2 px-2 py-0.5 bg-theme-card border border-theme-border rounded-full text-[10px] text-theme-muted hover:text-theme-text transition-colors"
                >
                  Ayarlar
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Expanded Settings Panel */}
      {expandedId && (
        <div className="p-4 rounded-xl bg-theme-bg border border-theme-border animate-in slide-in-from-top-2 duration-200">
          {expandedId === "bollinger" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-theme-text">
                  Bollinger Bands Ayarları
                </h4>
                <button
                  onClick={() => setExpandedId(null)}
                  className="text-theme-muted hover:text-theme-text"
                >
                  <ChevronUp className="w-4 h-4" />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-theme-muted block mb-1.5">
                    Period
                  </label>
                  <input
                    type="number"
                    value={bbPeriod}
                    onChange={(e) =>
                      handleBollingerSettings(
                        parseInt(e.target.value),
                        bbStdDev,
                      )
                    }
                    min="5"
                    max="100"
                    className="w-full bg-theme-card border border-theme-border rounded-lg px-3 py-2 text-sm text-theme-text focus:outline-none focus:border-primary transition-colors"
                  />
                </div>
                <div>
                  <label className="text-xs text-theme-muted block mb-1.5">
                    Std Dev
                  </label>
                  <input
                    type="number"
                    value={bbStdDev}
                    onChange={(e) =>
                      handleBollingerSettings(
                        bbPeriod,
                        parseFloat(e.target.value),
                      )
                    }
                    min="1"
                    max="5"
                    step="0.1"
                    className="w-full bg-theme-card border border-theme-border rounded-lg px-3 py-2 text-sm text-theme-text focus:outline-none focus:border-primary transition-colors"
                  />
                </div>
              </div>

              <p className="text-[10px] text-theme-muted">
                Standart: Period 20, Std Dev 2.0
              </p>
            </div>
          )}
        </div>
      )}

      {/* Info Text */}
      <p className="text-[10px] text-theme-muted text-center">
        Göstergeye tıklayarak aktif/pasif yapın
      </p>
    </div>
  );
};

export default IndicatorSelector;
