/**
 * Alert Panel Component
 * Alert yönetimi ve görüntüleme
 */
import React, { useState, useEffect } from 'react';
import { Bell, BellOff, Trash2, Plus, X } from 'lucide-react';
import notificationService from '../../services/NotificationService';

const AlertPanel = () => {
  const [alerts, setAlerts] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [permissionGranted, setPermissionGranted] = useState(false);

  // Form state
  const [newAlert, setNewAlert] = useState({
    type: 'score',
    ticker: 'THYAO.IS',
    scoreAbove: 80,
    priceAbove: '',
    priceBelow: '',
    sound: true
  });

  useEffect(() => {
    // Check permission
    if (Notification.permission === 'granted') {
      setPermissionGranted(true);
    }

    // Load alerts
    loadAlerts();

    // Start alert polling
    notificationService.startAlertPolling();

    // Cleanup
    return () => {
      notificationService.stopAlertPolling();
    };
  }, []);

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const activeAlerts = await notificationService.getActiveAlerts();
      setAlerts(activeAlerts);
    } catch (error) {
      console.error('Error loading alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const requestPermission = async () => {
    const granted = await notificationService.requestPermission();
    setPermissionGranted(granted);
    
    if (granted) {
      notificationService.showNotification('Bildirimler Aktif! 🔔', {
        message: 'Trading alertleri artık bildirim olarak gelecek',
        sound: true
      });
    }
  };

  const handleCreateAlert = async (e) => {
    e.preventDefault();

    let condition = {};
    
    if (newAlert.type === 'score') {
      condition = { score_above: parseInt(newAlert.scoreAbove) };
    } else if (newAlert.type === 'price') {
      if (newAlert.priceAbove) {
        condition = { price_above: parseFloat(newAlert.priceAbove) };
      } else if (newAlert.priceBelow) {
        condition = { price_below: parseFloat(newAlert.priceBelow) };
      }
    } else if (newAlert.type === 'signal') {
      condition = {};
    }

    try {
      await notificationService.createAlert({
        type: newAlert.type,
        ticker: newAlert.ticker,
        condition,
        notification: {
          browser: true,
          sound: newAlert.sound
        }
      });

      // Refresh alerts
      await loadAlerts();
      
      // Reset form
      setShowCreateForm(false);
      setNewAlert({
        type: 'score',
        ticker: 'THYAO.IS',
        scoreAbove: 80,
        priceAbove: '',
        priceBelow: '',
        sound: true
      });

      // Show success notification
      notificationService.showNotification('Alert Oluşturuldu! ✅', {
        message: `${newAlert.ticker} için alert aktif`,
        sound: true
      });
    } catch (error) {
      console.error('Error creating alert:', error);
      alert('Alert oluşturulamadı!');
    }
  };

  const handleDeleteAlert = async (alertId) => {
    try {
      await notificationService.deleteAlert(alertId);
      await loadAlerts();
    } catch (error) {
      console.error('Error deleting alert:', error);
    }
  };

  const getAlertIcon = (type) => {
    switch (type) {
      case 'price': return '💰';
      case 'score': return '🎯';
      case 'signal': return '📈';
      default: return '🔔';
    }
  };

  const getAlertDescription = (alert) => {
    const { type, ticker, condition } = alert;
    
    if (type === 'price') {
      if (condition.price_above) {
        return `${ticker} > ${condition.price_above}₺`;
      } else if (condition.price_below) {
        return `${ticker} < ${condition.price_below}₺`;
      }
    } else if (type === 'score') {
      return `${ticker} score > ${condition.score_above}`;
    } else if (type === 'signal') {
      return `${ticker} BUY sinyali`;
    }
    
    return ticker;
  };

  return (
    <div className="bg-dark-card rounded-lg p-6 border border-dark-border">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-xl font-semibold flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Alertler
          </h3>
          <p className="text-sm text-gray-400 mt-1">
            {alerts.length} aktif alert
          </p>
        </div>

        <div className="flex gap-2">
          {!permissionGranted && (
            <button
              onClick={requestPermission}
              className="px-3 py-2 bg-yellow-600 hover:bg-yellow-700 rounded-lg text-sm transition-colors flex items-center gap-2"
            >
              <Bell className="w-4 h-4" />
              Bildirimleri Aç
            </button>
          )}
          
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="px-3 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg text-sm transition-colors flex items-center gap-2"
          >
            {showCreateForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
            {showCreateForm ? 'İptal' : 'Yeni Alert'}
          </button>
        </div>
      </div>

      {/* Permission Warning */}
      {!permissionGranted && (
        <div className="mb-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
          <p className="text-sm text-yellow-400">
            ⚠️ Browser bildirimleri kapalı. Alertleri almak için bildirimleri açın.
          </p>
        </div>
      )}

      {/* Create Form */}
      {showCreateForm && (
        <form onSubmit={handleCreateAlert} className="mb-6 p-4 bg-dark-bg rounded-lg border border-dark-border">
          <h4 className="text-lg font-semibold mb-4">Yeni Alert Oluştur</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Alert Type */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Alert Tipi</label>
              <select
                value={newAlert.type}
                onChange={(e) => setNewAlert({...newAlert, type: e.target.value})}
                className="w-full bg-dark-card border border-dark-border rounded px-3 py-2"
              >
                <option value="score">Score Alert (Momentum)</option>
                <option value="price">Price Alert (Fiyat)</option>
                <option value="signal">Signal Alert (BUY sinyali)</option>
              </select>
            </div>

            {/* Ticker */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Hisse</label>
              <select
                value={newAlert.ticker}
                onChange={(e) => setNewAlert({...newAlert, ticker: e.target.value})}
                className="w-full bg-dark-card border border-dark-border rounded px-3 py-2"
                required
              >
                <option value="THYAO.IS">THYAO - Türk Hava Yolları</option>
                <option value="AKBNK.IS">AKBNK - Akbank</option>
                <option value="GARAN.IS">GARAN - Garanti Bankası</option>
                <option value="ISCTR.IS">ISCTR - İş Bankası (C)</option>
                <option value="SAHOL.IS">SAHOL - Sabancı Holding</option>
                <option value="PETKM.IS">PETKM - Petkim</option>
                <option value="TUPRS.IS">TUPRS - Tüpraş</option>
                <option value="EREGL.IS">EREGL - Ereğli Demir Çelik</option>
                <option value="ASELS.IS">ASELS - Aselsan</option>
                <option value="KCHOL.IS">KCHOL - Koç Holding</option>
              </select>
            </div>

            {/* Condition based on type */}
            {newAlert.type === 'score' && (
              <div>
                <label className="block text-sm text-gray-400 mb-2">Minimum Skor</label>
                <input
                  type="number"
                  value={newAlert.scoreAbove}
                  onChange={(e) => setNewAlert({...newAlert, scoreAbove: e.target.value})}
                  min="0"
                  max="100"
                  className="w-full bg-dark-card border border-dark-border rounded px-3 py-2"
                  required
                />
              </div>
            )}

            {newAlert.type === 'price' && (
              <>
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Fiyat Üstü (₺)</label>
                  <input
                    type="number"
                    value={newAlert.priceAbove}
                    onChange={(e) => setNewAlert({...newAlert, priceAbove: e.target.value, priceBelow: ''})}
                    step="0.01"
                    placeholder="450.00"
                    className="w-full bg-dark-card border border-dark-border rounded px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Fiyat Altı (₺)</label>
                  <input
                    type="number"
                    value={newAlert.priceBelow}
                    onChange={(e) => setNewAlert({...newAlert, priceBelow: e.target.value, priceAbove: ''})}
                    step="0.01"
                    placeholder="400.00"
                    className="w-full bg-dark-card border border-dark-border rounded px-3 py-2"
                  />
                </div>
              </>
            )}

            {/* Sound */}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="sound"
                checked={newAlert.sound}
                onChange={(e) => setNewAlert({...newAlert, sound: e.target.checked})}
                className="w-4 h-4"
              />
              <label htmlFor="sound" className="text-sm text-gray-400">
                🔊 Ses ile bildir
              </label>
            </div>
          </div>

          <button
            type="submit"
            className="mt-4 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
          >
            Alert Oluştur
          </button>
        </form>
      )}

      {/* Alerts List */}
      {loading ? (
        <p className="text-gray-400 text-center py-4">Yükleniyor...</p>
      ) : alerts.length === 0 ? (
        <p className="text-gray-400 text-center py-8">
          Henüz alert oluşturmadınız. Yukarıdan "Yeni Alert" butonuna tıklayın.
        </p>
      ) : (
        <div className="space-y-2">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className="p-4 bg-dark-bg rounded-lg border border-dark-border hover:border-primary-500/50 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{getAlertIcon(alert.type)}</span>
                  <div>
                    <p className="font-medium">{getAlertDescription(alert)}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(alert.created_at).toLocaleString('tr-TR')}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {alert.notification.sound && (
                    <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded">
                      🔊 Ses
                    </span>
                  )}
                  <button
                    onClick={() => handleDeleteAlert(alert.id)}
                    className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded transition-colors"
                    title="Sil"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AlertPanel;
