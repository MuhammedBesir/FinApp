/**
 * Real-time Notification Component
 * Shows push notifications from WebSocket
 */
import React, { useState, useEffect } from "react";
import {
  Bell,
  BellOff,
  X,
  Check,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Info,
  CheckCircle,
  XCircle,
  Trash2,
} from "lucide-react";
import { useNotifications } from "../../hooks/useWebSocket";

const NotificationCenter = () => {
  const {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    clearAll,
    requestPermission,
    isConnected,
  } = useNotifications();

  const [isOpen, setIsOpen] = useState(false);
  const [permissionGranted, setPermissionGranted] = useState(
    Notification.permission === "granted",
  );

  // Request notification permission on mount
  useEffect(() => {
    if (Notification.permission === "default") {
      requestPermission().then(setPermissionGranted);
    }
  }, []);

  const getIcon = (type) => {
    switch (type) {
      case "signal":
        return <TrendingUp className="w-4 h-4" />;
      case "success":
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-yellow-400" />;
      case "error":
        return <XCircle className="w-4 h-4 text-red-400" />;
      default:
        return <Info className="w-4 h-4 text-blue-400" />;
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case "signal":
        return "border-l-primary-500";
      case "success":
        return "border-l-green-500";
      case "warning":
        return "border-l-yellow-500";
      case "error":
        return "border-l-red-500";
      default:
        return "border-l-blue-500";
    }
  };

  const formatTime = (date) => {
    if (!date) return "";
    const now = new Date();
    const diff = now - new Date(date);
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);

    if (minutes < 1) return "Şimdi";
    if (minutes < 60) return `${minutes} dk önce`;
    if (hours < 24) return `${hours} saat önce`;
    return new Date(date).toLocaleDateString("tr-TR");
  };

  return (
    <div className="relative">
      {/* Bell Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all"
      >
        {isConnected ? (
          <Bell className="w-5 h-5 text-slate-300" />
        ) : (
          <BellOff className="w-5 h-5 text-slate-500" />
        )}

        {/* Unread Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-xs font-bold text-white animate-pulse">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}

        {/* Connection indicator */}
        <span
          className={`absolute bottom-1 right-1 w-2 h-2 rounded-full ${
            isConnected ? "bg-green-500" : "bg-red-500"
          }`}
        />
      </button>

      {/* Notification Panel */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Panel */}
          <div className="absolute right-0 top-12 w-80 sm:w-96 z-50 glass-card rounded-2xl border border-white/10 shadow-2xl overflow-hidden animate-fade-in">
            {/* Header */}
            <div className="p-4 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Bell className="w-5 h-5 text-primary-400" />
                <h3 className="font-semibold text-white">Bildirimler</h3>
                {unreadCount > 0 && (
                  <span className="px-2 py-0.5 bg-primary-500/20 text-primary-400 text-xs rounded-full">
                    {unreadCount} yeni
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {notifications.length > 0 && (
                  <>
                    <button
                      onClick={markAllAsRead}
                      className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
                      title="Tümünü okundu işaretle"
                    >
                      <Check className="w-4 h-4 text-slate-400" />
                    </button>
                    <button
                      onClick={clearAll}
                      className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
                      title="Tümünü temizle"
                    >
                      <Trash2 className="w-4 h-4 text-slate-400" />
                    </button>
                  </>
                )}
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
                >
                  <X className="w-4 h-4 text-slate-400" />
                </button>
              </div>
            </div>

            {/* Connection Status */}
            {!isConnected && (
              <div className="px-4 py-2 bg-yellow-500/10 border-b border-yellow-500/20 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-yellow-400" />
                <span className="text-xs text-yellow-400">
                  Bağlantı kesildi. Yeniden bağlanılıyor...
                </span>
              </div>
            )}

            {/* Notification List */}
            <div className="max-h-96 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="p-8 text-center">
                  <Bell className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                  <p className="text-slate-400 text-sm">Henüz bildirim yok</p>
                  <p className="text-slate-500 text-xs mt-1">
                    Sinyal ve fiyat uyarıları burada görünecek
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-white/5">
                  {notifications.map((notification) => (
                    <div
                      key={notification.id}
                      onClick={() => markAsRead(notification.id)}
                      className={`p-4 hover:bg-white/5 cursor-pointer transition-colors border-l-2 ${getTypeColor(
                        notification.type,
                      )} ${!notification.read ? "bg-white/5" : ""}`}
                    >
                      <div className="flex items-start gap-3">
                        <div
                          className={`p-2 rounded-lg ${
                            notification.type === "signal"
                              ? "bg-primary-500/20"
                              : "bg-white/5"
                          }`}
                        >
                          {getIcon(notification.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <h4 className="font-medium text-white text-sm truncate">
                              {notification.title}
                            </h4>
                            {!notification.read && (
                              <span className="w-2 h-2 bg-primary-500 rounded-full flex-shrink-0" />
                            )}
                          </div>
                          <p className="text-slate-400 text-xs mt-0.5 line-clamp-2">
                            {notification.body}
                          </p>
                          <span className="text-slate-500 text-xs mt-1 block">
                            {formatTime(notification.receivedAt)}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Browser Notification Permission */}
            {!permissionGranted && (
              <div className="p-4 border-t border-white/10 bg-white/5">
                <button
                  onClick={async () => {
                    const granted = await requestPermission();
                    setPermissionGranted(granted);
                  }}
                  className="w-full py-2 px-4 bg-primary-500/20 text-primary-400 rounded-lg text-sm hover:bg-primary-500/30 transition-colors"
                >
                  Masaüstü bildirimlerini etkinleştir
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default NotificationCenter;
