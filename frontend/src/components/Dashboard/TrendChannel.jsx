/**
 * Trend Channel Widget - Trend Kanalı Analizi
 * Yükselen/Düşen kanal tespiti ve sinyal gösterimi
 */
import React, { useEffect, useState } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Target,
  AlertTriangle,
  ArrowUp,
  ArrowDown,
  Activity,
  RefreshCw
} from 'lucide-react';
import { useStore } from '../../store';
import api from '../../services/api';

const TrendChannel = ({ refreshInterval = 60000 }) => {
  const { selectedTicker } = useStore();
  const [channelData, setChannelData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchChannelData = async () => {
    if (!selectedTicker) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.get(`/indicators/${selectedTicker}/trend-channel`, {
        params: {
          interval: '1d',
          period: '3mo',
          channel_period: 20
        }
      });
      
      if (response.data?.success) {
        setChannelData(response.data.analysis);
        setLastUpdate(new Date());
      }
    } catch (err) {
      console.error('Trend channel fetch error:', err);
      setError('Veri alınamadı');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChannelData();
    
    const interval = setInterval(fetchChannelData, refreshInterval);
    return () => clearInterval(interval);
  }, [selectedTicker, refreshInterval]);

  // Signal colors and icons
  const getSignalStyle = (action) => {
    switch (action) {
      case 'AL':
        return {
          bg: 'bg-green-500/20',
          border: 'border-green-500/50',
          text: 'text-green-500',
          icon: ArrowUp
        };
      case 'SAT':
        return {
          bg: 'bg-red-500/20',
          border: 'border-red-500/50',
          text: 'text-red-500',
          icon: ArrowDown
        };
      case 'KAR_AL':
        return {
          bg: 'bg-yellow-500/20',
          border: 'border-yellow-500/50',
          text: 'text-yellow-500',
          icon: Target
        };
      default:
        return {
          bg: 'bg-slate-500/20',
          border: 'border-slate-500/50',
          text: 'text-slate-400',
          icon: Minus
        };
    }
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'YUKSELIS':
        return <TrendingUp className="w-5 h-5 text-green-500" />;
      case 'DUSUS':
        return <TrendingDown className="w-5 h-5 text-red-500" />;
      default:
        return <Minus className="w-5 h-5 text-slate-400" />;
    }
  };

  const getTrendLabel = (trend) => {
    switch (trend) {
      case 'YUKSELIS': return 'Yükseliş';
      case 'DUSUS': return 'Düşüş';
      default: return 'Yatay';
    }
  };

  const getBreakoutLabel = (breakout) => {
    switch (breakout) {
      case 'YUKARI_KIRILMA': return 'Yukarı Kırılma';
      case 'ASAGI_KIRILMA': return 'Aşağı Kırılma';
      default: return 'Kanal İçi';
    }
  };

  if (!selectedTicker) {
    return (
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
            <Activity className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h4 className="font-bold text-theme-text">Trend Kanalı</h4>
            <p className="text-xs text-theme-muted">Hisse seçin</p>
          </div>
        </div>
        <div className="text-center py-8 text-theme-muted">
          Analiz için bir hisse seçin
        </div>
      </div>
    );
  }

  if (loading && !channelData) {
    return (
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
            <Activity className="w-5 h-5 text-purple-400 animate-pulse" />
          </div>
          <div>
            <h4 className="font-bold text-theme-text">Trend Kanalı</h4>
            <p className="text-xs text-theme-muted">{selectedTicker.split('.')[0]}</p>
          </div>
        </div>
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-6 h-6 text-theme-muted animate-spin" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center">
            <AlertTriangle className="w-5 h-5 text-red-400" />
          </div>
          <div>
            <h4 className="font-bold text-theme-text">Trend Kanalı</h4>
            <p className="text-xs text-red-400">{error}</p>
          </div>
        </div>
        <button 
          onClick={fetchChannelData}
          className="w-full py-2 text-sm text-theme-muted hover:text-theme-text"
        >
          Tekrar Dene
        </button>
      </div>
    );
  }

  if (!channelData) return null;

  const { signal, channel_data } = channelData;
  const signalStyle = getSignalStyle(signal?.action);
  const SignalIcon = signalStyle.icon;

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
            <Activity className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h4 className="font-bold text-theme-text">Trend Kanalı</h4>
            <p className="text-xs text-theme-muted">
              {selectedTicker.split('.')[0]} • {lastUpdate?.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
            </p>
          </div>
        </div>
        <button 
          onClick={fetchChannelData}
          disabled={loading}
          className="p-2 rounded-lg hover:bg-theme-card/50 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 text-theme-muted ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Signal Badge */}
      <div className={`p-4 rounded-xl ${signalStyle.bg} border ${signalStyle.border} mb-4`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center`}>
              <SignalIcon className={`w-6 h-6 ${signalStyle.text}`} />
            </div>
            <div>
              <div className={`text-xl font-bold ${signalStyle.text}`}>
                {signal?.action === 'KAR_AL' ? 'KÂR AL' : signal?.action}
              </div>
              <div className="text-sm text-theme-muted">
                Güven: <span className={signalStyle.text}>{signal?.confidence}%</span>
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2">
              {getTrendIcon(channel_data?.trend)}
              <span className="text-sm font-medium text-theme-text">
                {getTrendLabel(channel_data?.trend)}
              </span>
            </div>
            <div className="text-xs text-theme-muted mt-1">
              {getBreakoutLabel(channel_data?.breakout)}
            </div>
          </div>
        </div>
        
        {signal?.reason && (
          <p className="mt-3 text-sm text-theme-muted border-t border-white/10 pt-3">
            💡 {signal.reason}
          </p>
        )}
      </div>

      {/* Channel Position Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-xs text-theme-muted mb-2">
          <span>Destek</span>
          <span>Kanal İçi Pozisyon: %{channel_data?.position}</span>
          <span>Direnç</span>
        </div>
        <div className="h-3 bg-slate-700 rounded-full overflow-hidden relative">
          <div 
            className="absolute left-0 top-0 h-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 opacity-30"
            style={{ width: '100%' }}
          />
          <div 
            className="absolute top-0 h-full w-2 bg-white rounded-full shadow-lg transform -translate-x-1/2"
            style={{ left: `${Math.min(100, Math.max(0, channel_data?.position || 50))}%` }}
          />
        </div>
      </div>

      {/* Price Levels */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-green-500/10 rounded-xl p-3 text-center border border-green-500/20">
          <div className="text-xs text-green-400 mb-1">Destek</div>
          <div className="font-bold text-green-500">₺{channel_data?.support}</div>
        </div>
        <div className="bg-blue-500/10 rounded-xl p-3 text-center border border-blue-500/20">
          <div className="text-xs text-blue-400 mb-1">Mevcut</div>
          <div className="font-bold text-blue-500">₺{channel_data?.current_price}</div>
        </div>
        <div className="bg-red-500/10 rounded-xl p-3 text-center border border-red-500/20">
          <div className="text-xs text-red-400 mb-1">Direnç</div>
          <div className="font-bold text-red-500">₺{channel_data?.resistance}</div>
        </div>
      </div>

      {/* Trade Details (if AL signal) */}
      {signal?.action === 'AL' && signal?.entry && (
        <div className="mt-4 p-3 bg-green-500/10 rounded-xl border border-green-500/20">
          <div className="text-xs text-green-400 mb-2 font-medium">💰 İşlem Detayı</div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div>
              <div className="text-xs text-theme-muted">Giriş</div>
              <div className="text-sm font-bold text-theme-text">₺{signal.entry?.toFixed(2)}</div>
            </div>
            <div>
              <div className="text-xs text-theme-muted">Stop Loss</div>
              <div className="text-sm font-bold text-red-400">₺{signal.stop_loss?.toFixed(2)}</div>
            </div>
            <div>
              <div className="text-xs text-theme-muted">Hedef</div>
              <div className="text-sm font-bold text-green-400">₺{signal.target?.toFixed(2)}</div>
            </div>
          </div>
        </div>
      )}

      {/* Channel Width */}
      <div className="mt-4 flex items-center justify-between text-sm">
        <span className="text-theme-muted">Kanal Genişliği</span>
        <span className="font-medium text-theme-text">{channel_data?.channel_width}</span>
      </div>
    </div>
  );
};

export default TrendChannel;
