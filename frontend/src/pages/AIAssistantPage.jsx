/**
 * AI Assistant Page - Modern AI Trading Asistan Sayfası
 * Updated with Glassmorphism Design
 */
import React, { useState, useEffect, useRef } from "react";
import {
  Bot,
  Send,
  Sparkles,
  TrendingUp,
  BarChart3,
  Shield,
  Briefcase,
  Trash2,
  Loader2,
  Activity,
  AlertTriangle,
  Zap,
  MessageSquare,
} from "lucide-react";
import { usePortfolioStore } from "../store/portfolioStore";

const API_URL = "http://localhost:8000/api";

// Kullanıcı ID
const getUserId = () => {
  let userId = localStorage.getItem("ai_user_id");
  if (!userId) {
    userId = `user_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem("ai_user_id", userId);
  }
  return userId;
};

// İkon mapper
const iconMap = {
  briefcase: Briefcase,
  "trending-up": TrendingUp,
  "bar-chart": BarChart3,
  shield: Shield,
  activity: Activity,
  "alert-triangle": AlertTriangle,
};

export default function AIAssistantPage() {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [quickActions, setQuickActions] = useState([]);
  const [typing, setTyping] = useState(false);
  const [showActions, setShowActions] = useState(true);
  const [userId] = useState(getUserId);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Portfolio store
  const { holdings, trades, getTradeStats } = usePortfolioStore();

  useEffect(() => {
    fetchQuickActions();
    fetchHistory();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, typing]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchQuickActions = async () => {
    try {
      const res = await fetch(`${API_URL}/ai/quick-actions`);
      const data = await res.json();
      if (data.success) {
        setQuickActions(data.actions);
      }
    } catch (error) {
      console.error("Error fetching actions:", error);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_URL}/ai/history/${userId}?limit=20`);
      const data = await res.json();
      if (data.success && data.messages.length > 0) {
        setMessages(data.messages);
        setShowActions(false);
      }
    } catch (error) {
      console.error("Error fetching history:", error);
    }
  };

  const sendMessage = async (messageText = null, context = null) => {
    const text = messageText || newMessage.trim();
    if (!text || loading) return;

    const userMessage = {
      id: `user_${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setNewMessage("");
    setLoading(true);
    setTyping(true);
    setShowActions(false);

    try {
      const res = await fetch(`${API_URL}/ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, user_id: userId, context }),
      });

      const data = await res.json();
      await new Promise((resolve) => setTimeout(resolve, 300));

      if (data.success) {
        setMessages((prev) => [...prev, data.response]);
      }
    } catch (error) {
      console.error("Error:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: `error_${Date.now()}`,
          role: "assistant",
          content: "⚠️ Bir hata oluştu. Lütfen tekrar deneyin.",
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
      setTyping(false);
      inputRef.current?.focus();
    }
  };

  const handleQuickAction = async (actionId) => {
    switch (actionId) {
      case "portfolio":
        await analyzePortfolio();
        break;
      case "market":
        await getMarketSummary();
        break;
      case "rsi":
        sendMessage("RSI nedir ve nasıl yorumlanır?");
        break;
      case "stoploss":
        sendMessage("Stop-loss stratejileri nelerdir?");
        break;
      case "macd":
        sendMessage("MACD indikatörü nasıl kullanılır?");
        break;
      case "risk":
        sendMessage("Risk yönetimi nasıl yapılır?");
        break;
      default:
        break;
    }
  };

  const analyzePortfolio = async () => {
    const userMessage = {
      id: `user_${Date.now()}`,
      role: "user",
      content: "📊 Portföyümü analiz et",
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setTyping(true);
    setShowActions(false);

    try {
      const stats = getTradeStats();
      const res = await fetch(`${API_URL}/ai/portfolio-analysis`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ holdings, trades, stats }),
      });

      const data = await res.json();
      await new Promise((resolve) => setTimeout(resolve, 300));

      if (data.success) {
        setMessages((prev) => [
          ...prev,
          {
            id: `ai_${Date.now()}`,
            role: "assistant",
            content: data.analysis,
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
      setTyping(false);
    }
  };

  const getMarketSummary = async () => {
    const userMessage = {
      id: `user_${Date.now()}`,
      role: "user",
      content: "📈 Piyasa özeti ver",
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setTyping(true);
    setShowActions(false);

    try {
      const res = await fetch(`${API_URL}/ai/market-summary`);
      const data = await res.json();
      await new Promise((resolve) => setTimeout(resolve, 300));

      if (data.success) {
        setMessages((prev) => [
          ...prev,
          {
            id: `ai_${Date.now()}`,
            role: "assistant",
            content: data.summary,
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
      setTyping(false);
    }
  };

  const clearHistory = async () => {
    try {
      await fetch(`${API_URL}/ai/history/${userId}`, { method: "DELETE" });
      setMessages([]);
      setShowActions(true);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString("tr-TR", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatContent = (content) => {
    let formatted = content
      .replace(
        /\$([A-Z]{3,5})/g,
        '<span class="text-yellow-500 font-semibold">$$$1</span>',
      )
      .replace(
        /\*\*(.+?)\*\*/g,
        '<strong class="font-semibold text-theme-text">$1</strong>',
      )
      .replace(/^• /gm, '<span class="text-primary">•</span> ')
      .replace(/\n/g, "<br />");
    return formatted;
  };

  const colorMap = {
    blue: "glass border border-blue-500/20 text-blue-400 hover:border-blue-500/50 hover:shadow-lg hover:shadow-blue-500/10",
    green:
      "glass border border-emerald-500/20 text-emerald-400 hover:border-emerald-500/50 hover:shadow-lg hover:shadow-emerald-500/10",
    purple:
      "glass border border-purple-500/20 text-purple-400 hover:border-purple-500/50 hover:shadow-lg hover:shadow-purple-500/10",
    red: "glass border border-red-500/20 text-red-400 hover:border-red-500/50 hover:shadow-lg hover:shadow-red-500/10",
    orange:
      "glass border border-orange-500/20 text-orange-400 hover:border-orange-500/50 hover:shadow-lg hover:shadow-orange-500/10",
    yellow:
      "glass border border-yellow-500/20 text-yellow-400 hover:border-yellow-500/50 hover:shadow-lg hover:shadow-yellow-500/10",
  };

  return (
    <div className="h-[calc(100vh-100px)] sm:h-[calc(100vh-120px)] flex flex-col relative">
      {/* Background Gradient Effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-48 sm:w-96 h-48 sm:h-96 bg-primary-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-48 sm:w-96 h-48 sm:h-96 bg-accent-500/5 rounded-full blur-3xl" />
      </div>

      {/* Glass Header */}
      <div className="relative px-4 sm:px-6 py-3 sm:py-4 glass border-b border-[var(--glass-border)]">
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          <div className="flex items-center gap-3 sm:gap-4">
            <div className="relative">
              <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl sm:rounded-2xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shadow-xl shadow-primary-500/30">
                <Sparkles className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
              </div>
              <div className="absolute -bottom-1 -right-1 w-3 h-3 sm:w-4 sm:h-4 bg-success rounded-full border-2 border-[var(--color-bg-primary)] animate-pulse" />
            </div>
            <div>
              <h1 className="text-lg sm:text-xl font-bold text-gradient">AI Asistan</h1>
              <p className="text-[10px] sm:text-xs text-theme-muted flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-success rounded-full" />
                Trading & Portföy Analizi
              </p>
            </div>
          </div>
          {messages.length > 0 && (
            <button
              onClick={clearHistory}
              className="p-2 sm:p-2.5 glass border border-[var(--glass-border)] text-theme-muted hover:text-danger hover:border-danger/50 rounded-xl transition-all duration-300"
              title="Sohbeti Temizle"
            >
              <Trash2 size={16} className="sm:w-[18px] sm:h-[18px]" />
            </button>
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto relative">
        <div className="max-w-4xl mx-auto px-3 sm:px-4 py-4 sm:py-6">
          {/* Welcome State */}
          {messages.length === 0 && showActions && (
            <div className="flex flex-col items-center justify-center min-h-[50vh] sm:min-h-[60vh] animate-fade-in">
              {/* Hero Icon */}
              <div className="relative mb-6 sm:mb-8">
                <div className="w-16 h-16 sm:w-24 sm:h-24 rounded-2xl sm:rounded-3xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shadow-2xl shadow-primary-500/40">
                  <Bot className="w-8 h-8 sm:w-12 sm:h-12 text-white" />
                </div>
                <div className="absolute -top-1 -right-1 sm:-top-2 sm:-right-2 w-6 h-6 sm:w-8 sm:h-8 rounded-lg sm:rounded-xl bg-gradient-to-br from-success to-emerald-600 flex items-center justify-center shadow-lg">
                  <Sparkles className="w-3 h-3 sm:w-4 sm:h-4 text-white" />
                </div>
              </div>

              <h2 className="text-2xl sm:text-3xl font-bold text-gradient mb-2 sm:mb-3 text-center">
                Nasıl yardımcı olabilirim?
              </h2>
              <p className="text-theme-muted text-center mb-6 sm:mb-10 max-w-md leading-relaxed text-sm sm:text-base px-4">
                Trading stratejileri, teknik analiz veya portföy yönetimi
                hakkında sorularınızı yanıtlayabilirim.
              </p>

              {/* Quick Actions Grid - Glassmorphism */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 sm:gap-4 w-full max-w-2xl px-2 sm:px-0">
                {quickActions.map((action, i) => {
                  const IconComponent = iconMap[action.icon] || Zap;
                  return (
                    <button
                      key={action.id}
                      onClick={() => handleQuickAction(action.id)}
                      className={`flex items-center gap-3 p-5 rounded-2xl transition-all duration-300 ${colorMap[action.color]} group`}
                      style={{ animationDelay: `${i * 50}ms` }}
                    >
                      <div className="w-10 h-10 rounded-xl glass flex items-center justify-center group-hover:scale-110 transition-transform">
                        <IconComponent className="w-5 h-5" />
                      </div>
                      <span className="text-sm font-semibold text-left text-theme-text">
                        {action.label}
                      </span>
                    </button>
                  );
                })}
              </div>

              {/* Sample Questions - Pill Style */}
              <div className="mt-10 text-center">
                <p className="text-xs text-theme-muted mb-4 flex items-center justify-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  veya bir soru sorun
                </p>
                <div className="flex flex-wrap justify-center gap-3">
                  {[
                    "$THYAO analiz et",
                    "Fibonacci seviyeleri nedir?",
                    "Pozisyon boyutlandırma",
                  ].map((q, i) => (
                    <button
                      key={i}
                      onClick={() => sendMessage(q)}
                      className="px-5 py-2.5 text-sm glass border border-[var(--glass-border)] text-theme-muted rounded-full hover:text-primary-400 hover:border-primary-500/50 transition-all duration-300"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Messages */}
          <div className="space-y-5">
            {messages.map((msg, index) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-fade-in-up`}
                style={{ animationDelay: `${index * 30}ms` }}
              >
                <div
                  className={`max-w-[85%] ${msg.role === "user" ? "" : "flex gap-4"}`}
                >
                  {msg.role === "assistant" && (
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center flex-shrink-0 mt-1 shadow-lg shadow-primary-500/20">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                  )}
                  <div
                    className={`px-5 py-4 ${
                      msg.role === "user"
                        ? "bg-gradient-to-br from-primary-500 to-primary-600 text-white rounded-2xl rounded-br-md shadow-lg shadow-primary-500/20"
                        : "glass border border-[var(--glass-border)] text-theme-text rounded-2xl rounded-bl-md"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      <div
                        className="text-sm leading-relaxed"
                        dangerouslySetInnerHTML={{
                          __html: formatContent(msg.content),
                        }}
                      />
                    ) : (
                      <div className="text-sm">{msg.content}</div>
                    )}
                    <div
                      className={`text-[10px] mt-3 ${
                        msg.role === "user"
                          ? "text-white/60"
                          : "text-theme-muted"
                      }`}
                    >
                      {formatTime(msg.timestamp)}
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {/* Typing Indicator - Glass Style */}
            {typing && (
              <div className="flex justify-start animate-fade-in">
                <div className="flex gap-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center flex-shrink-0 shadow-lg shadow-primary-500/20">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div className="glass border border-[var(--glass-border)] rounded-2xl rounded-bl-md px-5 py-4">
                    <div className="flex items-center gap-1.5">
                      <div
                        className="w-2.5 h-2.5 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full animate-bounce"
                        style={{ animationDelay: "0ms" }}
                      />
                      <div
                        className="w-2.5 h-2.5 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full animate-bounce"
                        style={{ animationDelay: "150ms" }}
                      />
                      <div
                        className="w-2.5 h-2.5 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full animate-bounce"
                        style={{ animationDelay: "300ms" }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Quick Actions Bar (when chatting) - Glass Style */}
      {messages.length > 0 && !loading && (
        <div className="relative glass border-t border-[var(--glass-border)]">
          <div className="max-w-4xl mx-auto px-4 py-3">
            <div className="flex gap-3 overflow-x-auto scrollbar-hide">
              {quickActions.slice(0, 4).map((action) => {
                const IconComponent = iconMap[action.icon] || Zap;
                return (
                  <button
                    key={action.id}
                    onClick={() => handleQuickAction(action.id)}
                    className="flex items-center gap-2 px-4 py-2 glass border border-[var(--glass-border)] text-theme-muted rounded-xl text-xs font-medium hover:text-primary-400 hover:border-primary-500/50 transition-all duration-300 flex-shrink-0"
                  >
                    <IconComponent size={14} />
                    {action.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Input Area - Glass Design */}
      <div className="relative glass border-t border-[var(--glass-border)]">
        <div className="max-w-4xl mx-auto px-4 py-5">
          <div className="flex items-center gap-4">
            <div className="flex-1 flex items-center glass border border-[var(--glass-border)] rounded-2xl focus-within:border-primary-500/50 focus-within:shadow-lg focus-within:shadow-primary-500/10 transition-all duration-300">
              <input
                ref={inputRef}
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && sendMessage()}
                placeholder="Mesajınızı yazın..."
                disabled={loading}
                className="flex-1 px-5 py-4 bg-transparent focus:outline-none text-theme-text placeholder-theme-muted/50 text-sm disabled:opacity-50"
              />
            </div>
            <button
              onClick={() => sendMessage()}
              disabled={!newMessage.trim() || loading}
              className="p-4 bg-gradient-to-br from-primary-500 to-accent-500 text-white rounded-2xl hover:shadow-xl hover:shadow-primary-500/30 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:shadow-none transition-all duration-300"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
          <p className="text-xs text-theme-muted/70 text-center mt-3">
            <span className="px-2 py-1 rounded-md glass">$THYAO</span> gibi
            sembollerle hisse analizi isteyebilirsiniz
          </p>
        </div>
      </div>
    </div>
  );
}
