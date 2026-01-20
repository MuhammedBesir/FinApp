"""
Market Data Service - Küresel Piyasa Verileri
USD/TRY, EUR/TRY, Altın, Bitcoin, S&P500, NASDAQ
"""
import yfinance as yf
from typing import Dict, Optional
from datetime import datetime
import asyncio
import pandas as pd
from curl_cffi import requests as curl_requests
from app.services.data_fetcher import DataFetcher

class MarketDataService:
    """Küresel piyasa verilerini çeken servis"""
    
    # Ticker sembolleri
    TICKERS = {
        "USD_TRY": "TRY=X",      # USD/TRY
        "EUR_TRY": "EURTRY=X",   # EUR/TRY
        "GOLD": "GC=F",          # Gold Futures
        "BTC": "BTC-USD",        # Bitcoin
        "SP500": "^GSPC",        # S&P 500
        "NASDAQ": "^IXIC",       # NASDAQ
        "BIST100": "XU100.IS",   # BIST 100
        "BIST30": "XU030.IS"     # BIST 30
    }
    
    def __init__(self):
        self.cache = {}
        self.last_update = None
        self.data_fetcher = DataFetcher()
    
    def _fetch_bist_index(self, ticker: str) -> Optional[Dict]:
        """BIST endeks verisini DataFetcher üzerinden çek"""
        try:
            df = self.data_fetcher.fetch_realtime_data(ticker, interval="1d", period="5d")
            if df is None or df.empty:
                return None

            current_price = float(df["close"].iloc[-1])
            previous_close = float(df["close"].iloc[-2]) if len(df) > 1 else current_price
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0

            return {
                "ticker": ticker,
                "price": round(current_price, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "is_up": change >= 0,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Error fetching BIST index {ticker}: {e}")
            return None

    def _fetch_yahoo_price(self, ticker: str) -> Optional[Dict]:
        """Genel piyasa verilerini Yahoo Finance'tan çek"""
        try:
            # curl_cffi session per call to avoid cross-request contamination
            session = curl_requests.Session(impersonate="chrome", verify=False)
            hist = yf.download(
                ticker,
                period="2d",
                interval="1d",
                progress=False,
                session=session,
            )
            if hist.empty:
                return None

            # yfinance sometimes returns MultiIndex columns even for a single ticker
            if isinstance(hist.columns, pd.MultiIndex):
                hist = hist.droplevel(1, axis=1)

            last_close = hist["Close"].iloc[-1]
            prev_close_val = hist["Close"].iloc[-2] if len(hist) > 1 else last_close

            def _to_float(val):
                try:
                    return float(val.item()) if hasattr(val, "item") else float(val)
                except Exception:
                    return float(val)

            current_price = _to_float(last_close)
            previous_close = _to_float(prev_close_val)
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0

            return {
                "ticker": ticker,
                "price": round(current_price, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "is_up": change >= 0,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None
    
    async def get_all_market_data(self) -> Dict:
        """Tüm piyasa verilerini çek (Paralel)"""
        try:
            loop = asyncio.get_event_loop()

            def _fallback(key: str) -> Dict:
                return {
                    "ticker": self.TICKERS.get(key.upper(), key),
                    "price": 0,
                    "change": 0,
                    "change_percent": 0,
                    "is_up": True,
                    "timestamp": datetime.now().isoformat(),
                    "error": True,
                }

            # Helper wrappers for exception handling
            async def fetch_bist_safe(key: str):
                try:
                    res = await loop.run_in_executor(None, lambda: self._fetch_bist_index(self.TICKERS[key.upper()]))
                    return key, res
                except Exception:
                    return key, None

            async def fetch_yahoo_safe(key: str, ticker: str):
                try:
                    res = await loop.run_in_executor(None, lambda: self._fetch_yahoo_price(ticker))
                    return key, res
                except Exception:
                    return key, None

            # Prepare all tasks
            tasks = []
            
            # BIST tasks
            tasks.append(fetch_bist_safe("bist100"))
            tasks.append(fetch_bist_safe("bist30"))

            # Yahoo tasks
            yahoo_map = {
                "usd_try": self.TICKERS["USD_TRY"],
                "eur_try": self.TICKERS["EUR_TRY"],
                "gold": self.TICKERS["GOLD"],
                "btc": self.TICKERS["BTC"],
                "sp500": self.TICKERS["SP500"],
                "nasdaq": self.TICKERS["NASDAQ"],
            }
            
            for key, ticker in yahoo_map.items():
                tasks.append(fetch_yahoo_safe(key, ticker))

            # Execute all parallel
            results = await asyncio.gather(*tasks)
            
            # Process results
            market_data = {}
            for key, res in results:
                if isinstance(res, dict):
                    market_data[key] = res
                else:
                    market_data[key] = _fallback(key)

            self.cache = market_data
            self.last_update = datetime.now()

            return {
                "success": True,
                "data": market_data,
                "last_update": self.last_update.isoformat(),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": self.cache if self.cache else {},
            }
    
    async def get_forex_data(self) -> Dict:
        """Sadece döviz verilerini çek"""
        try:
            loop = asyncio.get_event_loop()
            usd_data, eur_data = await asyncio.gather(
                loop.run_in_executor(None, lambda: self._fetch_yahoo_price(self.TICKERS["USD_TRY"])),
                loop.run_in_executor(None, lambda: self._fetch_yahoo_price(self.TICKERS["EUR_TRY"]))
            )
            
            return {
                "success": True,
                "data": {
                    "usd_try": usd_data,
                    "eur_try": eur_data
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_commodities_data(self) -> Dict:
        """Emtia verilerini çek (Altın, Bitcoin)"""
        try:
            loop = asyncio.get_event_loop()
            gold_data, btc_data = await asyncio.gather(
                loop.run_in_executor(None, lambda: self._fetch_yahoo_price(self.TICKERS["GOLD"])),
                loop.run_in_executor(None, lambda: self._fetch_yahoo_price(self.TICKERS["BTC"]))
            )
            
            return {
                "success": True,
                "data": {
                    "gold": gold_data,
                    "bitcoin": btc_data
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_global_indices_data(self) -> Dict:
        """Küresel endeks verilerini çek"""
        try:
            loop = asyncio.get_event_loop()
            sp500_data, nasdaq_data = await asyncio.gather(
                loop.run_in_executor(None, lambda: self._fetch_yahoo_price(self.TICKERS["SP500"])),
                loop.run_in_executor(None, lambda: self._fetch_yahoo_price(self.TICKERS["NASDAQ"]))
            )
            
            return {
                "success": True,
                "data": {
                    "sp500": sp500_data,
                    "nasdaq": nasdaq_data
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# Singleton instance
market_data_service = MarketDataService()
