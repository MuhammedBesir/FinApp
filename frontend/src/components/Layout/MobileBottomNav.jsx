/**
 * Mobile Bottom Navigation
 * 📱 Fixed bottom navigation bar for mobile devices
 */
import React, { useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Target,
  Briefcase,
  PieChart,
  Menu,
  X,
  Activity,
  Bell,
  Calculator,
  Building2,
  Bot,
  MessageCircle,
  Newspaper,
  Settings,
  LogOut,
  User,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const MobileBottomNav = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, getUserInitials } = useAuth();

  // Main nav items (shown in bottom bar)
  const mainItems = [
    { to: '/', icon: LayoutDashboard, label: 'Ana Sayfa' },
    { to: '/daily-picks', icon: Target, label: 'Fırsatlar' },
    { to: '/portfolio', icon: Briefcase, label: 'Portföy' },
    { to: '/screener', icon: PieChart, label: 'Tarama' },
  ];

  // Extended menu items (shown in modal)
  const menuSections = [
    {
      title: 'Araçlar',
      items: [
        { to: '/performance', icon: Activity, label: 'Performans' },
        { to: '/signals', icon: Bell, label: 'Sinyal Merkezi' },
        { to: '/calculator', icon: Calculator, label: 'Hesaplayıcı' },
        { to: '/ipo', icon: Building2, label: 'Halka Arz' },
      ],
    },
    {
      title: 'Topluluk',
      items: [
        { to: '/ai-assistant', icon: Bot, label: 'AI Asistan' },
        { to: '/chat', icon: MessageCircle, label: 'Sohbet' },
      ],
    },
    {
      title: 'Haberler',
      items: [
        { to: '/news/economy', icon: Newspaper, label: 'Ekonomi' },
        { to: '/news/general', icon: Newspaper, label: 'Gündem' },
      ],
    },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
    setIsMenuOpen(false);
  };

  const handleNavigate = (to) => {
    navigate(to);
    setIsMenuOpen(false);
  };

  return (
    <>
      {/* Bottom Navigation Bar */}
      <nav className="fixed bottom-0 left-0 right-0 z-40 lg:hidden">
        {/* Gradient Border Top */}
        <div className="h-[1px] bg-gradient-to-r from-primary-500/50 via-accent-500/50 to-primary-500/50" />
        
        {/* Nav Container */}
        <div className="bg-theme-card/95 backdrop-blur-xl border-t border-[var(--glass-border)]">
          <div className="flex items-center justify-around px-2 py-2">
            {mainItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.to;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className="flex-1 flex flex-col items-center py-1.5"
                >
                  <div className={`p-2 rounded-xl transition-all ${
                    isActive 
                      ? 'bg-primary-500/20 text-primary-400' 
                      : 'text-theme-muted hover:text-theme-text'
                  }`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className={`text-[10px] mt-0.5 font-medium ${
                    isActive ? 'text-primary-400' : 'text-theme-muted'
                  }`}>
                    {item.label}
                  </span>
                </NavLink>
              );
            })}
            
            {/* More Menu Button */}
            <button
              onClick={() => setIsMenuOpen(true)}
              className="flex-1 flex flex-col items-center py-1.5"
            >
              <div className={`p-2 rounded-xl transition-all ${
                isMenuOpen 
                  ? 'bg-primary-500/20 text-primary-400' 
                  : 'text-theme-muted hover:text-theme-text'
              }`}>
                <Menu className="w-5 h-5" />
              </div>
              <span className={`text-[10px] mt-0.5 font-medium ${
                isMenuOpen ? 'text-primary-400' : 'text-theme-muted'
              }`}>
                Daha Fazla
              </span>
            </button>
          </div>
          
          {/* Safe area padding for iOS */}
          <div className="h-safe-area-inset-bottom bg-theme-card" />
        </div>
      </nav>

      {/* Extended Menu Modal */}
      {isMenuOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 lg:hidden animate-fade-in"
            onClick={() => setIsMenuOpen(false)}
          />
          
          {/* Menu Panel - Slide from bottom */}
          <div className="fixed inset-x-0 bottom-0 z-50 lg:hidden animate-slide-up">
            <div className="bg-theme-card rounded-t-2xl max-h-[85vh] overflow-y-auto">
              {/* Handle */}
              <div className="flex justify-center py-3">
                <div className="w-10 h-1 rounded-full bg-theme-muted/30" />
              </div>
              
              {/* Header */}
              <div className="flex items-center justify-between px-4 pb-3 border-b border-[var(--glass-border)]">
                <h2 className="font-bold text-theme-text text-lg">Menü</h2>
                <button
                  onClick={() => setIsMenuOpen(false)}
                  className="p-2 bg-theme-card rounded-lg"
                >
                  <X className="w-5 h-5 text-theme-muted" />
                </button>
              </div>

              {/* User Info */}
              <div className="px-4 py-4 border-b border-[var(--glass-border)]">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-400 to-accent-500 flex items-center justify-center text-white font-bold text-lg">
                    {getUserInitials?.() || 'U'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-theme-text truncate">
                      {user?.fullName || 'Misafir'}
                    </p>
                    <p className="text-xs text-theme-muted truncate">
                      {user?.email || 'misafir@email.com'}
                    </p>
                  </div>
                  <button
                    onClick={() => handleNavigate('/profile')}
                    className="p-2 bg-theme-card rounded-lg"
                  >
                    <ChevronRight className="w-5 h-5 text-theme-muted" />
                  </button>
                </div>
              </div>

              {/* Menu Sections */}
              <div className="px-4 py-3 space-y-4">
                {menuSections.map((section, idx) => (
                  <div key={idx}>
                    <p className="text-[10px] font-bold text-theme-muted uppercase tracking-wider mb-2">
                      {section.title}
                    </p>
                    <div className="grid grid-cols-4 gap-2">
                      {section.items.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.to;
                        return (
                          <button
                            key={item.to}
                            onClick={() => handleNavigate(item.to)}
                            className={`flex flex-col items-center p-3 rounded-xl transition-all ${
                              isActive 
                                ? 'bg-primary-500/20 text-primary-400' 
                                : 'bg-theme-card/50 text-theme-muted hover:bg-theme-card hover:text-theme-text'
                            }`}
                          >
                            <Icon className="w-5 h-5 mb-1" />
                            <span className="text-[10px] font-medium text-center">{item.label}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>

              {/* Bottom Actions */}
              <div className="px-4 py-4 border-t border-[var(--glass-border)] space-y-2">
                <button
                  onClick={() => handleNavigate('/settings')}
                  className="w-full flex items-center gap-3 p-3 rounded-xl bg-theme-card/50 text-theme-text"
                >
                  <Settings className="w-5 h-5 text-theme-muted" />
                  <span className="font-medium">Ayarlar</span>
                </button>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 p-3 rounded-xl bg-danger/10 text-danger"
                >
                  <LogOut className="w-5 h-5" />
                  <span className="font-medium">Çıkış Yap</span>
                </button>
              </div>

              {/* Safe area */}
              <div className="h-6" />
            </div>
          </div>
        </>
      )}
    </>
  );
};

export default MobileBottomNav;
