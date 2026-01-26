/**
 * Mobile Daily Picks Page
 * 📱 Compact view for daily stock picks
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Flame,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Target,
  Shield,
  ChevronDown,
  ChevronUp,
  Star,
  Activity,
  AlertTriangle,
} from 'lucide-react';
import { usePortfolioStore } from '../../store/portfolioStore';

const MobileDailyPicksPage = () => {
  const [morningPicks, setMorningPicks] = useState(null);
  const [dayTradeStatus, setDayTradeStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showPicks, setShowPicks] = useState(true);
  const [showStats, setShowStats] = useState(true);
  const { watchlist, addToWatchlist, removeFromWatchlist } = usePortfolioStore();

  const fetchMorningPicks = async () => {
    try {
      setLoading(true);
      // Hybrid Strategy Endpoint - Desktop ile senkronize
      const response = await axios.get(
        `/api/signals/daily-picks?strategy=hybrid&max_picks=5`
      );
      
      const picks = response.data.picks || [];
      const formattedPicks = picks.map(p => ({
        ticker: p.ticker,
        price: p.entry_price,
        score: Math.round(p.strength),
        recommendation: p.signal,
        signal: p.signal,
        reasons: p.reasons || [],
        sector: p.sector || 'BIST30',
        exitStrategy: p.exit_strategy || {
          tp1_action: "TP1'de %50 pozisyon kapat",
          tp1_new_stop: "Break-even'a çek",
          tp2_action: "TP2'de kalan %50 kapat"
        },
        levels: {
            entry_price: p.entry_price,
            stop_loss: p.stop_loss,
            take_profit: p.take_profit_1, // TP1 
            take_profit_1: p.take_profit_1,
            take_profit_2: p.take_profit_2,
            risk_reward_ratio: p.risk_reward_ratio || 2.5,
            risk_reward_2: p.risk_reward_2 || 4.0,
            risk_pct: p.risk_pct || Math.abs((p.entry_price - p.stop_loss) / p.entry_price * 100),
            reward_pct: p.reward_pct || Math.abs((p.take_profit_1 - p.entry_price) / p.entry_price * 100),
            reward_pct_2: p.take_profit_2 ? Math.abs((p.take_profit_2 - p.entry_price) / p.entry_price * 100) : 0,
            max_hold_days: 5,
        }
      }));

      // Mock summary stats if missing
      const summary = {
          total_picks: formattedPicks.length,
          avg_score: Math.round(formattedPicks.reduce((acc, curr) => acc + curr.score, 0) / (formattedPicks.length || 1)),
          avg_risk_pct: (formattedPicks.reduce((acc, curr) => acc + curr.levels.risk_pct, 0) / (formattedPicks.length || 1)).toFixed(2),
          avg_reward_pct: (formattedPicks.reduce((acc, curr) => acc + curr.levels.reward_pct, 0) / (formattedPicks.length || 1)).toFixed(2)
      };

      setMorningPicks({ 
          success: true, 
          picks: formattedPicks,
          summary: summary 
      });
      
      try {
           const statusRes = await axios.get('/api/screener/day-trade-status');
           setDayTradeStatus(statusRes.data);
      } catch (err) {
           console.log("Status fetch failed", err);
      }

    } catch (error) {
      console.error('Error fetching morning picks:', error);
      setMorningPicks({ success: false, message: 'Veri yüklenemedi' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMorningPicks();
  }, []);

  const isInWatchlist = (ticker) => Array.isArray(watchlist) && watchlist.includes(ticker);

  const toggleWatchlist = (ticker) => {
    if (isInWatchlist(ticker)) {
      removeFromWatchlist(ticker);
    } else {
      addToWatchlist(ticker);
    }
  };

  const getPhaseColor = (color) => {
    const colors = {
      green: 'bg-success/20 border-success text-success',
      red: 'bg-danger/20 border-danger text-danger',
      blue: 'bg-primary/20 border-primary text-primary',
      orange: 'bg-warning/20 border-warning text-warning',
    };
    return colors[color] || 'bg-gray-500/20 border-gray-500 text-gray-400';
  };

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
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-warning/10 flex items-center justify-center">
            <Flame className="w-4 h-4 text-warning" />
          </div>
          <div>
            <h1 className="font-bold text-theme-text text-base">Günün Fırsatları</h1>
            <p className="text-xs text-theme-muted">WR: %58.5 | PF: 1.66 | Hybrid V4</p>
          </div>
        </div>
        <button
          onClick={fetchMorningPicks}
          disabled={loading}
          className="p-2 bg-primary-500 rounded-lg"
        >
          <RefreshCw className={`w-4 h-4 text-white ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Market Status */}
      {dayTradeStatus && (
        <div className={`p-3 rounded-lg border ${getPhaseColor(dayTradeStatus.color)}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4" />
              <span className="font-bold text-sm">{dayTradeStatus.action}</span>
            </div>
            <div className="text-xs">
              Alım: <span className="font-bold">{dayTradeStatus.buy_window}</span>
            </div>
          </div>
        </div>
      )}

      {/* Stats Summary - Collapsible */}
      {morningPicks?.success && morningPicks.summary && (
        <div className="card">
          <ToggleHeader
            title="Özet İstatistikler"
            icon={Target}
            isOpen={showStats}
            onToggle={() => setShowStats(!showStats)}
            color="text-success"
          />
          {showStats && (
            <div className="grid grid-cols-4 gap-2 p-3">
              <div className="text-center">
                <p className="text-lg font-bold text-primary">{morningPicks.summary.total_picks}</p>
                <p className="text-[9px] text-theme-muted">Öneri</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-success">{morningPicks.summary.avg_score}</p>
                <p className="text-[9px] text-theme-muted">Ort. Skor</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-danger">%{morningPicks.summary.avg_risk_pct || 0}</p>
                <p className="text-[9px] text-theme-muted">Risk</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-bold text-success">%{morningPicks.summary.avg_reward_pct || 0}</p>
                <p className="text-[9px] text-theme-muted">Hedef</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Picks List - Collapsible */}
      <div className="card">
        <ToggleHeader
          title="Hisse Önerileri"
          icon={Flame}
          isOpen={showPicks}
          onToggle={() => setShowPicks(!showPicks)}
          badge={morningPicks?.picks?.length || 0}
          color="text-warning"
        />
        {showPicks && (
          <div className="divide-y divide-[var(--glass-border)]">
            {loading ? (
              <div className="p-6 text-center">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto text-primary mb-2" />
                <p className="text-sm text-theme-muted">Yükleniyor...</p>
              </div>
            ) : !morningPicks?.success ? (
              <div className="p-6 text-center">
                <AlertTriangle className="w-6 h-6 text-warning mx-auto mb-2" />
                <p className="text-sm text-theme-text">{morningPicks?.message || 'Veri bulunamadı'}</p>
              </div>
            ) : (
              morningPicks.picks?.map((pick, i) => (
                <div key={i} className="p-3">
                  {/* Header - Ticker, Signal, Star */}
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-primary-500/20 flex items-center justify-center text-xs font-bold text-primary">
                        {i + 1}
                      </span>
                      <span className="font-bold text-theme-text">{pick.ticker?.replace('.IS', '')}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded ${
                        pick.recommendation === 'BUY' || pick.signal === 'BUY' 
                          ? 'bg-success/20 text-success' 
                          : 'bg-danger/20 text-danger'
                      }`}>
                        {pick.recommendation === 'BUY' || pick.signal === 'BUY' ? 'AL' : 'SAT'}
                      </span>
                    </div>
                    <button
                      onClick={() => toggleWatchlist(pick.ticker)}
                      className={`p-1.5 rounded-lg transition-colors ${
                        isInWatchlist(pick.ticker) ? 'bg-warning/20 text-warning' : 'bg-theme-card text-theme-muted'
                      }`}
                    >
                      <Star className={`w-3.5 h-3.5 ${isInWatchlist(pick.ticker) ? 'fill-current' : ''}`} />
                    </button>
                  </div>
                  
                  {/* Current Price */}
                  <div className="flex items-center justify-between mb-2 px-2 py-1.5 rounded-lg bg-primary-500/10">
                    <span className="text-xs text-theme-muted">Anlık Fiyat</span>
                    <span className="font-bold text-primary">₺{pick.price?.toFixed(2) || '—'}</span>
                  </div>
                  
                  {/* Score Only - Centered */}
                  <div className="text-center mb-2">
                    <span className="text-[10px] text-theme-muted">Skor</span>
                    <p className={`text-xl font-bold ${pick.score >= 70 ? 'text-success' : pick.score >= 50 ? 'text-warning' : 'text-danger'}`}>
                      {pick.score}
                    </p>
                  </div>

                  {/* Risk/Reward Info from pick.levels */}
                  <div className="grid grid-cols-2 gap-2 text-xs mb-2">
                    <div className="text-center p-1.5 rounded bg-success/10">
                      <p className="text-theme-muted">Hedef</p>
                      <p className="font-bold text-success">
                        +%{(pick.levels?.reward_pct || pick.levels?.reward_pct_1)?.toFixed(2) || '—'}
                      </p>
                    </div>
                    <div className="text-center p-1.5 rounded bg-danger/10">
                      <p className="text-theme-muted">Risk</p>
                      <p className="font-bold text-danger">
                        -%{pick.levels?.risk_pct?.toFixed(2) || '—'}
                      </p>
                    </div>
                  </div>

                  {/* Entry, Target, Stop Prices from pick.levels */}
                  <div className="grid grid-cols-3 gap-1 text-xs">
                    <div className="text-center p-2 rounded bg-theme-card/30 border border-[var(--glass-border)]">
                      <p className="text-[10px] text-theme-muted uppercase">Giriş</p>
                      <p className="font-bold text-theme-text">
                        ₺{pick.levels?.entry_price?.toFixed(2) || pick.price?.toFixed(2) || '—'}
                      </p>
                    </div>
                    <div className="text-center p-2 rounded bg-success/10 border border-success/20">
                      <p className="text-[10px] text-theme-muted uppercase">TP1</p>
                      <p className="font-bold text-success">
                        ₺{(pick.levels?.take_profit_1 || pick.levels?.take_profit)?.toFixed(2) || '—'}
                      </p>
                    </div>
                    <div className="text-center p-2 rounded bg-danger/10 border border-danger/20">
                      <p className="text-[10px] text-theme-muted uppercase">Stop</p>
                      <p className="font-bold text-danger">
                        ₺{pick.levels?.stop_loss?.toFixed(2) || '—'}
                      </p>
                    </div>
                  </div>

                  {/* TP2 Hedefi */}
                  {pick.levels?.take_profit_2 && (
                    <div className="mt-2 p-2 rounded bg-primary-500/10 border border-primary-500/20">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-theme-muted">TP2 Hedef</span>
                        <span className="font-bold text-primary">
                          ₺{pick.levels.take_profit_2?.toFixed(2)} (+%{pick.levels.reward_pct_2?.toFixed(1)})
                        </span>
                      </div>
                    </div>
                  )}

                  {/* R:R Ratio */}
                  <div className="flex items-center justify-center gap-2 mt-2 text-xs">
                    {pick.levels?.risk_reward_ratio && (
                      <span className="px-2 py-1 rounded bg-primary-500/10 text-primary font-medium">
                        TP1 R:R 1:{pick.levels.risk_reward_ratio?.toFixed(1)}
                      </span>
                    )}
                    {pick.levels?.risk_reward_2 && (
                      <span className="px-2 py-1 rounded bg-success/10 text-success font-medium">
                        TP2 R:R 1:{pick.levels.risk_reward_2?.toFixed(1)}
                      </span>
                    )}
                  </div>

                  {/* Exit Strategy */}
                  {pick.exitStrategy && (
                    <div className="mt-2 p-2 rounded bg-theme-card/50 border border-[var(--glass-border)]">
                      <p className="text-[10px] text-theme-muted mb-1 font-semibold">📋 Çıkış Stratejisi</p>
                      <div className="space-y-0.5 text-[10px]">
                        <p className="text-success">✓ {pick.exitStrategy.tp1_action}</p>
                        <p className="text-primary">✓ {pick.exitStrategy.tp1_new_stop}</p>
                        <p className="text-warning">✓ {pick.exitStrategy.tp2_action}</p>
                      </div>
                    </div>
                  )}

                  {/* Reasons/Signals */}
                  {pick.reasons && pick.reasons.length > 0 && (
                    <div className="mt-2 p-2 rounded bg-theme-card/30">
                      <p className="text-[10px] text-theme-muted mb-1 font-semibold">📊 Sinyal Nedenleri</p>
                      <div className="flex flex-wrap gap-1">
                        {pick.reasons.slice(0, 3).map((reason, idx) => (
                          <span key={idx} className="text-[9px] px-1.5 py-0.5 rounded bg-primary-500/10 text-primary-400">
                            {reason}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Max Hold Days */}
                  <div className="flex items-center justify-center mt-2">
                    <span className="text-[10px] text-theme-muted">
                      ⏱️ Max tutma: {pick.levels?.max_hold_days || 5} gün
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Market Trend */}
      {morningPicks?.market_trend && (
        <div className={`card p-3 ${morningPicks.market_trend === 'YUKSELIS' ? 'border-success/30' : 'border-danger/30'}`}>
          <div className="flex items-center gap-2">
            {morningPicks.market_trend === 'YUKSELIS' ? (
              <TrendingUp className="w-5 h-5 text-success" />
            ) : (
              <TrendingDown className="w-5 h-5 text-danger" />
            )}
            <div>
              <p className={`font-bold ${morningPicks.market_trend === 'YUKSELIS' ? 'text-success' : 'text-danger'}`}>
                BIST100 {morningPicks.market_trend === 'YUKSELIS' ? 'YÜKSELİŞ' : 'DÜŞÜŞ'}
              </p>
              <p className="text-xs text-theme-muted">Piyasa Trendi</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MobileDailyPicksPage;
