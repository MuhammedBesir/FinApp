/**
 * Last Update Display Component
 * Shows when data was last refreshed
 */
import React from 'react';
import { Clock, RefreshCw } from 'lucide-react';

const LastUpdate = ({ timestamp, onRefresh, isRefreshing }) => {
  if (!timestamp) return null;

  const timeAgo = (date) => {
    const seconds = Math.floor((new Date() - new Date(date)) / 1000);
    if (seconds < 60) return `${seconds} saniye önce`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} dakika önce`;
    const hours = Math.floor(minutes / 60);
    return `${hours} saat önce`;
  };

  return (
    <div className="flex items-center justify-between bg-dark-card rounded-lg px-4 py-2 border border-dark-border text-sm">
      <div className="flex items-center gap-2 text-gray-400">
        <Clock className="w-4 h-4" />
        <span>Son güncelleme: {timeAgo(timestamp)}</span>
        <span className="text-xs text-gray-500">
          ({new Date(timestamp).toLocaleTimeString('tr-TR')})
        </span>
      </div>
      
      {onRefresh && (
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="flex items-center gap-2 px-3 py-1 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          Yenile
        </button>
      )}
    </div>
  );
};

export default LastUpdate;
