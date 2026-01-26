/**
 * API Client for Trading Bot Backend
 * Handles all HTTP requests to the FastAPI backend
 * With built-in caching to prevent rate limiting (429)
 */
import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "/api";

// ============ API Cache ============
const API_CACHE = new Map();
const CACHE_TTL = 60 * 1000; // 60 seconds cache
const RATE_LIMIT_DELAY = 500; // 500ms between requests
let lastRequestTime = 0;

// Cache helper functions
const getCached = (key) => {
  const cached = API_CACHE.get(key);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    console.log(`[API Cache] HIT: ${key}`);
    return cached.data;
  }
  return null;
};

const setCache = (key, data) => {
  API_CACHE.set(key, { data, timestamp: Date.now() });
  // Clean old cache entries
  if (API_CACHE.size > 100) {
    const oldest = [...API_CACHE.entries()]
      .sort((a, b) => a[1].timestamp - b[1].timestamp)[0];
    API_CACHE.delete(oldest[0]);
  }
};

// Rate limit helper
const waitForRateLimit = async () => {
  const now = Date.now();
  const timeSinceLastRequest = now - lastRequestTime;
  if (timeSinceLastRequest < RATE_LIMIT_DELAY) {
    await new Promise(r => setTimeout(r, RATE_LIMIT_DELAY - timeSinceLastRequest));
  }
  lastRequestTime = Date.now();
};

// Safety check: If API_URL is localhost but we are in production, force relative path
if (API_BASE_URL.includes('localhost') && typeof window !== 'undefined' && !window.location.hostname.includes('localhost')) {
  console.warn('⚠️ Detected localhost VITE_API_URL in production. Switching to relative path.');
  // We can't reassign const, so we need to refactor slightly or assume this runs before export
}
// Refactoring to let to allow reassignment
let finalApiUrl = API_BASE_URL;
if (finalApiUrl.includes('localhost') && typeof window !== 'undefined' && !window.location.hostname.includes('localhost')) {
   finalApiUrl = "/api";
}

