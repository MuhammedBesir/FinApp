/**
 * Header Component - Modern Glassmorphism Trading Dashboard
 * 🌙 Dark Mode | ✨ Glassmorphism | 📊 Real-time Data
 */
import React, { useState, useRef, useEffect, useMemo } from "react";
import {
  Search,
  Bell,
  Sun,
  Moon,
  Menu,
  ChevronDown,
  X,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Info,
  Sparkles,
  Zap,
} from "lucide-react";
import { useStore } from "../../store";
import { usePortfolioStore } from "../../store/portfolioStore";
import { useNotifications } from "../../context/NotificationContext";
import NotificationCenter from "../Notifications/NotificationCenter";

// BIST 30 + Altın
const STOCKS = [
  { value: "AKBNK.IS", label: "AKBNK", name: "Akbank" },
  { value: "AKSEN.IS", label: "AKSEN", name: "Aksa Enerji" },
  { value: "ARCLK.IS", label: "ARCLK", name: "Arçelik" },
  { value: "ASELS.IS", label: "ASELS", name: "Aselsan" },
  { value: "BIMAS.IS", label: "BIMAS", name: "BİM" },
  { value: "EKGYO.IS", label: "EKGYO", name: "Emlak Konut GYO" },
  { value: "ENKAI.IS", label: "ENKAI", name: "Enka İnşaat" },
  { value: "EREGL.IS", label: "EREGL", name: "Ereğli Demir Çelik" },
  { value: "FROTO.IS", label: "FROTO", name: "Ford Otosan" },
  { value: "GARAN.IS", label: "GARAN", name: "Garanti BBVA" },

  { value: "GUBRF.IS", label: "GUBRF", name: "Gübre Fabrikaları" },
  { value: "HEKTS.IS", label: "HEKTS", name: "Hektaş" },
  { value: "ISCTR.IS", label: "ISCTR", name: "İş Bankası C" },
  { value: "KCHOL.IS", label: "KCHOL", name: "Koç Holding" },
  { value: "KRDMD.IS", label: "KRDMD", name: "Kardemir D" },
  { value: "ODAS.IS", label: "ODAS", name: "Odaş Elektrik" },
  { value: "PETKM.IS", label: "PETKM", name: "Petkim" },
  { value: "PGSUS.IS", label: "PGSUS", name: "Pegasus" },
  { value: "SAHOL.IS", label: "SAHOL", name: "Sabancı Holding" },
  { value: "SASA.IS", label: "SASA", name: "Sasa Polyester" },
  { value: "SISE.IS", label: "SISE", name: "Şişecam" },
  { value: "TAVHL.IS", label: "TAVHL", name: "TAV Havalimanları" },
  { value: "TCELL.IS", label: "TCELL", name: "Turkcell" },
  { value: "THYAO.IS", label: "THYAO", name: "Türk Hava Yolları" },
  { value: "TKFEN.IS", label: "TKFEN", name: "Tekfen Holding" },
  { value: "TOASO.IS", label: "TOASO", name: "Tofaş" },
  { value: "TRALT.IS", label: "TRALT", name: "Türk Altın" },
  { value: "TUPRS.IS", label: "TUPRS", name: "Tüpraş" },
  { value: "YKBNK.IS", label: "YKBNK", name: "Yapı Kredi" },
];

