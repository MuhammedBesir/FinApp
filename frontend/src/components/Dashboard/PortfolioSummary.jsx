/**
 * Portfolio Summary Widget - Gelişmiş Portföy Özeti
 * 📊 Gerçek zamanlı PnL | 💰 Risk metrikleri | 📈 Performans izleme
 */
import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  PieChart, 
  AlertCircle,
  Activity,
  DollarSign,
  Percent,
  Target
} from 'lucide-react';
import { usePortfolioStore } from '../../store/portfolioStore';

const PortfolioSummary = () => {
  const { trades, positions } = usePortfolioStore();
  const [metrics, setMetrics] = useState({
    totalValue: 0,
    totalPnL: 0,
    todayPnL: 0,
    winRate: 0,
    profitFactor: 0,
    openPositions: 0,
    totalTrades: 0,
  });

  useEffect(() => {
    calculateMetrics();
  }, [trades, positions]);

  const calculateMetrics = () => {
    // Güvenli veri kontrolü
    const safeTrades = trades || [];
    const safePositions = positions || [];
    
    if (safeTrades.length === 0 && safePositions.length === 0) {
      return; // Veri yoksa hiçbir şey yapma
    }
    
    const today = new Date().toDateString();
    
    // Toplam değer ve PnL
    const totalValue = safePositions.reduce((sum, pos) => sum + (pos.quantity * pos.currentPrice), 0);
    const totalPnL = safeTrades.reduce((sum, t) => sum + (t.pnl || 0), 0);
    const todayPnL = safeTrades
      .filter(t => new Date(t.createdAt).toDateString() === today)
      .reduce((sum, t) => sum + (t.pnl || 0), 0);
    
    // Win rate
    const closedTrades = safeTrades.filter(t => t.status === 'closed');
    const winningTrades = closedTrades.filter(t => t.pnl > 0).length;
    const winRate = closedTrades.length > 0 
      ? (winningTrades / closedTrades.length) * 100 
      : 0;
    
    // Profit Factor
    const grossProfit = closedTrades
      .filter(t => t.pnl > 0)
      .reduce((sum, t) => sum + t.pnl, 0);
    const grossLoss = Math.abs(
      closedTrades
        .filter(t => t.pnl < 0)
        .reduce((sum, t) => sum + t.pnl, 0)
    );
    const profitFactor = grossLoss > 0 ? grossProfit / grossLoss : 0;

    setMetrics({
      totalValue,
      totalPnL,
      todayPnL,
      winRate,
      profitFactor,
      openPositions: safePositions.length,
      totalTrades: safeTrades.length,
    });
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const stats = [
    {
      label: 'Portföy Değeri',
      value: formatCurrency(metrics.totalValue),
      icon: DollarSign,
      color: 'text-primary-400',
      bgColor: 'bg-primary-500/10',
    },
    {
      label: 'Toplam P&L',
      value: formatCurrency(metrics.totalPnL),
      change: formatPercent((metrics.totalPnL / 10000) * 100), // 10k başlangıç sermayesi varsayımı
      icon: metrics.totalPnL >= 0 ? TrendingUp : TrendingDown,
      color: metrics.totalPnL >= 0 ? 'text-success' : 'text-danger',
      bgColor: metrics.totalPnL >= 0 ? 'bg-success/10' : 'bg-danger/10',
    },
    {
      label: 'Bugünün P&L',
      value: formatCurrency(metrics.todayPnL),
      icon: metrics.todayPnL >= 0 ? TrendingUp : TrendingDown,
      color: metrics.todayPnL >= 0 ? 'text-success' : 'text-danger',
      bgColor: metrics.todayPnL >= 0 ? 'bg-success/10' : 'bg-danger/10',
    },
    {
      label: 'Kazanma Oranı',
      value: `${metrics.winRate.toFixed(1)}%`,
      icon: Target,
      color: metrics.winRate >= 60 ? 'text-success' : metrics.winRate >= 40 ? 'text-warning' : 'text-danger',
      bgColor: metrics.winRate >= 60 ? 'bg-success/10' : metrics.winRate >= 40 ? 'bg-warning/10' : 'bg-danger/10',
    },
    {
      label: 'Profit Factor',
      value: metrics.profitFactor.toFixed(2),
      icon: Activity,
      color: metrics.profitFactor >= 2 ? 'text-success' : metrics.profitFactor >= 1.5 ? 'text-warning' : 'text-danger',
      bgColor: metrics.profitFactor >= 2 ? 'bg-success/10' : metrics.profitFactor >= 1.5 ? 'bg-warning/10' : 'bg-danger/10',
    },
    {
      label: 'Açık Pozisyonlar',
      value: metrics.openPositions,
      subtitle: `${metrics.totalTrades} toplam işlem`,
      icon: PieChart,
      color: 'text-accent-400',
      bgColor: 'bg-accent-500/10',
    },
  ];

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-theme-text mb-1">Portföy Özeti</h3>
          <p className="text-sm text-theme-muted">Gerçek zamanlı performans metrikleri</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-success/10 text-success text-sm font-medium">
          <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
          Canlı
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {stats.map((stat, index) => (
          <div
            key={index}
            className="p-4 rounded-xl bg-theme-card hover:bg-theme-card-hover border border-[var(--glass-border)] transition-all hover:scale-[1.02]"
          >
            <div className="flex items-start justify-between mb-3">
              <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`w-5 h-5 ${stat.color}`} />
              </div>
              {stat.change && (
                <span className={`text-xs font-medium ${stat.color}`}>
                  {stat.change}
                </span>
              )}
            </div>
            <p className="text-sm text-theme-muted mb-1">{stat.label}</p>
            <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
            {stat.subtitle && (
              <p className="text-xs text-theme-muted mt-1">{stat.subtitle}</p>
            )}
          </div>
        ))}
      </div>

      {/* Risk Uyarısı */}
      {metrics.profitFactor < 1.5 && (
        <div className="mt-4 p-4 rounded-xl bg-warning/10 border border-warning/30">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-warning mb-1">Risk Uyarısı</h4>
              <p className="text-sm text-theme-muted">
                Profit Factor düşük seviyede. Risk yönetiminizi gözden geçirin ve daha seçici olun.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PortfolioSummary;
