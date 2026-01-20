/**
 * Backtest Results Component
 * Displays backtest performance with charts and metrics
 */
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { TrendingUp, TrendingDown, DollarSign, Activity, BarChart3, Target } from 'lucide-react';
import { formatCurrency, formatPercent } from '../../utils/formatters';

const BacktestResults = ({ results }) => {
  if (!results || !results.summary) {
    return (
      <div className="bg-theme-card rounded-lg p-6 border border-theme-border">
        <p className="text-theme-muted text-center">Backtest sonucu yok. Backtest çalıştırmak için ayarları yapılandırın.</p>
      </div>
    );
  }

  const { summary, equity_curve, trades } = results;

  // Prepare equity curve data for chart
  const equityData = equity_curve?.map((point, index) => ({
    index: index,
    equity: point.equity,
    drawdown: point.drawdown_pct,
  })) || [];

  // Stats cards data
  const statsCards = [
    {
      label: 'Toplam Getiri',
      value: formatPercent(summary.total_return),
      icon: TrendingUp,
      color: summary.total_return >= 0 ? 'text-green-400' : 'text-red-400',
      bgColor: summary.total_return >= 0 ? 'bg-green-500/10' : 'bg-red-500/10',
    },
    {
      label: 'Kazanma Oranı',
      value: formatPercent(summary.win_rate),
      icon: Target,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
    },
    {
      label: 'Sharpe Ratio',
      value: summary.sharpe_ratio?.toFixed(2) || 'N/A',
      icon: Activity,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/10',
    },
    {
      label: 'Max Drawdown',
      value: formatPercent(summary.max_drawdown),
      icon: TrendingDown,
      color: 'text-orange-400',
      bgColor: 'bg-orange-500/10',
    },
    {
      label: 'Toplam İşlem',
      value: summary.total_trades,
      icon: BarChart3,
      color: 'text-cyan-400',
      bgColor: 'bg-cyan-500/10',
    },
    {
      label: 'Net Kâr',
      value: formatCurrency(summary.net_profit),
      icon: DollarSign,
      color: summary.net_profit >= 0 ? 'text-green-400' : 'text-red-400',
      bgColor: summary.net_profit >= 0 ? 'bg-green-500/10' : 'bg-red-500/10',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-theme-card rounded-lg p-6 border border-theme-border">
        <h2 className="text-2xl font-bold mb-2">Backtest Sonuçları</h2>
        <p className="text-theme-muted">
          {results.config?.ticker} - {results.config?.start_date} → {results.config?.end_date}
        </p>
        <p className="text-sm text-gray-500 mt-1">
          Strateji: <span className="text-primary-400 capitalize">{results.config?.strategy}</span>
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {statsCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="bg-theme-card rounded-lg p-4 border border-theme-border">
              <div className={`inline-flex p-2 rounded-lg ${stat.bgColor} mb-2`}>
                <Icon className={`w-5 h-5 ${stat.color}`} />
              </div>
              <div className="text-xs text-theme-muted mb-1">{stat.label}</div>
              <div className={`text-xl font-bold ${stat.color}`}>{stat.value}</div>
            </div>
          );
        })}
      </div>

      {/* Equity Curve Chart */}
      <div className="bg-theme-card rounded-lg p-6 border border-theme-border">
        <h3 className="text-lg font-semibold mb-4">Sermaye Eğrisi</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={equityData}>
            <defs>
              <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#2b2f3e" />
            <XAxis 
              dataKey="index" 
              stroke="#6b7280"
              tick={{ fill: '#9ca3af' }}
            />
            <YAxis 
              stroke="#6b7280"
              tick={{ fill: '#9ca3af' }}
              tickFormatter={(value) => formatCurrency(value)}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1a1d29',
                border: '1px solid #2b2f3e',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#9ca3af' }}
              formatter={(value) => [formatCurrency(value), 'Sermaye']}
            />
            <Area
              type="monotone"
              dataKey="equity"
              stroke="#10b981"
              strokeWidth={2}
              fill="url(#equityGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Drawdown Chart */}
      <div className="bg-theme-card rounded-lg p-6 border border-theme-border">
        <h3 className="text-lg font-semibold mb-4">Drawdown Analizi</h3>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={equityData}>
            <defs>
              <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#2b2f3e" />
            <XAxis 
              dataKey="index" 
              stroke="#6b7280"
              tick={{ fill: '#9ca3af' }}
            />
            <YAxis 
              stroke="#6b7280"
              tick={{ fill: '#9ca3af' }}
              tickFormatter={(value) => `${value.toFixed(1)}%`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1a1d29',
                border: '1px solid #2b2f3e',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#9ca3af' }}
              formatter={(value) => [`${value.toFixed(2)}%`, 'Drawdown']}
            />
            <Area
              type="monotone"
              dataKey="drawdown"
              stroke="#ef4444"
              strokeWidth={2}
              fill="url(#drawdownGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Trades Table */}
      {trades && trades.length > 0 && (
        <div className="bg-theme-card rounded-lg p-6 border border-theme-border">
          <h3 className="text-lg font-semibold mb-4">İşlem Geçmişi</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-dark-border">
                  <th className="text-left py-2 px-3 text-gray-400">Tarih</th>
                  <th className="text-left py-2 px-3 text-gray-400">Tip</th>
                  <th className="text-right py-2 px-3 text-gray-400">Fiyat</th>
                  <th className="text-right py-2 px-3 text-gray-400">Miktar</th>
                  <th className="text-right py-2 px-3 text-gray-400">Kâr/Zarar</th>
                  <th className="text-right py-2 px-3 text-gray-400">%</th>
                </tr>
              </thead>
              <tbody>
                {trades.slice(0, 10).map((trade, idx) => (
                  <tr key={idx} className="border-b border-theme-border/50 hover:bg-theme-bg/50">
                    <td className="py-2 px-3 text-gray-300">
                      {new Date(trade.entry_date).toLocaleDateString('tr-TR')}
                    </td>
                    <td className="py-2 px-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        trade.type === 'BUY' 
                          ? 'bg-green-500/20 text-green-400' 
                          : 'bg-red-500/20 text-red-400'
                      }`}>
                        {trade.type}
                      </span>
                    </td>
                    <td className="text-right py-2 px-3 text-gray-300">
                      {formatCurrency(trade.entry_price)}
                    </td>
                    <td className="text-right py-2 px-3 text-gray-300">
                      {trade.quantity}
                    </td>
                    <td className={`text-right py-2 px-3 font-medium ${
                      trade.profit >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {formatCurrency(trade.profit)}
                    </td>
                    <td className={`text-right py-2 px-3 font-medium ${
                      trade.profit_pct >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {formatPercent(trade.profit_pct)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {trades.length > 10 && (
              <p className="text-sm text-gray-400 mt-4 text-center">
                İlk 10 işlem gösteriliyor (Toplam: {trades.length})
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default BacktestResults;