const Header = ({ title, subtitle, onMenuClick, theme, onToggleTheme }) => {
  const {
    selectedTicker,
    setTicker,
    signal,
    indicators,
    getLatestIndicators,
    realtimeData,
    stockData,
  } = useStore();
  const { settings } = usePortfolioStore();
  const { unreadCount } = useNotifications();
  const isDark = theme === "dark";
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [notificationCenterOpen, setNotificationCenterOpen] = useState(false);
  const searchRef = useRef(null);
  const notificationRef = useRef(null);

  // Get latest indicator data
  const indicatorData = getLatestIndicators();
  const rsiValue = indicatorData?.rsi_14 || indicatorData?.rsi;
  const latestData =
    realtimeData?.price || stockData?.data?.[stockData?.data?.length - 1];

  const currentStock =
    STOCKS.find((s) => s.value === selectedTicker) || STOCKS[0];

  const filteredStocks = STOCKS.filter(
    (stock) =>
      stock.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
      stock.name.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  const handleSelectStock = (value) => {
    setTicker(value);
    setSearchOpen(false);
    setSearchQuery("");
  };

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setSearchOpen(false);
      }
      if (
        notificationRef.current &&
        !notificationRef.current.contains(e.target)
      ) {
        setNotificationsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Generate real-time notifications based on signal and indicator data
  const notifications = useMemo(() => {
    const notifs = [];
    const now = new Date().toLocaleTimeString("tr-TR", {
      hour: "2-digit",
      minute: "2-digit",
    });
    const ticker = selectedTicker?.split(".")[0] || "THYAO";

    // Signal notifications
    if (signal?.signal === "BUY" && signal?.confidence > 50) {
      notifs.push({
        id: 1,
        type: "signal",
        title: `${ticker} AL Sinyali`,
        message: `%${signal.confidence?.toFixed(0)} güvenle AL sinyali`,
        time: now,
        read: false,
        icon: TrendingUp,
        color: "success",
      });
    } else if (signal?.signal === "SELL" && signal?.confidence > 50) {
      notifs.push({
        id: 2,
        type: "signal",
        title: `${ticker} SAT Sinyali`,
        message: `%${signal.confidence?.toFixed(0)} güvenle SAT sinyali`,
        time: now,
        read: false,
        icon: TrendingDown,
        color: "danger",
      });
    }

    // RSI notifications
    if (rsiValue > 70) {
      notifs.push({
        id: 3,
        type: "alert",
        title: `${ticker} Aşırı Alım`,
        message: `RSI ${rsiValue?.toFixed(1)} - Dikkat!`,
        time: now,
        read: false,
        icon: AlertTriangle,
        color: "warning",
      });
    } else if (rsiValue < 30) {
      notifs.push({
        id: 4,
        type: "alert",
        title: `${ticker} Aşırı Satım`,
        message: `RSI ${rsiValue?.toFixed(1)} - Fırsat olabilir`,
        time: now,
        read: false,
        icon: AlertTriangle,
        color: "info",
      });
    }

    // Price change notification
    if (latestData?.close) {
      const changePercent =
        ((latestData.close - latestData.open) / latestData.open) * 100;
      if (Math.abs(changePercent) > 2) {
        notifs.push({
          id: 5,
          type: "info",
          title: `${ticker} Yüksek Volatilite`,
          message: `${changePercent > 0 ? "+" : ""}${changePercent.toFixed(
            2,
          )}% değişim`,
          time: now,
          read: false,
          icon: Info,
          color: changePercent > 0 ? "success" : "danger",
        });
      }
    }

    return notifs;
  }, [signal, rsiValue, latestData, selectedTicker]);

  return (
    <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8 animate-fade-in-down">
      {/* Left Section */}
      <div className="flex items-center gap-4">


        <div>
          <h1 className="header-title flex items-center gap-2">
            {title}
            <Sparkles className="w-5 h-5 text-accent-400 animate-pulse" />
          </h1>
          {subtitle && <p className="header-subtitle">{subtitle}</p>}
        </div>
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-1.5 sm:gap-3">
        {/* Stock Selector - Glass Style */}
        <div className="relative" ref={searchRef}>
          <button
            onClick={() => setSearchOpen(!searchOpen)}
            className="btn btn-outline flex items-center gap-1.5 sm:gap-3 group px-2 sm:px-4 py-1.5 sm:py-2.5"
          >
            <div className="flex items-center gap-1.5 sm:gap-2">
              <div className="w-6 h-6 sm:w-8 sm:h-8 rounded-lg bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center">
                <span className="text-[10px] sm:text-xs font-bold text-primary-400">
                  {currentStock.label.slice(0, 2)}
                </span>
              </div>
              <span className="font-bold text-gradient text-sm sm:text-base">
                {currentStock.label}
              </span>
            </div>
            <ChevronDown
              className={`w-3 h-3 sm:w-4 sm:h-4 transition-transform duration-300 text-theme-muted group-hover:text-primary-400 ${
                searchOpen ? "rotate-180" : ""
              }`}
            />
          </button>

          {searchOpen && (
            <div className="dropdown-menu w-[calc(100vw-1.5rem)] sm:w-80 left-0 sm:left-auto right-0 sm:right-auto animate-fade-in-down max-h-[80vh] sm:max-h-none">
              <div className="p-3 sm:p-4 border-b border-[var(--glass-border)]">
                <div className="relative">
                  <Search className="absolute left-3 sm:left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-theme-muted" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Hisse ara..."
                    className="input pl-10 sm:pl-11 text-sm"
                    autoFocus
                  />
                </div>
              </div>
              <div className="max-h-[60vh] sm:max-h-80 overflow-y-auto scrollbar-thin">
                {filteredStocks.map((stock, index) => (
                  <div
                    key={stock.value}
                    onClick={() => handleSelectStock(stock.value)}
                    className={`dropdown-item p-2.5 sm:p-3 ${
                      selectedTicker === stock.value
                        ? "bg-primary-500/10 border-l-2 border-primary-500"
                        : ""
                    }`}
                    style={{ animationDelay: `${index * 20}ms` }}
                  >
                    <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg sm:rounded-xl bg-gradient-to-br from-primary-500/10 to-accent-500/10 flex items-center justify-center border border-[var(--glass-border)]">
                      <span className="text-[10px] sm:text-xs font-bold text-primary-400">
                        {stock.label.slice(0, 2)}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-theme-text text-sm sm:text-base">
                        {stock.label}
                      </p>
                      <p className="text-[10px] sm:text-xs text-theme-muted truncate">{stock.name}</p>
                    </div>
                    {selectedTicker === stock.value && (
                      <div className="w-2.5 h-2.5 rounded-full bg-primary-500 animate-pulse shadow-lg shadow-primary-500/50" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Notifications - Glass Button */}
        <div className="relative" ref={notificationRef}>
          <button
            onClick={() => setNotificationCenterOpen(true)}
            className="relative p-2 sm:p-3 glass rounded-lg sm:rounded-xl border border-[var(--glass-border)] hover:border-primary-500 transition-all duration-300 group"
          >
            <Bell
              className={`w-4 h-4 sm:w-5 sm:h-5 transition-all duration-300 ${
                unreadCount > 0
                  ? "text-primary-400 group-hover:animate-pulse"
                  : "text-theme-muted group-hover:text-primary-400"
              }`}
            />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 sm:-top-1 sm:-right-1 w-4 h-4 sm:w-5 sm:h-5 bg-gradient-to-r from-danger to-danger-light text-white text-[9px] sm:text-[10px] rounded-full flex items-center justify-center font-bold animate-pulse shadow-lg shadow-danger/50">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </button>
        </div>

        {/* Notification Center Modal */}
        <NotificationCenter
          isOpen={notificationCenterOpen}
          onClose={() => setNotificationCenterOpen(false)}
        />

        {/* Theme Toggle - Animated */}
        <button
          onClick={onToggleTheme}
          className="p-2 sm:p-3 glass rounded-lg sm:rounded-xl border border-[var(--glass-border)] hover:border-accent-500 transition-all duration-300 group overflow-hidden"
        >
          <div className="relative">
            {isDark ? (
              <Sun className="w-4 h-4 sm:w-5 sm:h-5 text-accent-400 group-hover:rotate-180 transition-transform duration-500" />
            ) : (
              <Moon className="w-4 h-4 sm:w-5 sm:h-5 text-primary-400 group-hover:-rotate-12 transition-transform duration-300" />
            )}
          </div>
        </button>
      </div>
    </header>
  );
};

export default Header;
