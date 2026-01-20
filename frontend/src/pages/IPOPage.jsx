/**
 * IPO Page - Halka Arz Sayfası
 */
import React, { useState, useEffect, useCallback } from "react";
import {
  Rocket,
  Calendar,
  TrendingUp,
  TrendingDown,
  Clock,
  DollarSign,
  Users,
  Star,
  StarOff,
  Filter,
  BarChart3,
  ArrowRight,
  Bell,
  Calculator,
  ExternalLink,
  Building2,
  Percent,
  Layers,
  Settings,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Search,
  GitCompare,
  Grid3x3,
  List,
  Target,
  Sparkles,
  Award,
  PieChart as PieChartIcon,
} from "lucide-react";
import IPOAdminPanel from "../components/IPO/IPOAdminPanel";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import MobileIPOPage from "./mobile/MobileIPOPage";

// Mobile detection hook
const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState(
    typeof window !== 'undefined' ? window.innerWidth < 1024 : false
  );
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 1024);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  return isMobile;
};

const API_URL = "http://localhost:8000/api";

const COLORS = ["#3b82f6", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981", "#ef4444"];

// Status badge renkleri
const statusColors = {
  upcoming: "bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300",
  active:
    "bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300",
  completed:
    "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300",
  trading:
    "bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-300",
  cancelled: "bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300",
};

const statusLabels = {
  upcoming: "Yaklaşan",
  active: "Talep Toplama",
  completed: "Tamamlandı",
  trading: "İşlem Görüyor",
  cancelled: "İptal",
};

export default function IPOPage() {
  const isMobile = useIsMobile();
  
  // Early return for mobile view
  if (isMobile) {
    return <MobileIPOPage />;
  }

  const [ipos, setIpos] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [selectedIPO, setSelectedIPO] = useState(null);
  const [watchlist, setWatchlist] = useState([]);
  const [calcModal, setCalcModal] = useState(null);
  const [lotCount, setLotCount] = useState(1);
  const [calcResult, setCalcResult] = useState(null);
  const [showAdminPanel, setShowAdminPanel] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshResult, setRefreshResult] = useState(null);
  


  // Kullanıcı ID (gerçek uygulamada auth'dan gelir)
  const userId = "demo_user_123";

  // Auto refresh interval (60 saniye)
  const AUTO_REFRESH_INTERVAL = 60000;

  const fetchData = useCallback(async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const [iposRes, statsRes] = await Promise.all([
        fetch(`${API_URL}/ipo/`),
        fetch(`${API_URL}/ipo/stats`),
      ]);

      const iposData = await iposRes.json();
      const statsData = await statsRes.json();

      if (iposData.success) setIpos(iposData.ipos);
      if (statsData.success) {
        setStats(statsData.stats);
        if (statsData.stats.last_update) {
          setLastUpdate(new Date(statsData.stats.last_update));
        }
      }
    } catch (error) {
      console.error("Error fetching IPO data:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshFromWeb = async () => {
    setRefreshing(true);
    setRefreshResult(null);
    try {
      const res = await fetch(`${API_URL}/ipo/admin/refresh`, {
        method: "POST",
      });
      const data = await res.json();

      if (data.success) {
        setRefreshResult({
          success: data.result?.success,
          message: data.result?.success
            ? `${data.result.ipos_found} IPO güncellendi`
            : data.result?.errors?.[0] || "Güncelleme tamamlandı",
          iposFound: data.result?.ipos_found || 0,
        });
        // Verileri yeniden yükle
        await fetchData(false);
      }
    } catch (error) {
      console.error("Error refreshing IPO data:", error);
      setRefreshResult({
        success: false,
        message: "Güncelleme hatası",
      });
    } finally {
      setRefreshing(false);
      // 5 saniye sonra mesajı temizle
      setTimeout(() => setRefreshResult(null), 5000);
    }
  };

  useEffect(() => {
    fetchData();
    fetchWatchlist();

    // Auto refresh
    const interval = setInterval(() => {
      fetchData(false);
    }, AUTO_REFRESH_INTERVAL);

    return () => clearInterval(interval);
  }, [fetchData]);

  const fetchWatchlist = async () => {
    try {
      const res = await fetch(`${API_URL}/ipo/watchlist/${userId}`);
      const data = await res.json();
      if (data.success) {
        setWatchlist(data.ipos.map((ipo) => ipo.id));
      }
    } catch (error) {
      console.error("Error fetching watchlist:", error);
    }
  };

  const toggleWatchlist = async (ipoId) => {
    try {
      const isInWatchlist = watchlist.includes(ipoId);
      if (isInWatchlist) {
        await fetch(`${API_URL}/ipo/${ipoId}/watchlist?user_id=${userId}`, {
          method: "DELETE",
        });
        setWatchlist(watchlist.filter((id) => id !== ipoId));
      } else {
        await fetch(`${API_URL}/ipo/${ipoId}/watchlist`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId }),
        });
        setWatchlist([...watchlist, ipoId]);
      }
    } catch (error) {
      console.error("Error toggling watchlist:", error);
    }
  };

  const calculateInvestment = async (ipoId) => {
    try {
      const res = await fetch(`${API_URL}/ipo/${ipoId}/calculate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lot_count: lotCount }),
      });
      const data = await res.json();
      if (data.success) {
        setCalcResult(data.calculation);
      }
    } catch (error) {
      console.error("Error calculating investment:", error);
    }
  };

  const formatMoney = (value) => {
    if (value >= 1e9) return `₺${(value / 1e9).toFixed(2)} Milyar`;
    if (value >= 1e6) return `₺${(value / 1e6).toFixed(2)} Milyon`;
    return `₺${value.toLocaleString("tr-TR")}`;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString("tr-TR", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  };

  // IPO durumunu tarih bazlı hesapla
  const getIPOStatus = (ipo) => {
    const now = new Date();
    const demandStart = ipo.demand_start ? new Date(ipo.demand_start) : null;
    const demandEnd = ipo.demand_end ? new Date(ipo.demand_end) : null;
    const tradingStart = ipo.trading_start ? new Date(ipo.trading_start) : null;
    
    // İşlem görüyorsa
    if (ipo.status === 'trading' || (tradingStart && tradingStart <= now)) {
      return { label: 'İşlem Görüyor', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-300' };
    }
    
    // Talep toplama tamamlandıysa
    if (demandEnd && demandEnd < now && (!tradingStart || tradingStart > now)) {
      return { label: 'Talep Toplama Tamamlandı', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/50 dark:text-yellow-300' };
    }
    
    // Talep toplama devam ediyorsa
    if (demandStart && demandEnd && demandStart <= now && demandEnd >= now) {
      return { label: 'Talep Toplama Devam Ediyor', color: 'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300' };
    }
    
    // Yaklaşan
    if (demandStart && demandStart > now) {
      return { label: 'Yaklaşan', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300' };
    }
    
    return { label: statusLabels[ipo.status] || 'Bilinmiyor', color: statusColors[ipo.status] || 'bg-slate-100 text-slate-700' };
  };

  // Tüm IPO'ları tarihe göre sırala
  const displayIPOs = ipos
    .sort((a, b) => new Date(b.demand_start) - new Date(a.demand_start));

  const filteredIPOs = displayIPOs
    .filter((ipo) => {
      if (filter === "all") return true;
      if (filter === "watchlist") return watchlist.includes(ipo.id);
      return ipo.status === filter;
    });

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-3 sm:space-y-4 md:space-y-6">
      {/* Admin Panel */}
      <IPOAdminPanel
        isOpen={showAdminPanel}
        onClose={() => setShowAdminPanel(false)}
        onUpdate={fetchData}
      />

      {/* Page Header with Admin Button */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-lg sm:text-xl md:text-2xl font-bold flex items-center gap-2">
            <Rocket className="w-5 h-5 sm:w-6 sm:h-6 text-blue-500" />
            Halka Arz Merkezi
          </h1>
          {lastUpdate && (
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Son güncelleme: {lastUpdate.toLocaleString("tr-TR")}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* Refresh Result Message */}
          {refreshResult && (
            <div
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
                refreshResult.success
                  ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                  : "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
              }`}
            >
              {refreshResult.success ? (
                <CheckCircle size={16} />
              ) : (
                <AlertCircle size={16} />
              )}
              {refreshResult.message}
            </div>
          )}

          {/* Refresh Button */}
          <button
            onClick={refreshFromWeb}
            disabled={refreshing}
            className={`flex items-center gap-2 px-4 py-2 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors ${
              refreshing ? "opacity-50 cursor-not-allowed" : ""
            }`}
          >
            <RefreshCw size={18} className={refreshing ? "animate-spin" : ""} />
            <span className="hidden sm:inline">
              {refreshing ? "Güncelleniyor..." : "Güncelle"}
            </span>
          </button>

          {/* Admin Button */}
          <button
            onClick={() => setShowAdminPanel(true)}
            className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-700 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
          >
            <Settings size={18} />
            <span className="hidden sm:inline">Yönetim</span>
          </button>
        </div>
      </div>

      {/* Aktif Halka Arzlar Section */}
      <div>
        <h2 className="text-lg sm:text-xl font-bold text-slate-800 dark:text-white mb-3 sm:mb-4 flex items-center gap-2">
          <Rocket size={20} className="sm:w-6 sm:h-6 text-green-500" />
          Aktif Halka Arzlar
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4 md:gap-6">
        {displayIPOs
          .filter((i) => {
            // İşlem görmeyen ve henüz tamamlanmamış olanları göster
            if (i.status === "trading") return false;
            // trading_start varsa ve bugünden önceyse gösterme
            if (i.trading_start) {
              const tradingStart = new Date(i.trading_start);
              if (tradingStart <= new Date()) return false;
            }
            return true;
          })
          .map((ipo) => (
            <div
              key={ipo.id}
              className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg overflow-hidden border border-slate-200 dark:border-slate-700"
            >
              {/* Header */}
              <div className="p-3 sm:p-4 md:p-5 border-b border-slate-100 dark:border-slate-700">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg">
                      {ipo.symbol.substring(0, 2)}
                    </div>
                    <div>
                      <h3 className="font-bold text-base text-slate-800 dark:text-white">
                        {ipo.name}
                      </h3>
                      <span className="text-xs font-mono text-blue-600 dark:text-blue-400">
                        {ipo.symbol}
                      </span>
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getIPOStatus(ipo).color}`}>
                    {getIPOStatus(ipo).label}
                  </span>
                </div>
              </div>

              {/* Body */}
              <div className="p-3 sm:p-4 md:p-5 space-y-2 sm:space-y-3">
                {/* Halka Arz Tarihi */}
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500 dark:text-slate-400">Halka Arz Tarihi</span>
                  <span className="font-medium text-slate-800 dark:text-white">
                    {formatDate(ipo.demand_start)} - {formatDate(ipo.demand_end)}
                  </span>
                </div>

                {/* Halka Arz Fiyatı */}
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500 dark:text-slate-400">Halka Arz Fiyatı(Aralığı)</span>
                  <span className="font-medium text-slate-800 dark:text-white">
                    ₺{ipo.final_price
                      ? ipo.final_price.toFixed(2)
                      : `${ipo.price_range_min?.toFixed(2) || "0"} - ${ipo.price_range_max?.toFixed(2) || "0"}`}
                  </span>
                </div>

                {/* Dağıtım Yöntemi */}
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500 dark:text-slate-400">Dağıtım Yöntemi</span>
                  <span className="font-medium text-slate-800 dark:text-white">
                    {ipo.distribution_method || "Eşit Dağıtım"}
                  </span>
                </div>

                {/* Aracı Kurum */}
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500 dark:text-slate-400">Aracı Kurum</span>
                  <span className="font-medium text-slate-800 dark:text-white">
                    {ipo.lead_manager || "Kuvveyt Türk Yatırım"}
                  </span>
                </div>

                {/* BIST Kodu */}
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500 dark:text-slate-400">BIST Kodu</span>
                  <span className="font-medium text-slate-800 dark:text-white">
                    {ipo.symbol}
                  </span>
                </div>

                {/* Pazar */}
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500 dark:text-slate-400">Pazar</span>
                  <span className="font-medium text-slate-800 dark:text-white">
                    {ipo.market || "Ana Pazar"}
                  </span>
                </div>
              </div>

              {/* Footer Button */}
              <div className="px-5 py-4 bg-slate-50 dark:bg-slate-700/30 border-t border-slate-100 dark:border-slate-700">
                <button
                  onClick={() => setSelectedIPO(ipo)}
                  className="w-full py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition-colors text-sm flex items-center justify-center gap-2"
                >
                  Detayları Görüntüle <ArrowRight size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Geçmiş Halka Arzlar Section */}
      <div>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 mb-3 sm:mb-4">
          <h2 className="text-base sm:text-lg md:text-xl font-bold text-slate-800 dark:text-white">
            Geçmiş Halka Arzlar
          </h2>
          <span className="text-sm text-green-500 flex items-center gap-1">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            Canlı veri: {displayIPOs.filter((i) => i.status !== "active").length} hisse
          </span>
        </div>

        {/* Table - Mobile: Horizontal scroll, Reduced padding */}
        <div className="bg-white dark:bg-slate-800 rounded-xl sm:rounded-2xl shadow-lg overflow-x-auto border border-slate-200 dark:border-slate-700 -mx-3 sm:mx-0">
          <table className="w-full min-w-[900px]">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-700/50">
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-800 dark:text-white">#</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-800 dark:text-white">HİSSE</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-800 dark:text-white">HALKA ARZ FİYATI</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-800 dark:text-white">FİYAT</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-800 dark:text-white">GÜNLÜK DEĞİŞİM</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-800 dark:text-white">HACİM</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-800 dark:text-white">ARZ BÜYÜKLÜĞÜ</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-800 dark:text-white">ARZ SONRASI GETİRİ</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-800 dark:text-white">İŞLEM TARİHİ</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-800 dark:text-white">TALEP TOPLAMA</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-800 dark:text-white">SATILACAK LOT</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-800 dark:text-white">DETAY</th>
              </tr>
            </thead>
            <tbody>
              {displayIPOs
                .filter((i) => {
                  // İşlem gören veya trading_start geçmiş olanları göster
                  if (i.status === "trading") return true;
                  if (i.trading_start) {
                    const tradingStart = new Date(i.trading_start);
                    if (tradingStart <= new Date()) return true;
                  }
                  return false;
                })
                .slice(0, 10)
                .map((ipo, idx) => (
                  <tr
                    key={ipo.id}
                    className="border-b border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                  >
                    <td className="px-6 py-4 text-sm text-slate-800 dark:text-white font-medium">#{idx + 1}</td>
                    <td className="px-6 py-4 text-sm">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                          {ipo.symbol.substring(0, 2)}
                        </div>
                        <span className="font-medium text-green-500">{ipo.symbol}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm font-medium text-slate-800 dark:text-white">
                      ₺{ipo.final_price?.toFixed(2) || ipo.price_range_min?.toFixed(2) || "0.00"}
                    </td>
                    <td className="px-6 py-4 text-sm font-medium text-slate-800 dark:text-white">
                      ₺{ipo.current_price?.toFixed(2) || "-"}
                    </td>
                    <td className="px-6 py-4 text-sm font-medium">
                      {ipo.daily_change_percent != null ? (
                        <span className={ipo.daily_change_percent >= 0 ? "text-green-600" : "text-red-600"}>
                          {ipo.daily_change_percent >= 0 ? "+" : ""}
                          {ipo.daily_change_percent.toFixed(2)}%
                        </span>
                      ) : ipo.price_change_percent != null ? (
                        <span className={ipo.price_change_percent >= 0 ? "text-green-600" : "text-red-600"}>
                          {ipo.price_change_percent >= 0 ? "+" : ""}
                          {ipo.price_change_percent.toFixed(2)}%
                        </span>
                      ) : (
                        "-"
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-800 dark:text-white">
                      {ipo.trading_volume ? `${(ipo.trading_volume / 1000000).toFixed(1)}M` : "-"}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-800 dark:text-white">
                      ₺{ipo.market_cap_estimate?.toLocaleString("tr-TR") || "-"}
                    </td>
                    <td className="px-6 py-4 text-sm font-medium">
                      {ipo.total_return_percent != null ? (
                        <span className={ipo.total_return_percent >= 0 ? "text-green-600" : "text-red-600"}>
                          {ipo.total_return_percent >= 0 ? "+" : ""}
                          {ipo.total_return_percent.toFixed(1)}%
                        </span>
                      ) : (
                        "-"
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-800 dark:text-white">
                      {formatDate(ipo.trading_start)}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-800 dark:text-white">
                      {formatDate(ipo.demand_start)} - {formatDate(ipo.demand_end)}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-800 dark:text-white">
                      {ipo.lot_size?.toLocaleString("tr-TR") || "-"}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <button
                        onClick={() => setSelectedIPO(ipo)}
                        className="px-3 py-1 bg-green-500 hover:bg-green-600 text-white rounded text-xs font-medium transition-colors"
                      >
                        Detay
                      </button>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Investment Calculator Modal */}
      {calcModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-800 rounded-2xl max-w-md w-full shadow-2xl">
            <div className="p-5 border-b border-slate-200 dark:border-slate-700">
              <h3 className="text-lg font-bold text-slate-800 dark:text-white">
                Yatırım Hesaplama - {calcModal.symbol}
              </h3>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-sm text-slate-600 dark:text-slate-400 mb-2">
                  Lot Sayısı
                </label>
                <input
                  type="number"
                  min="1"
                  value={lotCount}
                  onChange={(e) => setLotCount(parseInt(e.target.value) || 1)}
                  className="w-full px-4 py-3 rounded-xl bg-slate-100 dark:bg-slate-700 border-0 focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <button
                onClick={() => calculateInvestment(calcModal.id)}
                className="w-full py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700"
              >
                Hesapla
              </button>

              {calcResult && (
                <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Hisse Adedi</span>
                    <span className="font-medium">{calcResult.shares}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Min. Tutar</span>
                    <span className="font-medium">
                      ₺{calcResult.investment_min?.toLocaleString("tr-TR")}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Max. Tutar</span>
                    <span className="font-medium">
                      ₺{calcResult.investment_max?.toLocaleString("tr-TR")}
                    </span>
                  </div>
                </div>
              )}
            </div>
            <div className="p-5 border-t border-slate-200 dark:border-slate-700">
              <button
                onClick={() => setCalcModal(null)}
                className="w-full py-2 text-slate-600 dark:text-slate-300 hover:text-slate-800"
              >
                Kapat
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {selectedIPO && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="p-5 border-b border-slate-200 dark:border-slate-700 sticky top-0 bg-white dark:bg-slate-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-xl">
                    {selectedIPO.symbol.substring(0, 2)}
                  </div>
                  <div>
                    <h3 className="font-bold text-lg">{selectedIPO.name}</h3>
                    <span className="text-blue-600">{selectedIPO.symbol}</span>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedIPO(null)}
                  className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="p-5 space-y-6">
              <div>
                <h4 className="font-medium text-slate-800 dark:text-white mb-2">
                  Açıklama
                </h4>
                <p className="text-slate-600 dark:text-slate-400">
                  {selectedIPO.description || "Açıklama bulunmamaktadır."}
                </p>
              </div>

              {/* Fiyat Bilgileri */}
              <div>
                <h4 className="font-medium text-slate-800 dark:text-white mb-3">
                  Fiyat Bilgileri
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4">
                    <div className="text-sm text-slate-500">Halka Arz Fiyatı</div>
                    <div className="font-bold text-lg">
                      ₺{selectedIPO.final_price?.toFixed(2) || selectedIPO.price_range_min?.toFixed(2) || "-"}
                    </div>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4">
                    <div className="text-sm text-slate-500">Güncel Fiyat</div>
                    <div className="font-bold text-lg">
                      {selectedIPO.current_price ? `₺${selectedIPO.current_price.toFixed(2)}` : "İşlem Başlamadı"}
                    </div>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4">
                    <div className="text-sm text-slate-500">Günlük Değişim</div>
                    <div className={`font-bold text-lg ${selectedIPO.daily_change_percent > 0 ? 'text-green-600' : selectedIPO.daily_change_percent < 0 ? 'text-red-600' : ''}`}>
                      {selectedIPO.daily_change_percent != null 
                        ? `${selectedIPO.daily_change_percent >= 0 ? '+' : ''}${selectedIPO.daily_change_percent.toFixed(2)}%` 
                        : "-"}
                    </div>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4">
                    <div className="text-sm text-slate-500">Toplam Getiri</div>
                    <div className={`font-bold text-lg ${selectedIPO.total_return_percent > 0 ? 'text-green-600' : selectedIPO.total_return_percent < 0 ? 'text-red-600' : ''}`}>
                      {selectedIPO.total_return_percent != null 
                        ? `${selectedIPO.total_return_percent >= 0 ? '+' : ''}${selectedIPO.total_return_percent.toFixed(1)}%` 
                        : "-"}
                    </div>
                  </div>
                </div>
              </div>

              {/* Genel Bilgiler */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4">
                  <div className="text-sm text-slate-500">Sektör</div>
                  <div className="font-bold">{selectedIPO.sector || "-"}</div>
                </div>
                <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4">
                  <div className="text-sm text-slate-500">Dağıtım Yöntemi</div>
                  <div className="font-bold">
                    {selectedIPO.distribution_method || "-"}
                  </div>
                </div>
                <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4">
                  <div className="text-sm text-slate-500">Lot Adedi</div>
                  <div className="font-bold">
                    {selectedIPO.lot_size?.toLocaleString("tr-TR") || "-"}
                  </div>
                </div>
                <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4">
                  <div className="text-sm text-slate-500">Aracı Kurum</div>
                  <div className="font-bold">
                    {selectedIPO.lead_manager || "-"}
                  </div>
                </div>
                <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4">
                  <div className="text-sm text-slate-500">Piyasa Değeri</div>
                  <div className="font-bold">
                    {selectedIPO.market_cap_estimate 
                      ? `₺${(selectedIPO.market_cap_estimate / 1000000).toFixed(0)}M` 
                      : "-"}
                  </div>
                </div>
                <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4">
                  <div className="text-sm text-slate-500">İşlem Hacmi</div>
                  <div className="font-bold">
                    {selectedIPO.trading_volume 
                      ? `₺${(selectedIPO.trading_volume / 1000000).toFixed(1)}M` 
                      : "-"}
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-slate-800 dark:text-white mb-3">
                  Tarihler
                </h4>
                <div className="space-y-2">
                  <div className="flex justify-between py-2 border-b border-slate-100 dark:border-slate-700">
                    <span className="text-slate-500">Talep Başlangıç</span>
                    <span>{formatDate(selectedIPO.demand_start) || "-"}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-slate-100 dark:border-slate-700">
                    <span className="text-slate-500">Talep Bitiş</span>
                    <span>{formatDate(selectedIPO.demand_end) || "-"}</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-slate-500">İşlem Başlangıç</span>
                    <span>{formatDate(selectedIPO.trading_start) || "-"}</span>
                  </div>
                </div>
              </div>

              {selectedIPO.website && (
                <a
                  href={selectedIPO.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 w-full py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700"
                >
                  <ExternalLink size={18} />
                  Şirket Web Sitesi
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
