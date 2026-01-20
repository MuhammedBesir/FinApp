import React, { useState } from 'react';
import {
  Bell,
  Plus,
  TrendingUp,
  TrendingDown,
  Target,
  Zap,
  AlertTriangle,
  DollarSign,
  Activity,
  Save,
  X
} from 'lucide-react';
import { useNotifications } from '../../context/NotificationContext';

const AlertCreator = ({ ticker, currentPrice, onClose }) => {
  const { createAlert } = useNotifications();
  const [alertType, setAlertType] = useState('price');
  const [priority, setPriority] = useState('medium');
  const [condition, setCondition] = useState({});
  const [browserNotif, setBrowserNotif] = useState(true);
  const [soundNotif, setSoundNotif] = useState(true);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await createAlert({
        type: alertType,
        ticker: ticker,
        condition: condition,
        priority: priority,
        notification: {
          browser: browserNotif,
          sound: soundNotif
        }
      });

      if (onClose) onClose();
    } catch (error) {
      console.error('Alert oluşturulamadı:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass rounded-2xl border border-[var(--glass-border)] p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-primary/20 to-primary/10 rounded-xl">
            <Bell className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-theme-text">Yeni Alert</h3>
            <p className="text-sm text-theme-muted">{ticker}</p>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/5 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-theme-muted" />
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Alert Tipi */}
        <div>
          <label className="block text-sm font-medium text-theme-text mb-2">
            Alert Tipi
          </label>
          <div className="grid grid-cols-2 gap-2">
            {[
              { value: 'price', icon: DollarSign, label: 'Fiyat' },
              { value: 'score', icon: Activity, label: 'Skor' },
              { value: 'signal', icon: Zap, label: 'Sinyal' },
              { value: 'position', icon: Target, label: 'Pozisyon' }
            ].map(type => (
              <button
                key={type.value}
                type="button"
                onClick={() => {
                  setAlertType(type.value);
                  setCondition({});
                }}
                className={`p-3 rounded-xl border transition-all flex items-center gap-2 ${
                  alertType === type.value
                    ? 'bg-primary border-primary text-white'
                    : 'bg-white/5 border-[var(--glass-border)] text-theme-muted hover:bg-white/10'
                }`}
              >
                <type.icon className="w-5 h-5" />
                <span className="font-medium">{type.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Koşullar */}
        {alertType === 'price' && (
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-theme-text mb-2">
                Fiyat Koşulu
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setCondition({ price_above: currentPrice * 1.05 })}
                  className={`p-3 rounded-xl border transition-all ${
                    'price_above' in condition
                      ? 'bg-success/20 border-success text-success'
                      : 'bg-white/5 border-[var(--glass-border)] text-theme-muted hover:bg-white/10'
                  }`}
                >
                  <TrendingUp className="w-5 h-5 mx-auto mb-1" />
                  <div className="text-xs">Üstüne Çıkarsa</div>
                </button>
                <button
                  type="button"
                  onClick={() => setCondition({ price_below: currentPrice * 0.95 })}
                  className={`p-3 rounded-xl border transition-all ${
                    'price_below' in condition
                      ? 'bg-danger/20 border-danger text-danger'
                      : 'bg-white/5 border-[var(--glass-border)] text-theme-muted hover:bg-white/10'
                  }`}
                >
                  <TrendingDown className="w-5 h-5 mx-auto mb-1" />
                  <div className="text-xs">Altına Düşerse</div>
                </button>
              </div>
            </div>

            {Object.keys(condition).length > 0 && (
              <div>
                <label className="block text-sm font-medium text-theme-text mb-2">
                  Hedef Fiyat (₺)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={condition.price_above || condition.price_below || ''}
                  onChange={(e) => {
                    const value = parseFloat(e.target.value);
                    if ('price_above' in condition) {
                      setCondition({ price_above: value });
                    } else {
                      setCondition({ price_below: value });
                    }
                  }}
                  className="w-full px-4 py-3 bg-white/5 border border-[var(--glass-border)] rounded-xl text-theme-text focus:outline-none focus:border-primary transition-colors"
                  placeholder={currentPrice.toString()}
                  required
                />
                {currentPrice && (
                  <p className="text-xs text-theme-muted mt-1">
                    Mevcut fiyat: ₺{currentPrice.toFixed(2)}
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {alertType === 'score' && (
          <div>
            <label className="block text-sm font-medium text-theme-text mb-2">
              Momentum Skoru
            </label>
            <input
              type="number"
              min="0"
              max="100"
              value={condition.score_above || ''}
              onChange={(e) => setCondition({ score_above: parseInt(e.target.value) })}
              className="w-full px-4 py-3 bg-white/5 border border-[var(--glass-border)] rounded-xl text-theme-text focus:outline-none focus:border-primary transition-colors"
              placeholder="80"
              required
            />
            <p className="text-xs text-theme-muted mt-1">
              Skor bu değerin üstüne çıktığında bildirim gönder
            </p>
          </div>
        )}

        {alertType === 'signal' && (
          <div className="p-4 bg-accent-500/10 border border-accent-500/30 rounded-xl">
            <p className="text-sm text-theme-text">
              BUY sinyali oluştuğunda bildirim alacaksınız
            </p>
          </div>
        )}

        {/* Öncelik */}
        <div>
          <label className="block text-sm font-medium text-theme-text mb-2">
            Öncelik Seviyesi
          </label>
          <div className="grid grid-cols-4 gap-2">
            {[
              { value: 'low', label: 'Düşük', color: 'bg-blue-500/20 border-blue-500/50 text-blue-400' },
              { value: 'medium', label: 'Orta', color: 'bg-primary/20 border-primary/50 text-primary' },
              { value: 'high', label: 'Yüksek', color: 'bg-warning/20 border-warning/50 text-warning' },
              { value: 'critical', label: 'Kritik', color: 'bg-danger/20 border-danger/50 text-danger' }
            ].map(p => (
              <button
                key={p.value}
                type="button"
                onClick={() => setPriority(p.value)}
                className={`p-2 rounded-lg border transition-all text-xs font-medium ${
                  priority === p.value
                    ? p.color
                    : 'bg-white/5 border-[var(--glass-border)] text-theme-muted hover:bg-white/10'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Bildirim Ayarları */}
        <div>
          <label className="block text-sm font-medium text-theme-text mb-2">
            Bildirim Tercihleri
          </label>
          <div className="space-y-2">
            <label className="flex items-center gap-3 p-3 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors">
              <input
                type="checkbox"
                checked={browserNotif}
                onChange={(e) => setBrowserNotif(e.target.checked)}
                className="w-4 h-4 rounded border-gray-600 text-primary focus:ring-primary"
              />
              <span className="text-sm text-theme-text">Tarayıcı Bildirimi</span>
            </label>
            <label className="flex items-center gap-3 p-3 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors">
              <input
                type="checkbox"
                checked={soundNotif}
                onChange={(e) => setSoundNotif(e.target.checked)}
                className="w-4 h-4 rounded border-gray-600 text-primary focus:ring-primary"
              />
              <span className="text-sm text-theme-text">Ses Bildirimi</span>
            </label>
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading || Object.keys(condition).length === 0}
          className="btn btn-primary w-full flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
              Oluşturuluyor...
            </>
          ) : (
            <>
              <Save className="w-5 h-5" />
              Alert Oluştur
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default AlertCreator;
