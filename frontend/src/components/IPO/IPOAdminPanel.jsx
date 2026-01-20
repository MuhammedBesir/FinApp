/**
 * IPO Admin Panel - Halka Arz Yönetim Paneli
 * Manuel IPO ekleme, güncelleme ve yenileme işlemleri
 */
import React, { useState, useEffect } from "react";
import {
  Settings,
  RefreshCw,
  Plus,
  Save,
  X,
  Clock,
  CheckCircle,
  AlertCircle,
  Database,
  Wifi,
  WifiOff,
} from "lucide-react";

const API_URL = "http://localhost:8000/api";

// Boş IPO şablonu
const emptyIPO = {
  symbol: "",
  name: "",
  sector: "",
  description: "",
  ipo_type: "primary",
  status: "upcoming",
  price_range_min: "",
  price_range_max: "",
  final_price: "",
  lot_size: 100,
  min_lot: 1,
  shares_offered: "",
  total_shares: "",
  market_cap_estimate: "",
  demand_start: "",
  demand_end: "",
  allocation_date: "",
  trading_start: "",
  website: "",
  kap_url: "",
};

// Sektör listesi
const sectors = [
  "Teknoloji",
  "Fintech",
  "E-Ticaret",
  "Enerji",
  "Savunma",
  "Otomotiv",
  "Gıda",
  "Perakende",
  "Madencilik",
  "Sağlık",
  "İnşaat",
  "Tekstil",
  "Turizm",
  "Oyun",
  "Holding",
  "Ambalaj",
  "Diğer",
];

