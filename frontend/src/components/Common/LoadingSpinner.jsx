/**
 * Loading Spinner Component - Modern Glassmorphism Design
 * ✨ Animated gradient spinner with glow effects
 */
import React from "react";

const LoadingSpinner = ({ message = "Yükleniyor...", size = "md" }) => {
  const sizeClasses = {
    sm: "h-8 w-8",
    md: "h-12 w-12",
    lg: "h-16 w-16",
  };

  return (
    <div className="flex flex-col items-center justify-center p-8 animate-fade-in">
      {/* Spinner Container */}
      <div className="relative">
        {/* Glow Effect */}
        <div
          className={`absolute inset-0 ${sizeClasses[size]} rounded-full bg-gradient-to-r from-primary-500 to-accent-500 blur-xl opacity-30 animate-pulse`}
        />

        {/* Outer Ring */}
        <div
          className={`${sizeClasses[size]} rounded-full border-4 border-[var(--glass-border)] relative`}
        >
          {/* Gradient Spinner */}
          <div
            className={`absolute inset-0 ${sizeClasses[size]} rounded-full border-4 border-transparent border-t-primary-500 border-r-accent-500 animate-spin`}
          />

          {/* Inner Glow Dot */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-2 h-2 rounded-full bg-gradient-to-r from-primary-500 to-accent-500 animate-pulse shadow-lg shadow-primary-500/50" />
          </div>
        </div>
      </div>

      {/* Loading Text */}
      {message && (
        <p className="mt-4 text-sm text-theme-muted animate-pulse">{message}</p>
      )}
    </div>
  );
};

export default LoadingSpinner;
