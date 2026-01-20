/**
 * Position Card - Detaylı Pozisyon Kartı
 * 💼 Açık pozisyon takibi | 📊 P&L hesaplama | 🎯 TP/SL gösterimi
 */
import React, { useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Edit2,
  Trash2,
  Target,
  Shield,
  Calendar,
  Activity,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

const PositionCard = ({ position, onUpdate, onRemove }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('tr-TR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  // Hesaplamalar
  const totalCost = position.quantity * position.buyPrice;
  const currentValue = position.quantity * position.currentPrice;
  const pnl = currentValue - totalCost;
  const pnlPercent = ((pnl / totalCost) * 100);
  const isProfit = pnl >= 0;

  // Holding period
  const holdingDays = Math.floor(
    (new Date() - new Date(position.buyDate)) / (1000 * 60 * 60 * 24)
  );

  // TP/SL durumu
  const slDistance = position.stopLoss
    ? ((position.currentPrice - position.stopLoss) / position.stopLoss) * 100
    : null;
  const tpDistance = position.takeProfit
    ? ((position.takeProfit - position.currentPrice) / position.currentPrice) * 100
    : null;

  return (
    <div className="card border-2 border-primary/20 hover:border-primary/40 transition-all">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg ${
            isProfit ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger'
          }`}>
            {position.ticker?.split('.')[0] || position.symbol}
          </div>
          <div>
            <h3 className="text-lg font-bold text-theme-text">
              {position.ticker?.replace('.IS', '') || position.symbol}
            </h3>
            <div className="flex items-center gap-2 text-xs text-theme-muted">
              <Calendar className="w-3 h-3" />
              <span>{formatDate(position.buyDate)}</span>
              <span>•</span>
              <span>{holdingDays} gün</span>
              {position.trailingStop && (
                <>
                  <span>•</span>
                  <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-500 font-medium">
                    TS {position.trailPercent}%
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className={`text-2xl font-bold ${isProfit ? 'text-success' : 'text-danger'}`}>
            {isProfit ? '+' : ''}{formatCurrency(pnl)}
          </div>
          <div className={`text-sm font-medium ${isProfit ? 'text-success' : 'text-danger'}`}>
            {isProfit ? '+' : ''}{pnlPercent.toFixed(2)}%
          </div>
        </div>
      </div>

      {/* Quantity & Prices */}
      <div className="grid grid-cols-3 gap-3 mb-3">
        <div className="p-3 rounded-lg bg-theme-card border border-[var(--glass-border)]">
          <p className="text-xs text-theme-muted mb-1">Miktar</p>
          <p className="text-lg font-bold text-theme-text">{position.quantity}</p>
        </div>
        <div className="p-3 rounded-lg bg-theme-card border border-[var(--glass-border)]">
          <p className="text-xs text-theme-muted mb-1">Alış</p>
          <p className="text-lg font-bold text-theme-text">
            {formatCurrency(position.buyPrice)}
          </p>
        </div>
        <div className="p-3 rounded-lg bg-theme-card border border-[var(--glass-border)]">
          <p className="text-xs text-theme-muted mb-1">Güncel</p>
          <p className="text-lg font-bold text-primary">
            {formatCurrency(position.currentPrice)}
          </p>
        </div>
      </div>

      {/* TP/SL Levels */}
      {(position.takeProfit || position.stopLoss) && (
        <div className="grid grid-cols-2 gap-3 mb-3">
          {position.stopLoss && (
            <div className="p-3 rounded-lg bg-danger/10 border border-danger/30">
              <div className="flex items-center gap-2 mb-1">
                <Shield className="w-4 h-4 text-danger" />
                <p className="text-xs text-danger font-medium">Stop-Loss</p>
              </div>
              <p className="text-lg font-bold text-danger">
                {formatCurrency(position.stopLoss)}
              </p>
              {slDistance !== null && (
                <p className="text-xs text-danger/70 mt-1">
                  {slDistance > 0 ? '+' : ''}{slDistance.toFixed(1)}% mesafe
                </p>
              )}
            </div>
          )}
          {position.takeProfit && (
            <div className="p-3 rounded-lg bg-success/10 border border-success/30">
              <div className="flex items-center gap-2 mb-1">
                <Target className="w-4 h-4 text-success" />
                <p className="text-xs text-success font-medium">Take-Profit</p>
              </div>
              <p className="text-lg font-bold text-success">
                {formatCurrency(position.takeProfit)}
              </p>
              {tpDistance !== null && (
                <p className="text-xs text-success/70 mt-1">
                  {tpDistance > 0 ? '+' : ''}{tpDistance.toFixed(1)}% kaldı
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Value Summary */}
      <div className="flex items-center justify-between p-3 rounded-lg bg-theme-card/50 border border-[var(--glass-border)] mb-3">
        <div>
          <p className="text-xs text-theme-muted">Toplam Maliyet</p>
          <p className="text-sm font-bold text-theme-text">{formatCurrency(totalCost)}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-theme-muted">Güncel Değer</p>
          <p className="text-sm font-bold text-primary">{formatCurrency(currentValue)}</p>
        </div>
      </div>

      {/* Expandable Details */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-center gap-2 py-2 text-sm text-theme-muted hover:text-primary transition-colors"
      >
        <span>Detaylar</span>
        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {isExpanded && (
        <div className="pt-3 border-t border-[var(--glass-border)] mt-3 space-y-2">
          {/* Additional Info */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2 rounded bg-theme-card">
              <p className="text-theme-muted">Ortalama Maliyet</p>
              <p className="font-bold text-theme-text">{formatCurrency(position.buyPrice)}</p>
            </div>
            <div className="p-2 rounded bg-theme-card">
              <p className="text-theme-muted">Holding Period</p>
              <p className="font-bold text-theme-text">{holdingDays} gün</p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2 pt-2">
            <button
              onClick={() => onUpdate(position)}
              className="flex-1 btn btn-secondary text-sm"
            >
              <Edit2 className="w-4 h-4" />
              Düzenle
            </button>
            <button
              onClick={() => onRemove(position.id)}
              className="flex-1 btn bg-danger/10 text-danger hover:bg-danger/20 text-sm"
            >
              <Trash2 className="w-4 h-4" />
              Kapat
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PositionCard;
