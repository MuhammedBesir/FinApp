/**
 * Portfolio Store with Trade Tracking
 * Portföy yönetimi ve işlem takibi için Zustand store
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";

export const usePortfolioStore = create(
  persist(
    (set, get) => ({
      // Portfolio holdings
      holdings: [],

      // Open positions - Açık pozisyonlar
      positions: [],

      // Trade history - günlük al-sat işlemleri
      trades: [],

      // Equity history - portföy değer geçmişi
      equityHistory: [],

      // Watchlist
      watchlist: ["TRALT.IS", "THYAO.IS", "GARAN.IS"],

      // Settings
      settings: {
        notifications: true,
        soundAlerts: true,
        pushNotifications: false,
        emailAlerts: false,
        priceAlertThreshold: 5,
        autoRefresh: true,
        refreshInterval: 30,
        language: "tr",
        currency: "TRY",
      },

      // Holding Actions
      addHolding: (holding) =>
        set((state) => ({
          holdings: [...state.holdings, { ...holding, id: Date.now() }],
        })),

      removeHolding: (id) =>
        set((state) => ({
          holdings: state.holdings.filter((h) => h.id !== id),
        })),

      clearHoldings: () => set({ holdings: [] }),

      reorderHoldings: (fromIndex, toIndex) =>
        set((state) => {
          const updated = [...state.holdings];
          const [moved] = updated.splice(fromIndex, 1);
          updated.splice(toIndex, 0, moved);
          return { holdings: updated };
        }),

      bulkUpdateStopLoss: (percent) =>
        set((state) => ({
          holdings: state.holdings.map((h) => ({
            ...h,
            stopLoss: h.buyPrice ? h.buyPrice * (1 - percent / 100) : h.stopLoss,
          })),
        })),

      enableTrailingStop: (id, trailPercent) =>
        set((state) => ({
          holdings: state.holdings.map((h) =>
            h.id === id
              ? { ...h, trailingStop: true, trailPercent: trailPercent || 5 }
              : h
          ),
        })),

      updateTrailingStop: (id, newPrice) =>
        set((state) => ({
          holdings: state.holdings.map((h) => {
            if (h.id !== id || !h.trailingStop) return h;
            const trailAmount = newPrice * (h.trailPercent / 100);
            const newStopLoss = newPrice - trailAmount;
            if (!h.stopLoss || newStopLoss > h.stopLoss) {
              return { ...h, stopLoss: newStopLoss };
            }
            return h;
          }),
        })),

      updateHolding: (id, updates) =>
        set((state) => ({
          holdings: state.holdings.map((h) =>
            h.id === id ? { ...h, ...updates } : h
          ),
        })),

      // Trade Actions - İşlem ekleme/silme/güncelleme
      addTrade: (trade) =>
        set((state) => ({
          trades: [
            ...state.trades,
            {
              ...trade,
              id: Date.now(),
              createdAt: new Date().toISOString(),
            },
          ],
        })),

      removeTrade: (id) =>
        set((state) => ({
          trades: state.trades.filter((t) => t.id !== id),
        })),

      updateTrade: (id, updates) =>
        set((state) => ({
          trades: state.trades.map((t) =>
            t.id === id ? { ...t, ...updates } : t
          ),
        })),

      clearAllTrades: () => set({ trades: [] }),

      // Watchlist Actions
      addToWatchlist: (ticker) =>
        set((state) => ({
          watchlist: state.watchlist.includes(ticker)
            ? state.watchlist
            : [...state.watchlist, ticker],
        })),

      removeFromWatchlist: (ticker) =>
        set((state) => ({
          watchlist: state.watchlist.filter((t) => t !== ticker),
        })),

      // Settings Actions
      updateSettings: (newSettings) =>
        set((state) => ({
          settings: { ...state.settings, ...newSettings },
        })),

      // Equity snapshot kaydet
      takeEquitySnapshot: () =>
        set((state) => {
          const totalValue = state.holdings.reduce(
            (sum, h) => sum + h.quantity * h.currentPrice,
            0
          );
          const timestamp = new Date().toISOString();
          return {
            equityHistory: [
              ...state.equityHistory,
              { timestamp, value: totalValue },
            ].slice(-365), // Son 1 yıl
          };
        }),

      // Computed values - Holdings
      getTotalValue: () => {
        const { holdings } = get();
        return holdings.reduce(
          (sum, h) => sum + h.quantity * h.currentPrice,
          0
        );
      },

      getTotalCost: () => {
        const { holdings } = get();
        return holdings.reduce((sum, h) => sum + h.quantity * h.buyPrice, 0);
      },

      getTotalProfitLoss: () => {
        const { getTotalValue, getTotalCost } = get();
        return getTotalValue() - getTotalCost();
      },

      getTotalProfitLossPercent: () => {
        const { getTotalProfitLoss, getTotalCost } = get();
        const cost = getTotalCost();
        return cost > 0 ? (getTotalProfitLoss() / cost) * 100 : 0;
      },

      // Gerçekleşmiş kar/zarar (kapatılmış işlemler)
      getRealizedPnL: () => {
        const { trades } = get();
        return trades
          .filter((t) => t.status === "closed")
          .reduce((sum, t) => sum + (t.pnl || 0), 0);
      },

      // Gerçekleşmemiş kar/zarar (açık pozisyonlar)
      getUnrealizedPnL: () => {
        const { holdings } = get();
        return holdings.reduce((sum, h) => {
          return sum + (h.currentPrice - h.buyPrice) * h.quantity;
        }, 0);
      },

      // Toplam PnL (gerçekleşmiş + gerçekleşmemiş)
      getTotalPnL: () => {
        const { getRealizedPnL, getUnrealizedPnL } = get();
        return getRealizedPnL() + getUnrealizedPnL();
      },

      // Drawdown hesaplama
      getDrawdownData: () => {
        const { equityHistory } = get();
        if (equityHistory.length < 2) return [];

        let peak = equityHistory[0].value;
        const drawdowns = [];

        equityHistory.forEach((point) => {
          if (point.value > peak) peak = point.value;
          const drawdown = peak > 0 ? ((peak - point.value) / peak) * 100 : 0;
          drawdowns.push({
            timestamp: point.timestamp,
            drawdown: -drawdown,
            peak,
          });
        });

        return drawdowns;
      },

      getMaxDrawdown: () => {
        const { getDrawdownData } = get();
        const drawdowns = getDrawdownData();
        if (drawdowns.length === 0) return 0;
        return Math.min(...drawdowns.map((d) => d.drawdown));
      },

      // İşlem istatistikleri
      getTradeStats: () => {
        const { trades } = get();
        const closedTrades = trades.filter((t) => t.status === "closed");
        const winningTrades = closedTrades.filter((t) => (t.pnl || 0) > 0);
        const losingTrades = closedTrades.filter((t) => (t.pnl || 0) < 0);

        const totalPnL = closedTrades.reduce((sum, t) => sum + (t.pnl || 0), 0);
        const totalWinAmount = winningTrades.reduce(
          (sum, t) => sum + (t.pnl || 0),
          0
        );
        const totalLossAmount = Math.abs(
          losingTrades.reduce((sum, t) => sum + (t.pnl || 0), 0)
        );

        return {
          totalTrades: closedTrades.length,
          winningTrades: winningTrades.length,
          losingTrades: losingTrades.length,
          winRate:
            closedTrades.length > 0
              ? (winningTrades.length / closedTrades.length) * 100
              : 0,
          totalPnL,
          avgWin:
            winningTrades.length > 0
              ? totalWinAmount / winningTrades.length
              : 0,
          avgLoss:
            losingTrades.length > 0 ? totalLossAmount / losingTrades.length : 0,
          profitFactor:
            totalLossAmount > 0
              ? totalWinAmount / totalLossAmount
              : totalWinAmount > 0
              ? Infinity
              : 0,
          largestWin:
            winningTrades.length > 0
              ? Math.max(...winningTrades.map((t) => t.pnl || 0))
              : 0,
          largestLoss:
            losingTrades.length > 0
              ? Math.min(...losingTrades.map((t) => t.pnl || 0))
              : 0,
        };
      },

      // Günlük PnL
      getDailyPnL: () => {
        const { trades } = get();
        const today = new Date().toISOString().split("T")[0];
        return trades
          .filter((t) => t.status === "closed" && t.closedAt?.startsWith(today))
          .reduce((sum, t) => sum + (t.pnl || 0), 0);
      },

      // Haftalık PnL
      getWeeklyPnL: () => {
        const { trades } = get();
        const oneWeekAgo = new Date();
        oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);

        return trades
          .filter(
            (t) => t.status === "closed" && new Date(t.closedAt) >= oneWeekAgo
          )
          .reduce((sum, t) => sum + (t.pnl || 0), 0);
      },

      // Aylık PnL
      getMonthlyPnL: () => {
        const { trades } = get();
        const oneMonthAgo = new Date();
        oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);

        return trades
          .filter(
            (t) => t.status === "closed" && new Date(t.closedAt) >= oneMonthAgo
          )
          .reduce((sum, t) => sum + (t.pnl || 0), 0);
      },

      // En iyi/kötü performans gösteren hisseler
      getTopPerformers: () => {
        const { trades } = get();
        const tickerPnL = {};

        trades
          .filter((t) => t.status === "closed")
          .forEach((t) => {
            if (!tickerPnL[t.ticker]) {
              tickerPnL[t.ticker] = { ticker: t.ticker, pnl: 0, trades: 0 };
            }
            tickerPnL[t.ticker].pnl += t.pnl || 0;
            tickerPnL[t.ticker].trades += 1;
          });

        return Object.values(tickerPnL).sort((a, b) => b.pnl - a.pnl);
      },
    }),
    {
      name: "trading-bot-portfolio",
    }
  )
);

export default usePortfolioStore;
