/**
 * Recent Trades Widget - Son İşlemler
 * 📊 Son işlemlerin detaylı görünümü | 💰 PnL takibi | ⏱️ Gerçek zamanlı
 */
import React, { useState } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  DollarSign,
  ChevronRight,
  Filter,
  Download
} from 'lucide-react';
import { usePortfolioStore } from '../../store/portfolioStore';
import { Link } from 'react-router-dom';

const RecentTrades = ({ limit = 10 }) => {
  const { trades } = usePortfolioStore();
  const [filter, setFilter] = useState('all'); // all, buy, sell, profit, loss

  // Güvenli trades kontrolü
  const safeTrades = trades || [];

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const today = new Date();
    const diffTime = today - date;
    const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
    
    if (diffHours < 1) {
      const diffMins = Math.floor(diffTime / (1000 * 60));
      return `${diffMins}dk önce`;
    }
    if (diffHours < 24) return `${diffHours}s önce`;
    
    return date.toLocaleDateString('tr-TR', { 
      day: '2-digit', 
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getFilteredTrades = () => {
    let filtered = [...safeTrades].sort((a, b) => 
      new Date(b.createdAt) - new Date(a.createdAt)
    );

    switch (filter) {
      case 'buy':
        filtered = filtered.filter(t => t.type === 'buy');
        break;
      case 'sell':
        filtered = filtered.filter(t => t.type === 'sell');
        break;
      case 'profit':
        filtered = filtered.filter(t => t.pnl > 0);
        break;
      case 'loss':
        filtered = filtered.filter(t => t.pnl < 0);
        break;
      default:
        break;
    }

    return filtered.slice(0, limit);
  };

  const filteredTrades = getFilteredTrades();

  // İstatistikler
  const stats = {
    totalTrades: safeTrades.length,
    wins: safeTrades.filter(t => t.pnl > 0).length,
    losses: safeTrades.filter(t => t.pnl < 0).length,
    totalPnL: safeTrades.reduce((sum, t) => sum + (t.pnl || 0), 0),
  };

  return (
    <div className="card">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-0 mb-4 sm:mb-6">
        <div>
          <h3 className="text-base sm:text-lg font-bold text-theme-text mb-1">Son İşlemler</h3>
          <p className="text-xs sm:text-sm text-theme-muted">
            {stats.totalTrades} işlem • {stats.wins} kazanan • {stats.losses} kaybeden
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="p-1.5 sm:p-2 rounded-lg bg-theme-card hover:bg-theme-card-hover text-theme-muted hover:text-theme-text transition-colors">
            <Download className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
          </button>
          <Link 
            to="/performance"
            className="flex items-center gap-1 px-2.5 sm:px-3 py-1.5 sm:py-2 rounded-lg bg-primary-500/10 text-primary-400 hover:bg-primary-500/20 transition-colors text-xs sm:text-sm font-medium"
          >
            Tümünü Gör
            <ChevronRight className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
          </Link>
        </div>
      </div>

      {/* Filtreler */}
      <div className="flex items-center gap-1.5 sm:gap-2 mb-3 sm:mb-4 pb-3 sm:pb-4 border-b border-[var(--glass-border)] overflow-x-auto">
        {[
          { id: 'all', label: 'Tümü', count: trades.length },
          { id: 'buy', label: 'Alım', count: trades.filter(t => t.type === 'buy').length },
          { id: 'sell', label: 'Satım', count: trades.filter(t => t.type === 'sell').length },
          { id: 'profit', label: 'Kar', count: stats.wins },
          { id: 'loss', label: 'Zarar', count: stats.losses },
        ].map((f) => (
          <button
            key={f.id}
            onClick={() => setFilter(f.id)}
            className={`px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all whitespace-nowrap ${
              filter === f.id
                ? 'bg-primary-500 text-white'
                : 'bg-theme-card hover:bg-theme-card-hover text-theme-muted hover:text-theme-text'
            }`}
          >
            {f.label}
            <span className="ml-1 sm:ml-1.5 text-[10px] sm:text-xs opacity-75">({f.count})</span>
          </button>
        ))}
      </div>

      {/* İşlem Listesi */}
      <div className="space-y-2">
        {filteredTrades.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-theme-card flex items-center justify-center">
              <Filter className="w-8 h-8 text-theme-muted" />
            </div>
            <p className="text-theme-muted">Bu filtre için işlem bulunamadı</p>
          </div>
        ) : (
          filteredTrades.map((trade, index) => {
            const pnlPercent = trade.pnl && trade.price && trade.quantity
              ? (trade.pnl / (trade.price * trade.quantity)) * 100
              : 0;
            const isProfit = trade.pnl >= 0;

            return (
              <div
                key={index}
                className="p-4 rounded-xl bg-theme-card hover:bg-theme-card-hover border border-[var(--glass-border)] transition-all hover:scale-[1.01]"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    {/* Tip Badge */}
                    <div className={`px-3 py-1.5 rounded-lg font-semibold text-xs ${
                      trade.type === 'buy'
                        ? 'bg-success/10 text-success'
                        : 'bg-danger/10 text-danger'
                    }`}>
                      {trade.type === 'buy' ? 'AL' : 'SAT'}
                    </div>

                    {/* İşlem Detayları */}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-bold text-theme-text">
                          {trade.ticker?.split('.')[0] || trade.symbol}
                        </span>
                        <span className="text-xs text-theme-muted">
                          {trade.quantity} adet × {formatCurrency(trade.price)}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-theme-muted">
                        <Clock className="w-3 h-3" />
                        {formatDate(trade.createdAt)}
                        {trade.exitDate && (
                          <>
                            <span>→</span>
                            {formatDate(trade.exitDate)}
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* PnL */}
                  {trade.pnl !== undefined && (
                    <div className="text-right">
                      <div className={`flex items-center gap-1 font-bold ${
                        isProfit ? 'text-success' : 'text-danger'
                      }`}>
                        {isProfit ? (
                          <TrendingUp className="w-4 h-4" />
                        ) : (
                          <TrendingDown className="w-4 h-4" />
                        )}
                        {formatCurrency(Math.abs(trade.pnl))}
                      </div>
                      <div className={`text-xs ${
                        isProfit ? 'text-success' : 'text-danger'
                      }`}>
                        {pnlPercent >= 0 ? '+' : ''}{pnlPercent.toFixed(2)}%
                      </div>
                    </div>
                  )}
                </div>

                {/* Stop-Loss ve Take-Profit (varsa) */}
                {(trade.stopLoss || trade.takeProfit) && (
                  <div className="flex items-center gap-4 mt-3 pt-3 border-t border-[var(--glass-border)]">
                    {trade.stopLoss && (
                      <div className="flex items-center gap-1.5 text-xs">
                        <span className="text-theme-muted">SL:</span>
                        <span className="text-danger font-medium">
                          {formatCurrency(trade.stopLoss)}
                        </span>
                      </div>
                    )}
                    {trade.takeProfit && (
                      <div className="flex items-center gap-1.5 text-xs">
                        <span className="text-theme-muted">TP:</span>
                        <span className="text-success font-medium">
                          {formatCurrency(trade.takeProfit)}
                        </span>
                      </div>
                    )}
                    {trade.exitReason && (
                      <div className="flex items-center gap-1.5 text-xs ml-auto">
                        <span className="text-theme-muted">Çıkış:</span>
                        <span className="text-theme-text font-medium">
                          {trade.exitReason}
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Toplam PnL */}
      {filteredTrades.length > 0 && (
        <div className="mt-4 pt-4 border-t border-[var(--glass-border)]">
          <div className="flex items-center justify-between p-4 rounded-xl bg-theme-card">
            <span className="text-sm font-medium text-theme-muted">
              Toplam P&L ({filteredTrades.length} işlem)
            </span>
            <span className={`text-lg font-bold ${
              stats.totalPnL >= 0 ? 'text-success' : 'text-danger'
            }`}>
              {stats.totalPnL >= 0 ? '+' : ''}{formatCurrency(stats.totalPnL)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default RecentTrades;
