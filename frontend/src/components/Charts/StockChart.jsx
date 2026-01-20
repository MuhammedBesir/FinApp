/**
 * Enhanced Stock Chart Component
 * Interactive candlestick chart with advanced technical indicators
 */
import React, { useEffect, useRef, useState } from "react";
import { createChart } from "lightweight-charts";
import { useStore } from "../../store";
import axios from "axios";

const StockChart = ({ data, indicators, selectedIndicators = {}, height }) => {
  const chartContainerRef = useRef();
  const chartRef = useRef();
  const candlestickSeriesRef = useRef();
  const seriesRefs = useRef({});

  const { selectedTicker } = useStore();

  const [ichimokuData, setIchimokuData] = useState(null);
  const [fibonacciLevels, setFibonacciLevels] = useState(null);
  const [bollingerData, setBollingerData] = useState(null);
  const [linregData, setLinregData] = useState(null);
  const [trendChannelData, setTrendChannelData] = useState(null);

  // Fetch indicator data when enabled
  useEffect(() => {
    const fetchIndicatorData = async () => {
      try {
        // Fetch Ichimoku - 1h interval, 1mo period for better data
        if (selectedIndicators.ichimoku?.enabled) {
          const response = await axios.get(
            `http://localhost:8000/api/indicators/${selectedTicker}/ichimoku?interval=1h&period=1mo`
          );
          setIchimokuData(response.data.data);
        } else {
          setIchimokuData(null);
        }

        // Fetch Fibonacci - 1h interval for better accuracy
        if (selectedIndicators.fibonacci?.enabled) {
          const response = await axios.get(
            `http://localhost:8000/api/indicators/${selectedTicker}/fibonacci?interval=1h&period=1mo&lookback=100`
          );
          setFibonacciLevels(response.data.levels);
        } else {
          setFibonacciLevels(null);
        }

        // Fetch Bollinger Bands - 1h interval
        if (selectedIndicators.bollinger?.enabled) {
          const { period = 20, stdDev = 2.0 } = selectedIndicators.bollinger;
          const response = await axios.get(
            `http://localhost:8000/api/indicators/${selectedTicker}/bollinger?interval=1h&period=1mo&bb_period=${period}&std_dev=${stdDev}`
          );
          setBollingerData(response.data.data);
        } else {
          setBollingerData(null);
        }

        // Calculate Linear Regression locally - Sabit: (100, close, 2, 2)
        if (selectedIndicators.linreg?.enabled && data && data.length > 0) {
          const period = 100; // Sabit period
          const offset = 2; // Sabit offset
          const linregValues = calculateLinearRegression(data, period, offset);
          setLinregData(linregValues);
        } else {
          setLinregData(null);
        }

        // Fetch Trend Channel
        if (selectedIndicators.trendChannel?.enabled) {
          const response = await axios.get(
            `http://localhost:8000/api/indicators/${selectedTicker}/trend-channel?interval=1d&period=3mo&channel_period=20`
          );
          if (response.data?.success) {
            setTrendChannelData(response.data);
          }
        } else {
          setTrendChannelData(null);
        }
      } catch (error) {
        console.error("Error fetching indicator data:", error);
      }
    };

    if (selectedTicker) {
      fetchIndicatorData();
    }
  }, [selectedTicker, selectedIndicators, data]);

  // Linear Regression calculation - LinReg (100, close, 2, 2)
  const calculateLinearRegression = (priceData, period = 100, offset = 2) => {
    if (!priceData || priceData.length < period) return [];

    const result = [];

    for (let i = period - 1; i < priceData.length; i++) {
      const slice = priceData.slice(i - period + 1, i + 1);

      // Calculate linear regression using close prices
      let sumX = 0,
        sumY = 0,
        sumXY = 0,
        sumX2 = 0;
      const n = slice.length;

      for (let j = 0; j < n; j++) {
        sumX += j;
        sumY += slice[j].close; // close fiyatı kullan
        sumXY += j * slice[j].close;
        sumX2 += j * j;
      }

      const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
      const intercept = (sumY - slope * sumX) / n;
      // offset kadar ileri kaydır
      const linregValue = intercept + slope * (n - 1 + offset);

      result.push({
        timestamp: priceData[i].timestamp,
        value: linregValue,
      });
    }

    return result;
  };

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Detect mobile screen and set chart height
    const isMobile = window.innerWidth < 640;
    const chartHeight = height || (isMobile ? 280 : 380);

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: chartHeight,
      layout: {
        background: { color: "#1a1d29" },
        textColor: "#d1d4dc",
        fontSize: isMobile ? 10 : 12,
      },
      grid: {
        vertLines: { color: "#2b2f3e" },
        horzLines: { color: "#2b2f3e" },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: "#2b2f3e",
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
      timeScale: {
        borderColor: "#2b2f3e",
        timeVisible: true,
        secondsVisible: false,
        fixLeftEdge: true,
        fixRightEdge: true,
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: false,
      },
      handleScale: {
        axisPressedMouseMove: {
          time: true,
          price: true,
        },
        mouseWheel: true,
        pinch: true,
      },
    });

    chartRef.current = chart;

    // Add candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderVisible: false,
      wickUpColor: "#26a69a",
      wickDownColor: "#ef5350",
    });

    candlestickSeriesRef.current = candlestickSeries;

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        const isMobile = window.innerWidth < 640;
        const nextHeight = height || (isMobile ? 280 : 380);
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: nextHeight,
        });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
      }
    };
  }, [height]);

  // Update candlestick data
  useEffect(() => {
    if (!candlestickSeriesRef.current || !data || data.length === 0) return;

    // Convert data to lightweight-charts format
    const chartData = data.map((item) => ({
      time: Math.floor(new Date(item.timestamp).getTime() / 1000),
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
    }));

    candlestickSeriesRef.current.setData(chartData);

    // Fit content
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  }, [data]);

  // Render basic EMA/SMA indicators
  useEffect(() => {
    if (!chartRef.current || !indicators || !data || data.length === 0) return;

    // Remove old indicator series (basic ones)
    Object.keys(seriesRefs.current).forEach((key) => {
      if (key.startsWith("basic_")) {
        try {
          chartRef.current.removeSeries(seriesRefs.current[key]);
          delete seriesRefs.current[key];
        } catch (e) {
          // Series already removed
        }
      }
    });

    // Add EMA 9
    if (indicators.trend?.ema_9 && data[0]?.ema_9) {
      const ema9Series = chartRef.current.addLineSeries({
        color: "#2962FF",
        lineWidth: 2,
        title: "EMA 9",
      });

      const ema9Data = data
        .map((item) => ({
          time: Math.floor(new Date(item.timestamp).getTime() / 1000),
          value: item.ema_9,
        }))
        .filter((item) => item.value != null && !isNaN(item.value));

      ema9Series.setData(ema9Data);
      seriesRefs.current["basic_ema9"] = ema9Series;
    }

    // Add EMA 21
    if (indicators.trend?.ema_21 && data[0]?.ema_21) {
      const ema21Series = chartRef.current.addLineSeries({
        color: "#FF6D00",
        lineWidth: 2,
        title: "EMA 21",
      });

      const ema21Data = data
        .map((item) => ({
          time: Math.floor(new Date(item.timestamp).getTime() / 1000),
          value: item.ema_21,
        }))
        .filter((item) => item.value != null && !isNaN(item.value));

      ema21Series.setData(ema21Data);
      seriesRefs.current["basic_ema21"] = ema21Series;
    }
  }, [indicators, data]);

  // Render Ichimoku Cloud
  useEffect(() => {
    if (!chartRef.current || !ichimokuData) {
      // Remove Ichimoku series if they exist
      [
        "ichimoku_tenkan",
        "ichimoku_kijun",
        "ichimoku_chikou",
        "ichimoku_senkou_a",
        "ichimoku_senkou_b",
      ].forEach((key) => {
        if (seriesRefs.current[key]) {
          try {
            chartRef.current.removeSeries(seriesRefs.current[key]);
            delete seriesRefs.current[key];
          } catch (e) {}
        }
      });
      return;
    }

    // Tenkan-sen (Conversion Line) - Red
    const tenkanSeries = chartRef.current.addLineSeries({
      color: "#FF6B6B",
      lineWidth: 1,
      title: "Tenkan-sen",
    });
    const tenkanData = ichimokuData
      .map((item) => ({
        time: Math.floor(new Date(item.timestamp).getTime() / 1000),
        value: item.tenkan,
      }))
      .filter((item) => item.value != null);
    tenkanSeries.setData(tenkanData);
    seriesRefs.current["ichimoku_tenkan"] = tenkanSeries;

    // Kijun-sen (Base Line) - Blue
    const kijunSeries = chartRef.current.addLineSeries({
      color: "#4ECDC4",
      lineWidth: 1,
      title: "Kijun-sen",
    });
    const kijunData = ichimokuData
      .map((item) => ({
        time: Math.floor(new Date(item.timestamp).getTime() / 1000),
        value: item.kijun,
      }))
      .filter((item) => item.value != null);
    kijunSeries.setData(kijunData);
    seriesRefs.current["ichimoku_kijun"] = kijunSeries;

    // Chikou Span (Lagging Span) - Purple
    const chikouSeries = chartRef.current.addLineSeries({
      color: "#A855F7",
      lineWidth: 1,
      title: "Chikou Span",
      lineStyle: 2, // dashed
    });
    const chikouData = ichimokuData
      .map((item) => ({
        time: Math.floor(new Date(item.timestamp).getTime() / 1000),
        value: item.chikou,
      }))
      .filter((item) => item.value != null);
    chikouSeries.setData(chikouData);
    seriesRefs.current["ichimoku_chikou"] = chikouSeries;

    // Senkou Span A (Leading Span A) - Green
    const senkouASeries = chartRef.current.addLineSeries({
      color: "rgba(34, 197, 94, 0.5)",
      lineWidth: 1,
      title: "Senkou Span A",
    });
    const senkouAData = ichimokuData
      .map((item) => ({
        time: Math.floor(new Date(item.timestamp).getTime() / 1000),
        value: item.senkou_a,
      }))
      .filter((item) => item.value != null);
    senkouASeries.setData(senkouAData);
    seriesRefs.current["ichimoku_senkou_a"] = senkouASeries;

    // Senkou Span B (Leading Span B) - Red
    const senkouBSeries = chartRef.current.addLineSeries({
      color: "rgba(239, 68, 68, 0.5)",
      lineWidth: 1,
      title: "Senkou Span B",
    });
    const senkouBData = ichimokuData
      .map((item) => ({
        time: Math.floor(new Date(item.timestamp).getTime() / 1000),
        value: item.senkou_b,
      }))
      .filter((item) => item.value != null);
    senkouBSeries.setData(senkouBData);
    seriesRefs.current["ichimoku_senkou_b"] = senkouBSeries;
  }, [ichimokuData]);

  // Render Fibonacci Levels
  useEffect(() => {
    if (!chartRef.current || !fibonacciLevels) {
      // Remove Fibonacci price lines
      [
        "fib_0",
        "fib_236",
        "fib_382",
        "fib_500",
        "fib_618",
        "fib_786",
        "fib_100",
      ].forEach((key) => {
        if (seriesRefs.current[key]) {
          try {
            candlestickSeriesRef.current.removePriceLine(
              seriesRefs.current[key]
            );
            delete seriesRefs.current[key];
          } catch (e) {}
        }
      });
      return;
    }

    const fibLevels = [
      {
        key: "fib_0",
        value: fibonacciLevels.fib_0,
        label: "0%",
        color: "#9CA3AF",
      },
      {
        key: "fib_236",
        value: fibonacciLevels.fib_236,
        label: "23.6%",
        color: "#60A5FA",
      },
      {
        key: "fib_382",
        value: fibonacciLevels.fib_382,
        label: "38.2%",
        color: "#34D399",
      },
      {
        key: "fib_500",
        value: fibonacciLevels.fib_500,
        label: "50%",
        color: "#FBBF24",
      },
      {
        key: "fib_618",
        value: fibonacciLevels.fib_618,
        label: "61.8%",
        color: "#F59E0B",
      },
      {
        key: "fib_786",
        value: fibonacciLevels.fib_786,
        label: "78.6%",
        color: "#EF4444",
      },
      {
        key: "fib_100",
        value: fibonacciLevels.fib_100,
        label: "100%",
        color: "#9CA3AF",
      },
    ];

    fibLevels.forEach(({ key, value, label, color }) => {
      const priceLine = candlestickSeriesRef.current.createPriceLine({
        price: value,
        color: color,
        lineWidth: 1,
        lineStyle: 2, // dashed
        axisLabelVisible: true,
        title: `Fib ${label}`,
      });
      seriesRefs.current[key] = priceLine;
    });
  }, [fibonacciLevels]);

  // Render Bollinger Bands
  useEffect(() => {
    if (!chartRef.current || !bollingerData) {
      // Remove Bollinger Bands series
      ["bb_upper", "bb_middle", "bb_lower"].forEach((key) => {
        if (seriesRefs.current[key]) {
          try {
            chartRef.current.removeSeries(seriesRefs.current[key]);
            delete seriesRefs.current[key];
          } catch (e) {}
        }
      });
      return;
    }

    // Upper Band - Red dashed
    const upperSeries = chartRef.current.addLineSeries({
      color: "#EF4444",
      lineWidth: 1,
      title: "BB Upper",
      lineStyle: 2, // dashed
    });
    const upperData = bollingerData
      .map((item) => ({
        time: Math.floor(new Date(item.timestamp).getTime() / 1000),
        value: item.bb_upper,
      }))
      .filter((item) => item.value != null);
    upperSeries.setData(upperData);
    seriesRefs.current["bb_upper"] = upperSeries;

    // Middle Band - Yellow
    const middleSeries = chartRef.current.addLineSeries({
      color: "#FBBF24",
      lineWidth: 1,
      title: "BB Middle",
    });
    const middleData = bollingerData
      .map((item) => ({
        time: Math.floor(new Date(item.timestamp).getTime() / 1000),
        value: item.bb_middle,
      }))
      .filter((item) => item.value != null);
    middleSeries.setData(middleData);
    seriesRefs.current["bb_middle"] = middleSeries;

    // Lower Band - Green dashed
    const lowerSeries = chartRef.current.addLineSeries({
      color: "#10B981",
      lineWidth: 1,
      title: "BB Lower",
      lineStyle: 2, // dashed
    });
    const lowerData = bollingerData
      .map((item) => ({
        time: Math.floor(new Date(item.timestamp).getTime() / 1000),
        value: item.bb_lower,
      }))
      .filter((item) => item.value != null);
    lowerSeries.setData(lowerData);
    seriesRefs.current["bb_lower"] = lowerSeries;
  }, [bollingerData]);

  // Render Linear Regression
  useEffect(() => {
    if (!chartRef.current) return;

    // Remove existing LinReg series
    if (seriesRefs.current["linreg"]) {
      try {
        chartRef.current.removeSeries(seriesRefs.current["linreg"]);
        delete seriesRefs.current["linreg"];
      } catch (e) {}
    }

    if (!linregData || linregData.length === 0) return;

    // Linear Regression Line - Purple
    const linregSeries = chartRef.current.addLineSeries({
      color: "#A855F7",
      lineWidth: 2,
      title: "LinReg",
    });

    const linregChartData = linregData
      .map((item) => ({
        time: Math.floor(new Date(item.timestamp).getTime() / 1000),
        value: item.value,
      }))
      .filter((item) => item.value != null && !isNaN(item.value));

    linregSeries.setData(linregChartData);
    seriesRefs.current["linreg"] = linregSeries;
  }, [linregData]);

  // Render Trend Channel - Tüm veri üzerinde renkli paralel kanal
  useEffect(() => {
    if (!chartRef.current || !data || data.length === 0) return;

    // Remove existing Trend Channel series
    ['trendChannel_support', 'trendChannel_resistance', 'trendChannel_mid'].forEach(key => {
      if (seriesRefs.current[key]) {
        try {
          chartRef.current.removeSeries(seriesRefs.current[key]);
          delete seriesRefs.current[key];
        } catch (e) {}
      }
    });

    if (!selectedIndicators.trendChannel?.enabled) return;

    const dataLength = data.length;
    if (dataLength < 10) return;

    // TÜM VERİYİ KULLAN - baştan sona kanal çiz
    const relevantData = data;
    const n = relevantData.length;

    // Close fiyatlarına lineer regresyon
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
    
    for (let i = 0; i < n; i++) {
      sumX += i;
      sumY += relevantData[i].close;
      sumXY += i * relevantData[i].close;
      sumX2 += i * i;
    }
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    // Trend yönünü belirle - eğim yüzdesine göre
    const avgPrice = sumY / n;
    const slopePercent = (slope / avgPrice) * 100; // Günlük yüzde değişim
    
    // Renk şeması - trend yönüne göre
    let upperColor, lowerColor, midColor, trendLabel;
    
    if (Math.abs(slopePercent) < 0.05) {
      // Yatay trend - Sarı/Turuncu
      upperColor = '#F59E0B';
      lowerColor = '#FBBF24';
      midColor = 'rgba(251, 191, 36, 0.7)';
      trendLabel = 'YATAY';
    } else if (slope > 0) {
      // Yükselen trend - Yeşil tonları
      upperColor = '#10B981';
      lowerColor = '#34D399';
      midColor = 'rgba(52, 211, 153, 0.7)';
      trendLabel = 'YUKARI';
    } else {
      // Düşen trend - Kırmızı tonları
      upperColor = '#EF4444';
      lowerColor = '#F87171';
      midColor = 'rgba(248, 113, 113, 0.7)';
      trendLabel = 'AŞAĞI';
    }

    // Regresyon çizgisinden sapmaları hesapla
    let maxUpperDev = 0;
    let maxLowerDev = 0;
    
    for (let i = 0; i < n; i++) {
      const regValue = intercept + slope * i;
      const highDev = relevantData[i].high - regValue;
      const lowDev = regValue - relevantData[i].low;
      
      if (highDev > maxUpperDev) maxUpperDev = highDev;
      if (lowDev > maxLowerDev) maxLowerDev = lowDev;
    }

    // Kanal genişliği (paralel kanal için aynı değer kullan)
    const channelWidth = Math.max(maxUpperDev, maxLowerDev);

    const getTimestamp = (item) => {
      if (item.time) {
        return typeof item.time === 'number' ? item.time : Math.floor(new Date(item.time).getTime() / 1000);
      } else if (item.timestamp) {
        return Math.floor(new Date(item.timestamp).getTime() / 1000);
      }
      return null;
    };

    // Orta çizgi (regresyon çizgisi)
    const midData = relevantData.map((item, idx) => ({
      time: getTimestamp(item),
      value: intercept + slope * idx,
    })).filter(item => item.time && !isNaN(item.value));

    // Üst çizgi (direnç - paralel)
    const resistanceData = relevantData.map((item, idx) => ({
      time: getTimestamp(item),
      value: intercept + slope * idx + channelWidth,
    })).filter(item => item.time && !isNaN(item.value));

    // Alt çizgi (destek - paralel)
    const supportData = relevantData.map((item, idx) => ({
      time: getTimestamp(item),
      value: intercept + slope * idx - channelWidth,
    })).filter(item => item.time && !isNaN(item.value));

    // ÜST BANT - Kırmızı dolgulu alan (direnç üstü) - şeffaf
    if (resistanceData.length > 0 && midData.length > 0) {
      const upperAreaSeries = chartRef.current.addAreaSeries({
        topColor: 'rgba(239, 68, 68, 0.15)',
        bottomColor: 'rgba(239, 68, 68, 0.05)',
        lineColor: 'rgba(239, 68, 68, 0.6)',
        lineWidth: 2,
        title: '',
      });
      upperAreaSeries.setData(resistanceData);
      seriesRefs.current['trendChannel_resistance'] = upperAreaSeries;
    }

    // ORTA BANT - Mavi dolgulu alan (kanal içi) - şeffaf
    if (midData.length > 0) {
      const midAreaSeries = chartRef.current.addAreaSeries({
        topColor: 'rgba(59, 130, 246, 0.12)',
        bottomColor: 'rgba(59, 130, 246, 0.12)',
        lineColor: 'rgba(59, 130, 246, 0.5)',
        lineWidth: 1,
        lineStyle: 2,
        title: '',
      });
      midAreaSeries.setData(midData);
      seriesRefs.current['trendChannel_mid'] = midAreaSeries;
    }

    // ALT ÇİZGİ - Sadece çizgi, dolgu yok
    if (supportData.length > 0) {
      const lowerLineSeries = chartRef.current.addLineSeries({
        color: 'rgba(59, 130, 246, 0.6)',
        lineWidth: 2,
        title: '',
      });
      lowerLineSeries.setData(supportData);
      seriesRefs.current['trendChannel_support'] = lowerLineSeries;
    }

  }, [selectedIndicators.trendChannel?.enabled, data]);

  return (
    <div className="w-full relative">
      <div
        ref={chartContainerRef}
        className="w-full rounded-lg overflow-hidden"
      />

      {/* Trend Channel Signal Badge */}
      {selectedIndicators.trendChannel?.enabled && trendChannelData?.analysis?.signal && (
        <div className={`absolute top-3 right-3 px-3 py-1.5 rounded-lg text-xs font-bold ${
          trendChannelData.analysis.signal.action === 'AL' 
            ? 'bg-green-500/20 text-green-400 border border-green-500/30'
            : trendChannelData.analysis.signal.action === 'SAT'
            ? 'bg-red-500/20 text-red-400 border border-red-500/30'
            : 'bg-slate-500/20 text-slate-400 border border-slate-500/30'
        }`}>
          {trendChannelData.analysis.signal.action} ({trendChannelData.analysis.signal.confidence}%)
        </div>
      )}

      {/* Active Indicators Legend */}
      <div className="flex flex-wrap gap-2 absolute left-3 right-3 bottom-0">
        {selectedIndicators.ichimoku?.enabled && (
          <span className="text-xs px-2 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
            Ichimoku
          </span>
        )}
        {selectedIndicators.fibonacci?.enabled && (
          <span className="text-xs px-2 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
            Fibonacci
          </span>
        )}
        {selectedIndicators.bollinger?.enabled && (
          <span className="text-xs px-2 py-1 rounded-full bg-green-500/10 text-green-400 border border-green-500/20">
            Bollinger ({selectedIndicators.bollinger.period || 20})
          </span>
        )}
        {selectedIndicators.linreg?.enabled && (
          <span className="text-xs px-2 py-1 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
            LinReg (100, close, 2, 2)
          </span>
        )}
        {selectedIndicators.trendChannel?.enabled && (
          <span className="text-xs px-2 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            Trend Kanalı ({trendChannelData?.analysis?.channel_data?.trend || 'Yükleniyor...'})
          </span>
        )}
      </div>
    </div>
  );
};

export default StockChart;
