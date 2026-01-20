import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  X,
  Moon,
  Sun,
  Monitor,
  BarChart2,
  Calendar,
  Clock,
  Bell,
  Volume2,
  Mail,
  Globe,
  Smartphone,
  User,
  LogOut,
  Shield,
  Key,
  Trash2,
  AlertTriangle,
  Crown,
} from "lucide-react";
import { useTheme } from "../../context/ThemeContext";
import { useStore } from "../../store";
import { usePortfolioStore } from "../../store/portfolioStore";
import { useAuth } from "../../context/AuthContext";

const SettingsModal = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const { strategy, setStrategy, interval, setInterval, period, setPeriod } =
    useStore();
  const { user, logout, getUserInitials } = useAuth();
  const { settings, updateSettings } = usePortfolioStore();
  const [activeTab, setActiveTab] = useState("general");
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const handleLogout = () => {
    logout();
    onClose();
    navigate("/login");
  };

  if (!isOpen) return null;

  const tabs = [
    { id: "general", label: "Genel", icon: Monitor },
    { id: "notifications", label: "Bildirimler", icon: Bell },
    { id: "trading", label: "Al-Sat", icon: BarChart2 },
    { id: "account", label: "Hesap", icon: User },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Modal Window */}
      <div className="relative w-full max-w-lg bg-theme-card border border-theme-border rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-theme-border bg-theme-bg/50">
          <h2 className="text-xl font-bold text-theme-text flex items-center gap-2">
            <Monitor className="w-5 h-5 text-primary-500" />
            Ayarlar
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-theme-bg rounded-lg transition-colors text-theme-muted hover:text-theme-text"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-theme-border">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? "text-primary-500 border-b-2 border-primary-500 bg-primary-500/5"
                    : "text-theme-muted hover:text-theme-text hover:bg-theme-bg/50"
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 max-h-[60vh] overflow-y-auto">
          {/* General Tab */}
          {activeTab === "general" && (
            <>
              {/* Theme Toggle */}
              <div className="space-y-3">
                <label className="text-sm font-medium text-theme-muted flex items-center gap-2">
                  {theme === "dark" ? (
                    <Moon className="w-4 h-4" />
                  ) : (
                    <Sun className="w-4 h-4" />
                  )}
                  Görünüm Modu
                </label>
                <div className="flex gap-2">
                  <button
                    onClick={() => theme === "light" || toggleTheme()}
                    className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg transition-all ${
                      theme === "dark"
                        ? "bg-primary-500 text-white shadow-lg shadow-primary-500/20"
                        : "bg-theme-bg text-theme-muted hover:bg-theme-border"
                    }`}
                  >
                    <Moon className="w-4 h-4" />
                    Karanlık
                  </button>
                  <button
                    onClick={() => theme === "dark" || toggleTheme()}
                    className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg transition-all ${
                      theme === "light"
                        ? "bg-primary-500 text-white shadow-lg shadow-primary-500/20"
                        : "bg-theme-bg text-theme-muted hover:bg-theme-border"
                    }`}
                  >
                    <Sun className="w-4 h-4" />
                    Aydınlık
                  </button>
                </div>
              </div>

              {/* Language */}
              <div className="space-y-3">
                <label className="text-sm font-medium text-theme-muted flex items-center gap-2">
                  <Globe className="w-4 h-4" />
                  Dil
                </label>
                <select
                  value={settings?.language || "tr"}
                  onChange={(e) => updateSettings({ language: e.target.value })}
                  className="w-full bg-theme-bg border border-theme-border rounded-lg px-3 py-2.5 text-sm text-theme-text focus:outline-none focus:border-primary-500 transition-colors"
                >
                  <option value="tr">Türkçe</option>
                  <option value="en">English</option>
                </select>
              </div>

              {/* Auto Refresh */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-theme-muted flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    Otomatik Yenileme
                  </label>
                  <button
                    onClick={() =>
                      updateSettings({ autoRefresh: !settings?.autoRefresh })
                    }
                    className={`relative w-12 h-6 rounded-full transition-colors ${
                      settings?.autoRefresh
                        ? "bg-primary-500"
                        : "bg-theme-border"
                    }`}
                  >
                    <span
                      className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform ${
                        settings?.autoRefresh ? "translate-x-6" : ""
                      }`}
                    />
                  </button>
                </div>
                {settings?.autoRefresh && (
                  <select
                    value={settings?.refreshInterval || 30}
                    onChange={(e) =>
                      updateSettings({
                        refreshInterval: parseInt(e.target.value),
                      })
                    }
                    className="w-full bg-theme-bg border border-theme-border rounded-lg px-3 py-2.5 text-sm text-theme-text focus:outline-none focus:border-primary-500 transition-colors"
                  >
                    <option value="10">10 saniye</option>
                    <option value="30">30 saniye</option>
                    <option value="60">1 dakika</option>
                    <option value="300">5 dakika</option>
                  </select>
                )}
              </div>
            </>
          )}

          {/* Notifications Tab */}
          {activeTab === "notifications" && (
            <>
              {/* Enable Notifications */}
              <div className="flex items-center justify-between p-4 rounded-xl bg-theme-bg">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-primary-500/20 flex items-center justify-center">
                    <Bell className="w-5 h-5 text-primary-500" />
                  </div>
                  <div>
                    <p className="font-medium text-theme-text">Bildirimler</p>
                    <p className="text-xs text-theme-muted">
                      Fiyat uyarıları ve sinyaller
                    </p>
                  </div>
                </div>
                <button
                  onClick={() =>
                    updateSettings({ notifications: !settings?.notifications })
                  }
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    settings?.notifications
                      ? "bg-primary-500"
                      : "bg-theme-border"
                  }`}
                >
                  <span
                    className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform ${
                      settings?.notifications ? "translate-x-6" : ""
                    }`}
                  />
                </button>
              </div>

              {/* Sound Alerts */}
              <div className="flex items-center justify-between p-4 rounded-xl bg-theme-bg">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
                    <Volume2 className="w-5 h-5 text-blue-500" />
                  </div>
                  <div>
                    <p className="font-medium text-theme-text">Ses Uyarıları</p>
                    <p className="text-xs text-theme-muted">
                      Önemli olaylarda sesli uyarı
                    </p>
                  </div>
                </div>
                <button
                  onClick={() =>
                    updateSettings({ soundAlerts: !settings?.soundAlerts })
                  }
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    settings?.soundAlerts ? "bg-primary-500" : "bg-theme-border"
                  }`}
                >
                  <span
                    className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform ${
                      settings?.soundAlerts ? "translate-x-6" : ""
                    }`}
                  />
                </button>
              </div>

              {/* Push Notifications */}
              <div className="flex items-center justify-between p-4 rounded-xl bg-theme-bg">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-green-500/20 flex items-center justify-center">
                    <Smartphone className="w-5 h-5 text-green-500" />
                  </div>
                  <div>
                    <p className="font-medium text-theme-text">
                      Push Bildirimi
                    </p>
                    <p className="text-xs text-theme-muted">
                      Tarayıcı bildirimleri
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    if (
                      !settings?.pushNotifications &&
                      "Notification" in window
                    ) {
                      Notification.requestPermission().then((permission) => {
                        if (permission === "granted") {
                          updateSettings({ pushNotifications: true });
                        }
                      });
                    } else {
                      updateSettings({
                        pushNotifications: !settings?.pushNotifications,
                      });
                    }
                  }}
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    settings?.pushNotifications
                      ? "bg-primary-500"
                      : "bg-theme-border"
                  }`}
                >
                  <span
                    className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform ${
                      settings?.pushNotifications ? "translate-x-6" : ""
                    }`}
                  />
                </button>
              </div>

              {/* Price Alert Threshold */}
              <div className="space-y-3">
                <label className="text-sm font-medium text-theme-muted">
                  Fiyat Uyarı Eşiği (%)
                </label>
                <input
                  type="number"
                  value={settings?.priceAlertThreshold || 5}
                  onChange={(e) =>
                    updateSettings({
                      priceAlertThreshold: parseFloat(e.target.value),
                    })
                  }
                  className="w-full bg-theme-bg border border-theme-border rounded-lg px-3 py-2.5 text-sm text-theme-text focus:outline-none focus:border-primary-500 transition-colors"
                  min="1"
                  max="50"
                  step="0.5"
                />
                <p className="text-xs text-theme-muted">
                  Fiyat bu yüzde kadar değiştiğinde bildirim alın
                </p>
              </div>
            </>
          )}

          {/* Trading Tab */}
          {activeTab === "trading" && (
            <>
              {/* Strategy Section */}
              <div className="space-y-3">
                <label className="text-sm font-medium text-theme-muted flex items-center gap-2">
                  <BarChart2 className="w-4 h-4 text-primary-400" />
                  Al-Sat Stratejisi
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    {
                      id: "conservative",
                      label: "Muhafazakâr",
                      desc: "Düşük risk",
                    },
                    { id: "moderate", label: "Dengeli", desc: "Orta risk" },
                    { id: "aggressive", label: "Agresif", desc: "Yüksek risk" },
                  ].map((opt) => (
                    <button
                      key={opt.id}
                      onClick={() => setStrategy(opt.id)}
                      className={`p-3 rounded-lg text-center transition-all ${
                        strategy === opt.id
                          ? "bg-primary-500 text-white shadow-lg shadow-primary-500/20"
                          : "bg-theme-bg text-theme-muted hover:bg-theme-border hover:text-theme-text"
                      }`}
                    >
                      <span className="text-sm font-medium block">
                        {opt.label}
                      </span>
                      <span className="text-xs opacity-70">{opt.desc}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Time Settings */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-theme-muted flex items-center gap-2">
                    <Clock className="w-4 h-4 text-blue-400" />
                    Zaman Aralığı
                  </label>
                  <select
                    value={interval}
                    onChange={(e) => setInterval(e.target.value)}
                    className="w-full bg-theme-bg border border-theme-border rounded-lg px-3 py-2.5 text-sm text-theme-text focus:outline-none focus:border-primary-500 transition-colors"
                  >
                    <option value="1m">1 Dakika</option>
                    <option value="5m">5 Dakika</option>
                    <option value="15m">15 Dakika</option>
                    <option value="30m">30 Dakika</option>
                    <option value="1h">1 Saat</option>
                    <option value="1d">1 Gün</option>
                    <option value="1wk">1 Hafta</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-theme-muted flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-purple-400" />
                    Geçmiş Veri
                  </label>
                  <select
                    value={period}
                    onChange={(e) => setPeriod(e.target.value)}
                    className="w-full bg-theme-bg border border-theme-border rounded-lg px-3 py-2.5 text-sm text-theme-text focus:outline-none focus:border-primary-500 transition-colors"
                  >
                    <option value="1d">1 Gün</option>
                    <option value="5d">5 Gün</option>
                    <option value="1mo">1 Ay</option>
                    <option value="3mo">3 Ay</option>
                    <option value="6mo">6 Ay</option>
                    <option value="1y">1 Yıl</option>
                    <option value="max">Tümü</option>
                  </select>
                </div>
              </div>
            </>
          )}

          {/* Account Tab */}
          {activeTab === "account" && (
            <>
              {/* Profile Info */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-theme-text flex items-center gap-2">
                  <User className="w-4 h-4 text-primary-500" />
                  Profil Bilgileri
                </h3>
                <div className="p-4 bg-theme-bg rounded-xl border border-theme-border">
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-400 via-primary-500 to-accent-500 flex items-center justify-center text-white font-bold text-2xl shadow-lg shadow-primary-500/20">
                      {getUserInitials()}
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-theme-text">
                        {user?.fullName || "Misafir"}
                      </p>
                      <p className="text-sm text-theme-muted">
                        {user?.email || "email@example.com"}
                      </p>
                      <div className="flex items-center gap-1 mt-1">
                        {user?.membership === "Pro" ? (
                          <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-gradient-to-r from-yellow-500/20 to-orange-500/20 text-yellow-400 border border-yellow-500/20 flex items-center gap-1">
                            <Crown className="w-3 h-3" />
                            Pro Üyelik
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-gradient-to-r from-primary-500/20 to-accent-500/20 text-primary-400 border border-primary-500/20">
                            Ücretsiz Üyelik
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Security */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-theme-text flex items-center gap-2">
                  <Shield className="w-4 h-4 text-green-500" />
                  Güvenlik
                </h3>
                <div className="space-y-3">
                  <button
                    onClick={() => {
                      onClose();
                      navigate("/profile");
                    }}
                    className="w-full flex items-center justify-between p-4 bg-theme-bg rounded-xl border border-theme-border hover:border-primary-500/30 transition-colors group"
                  >
                    <div className="flex items-center gap-3">
                      <Key className="w-5 h-5 text-theme-muted group-hover:text-primary-500 transition-colors" />
                      <div className="text-left">
                        <p className="text-sm font-medium text-theme-text">
                          Şifre Değiştir
                        </p>
                        <p className="text-xs text-theme-muted">
                          Hesap şifrenizi güncelleyin
                        </p>
                      </div>
                    </div>
                    <span className="text-theme-muted">→</span>
                  </button>

                  <button
                    onClick={() => {
                      onClose();
                      navigate("/profile");
                    }}
                    className="w-full flex items-center justify-between p-4 bg-theme-bg rounded-xl border border-theme-border hover:border-primary-500/30 transition-colors group"
                  >
                    <div className="flex items-center gap-3">
                      <Smartphone
                        className={`w-5 h-5 ${user?.twoFactorEnabled ? "text-green-400" : "text-theme-muted"} group-hover:text-primary-500 transition-colors`}
                      />
                      <div className="text-left">
                        <p className="text-sm font-medium text-theme-text">
                          İki Faktörlü Doğrulama
                        </p>
                        <p className="text-xs text-theme-muted">
                          Ekstra güvenlik katmanı ekleyin
                        </p>
                      </div>
                    </div>
                    <span
                      className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                        user?.twoFactorEnabled
                          ? "bg-green-500/20 text-green-400"
                          : "bg-theme-bg-secondary text-theme-muted"
                      }`}
                    >
                      {user?.twoFactorEnabled ? "Açık" : "Kapalı"}
                    </span>
                  </button>
                </div>
              </div>

              {/* Danger Zone */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-red-400 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  Tehlikeli Bölge
                </h3>
                <div className="space-y-3">
                  {/* Logout Button */}
                  {!showLogoutConfirm ? (
                    <button
                      onClick={() => setShowLogoutConfirm(true)}
                      className="w-full flex items-center justify-between p-4 bg-red-500/10 rounded-xl border border-red-500/20 hover:bg-red-500/20 hover:border-red-500/30 transition-colors group"
                    >
                      <div className="flex items-center gap-3">
                        <LogOut className="w-5 h-5 text-red-400" />
                        <div className="text-left">
                          <p className="text-sm font-medium text-red-400">
                            Hesaptan Çıkış Yap
                          </p>
                          <p className="text-xs text-red-400/70">
                            Oturumunuzu sonlandırın
                          </p>
                        </div>
                      </div>
                      <span className="text-red-400">→</span>
                    </button>
                  ) : (
                    <div className="p-4 bg-red-500/10 rounded-xl border border-red-500/30 space-y-3">
                      <p className="text-sm text-red-400 font-medium">
                        Çıkış yapmak istediğinizden emin misiniz?
                      </p>
                      <div className="flex gap-2">
                        <button
                          onClick={() => setShowLogoutConfirm(false)}
                          className="flex-1 px-4 py-2 bg-theme-bg border border-theme-border rounded-lg text-sm font-medium text-theme-text hover:bg-theme-bg-secondary transition-colors"
                        >
                          İptal
                        </button>
                        <button
                          onClick={handleLogout}
                          className="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 rounded-lg text-sm font-medium text-white transition-colors flex items-center justify-center gap-2"
                        >
                          <LogOut className="w-4 h-4" />
                          Çıkış Yap
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Delete Account */}
                  <button className="w-full flex items-center justify-between p-4 bg-theme-bg rounded-xl border border-theme-border hover:border-red-500/30 transition-colors group opacity-50 cursor-not-allowed">
                    <div className="flex items-center gap-3">
                      <Trash2 className="w-5 h-5 text-theme-muted" />
                      <div className="text-left">
                        <p className="text-sm font-medium text-theme-text">
                          Hesabı Sil
                        </p>
                        <p className="text-xs text-theme-muted">
                          Hesabınızı kalıcı olarak silin
                        </p>
                      </div>
                    </div>
                    <span className="text-xs text-theme-muted">Yakında</span>
                  </button>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-theme-bg/50 border-t border-theme-border flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-theme-muted hover:text-theme-text font-medium rounded-lg transition-colors"
          >
            İptal
          </button>
          <button
            onClick={onClose}
            className="px-6 py-2 bg-primary-600 hover:bg-primary-500 text-white font-medium rounded-lg transition-colors shadow-lg shadow-primary-500/20"
          >
            Kaydet
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
