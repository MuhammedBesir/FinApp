/**
 * Advanced WebSocket Service for Real-time Trading Data
 * Supports multiple channels: prices, signals, alerts, notifications
 */

// Channel types
export const ChannelType = {
  PRICE: "price",
  SIGNAL: "signal",
  ALERT: "alert",
  NOTIFICATION: "notification",
  SCREENER: "screener",
  ALL: "all",
};

// Event types
export const EventType = {
  CONNECTED: "connected",
  DISCONNECTED: "disconnected",
  PRICE_UPDATE: "price_update",
  NEW_SIGNAL: "new_signal",
  ALERT_TRIGGERED: "alert_triggered",
  NOTIFICATION: "notification",
  SCREENER_UPDATE: "screener_update",
  ERROR: "error",
  HEARTBEAT: "heartbeat",
};

class AdvancedWebSocketService {
  constructor() {
    this.ws = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.baseReconnectDelay = 1000;
    this.maxReconnectDelay = 30000;

    // Subscriptions
    this.subscribedChannels = new Set();
    this.subscribedTickers = new Set();
    this.userId = null;

    // Event listeners by channel
    this.listeners = {
      [ChannelType.PRICE]: new Map(),
      [ChannelType.SIGNAL]: new Map(),
      [ChannelType.ALERT]: new Map(),
      [ChannelType.NOTIFICATION]: new Map(),
      [ChannelType.SCREENER]: new Map(),
      system: new Map(),
    };

    // Global listeners (receive all events)
    this.globalListeners = new Set();

    // Connection state listeners
    this.connectionListeners = new Set();

    // Heartbeat
    this.heartbeatInterval = null;
    this.lastHeartbeat = null;

    // Message queue for offline mode
    this.messageQueue = [];

    // Stats
    this.stats = {
      messagesReceived: 0,
      messagesSent: 0,
      reconnects: 0,
    };
  }

  /**
   * Connect to WebSocket server
   * @param {Object} options - Connection options
   * @param {string[]} options.channels - Channels to subscribe
   * @param {string[]} options.tickers - Tickers to subscribe
   * @param {string} options.userId - User ID for targeted notifications
   */
  connect(options = {}) {
    const { channels = ["all"], tickers = [], userId = null } = options;

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log("[WebSocket] Already connected, updating subscriptions");
      this.updateSubscriptions(channels, tickers);
      return;
    }

    this.subscribedChannels = new Set(channels);
    this.subscribedTickers = new Set(tickers);
    this.userId = userId;

    // Build URL with query params
    let baseUrl = import.meta.env.VITE_WS_URL;

    // Safety check: Ignore localhost in production (common Vercel misconfig)
    if (baseUrl && baseUrl.includes('localhost') && !window.location.hostname.includes('localhost')) {
      console.warn('Ignoring localhost VITE_WS_URL in production');
      baseUrl = null;
    }
    
