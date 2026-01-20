/**
 * General News Page - Modern Design
 * Türkiye ve dünya gündem haberleri
 */
import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import {
  RefreshCw,
  Globe,
  Clock,
  ExternalLink,
  Newspaper,
  MapPin,
  Flame,
  ChevronRight,
  AlertCircle,
} from "lucide-react";

const GeneralNewsPage = () => {
  const [news, setNews] = useState({ turkey: [], world: [] });
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [activeTab, setActiveTab] = useState("turkey");

  const fetchNews = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(
        "/api/news/general"
      );
      setNews({
        turkey: response.data.turkey || [],
        world: response.data.world || [],
      });
      setLastUpdate(new Date());
    } catch (error) {
      console.error("Error fetching general news:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNews();
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchNews, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchNews]);

  const formatTime = (dateStr) => {
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diff = (now - date) / 1000 / 60; // dakika cinsinden

      if (diff < 60) {
        return `${Math.floor(diff)} dk önce`;
      } else if (diff < 1440) {
        return `${Math.floor(diff / 60)} saat önce`;
      } else {
        return date.toLocaleDateString("tr-TR");
      }
    } catch {
      return "";
    }
  };

  const currentNews = activeTab === "turkey" ? news.turkey : news.world;

  return (
    <div className="space-y-4 md:space-y-6 animate-fade-in">
      {/* Header Card */}
      <div className="card">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
          <div className="flex items-center gap-3 sm:gap-4">
            <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-warning/20 flex items-center justify-center">
              <Flame className="w-5 h-5 sm:w-6 sm:h-6 text-warning" />
            </div>
            <div>
              <h2 className="text-lg sm:text-xl font-bold text-theme-text">
                Gündem Haberleri
              </h2>
              <p className="text-xs sm:text-sm text-theme-muted">
                Türkiye ve dünyadan son dakika gelişmeler
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {lastUpdate && (
              <div className="flex items-center gap-2 text-sm text-theme-muted">
                <Clock className="w-4 h-4" />
                <span>Son: {lastUpdate.toLocaleTimeString("tr-TR")}</span>
              </div>
            )}
            <button
              onClick={fetchNews}
              disabled={loading}
              className="btn btn-primary"
            >
              <RefreshCw
                className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}
              />
              Yenile
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto">
        <button
          onClick={() => setActiveTab("turkey")}
          className={`flex items-center gap-2 px-3 sm:px-4 py-2 sm:py-2.5 rounded-xl font-medium transition-all whitespace-nowrap ${
            activeTab === "turkey"
              ? "bg-danger text-white"
              : "bg-[var(--color-card)] text-theme-muted hover:text-theme-text border border-[var(--color-border)]"
          }`}
        >
          <MapPin className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
          Türkiye
          <span
            className={`text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 rounded-full ${
              activeTab === "turkey"
                ? "bg-white/20"
                : "bg-[var(--color-bg-secondary)]"
            }`}
          >
            {news.turkey.length}
          </span>
        </button>
        <button
          onClick={() => setActiveTab("world")}
          className={`flex items-center gap-2 px-3 sm:px-4 py-2 sm:py-2.5 rounded-xl font-medium transition-all whitespace-nowrap ${
            activeTab === "world"
              ? "bg-danger text-white"
              : "bg-[var(--color-card)] text-theme-muted hover:text-theme-text border border-[var(--color-border)]"
          }`}
        >
          <Globe className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
          Dünya
          <span
            className={`text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 rounded-full ${
              activeTab === "world"
                ? "bg-white/20"
                : "bg-[var(--color-bg-secondary)]"
            }`}
          >
            {news.world.length}
          </span>
        </button>
      </div>

      {/* Breaking News Banner (if there are recent news) */}
      {currentNews.length > 0 && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-danger/10 border border-danger/30">
          <AlertCircle className="w-5 h-5 text-danger flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <span className="text-xs font-bold text-danger uppercase tracking-wide">
              Son Dakika
            </span>
            <p className="text-sm text-theme-text font-medium truncate mt-0.5">
              {currentNews[0]?.title}
            </p>
          </div>
          <ChevronRight className="w-5 h-5 text-danger flex-shrink-0" />
        </div>
      )}

      {/* News List */}
      {loading && currentNews.length === 0 ? (
        <div className="card text-center py-12">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-primary mb-4" />
          <p className="text-theme-muted">Haberler yükleniyor...</p>
        </div>
      ) : currentNews.length === 0 ? (
        <div className="card text-center py-12">
          <Newspaper className="w-12 h-12 text-theme-muted mx-auto mb-4 opacity-50" />
          <p className="text-theme-text font-medium mb-2">Haber bulunamadı</p>
          <p className="text-sm text-theme-muted">Daha sonra tekrar deneyin</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {currentNews.map((item, index) => (
            <article
              key={index}
              className={`card hover:border-primary/50 transition-all group ${
                index === 0 ? "border-danger/30" : ""
              }`}
            >
              <div className="flex items-start gap-4">
                <div className="hidden sm:flex w-12 h-12 rounded-xl bg-[var(--color-bg-secondary)] items-center justify-center flex-shrink-0">
                  {index === 0 ? (
                    <Flame className="w-5 h-5 text-danger" />
                  ) : activeTab === "turkey" ? (
                    <MapPin className="w-5 h-5 text-warning" />
                  ) : (
                    <Globe className="w-5 h-5 text-info" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      {index === 0 && (
                        <span className="inline-block text-xs font-bold text-danger uppercase tracking-wide mb-1">
                          Son Dakika
                        </span>
                      )}
                      <h3 className="font-semibold text-theme-text group-hover:text-primary transition-colors line-clamp-2">
                        {item.title}
                      </h3>
                    </div>
                    {item.link && item.link !== "#" && (
                      <a
                        href={item.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-shrink-0 p-2 rounded-lg hover:bg-[var(--color-bg-secondary)] text-theme-muted hover:text-primary transition-colors"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    )}
                  </div>

                  {item.description && (
                    <p className="mt-2 text-sm text-theme-muted line-clamp-2">
                      {item.description}
                    </p>
                  )}

                  <div className="flex items-center gap-4 mt-3 text-xs text-theme-dim">
                    <span className="badge">{item.source}</span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatTime(item.published)}
                    </span>
                  </div>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      {/* Auto-update indicator */}
      <div className="flex items-center justify-center gap-2 text-sm text-theme-muted">
        <div className="w-2 h-2 bg-success rounded-full animate-pulse" />
        <span>Haberler 5 dakikada bir güncellenir</span>
      </div>
    </div>
  );
};

export default GeneralNewsPage;
