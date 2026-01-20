import React, { useState, useEffect } from 'react';
import {
  Bell,
  X,
  Check,
  CheckCheck,
  Trash2,
  Filter,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Info,
  Clock,
  Settings,
  Sparkles
} from 'lucide-react';
import axios from 'axios';

const NotificationCenter = ({ isOpen, onClose }) => {
  const [notifications, setNotifications] = useState([]);
  const [filter, setFilter] = useState('all'); // all, unread, price, signal
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);

  // API base URL
  const API_BASE = '/api';

  // Bildirimleri yükle
  const loadNotifications = async (unreadOnly = false) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/alerts/history`, {
        params: {
          limit: 50,
          unread_only: unreadOnly
        }
      });
      
      if (response.data.success) {
        setNotifications(response.data.notifications);
      }
    } catch (error) {
      console.error('Bildirimler yüklenemedi:', error);
    } finally {
      setLoading(false);
    }
  };

  // İstatistikleri yükle
  const loadStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/alerts/statistics`);
      if (response.data.success) {
        setStats(response.data.statistics);
      }
    } catch (error) {
      console.error('İstatistikler yüklenemedi:', error);
    }
  };

  // Bildirimi okundu işaretle
  const markAsRead = async (alertId) => {
    try {
      await axios.put(`${API_BASE}/alerts/notifications/${alertId}/read`);
      setNotifications(prev =>
        prev.map(n => n.id === alertId ? { ...n, read: true } : n)
      );
      loadStats();
    } catch (error) {
      console.error('Bildirim güncellenemedi:', error);
    }
  };

  // Tümünü okundu işaretle
  const markAllAsRead = async () => {
    try {
      await axios.put(`${API_BASE}/alerts/notifications/read-all`);
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      loadStats();
    } catch (error) {
      console.error('Bildirimler güncellenemedi:', error);
    }
  };

  // Geçmişi temizle
  const clearHistory = async () => {
    if (!window.confirm('Tüm bildirim geçmişini temizlemek istediğinize emin misiniz?')) {
      return;
    }
    
    try {
      await axios.delete(`${API_BASE}/alerts/history/clear`);
      setNotifications([]);
      loadStats();
    } catch (error) {
      console.error('Geçmiş temizlenemedi:', error);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadNotifications(filter === 'unread');
      loadStats();
    }
  }, [isOpen, filter]);

  // Filtrelenmiş bildirimler
  const filteredNotifications = notifications.filter(n => {
    if (filter === 'unread') return !n.read;
    if (filter === 'price') return n.type === 'price';
    if (filter === 'signal') return n.type === 'signal';
    return true;
  });

  // Bildirim ikonu ve renk
  const getNotificationStyle = (notification) => {
    const priority = notification.priority || 'medium';
    const type = notification.type;
    const condition = notification.condition || {};

    // IPO bildirimi özel stili
    if (condition.type === 'new_ipo') {
      return {
        icon: Sparkles,
        bg: 'from-purple-500/20 to-pink-500/10',
        text: 'text-purple-400',
        border: 'border-purple-500/30'
      };
    }

    const styles = {
      critical: {
        icon: AlertTriangle,
        bg: 'from-danger/20 to-danger/10',
        text: 'text-danger',
        border: 'border-danger/30'
      },
      high: {
        icon: TrendingUp,
        bg: 'from-warning/20 to-warning/10',
        text: 'text-warning',
        border: 'border-warning/30'
      },
      medium: {
        icon: Info,
        bg: 'from-primary/20 to-primary/10',
        text: 'text-primary',
        border: 'border-primary/30'
      },
      low: {
        icon: Clock,
        bg: 'from-accent-500/20 to-accent-500/10',
        text: 'text-accent-400',
        border: 'border-accent-500/30'
      }
    };

    return styles[priority] || styles.medium;
  };

  // Zaman formatla
  const formatTime = (isoString) => {
    const date = new Date(isoString);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000); // saniye

    if (diff < 60) return `${diff}s önce`;
    if (diff < 3600) return `${Math.floor(diff / 60)}dk önce`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}sa önce`;
    return `${Math.floor(diff / 86400)}g önce`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4">
      {/* Overlay */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Notification Panel */}
      <div className="relative glass rounded-2xl border border-[var(--glass-border)] shadow-2xl max-w-2xl w-full max-h-[80vh] flex flex-col animate-scale-in">
        {/* Header */}
        <div className="p-6 border-b border-[var(--glass-border)]">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-primary/20 to-primary/10 rounded-xl">
                <Bell className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-theme-text">Bildirimler</h2>
                {stats && (
                  <p className="text-sm text-theme-muted">
                    {stats.unread_count} okunmamış, {stats.total_history} toplam
                  </p>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/5 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-theme-muted" />
            </button>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 flex-wrap">
            {/* Filters */}
            {['all', 'unread', 'price', 'signal'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  filter === f
                    ? 'bg-primary text-white'
                    : 'bg-white/5 text-theme-muted hover:bg-white/10'
                }`}
              >
                {f === 'all' && 'Tümü'}
                {f === 'unread' && 'Okunmamış'}
                {f === 'price' && 'Fiyat'}
                {f === 'signal' && 'Sinyal'}
              </button>
            ))}

            <div className="flex-1" />

            {/* Action Buttons */}
            {stats && stats.unread_count > 0 && (
              <button
                onClick={markAllAsRead}
                className="p-2 hover:bg-white/5 rounded-lg transition-colors group"
                title="Tümünü okundu işaretle"
              >
                <CheckCheck className="w-4 h-4 text-theme-muted group-hover:text-success" />
              </button>
            )}
            <button
              onClick={clearHistory}
              className="p-2 hover:bg-white/5 rounded-lg transition-colors group"
              title="Geçmişi temizle"
            >
              <Trash2 className="w-4 h-4 text-theme-muted group-hover:text-danger" />
            </button>
          </div>
        </div>

        {/* Notifications List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
          ) : filteredNotifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="p-4 bg-white/5 rounded-full mb-4">
                <Bell className="w-8 h-8 text-theme-muted" />
              </div>
              <p className="text-theme-muted">
                {filter === 'unread' ? 'Okunmamış bildirim yok' : 'Henüz bildirim yok'}
              </p>
            </div>
          ) : (
            filteredNotifications.map(notification => {
              const style = getNotificationStyle(notification);
              const IconComponent = style.icon;

              return (
                <div
                  key={notification.id}
                  className={`p-4 rounded-xl border ${style.border} bg-gradient-to-br ${style.bg} transition-all hover:scale-[1.02] ${
                    !notification.read ? 'shadow-lg' : 'opacity-70'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg bg-gradient-to-br ${style.bg} border ${style.border}`}>
                      <IconComponent className={`w-5 h-5 ${style.text}`} />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-theme-text">
                            {notification.ticker}
                          </span>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${style.text} bg-current/10`}>
                            {notification.type}
                          </span>
                        </div>
                        <span className="text-xs text-theme-muted whitespace-nowrap">
                          {formatTime(notification.triggered_at || notification.created_at)}
                        </span>
                      </div>

                      <p className="text-sm text-theme-text mb-2">
                        {notification.message}
                      </p>

                      <div className="flex items-center gap-2">
                        {!notification.read && (
                          <button
                            onClick={() => markAsRead(notification.id)}
                            className="text-xs px-2 py-1 rounded bg-white/5 hover:bg-white/10 text-theme-muted hover:text-success transition-colors flex items-center gap-1"
                          >
                            <Check className="w-3 h-3" />
                            Okundu
                          </button>
                        )}
                        {notification.priority && (
                          <span className={`text-xs px-2 py-1 rounded ${
                            notification.priority === 'critical' ? 'bg-danger/20 text-danger' :
                            notification.priority === 'high' ? 'bg-warning/20 text-warning' :
                            'bg-primary/20 text-primary'
                          }`}>
                            {notification.priority === 'critical' && '🔴 Kritik'}
                            {notification.priority === 'high' && '🟡 Yüksek'}
                            {notification.priority === 'medium' && '🔵 Orta'}
                            {notification.priority === 'low' && '⚪ Düşük'}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer Stats */}
        {stats && (
          <div className="p-4 border-t border-[var(--glass-border)] bg-white/5">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-primary">
                  {stats.active_alerts}
                </div>
                <div className="text-xs text-theme-muted">Aktif Alert</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-success">
                  {stats.triggered_today}
                </div>
                <div className="text-xs text-theme-muted">Bugün Tetiklenen</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-accent-400">
                  {stats.total_history}
                </div>
                <div className="text-xs text-theme-muted">Toplam Geçmiş</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationCenter;
