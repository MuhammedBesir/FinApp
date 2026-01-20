/**
 * Format numbers as currency
 */
export const formatCurrency = (value, decimals = 2) => {
  if (value === null || value === undefined || isNaN(value)) return '-';
  return `₺${Number(value).toFixed(decimals)}`;
};

/**
 * Format percentages
 */
export const formatPercent = (value, decimals = 2) => {
  if (value === null || value === undefined || isNaN(value)) return '-';
  const formatted = Number(value).toFixed(decimals);
  return `${formatted}%`;
};

/**
 * Format numbers with K/M/B suffixes
 */
export const formatNumber = (value) => {
  if (value === null || value === undefined || isNaN(value)) return '-';
  
  const num = Number(value);
  
  if (num >= 1e9) {
    return `${(num / 1e9).toFixed(2)}B`;
  } else if (num >= 1e6) {
    return `${(num / 1e6).toFixed(2)}M`;
  } else if (num >= 1e3) {
    return `${(num / 1e3).toFixed(2)}K`;
  }
  
  return num.toFixed(2);
};

/**
 * Format date/time
 */
export const formatDateTime = (dateString) => {
  if (!dateString) return '-';
  
  try {
    const date = new Date(dateString);
    return date.toLocaleString('tr-TR');
  } catch {
    return dateString;
  }
};

/**
 * Format time only
 */
export const formatTime = (dateString) => {
  if (!dateString) return '-';
  
  try {
    const date = new Date(dateString);
    return date.toLocaleTimeString('tr-TR');
  } catch {
    return dateString;
  }
};

/**
 * Get color for positive/negative values
 */
export const getValueColor = (value) => {
  if (value > 0) return 'text-green-500';
  if (value < 0) return 'text-red-500';
  return 'text-gray-400';
};

/**
 * Get color  for signal strength
 */
export const getSignalColor = (strength) => {
  if (strength >= 75) return 'bg-green-500';
  if (strength >= 50) return 'bg-yellow-500';
  if (strength >= 25) return 'bg-orange-500';
  return 'bg-red-500';
};

/**
 * Get text color for signal type
 */
export const getSignalTextColor = (signalType) => {
  if (signalType === 'BUY') return 'text-green-500';
  if (signalType === 'SELL') return 'text-red-500';
  return 'text-gray-400';
};

/**
 * Get background color for signal type
 */
export const getSignalBgColor = (signalType) => {
  if (signalType === 'BUY') return 'bg-green-500/20 border-green-500';
  if (signalType === 'SELL') return 'bg-red-500/20 border-red-500';
  return 'bg-gray-500/20 border-gray-500';
};