// Create axios instance
const apiClient = axios.create({
  baseURL: finalApiUrl,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("authToken");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor for error handling and token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 errors (token expired)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem("refreshToken");
      if (refreshToken) {
        try {
          const response = await axios.post(`${finalApiUrl}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          if (response.data.success) {
            const newToken = response.data.data.access_token;
            localStorage.setItem("authToken", newToken);
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return apiClient(originalRequest);
          }
        } catch (refreshError) {
          // Refresh failed, clear auth data
          localStorage.removeItem("authToken");
          localStorage.removeItem("refreshToken");
          localStorage.removeItem("user");
          window.location.href = "/login";
        }
      }
    }

    if (import.meta.env.DEV) {
      console.error("[API Error]", error.response?.data || error.message);
    }
    return Promise.reject(error);
  },
);

// ============ Auth API ============
export const authApi = {
  // Login
  login: async (email, password, rememberMe = false) => {
    const response = await apiClient.post("/auth/login", {
      email,
      password,
      remember_me: rememberMe,
    });
    return response.data;
  },

  // Register
  register: async (fullName, email, password) => {
    const response = await apiClient.post("/auth/register", {
      full_name: fullName,
      email,
      password,
    });
    return response.data;
  },

  // Logout
  logout: async () => {
    const response = await apiClient.post("/auth/logout");
    return response.data;
  },

  // Verify token
  verifyToken: async () => {
    const response = await apiClient.get("/auth/verify");
    return response.data;
  },

  // Refresh token
  refreshToken: async (refreshToken) => {
    const response = await apiClient.post("/auth/refresh", {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  // Get current user
  getMe: async () => {
    const response = await apiClient.get("/auth/me");
    return response.data;
  },

  // Update profile
  updateProfile: async (updates) => {
    const response = await apiClient.put("/auth/me", updates);
    return response.data;
  },

  // Change password
  changePassword: async (currentPassword, newPassword) => {
    const response = await apiClient.post("/auth/change-password", {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  },
};

// ============ Portfolio API ============
export const portfolioApi = {
  // Get all portfolios
  getPortfolios: async () => {
    const response = await apiClient.get("/portfolio/");
    return response.data;
  },

  // Create portfolio
  createPortfolio: async (name, description = null, isDefault = false) => {
    const response = await apiClient.post("/portfolio/", {
      name,
      description,
      is_default: isDefault,
    });
    return response.data;
  },

  // Get portfolio by ID
  getPortfolio: async (portfolioId) => {
    const response = await apiClient.get(`/portfolio/${portfolioId}`);
    return response.data;
  },

  // Delete portfolio
  deletePortfolio: async (portfolioId) => {
    const response = await apiClient.delete(`/portfolio/${portfolioId}`);
    return response.data;
  },

  // Add transaction
  addTransaction: async (portfolioId, transaction) => {
    const response = await apiClient.post(
      `/portfolio/${portfolioId}/transactions`,
      transaction,
    );
    return response.data;
  },

  // Delete transaction
  deleteTransaction: async (portfolioId, transactionId) => {
    const response = await apiClient.delete(
      `/portfolio/${portfolioId}/transactions/${transactionId}`,
    );
    return response.data;
  },

  // Get watchlists
  getWatchlists: async () => {
    const response = await apiClient.get("/portfolio/watchlists/all");
    return response.data;
  },

  // Create watchlist
  createWatchlist: async (name, tickers = []) => {
    const response = await apiClient.post("/portfolio/watchlists", {
      name,
      tickers,
    });
    return response.data;
  },

  // Add to watchlist
  addToWatchlist: async (watchlistId, ticker) => {
    const response = await apiClient.post(
      `/portfolio/watchlists/${watchlistId}/add`,
      { ticker },
    );
    return response.data;
  },

  // Remove from watchlist
  removeFromWatchlist: async (watchlistId, ticker) => {
    const response = await apiClient.delete(
      `/portfolio/watchlists/${watchlistId}/remove/${ticker}`,
    );
    return response.data;
  },

  // Delete watchlist
  deleteWatchlist: async (watchlistId) => {
    const response = await apiClient.delete(
      `/portfolio/watchlists/${watchlistId}`,
    );
    return response.data;
  },
};

export const api = {
  // Stock Data (with cache)
  getStockData: async (ticker, interval = "5m", period = "1d") => {
    const cacheKey = `stockData:${ticker}:${interval}:${period}`;
    const cached = getCached(cacheKey);
    if (cached) return cached;
    
    await waitForRateLimit();
    const response = await apiClient.get(`/stocks/${ticker}/data`, {
      params: { interval, period },
    });
    setCache(cacheKey, response.data);
    return response.data;
  },

  // Technical Indicators (with cache)
  getIndicators: async (ticker, interval = "5m", period = "1d") => {
    const cacheKey = `indicators:${ticker}:${interval}:${period}`;
    const cached = getCached(cacheKey);
    if (cached) return cached;
    
    await waitForRateLimit();
    const response = await apiClient.get(`/stocks/${ticker}/indicators`, {
      params: { interval, period },
    });
    setCache(cacheKey, response.data);
    return response.data;
  },

  // Stock Info (with cache - longer TTL)
  getStockInfo: async (ticker) => {
    const cacheKey = `stockInfo:${ticker}`;
    const cached = getCached(cacheKey);
    if (cached) return cached;
    
    await waitForRateLimit();
    const response = await apiClient.get(`/stocks/${ticker}/info`);
    setCache(cacheKey, response.data);
    return response.data;
  },

  // Current Price (with short cache)
  getCurrentPrice: async (ticker) => {
    const cacheKey = `price:${ticker}`;
    const cached = getCached(cacheKey);
    if (cached) return cached;
    
    await waitForRateLimit();
    const response = await apiClient.get(`/stocks/${ticker}/current-price`);
    setCache(cacheKey, response.data);
    return response.data;
  },

  // Trading Signals (with cache)
  getSignals: async (
    ticker,
    strategy = "moderate",
    interval = "5m",
    period = "1d",
  ) => {
    const cacheKey = `signals:${ticker}:${strategy}:${interval}:${period}`;
    const cached = getCached(cacheKey);
    if (cached) return cached;
    
    await waitForRateLimit();
    const response = await apiClient.get(`/signals/${ticker}`, {
      params: { strategy, interval, period },
    });
    setCache(cacheKey, response.data);
    return response.data;
  },
  
  // Clear cache (useful after trading actions)
  clearCache: () => {
    API_CACHE.clear();
    console.log('[API Cache] Cleared');
  },

  // Backtesting
  runBacktest: async (config) => {
    const response = await apiClient.post("/backtest/", config);
    return response.data;
  },

  // Market Status
  getMarketStatus: async () => {
    const response = await apiClient.get("/market-status");
    return response.data;
  },

  // Health Check
  healthCheck: async () => {
    const response = await axios.get("/health");
    return response.data;
  },
};

export default api;
