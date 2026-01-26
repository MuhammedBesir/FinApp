/**
 * Notification Service
 * Browser notifications ve alert yönetimi
 */
import axios from 'axios';

class NotificationService {
  constructor() {
    this.permission = 'default';
    this.checkInterval = null;
    this.listeners = [];
  }

  /**
   * Browser notification izni iste
   */
  async requestPermission() {
    if (!('Notification' in window)) {
      console.warn('Browser notifications not supported');
      return false;
    }

    if (Notification.permission === 'granted') {
      this.permission = 'granted';
      return true;
    }

    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      this.permission = permission;
      return permission === 'granted';
    }

    return false;
  }

  /**
   * Browser notification göster
   */
  showNotification(title, options = {}) {
    if (Notification.permission !== 'granted') {
      console.warn('Notification permission not granted');
      return;
    }

    const notification = new Notification(title, {
      body: options.message || '',
      icon: options.icon || '/vite.svg',
      badge: '/vite.svg',
      tag: options.tag || 'trading-alert',
      requireInteraction: options.requireInteraction || true,
      silent: !options.sound,
      ...options
    });

    // Sound alert
    if (options.sound) {
      this.playSound();
    }

    // Click handler
    notification.onclick = () => {
      window.focus();
      notification.close();
      if (options.onClick) {
        options.onClick();
      }
    };

    return notification;
  }

  /**
   * Alert sound çal
   */
  playSound() {
    try {
      // Simple beep using Web Audio API
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.value = 800;
      oscillator.type = 'sine';

      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

      oscillator.start(audioContext.current);
      oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
      console.error('Error playing sound:', error);
    }
  }

  /**
   * Alert kontrolünü başlat (30 saniyede bir)
   */
  startAlertPolling() {
    if (this.checkInterval) {
      return; // Already running
    }

    // İlk kontrol
    this.checkAlerts();

    // Her 5 dakikada bir kontrol et (rate limit için)
    this.checkInterval = setInterval(() => {
      this.checkAlerts();
    }, 5 * 60 * 1000);

    console.log('Alert polling started');
  }

  /**
   * Alert kontrolünü durdur
   */
  stopAlertPolling() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
      console.log('Alert polling stopped');
    }
  }

  /**
   * Alertleri kontrol et ve bildirimleri göster
   */
  async checkAlerts() {
    try {
      const response = await axios.get('/api/alerts/check');
      
      if (response.data.success && response.data.triggered_alerts) {
        const triggered = response.data.triggered_alerts;
        
        triggered.forEach(alert => {
          // Browser notification göster
          this.showNotification('Trading Alert! 🔔', {
            message: alert.message,
            sound: alert.notification.sound,
            tag: alert.id,
            requireInteraction: true
          });

          // Listeners'a bildir
          this.notifyListeners(alert);
        });
      }
    } catch (error) {
      console.error('Error checking alerts:', error);
    }
  }

  /**
   * Alert listener ekle
   */
  addListener(callback) {
    this.listeners.push(callback);
  }

  /**
   * Alert listener kaldır
   */
  removeListener(callback) {
    this.listeners = this.listeners.filter(cb => cb !== callback);
  }

  /**
   * Tüm listeners'a alert bildir
   */
  notifyListeners(alert) {
    this.listeners.forEach(callback => {
      try {
        callback(alert);
      } catch (error) {
        console.error('Error in alert listener:', error);
      }
    });
  }

  /**
   * Alert oluştur
   */
  async createAlert(alertData) {
    try {
      const response = await axios.post('/api/alerts/create', alertData);
      return response.data;
    } catch (error) {
      console.error('Error creating alert:', error);
      throw error;
    }
  }

  /**
   * Aktif alertleri getir
   */
  async getActiveAlerts() {
    try {
      const response = await axios.get('/api/alerts/active');
      return response.data.alerts || [];
    } catch (error) {
      console.error('Error getting alerts:', error);
      return [];
    }
  }

  /**
   * Alert sil
   */
  async deleteAlert(alertId) {
    try {
      const response = await axios.delete(`/api/alerts/${alertId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting alert:', error);
      throw error;
    }
  }

  /**
   * Alert toggle (aktif/pasif)
   */
  async toggleAlert(alertId, active) {
    try {
      const response = await axios.put(
        `/api/alerts/${alertId}/toggle?active=${active}`
      );
      return response.data;
    } catch (error) {
      console.error('Error toggling alert:', error);
      throw error;
    }
  }
}

// Singleton instance
const notificationService = new NotificationService();

export default notificationService;
