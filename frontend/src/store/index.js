/**
 * Global State Management using Zustand (Optimized)
 */
import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";

export const useStore = create(
  subscribeWithSelector((set, get) => ({
    // Selected ticker and settings
    selectedTicker: "TRALT.IS",
    strategy: "moderate",
    interval: "1d",
    period: "3mo",

    // Data
    stockData: null,
    stockInfo: null,
    indicators: null,
    signal: null,
    backtestResults: null,
    marketStatus: null,

    // Real-time data
    realtimeData: null,
    realtimeIndicators: null,

    // UI State
    isLoading: false,
    error: null,
    activeTab: "dashboard",

    // Actions
    setTicker: (ticker) => set({ selectedTicker: ticker }),
    setStrategy: (strategy) => set({ strategy }),
    setInterval: (interval) => set({ interval }),
    setPeriod: (period) => set({ period }),
    setStockData: (data) => set({ stockData: data }),
    setStockInfo: (info) => set({ stockInfo: info }),
    setIndicators: (indicators) => set({ indicators }),
    setSignal: (signal) => set({ signal }),
    setBacktestResults: (results) => set({ backtestResults: results }),
    setMarketStatus: (status) => set({ marketStatus: status }),

    setRealtimeData: (data) => {
      set({
        realtimeData: data,
        realtimeIndicators: data?.indicators,
      });
    },

    setLoading: (isLoading) => set({ isLoading }),
    setError: (error) => set({ error }),
    setActiveTab: (tab) => set({ activeTab: tab }),
    clearError: () => set({ error: null }),

    // Computed values
    getCurrentPrice: () => {
      const state = get();
      return (
        state.realtimeData?.price?.close ||
        state.stockData?.data?.[state.stockData.data.length - 1]?.close ||
        0
      );
    },

    // Memoized indicator flattening
    getLatestIndicators: () => {
      const state = get();
      const rawIndicators =
        state.realtimeIndicators || state.indicators?.indicators || {};

      // Flatten nested indicator structure without causing state updates during render
      const flatIndicators = {
        ...(rawIndicators.trend || {}),
        ...(rawIndicators.momentum || {}),
        ...(rawIndicators.volatility || {}),
        ...(rawIndicators.volume || {}),
      };

      // If already flat, return raw; otherwise return flattened copy
      return Object.keys(flatIndicators).length === 0
        ? rawIndicators
        : flatIndicators;
    },
  })),
);

export default useStore;