export default function IPOAdminPanel({ onUpdate, isOpen, onClose }) {
  const [status, setStatus] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newIPO, setNewIPO] = useState({ ...emptyIPO });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    if (isOpen) {
      fetchStatus();
    }
  }, [isOpen]);

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/ipo/admin/status`);
      const data = await res.json();
      if (data.success) {
        setStatus(data);
      }
    } catch (error) {
      console.error("Error fetching status:", error);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    setMessage(null);
    try {
      const res = await fetch(`${API_URL}/ipo/admin/refresh`, {
        method: "POST",
      });
      const data = await res.json();

      if (data.success) {
        setMessage({
          type: data.result?.success ? "success" : "warning",
          text: data.result?.success
            ? `${data.result.ipos_found} IPO bulundu, ${data.result.ipos_updated} güncellendi`
            : `Güncelleme tamamlandı. ${data.result?.errors?.join(", ") || "Veri bulunamadı"}`,
        });
        if (onUpdate) onUpdate();
        fetchStatus();
      }
    } catch (error) {
      setMessage({
        type: "error",
        text: "Güncelleme sırasında hata oluştu: " + error.message,
      });
    } finally {
      setRefreshing(false);
    }
  };

  const handleAddIPO = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);

    try {
      // Sayısal alanları dönüştür
      const ipoData = {
        ...newIPO,
        price_range_min: parseFloat(newIPO.price_range_min) || 0,
        price_range_max: parseFloat(newIPO.price_range_max) || 0,
        final_price: newIPO.final_price ? parseFloat(newIPO.final_price) : null,
        lot_size: parseInt(newIPO.lot_size) || 100,
        min_lot: parseInt(newIPO.min_lot) || 1,
        shares_offered: parseInt(newIPO.shares_offered) || 0,
        total_shares: parseInt(newIPO.total_shares) || 0,
        market_cap_estimate: parseFloat(newIPO.market_cap_estimate) || 0,
      };

      const res = await fetch(`${API_URL}/ipo/admin/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(ipoData),
      });
      const data = await res.json();

      if (data.success) {
        setMessage({
          type: "success",
          text: `${newIPO.name} başarıyla eklendi!`,
        });
        setNewIPO({ ...emptyIPO });
        setShowAddForm(false);
        if (onUpdate) onUpdate();
        fetchStatus();
      } else {
        setMessage({
          type: "error",
          text: data.detail || "IPO eklenirken hata oluştu",
        });
      }
    } catch (error) {
      setMessage({
        type: "error",
        text: "IPO eklenirken hata oluştu: " + error.message,
      });
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field, value) => {
    setNewIPO((prev) => ({ ...prev, [field]: value }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-blue-600 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Settings className="text-white" size={24} />
            <h2 className="text-xl font-bold text-white">IPO Yönetim Paneli</h2>
          </div>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
          {/* Mesaj */}
          {message && (
            <div
              className={`mb-4 p-4 rounded-lg flex items-center gap-2 ${
                message.type === "success"
                  ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300"
                  : message.type === "warning"
                    ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300"
                    : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"
              }`}
            >
              {message.type === "success" ? (
                <CheckCircle size={20} />
              ) : (
                <AlertCircle size={20} />
              )}
              {message.text}
            </div>
          )}

          {/* Durum Kartları */}
          {status && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-slate-100 dark:bg-slate-700 rounded-xl p-4">
                <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 mb-1">
                  <Database size={16} />
                  <span className="text-sm">Toplam IPO</span>
                </div>
                <div className="text-2xl font-bold">
                  {status.data_status?.ipo_count || 0}
                </div>
              </div>

              <div className="bg-slate-100 dark:bg-slate-700 rounded-xl p-4">
                <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 mb-1">
                  <Clock size={16} />
                  <span className="text-sm">Son Güncelleme</span>
                </div>
                <div className="text-sm font-medium">
                  {status.data_status?.last_update
                    ? new Date(status.data_status.last_update).toLocaleString(
                        "tr-TR",
                      )
                    : "-"}
                </div>
              </div>

              <div className="bg-slate-100 dark:bg-slate-700 rounded-xl p-4">
                <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 mb-1">
                  {status.scheduler_status?.is_running ? (
                    <Wifi size={16} className="text-green-500" />
                  ) : (
                    <WifiOff size={16} className="text-red-500" />
                  )}
                  <span className="text-sm">Otomatik Güncelleme</span>
                </div>
                <div className="text-sm font-medium">
                  {status.scheduler_status?.is_running ? "Aktif" : "Pasif"}
                </div>
              </div>

              <div className="bg-slate-100 dark:bg-slate-700 rounded-xl p-4">
                <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 mb-1">
                  <RefreshCw size={16} />
                  <span className="text-sm">Güncelleme Sayısı</span>
                </div>
                <div className="text-2xl font-bold">
                  {status.scheduler_status?.run_count || 0}
                </div>
              </div>
            </div>
          )}

          {/* Aksiyon Butonları */}
          <div className="flex flex-wrap gap-4 mb-6">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              <RefreshCw
                size={18}
                className={refreshing ? "animate-spin" : ""}
              />
              {refreshing ? "Güncelleniyor..." : "Web'den Güncelle"}
            </button>

            <button
              onClick={() => setShowAddForm(!showAddForm)}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              <Plus size={18} />
              Manuel IPO Ekle
            </button>
          </div>

          {/* Manuel IPO Ekleme Formu */}
          {showAddForm && (
            <form
              onSubmit={handleAddIPO}
              className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-6 space-y-4"
            >
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                <Plus size={20} />
                Yeni Halka Arz Ekle
              </h3>

              {/* Temel Bilgiler */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Borsa Kodu *
                  </label>
                  <input
                    type="text"
                    required
                    value={newIPO.symbol}
                    onChange={(e) =>
                      handleInputChange("symbol", e.target.value.toUpperCase())
                    }
                    placeholder="XXXXX"
                    className="w-full px-3 py-2 rounded-lg border dark:bg-slate-700 dark:border-slate-600"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">
                    Şirket Adı *
                  </label>
                  <input
                    type="text"
                    required
                    value={newIPO.name}
                    onChange={(e) => handleInputChange("name", e.target.value)}
                    placeholder="Şirket A.Ş."
                    className="w-full px-3 py-2 rounded-lg border dark:bg-slate-700 dark:border-slate-600"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">
                    Sektör *
                  </label>
                  <select
                    required
                    value={newIPO.sector}
                    onChange={(e) =>
                      handleInputChange("sector", e.target.value)
                    }
                    className="w-full px-3 py-2 rounded-lg border dark:bg-slate-700 dark:border-slate-600"
                  >
                    <option value="">Seçiniz...</option>
                    {sectors.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">
                    Halka Arz Türü
                  </label>
                  <select
                    value={newIPO.ipo_type}
                    onChange={(e) =>
                      handleInputChange("ipo_type", e.target.value)
                    }
                    className="w-full px-3 py-2 rounded-lg border dark:bg-slate-700 dark:border-slate-600"
                  >
                    <option value="primary">Birincil (Yeni Hisse)</option>
                    <option value="secondary">İkincil (Mevcut Satış)</option>
                    <option value="mixed">Karma</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">
                    Durum
                  </label>
                  <select
                    value={newIPO.status}
                    onChange={(e) =>
                      handleInputChange("status", e.target.value)
                    }
                    className="w-full px-3 py-2 rounded-lg border dark:bg-slate-700 dark:border-slate-600"
                  >
                    <option value="upcoming">Yaklaşan</option>
                    <option value="active">Talep Toplama</option>
                    <option value="trading">İşlem Görüyor</option>
                    <option value="completed">Tamamlandı</option>
                  </select>
                </div>
              </div>

              {/* Açıklama */}
              <div>
                <label className="block text-sm font-medium mb-1">
                  Açıklama
                </label>
                <textarea
                  value={newIPO.description}
                  onChange={(e) =>
                    handleInputChange("description", e.target.value)
                  }
                  placeholder="Şirket hakkında kısa bilgi..."
                  rows={2}
                  className="w-full px-3 py-2 rounded-lg border dark:bg-slate-700 dark:border-slate-600"
                />
              </div>

              {/* Fiyat Bilgileri */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Min Fiyat (₺)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={newIPO.price_range_min}
                    onChange={(e) =>
                      handleInputChange("price_range_min", e.target.value)
                    }
                    placeholder="0.00"
                    className="w-full px-3 py-2 rounded-lg border dark:bg-slate-700 dark:border-slate-600"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">
                    Max Fiyat (₺)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={newIPO.price_range_max}
                    onChange={(e) =>
                      handleInputChange("price_range_max", e.target.value)
                    }
                    placeholder="0.00"
                    className="w-full px-3 py-2 rounded-lg border dark:bg-slate-700 dark:border-slate-600"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">
                    Lot Büyüklüğü
                  </label>
                  <input
                    type="number"
                    value={newIPO.lot_size}
                    onChange={(e) =>
                      handleInputChange("lot_size", e.target.value)
                    }
                    placeholder="100"
                    className="w-full px-3 py-2 rounded-lg border dark:bg-slate-700 dark:border-slate-600"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">
                    Min Lot
                  </label>
                  <input
                    type="number"
                    value={newIPO.min_lot}
                    onChange={(e) =>
                      handleInputChange("min_lot", e.target.value)
                    }
                    placeholder="1"
                    className="w-full px-3 py-2 rounded-lg border dark:bg-slate-700 dark:border-slate-600"
                  />
                </div>
              </div>

              {/* Tarihler */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Talep Başlangıç
                  </label>
                  <input
                    type="datetime-local"
                    value={newIPO.demand_start}
                    onChange={(e) =>
                      handleInputChange("demand_start", e.target.value)
                    }
                    className="w-full px-3 py-2 rounded-lg border dark:bg-slate-700 dark:border-slate-600"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">
                    Talep Bitiş
                  </label>
                  <input
                    type="datetime-local"
                    value={newIPO.demand_end}
                    onChange={(e) =>
                      handleInputChange("demand_end", e.target.value)
                    }
                    className="w-full px-3 py-2 rounded-lg border dark:bg-slate-700 dark:border-slate-600"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">
                    Dağıtım Tarihi
                  </label>
                  <input
                    type="date"
                    value={newIPO.allocation_date}
                    onChange={(e) =>
                      handleInputChange("allocation_date", e.target.value)
                    }
                    className="w-full px-3 py-2 rounded-lg border dark:bg-slate-700 dark:border-slate-600"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">
                    İşlem Başlangıç
                  </label>
                  <input
                    type="date"
                    value={newIPO.trading_start}
                    onChange={(e) =>
                      handleInputChange("trading_start", e.target.value)
                    }
                    className="w-full px-3 py-2 rounded-lg border dark:bg-slate-700 dark:border-slate-600"
                  />
                </div>
              </div>

              {/* Linkler */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Web Sitesi
                  </label>
                  <input
                    type="url"
                    value={newIPO.website}
                    onChange={(e) =>
                      handleInputChange("website", e.target.value)
                    }
                    placeholder="https://..."
                    className="w-full px-3 py-2 rounded-lg border dark:bg-slate-700 dark:border-slate-600"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">
                    KAP Linki
                  </label>
                  <input
                    type="url"
                    value={newIPO.kap_url}
                    onChange={(e) =>
                      handleInputChange("kap_url", e.target.value)
                    }
                    placeholder="https://www.kap.org.tr/..."
                    className="w-full px-3 py-2 rounded-lg border dark:bg-slate-700 dark:border-slate-600"
                  />
                </div>
              </div>

              {/* Form Butonları */}
              <div className="flex gap-4 pt-4">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                >
                  <Save size={18} />
                  {saving ? "Kaydediliyor..." : "Kaydet"}
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setShowAddForm(false);
                    setNewIPO({ ...emptyIPO });
                  }}
                  className="px-6 py-2 bg-slate-200 dark:bg-slate-600 rounded-lg hover:bg-slate-300 dark:hover:bg-slate-500 transition-colors"
                >
                  İptal
                </button>
              </div>
            </form>
          )}

          {/* Scheduled Jobs */}
          {status?.scheduler_status?.jobs && (
            <div className="mt-6">
              <h3 className="text-lg font-bold mb-3">
                Zamanlanmış Güncellemeler
              </h3>
              <div className="space-y-2">
                {status.scheduler_status.jobs.map((job) => (
                  <div
                    key={job.id}
                    className="bg-slate-100 dark:bg-slate-700 rounded-lg p-3 flex items-center justify-between"
                  >
                    <div>
                      <div className="font-medium">{job.name}</div>
                      <div className="text-sm text-slate-500 dark:text-slate-400">
                        {job.trigger}
                      </div>
                    </div>
                    <div className="text-sm text-right">
                      <div className="text-slate-500 dark:text-slate-400">
                        Sonraki çalışma
                      </div>
                      <div className="font-medium">
                        {new Date(job.next_run).toLocaleString("tr-TR")}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Bilgi Notu */}
          <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-sm">
            <h4 className="font-medium text-blue-700 dark:text-blue-300 mb-2">
              ℹ️ Veri Kaynakları Hakkında
            </h4>
            <ul className="list-disc list-inside text-blue-600 dark:text-blue-400 space-y-1">
              <li>
                Web kaynakları (KAP, halkaarz.com) bazen bot koruması nedeniyle
                erişilemeyebilir
              </li>
              <li>
                Bu durumda "Manuel IPO Ekle" özelliğini kullanarak verileri
                girebilirsiniz
              </li>
              <li>
                Veriler otomatik olarak günde 3 kez (08:00, 18:30, 00:30)
                güncellenmeye çalışılır
              </li>
              <li>
                Tüm veriler sunucu yeniden başlatılsa bile korunur (JSON
                persistence)
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
