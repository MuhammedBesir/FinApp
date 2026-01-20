/**
 * Protected Route Component
 * Handles authentication-based route protection
 */
import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { Loader2 } from "lucide-react";

/**
 * ProtectedRoute - Wraps routes that require authentication
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children - Child components to render if authenticated
 * @param {boolean} props.requireAuth - Whether authentication is required (default: true)
 * @param {string[]} props.allowedMemberships - Array of allowed membership types
 * @param {string} props.redirectTo - Redirect path if not authenticated
 */
const ProtectedRoute = ({ 
  children, 
  requireAuth = true,
  allowedMemberships = null,
  redirectTo = "/login"
}) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  // Show loading spinner while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0f172a]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 text-primary-500 animate-spin" />
          <p className="text-slate-400 animate-pulse">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  // If auth is required but user is not authenticated
  if (requireAuth && !isAuthenticated) {
    // Redirect to login, preserving the intended destination
    return (
      <Navigate 
        to={redirectTo} 
        state={{ from: location.pathname }} 
        replace 
      />
    );
  }

  // If specific memberships are required
  if (allowedMemberships && allowedMemberships.length > 0) {
    const userMembership = user?.membership || "free";
    if (!allowedMemberships.includes(userMembership)) {
      // Redirect to upgrade page or show access denied
      return (
        <div className="min-h-screen flex items-center justify-center bg-[#0f172a]">
          <div className="glass-card p-8 rounded-2xl text-center max-w-md">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-yellow-500/20 flex items-center justify-center">
              <svg className="w-8 h-8 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-white mb-2">Erişim Kısıtlı</h2>
            <p className="text-slate-400 mb-4">
              Bu özelliğe erişmek için üyelik planınızı yükseltmeniz gerekiyor.
            </p>
            <button 
              onClick={() => window.location.href = "/profile?tab=membership"}
              className="px-6 py-2 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-xl font-medium hover:opacity-90 transition-opacity"
            >
              Planı Yükselt
            </button>
          </div>
        </div>
      );
    }
  }

  // User is authenticated and has required permissions
  return children;
};

/**
 * GuestRoute - Only accessible when NOT authenticated
 * Useful for login/register pages
 */
export const GuestRoute = ({ children, redirectTo = "/" }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0f172a]">
        <Loader2 className="w-12 h-12 text-primary-500 animate-spin" />
      </div>
    );
  }

  if (isAuthenticated) {
    // Redirect authenticated users away from auth pages
    const from = location.state?.from || redirectTo;
    return <Navigate to={from} replace />;
  }

  return children;
};

export default ProtectedRoute;
