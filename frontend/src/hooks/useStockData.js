/**
 * Custom hook for fetching stock data
 */
import { useEffect } from "react";
import { useStore } from "../store";
import api from "../services/api";
import websocketService from "../services/WebSocketService";

export const useStockData = () => {
  const {
    selectedTicker,
    interval,
    period,
    strategy,
    setStockData,
    setStockInfo,
    setIndicators,
    setSignal,
    setRealtimeData,
    setLoading,
    setError,
  } = useStore();

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      if (!selectedTicker) return;

      setLoading(true);
      setError(null);

      try {
        // Fetch all data in parallel
        const [stockData, stockInfo, indicators, signal] = await Promise.all([
          api.getStockData(selectedTicker, interval, period),
          api.getStockInfo(selectedTicker),
          api.getIndicators(selectedTicker, interval, period),
          api.getSignals(selectedTicker, strategy, interval, period),
        ]);

        setStockData(stockData);
        setStockInfo(stockInfo);
        setIndicators(indicators);
        setSignal(signal);
      } catch (error) {
        console.error("Error fetching stock data:", error);

        // Handle 404 specifically (No data available)
        if (error.response && error.response.status === 404) {
          setError(
            "Bu zaman aralığı için veri bulunamadı. Lütfen farklı bir aralık seçin.",
          );
        } else {
          setError(error.message || "Veri alınırken bir hata oluştu");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedTicker, interval, period, strategy]);

  // Setup WebSocket for real-time updates
  useEffect(() => {
    if (!selectedTicker) return;

    // Connect to WebSocket with proper options
    websocketService.connect({
      channels: ["price", "signal"],
      tickers: [selectedTicker],
    });

    // Subscribe to price updates for this ticker
    const unsubscribePriceUpdate = websocketService.onPriceUpdate((data) => {
      setRealtimeData(data);
    }, selectedTicker);

    // Cleanup
    return () => {
      if (unsubscribePriceUpdate) {
        unsubscribePriceUpdate();
      }
    };
  }, [selectedTicker]);

  return {};
};

export default useStockData;
