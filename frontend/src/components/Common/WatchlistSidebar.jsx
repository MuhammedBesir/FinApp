/**
 * Watchlist Sidebar Component
 * Quick access to favorite stocks
 */
import React from 'react';
import { Star, X } from 'lucide-react';
import { usePortfolioStore } from '../store/portfolioStore';
import { useStore } from '../store';

const WatchlistSidebar = () => {
  const { watchlist, addToWatchlist, removeFromWatchlist } = usePortfolioStore();
  const { selectedTicker, setTicker } = useStore();

  const handleTickerClick = (ticker) => {
    setTicker(ticker);
  };

  return (
    <div className="bg-dark-card rounded-lg p-4 border border-dark-border">
      <div className="flex items-center gap-2 mb-4">
        <Star className="w-5 h-5 text-yellow-400" />
        <h3 className="font-semibold">Favoriler</h3>
      </div>
      
      {watchlist.length === 0 ? (
        <p className="text-sm text-gray-400 text-center py-4">Favori yok</p>
      ) : (
        <div className="space-y-2">
          {watchlist.map((ticker) => (
            <div
              key={ticker}
              className={`flex items-center justify-between p-2 rounded cursor-pointer transition-colors ${
                selectedTicker === ticker
                  ? 'bg-primary-600'
                  : 'hover:bg-dark-bg'
              }`}
              onClick={() => handleTickerClick(ticker)}
            >
              <span className="text-sm font-medium">{ticker}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  removeFromWatchlist(ticker);
                }}
                className="text-gray-400 hover:text-red-400 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
      
      <button
        onClick={() => {
          const ticker = prompt('Hisse kodu (ör: AKBNK.IS):');
          if (ticker) addToWatchlist(ticker.toUpperCase());
        }}
        className="w-full mt-4 py-2 border border-dashed border-gray-600 rounded hover:border-primary-500 transition-colors text-sm text-gray-400"
      >
        + Favori Ekle
      </button>
    </div>
  );
};

export default WatchlistSidebar;
