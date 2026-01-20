/**
 * useWebSocket Hook - Real-time data subscription
 * Provides easy access to WebSocket service in React components
 */
import { useState, useEffect, useCallback, useRef } from "react";
import wsService, {
  ChannelType,
  EventType,
} from "../services/WebSocketService";

/**
 * Hook for WebSocket connection management
 * @param {Object} options - Connection options
 * @returns {Object} WebSocket state and methods
 */
export const useWebSocket = (options = {}) => {
  const {
    channels = ["all"],
    tickers = [],
    userId = null,
    autoConnect = true,
  } = options;

  const [isConnected, setIsConnected] = useState(wsService.isConnected);
  const [stats, setStats] = useState(wsService.getStats());

  useEffect(() => {
    // Subscribe to connection changes
    const unsubscribe = wsService.onConnectionChange((connected) => {
      setIsConnected(connected);
      setStats(wsService.getStats());
    });

    // Auto connect if enabled
    if (autoConnect && !wsService.isConnected) {
      wsService.connect({ channels, tickers, userId });
    }

    return () => {
      unsubscribe();
    };
  }, [autoConnect, channels.join(","), tickers.join(","), userId]);

  const connect = useCallback(() => {
    wsService.connect({ channels, tickers, userId });
  }, [channels, tickers, userId]);

  const disconnect = useCallback(() => {
    wsService.disconnect();
  }, []);

  const subscribe = useCallback((newChannels, newTickers) => {
    wsService.subscribe(newChannels, newTickers);
  }, []);

  const unsubscribe = useCallback((channels, tickers) => {
    wsService.unsubscribe(channels, tickers);
  }, []);

  return {
    isConnected,
    stats,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    wsService,
  };
};

/**
 * Hook for real-time price updates
 * @param {string|string[]} tickers - Ticker(s) to subscribe
 * @returns {Object} Price data and loading state
 */
export const useRealtimePrice = (tickers) => {
  const tickerArray = Array.isArray(tickers) ? tickers : [tickers];
  const [prices, setPrices] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const unsubscribesRef = useRef([]);

  useEffect(() => {
    if (!tickers || tickerArray.length === 0) return;

    // Connect with price channel and specified tickers
    if (!wsService.isConnected) {
      wsService.connect({
        channels: [ChannelType.PRICE],
        tickers: tickerArray,
      });
    } else {
      // Subscribe to additional tickers
      wsService.subscribe([ChannelType.PRICE], tickerArray);
    }

    // Listen for price updates
    const unsubscribes = tickerArray.map((ticker) => {
      return wsService.onPriceUpdate((data) => {
        setIsLoading(false);
        setPrices((prev) => ({
          ...prev,
          [data.ticker]: {
            ...data,
            updatedAt: new Date(),
          },
        }));
      }, ticker);
    });

    unsubscribesRef.current = unsubscribes;

    return () => {
      unsubscribes.forEach((unsub) => unsub());
    };
  }, [tickerArray.join(",")]);

  // Get single ticker price for convenience
  const price = tickerArray.length === 1 ? prices[tickerArray[0]] : null;

  return {
    prices,
    price,
    isLoading,
    isConnected: wsService.isConnected,
  };
};

/**
 * Hook for real-time trading signals
 * @param {string} ticker - Optional ticker filter
 * @returns {Object} Signals and state
 */
export const useRealtimeSignals = (ticker = null) => {
  const [signals, setSignals] = useState([]);
  const [latestSignal, setLatestSignal] = useState(null);

  useEffect(() => {
    // Connect with signal channel
    if (!wsService.isConnected) {
      wsService.connect({
        channels: [ChannelType.SIGNAL],
        tickers: ticker ? [ticker] : [],
      });
    }

    const unsubscribe = wsService.onSignal((data) => {
      setLatestSignal(data);
      setSignals((prev) => [data, ...prev.slice(0, 49)]); // Keep last 50
    }, ticker);

    return () => unsubscribe();
  }, [ticker]);

  return {
    signals,
    latestSignal,
    isConnected: wsService.isConnected,
  };
};

/**
 * Hook for notifications
 * @returns {Object} Notifications state and methods
 */
export const useNotifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    // Connect with notification channel
    if (!wsService.isConnected) {
      wsService.connect({
        channels: [ChannelType.NOTIFICATION],
      });
    }

    const unsubscribe = wsService.onNotification((data) => {
      const notification = {
        id: Date.now(),
        ...data,
        read: false,
        receivedAt: new Date(),
      };

      setNotifications((prev) => [notification, ...prev.slice(0, 99)]); // Keep last 100
      setUnreadCount((prev) => prev + 1);

      // Show browser notification if permitted
      if (Notification.permission === "granted") {
        new Notification(data.title, {
          body: data.body,
          icon: "/favicon.ico",
        });
      }
    });

    return () => unsubscribe();
  }, []);

  const markAsRead = useCallback((notificationId) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === notificationId ? { ...n, read: true } : n)),
    );
    setUnreadCount((prev) => Math.max(0, prev - 1));
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    setUnreadCount(0);
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
    setUnreadCount(0);
  }, []);

  const requestPermission = useCallback(async () => {
    if ("Notification" in window) {
      const permission = await Notification.requestPermission();
      return permission === "granted";
    }
    return false;
  }, []);

  return {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    clearAll,
    requestPermission,
    isConnected: wsService.isConnected,
  };
};

/**
 * Hook for price alerts
 * @returns {Object} Alerts state
 */
export const useAlerts = () => {
  const [triggeredAlerts, setTriggeredAlerts] = useState([]);

  useEffect(() => {
    if (!wsService.isConnected) {
      wsService.connect({
        channels: [ChannelType.ALERT],
      });
    }

    const unsubscribe = wsService.onAlert((data) => {
      setTriggeredAlerts((prev) => [
        { ...data, triggeredAt: new Date() },
        ...prev.slice(0, 49),
      ]);
    });

    return () => unsubscribe();
  }, []);

  return {
    triggeredAlerts,
    isConnected: wsService.isConnected,
  };
};

/**
 * Hook for screener updates
 * @returns {Object} Screener results
 */
export const useRealtimeScreener = () => {
  const [screenerResults, setScreenerResults] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    if (!wsService.isConnected) {
      wsService.connect({
        channels: [ChannelType.SCREENER],
      });
    }

    const unsubscribe = wsService.onScreenerUpdate((data) => {
      setScreenerResults(data);
      setLastUpdated(new Date());
    });

    return () => unsubscribe();
  }, []);

  return {
    screenerResults,
    lastUpdated,
    isConnected: wsService.isConnected,
  };
};

export default useWebSocket;
