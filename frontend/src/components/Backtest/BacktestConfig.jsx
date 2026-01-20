/**
 * Backtest Configuration Component
 * Form for setting up backtest parameters
 */
import React, { useState } from 'react';
import { Play, Calendar, DollarSign, TrendingUp } from 'lucide-react';
import { useBacktest } from '../../hooks/useBacktest';
import { useStore } from '../../store';
import LoadingSpinner from '../Common/LoadingSpinner';

const BacktestConfig = () => {
  const { selectedTicker, strategy } = useStore();
  const { runBacktest, isLoading, error } = useBacktest();

  const [config, setConfig] = useState({
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    initialCapital: 100000,
    commission: 0.001,
    stopLossPct: 3.0,
    takeProfitPct: 5.0,
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    runBacktest({
      ticker: selectedTicker,
      start_date: config.startDate,
      end_date: config.endDate,
      initial_capital: config.initialCapital,
      strategy: strategy,
      commission: config.commission,
      stop_loss_pct: config.stopLossPct,
      take_profit_pct: config.takeProfitPct,
    });
  };

  const handleChange = (field, value) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="bg-theme-card rounded-lg p-6 border border-theme-border">
      <h2 className="text-xl font-semibold mb-4">Backtest Ayarları</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Date Range */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-theme-muted mb-2">
              <Calendar className="inline w-4 h-4 mr-1" />
              Başlangıç Tarihi
            </label>
            <input
              type="date"
              value={config.startDate}
              onChange={(e) => handleChange('startDate', e.target.value)}
              className="w-full bg-theme-bg border border-theme-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-theme-muted mb-2">
              <Calendar className="inline w-4 h-4 mr-1" />
              Bitiş Tarihi
            </label>
            <input
              type="date"
              value={config.endDate}
              onChange={(e) => handleChange('endDate', e.target.value)}
              className="w-full bg-theme-bg border border-theme-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
              required
            />
          </div>
        </div>

        {/* Initial Capital */}
        <div>
          <label className="block text-sm text-gray-400 mb-2">
            <DollarSign className="inline w-4 h-4 mr-1" />
            Başlangıç Sermayesi (₺)
          </label>
          <input
            type="number"
            value={config.initialCapital}
            onChange={(e) => handleChange('initialCapital', parseFloat(e.target.value))}
            min="1000"
            step="1000"
            className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
            required
          />
        </div>

        {/* Risk Management */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-theme-muted mb-2">
              <TrendingUp className="inline w-4 h-4 mr-1" />
              Stop Loss (%)
            </label>
            <input
              type="number"
              value={config.stopLossPct}
              onChange={(e) => handleChange('stopLossPct', parseFloat(e.target.value))}
              min="0.1"
              max="20"
              step="0.1"
              className="w-full bg-theme-bg border border-theme-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-theme-muted mb-2">
              <TrendingUp className="inline w-4 h-4 mr-1" />
              Take Profit (%)
            </label>
            <input
              type="number"
              value={config.takeProfitPct}
              onChange={(e) => handleChange('takeProfitPct', parseFloat(e.target.value))}
              min="0.1"
              max="50"
              step="0.1"
              className="w-full bg-theme-bg border border-theme-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
              required
            />
          </div>
        </div>

        {/* Commission */}
        <div>
          <label className="block text-sm text-gray-400 mb-2">
            Komisyon Oranı
          </label>
          <input
            type="number"
            value={config.commission}
            onChange={(e) => handleChange('commission', parseFloat(e.target.value))}
            min="0"
            max="0.01"
            step="0.0001"
            className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Örnek: 0.001 = %0.1
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/10 border border-red-500 rounded-lg p-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Backtest Çalıştırılıyor...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              Backtest Başlat
            </>
          )}
        </button>

        <p className="text-xs text-gray-500 text-center">
          Mevcut Hisse: <span className="text-primary-400">{selectedTicker}</span> • 
          Strateji: <span className="text-primary-400 capitalize">{strategy}</span>
        </p>
      </form>
    </div>
  );
};

export default BacktestConfig;