    if (!baseUrl) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      baseUrl = `${protocol}//${host}/ws/stream`;
    }

    const params = new URLSearchParams();
    params.set("channels", channels.join(","));
    if (tickers.length > 0) params.set("tickers", tickers.join(","));
    if (userId) params.set("user_id", userId);

    const wsUrl = `${baseUrl}?${params.toString()}`;

    console.log("[WebSocket] Connecting to:", wsUrl);

    // Check for Vercel environment - WebSockets are not supported on Python Serverless
    if (window.location.hostname.includes('vercel.app')) {
      console.warn("[WebSocket] Vercel environment detected. WebSockets are disabled (not supported on Serverless).");
      console.log("[WebSocket] Switching to polling mode is recommended (handled by individual components).");
      this.isConnected = false;
      return; // Do not attempt to connect
    }

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log("[WebSocket] Connected");
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.notifyConnectionListeners(true);
        this.startHeartbeat();
        this.flushMessageQueue();
      };

      this.ws.onmessage = (event) => {
        this.handleMessage(event);
      };

      this.ws.onerror = (error) => {
        console.error("[WebSocket] Error:", error);
        this.notifyListeners("system", EventType.ERROR, { error });
      };

      this.ws.onclose = (event) => {
        console.log("[WebSocket] Connection closed:", event.code, event.reason);
        this.isConnected = false;
        this.stopHeartbeat();
        this.notifyConnectionListeners(false);
        this.attemptReconnect();
      };
    } catch (error) {
      console.error("[WebSocket] Connection failed:", error);
      // Do not reconnect if it failed synchronously, likely invalid URL or environment
    }
  }

  /**
   * Handle incoming WebSocket message
   */
  handleMessage(event) {
    try {
      const message = JSON.parse(event.data);
      this.stats.messagesReceived++;

      const { channel, event: eventType, data, timestamp } = message;

      // Notify global listeners
      for (const listener of this.globalListeners) {
        try {
          listener(message);
        } catch (e) {
          console.error("[WebSocket] Global listener error:", e);
        }
      }

      // Notify channel-specific listeners
      this.notifyListeners(channel, eventType, data, timestamp);

      // Handle system events
      if (channel === "system") {
        this.handleSystemEvent(eventType, data);
      }
    } catch (error) {
      console.error("[WebSocket] Message parse error:", error);
    }
  }

  /**
   * Handle system events
   */
  handleSystemEvent(eventType, data) {
    switch (eventType) {
      case "connected":
        console.log("[WebSocket] Server confirmed connection:", data);
        break;
      case "subscribed":
        console.log("[WebSocket] Subscription updated:", data);
        break;
      case "pong":
        this.lastHeartbeat = Date.now();
        break;
      case "heartbeat":
        this.lastHeartbeat = Date.now();
        break;
    }
  }

  /**
   * Notify listeners for a specific channel/event
   */
  notifyListeners(channel, eventType, data, timestamp) {
    const channelListeners = this.listeners[channel];
    if (!channelListeners) return;

    // Notify event-specific listeners
    const eventListeners = channelListeners.get(eventType);
    if (eventListeners) {
      for (const listener of eventListeners) {
        try {
          listener(data, { channel, event: eventType, timestamp });
        } catch (e) {
          console.error("[WebSocket] Listener error:", e);
        }
      }
    }

    // Notify wildcard listeners (listen to all events in channel)
    const wildcardListeners = channelListeners.get("*");
    if (wildcardListeners) {
      for (const listener of wildcardListeners) {
        try {
          listener(data, { channel, event: eventType, timestamp });
        } catch (e) {
          console.error("[WebSocket] Wildcard listener error:", e);
        }
      }
    }
  }

  /**
   * Notify connection state listeners
   */
  notifyConnectionListeners(isConnected) {
    for (const listener of this.connectionListeners) {
      try {
        listener(isConnected);
      } catch (e) {
        console.error("[WebSocket] Connection listener error:", e);
      }
    }
  }

  /**
   * Send message to server
   */
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
      this.stats.messagesSent++;
    } else {
      // Queue message for when connection is restored
      this.messageQueue.push(data);
      console.log("[WebSocket] Message queued, not connected");
    }
  }

  /**
   * Flush message queue after reconnection
   */
  flushMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      this.send(message);
    }
  }

  /**
   * Subscribe to additional channels/tickers
   */
  subscribe(channels = [], tickers = []) {
    channels.forEach((c) => this.subscribedChannels.add(c));
    tickers.forEach((t) => this.subscribedTickers.add(t));

    this.send({
      action: "subscribe",
      channels,
      tickers,
    });
  }

  /**
   * Unsubscribe from channels/tickers
   */
  unsubscribe(channels = [], tickers = []) {
    channels.forEach((c) => this.subscribedChannels.delete(c));
    tickers.forEach((t) => this.subscribedTickers.delete(t));

    this.send({
      action: "unsubscribe",
      channels,
      tickers,
    });
  }

  /**
   * Update subscriptions (reconnect with new params)
   */
  updateSubscriptions(channels, tickers) {
    this.subscribe(channels, tickers);
  }

  /**
   * Add event listener for a channel
   * @param {string} channel - Channel name (price, signal, etc.)
   * @param {string} event - Event name (* for all events)
   * @param {Function} callback - Callback function
   */
  on(channel, event, callback) {
    if (!this.listeners[channel]) {
      this.listeners[channel] = new Map();
    }

    if (!this.listeners[channel].has(event)) {
      this.listeners[channel].set(event, new Set());
    }

    this.listeners[channel].get(event).add(callback);

    // Return unsubscribe function
    return () => this.off(channel, event, callback);
  }

  /**
   * Remove event listener
   */
  off(channel, event, callback) {
    const channelListeners = this.listeners[channel];
    if (!channelListeners) return;

    const eventListeners = channelListeners.get(event);
    if (eventListeners) {
      eventListeners.delete(callback);
    }
  }

  /**
   * Add global listener (receives all messages)
   */
  onAny(callback) {
    this.globalListeners.add(callback);
    return () => this.globalListeners.delete(callback);
  }

  /**
   * Add connection state listener
   */
  onConnectionChange(callback) {
    this.connectionListeners.add(callback);
    // Immediately notify with current state
    callback(this.isConnected);
    return () => this.connectionListeners.delete(callback);
  }

  // Convenience methods for specific channels

  /**
   * Listen to price updates
   */
  onPriceUpdate(callback, ticker = null) {
    if (ticker) {
      // Filter by ticker
      const wrappedCallback = (data, meta) => {
        if (data.ticker === ticker) {
          callback(data, meta);
        }
      };
      return this.on(
        ChannelType.PRICE,
        EventType.PRICE_UPDATE,
        wrappedCallback,
      );
    }
    return this.on(ChannelType.PRICE, EventType.PRICE_UPDATE, callback);
  }

  /**
   * Listen to trading signals
   */
  onSignal(callback, ticker = null) {
    if (ticker) {
      const wrappedCallback = (data, meta) => {
        if (data.ticker === ticker) {
          callback(data, meta);
        }
      };
      return this.on(ChannelType.SIGNAL, EventType.NEW_SIGNAL, wrappedCallback);
    }
    return this.on(ChannelType.SIGNAL, EventType.NEW_SIGNAL, callback);
  }

  /**
   * Listen to alerts
   */
  onAlert(callback) {
    return this.on(ChannelType.ALERT, EventType.ALERT_TRIGGERED, callback);
  }

  /**
   * Listen to notifications
   */
  onNotification(callback) {
    return this.on(ChannelType.NOTIFICATION, EventType.NOTIFICATION, callback);
  }

  /**
   * Listen to screener updates
   */
  onScreenerUpdate(callback) {
    return this.on(ChannelType.SCREENER, EventType.SCREENER_UPDATE, callback);
  }

  /**
   * Start heartbeat to keep connection alive
   */
  startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected) {
        this.send({ action: "ping", timestamp: Date.now() });
      }
    }, 25000); // Every 25 seconds
  }

  /**
   * Stop heartbeat
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("[WebSocket] Max reconnect attempts reached");
      return;
    }

    this.reconnectAttempts++;
    this.stats.reconnects++;

    const delay = Math.min(
      this.baseReconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay,
    );

    console.log(
      `[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`,
    );

    setTimeout(() => {
      this.connect({
        channels: Array.from(this.subscribedChannels),
        tickers: Array.from(this.subscribedTickers),
        userId: this.userId,
      });
    }, delay);
  }

  /**
   * Disconnect from server
   */
  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000, "Client disconnect");
      this.ws = null;
    }
    this.isConnected = false;
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent auto-reconnect
  }

  /**
   * Get connection statistics
   */
  getStats() {
    return {
      ...this.stats,
      isConnected: this.isConnected,
      subscribedChannels: Array.from(this.subscribedChannels),
      subscribedTickers: Array.from(this.subscribedTickers),
      reconnectAttempts: this.reconnectAttempts,
    };
  }
}

// Export singleton instance
const wsService = new AdvancedWebSocketService();
export default wsService;

// Also export class for testing/multiple instances
export { AdvancedWebSocketService };
