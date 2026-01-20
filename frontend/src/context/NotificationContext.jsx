import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { toast } from 'react-hot-toast';

const NotificationContext = createContext();

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider');
  }
  return context;
};

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [stats, setStats] = useState(null);
  const [isChecking, setIsChecking] = useState(false);

  // Fix: Do not default to /api here if we want to avoid double prefixing with axios instance
  // But since we use raw axios here, we need a safe base.
  // Ideally, use the apiClient from ../services/api
  const API_BASE = import.meta.env.VITE_API_URL || ''; 
  // If empty, axios uses relative path (which is what we want for proxy/Vercel)
  // If VITE_API_URL is set (e.g. http://localhost:8000), it uses that.


  // Bildirimleri kontrol et
  const checkNotifications = useCallback(async () => {
    if (isChecking) return;
    
    setIsChecking(true);
    try {
      const response = await axios.get(`${API_BASE}/api/alerts/check`);
      
      if (response.data.success && response.data.triggered_alerts.length > 0) {
        const newNotifications = response.data.triggered_alerts;
        
        // Her yeni bildirim için toast göster
        newNotifications.forEach(notif => {
          const notifType = notif.priority === 'critical' || notif.priority === 'high' 
            ? 'error' 
            : notif.priority === 'medium' 
            ? 'success' 
            : 'info';
          
          toast[notifType](notif.message, {
            duration: 5000,
            icon: notif.priority === 'critical' ? '🔴' : 
                  notif.priority === 'high' ? '🟡' : 
                  notif.priority === 'medium' ? '🟢' : '⚪',
          });

          // Tarayıcı bildirimi (izin verilmişse)
          if (notif.notification?.browser && 'Notification' in window && Notification.permission === 'granted') {
            new Notification('Trading Bot Alert', {
              body: notif.message,
              icon: '/logo.png',
              tag: notif.id,
              requireInteraction: notif.priority === 'critical'
            });
          }

          // Ses çal (izin verilmişse)
          if (notif.notification?.sound) {
            playNotificationSound(notif.priority);
          }
        });

        // Bildirimleri güncelle
        setNotifications(prev => [...newNotifications, ...prev]);
        loadStats();
      }
    } catch (error) {
      console.error('Bildirim kontrolü başarısız:', error);
    } finally {
      setIsChecking(false);
    }
  }, [isChecking]);

  // İstatistikleri yükle
  const loadStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/alerts/statistics`);
      if (response.data.success) {
        setStats(response.data.statistics);
        setUnreadCount(response.data.statistics.unread_count);
      }
    } catch (error) {
      console.error('İstatistikler yüklenemedi:', error);
    }
  };

  // Bildirim sesi çal
  const playNotificationSound = (priority) => {
    try {
      const audio = new Audio();
      // Farklı öncelikler için farklı sesler
      if (priority === 'critical') {
        audio.src = '/sounds/critical-alert.mp3';
      } else if (priority === 'high') {
        audio.src = '/sounds/high-alert.mp3';
      } else {
        audio.src = '/sounds/notification.mp3';
      }
      audio.volume = 0.5;
      audio.play().catch(err => console.error('Ses çalınamadı:', err));
    } catch (error) {
      console.error('Ses hatası:', error);
    }
  };

  // Alert oluştur
  const createAlert = async (alertData) => {
    try {
      const response = await axios.post(`${API_BASE}/api/alerts/create`, alertData);
      
      if (response.data.success) {
        toast.success('Alert başarıyla oluşturuldu!');
        loadStats();
        return response.data.alert_id;
      }
    } catch (error) {
      console.error('Alert oluşturulamadı:', error);
      toast.error('Alert oluşturulamadı');
      throw error;
    }
  };

  // Alert sil
  const deleteAlert = async (alertId) => {
    try {
      const response = await axios.delete(`${API_BASE}/api/alerts/${alertId}`);
      
      if (response.data.success) {
        toast.success('Alert silindi');
        loadStats();
      }
    } catch (error) {
      console.error('Alert silinemedi:', error);
      toast.error('Alert silinemedi');
      throw error;
    }
  };

  // Bildirimi okundu işaretle
  const markAsRead = async (alertId) => {
    try {
      await axios.put(`${API_BASE}/api/alerts/notifications/${alertId}/read`);
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Bildirim güncellenemedi:', error);
    }
  };

  // Tümünü okundu işaretle
  const markAllAsRead = async () => {
    try {
      await axios.put(`${API_BASE}/api/alerts/notifications/read-all`);
      setUnreadCount(0);
    } catch (error) {
      console.error('Bildirimler güncellenemedi:', error);
    }
  };

  // Tarayıcı bildirim izni iste
  const requestNotificationPermission = async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        toast.success('Tarayıcı bildirimleri aktif!');
      }
    }
  };

  // Periyodik kontrol (30 saniye)
  useEffect(() => {
    loadStats();
    checkNotifications();
    requestNotificationPermission();

    const interval = setInterval(() => {
      checkNotifications();
    }, 30000); // 30 saniye

    return () => clearInterval(interval);
  }, [checkNotifications]);

  const value = {
    notifications,
    unreadCount,
    stats,
    createAlert,
    deleteAlert,
    markAsRead,
    markAllAsRead,
    checkNotifications,
    requestNotificationPermission
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

export default NotificationContext;
