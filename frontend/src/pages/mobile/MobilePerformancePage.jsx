/**
 * Mobile Performance Page
 * 📱 Compact performance metrics with collapsible charts
 */
import React, { useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  Target,
  ChevronDown,
  ChevronUp,
  Activity,
  Percent,
} from 'lucide-react';
import { usePortfolioStore } from '../../store/portfolioStore';
import { formatCurrency, formatPercent } from '../../utils/formatters';

const MobilePerformancePage = () => {
  const {
    trades = [],
    getTradeStats,
    getRealizedPnL,
    getDailyPnL,
    getWeeklyPnL,
    getMonthlyPnL,
    getMaxDrawdown,
  } = usePortfolioStore() || {};

  const [showStats, setShowStats] = useState(true);
  const [showTrades, setShowTrades] = useState(true);
  const [timeframe, setTimeframe] = useState('monthly');

  const stats = getTradeStats?.() || {};
  const realizedPnL = getRealizedPnL?.() || 0;
  const dailyPnL = getDailyPnL?.() || 0;
  const weeklyPnL = getWeeklyPnL?.() || 0;
  const monthlyPnL = getMonthlyPnL?.() || 0;
  const maxDrawdown = getMaxDrawdown?.() || 0;

  const currentPnL = timeframe === 'daily' ? dailyPnL : timeframe === 'weekly' ? weeklyPnL : monthlyPnL;
  const closedTrades = (trades || []).filter(t => t.status === 'closed').slice(-10).reverse();

  const ToggleHeader = ({ title, icon: Icon, isOpen, onToggle, badge, color = 'text-primary-400' }) => (
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
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-primary-500/10 flex items-center justify-center">
          <BarChart3 className="w-4 h-4 text-primary-400" />
        </div>
        <div>
          <h1 className="font-bold text-theme-text text-base">Performans</h1>
          <p className="text-xs text-theme-muted">{trades.length} işlem</p>
        </div>
      </div>

      {/* PnL Summary */}
      <div className="grid grid-cols-3 gap-2">
        <button
          onClick={() => setTimeframe('daily')}
          className={`card p-2 text-center ${timeframe === 'daily' ? 'border-primary-500/50' : ''}`}
        >
          <p className="text-[9px] text-theme-muted">Günlük</p>
          <p className={`text-sm font-bold ${dailyPnL >= 0 ? 'text-success' : 'text-danger'}`}>
            {dailyPnL >= 0 ? '+' : ''}{formatCurrency(dailyPnL)}
          </p>
        </button>
        <button
          onClick={() => setTimeframe('weekly')}
          className={`card p-2 text-center ${timeframe === 'weekly' ? 'border-primary-500/50' : ''}`}
        >
          <p className="text-[9px] text-theme-muted">Haftalık</p>
          <p className={`text-sm font-bold ${weeklyPnL >= 0 ? 'text-success' : 'text-danger'}`}>
            {weeklyPnL >= 0 ? '+' : ''}{formatCurrency(weeklyPnL)}
          </p>
        </button>
        <button
          onClick={() => setTimeframe('monthly')}
          className={`card p-2 text-center ${timeframe === 'monthly' ? 'border-primary-500/50' : ''}`}
        >
          <p className="text-[9px] text-theme-muted">Aylık</p>
          <p className={`text-sm font-bold ${monthlyPnL >= 0 ? 'text-success' : 'text-danger'}`}>
            {monthlyPnL >= 0 ? '+' : ''}{formatCurrency(monthlyPnL)}
          </p>
        </button>
      </div>

      {/* Stats - Collapsible */}
      <div className="card">
        <ToggleHeader
          title="İstatistikler"
          icon={Target}
          isOpen={showStats}
          onToggle={() => setShowStats(!showStats)}
          color="text-success"
        />
        {showStats && (
          <div className="grid grid-cols-2 gap-2 p-3">
            <div className="p-2 rounded-lg bg-theme-card/50 text-center">
              <p className="text-[10px] text-theme-muted uppercase">Win Rate</p>
              <p className="font-bold text-success">{formatPercent(stats.winRate || 0)}</p>
            </div>
            <div className="p-2 rounded-lg bg-theme-card/50 text-center">
              <p className="text-[10px] text-theme-muted uppercase">Profit Factor</p>
              <p className="font-bold text-theme-text">{(stats.profitFactor || 0).toFixed(2)}</p>
            </div>
            <div className="p-2 rounded-lg bg-theme-card/50 text-center">
              <p className="text-[10px] text-theme-muted uppercase">Toplam Kar</p>
              <p className={`font-bold ${realizedPnL >= 0 ? 'text-success' : 'text-danger'}`}>
                {realizedPnL >= 0 ? '+' : ''}{formatCurrency(realizedPnL)}
              </p>
            </div>
            <div className="p-2 rounded-lg bg-theme-card/50 text-center">
              <p className="text-[10px] text-theme-muted uppercase">Max DD</p>
              <p className="font-bold text-warning">{formatPercent(maxDrawdown)}</p>
            </div>
            <div className="p-2 rounded-lg bg-theme-card/50 text-center">
              <p className="text-[10px] text-theme-muted uppercase">Kazanan</p>
              <p className="font-bold text-success">{stats.winningTrades || 0}</p>
            </div>
            <div className="p-2 rounded-lg bg-theme-card/50 text-center">
              <p className="text-[10px] text-theme-muted uppercase">Kaybeden</p>
              <p className="font-bold text-danger">{stats.losingTrades || 0}</p>
            </div>
          </div>
        )}
      </div>

      {/* Recent Trades - Collapsible */}
      <div className="card">
        <ToggleHeader
          title="Son İşlemler"
          icon={Activity}
          isOpen={showTrades}
          onToggle={() => setShowTrades(!showTrades)}
          badge={closedTrades.length}
        />
        {showTrades && (
          <div className="divide-y divide-[var(--glass-border)]">
            {closedTrades.length > 0 ? (
              closedTrades.map((trade, i) => (
                <div key={i} className="p-3 flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-theme-text text-sm">
                        {trade.ticker?.replace('.IS', '')}
                      </span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        trade.type === 'BUY' ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger'
                      }`}>
                        {trade.type === 'BUY' ? 'AL' : 'SAT'}
                      </span>
                    </div>
                    <p className="text-xs text-theme-muted">
                      {trade.quantity} adet @ {formatCurrency(trade.sellPrice || trade.buyPrice)}
                    </p>
                  </div>
                  <span className={`font-bold ${(trade.pnl || 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                    {(trade.pnl || 0) >= 0 ? '+' : ''}{formatCurrency(trade.pnl || 0)}
                  </span>
                </div>
              ))
            ) : (
              <div className="p-6 text-center">
                <Activity className="w-6 h-6 text-theme-muted mx-auto mb-2" />
                <p className="text-sm text-theme-muted">Henüz işlem yok</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MobilePerformancePage;
