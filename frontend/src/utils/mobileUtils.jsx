/**
 * Mobile Utilities - Shared hooks and components for mobile layouts
 * 📱 Collapsible sections, responsive detection, mobile-friendly patterns
 */
import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

// Hook to detect mobile screens
export const useIsMobile = (breakpoint = 1024) => {
  const [isMobile, setIsMobile] = useState(
    typeof window !== 'undefined' ? window.innerWidth < breakpoint : false
  );
  
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < breakpoint);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [breakpoint]);
  
  return isMobile;
};

// Collapsible Section Component
export const CollapsibleSection = ({ 
  title, 
  icon: Icon, 
  iconColor = 'text-primary-400',
  children, 
  defaultOpen = true,
  badge = null 
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="card">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 border-b border-[var(--glass-border)] hover:bg-theme-card-hover transition-colors"
      >
        <div className="flex items-center gap-2">
          {Icon && <Icon className={`w-4 h-4 ${iconColor}`} />}
          <span className="font-bold text-theme-text text-sm">{title}</span>
          {badge && (
            <span className="text-xs text-theme-muted bg-theme-card px-1.5 py-0.5 rounded">
              {badge}
            </span>
          )}
        </div>
        {isOpen ? (
          <ChevronUp className="w-4 h-4 text-theme-muted" />
        ) : (
          <ChevronDown className="w-4 h-4 text-theme-muted" />
        )}
      </button>
      {isOpen && <div className="p-3">{children}</div>}
    </div>
  );
};

// Mobile Page Header
export const MobilePageHeader = ({ title, subtitle, icon: Icon, action }) => (
  <div className="flex items-center justify-between mb-3">
    <div className="flex items-center gap-2">
      {Icon && (
        <div className="w-8 h-8 rounded-lg bg-primary-500/10 flex items-center justify-center">
          <Icon className="w-4 h-4 text-primary-400" />
        </div>
      )}
      <div>
        <h1 className="font-bold text-theme-text text-base">{title}</h1>
        {subtitle && <p className="text-xs text-theme-muted">{subtitle}</p>}
      </div>
    </div>
    {action}
  </div>
);

// Mobile Stat Card
export const MobileStatCard = ({ label, value, icon: Icon, color = 'primary', small = false }) => {
  const colorClasses = {
    primary: 'text-primary-400 bg-primary-500/10',
    success: 'text-success bg-success/10',
    danger: 'text-danger bg-danger/10',
    warning: 'text-warning bg-warning/10',
  };

  return (
    <div className={`card ${small ? 'p-2' : 'p-3'} text-center`}>
      {Icon && (
        <div className={`w-6 h-6 rounded-lg ${colorClasses[color]} flex items-center justify-center mx-auto mb-1`}>
          <Icon className="w-3 h-3" />
        </div>
      )}
      <p className={`font-bold text-theme-text ${small ? 'text-base' : 'text-lg'}`}>{value}</p>
      <p className="text-[9px] text-theme-muted uppercase tracking-wider">{label}</p>
    </div>
  );
};

// Mobile List Item
export const MobileListItem = ({ title, subtitle, value, valueColor = 'text-theme-text', onClick }) => (
  <div 
    className={`flex items-center justify-between p-3 border-b border-[var(--glass-border)] last:border-b-0 ${onClick ? 'cursor-pointer hover:bg-theme-card-hover transition-colors' : ''}`}
    onClick={onClick}
  >
    <div className="min-w-0 flex-1">
      <p className="font-medium text-theme-text text-sm truncate">{title}</p>
      {subtitle && <p className="text-xs text-theme-muted">{subtitle}</p>}
    </div>
    <span className={`font-bold text-sm ${valueColor} ml-2`}>{value}</span>
  </div>
);

export default {
  useIsMobile,
  CollapsibleSection,
  MobilePageHeader,
  MobileStatCard,
  MobileListItem,
};
