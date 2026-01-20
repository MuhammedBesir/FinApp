/**
 * Auth Context - User Authentication State Management
 * Real JWT authentication with backend API
 */
import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import { authApi } from "../services/api";

const AuthContext = createContext(null);

// Token storage keys
const TOKEN_KEY = "authToken";
const REFRESH_TOKEN_KEY = "refreshToken";
const USER_KEY = "user";

// Get initial values from localStorage
const getStoredUser = () => {
  try {
    const user = localStorage.getItem(USER_KEY);
    return user ? JSON.parse(user) : null;
  } catch {
    return null;
  }
};

const getStoredToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

const getStoredRefreshToken = () => {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(getStoredUser);
  const [token, setToken] = useState(getStoredToken);
  const [refreshToken, setRefreshToken] = useState(getStoredRefreshToken);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Store tokens and user in localStorage
  const storeAuthData = useCallback((accessToken, refreshTok, userData) => {
    if (accessToken) {
      localStorage.setItem(TOKEN_KEY, accessToken);
      setToken(accessToken);
    }
    if (refreshTok) {
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshTok);
      setRefreshToken(refreshTok);
    }
    if (userData) {
      localStorage.setItem(USER_KEY, JSON.stringify(userData));
      setUser(userData);
    }
  }, []);

  // Clear all auth data
  const clearAuthData = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem("rememberMe");
    setToken(null);
    setRefreshToken(null);
    setUser(null);
  }, []);

  // Verify token on mount
  useEffect(() => {
    const verifyAuth = async () => {
      const storedToken = getStoredToken();

      if (!storedToken) {
        setIsLoading(false);
        return;
      }

      try {
        // Verify token with backend
        const response = await authApi.verifyToken();

        if (response.success && response.user) {
          setUser(response.user);
          localStorage.setItem(USER_KEY, JSON.stringify(response.user));
        } else {
          // Token invalid, try refresh
          const storedRefresh = getStoredRefreshToken();
          if (storedRefresh) {
            try {
              const refreshResponse = await authApi.refreshToken(storedRefresh);
              if (refreshResponse.success) {
                storeAuthData(refreshResponse.data.access_token, null, null);
              } else {
                clearAuthData();
              }
            } catch {
              clearAuthData();
            }
          } else {
            clearAuthData();
          }
        }
      } catch (err) {
        console.error("Auth verification failed:", err);
        // On network error, keep local data but mark as not verified
        // Try refresh token if available
        const storedRefresh = getStoredRefreshToken();
        if (storedRefresh) {
          try {
            const refreshResponse = await authApi.refreshToken(storedRefresh);
            if (refreshResponse.success) {
              storeAuthData(refreshResponse.data.access_token, null, null);
            } else {
              clearAuthData();
            }
          } catch {
            // Keep existing user data on network error
          }
        }
      } finally {
        setIsLoading(false);
      }
    };

    verifyAuth();
  }, [storeAuthData, clearAuthData]);

  // Login function
  const login = async (email, password, rememberMe = false) => {
    setError(null);

    try {
      const response = await authApi.login(email, password, rememberMe);

      if (response.success && response.data) {
        const { access_token, refresh_token, user: userData } = response.data;

        storeAuthData(access_token, refresh_token, userData);

        if (rememberMe) {
          localStorage.setItem("rememberMe", "true");
        }

        return { success: true, user: userData };
      } else {
        throw new Error(response.message || "Giriş başarısız");
      }
    } catch (err) {
      const errorMessage =
        err.response?.data?.detail || err.message || "Giriş başarısız";
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  // Register function
  const register = async (fullName, email, password) => {
    setError(null);

    try {
      const response = await authApi.register(fullName, email, password);

      if (response.success && response.data) {
        // Don't auto-login after registration, redirect to login page
        return { success: true, message: response.message };
      } else {
        throw new Error(response.message || "Kayıt başarısız");
      }
    } catch (err) {
      const errorMessage =
        err.response?.data?.detail || err.message || "Kayıt başarısız";
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  // Logout function
  const logout = async () => {
    try {
      // Notify backend (optional, for audit logging)
      if (token) {
        await authApi.logout().catch(() => {});
      }
    } finally {
      // Always clear local data
      clearAuthData();
    }
  };

  // Update user profile
  const updateProfile = async (updates) => {
    try {
      const response = await authApi.updateProfile(updates);

      if (response.success && response.data) {
        const updatedUser = response.data;
        setUser(updatedUser);
        localStorage.setItem(USER_KEY, JSON.stringify(updatedUser));
        return updatedUser;
      }

      throw new Error("Profil güncellenemedi");
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message;
      throw new Error(errorMessage);
    }
  };

  // Change password
  const changePassword = async (currentPassword, newPassword) => {
    try {
      const response = await authApi.changePassword(
        currentPassword,
        newPassword,
      );

      if (response.success) {
        return { success: true, message: response.message };
      }

      throw new Error("Şifre değiştirilemedi");
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message;
      throw new Error(errorMessage);
    }
  };

  // Check if user is authenticated
  const isAuthenticated = !!user && !!token;

  // Get user initials for avatar
  const getUserInitials = () => {
    if (!user?.fullName) return "U";
    const names = user.fullName.split(" ");
    if (names.length >= 2) {
      return (names[0][0] + names[names.length - 1][0]).toUpperCase();
    }
    return names[0][0].toUpperCase();
  };

  // Refresh user data from server
  const refreshUserData = async () => {
    try {
      const response = await authApi.getMe();
      if (response.success && response.data) {
        setUser(response.data);
        localStorage.setItem(USER_KEY, JSON.stringify(response.data));
        return response.data;
      }
    } catch (err) {
      console.error("Failed to refresh user data:", err);
    }
    return null;
  };

  const value = {
    user,
    token,
    isLoading,
    error,
    isAuthenticated,
    login,
    register,
    logout,
    updateProfile,
    changePassword,
    getUserInitials,
    refreshUserData,
    clearError: () => setError(null),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export default AuthContext;
