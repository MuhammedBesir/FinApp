/**
 * Mobile Dashboard Component
 * 📱 Mobil-first tasarım, mevcut Dashboard verileriyle
 * Tasarım stili: Kullanıcının referans görselinden
 */
import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  ChevronDown,
  ChevronUp,
  Zap,
  Target,
  Activity,
  BarChart3,
  RefreshCw
} from 'lucide-react';
import { useStore } from '../../store';
import { usePortfolioStore } from '../../store/portfolioStore';
import { useStockData } from '../../hooks/useStockData';
import MiniChart from '../Charts/MiniChart';
import StockChart from '../Charts/StockChart';

const MobileDashboard = () => {
  useStockData();
  
  const {
    selectedTicker,
    stockData,
    stockInfo,
    signal,
    isLoading,
    realtimeData,
    getLatestIndicators,
  } = useStore();

  const { watchlist } = usePortfolioStore();

  const [showChart, setShowChart] = useState(true);
  const [showIndicators, setShowIndicators] = useState(true);
  const [showMarket, setShowMarket] = useState(true);
  const [marketData, setMarketData] = useState(null);

  // Fetch market data
  useEffect(() => {
    const fetchMarket = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/market/all');
        const data = await res.json();
        if (data.success) setMarketData(data.data);
      } catch (e) {
        console.error('Market fetch error:', e);
      }
    };
    fetchMarket();
    const interval = setInterval(fetchMarket, 30000);
    return () => clearInterval(interval);
  }, []);

  const latestData = realtimeData?.price || stockData?.data?.[stockData.data?.length - 1];
  const indicatorData = getLatestIndicators();

  const currentPrice = latestData?.close || stockInfo?.current_price || 0;
  const previousClose = stockInfo?.previous_close || latestData?.open || currentPrice;
  const change = currentPrice - previousClose;
  const changePercent = previousClose ? (change / previousClose) * 100 : 0;
  const isPositive = change >= 0;

  const formatCurrency = (value) => {
    if (!value) return "—";
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const bist100 = marketData?.bist100 || { price: 0, change_percent: 0, is_up: true };

  const currentDate = new Date();
  const dateStr = currentDate.toLocaleDateString('tr-TR', { 
    day: 'numeric', month: 'short', weekday: 'short'
  });
  const timeStr = currentDate.toLocaleTimeString('tr-TR', {
    hour: '2-digit', minute: '2-digit'
  });

  // Toggle header component
  const ToggleHeader = ({ title, icon: Icon, isOpen, onToggle, color = "text-primary-400" }) => (
    <button 
      onClick={onToggle}
      className="w-full flex items-center justify-between p-3 border-b border-[var(--glass-border)]"
    >
      <div className="flex items-center gap-2">
        <Icon className={`w-4 h-4 ${color}`} />
        <span className="font-bold text-theme-text text-sm">{title}</span>
      </div>
      {isOpen ? <ChevronUp className="w-4 h-4 text-theme-muted" /> : <ChevronDown className="w-4 h-4 text-theme-muted" />}
    </button>
  );

  return (
    <div className="space-y-3 pb-6">
      {/* Piyasa Durumu - Collapsible */}
      <div className="card">
        <ToggleHeader 
          title="Piyasa Durumu" 
          icon={Activity} 
          isOpen={showMarket} 
          onToggle={() => setShowMarket(!showMarket)}
          color="text-success"
        />
        {showMarket && (
          <div className="p-3">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="font-bold text-theme-text">XU100</span>
                {bist100.is_up ? <TrendingUp className="w-4 h-4 text-success" /> : <TrendingDown className="w-4 h-4 text-danger" />}
              </div>
              <div className="text-right text-xs text-theme-muted">
                <div>{dateStr}</div>
                <div>{timeStr}</div>
              </div>
            </div>
            <div className="flex items-end justify-between">
              <div>
                <div className="text-xl font-bold text-theme-text">
                  {bist100.price?.toLocaleString('tr-TR', { minimumFractionDigits: 2 }) || '—'}
                </div>
                <div className={`text-sm font-medium ${bist100.is_up ? 'text-success' : 'text-danger'}`}>
                  {bist100.is_up ? '▲' : '▼'} %{Math.abs(bist100.change_percent || 0).toFixed(2)}
                </div>
              </div>
              <div className="flex items-end gap-0.5 h-8">
                {[40, 60, 45, 70, 55, 80, 65, 90, 75, 95].map((h, i) => (
                  <div 
                    key={i} 
                    className={`w-1.5 rounded-t ${bist100.is_up ? 'bg-success' : 'bg-danger'}`}
                    style={{ height: `${h}%` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Seçili Hisse + Sinyal */}
      <div className="card p-3">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="px-2 py-1 rounded-lg bg-primary-500/20 text-primary-400 font-bold text-sm border border-primary-500/30">
              {selectedTicker?.split('.')[0] || 'THYAO'}
            </span>
            <span className="flex items-center gap-1 text-[10px] text-success bg-success/10 px-1.5 py-0.5 rounded">
              <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
              Canlı
            </span>
          </div>
          {/* Signal Badge */}
          <div className={`flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-bold ${
            signal?.signal === 'BUY' ? 'bg-success/15 text-success border border-success/30' :
            signal?.signal === 'SELL' ? 'bg-danger/15 text-danger border border-danger/30' :
            'bg-warning/15 text-warning border border-warning/30'
          }`}>
            <Zap className="w-3 h-3" />
            {signal?.signal === 'BUY' ? 'AL' : signal?.signal === 'SELL' ? 'SAT' : 'BEKLE'}
          </div>
        </div>

        <div className="flex items-end justify-between">
          <div>
            <div className="text-2xl font-bold text-theme-text">
              {formatCurrency(currentPrice)}
            </div>
            <div className={`text-sm font-medium ${isPositive ? 'text-success' : 'text-danger'}`}>
              {isPositive ? '▲' : '▼'} {formatCurrency(Math.abs(change))} ({isPositive ? '+' : ''}{changePercent.toFixed(2)}%)
            </div>
          </div>
          {/* Mini Chart */}
          <div className="w-24 h-12 rounded overflow-hidden">
            {stockData?.data && (
              <MiniChart
                data={stockData.data.slice(-30).map(d => d.close)}
                color={isPositive ? '#10b981' : '#ef4444'}
                height={48}
              />
            )}
          </div>
        </div>
      </div>

      {/* Grafik - Collapsible */}
      <div className="card">
        <ToggleHeader 
          title="Fiyat Grafiği" 
          icon={BarChart3} 
          isOpen={showChart} 
          onToggle={() => setShowChart(!showChart)}
        />
        {showChart && (
          <div className="p-2">
            {isLoading && !stockData?.data ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="w-6 h-6 animate-spin text-primary" />
              </div>
            ) : (
              <div className="h-48">
                <StockChart
                  height={180}
                  data={stockData?.data || []}
                  indicators={indicatorData}
                  selectedIndicators={{}}
                />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Teknik Göstergeler - Collapsible */}
      <div className="card">
        <ToggleHeader 
          title="Teknik Göstergeler" 
          icon={Target} 
          isOpen={showIndicators} 
          onToggle={() => setShowIndicators(!showIndicators)}
          color="text-accent-400"
        />
        {showIndicators && (
          <div className="p-3 grid grid-cols-2 gap-2">
            {[
              { name: 'RSI', value: indicatorData?.rsi_14?.toFixed(1) || indicatorData?.rsi?.toFixed(1) || '—', 
                status: (indicatorData?.rsi_14 || indicatorData?.rsi) > 70 ? 'danger' : (indicatorData?.rsi_14 || indicatorData?.rsi) < 30 ? 'success' : 'neutral' },
              { name: 'MACD', value: indicatorData?.macd?.toFixed(2) || '—', 
                status: indicatorData?.macd > 0 ? 'success' : indicatorData?.macd < 0 ? 'danger' : 'neutral' },
              { name: 'ADX', value: indicatorData?.adx?.toFixed(1) || '—', 
                status: indicatorData?.adx > 25 ? 'success' : 'neutral' },
              { name: 'Stoch %K', value: indicatorData?.stoch_k?.toFixed(1) || '—', 
                status: indicatorData?.stoch_k > 80 ? 'danger' : indicatorData?.stoch_k < 20 ? 'success' : 'neutral' },
            ].map((ind, i) => (
              <div key={i} className="p-2 rounded-lg bg-theme-card/50 border border-[var(--glass-border)]">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-theme-muted uppercase">{ind.name}</span>
                  <span className={`w-1.5 h-1.5 rounded-full ${
                    ind.status === 'success' ? 'bg-success' : ind.status === 'danger' ? 'bg-danger' : 'bg-theme-muted'
                  }`} />
                </div>
                <span className={`text-lg font-bold ${
                  ind.status === 'success' ? 'text-success' : ind.status === 'danger' ? 'text-danger' : 'text-theme-text'
                }`}>{ind.value}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* İstatistikler */}
      <div className="card p-3">
        <div className="flex items-center gap-2 mb-3">
          <Activity className="w-4 h-4 text-success" />
          <span className="font-bold text-theme-text text-sm">Günlük İstatistikler</span>
        </div>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="flex justify-between p-2 rounded bg-theme-card/50">
            <span className="text-theme-muted">En Yüksek</span>
            <span className="text-success font-medium">{formatCurrency(latestData?.high)}</span>
          </div>
          <div className="flex justify-between p-2 rounded bg-theme-card/50">
            <span className="text-theme-muted">En Düşük</span>
            <span className="text-danger font-medium">{formatCurrency(latestData?.low)}</span>
          </div>
          <div className="flex justify-between p-2 rounded bg-theme-card/50">
            <span className="text-theme-muted">Açılış</span>
            <span className="text-theme-text font-medium">{formatCurrency(latestData?.open)}</span>
          </div>
          <div className="flex justify-between p-2 rounded bg-theme-card/50">
            <span className="text-theme-muted">Önceki</span>
            <span className="text-theme-text font-medium">{formatCurrency(stockInfo?.previous_close)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MobileDashboard;
