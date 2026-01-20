/**
 * Mobile Portfolio Page
 * 📱 Compact, collapsible sections for portfolio management
 */
import React, { useState, useEffect, useMemo } from 'react';
import {
  Briefcase,
  TrendingUp,
  TrendingDown,
  Plus,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  DollarSign,
  Percent,
  Eye,
  EyeOff,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { usePortfolioStore } from '../../store/portfolioStore';
import { formatCurrency, formatPercent } from '../../utils/formatters';

const MobilePortfolioPage = () => {
  const {
    holdings = [],
    getTotalValue,
    getTotalCost,
    getTotalProfitLoss,
    getTotalProfitLossPercent,
    getRealizedPnL,
    getMaxDrawdown,
  } = usePortfolioStore() || {};

  const [showValues, setShowValues] = useState(true);
  const [showPositions, setShowPositions] = useState(true);
  const [showStats, setShowStats] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const totalValue = getTotalValue?.() || 0;
  const totalCost = getTotalCost?.() || 0;
  const profitLoss = getTotalProfitLoss?.() || 0;
  const profitLossPercent = getTotalProfitLossPercent?.() || 0;
  const realizedPnL = getRealizedPnL?.() || 0;
  const maxDrawdown = getMaxDrawdown?.() || 0;

  const validHoldings = (holdings || []).filter(h => h && h.ticker && h.quantity && h.currentPrice);

  const holdingsWithPnL = validHoldings.map(h => ({
    ...h,
    pnl: (h.currentPrice - h.buyPrice) * h.quantity,
    pnlPercent: ((h.currentPrice - h.buyPrice) / h.buyPrice) * 100,
    value: h.quantity * h.currentPrice,
  }));

  const ToggleHeader = ({ title, icon: Icon, isOpen, onToggle, badge, color = "text-primary-400" }) => (
    <button 
      onClick={onToggle}
      className="w-full flex items-center justify-between p-3 border-b border-[var(--glass-border)]"
    >
      <div className="flex items-center gap-2">
        <Icon className={`w-4 h-4 ${color}`} />
        <span className="font-bold text-theme-text text-sm">{title}</span>
        {badge && <span className="text-xs text-theme-muted bg-theme-card px-1.5 py-0.5 rounded">{badge}</span>}
      </div>
      {isOpen ? <ChevronUp className="w-4 h-4 text-theme-muted" /> : <ChevronDown className="w-4 h-4 text-theme-muted" />}
    </button>
  );

  return (
    <div className="space-y-3 pb-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary-500/10 flex items-center justify-center">
            <Briefcase className="w-4 h-4 text-primary-400" />
          </div>
          <div>
            <h1 className="font-bold text-theme-text text-base">Portföyüm</h1>
            <p className="text-xs text-theme-muted">{holdings.length} pozisyon</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowValues(!showValues)}
            className="p-2 bg-theme-card rounded-lg"
          >
            {showValues ? <EyeOff className="w-4 h-4 text-theme-muted" /> : <Eye className="w-4 h-4 text-theme-muted" />}
          </button>
          <button className="p-2 bg-primary-500 rounded-lg">
            <Plus className="w-4 h-4 text-white" />
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-2">
        <div className="card p-3 text-center">
          <p className="text-xs text-theme-muted mb-1">Portföy Değeri</p>
          <p className="text-lg font-bold text-theme-text">
            {showValues ? formatCurrency(totalValue) : '••••••'}
          </p>
        </div>
        <div className={`card p-3 text-center ${profitLoss >= 0 ? 'border-success/30' : 'border-danger/30'}`}>
          <p className="text-xs text-theme-muted mb-1">Açık PnL</p>
          <p className={`text-lg font-bold ${profitLoss >= 0 ? 'text-success' : 'text-danger'}`}>
            {showValues ? `${profitLoss >= 0 ? '+' : ''}${formatCurrency(profitLoss)}` : '••••••'}
          </p>
        </div>
      </div>

      {/* Stats Section - Collapsible */}
      <div className="card">
        <ToggleHeader 
          title="İstatistikler" 
          icon={TrendingUp} 
          isOpen={showStats} 
          onToggle={() => setShowStats(!showStats)}
          color="text-success"
        />
        {showStats && (
          <div className="grid grid-cols-2 gap-2 p-3">
            <div className="p-2 rounded-lg bg-theme-card/50 text-center">
              <p className="text-[10px] text-theme-muted uppercase">Getiri</p>
              <p className={`font-bold ${profitLossPercent >= 0 ? 'text-success' : 'text-danger'}`}>
                {profitLossPercent >= 0 ? '+' : ''}{formatPercent(profitLossPercent)}
              </p>
            </div>
            <div className="p-2 rounded-lg bg-theme-card/50 text-center">
              <p className="text-[10px] text-theme-muted uppercase">Gerçekleşmiş</p>
              <p className={`font-bold ${realizedPnL >= 0 ? 'text-success' : 'text-danger'}`}>
                {showValues ? `${realizedPnL >= 0 ? '+' : ''}${formatCurrency(realizedPnL)}` : '••••'}
              </p>
            </div>
            <div className="p-2 rounded-lg bg-theme-card/50 text-center">
              <p className="text-[10px] text-theme-muted uppercase">Maliyet</p>
              <p className="font-bold text-theme-text">
                {showValues ? formatCurrency(totalCost) : '••••'}
              </p>
            </div>
            <div className="p-2 rounded-lg bg-theme-card/50 text-center">
              <p className="text-[10px] text-theme-muted uppercase">Max DD</p>
              <p className="font-bold text-warning">{formatPercent(maxDrawdown)}</p>
            </div>
          </div>
        )}
      </div>

      {/* Positions - Collapsible */}
      <div className="card">
        <ToggleHeader 
          title="Pozisyonlar" 
          icon={Briefcase} 
          isOpen={showPositions} 
          onToggle={() => setShowPositions(!showPositions)}
          badge={`${holdings.length}`}
        />
        {showPositions && (
          <div className="divide-y divide-[var(--glass-border)]">
            {holdingsWithPnL.length > 0 ? (
              holdingsWithPnL.map((h, i) => (
                <div key={i} className="p-3 hover:bg-theme-card-hover transition-colors">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-theme-text">{h.ticker?.replace('.IS', '')}</span>
                      <span className="text-xs text-theme-muted">{h.quantity} adet</span>
                    </div>
                    <span className={`font-bold ${h.pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                      {h.pnl >= 0 ? '+' : ''}{formatPercent(h.pnlPercent)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <div className="text-theme-muted">
                      <span>Maliyet: </span>
                      <span className="text-theme-text">{formatCurrency(h.buyPrice)}</span>
                    </div>
                    <div className="text-theme-muted">
                      <span>Şimdi: </span>
                      <span className="text-theme-text">{formatCurrency(h.currentPrice)}</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs mt-1">
                    <span className="text-theme-muted">
                      Değer: {showValues ? formatCurrency(h.value) : '••••'}
                    </span>
                    <span className={h.pnl >= 0 ? 'text-success' : 'text-danger'}>
                      {showValues ? `${h.pnl >= 0 ? '+' : ''}${formatCurrency(h.pnl)}` : '••••'}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-6 text-center">
                <Briefcase className="w-8 h-8 text-theme-muted mx-auto mb-2" />
                <p className="text-theme-muted text-sm">Henüz pozisyon yok</p>
                <p className="text-xs text-theme-muted mt-1">+ butonuna tıklayarak ekleyin</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MobilePortfolioPage;
