/**
 * Mobile Screener Page
 * 📱 Compact stock screener with filters
 */
import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  TrendingDown,
  Star,
  RefreshCw,
} from 'lucide-react';
import { usePortfolioStore } from '../../store/portfolioStore';

const MobileScreenerPage = () => {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filter, setFilter] = useState('all');
  const { watchlist, addToWatchlist, removeFromWatchlist } = usePortfolioStore();

  useEffect(() => {
    const fetchStocks = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/screener/top-picks');
        const data = await res.json();
        if (data.success) {
          setStocks(data.picks || []);
        }
      } catch (error) {
        console.error('Screener fetch error:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchStocks();
  }, []);

  const isInWatchlist = (ticker) => Array.isArray(watchlist) && watchlist.includes(ticker);
  const toggleWatchlist = (ticker) => {
    if (isInWatchlist(ticker)) removeFromWatchlist(ticker);
    else addToWatchlist(ticker);
  };

  const filteredStocks = stocks.filter(s => {
    const matchesSearch = s.ticker?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filter === 'all' || 
      (filter === 'buy' && s.signal === 'BUY') ||
      (filter === 'sell' && s.signal === 'SELL') ||
      (filter === 'watchlist' && isInWatchlist(s.ticker));
    return matchesSearch && matchesFilter;
  });

  const ToggleHeader = ({ title, icon: Icon, isOpen, onToggle, color = 'text-primary-400' }) => (
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
      {/* Header */}
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-primary-500/10 flex items-center justify-center">
          <Search className="w-4 h-4 text-primary-400" />
        </div>
        <div>
          <h1 className="font-bold text-theme-text text-base">Hisse Tarayıcı</h1>
          <p className="text-xs text-theme-muted">{filteredStocks.length} sonuç</p>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-theme-muted" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Hisse ara..."
          className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-theme-card border border-[var(--glass-border)] text-theme-text text-sm focus:outline-none focus:border-primary-500"
        />
      </div>

      {/* Filter Buttons */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {['all', 'buy', 'sell', 'watchlist'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
              filter === f
                ? 'bg-primary-500 text-white'
                : 'bg-theme-card text-theme-muted hover:bg-theme-card-hover'
            }`}
          >
            {f === 'all' ? 'Tümü' : f === 'buy' ? 'Al Sinyali' : f === 'sell' ? 'Sat Sinyali' : 'Favoriler'}
          </button>
        ))}
      </div>

      {/* Stocks List */}
      <div className="card">
        <div className="divide-y divide-[var(--glass-border)]">
          {loading ? (
            <div className="p-6 text-center">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto text-primary mb-2" />
              <p className="text-sm text-theme-muted">Yükleniyor...</p>
            </div>
          ) : filteredStocks.length > 0 ? (
            filteredStocks.slice(0, 20).map((stock, i) => (
              <div key={i} className="p-3">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-theme-text">{stock.ticker?.replace('.IS', '')}</span>
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      stock.signal === 'BUY' ? 'bg-success/20 text-success' : 
                      stock.signal === 'SELL' ? 'bg-danger/20 text-danger' : 
                      'bg-theme-card text-theme-muted'
                    }`}>
                      {stock.signal === 'BUY' ? 'AL' : stock.signal === 'SELL' ? 'SAT' : 'BEKLE'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-theme-text text-sm">₺{stock.price?.toFixed(2)}</span>
                    <button
                      onClick={() => toggleWatchlist(stock.ticker)}
                      className={`p-1 rounded ${isInWatchlist(stock.ticker) ? 'text-warning' : 'text-theme-muted'}`}
                    >
                      <Star className={`w-4 h-4 ${isInWatchlist(stock.ticker) ? 'fill-current' : ''}`} />
                    </button>
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-theme-muted">Skor: <span className="text-theme-text font-medium">{stock.score || '—'}</span></span>
                  <span className={`font-medium ${(stock.change || 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                    {(stock.change || 0) >= 0 ? '+' : ''}{(stock.change || 0).toFixed(2)}%
                  </span>
                </div>
              </div>
            ))
          ) : (
            <div className="p-6 text-center">
              <Search className="w-6 h-6 text-theme-muted mx-auto mb-2" />
              <p className="text-sm text-theme-muted">Sonuç bulunamadı</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MobileScreenerPage;
