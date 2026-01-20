/**
 * Modern Navigation Bar - Investia
 */
import React, { useState, useRef, useEffect } from "react";
import { NavLink } from "react-router-dom";
import {
  TrendingUp,
  Settings,
  ChevronDown,
  Search,
  Home,
  Target,
  BarChart3,
  Briefcase,
  Activity,
  X,
} from "lucide-react";
import { useStore } from "../../store";
import SettingsModal from "./SettingsModal";

// BIST 30 Hisseleri + Altın
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

const Navbar = () => {
  const { selectedTicker, setTicker } = useStore();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [stockDropdownOpen, setStockDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const dropdownRef = useRef(null);

  const currentStock = STOCKS.find((s) => s.value === selectedTicker) || {
    label: selectedTicker?.split(".")[0] || "THYAO",
    name: "",
  };

  const filteredStocks = STOCKS.filter(
    (stock) =>
      stock.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
      stock.name.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  const handleSelectStock = (value) => {
    setTicker(value);
    setStockDropdownOpen(false);
    setSearchQuery("");
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setStockDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const navItems = [
    { to: "/", label: "Ana Sayfa", mobileLabel: "Ana", icon: Home },
    {
      to: "/daily-picks",
      label: "Fırsatlar",
      mobileLabel: "Fırsat",
      icon: Target,
    },
    {
      to: "/performance",
      label: "Performans",
      mobileLabel: "Perf.",
      icon: Activity,
    },
    {
      to: "/backtest",
      label: "Backtest",
      mobileLabel: "Test",
      icon: BarChart3,
    },
    {
      to: "/portfolio",
      label: "Portföy",
      mobileLabel: "Port.",
      icon: Briefcase,
    },
  ];

  return (
    <>
      <nav className="bg-theme-card border-b border-theme-border sticky top-0 z-50">
        <div className="container mx-auto px-3 sm:px-4 lg:px-6">
          <div className="flex items-center justify-between h-14 sm:h-16">
            {/* Left: Logo */}
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 sm:w-9 sm:h-9 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
              </div>
              <span className="text-base sm:text-lg font-bold text-theme-text">
                Investia
              </span>
            </div>

            {/* Center: Navigation Links - Desktop Only */}
            <div className="hidden lg:flex items-center gap-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `px-4 py-2 text-sm font-medium rounded-lg transition-all ${
                      isActive
                        ? "bg-theme-bg text-theme-text"
                        : "text-theme-muted hover:text-theme-text hover:bg-theme-bg/50"
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              ))}

              {/* Stock Selector Dropdown - Desktop */}
              <div className="relative ml-2" ref={dropdownRef}>
                <button
                  onClick={() => setStockDropdownOpen(!stockDropdownOpen)}
                  className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all ${
                    stockDropdownOpen
                      ? "bg-primary-500/10 text-primary-500"
                      : "text-theme-muted hover:text-theme-text hover:bg-theme-bg/50"
                  }`}
                >
                  <span>{currentStock.label}</span>
                  <ChevronDown
                    className={`w-4 h-4 transition-transform ${
                      stockDropdownOpen ? "rotate-180" : ""
                    }`}
                  />
                </button>

                {/* Desktop Dropdown Menu */}
                {stockDropdownOpen && (
                  <div className="absolute top-full right-0 mt-2 w-72 bg-theme-card border border-theme-border rounded-xl shadow-xl shadow-black/20 overflow-hidden z-50">
                    <div className="p-2 border-b border-theme-border">
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-theme-muted" />
                        <input
                          type="text"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          placeholder="BIST 30'da ara..."
                          className="w-full pl-9 pr-3 py-2 bg-theme-bg border border-theme-border rounded-lg text-sm focus:outline-none focus:border-primary-500 text-theme-text"
                          autoFocus
                        />
                      </div>
                    </div>
                    <div className="max-h-72 overflow-y-auto">
                      {filteredStocks.map((stock) => (
                        <button
                          key={stock.value}
                          onClick={() => handleSelectStock(stock.value)}
                          className={`w-full flex items-center justify-between px-4 py-2.5 text-left hover:bg-theme-bg/50 transition-colors ${
                            selectedTicker === stock.value
                              ? "bg-primary-500/10"
                              : ""
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <span className="text-sm font-semibold text-theme-text w-14">
                              {stock.label}
                            </span>
                            <span className="text-xs text-theme-muted">
                              {stock.name}
                            </span>
                          </div>
                          {selectedTicker === stock.value && (
                            <div className="w-2 h-2 bg-primary-500 rounded-full" />
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Right: Actions */}
            <div className="flex items-center gap-2">
              {/* Settings */}
              <button
                onClick={() => setSettingsOpen(true)}
                className="p-2 hover:bg-theme-bg rounded-lg transition-colors"
              >
                <Settings className="w-5 h-5 text-theme-muted" />
              </button>

              {/* Premium Badge - Desktop only */}
              <button className="hidden md:flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity">
                <span>⚡</span>
                <span>Pro</span>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Bottom Navigation Bar */}
        <div className="lg:hidden border-t border-theme-border bg-theme-card">
          <div className="flex items-stretch">
            {/* Navigation Items */}
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex-1 flex flex-col items-center justify-center py-2 transition-all ${
                      isActive ? "text-primary-500" : "text-theme-muted"
                    }`
                  }
                >
                  <Icon className="w-5 h-5" />
                  <span className="text-[10px] mt-0.5 font-medium">
                    {item.mobileLabel}
                  </span>
                </NavLink>
              );
            })}

            {/* Mobile Stock Selector Button */}
            <button
              onClick={() => setStockDropdownOpen(true)}
              className="flex-1 flex flex-col items-center justify-center py-2 text-primary-500 border-l border-theme-border"
            >
              <span className="text-xs font-bold">{currentStock.label}</span>
              <ChevronDown className="w-3 h-3 mt-0.5" />
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Full Screen Stock Selector */}
      {stockDropdownOpen && (
        <div className="lg:hidden fixed inset-0 bg-theme-bg z-[60] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-theme-border bg-theme-card">
            <h2 className="text-base font-semibold text-theme-text">
              BIST 30 Hisseleri
            </h2>
            <button
              onClick={() => setStockDropdownOpen(false)}
              className="p-2 hover:bg-theme-bg rounded-lg"
            >
              <X className="w-5 h-5 text-theme-muted" />
            </button>
          </div>

          {/* Search */}
          <div className="p-3 border-b border-theme-border bg-theme-card">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-theme-muted" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Hisse ara..."
                className="w-full pl-10 pr-4 py-3 bg-theme-bg border border-theme-border rounded-xl text-sm focus:outline-none focus:border-primary-500 text-theme-text"
                autoFocus
              />
            </div>
          </div>

          {/* Stock List */}
          <div className="flex-1 overflow-y-auto">
            {filteredStocks.map((stock) => (
              <button
                key={stock.value}
                onClick={() => handleSelectStock(stock.value)}
                className={`w-full flex items-center justify-between px-4 py-4 border-b border-theme-border/50 active:bg-theme-card transition-colors ${
                  selectedTicker === stock.value ? "bg-primary-500/10" : ""
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className="w-11 h-11 bg-theme-card border border-theme-border rounded-xl flex items-center justify-center">
                    <span className="text-xs font-bold text-primary-500">
                      {stock.label.slice(0, 2)}
                    </span>
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-semibold text-theme-text">
                      {stock.label}
                    </p>
                    <p className="text-xs text-theme-muted">{stock.name}</p>
                  </div>
                </div>
                {selectedTicker === stock.value && (
                  <div className="w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-xs">✓</span>
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      <SettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />
    </>
  );
};

export default Navbar;
