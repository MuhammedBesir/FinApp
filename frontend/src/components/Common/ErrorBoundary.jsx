/**
 * Error Boundary Component - React Crash Handler
 * Catches JavaScript errors in child components and displays fallback UI
 */
import React from "react";
import { AlertTriangle, RefreshCw, Home, Bug } from "lucide-react";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render shows the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log error to console in development
    console.error("Error Boundary caught an error:", error, errorInfo);

    this.setState({ errorInfo });

    // You can also log to an external error reporting service here
    // Example: logErrorToService(error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  handleGoHome = () => {
    window.location.href = "/";
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      return (
        <div className="min-h-screen bg-[#0f172a] flex items-center justify-center p-4">
          {/* Background Effects */}
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute top-1/4 -left-20 w-96 h-96 bg-red-500/10 rounded-full blur-3xl" />
            <div className="absolute bottom-1/4 -right-20 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl" />
          </div>

          <div className="relative glass-card p-8 rounded-3xl border border-white/10 backdrop-blur-xl bg-white/5 max-w-lg w-full text-center">
            {/* Error Icon */}
            <div className="flex justify-center mb-6">
              <div className="p-4 rounded-full bg-red-500/10 border border-red-500/20">
                <AlertTriangle className="w-12 h-12 text-red-400" />
              </div>
            </div>

            {/* Error Title */}
            <h1 className="text-2xl font-bold text-white mb-3">
              Bir Hata Oluştu 😔
            </h1>
            <p className="text-slate-400 mb-6">
              Üzgünüz, beklenmeyen bir hata meydana geldi. Lütfen sayfayı
              yenileyin veya ana sayfaya dönün.
            </p>

            {/* Error Details (Development Only) */}
            {import.meta.env.DEV && this.state.error && (
              <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-left">
                <div className="flex items-center gap-2 mb-2">
                  <Bug className="w-4 h-4 text-red-400" />
                  <span className="text-red-400 text-sm font-medium">
                    Hata Detayı (Dev Mode)
                  </span>
                </div>
                <pre className="text-xs text-red-300 overflow-auto max-h-32 whitespace-pre-wrap">
                  {this.state.error.toString()}
                </pre>
                {this.state.errorInfo && (
                  <pre className="text-xs text-red-300/70 overflow-auto max-h-32 mt-2 whitespace-pre-wrap">
                    {this.state.errorInfo.componentStack}
                  </pre>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={this.handleRetry}
                className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-primary-500 to-accent-500 text-white font-medium rounded-xl hover:opacity-90 transition-opacity"
              >
                <RefreshCw className="w-4 h-4" />
                Tekrar Dene
              </button>
              <button
                onClick={this.handleGoHome}
                className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-white/5 border border-white/10 text-white font-medium rounded-xl hover:bg-white/10 transition-colors"
              >
                <Home className="w-4 h-4" />
                Ana Sayfa
              </button>
            </div>

            {/* Reload Link */}
            <button
              onClick={this.handleReload}
              className="mt-4 text-sm text-slate-400 hover:text-white transition-colors"
            >
              Sayfayı yenile
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
