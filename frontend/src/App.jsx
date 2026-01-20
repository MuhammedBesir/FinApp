/**
 * Main App Component with Modern Layout
 */
import React, { useState } from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import Sidebar from "./components/Layout/Sidebar";
import Header from "./components/Layout/Header";
import MobileBottomNav from "./components/Layout/MobileBottomNav";
import Dashboard from "./components/Dashboard/Dashboard";
import PortfolioPage from "./pages/PortfolioPage";
import DailyPicksPage from "./pages/DailyPicksPage";
import PerformancePage from "./pages/PerformancePage";
import EconomyNewsPage from "./pages/EconomyNewsPage";
import GeneralNewsPage from "./pages/GeneralNewsPage";
import SignalCenterPage from "./pages/SignalCenterPage";
import ScreenerPage from "./pages/ScreenerPage";
import CalculatorPage from "./pages/CalculatorPage";
import ChatPage from "./pages/ChatPage";
import AIAssistantPage from "./pages/AIAssistantPage";
import IPOPage from "./pages/IPOPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ProfilePage from "./pages/ProfilePage";
import NotFoundPage from "./pages/NotFoundPage";
import ProtectedRoute, { GuestRoute } from "./components/Common/ProtectedRoute";
import { ThemeProvider, useTheme } from "./context/ThemeContext";
import { AuthProvider } from "./context/AuthContext";
import { NotificationProvider } from "./context/NotificationContext";
import { Toaster } from 'react-hot-toast';
import "./index.css";

// Main Layout Component
const MainLayout = ({ children }) => {
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Get page title based on route
  const getPageInfo = () => {
    const routes = {
      "/": { title: "Dashboard", subtitle: "Portföy özeti ve piyasa analizi" },
      "/daily-picks": {
        title: "Günün Seçimleri",
        subtitle: "En iyi yatırım fırsatları",
      },
      "/performance": {
        title: "Performans",
        subtitle: "İşlem geçmişi ve PnL takibi",
      },
      "/portfolio": {
        title: "Portföy",
        subtitle: "Portföy yönetimi ve takibi",
      },
      "/news/economy": {
        title: "Ekonomi Haberleri",
        subtitle: "Türkiye ve dünya ekonomi haberleri",
      },
      "/news/general": {
        title: "Gündem Haberleri",
        subtitle: "Türkiye ve dünya gündem haberleri",
      },
      "/signals": {
        title: "Sinyal Merkezi",
        subtitle: "Tüm hisseler için alım/satım sinyalleri",
      },
      "/screener": {
        title: "Hisse Tarama",
        subtitle: "BIST hisselerini momentum skoruna göre tara",
      },
      "/calculator": {
        title: "Hesaplayıcı",
        subtitle: "Pozisyon boyutu ve kar/zarar hesaplama",
      },
      "/chat": {
        title: "Sohbet",
        subtitle: "Trader topluluğu ile sohbet",
      },
      "/ai-assistant": {
        title: "AI Asistan",
        subtitle: "Yapay zeka destekli trading tavsiyesi",
      },
      "/ipo": {
        title: "Halka Arz",
        subtitle: "BIST halka arz takibi",
      },
      "/profile": {
        title: "Profilim",
        subtitle: "Hesap ayarları ve güvenlik",
      },
    };
    return routes[location.pathname] || routes["/"];
  };

  const pageInfo = getPageInfo();

  return (
    <div className={`app-layout ${theme}`}>
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="main-content">
        <Header
          title={pageInfo.title}
          subtitle={pageInfo.subtitle}
          theme={theme}
          onToggleTheme={toggleTheme}
          onMenuClick={() => setSidebarOpen(true)}
        />
        {/* Added pb-20 for mobile bottom nav spacing */}
        <main className="content-area p-4 sm:p-6 pb-24 lg:pb-6">{children}</main>
      </div>

      {/* Mobile Bottom Navigation */}
      <MobileBottomNav />
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <NotificationProvider>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: 'var(--glass-bg)',
                color: 'var(--theme-text)',
                border: '1px solid var(--glass-border)',
                backdropFilter: 'blur(10px)',
              },
              success: {
                iconTheme: {
                  primary: 'var(--success)',
                  secondary: 'white',
                },
              },
              error: {
                iconTheme: {
                  primary: 'var(--danger)',
                  secondary: 'white',
                },
              },
            }}
          />
          <BrowserRouter>
            <Routes>
              {/* Auth Pages - Guest Only */}
              <Route path="/login" element={
                <GuestRoute>
                  <LoginPage />
                </GuestRoute>
              } />
              <Route path="/register" element={
                <GuestRoute>
                  <RegisterPage />
                </GuestRoute>
              } />
              <Route path="/forgot-password" element={
                <GuestRoute>
                  <ForgotPasswordPage />
                </GuestRoute>
              } />

              {/* Main App Routes - With Layout */}
              <Route
                path="/*"
                element={
                  <MainLayout>
                    <Routes>
                      {/* Public Routes */}
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/daily-picks" element={<DailyPicksPage />} />
                      <Route path="/news/economy" element={<EconomyNewsPage />} />
                      <Route path="/news/general" element={<GeneralNewsPage />} />
                      <Route path="/signals" element={<SignalCenterPage />} />
                      <Route path="/screener" element={<ScreenerPage />} />
                      <Route path="/calculator" element={<CalculatorPage />} />
                      <Route path="/ipo" element={<IPOPage />} />
                      
                      {/* Protected Routes - Require Authentication */}
                      <Route path="/performance" element={
                        <ProtectedRoute>
                          <PerformancePage />
                        </ProtectedRoute>
                      } />
                      <Route path="/portfolio" element={
                        <ProtectedRoute>
                          <PortfolioPage />
                        </ProtectedRoute>
                      } />
                      <Route path="/chat" element={
                        <ProtectedRoute>
                          <ChatPage />
                        </ProtectedRoute>
                      } />
                      <Route path="/ai-assistant" element={
                        <ProtectedRoute>
                          <AIAssistantPage />
                        </ProtectedRoute>
                      } />
                      <Route path="/profile" element={
                        <ProtectedRoute>
                          <ProfilePage />
                        </ProtectedRoute>
                      } />
                      
                      {/* 404 Page */}
                      <Route path="*" element={<NotFoundPage />} />
                    </Routes>
                  </MainLayout>
                }
              />
            </Routes>
          </BrowserRouter>
        </NotificationProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App;
