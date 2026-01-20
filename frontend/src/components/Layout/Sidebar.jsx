/**
 * Sidebar Component - Modern Glassmorphism Trading Dashboard
 * 🌙 Dark Mode Dominance | ✨ Glassmorphism | 🎨 Minimalist Design
 * With Toggle (Collapse/Expand) Feature
 */
import React, { useState, useRef, useEffect } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Target,
  BarChart3,
  Briefcase,
  Activity,
  Settings,
  Bell,
  HelpCircle,
  LogOut,
  TrendingUp,
  PieChart,
  Calculator,
  Newspaper,
  Calendar,
  ChevronDown,
  X,
  Globe,
  TrendingDown,
  MessageCircle,
  Building2,
  Bot,
  Sparkles,
  User,
  ChevronUp,
  Crown,
  ChevronLeft,
  ChevronRight,
  Menu,
} from "lucide-react";
import { useStore } from "../../store";
import { useAuth } from "../../context/AuthContext";
import SettingsModal from "../Common/SettingsModal";

const Sidebar = ({ isOpen, onClose }) => {
  const { selectedTicker } = useStore();
  const { user, logout, getUserInitials } = useAuth();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(() => {
    // Get from localStorage if available
    const saved = localStorage.getItem('sidebarCollapsed');
    return saved === 'true';
  });
  const location = useLocation();
  const navigate = useNavigate();
  const userMenuRef = useRef(null);

  // Sync collapsed state with body class and localStorage
  useEffect(() => {
    document.body.classList.toggle('sidebar-collapsed', isCollapsed);
    localStorage.setItem('sidebarCollapsed', isCollapsed.toString());
    return () => {
      document.body.classList.remove('sidebar-collapsed');
    };
  }, [isCollapsed]);

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setIsUserMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const menuItems = [
    {
      section: "MENU",
      items: [
        { to: "/", icon: LayoutDashboard, label: "Dashboard" },
        { to: "/daily-picks", icon: Target, label: "Günün Fırsatları" },
        { to: "/performance", icon: Activity, label: "Performans" },
        { to: "/portfolio", icon: Briefcase, label: "Portföy" },
      ],
    },
    {
      section: "ARAÇLAR",
      items: [
        { to: "/signals", icon: Bell, label: "Sinyal Merkezi" },
        { to: "/screener", icon: PieChart, label: "Hisse Tarama" },
        { to: "/calculator", icon: Calculator, label: "Hesaplayıcı" },
        { to: "/ipo", icon: Building2, label: "Halka Arz" },
      ],
    },
    {
      section: "TOPLULUK",
      items: [
        { to: "/ai-assistant", icon: Bot, label: "AI Asistan" },
        { to: "/chat", icon: MessageCircle, label: "Sohbet" },
      ],
    },
    {
      section: "HABERLER",
      items: [
        { to: "/news/economy", icon: TrendingDown, label: "Ekonomi Haberleri" },
        { to: "/news/general", icon: Globe, label: "Gündem Haberleri" },
      ],
    },
  ];

  return (
    <>
      {/* Backdrop for mobile - Blur effect */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-30 lg:hidden animate-fade-in"
          onClick={onClose}
        />
      )}

      {/* Sidebar - Glassmorphism Design */}
      <aside className={`sidebar ${isOpen ? "open" : ""} ${isCollapsed ? "collapsed" : ""}`}>
        {/* Background Gradient Mesh */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-radial from-primary-500/10 via-transparent to-transparent" />
          <div className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-radial from-accent-500/10 via-transparent to-transparent" />
        </div>

        {/* Logo Section - Investia Brand */}
        <div className="relative flex items-center justify-between px-6 py-6 border-b border-[var(--glass-border)]">
          {isCollapsed ? (
            /* Collapsed: Show only menu icon */
            <button
              onClick={() => setIsCollapsed(false)}
              className="w-full flex items-center justify-center p-2 hover:bg-[var(--color-sidebar-hover)] rounded-xl transition-all duration-200 group"
            >
              <Menu className="w-6 h-6 text-primary-400 group-hover:text-primary-300 transition-colors" />
            </button>
          ) : (
            /* Expanded: Show logo and collapse button */
            <>
              <div className="flex items-center gap-3">
                {/* Investia Logo - Brand Guide SVG */}
                <svg
                  width="140"
                  height="42"
                  viewBox="0 0 200 60"
                  fill="none"
                  className="hover:scale-105 transition-transform duration-300"
                >
                  <defs>
                    <linearGradient
                      id="sidebarLogoGradient"
                      x1="0%"
                      y1="0%"
                      x2="100%"
                      y2="0%"
                    >
                      <stop offset="0%" stopColor="#10b981" />
                      <stop offset="100%" stopColor="#06b6d4" />
                    </linearGradient>
                  </defs>
                  {/* Chart Icon */}
                  <path
                    d="M5 45L20 30L30 40L55 15"
                    stroke="url(#sidebarLogoGradient)"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    fill="none"
                  />
                  <circle cx="20" cy="30" r="3" fill="#10b981" />
                  <circle cx="30" cy="40" r="3" fill="#059669" />
                  <circle cx="55" cy="15" r="3" fill="#06b6d4" />
                  {/* Text */}
                  <text
                    x="70"
                    y="40"
                    fontFamily="Inter, -apple-system, BlinkMacSystemFont, sans-serif"
                    fontSize="26"
                    fontWeight="800"
                    fill="url(#sidebarLogoGradient)"
                  >
                    Investia
                  </text>
                </svg>
              </div>
              {/* Collapse Button - Desktop */}
              <button
                onClick={() => setIsCollapsed(true)}
                className="hidden lg:flex p-2 hover:bg-[var(--color-sidebar-hover)] rounded-xl transition-all duration-200 group"
                title="Sidebar'ı daralt"
              >
                <ChevronLeft className="w-5 h-5 text-theme-muted group-hover:text-theme-text transition-colors" />
              </button>
              {/* Close Button - Mobile */}
              <button
                onClick={onClose}
                className="lg:hidden p-2.5 hover:bg-[var(--color-sidebar-hover)] rounded-xl transition-all duration-200 group"
              >
                <X className="w-5 h-5 text-theme-muted group-hover:text-theme-text transition-colors" />
              </button>
            </>
          )}
        </div>

        {/* Navigation */}
        <nav className="relative flex-1 py-5 overflow-y-auto scrollbar-hide">
          {menuItems.map((section, idx) => (
            <div
              key={idx}
              className="animate-fade-in"
              style={{ animationDelay: `${idx * 50}ms` }}
            >
              {!isCollapsed && (
                <div className="sidebar-section-title">{section.section}</div>
              )}
              {section.items.map((item, itemIdx) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.to;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={onClose}
                    className={`sidebar-item group ${isActive ? "active" : ""} ${isCollapsed ? "justify-center px-0" : ""}`}
                    style={{ animationDelay: `${(idx * 4 + itemIdx) * 30}ms` }}
                    title={isCollapsed ? item.label : undefined}
                  >
                    <div
                      className={`relative ${isActive ? "" : "group-hover:scale-110"} transition-transform duration-200`}
                    >
                      <Icon className={`${isCollapsed ? "w-6 h-6" : "w-5 h-5"}`} />
                      {isActive && (
                        <div className="absolute -inset-1 bg-white/20 rounded-lg blur-sm" />
                      )}
                    </div>
                    {!isCollapsed && (
                      <>
                        <span className="font-medium">{item.label}</span>
                        {isActive && (
                          <div className="ml-auto w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                        )}
                      </>
                    )}
                  </NavLink>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Selected Stock Info - Glass Card (only when expanded) */}
        {!isCollapsed && (
          <div className="relative p-4">
            <div className="glass rounded-2xl p-4 border border-[var(--glass-border)]">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-theme-muted font-medium">
                  Seçili Hisse
                </span>
                <span className="badge badge-primary text-xs">
                  {selectedTicker?.split(".")[0] || "THYAO"}
                </span>
              </div>
              <p className="text-sm text-theme-text font-semibold">
                {selectedTicker?.split(".")[0] === "THYAO"
                  ? "Türk Hava Yolları"
                  : selectedTicker?.split(".")[0] === "GARAN"
                    ? "Garanti BBVA"
                    : selectedTicker?.split(".")[0] || "Seçiniz"}
              </p>
              <div className="mt-3 flex items-center gap-2">
                <div className="live-dot" />
                <span className="text-xs text-success">Canlı Veri</span>
              </div>
            </div>
          </div>
        )}

        {/* User Profile - Modern Glass with Dropdown */}
        <div className="relative p-4 border-t border-[var(--glass-border)]" ref={userMenuRef}>
          {/* User Menu Dropdown */}
          {isUserMenuOpen && (
            <div className={`absolute bottom-full mb-2 glass rounded-xl border border-[var(--glass-border)] overflow-hidden animate-fade-in-up shadow-xl ${isCollapsed ? "left-0 right-auto w-56 ml-2" : "left-4 right-4"}`}>
              <div className="p-3 border-b border-[var(--glass-border)]">
                <p className="text-xs text-theme-muted">Oturum açık</p>
                <p className="text-sm font-medium text-theme-text truncate">{user?.email || "misafir@email.com"}</p>
              </div>
              <div className="p-1">
                <button
                  onClick={() => {
                    setIsUserMenuOpen(false);
                    navigate("/profile");
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-theme-text hover:bg-[var(--color-sidebar-hover)] rounded-lg transition-colors"
                >
                  <User className="w-4 h-4 text-theme-muted" />
                  Profilim
                </button>
                <button
                  onClick={() => {
                    setIsUserMenuOpen(false);
                    setIsSettingsOpen(true);
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-theme-text hover:bg-[var(--color-sidebar-hover)] rounded-lg transition-colors"
                >
                  <Settings className="w-4 h-4 text-theme-muted" />
                  Ayarlar
                </button>
                <button
                  onClick={() => {
                    setIsUserMenuOpen(false);
                    // TODO: Open help
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-theme-text hover:bg-[var(--color-sidebar-hover)] rounded-lg transition-colors"
                >
                  <HelpCircle className="w-4 h-4 text-theme-muted" />
                  Yardım
                </button>
              </div>
              <div className="p-1 border-t border-[var(--glass-border)]">
                <button
                  onClick={() => {
                    setIsUserMenuOpen(false);
                    handleLogout();
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Çıkış Yap
                </button>
              </div>
            </div>
          )}

          {/* User Profile Button */}
          <button
            onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
            className={`w-full flex items-center gap-3 p-2 -m-2 rounded-xl hover:bg-[var(--color-sidebar-hover)] transition-all duration-200 ${isCollapsed ? "justify-center" : ""}`}
          >
            <div className="relative">
              <div className={`${isCollapsed ? "w-10 h-10" : "w-11 h-11"} rounded-xl bg-gradient-to-br from-primary-400 via-primary-500 to-accent-500 flex items-center justify-center text-white font-bold ${isCollapsed ? "text-base" : "text-lg"} shadow-lg shadow-primary-500/20`}>
                {getUserInitials()}
              </div>
              <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-success rounded-full border-2 border-[var(--color-sidebar)]" />
            </div>
            {!isCollapsed && (
              <>
                <div className="flex-1 min-w-0 text-left">
                  <p className="text-sm font-semibold text-theme-text truncate">
                    {user?.fullName || "Misafir"}
                  </p>
                  <p className="text-xs text-theme-muted truncate flex items-center gap-1">
                    {user?.membership === "Pro" ? (
                      <>
                        <Crown className="w-3 h-3 text-yellow-400" />
                        <span className="text-yellow-400">Pro Üyelik</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3 h-3 text-accent-400" />
                        <span>Ücretsiz</span>
                      </>
                    )}
                  </p>
                </div>
                <div className="p-1">
                  {isUserMenuOpen ? (
                    <ChevronUp className="w-4 h-4 text-theme-muted" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-theme-muted" />
                  )}
                </div>
              </>
            )}
          </button>
        </div>
      </aside>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </>
  );
};

export default Sidebar;
