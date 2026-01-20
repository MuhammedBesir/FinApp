/**
 * Mobile IPO Page - Halka Arz Sayfası
 * 📱 Compact, mobile-optimized view
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Rocket,
  Calendar,
  TrendingUp,
  TrendingDown,
  Clock,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Star,
  Building2,
  ArrowRight,
} from 'lucide-react';

const API_URL = '/api';

const statusLabels = {
  upcoming: 'Yaklaşan',
  active: 'Talep Toplama',
  completed: 'Tamamlandı',
  trading: 'İşlem Görüyor',
  cancelled: 'İptal',
};

const MobileIPOPage = () => {
  const [ipos, setIpos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showActive, setShowActive] = useState(true);
  const [showPast, setShowPast] = useState(true);
  const [selectedIPO, setSelectedIPO] = useState(null);
  const [watchlist, setWatchlist] = useState([]);
  const userId = 'demo_user_123';

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/ipo/`);
      const data = await res.json();
      if (data.success) setIpos(data.ipos);
    } catch (error) {
      console.error('Error fetching IPO data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const refreshData = async () => {
    setRefreshing(true);
    try {
      await fetch(`${API_URL}/ipo/admin/refresh`, { method: 'POST' });
      await fetchData();
    } catch (error) {
      console.error('Error refreshing:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('tr-TR', {
      day: 'numeric',
      month: 'short',
    });
  };

  const getIPOStatus = (ipo) => {
    const now = new Date();
    const demandStart = ipo.demand_start ? new Date(ipo.demand_start) : null;
    const demandEnd = ipo.demand_end ? new Date(ipo.demand_end) : null;
    const tradingStart = ipo.trading_start ? new Date(ipo.trading_start) : null;

    if (ipo.status === 'trading' || (tradingStart && tradingStart <= now)) {
      return { label: 'İşlem Görüyor', color: 'bg-purple-500/20 text-purple-400' };
    }
    if (demandEnd && demandEnd < now && (!tradingStart || tradingStart > now)) {
      return { label: 'Talep Tamamlandı', color: 'bg-warning/20 text-warning' };
    }
    if (demandStart && demandEnd && demandStart <= now && demandEnd >= now) {
      return { label: 'Talep Devam', color: 'bg-success/20 text-success' };
    }
    if (demandStart && demandStart > now) {
      return { label: 'Yaklaşan', color: 'bg-primary-500/20 text-primary-400' };
    }
    return { label: statusLabels[ipo.status] || 'Bilinmiyor', color: 'bg-theme-card text-theme-muted' };
  };

  const activeIPOs = ipos.filter((ipo) => {
    if (ipo.status === 'trading') return false;
    if (ipo.trading_start) {
      const tradingStart = new Date(ipo.trading_start);
      if (tradingStart <= new Date()) return false;
    }
    return true;
  });

  const pastIPOs = ipos.filter((ipo) => {
    if (ipo.status === 'trading') return true;
    if (ipo.trading_start) {
      const tradingStart = new Date(ipo.trading_start);
      if (tradingStart <= new Date()) return true;
    }
    return false;
  });

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

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-3 pb-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary-500/10 flex items-center justify-center">
            <Rocket className="w-4 h-4 text-primary-400" />
          </div>
          <div>
            <h1 className="font-bold text-theme-text text-base">Halka Arz</h1>
            <p className="text-xs text-theme-muted">{ipos.length} halka arz</p>
          </div>
        </div>
        <button
          onClick={refreshData}
          disabled={refreshing}
          className="p-2 bg-primary-500 rounded-lg"
        >
          <RefreshCw className={`w-4 h-4 text-white ${refreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Active IPOs - Collapsible */}
      <div className="card">
        <ToggleHeader
          title="Aktif Halka Arzlar"
          icon={Rocket}
          isOpen={showActive}
          onToggle={() => setShowActive(!showActive)}
          badge={activeIPOs.length}
          color="text-success"
        />
        {showActive && (
          <div className="divide-y divide-[var(--glass-border)]">
            {activeIPOs.length > 0 ? (
              activeIPOs.map((ipo) => {
                const status = getIPOStatus(ipo);
                return (
                  <div key={ipo.id} className="p-3">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center text-white font-bold text-xs">
                          {ipo.symbol?.substring(0, 2)}
                        </div>
                        <div>
                          <p className="font-bold text-theme-text text-sm">{ipo.symbol}</p>
                          <p className="text-[10px] text-theme-muted truncate max-w-[120px]">{ipo.name}</p>
                        </div>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${status.color}`}>
                        {status.label}
                      </span>
                    </div>

                    {/* Info Grid */}
                    <div className="grid grid-cols-2 gap-2 text-xs mb-2">
                      <div className="p-2 rounded bg-theme-card/50">
                        <p className="text-theme-muted">Fiyat</p>
                        <p className="font-bold text-theme-text">
                          ₺{ipo.final_price?.toFixed(2) || `${ipo.price_range_min?.toFixed(2) || '?'} - ${ipo.price_range_max?.toFixed(2) || '?'}`}
                        </p>
                      </div>
                      <div className="p-2 rounded bg-theme-card/50">
                        <p className="text-theme-muted">Tarih</p>
                        <p className="font-bold text-theme-text">
                          {formatDate(ipo.demand_start)} - {formatDate(ipo.demand_end)}
                        </p>
                      </div>
                    </div>

                    {/* Extra Info */}
                    <div className="flex items-center justify-between text-xs text-theme-muted">
                      <span>Lot: {ipo.lot_size?.toLocaleString('tr-TR') || '-'}</span>
                      <span>{ipo.distribution_method || 'Eşit Dağıtım'}</span>
                    </div>

                    {/* Detail Button */}
                    <button
                      onClick={() => setSelectedIPO(ipo)}
                      className="w-full mt-2 py-2 bg-success/10 text-success rounded-lg text-xs font-medium flex items-center justify-center gap-1"
                    >
                      Detay <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                );
              })
            ) : (
              <div className="p-6 text-center">
                <Rocket className="w-6 h-6 text-theme-muted mx-auto mb-2" />
                <p className="text-sm text-theme-muted">Aktif halka arz yok</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Past IPOs - Collapsible */}
      <div className="card">
        <ToggleHeader
          title="Geçmiş Halka Arzlar"
          icon={Clock}
          isOpen={showPast}
          onToggle={() => setShowPast(!showPast)}
          badge={pastIPOs.length}
          color="text-purple-400"
        />
        {showPast && (
          <div className="divide-y divide-[var(--glass-border)]">
            {pastIPOs.slice(0, 10).map((ipo) => (
              <div key={ipo.id} className="p-3 flex items-center justify-between">
                <div className="flex items-center gap-2 min-w-0">
                  <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center text-white font-bold text-[10px] flex-shrink-0">
                    {ipo.symbol?.substring(0, 2)}
                  </div>
                  <div className="min-w-0">
                    <p className="font-bold text-theme-text text-sm">{ipo.symbol}</p>
                    <p className="text-[10px] text-theme-muted">{formatDate(ipo.trading_start)}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-bold text-theme-text text-sm">₺{ipo.current_price?.toFixed(2) || '-'}</p>
                  {ipo.total_return_percent != null && (
                    <p className={`text-xs font-medium ${ipo.total_return_percent >= 0 ? 'text-success' : 'text-danger'}`}>
                      {ipo.total_return_percent >= 0 ? '+' : ''}{ipo.total_return_percent.toFixed(1)}%
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedIPO && (
        <div className="fixed inset-0 bg-black/70 flex items-end justify-center z-50" onClick={() => setSelectedIPO(null)}>
          <div 
            className="bg-theme-card w-full max-h-[85vh] rounded-t-2xl overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="sticky top-0 bg-theme-card p-4 border-b border-[var(--glass-border)]">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center text-white font-bold">
                    {selectedIPO.symbol?.substring(0, 2)}
                  </div>
                  <div>
                    <p className="font-bold text-theme-text">{selectedIPO.symbol}</p>
                    <p className="text-xs text-theme-muted">{selectedIPO.name}</p>
                  </div>
                </div>
                <button 
                  onClick={() => setSelectedIPO(null)}
                  className="p-2 bg-theme-card rounded-lg text-theme-muted"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-4 space-y-4">
              {/* Price Info */}
              <div className="grid grid-cols-2 gap-2">
                <div className="p-3 rounded-lg bg-theme-card/50 border border-[var(--glass-border)]">
                  <p className="text-xs text-theme-muted">Halka Arz Fiyatı</p>
                  <p className="font-bold text-theme-text">
                    ₺{selectedIPO.final_price?.toFixed(2) || selectedIPO.price_range_min?.toFixed(2) || '-'}
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-theme-card/50 border border-[var(--glass-border)]">
                  <p className="text-xs text-theme-muted">Güncel Fiyat</p>
                  <p className="font-bold text-theme-text">
                    {selectedIPO.current_price ? `₺${selectedIPO.current_price.toFixed(2)}` : 'Bekliyor'}
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-theme-card/50 border border-[var(--glass-border)]">
                  <p className="text-xs text-theme-muted">Günlük Değişim</p>
                  <p className={`font-bold ${(selectedIPO.daily_change_percent || 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                    {selectedIPO.daily_change_percent != null 
                      ? `${selectedIPO.daily_change_percent >= 0 ? '+' : ''}${selectedIPO.daily_change_percent.toFixed(2)}%` 
                      : '-'}
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-theme-card/50 border border-[var(--glass-border)]">
                  <p className="text-xs text-theme-muted">Toplam Getiri</p>
                  <p className={`font-bold ${(selectedIPO.total_return_percent || 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                    {selectedIPO.total_return_percent != null 
                      ? `${selectedIPO.total_return_percent >= 0 ? '+' : ''}${selectedIPO.total_return_percent.toFixed(1)}%` 
                      : '-'}
                  </p>
                </div>
              </div>

              {/* General Info */}
              <div className="space-y-2">
                <div className="flex justify-between py-2 border-b border-[var(--glass-border)] text-sm">
                  <span className="text-theme-muted">Sektör</span>
                  <span className="text-theme-text font-medium">{selectedIPO.sector || '-'}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-[var(--glass-border)] text-sm">
                  <span className="text-theme-muted">Dağıtım</span>
                  <span className="text-theme-text font-medium">{selectedIPO.distribution_method || '-'}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-[var(--glass-border)] text-sm">
                  <span className="text-theme-muted">Lot Adedi</span>
                  <span className="text-theme-text font-medium">{selectedIPO.lot_size?.toLocaleString('tr-TR') || '-'}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-[var(--glass-border)] text-sm">
                  <span className="text-theme-muted">Aracı Kurum</span>
                  <span className="text-theme-text font-medium">{selectedIPO.lead_manager || '-'}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-[var(--glass-border)] text-sm">
                  <span className="text-theme-muted">Talep Tarihi</span>
                  <span className="text-theme-text font-medium">
                    {formatDate(selectedIPO.demand_start)} - {formatDate(selectedIPO.demand_end)}
                  </span>
                </div>
                <div className="flex justify-between py-2 text-sm">
                  <span className="text-theme-muted">İşlem Başlangıç</span>
                  <span className="text-theme-text font-medium">{formatDate(selectedIPO.trading_start) || 'Bekliyor'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MobileIPOPage;
