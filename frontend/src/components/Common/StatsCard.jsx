/**
 * Stats Card Component - Modern Glassmorphism Design
 * ✨ Real-time data display with glow effects
 */
import React from "react";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  Activity,
  BarChart3,
} from "lucide-react";

const StatsCard = ({
  title,
  value,
  subtitle,
  change,
  changeType = "neutral", // 'up', 'down', 'neutral'
  icon: Icon = DollarSign,
  iconColor = "primary", // 'primary', 'success', 'danger', 'warning', 'info'
  animated = true,
}) => {
  const getChangeColor = () => {
    if (changeType === "up") return "text-success-light";
    if (changeType === "down") return "text-danger-light";
    return "text-theme-muted";
  };

  const getChangeIcon = () => {
    if (changeType === "up") return <TrendingUp className="w-3.5 h-3.5" />;
    if (changeType === "down") return <TrendingDown className="w-3.5 h-3.5" />;
    return null;
  };

  const getChangeBadgeClass = () => {
    if (changeType === "up") return "badge-success";
    if (changeType === "down") return "badge-danger";
    return "badge-primary";
  };

  return (
    <div className={`stat-card group ${animated ? "animate-fade-in-up" : ""}`}>
      {/* Icon with Glow */}
      <div className={`stat-icon ${iconColor}`}>
        <Icon className="w-6 h-6 relative z-10" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className="text-xs text-theme-muted mb-1.5 font-medium uppercase tracking-wide">
          {title}
        </p>
        <p className="text-2xl font-bold text-theme-text truncate group-hover:text-gradient transition-all duration-300">
          {value}
        </p>
        {(subtitle || change) && (
          <div className="flex items-center gap-2 mt-2">
            {change && (
              <span
                className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-md ${getChangeColor()} bg-current/10`}
              >
                {getChangeIcon()}
                {change}
              </span>
            )}
            {subtitle && (
              <span className="text-xs text-theme-dim">{subtitle}</span>
            )}
          </div>
        )}
      </div>

      {/* Hover Indicator */}
      <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-radial from-primary-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-full -translate-y-1/2 translate-x-1/2" />
    </div>
  );
};

export default StatsCard;
