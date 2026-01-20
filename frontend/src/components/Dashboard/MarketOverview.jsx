/**
 * Market Overview - Piyasa Genel Görünümü
 * 📊 BIST100 | 🌍 Küresel piyasalar | 💱 Döviz | 🏅 Emtia
 */
import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Globe, 
  DollarSign,
  Euro,
  Bitcoin,
  Coins,
  RefreshCw
} from 'lucide-react';

const MarketOverview = () => {
  const [marketData, setMarketData] = useState({
    bist100: { value: 11958, change: 1.23, isUp: true },
    bist30: { value: 11892, change: 0.98, isUp: true },
    usd: { value: 32.45, change: -0.12, isUp: false },
    eur: { value: 35.67, change: 0.08, isUp: true },
    gold: { value: 2854.50, change: 2.34, isUp: true },
    btc: { value: 98234, change: 3.45, isUp: true },
    sp500: { value: 5914.8, change: 0.45, isUp: true },
    nasdaq: { value: 19614, change: 0.89, isUp: true },
  });
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [error, setError] = useState(null);

  const fetchMarketData = async () => {
    setIsLoading(true);
    try {
      // Tüm piyasa verilerini tek seferde çek
      const response = await fetch('/api/market/all', {
        cache: 'no-cache'
      });
      const result = await response.json();

      if (result.success && result.data) {
        const data = result.data;
        setError(null);
        setMarketData({
          bist100: {
            value: data.bist100?.price || 11958,
            change: data.bist100?.change_percent || 0,
            isUp: data.bist100?.is_up ?? true
          },
          bist30: {
            value: data.bist30?.price || 11892,
            change: data.bist30?.change_percent || 0,
            isUp: data.bist30?.is_up ?? true
          },
          usd: {
            value: data.usd_try?.price || 32.45,
            change: data.usd_try?.change_percent || 0,
            isUp: data.usd_try?.is_up ?? false
          },
          eur: {
            value: data.eur_try?.price || 35.67,
            change: data.eur_try?.change_percent || 0,
            isUp: data.eur_try?.is_up ?? true
          },
          gold: {
            value: data.gold?.price || 2854.50,
            change: data.gold?.change_percent || 0,
            isUp: data.gold?.is_up ?? true
          },
          btc: {
            value: data.btc?.price || 98234,
            change: data.btc?.change_percent || 0,
            isUp: data.btc?.is_up ?? true
          },
          sp500: {
            value: data.sp500?.price || 5914.8,
            change: data.sp500?.change_percent || 0,
            isUp: data.sp500?.is_up ?? true
          },
          nasdaq: {
            value: data.nasdaq?.price || 19614,
            change: data.nasdaq?.change_percent || 0,
            isUp: data.nasdaq?.is_up ?? true
          }
        });
      }
      setLastUpdate(result.last_update ? new Date(result.last_update) : new Date());
    } catch (error) {
      console.error('Market data fetch error:', error);
      setError('Piyasa verisi alınamadı');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMarketData(); // İlk yükleme
    const interval = setInterval(fetchMarketData, 30000); // 30 saniyede bir otomatik güncelle
    return () => clearInterval(interval);
  }, []);

  const formatValue = (value, type = 'number') => {
    switch (type) {
      case 'currency':
        return new Intl.NumberFormat('tr-TR', {
          style: 'currency',
          currency: 'TRY',
          minimumFractionDigits: 2,
        }).format(value);
      case 'usd':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
        }).format(value);
      case 'index':
        return new Intl.NumberFormat('tr-TR', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        }).format(value);
      default:
        return value.toFixed(2);
    }
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString('tr-TR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const markets = [
    {
      category: 'Türkiye',
      icon: TrendingUp,
      color: 'text-primary-400',
      items: [
        { 
          label: 'BIST 100', 
          value: marketData.bist100.value, 
          change: marketData.bist100.change, 
          isUp: marketData.bist100.isUp,
          type: 'index'
        },
        { 
          label: 'BIST 30', 
          value: marketData.bist30.value, 
          change: marketData.bist30.change, 
          isUp: marketData.bist30.isUp,
          type: 'index'
        },
      ]
    },
    {
      category: 'Döviz',
      icon: DollarSign,
      color: 'text-success',
      items: [
        { 
          label: 'USD/TRY', 
          value: marketData.usd.value, 
          change: marketData.usd.change, 
          isUp: marketData.usd.isUp,
          type: 'currency'
        },
        { 
          label: 'EUR/TRY', 
          value: marketData.eur.value, 
          change: marketData.eur.change, 
          isUp: marketData.eur.isUp,
          type: 'currency'
        },
      ]
    },
    {
      category: 'Emtia',
      icon: Coins,
      color: 'text-warning',
      items: [
        { 
          label: 'Altın (oz)', 
          value: marketData.gold.value, 
          change: marketData.gold.change, 
          isUp: marketData.gold.isUp,
          type: 'usd'
        },
        { 
          label: 'Bitcoin', 
          value: marketData.btc.value, 
          change: marketData.btc.change, 
          isUp: marketData.btc.isUp,
          type: 'usd'
        },
      ]
    },
    {
      category: 'Küresel',
      icon: Globe,
      color: 'text-accent-400',
      items: [
        { 
          label: 'S&P 500', 
          value: marketData.sp500.value, 
          change: marketData.sp500.change, 
          isUp: marketData.sp500.isUp,
          type: 'index'
        },
        { 
          label: 'NASDAQ', 
          value: marketData.nasdaq.value, 
          change: marketData.nasdaq.change, 
          isUp: marketData.nasdaq.isUp,
          type: 'index'
        },
      ]
    },
  ];

  const handleRefresh = async () => {
    await fetchMarketData();
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-bold text-theme-text mb-1">Piyasa Durumu</h3>
          <p className="text-xs text-theme-muted flex items-center gap-2">
            <span className={`w-1.5 h-1.5 rounded-full ${error ? 'bg-danger' : 'bg-success'} ${isLoading ? 'animate-pulse' : ''}`} />
            {error ? error : `Son güncelleme: ${formatTime(lastUpdate)}`}
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={isLoading}
          className="p-2 rounded-lg bg-theme-card hover:bg-theme-card-hover text-theme-muted hover:text-theme-text transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
        {markets.map((market, idx) => (
          <div key={idx} className="space-y-2 sm:space-y-3">
            {/* Kategori Başlığı */}
            <div className="flex items-center gap-2 pb-2 border-b border-[var(--glass-border)]">
              <market.icon className={`w-3.5 h-3.5 sm:w-4 sm:h-4 ${market.color}`} />
              <span className="text-xs sm:text-sm font-semibold text-theme-text">
                {market.category}
              </span>
            </div>

            {/* Market Items */}
            <div className="space-y-2">
              {market.items.map((item, itemIdx) => (
                <div
                  key={itemIdx}
                  className="p-2 sm:p-3 rounded-xl bg-theme-card hover:bg-theme-card-hover border border-[var(--glass-border)] transition-all hover:scale-[1.02]"
                >
                  <div className="flex items-start justify-between mb-1">
                    <span className="text-[10px] sm:text-xs text-theme-muted">{item.label}</span>
                    <div className="flex items-center gap-1">
                      {item.isUp ? (
                        <TrendingUp className="w-2.5 h-2.5 sm:w-3 sm:h-3 text-success" />
                      ) : (
                        <TrendingDown className="w-2.5 h-2.5 sm:w-3 sm:h-3 text-danger" />
                      )}
                    </div>
                  </div>
                  <div className="flex items-end justify-between">
                    <span className="font-bold text-theme-text">
                      {formatValue(item.value, item.type)}
                    </span>
                    <span className={`text-xs font-medium ${
                      item.isUp ? 'text-success' : 'text-danger'
                    }`}>
                      {item.isUp ? '+' : ''}{item.change.toFixed(2)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

    </div>
  );
};

export default MarketOverview;
