import requests
import time
import json
import os
import asyncio
from shared import Logger

DEFAULT_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"
DEFAULT_CACHE_FILE = "exchange_rates.json"
DEFAULT_CACHE_EXPIRY = 3600
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 2
REQUEST_TIMEOUT = 5

"""
Универсальный сервис для получения курсов валют.
Применяем разновидность Singleton - Multiton, когда создается уникальный экземляр, зависящих от входящих параметров.
"""

class ExchangeRateService:
    _instances = {}

    def __new__(cls,
                *,
                api_url: str = DEFAULT_API_URL,
                cache_file: str = DEFAULT_CACHE_FILE,
                cache_expiry: int = DEFAULT_CACHE_EXPIRY,
                max_retries: int = DEFAULT_MAX_RETRIES,
                retry_delay: int = DEFAULT_RETRY_DELAY):
       
        key = (api_url, cache_file, cache_expiry, max_retries, retry_delay)

        if key not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[key] = instance

        return cls._instances[key]

    def __init__(self,
                 *,
                 api_url: str = DEFAULT_API_URL,
                 cache_file: str = DEFAULT_CACHE_FILE,
                 cache_expiry: int = DEFAULT_CACHE_EXPIRY,
                 max_retries: int = DEFAULT_MAX_RETRIES,
                 retry_delay: int = DEFAULT_RETRY_DELAY):

        if getattr(self, '_initialized', False):
            return
        self._initialized = True

        self.api_url = api_url
        self.cache_file = cache_file
        self.cache_expiry = cache_expiry
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        logger = Logger(__name__)
        self.logger = logger.get_logger()

        self._lock = asyncio.Lock()

    def _load_from_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if time.time() - data['timestamp'] < self.cache_expiry:
                        return data['rates']
            except (json.JSONDecodeError, KeyError):
                self.logger.info("Invalid cache file. Fetching from API.")
        return None

    def _save_to_cache(self, rates: dict):
        try:
            data = {
                'timestamp': time.time(),
                'rates': rates
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except IOError as e:
            self.logger.error(f"Error saving to cache: {e}")

    async def get_rates(self) -> dict:
        async with self._lock:
            cached_rates = self._load_from_cache()
            if cached_rates:
                return cached_rates
            
            rates = await self._fetch_data()
            if rates:
                self._save_to_cache(rates)
                return rates
            return {}
    
    async def _fetch_data(self) -> dict:
        return await asyncio.to_thread(self._blocking_fetch_data)
    
    def _blocking_fetch_data(self) -> dict:
        self.logger.info("Fetching exchange rates from API...")
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(self.api_url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                data = response.json()
                rates = data['rates']
                return rates

            except requests.exceptions.RequestException as e:
                self.logger.error(
                    f"Request failed (attempt {attempt+1}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error("Max retries reached. Unable to fetch rates.")
                    return {}

            except (json.JSONDecodeError, KeyError) as e:
                self.logger.error(f"Error processing JSON response: {e}")
                return {}

        return {}
