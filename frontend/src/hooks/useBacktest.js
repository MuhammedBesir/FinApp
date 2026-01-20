/**
 * Custom hook for running backtests
 */
import { useState } from 'react';
import { useStore } from '../store';
import api from '../services/api';

export const useBacktest = () => {
  const [isRunning, setIsRunning] = useState(false);
  const { setBacktestResults, setError } = useStore();

  const runBacktest = async (config) => {
    setIsRunning(true);
    setError(null);

    try {
      console.log('Running backtest with config:', config);
      const results = await api.runBacktest(config);
      
      setBacktestResults(results);
      console.log('Backtest completed:', results);
      
      return results;
    } catch (error) {
      console.error('Backtest error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Backtest failed';
      setError(errorMessage);
      throw error;
    } finally {
      setIsRunning(false);
    }
  };

  return { runBacktest, isRunning };
};

export default useBacktest;
