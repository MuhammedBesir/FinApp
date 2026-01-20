/**
 * Advanced Stock Pick Card - Gelişmiş Hisse Kartı
 * 📊 Detaylı analiz | 🎯 TP1 & TP2 | 🛡️ Risk yönetimi | ⚡ Tek tıkla işlem
 */
import React, { useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Target,
  Shield,
  Activity,
  ChevronDown,
  ChevronUp,
  Plus,
  BarChart3,
  AlertCircle,
  CheckCircle2,
  Clock,
  Zap,
  Star
} from 'lucide-react';
import { usePortfolioStore } from '../../store/portfolioStore';

const StockPickCard = ({ pick, rank, inWatchlist, onToggleWatchlist }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const { addTrade } = usePortfolioStore();
  const [isAdding, setIsAdding] = useState(false);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const getRankBadgeColor = (rank) => {
    if (rank === 1) return 'bg-warning text-white';
    if (rank === 2) return 'bg-gray-400 text-white';
    if (rank === 3) return 'bg-orange-600 text-white';
    return 'bg-theme-card text-theme-muted';
  };

  const getQualityColor = (quality) => {
    const colors = {
      'Excellent': 'text-success',
      'Good': 'text-primary-400',
      'Fair': 'text-warning',
      'Poor': 'text-danger'
    };
    return colors[quality] || 'text-theme-muted';
  };

  const handleAddToPortfolio = async () => {
    setIsAdding(true);
    try {
      const trade = {
        ticker: pick.ticker,
        type: 'buy',
        price: pick.price,
        quantity: 100, // Default quantity
        stopLoss: pick.levels.stop_loss,
        takeProfit: pick.levels.take_profit_1,
        takeProfitTP2: pick.levels.take_profit_2,
        strategy: 'V2_Enhanced',
        status: 'open'
      };
      
      await addTrade(trade);
      
      // Success notification
      alert(`${pick.ticker} başarıyla portföye eklendi!`);
    } catch (error) {
      console.error('Error adding trade:', error);
      alert('İşlem eklenirken bir hata oluştu.');
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <div className="card hover:shadow-lg transition-all duration-300">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          {/* Rank Badge */}
          <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg ${getRankBadgeColor(rank)}`}>
            {rank}
          </div>
          
          {/* Stock Info */}
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-xl font-bold text-theme-text">
                {pick.ticker.replace('.IS', '')}
              </h3>
              <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                pick.momentum === 'very_strong' ? 'bg-success/20 text-success' :
                pick.momentum === 'strong' ? 'bg-primary-500/20 text-primary-400' :
                'bg-theme-card text-theme-muted'
              }`}>
                {pick.momentum === 'very_strong' ? '🔥 Çok Güçlü' :
                 pick.momentum === 'strong' ? '⚡ Güçlü' : '📊 Orta'}
              </span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <span className="text-theme-muted">{pick.sector}</span>
              <span className="text-theme-muted">•</span>
              <span className={getQualityColor(pick.setup_quality)}>
                {pick.setup_quality}
              </span>
            </div>
          </div>
        </div>

        {/* Score Badge - Skor ve Momentum yan yana */}
        <div className="flex items-center gap-3">
          <div className="text-center">
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary-500/10">
              <BarChart3 className="w-4 h-4 text-primary-400" />
              <span className="font-bold text-primary-400 text-lg">{pick.score}</span>
            </div>
            <p className="text-xs text-theme-muted mt-1">Skor</p>
          </div>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              e.preventDefault();
              onToggleWatchlist?.(e, pick.ticker);
            }}
            className={`p-2.5 rounded-xl border-2 transition-all hover:scale-105 active:scale-95 shadow-sm ${
              inWatchlist
                ? 'bg-gradient-to-br from-warning via-warning to-orange-500 text-white border-white/30'
                : 'bg-theme-card text-theme-muted hover:text-warning hover:border-warning/60 border-[var(--color-border)]'
            }`}
            title={inWatchlist ? 'Portföyden çıkar' : 'Portföye ekle'}
          >
            <Star className={`w-4 h-4 ${inWatchlist ? 'fill-current' : ''}`} />
          </button>
        </div>
      </div>

      {/* Price Info */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="p-3 rounded-xl bg-theme-card">
          <p className="text-xs text-theme-muted mb-1">Anlık Fiyat</p>
          <p className="text-2xl font-bold text-theme-text">
            {formatCurrency(pick.price)}
          </p>
          <p className={`text-sm font-medium mt-1 ${
            pick.change_percent >= 0 ? 'text-success' : 'text-danger'
          }`}>
            {pick.change_percent >= 0 ? '+' : ''}{pick.change_percent.toFixed(2)}%
          </p>
        </div>

        <div className="p-3 rounded-xl bg-theme-card">
          <p className="text-xs text-theme-muted mb-1">Volatilite</p>
          <p className="text-xl font-bold text-theme-text">
            {pick.levels.volatility_class}
          </p>
          <p className="text-xs text-theme-muted mt-1">
            ATR: {pick.atr?.toFixed(2)} ({pick.levels.atr_percent?.toFixed(2)}%)
          </p>
        </div>
      </div>

      {/* Trade Levels - V2 ENHANCED */}
      <div className="space-y-3 mb-4">
        {/* Entry + SL */}
        <div className="grid grid-cols-2 gap-2">
          <div className="p-3 rounded-xl bg-primary-500/10 border border-primary-500/30">
            <div className="flex items-center gap-2 mb-1">
              <Target className="w-4 h-4 text-primary-400" />
              <p className="text-xs text-primary-400 font-semibold">GİRİŞ</p>
            </div>
            <p className="text-lg font-bold text-theme-text">
              {formatCurrency(pick.levels.entry_price)}
            </p>
          </div>

          <div className="p-3 rounded-xl bg-danger/10 border border-danger/30">
            <div className="flex items-center gap-2 mb-1">
              <Shield className="w-4 h-4 text-danger" />
              <p className="text-xs text-danger font-semibold">STOP-LOSS</p>
            </div>
            <p className="text-lg font-bold text-theme-text">
              {formatCurrency(pick.levels.stop_loss)}
            </p>
            <p className="text-xs text-danger mt-1">
              -{pick.levels.risk_pct?.toFixed(2)}%
            </p>
          </div>
        </div>

        {/* TP1 & TP2 - Partial Exit */}
        {pick.levels.take_profit_2 ? (
          <>
            <div className="flex items-center gap-2 px-2 py-1 rounded-lg bg-success/10">
              <Zap className="w-4 h-4 text-success" />
              <span className="text-xs font-semibold text-success">
                Partial Exit Stratejisi (TP1: %50 | TP2: %50)
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="p-3 rounded-xl bg-success/10 border border-success/30">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs text-success font-semibold">HEDEF 1 (50%)</p>
                  <span className="text-xs text-theme-muted">1:2.5</span>
                </div>
                <p className="text-lg font-bold text-theme-text">
                  {formatCurrency(pick.levels.take_profit_1)}
                </p>
                <p className="text-xs text-success mt-1">
                  +{pick.levels.reward_pct_1?.toFixed(2)}%
                </p>
              </div>

              <div className="p-3 rounded-xl bg-success/10 border border-success/30">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs text-success font-semibold">HEDEF 2 (50%)</p>
                  <span className="text-xs text-theme-muted">1:4.0</span>
                </div>
                <p className="text-lg font-bold text-theme-text">
                  {formatCurrency(pick.levels.take_profit_2)}
                </p>
                <p className="text-xs text-success mt-1">
                  +{pick.levels.reward_pct_2?.toFixed(2)}%
                </p>
              </div>
            </div>
          </>
        ) : (
          <div className="p-3 rounded-xl bg-success/10 border border-success/30">
            <div className="flex items-center gap-2 mb-1">
              <Target className="w-4 h-4 text-success" />
              <p className="text-xs text-success font-semibold">HEDEF</p>
            </div>
            <p className="text-lg font-bold text-theme-text">
              {formatCurrency(pick.levels.take_profit)}
            </p>
            <p className="text-xs text-success mt-1">
              +{pick.levels.reward_pct?.toFixed(2)}%
            </p>
          </div>
        )}
      </div>

      {/* Risk/Reward Summary */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="p-2 rounded-lg bg-theme-card text-center">
          <p className="text-xs text-theme-muted mb-1">Risk</p>
          <p className="text-sm font-bold text-danger">
            {pick.levels.risk_pct?.toFixed(2)}%
          </p>
        </div>
        <div className="p-2 rounded-lg bg-theme-card text-center">
          <p className="text-xs text-theme-muted mb-1">Reward</p>
          <p className="text-sm font-bold text-success">
            {pick.levels.reward_pct?.toFixed(2)}%
          </p>
        </div>
        <div className="p-2 rounded-lg bg-primary-500/10 text-center">
          <p className="text-xs text-theme-muted mb-1">R:R</p>
          <p className="text-sm font-bold text-primary-400">
            1:{pick.levels.risk_reward_ratio?.toFixed(1)}
          </p>
        </div>
      </div>

      {/* Detay Butonu Köşede */}
      <div className="mt-4">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full btn btn-outline flex items-center justify-center gap-2"
        >
          {isExpanded ? 'Detayları Gizle' : 'Detayları Göster'}
          {isExpanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-[var(--glass-border)] space-y-3 animate-fade-in">
          {/* Technical Details */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs text-theme-muted mb-2">Teknik İndikatörler</p>
              <div className="space-y-1 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-theme-muted">RSI:</span>
                  <span className="text-theme-text font-medium">
                    {pick.details?.rsi_value?.toFixed(2)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-theme-muted">Hacim:</span>
                  <span className="text-theme-text font-medium">
                    {pick.details?.volume_ratio?.toFixed(2)}x
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-theme-muted">MACD:</span>
                  <span className={`font-medium ${
                    pick.details?.macd_signal === 'bullish' ? 'text-success' : 'text-danger'
                  }`}>
                    {pick.details?.macd_signal}
                  </span>
                </div>
              </div>
            </div>

            <div>
              <p className="text-xs text-theme-muted mb-2">Strateji Bilgileri</p>
              <div className="space-y-1 text-sm">
                {pick.reasons && pick.reasons.length > 0 ? (
                  <ul className="space-y-1">
                    {pick.reasons.map((reason, idx) => (
                      <li key={idx} className="text-xs text-theme-text flex items-start gap-1.5">
                        <span className="mt-0.5">•</span>
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-theme-muted">Max Tutma:</span>
                      <span className="text-theme-text font-medium">
                        {pick.levels?.max_hold_days || 1} gün
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-theme-muted">Trend:</span>
                      <span className="text-theme-text font-medium">
                        {pick.details?.trend_status || 'Yükseliş'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-theme-muted">Sinyal:</span>
                      <span className={`font-medium ${
                        pick.recommendation === 'BUY' ? 'text-success' :
                        pick.recommendation === 'WAIT' ? 'text-warning' : 'text-danger'
                      }`}>
                        {pick.recommendation || pick.signal}
                      </span>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Warnings */}
          {pick.recommendation === 'WAIT' && (
            <div className="p-3 rounded-lg bg-warning/10 border border-warning/30">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-warning flex-shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="text-warning font-semibold mb-1">İşlem Zamanı Değil</p>
                  <p className="text-theme-muted text-xs">
                    {pick.market_status?.message} - Piyasa saatleri dışında veya güvenli işlem zamanı değil.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StockPickCard;
