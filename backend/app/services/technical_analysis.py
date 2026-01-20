"""
Technical Analysis Service (Python 3.14 Compatible - No pandas_ta)
Calculates various technical indicators using native pandas/numpy
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from app.utils.logger import logger


class TechnicalAnalysis:
    """Service for calculating technical indicators using pandas/numpy"""
    
    def __init__(self):
        """Initialize technical analysis service"""
        logger.info("TechnicalAnalysis initialized (native implementation)")
    
    # TREND INDICATORS
    
    def calculate_ema(self, df: pd.DataFrame, periods: List[int] = [9, 21, 50, 200]) -> pd.DataFrame:
        """Calculate Exponential Moving Averages"""
        for period in periods:
            col_name = f'ema_{period}'
            if col_name not in df.columns:
                df[col_name] = df['close'].ewm(span=period, adjust=False).mean()
        return df
    
    def calculate_sma(self, df: pd.DataFrame, periods: List[int] = [20, 50, 100]) -> pd.DataFrame:
        """Calculate Simple Moving Averages"""
        for period in periods:
            col_name = f'sma_{period}'
            if col_name not in df.columns:
                df[col_name] = df['close'].rolling(window=period).mean()
        return df
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate Average True Range (ATR) - Optimized"""
        if 'atr' in df.columns:
            return df
        
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        
        # Use pandas max for proper Series handling
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = true_range.rolling(window=period).mean()
        return df
    
    def calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate simplified ADX - Optimized"""
        if 'adx' in df.columns:
            return df
        
        # Simplified ADX calculation
        high_diff = df['high'].diff()
        low_diff = df['low'].diff()
        
        df['di_plus'] = np.where(
            (high_diff > low_diff) & (high_diff > 0),
            high_diff, 0
        )
        df['di_minus'] = np.where(
            (low_diff > high_diff) & (low_diff > 0),
            low_diff, 0
        )
        
        # Smooth and calculate ADX
        df['di_plus'] = df['di_plus'].rolling(window=period).mean()
        df['di_minus'] = df['di_minus'].rolling(window=period).mean()
        df['adx'] = abs(df['di_plus'] - df['di_minus']) / (df['di_plus'] + df['di_minus'] + 1e-10) * 100
        return df
    
    # MOMENTUM INDICATORS
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate Relative Strength Index (RSI) - Optimized"""
        if 'rsi' in df.columns:
            return df
        
        delta = df['close'].diff()
        gain = delta.clip(lower=0).rolling(window=period).mean()
        loss = (-delta.clip(upper=0)).rolling(window=period).mean()
        
        rs = gain / (loss + 1e-10)
        df['rsi'] = 100 - (100 / (1 + rs))
        return df
    
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """Calculate MACD - Optimized"""
        if 'macd' in df.columns:
            return df
        
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        return df
    
    def calculate_stochastic(self, df: pd.DataFrame, period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> pd.DataFrame:
        """Calculate Stochastic Oscillator - Optimized"""
        if 'stoch_k' in df.columns:
            return df
        
        low_min = df['low'].rolling(window=period).min()
        high_max = df['high'].rolling(window=period).max()
        
        df['stoch_k'] = 100 * (df['close'] - low_min) / (high_max - low_min + 1e-10)
        df['stoch_k'] = df['stoch_k'].rolling(window=smooth_k).mean()
        df['stoch_d'] = df['stoch_k'].rolling(window=smooth_d).mean()
        return df
    
    def calculate_cci(self, df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """Calculate Commodity Channel Index (CCI) - Optimized"""
        if 'cci' in df.columns:
            return df
        
        tp = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = tp.rolling(window=period).mean()
        # Use std instead of MAD for better performance
        std_tp = tp.rolling(window=period).std()
        
        df['cci'] = (tp - sma_tp) / (0.015 * std_tp + 1e-10)
        return df
    
    # VOLATILITY INDICATORS
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std: float = 2.0) -> pd.DataFrame:
        """Calculate Bollinger Bands - Optimized"""
        if 'bb_middle' in df.columns:
            return df
        
        df['bb_middle'] = df['close'].rolling(window=period).mean()
        rolling_std = df['close'].rolling(window=period).std()
        
        df['bb_upper'] = df['bb_middle'] + (rolling_std * std)
        df['bb_lower'] = df['bb_middle'] - (rolling_std * std)
        df['bb_bandwidth'] = (df['bb_upper'] - df['bb_lower']) / (df['bb_middle'] + 1e-10)
        df['bb_percent'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'] + 1e-10)
        return df
    
    # VOLUME INDICATORS
    
    def calculate_obv(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate On-Balance Volume (OBV) - Optimized"""
        if 'obv' in df.columns:
            return df
        
        # Use pandas operations for proper type handling
        sign = df['close'].diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
        df['obv'] = (sign * df['volume']).fillna(0).cumsum()
        return df
    
    def calculate_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Volume Weighted Average Price (VWAP) - Optimized"""
        if 'vwap' in df.columns:
            return df
        
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        df['vwap'] = (df['volume'] * typical_price).cumsum() / (df['volume'].cumsum() + 1e-10)
        return df
    
    def calculate_mfi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate Money Flow Index (MFI) - Optimized"""
        if 'mfi' in df.columns:
            return df
        
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        money_flow = typical_price * df['volume']
        
        positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0).rolling(window=period).sum()
        negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0).rolling(window=period).sum()
        
        money_ratio = positive_flow / (negative_flow + 1e-10)
        df['mfi'] = 100 - (100 / (1 + money_ratio))
        
        logger.debug("Calculated MFI")
        return df
    
    # PRICE ACTION
    
    def detect_support_resistance(self, df: pd.DataFrame, window: int = 20) -> Dict[str, List[float]]:
        """Detect support and resistance levels"""
        df = df.copy()
        
        # Find local minima (support)
        support = df['low'].rolling(window=window, center=True).min()
        support_levels = df[df['low'] == support]['low'].unique().tolist()
        
        # Find local maxima (resistance)
        resistance = df['high'].rolling(window=window, center=True).max()
        resistance_levels = df[df['high'] == resistance]['high'].unique().tolist()
        
        # Take only the most significant levels (last 5)
        support_levels = sorted(support_levels)[-5:]
        resistance_levels = sorted(resistance_levels)[-5:]
        
        logger.debug(f"Detected {len(support_levels)} support and {len(resistance_levels)} resistance levels")
        
        return {
            "support": support_levels,
            "resistance": resistance_levels
        }
    
    def calculate_pivot_points(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate Pivot Points"""
        # Use last complete candle
        last = df.iloc[-1]
        high = last['high']
        low = last['low']
        close = last['close']
        
        # Calculate pivot point
        pivot = (high + low + close) / 3
        
        # Calculate support and resistance levels
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)
        
        logger.debug("Calculated Pivot Points")
        
        return {
            "pivot": pivot,
            "r1": r1,
            "r2": r2,
            "r3": r3,
            "s1": s1,
            "s2": s2,
            "s3": s3
        }
    
    # COMPREHENSIVE ANALYSIS
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators at once - Optimized
        
        Uses in-place modifications and skips already calculated indicators
        for better performance.
        """
        if df.empty:
            return df
        
        # Make a single copy at the start
        df = df.copy()
        
        # All indicator functions now check if columns exist and skip if so
        # Trend indicators
        self.calculate_ema(df)
        self.calculate_sma(df)
        self.calculate_atr(df)
        self.calculate_adx(df)
        
        # Momentum indicators  
        self.calculate_rsi(df)
        self.calculate_macd(df)
        self.calculate_stochastic(df)
        self.calculate_cci(df)
        
        # Volatility indicators
        self.calculate_bollinger_bands(df)
        
        # Volume indicators
        self.calculate_obv(df)
        self.calculate_vwap(df)
        self.calculate_mfi(df)
        
        return df
    
    def get_latest_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get the latest indicator values in a structured format"""
        if df.empty or len(df) == 0:
            return {}
        
        latest = df.iloc[-1]
        
        # Helper function to convert NaN to None for JSON serialization
        def safe_float(value):
            """Convert value to float, replacing NaN with None"""
            if pd.isna(value):
                return None
            return float(value)
        
        indicators = {
            "trend": {
                "ema_9": safe_float(latest.get('ema_9', np.nan)),
                "ema_21": safe_float(latest.get('ema_21', np.nan)),
                "ema_50": safe_float(latest.get('ema_50', np.nan)),
                "sma_20": safe_float(latest.get('sma_20', np.nan)),
                "adx": safe_float(latest.get('adx', np.nan)),
                "di_plus": safe_float(latest.get('di_plus', np.nan)),
                "di_minus": safe_float(latest.get('di_minus', np.nan)),
            },
            "momentum": {
                "rsi": safe_float(latest.get('rsi', np.nan)),
                "macd": safe_float(latest.get('macd', np.nan)),
                "macd_signal": safe_float(latest.get('macd_signal', np.nan)),
                "macd_histogram": safe_float(latest.get('macd_histogram', np.nan)),
                "stoch_k": safe_float(latest.get('stoch_k', np.nan)),
                "stoch_d": safe_float(latest.get('stoch_d', np.nan)),
                "cci": safe_float(latest.get('cci', np.nan)),
            },
            "volatility": {
                "bb_upper": safe_float(latest.get('bb_upper', np.nan)),
                "bb_middle": safe_float(latest.get('bb_middle', np.nan)),
                "bb_lower": safe_float(latest.get('bb_lower', np.nan)),
                "atr": safe_float(latest.get('atr', np.nan)),
            },
            "volume": {
                "obv": safe_float(latest.get('obv', np.nan)),
                "vwap": safe_float(latest.get('vwap', np.nan)),
                "mfi": safe_float(latest.get('mfi', np.nan)),
            }
        }
        
        logger.debug("Extracted latest indicator values")
        return indicators
    # ADVANCED INDICATORS
    
    def calculate_ichimoku(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Ichimoku Cloud"""
        df = df.copy()
        
        # Tenkan-sen (9-period)
        nine_high = df['high'].rolling(window=9).max()
        nine_low = df['low'].rolling(window=9).min()
        df['ichimoku_tenkan'] = (nine_high + nine_low) / 2
        
        # Kijun-sen (26-period)
        period26_high = df['high'].rolling(window=26).max()
        period26_low = df['low'].rolling(window=26).min()
        df['ichimoku_kijun'] = (period26_high + period26_low) / 2
        
        # Senkou Span A
        df['ichimoku_senkou_a'] = ((df['ichimoku_tenkan'] + df['ichimoku_kijun']) / 2).shift(26)
        
        # Senkou Span B (52-period)
        period52_high = df['high'].rolling(window=52).max()
        period52_low = df['low'].rolling(window=52).min()
        df['ichimoku_senkou_b'] = ((period52_high + period52_low) / 2).shift(26)
        
        # Chikou Span
        df['ichimoku_chikou'] = df['close'].shift(-26)
        
        logger.debug("Calculated Ichimoku Cloud")
        return df
    
    def calculate_fibonacci_levels(self, df: pd.DataFrame, lookback: int = 100) -> Dict[str, float]:
        """Calculate Fibonacci retracement levels"""
        recent_data = df.tail(lookback)
        high = recent_data['high'].max()
        low = recent_data['low'].min()
        diff = high - low
        
        levels = {
            'high': high, 'low': low,
            'fib_0': high,
            'fib_236': high - 0.236 * diff,
            'fib_382': high - 0.382 * diff,
            'fib_500': high - 0.500 * diff,
            'fib_618': high - 0.618 * diff,
            'fib_786': high - 0.786 * diff,
            'fib_100': low,
        }
        
        logger.debug("Calculated Fibonacci levels")
        return levels


class TrendChannelIndicator:
    """
    Trend Kanalı İndikatörü
    Yükselen/Düşen kanal tespiti ve sinyal üretimi
    """
    
    def __init__(self, df: pd.DataFrame, period: int = 20):
        """
        Initialize trend channel indicator
        
        Args:
            df: DataFrame with columns: date, open, high, low, close, volume
            period: Lookback period for channel calculation
        """
        self.df = df
        self.period = period
        self.highs = df['high'].values
        self.lows = df['low'].values
        self.closes = df['close'].values
    
    def _calculate_linear_regression(self, data: np.ndarray) -> Dict[str, float]:
        """Calculate linear regression for given data"""
        n = len(data)
        x = np.arange(n)
        
        sum_x = np.sum(x)
        sum_y = np.sum(data)
        sum_xy = np.sum(x * data)
        sum_x2 = np.sum(x * x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x + 1e-10)
        intercept = (sum_y - slope * sum_x) / n
        
        return {'slope': slope, 'intercept': intercept}
    
    def find_rising_lows(self) -> Dict[str, float]:
        """Find rising lows for support line"""
        recent_lows = self.lows[-self.period:]
        return self._calculate_linear_regression(recent_lows)
    
    def find_rising_highs(self) -> Dict[str, float]:
        """Find rising highs for resistance line"""
        recent_highs = self.highs[-self.period:]
        return self._calculate_linear_regression(recent_highs)
    
    def calculate_channel_width(self) -> Dict[str, float]:
        """Calculate channel width"""
        support_line = self.find_rising_lows()
        resistance_line = self.find_rising_highs()
        
        last_index = self.period - 1
        support_value = support_line['slope'] * last_index + support_line['intercept']
        resistance_value = resistance_line['slope'] * last_index + resistance_line['intercept']
        
        width = resistance_value - support_value
        width_percent = (width / support_value) * 100 if support_value > 0 else 0
        
        return {
            'width': width,
            'width_percent': width_percent
        }
    
    def get_price_position_in_channel(self) -> Dict[str, float]:
        """Get current price position within channel (0-100)"""
        current_price = self.closes[-1]
        support_line = self.find_rising_lows()
        resistance_line = self.find_rising_highs()
        
        last_index = self.period - 1
        support_value = support_line['slope'] * last_index + support_line['intercept']
        resistance_value = resistance_line['slope'] * last_index + resistance_line['intercept']
        
        # 0 = at support, 100 = at resistance
        channel_height = resistance_value - support_value
        if channel_height <= 0:
            position = 50
        else:
            position = ((current_price - support_value) / channel_height) * 100
        
        return {
            'position': max(0, min(100, position)),
            'current_price': current_price,
            'support': support_value,
            'resistance': resistance_value
        }
    
    def get_trend_direction(self) -> str:
        """Determine trend direction"""
        support_line = self.find_rising_lows()
        resistance_line = self.find_rising_highs()
        
        avg_slope = (support_line['slope'] + resistance_line['slope']) / 2
        
        # Normalize slope by price level
        avg_price = np.mean(self.closes[-self.period:])
        normalized_slope = (avg_slope / avg_price) * 100
        
        if normalized_slope > 0.1:
            return 'YUKSELIS'
        elif normalized_slope < -0.1:
            return 'DUSUS'
        return 'YATAY'
    
    def detect_breakout(self) -> Dict[str, Any]:
        """Detect channel breakout"""
        position = self.get_price_position_in_channel()
        current_price = position['current_price']
        tolerance = 0.5  # 0.5% tolerance
        
        if current_price > position['resistance'] * (1 + tolerance / 100):
            return {
                'type': 'YUKARI_KIRILMA',
                'price': current_price,
                'level': position['resistance'],
                'strength': 'GUCLU'
            }
        
        if current_price < position['support'] * (1 - tolerance / 100):
            return {
                'type': 'ASAGI_KIRILMA',
                'price': current_price,
                'level': position['support'],
                'strength': 'GUCLU'
            }
        
        return {'type': 'KANAL_ICI', 'price': current_price}
    
    def generate_signal(self) -> Dict[str, Any]:
        """Generate trading signal based on channel analysis"""
        position = self.get_price_position_in_channel()
        trend = self.get_trend_direction()
        breakout = self.detect_breakout()
        channel = self.calculate_channel_width()
        
        signal = {
            'action': 'BEKLE',
            'confidence': 0,
            'reason': '',
            'entry': None,
            'stop_loss': None,
            'target': None,
            'type': None
        }
        
        # Breakout conditions
        if breakout['type'] == 'YUKARI_KIRILMA' and trend == 'YUKSELIS':
            signal = {
                'action': 'AL',
                'confidence': 85,
                'reason': 'Yükselen kanaldan yukarı kırılma',
                'entry': position['current_price'],
                'stop_loss': position['resistance'] * 0.97,  # 3% below
                'target': position['current_price'] * 1.06,  # 6% above (1:2 risk/reward)
                'type': 'BREAKOUT'
            }
        elif breakout['type'] == 'ASAGI_KIRILMA':
            signal = {
                'action': 'SAT',
                'confidence': 80,
                'reason': 'Kanaldan aşağı kırılma - trend değişimi riski',
                'type': 'BREAKDOWN'
            }
        # In-channel trading
        elif position['position'] <= 20 and trend == 'YUKSELIS':
            # At support in uptrend
            signal = {
                'action': 'AL',
                'confidence': 75,
                'reason': 'Yükselen kanalın destek bölgesinde',
                'entry': position['current_price'],
                'stop_loss': position['support'] * 0.97,
                'target': position['resistance'] * 0.98,
                'type': 'SUPPORT_BOUNCE'
            }
        elif position['position'] >= 80:
            # At resistance
            signal = {
                'action': 'KAR_AL',
                'confidence': 70,
                'reason': 'Kanalın direnç bölgesine yaklaştı',
                'type': 'RESISTANCE'
            }
        elif 40 <= position['position'] <= 60:
            # Mid-channel - neutral
            signal = {
                'action': 'BEKLE',
                'confidence': 50,
                'reason': 'Kanal ortasında - net sinyal yok',
                'type': 'NEUTRAL'
            }
        
        return {
            'signal': signal,
            'channel_data': {
                'trend': trend,
                'position': round(position['position'], 2),
                'support': round(position['support'], 2),
                'resistance': round(position['resistance'], 2),
                'current_price': round(position['current_price'], 2),
                'channel_width': f"{round(channel['width_percent'], 2)}%",
                'breakout': breakout['type']
            }
        }
    
    def get_channel_lines(self, future_points: int = 5) -> Dict[str, List[Dict[str, float]]]:
        """Get channel line points for charting"""
        support_line = self.find_rising_lows()
        resistance_line = self.find_rising_highs()
        
        total_points = self.period + future_points
        support_points = []
        resistance_points = []
        
        for i in range(total_points):
            support_points.append({
                'x': i,
                'y': support_line['slope'] * i + support_line['intercept']
            })
            resistance_points.append({
                'x': i,
                'y': resistance_line['slope'] * i + resistance_line['intercept']
            })
        
        return {
            'support_points': support_points,
            'resistance_points': resistance_points
        }
    
    def get_full_analysis(self) -> Dict[str, Any]:
        """Get complete trend channel analysis"""
        result = self.generate_signal()
        lines = self.get_channel_lines()
        
        return {
            'timestamp': pd.Timestamp.now().isoformat(),
            'signal': result['signal'],
            'channel_data': result['channel_data'],
            'lines': lines,
            'recommendation': self._generate_recommendation(result['signal'], result['channel_data'])
        }
    
    def _generate_recommendation(self, signal: Dict, data: Dict) -> str:
        """Generate user-friendly recommendation text"""
        recommendation = f"""
📊 TREND KANALI ANALİZİ

🎯 SİNYAL: {signal['action']}
📈 Güven: {signal['confidence']}%
💡 Neden: {signal['reason']}

📉 KANAL BİLGİLERİ:
- Trend: {data['trend']}
- Mevcut Fiyat: ₺{data['current_price']}
- Destek: ₺{data['support']}
- Direnç: ₺{data['resistance']}
- Kanal İçi Pozisyon: %{data['position']}
- Kanal Genişliği: {data['channel_width']}
- Durum: {data['breakout']}
"""
        
        if signal['action'] == 'AL' and signal.get('entry'):
            recommendation += f"""
💰 İŞLEM DETAYI:
- Giriş: ₺{round(signal['entry'], 2)}
- Stop Loss: ₺{round(signal['stop_loss'], 2)}
- Hedef: ₺{round(signal['target'], 2)}
- Risk/Ödül: 1:2

⚠️ UYARI: Stop-loss'u mutlaka koy!
"""
        
        return recommendation
