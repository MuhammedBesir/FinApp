/**
 * Chat Page - Grup Sohbet Sayfası
 * Updated with Glassmorphism Design
 */
import React, { useState, useEffect, useRef } from "react";
import {
  MessageCircle,
  Send,
  Users,
  Hash,
  Smile,
  Reply,
  TrendingUp,
  Clock,
  ChevronLeft,
  MoreVertical,
  Share2,
  Sparkles,
  X,
} from "lucide-react";

const API_URL = "/api";

// Emoji seçici
const QUICK_EMOJIS = ["👍", "❤️", "😂", "🚀", "📈", "📉", "💰", "🔥"];

// Kullanıcı ID (gerçek uygulamada auth'dan gelir)
const getCurrentUser = () => ({
  id: `user_${Math.random().toString(36).substr(2, 9)}`,
  username: `Trader${Math.floor(Math.random() * 1000)}`,
});

export default function ChatPage() {
  const [rooms, setRooms] = useState([]);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [showRoomList, setShowRoomList] = useState(true);
  const [onlineCount, setOnlineCount] = useState(0);
  const [user] = useState(getCurrentUser);
  const [replyTo, setReplyTo] = useState(null);
  const messagesEndRef = useRef(null);

  // Odaları yükle
  useEffect(() => {
    fetchRooms();
  }, []);

  // Oda seçildiğinde mesajları yükle
  useEffect(() => {
    if (selectedRoom) {
      fetchMessages(selectedRoom.id);
      joinRoom(selectedRoom.id);

      // Her 5 saniyede mesajları güncelle
      const interval = setInterval(() => {
        fetchMessages(selectedRoom.id);
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [selectedRoom]);

  // Yeni mesaj geldiğinde scroll
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchRooms = async () => {
    try {
      const res = await fetch(`${API_URL}/chat/rooms`);
      const data = await res.json();
      if (data.success) {
        setRooms(data.rooms);
        setOnlineCount(data.total_online);
        if (data.rooms.length > 0 && !selectedRoom) {
          setSelectedRoom(data.rooms[0]);
        }
      }
    } catch (error) {
      console.error("Error fetching rooms:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMessages = async (roomId) => {
    try {
      const res = await fetch(
        `${API_URL}/chat/rooms/${roomId}/messages?limit=50`,
      );
      const data = await res.json();
      if (data.success) {
        setMessages(data.messages);
      }
    } catch (error) {
      console.error("Error fetching messages:", error);
    }
  };

  const joinRoom = async (roomId) => {
    try {
      await fetch(`${API_URL}/chat/rooms/${roomId}/join`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.id, username: user.username }),
      });
    } catch (error) {
      console.error("Error joining room:", error);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedRoom) return;

    try {
      const res = await fetch(
        `${API_URL}/chat/rooms/${selectedRoom.id}/messages`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: user.id,
            username: user.username,
            content: newMessage,
            message_type: "text",
            reply_to: replyTo?.id || null,
          }),
        },
      );

      const data = await res.json();
      if (data.success) {
        setMessages([...messages, data.message]);
        setNewMessage("");
        setReplyTo(null);
      }
    } catch (error) {
      console.error("Error sending message:", error);
    }
  };

  const addReaction = async (messageId, emoji) => {
    try {
      await fetch(
        `${API_URL}/chat/rooms/${selectedRoom.id}/messages/${messageId}/reactions`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: user.id, emoji }),
        },
      );
      fetchMessages(selectedRoom.id);
    } catch (error) {
      console.error("Error adding reaction:", error);
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("tr-TR", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return "Bugün";
    } else if (date.toDateString() === yesterday.toDateString()) {
      return "Dün";
    }
    return date.toLocaleDateString("tr-TR", { day: "numeric", month: "long" });
  };

  // Mesaj türüne göre render
  const renderMessage = (msg, index, prevMsg) => {
    const showDateSeparator =
      index === 0 ||
      formatDate(msg.timestamp) !== formatDate(prevMsg?.timestamp);
    const isOwn = msg.user_id === user.id;
    const isSystem = msg.message_type === "system";

    return (
      <React.Fragment key={msg.id}>
        {showDateSeparator && (
          <div className="flex items-center justify-center my-6">
            <div className="px-4 py-1.5 text-xs font-medium rounded-full glass border border-[var(--glass-border)] text-theme-muted">
              {formatDate(msg.timestamp)}
            </div>
          </div>
        )}

        {isSystem ? (
          <div className="flex justify-center my-3">
            <div className="px-5 py-2.5 text-sm text-theme-muted glass border border-[var(--glass-border)] rounded-xl">
              {msg.content}
            </div>
          </div>
        ) : (
          <div
            className={`flex ${isOwn ? "justify-end" : "justify-start"} mb-4 animate-fade-in`}
            style={{ animationDelay: `${index * 20}ms` }}
          >
            <div className={`max-w-[75%] ${isOwn ? "order-2" : ""}`}>
              {/* Username */}
              {!isOwn && (
                <div className="text-xs font-medium text-theme-muted mb-1.5 ml-2">
                  {msg.username}
                </div>
              )}

              {/* Reply Preview */}
              {msg.reply_to && (
                <div className="text-xs glass border-l-2 border-primary-500 px-3 py-1.5 rounded-lg mb-2">
                  Yanıt...
                </div>
              )}

              {/* Message Bubble */}
              <div
                className={`group relative px-5 py-3 rounded-2xl ${
                  isOwn
                    ? "bg-gradient-to-br from-primary-500 to-primary-600 text-white rounded-br-sm shadow-lg shadow-primary-500/20"
                    : "glass border border-[var(--glass-border)] text-theme-text rounded-bl-sm"
                } ${msg.message_type === "trade_share" ? "border-l-4 border-success" : ""}`}
              >
                {/* Stock mentions */}
                <div className="text-sm whitespace-pre-wrap leading-relaxed">
                  {msg.content.split(/(\$[A-Z]{3,5})/g).map((part, i) =>
                    part.match(/^\$[A-Z]{3,5}$/) ? (
                      <span
                        key={i}
                        className={`font-bold ${isOwn ? "text-warning" : "text-warning"}`}
                      >
                        {part}
                      </span>
                    ) : (
                      part
                    ),
                  )}
                </div>

                {/* Time */}
                <div
                  className={`text-[10px] mt-2 ${
                    isOwn ? "text-white/60" : "text-theme-muted"
                  }`}
                >
                  {formatTime(msg.timestamp)}
                </div>

                {/* Quick Actions - Glass Style */}
                <div className="absolute -bottom-2 right-2 hidden group-hover:flex gap-1.5 glass border border-[var(--glass-border)] rounded-full shadow-xl px-2 py-1.5 animate-fade-in">
                  {QUICK_EMOJIS.slice(0, 4).map((emoji) => (
                    <button
                      key={emoji}
                      onClick={() => addReaction(msg.id, emoji)}
                      className="hover:scale-125 transition-transform text-sm"
                    >
                      {emoji}
                    </button>
                  ))}
                  <button
                    onClick={() => setReplyTo(msg)}
                    className="text-theme-muted hover:text-primary-400 ml-1 transition-colors"
                  >
                    <Reply size={14} />
                  </button>
                </div>
              </div>

              {/* Reactions - Glass Style */}
              {Object.keys(msg.reactions || {}).length > 0 && (
                <div className="flex gap-1.5 mt-2 ml-2">
                  {Object.entries(msg.reactions).map(([emoji, users]) => (
                    <button
                      key={emoji}
                      onClick={() => addReaction(msg.id, emoji)}
                      className="flex items-center gap-1 px-2.5 py-1 text-xs glass border border-[var(--glass-border)] rounded-full hover:border-primary-500/50 transition-all"
                    >
                      {emoji}{" "}
                      <span className="text-theme-muted font-medium">
                        {users.length}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </React.Fragment>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-120px)]">
        <div className="relative">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-500 animate-pulse" />
          <div className="absolute inset-0 w-16 h-16 rounded-2xl border-2 border-primary-500 border-t-transparent animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-100px)] sm:h-[calc(100vh-120px)] card p-0 overflow-hidden relative">
      {/* Background Effects */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-0 w-48 sm:w-64 h-48 sm:h-64 bg-primary-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-48 sm:w-64 h-48 sm:h-64 bg-accent-500/5 rounded-full blur-3xl" />
      </div>

      {/* Room List Sidebar - Glass */}
      <div
        className={`${
          showRoomList ? "w-full sm:w-80" : "w-0"
        } transition-all duration-300 border-r border-[var(--glass-border)] overflow-hidden relative z-10`}
      >
        <div className="h-full flex flex-col glass">
          {/* Header */}
          <div className="p-3 sm:p-5 border-b border-[var(--glass-border)]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 sm:gap-3">
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shadow-lg shadow-primary-500/20">
                  <MessageCircle className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                </div>
                <h2 className="text-base sm:text-lg font-bold text-gradient">
                  Sohbet Odaları
                </h2>
              </div>
              <div className="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1 sm:py-1.5 rounded-xl glass border border-[var(--glass-border)]">
                <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-success rounded-full animate-pulse" />
                <span className="text-[10px] sm:text-xs font-medium text-theme-muted">
                  {onlineCount}
                </span>
              </div>
            </div>
          </div>

          {/* Room List */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {rooms.map((room, i) => (
              <button
                key={room.id}
                onClick={() => {
                  setSelectedRoom(room);
                  setShowRoomList(window.innerWidth >= 768);
                }}
                className={`w-full p-4 rounded-2xl text-left transition-all duration-300 ${
                  selectedRoom?.id === room.id
                    ? "glass border-2 border-primary-500 shadow-lg shadow-primary-500/10"
                    : "glass border border-[var(--glass-border)] hover:border-primary-500/50"
                }`}
                style={{ animationDelay: `${i * 50}ms` }}
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center text-2xl border border-[var(--glass-border)]">
                    {room.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-theme-text truncate">
                      {room.name}
                    </div>
                    <div className="text-xs text-theme-muted truncate mt-0.5">
                      {room.description}
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>

          {/* User Info - Glass Card */}
          <div className="p-4 border-t border-[var(--glass-border)]">
            <div className="flex items-center gap-3 p-3 rounded-xl glass border border-[var(--glass-border)]">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-success to-emerald-600 flex items-center justify-center text-white font-bold shadow-lg shadow-success/20">
                {user.username.charAt(0)}
              </div>
              <div className="flex-1">
                <div className="font-semibold text-theme-text">
                  {user.username}
                </div>
                <div className="text-xs text-success flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-success animate-pulse"></span>
                  Çevrimiçi
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col relative z-10">
        {selectedRoom ? (
          <>
            {/* Chat Header - Glass */}
            <div className="p-5 border-b border-[var(--glass-border)] glass flex items-center gap-4">
              <button
                onClick={() => setShowRoomList(!showRoomList)}
                className="p-2.5 glass border border-[var(--glass-border)] hover:border-primary-500/50 rounded-xl md:hidden transition-all"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-xl shadow-lg shadow-primary-500/20">
                {selectedRoom.icon}
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-theme-text">
                  {selectedRoom.name}
                </h3>
                <p className="text-xs text-theme-muted">
                  {selectedRoom.description}
                </p>
              </div>
              <button className="p-2.5 glass border border-[var(--glass-border)] hover:border-primary-500/50 rounded-xl transition-all">
                <MoreVertical size={20} className="text-theme-muted" />
              </button>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-5 space-y-1">
              {messages.map((msg, index) =>
                renderMessage(msg, index, messages[index - 1]),
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Reply Preview - Glass */}
            {replyTo && (
              <div className="px-5 py-3 glass border-t border-[var(--glass-border)] flex items-center gap-3 animate-fade-in">
                <div className="w-1 h-8 bg-gradient-to-b from-primary-500 to-accent-500 rounded-full" />
                <Reply size={16} className="text-primary-400" />
                <div className="flex-1 text-sm text-theme-muted truncate">
                  <span className="font-semibold text-theme-text">
                    {replyTo.username}:
                  </span>{" "}
                  {replyTo.content}
                </div>
                <button
                  onClick={() => setReplyTo(null)}
                  className="p-1.5 glass rounded-lg hover:bg-danger/20 transition-colors"
                >
                  <X size={14} className="text-theme-muted hover:text-danger" />
                </button>
              </div>
            )}

            {/* Input Area - Glass */}
            <div className="p-5 border-t border-[var(--glass-border)] glass">
              <div className="flex items-center gap-3">
                <div className="flex-1 flex items-center glass border border-[var(--glass-border)] rounded-2xl focus-within:border-primary-500/50 focus-within:shadow-lg focus-within:shadow-primary-500/10 transition-all">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && sendMessage()}
                    placeholder="Mesajınızı yazın... ($THYAO gibi hisse sembolleri kullanın)"
                    className="flex-1 px-5 py-3.5 bg-transparent focus:outline-none text-theme-text placeholder-theme-muted/50"
                  />
                  <button className="p-2 mr-2 text-theme-muted hover:text-warning transition-colors">
                    <Smile size={20} />
                  </button>
                </div>
                <button
                  onClick={sendMessage}
                  disabled={!newMessage.trim()}
                  className="p-4 bg-gradient-to-br from-primary-500 to-accent-500 text-white rounded-2xl hover:shadow-xl hover:shadow-primary-500/30 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:shadow-none transition-all duration-300"
                >
                  <Send size={20} />
                </button>
              </div>
              <div className="mt-3 flex items-center gap-2 text-xs text-theme-muted">
                <TrendingUp size={12} className="text-warning" />
                <span>
                  İpucu:{" "}
                  <span className="px-1.5 py-0.5 rounded glass">$THYAO</span>{" "}
                  formatında hisse sembolleri kullanarak hisseleri
                  vurgulayabilirsiniz
                </span>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center animate-fade-in">
              <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-primary-500/10 to-accent-500/10 flex items-center justify-center border border-[var(--glass-border)]">
                <MessageCircle size={40} className="text-theme-muted" />
              </div>
              <h3 className="text-lg font-bold text-theme-text mb-2">
                Bir sohbet odası seçin
              </h3>
              <p className="text-sm text-theme-muted">
                Yatırımcı topluluğuyla iletişime geçin
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
