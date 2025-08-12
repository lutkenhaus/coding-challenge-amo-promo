import json
import logging
import requests
from typing import List, Dict, Optional
from requests.auth import HTTPBasicAuth
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)

class AirportCacheService:
    def __init__(self):
        self.cache_keys = getattr(settings, 'CACHE_KEYS', {})
        self.cache_timeouts = getattr(settings, 'CACHE_TIMEOUTS', {})

        self.airports_data_key = f"{self.cache_keys.get('AIRPORTS_DATA', '')}"
        self.airports_by_iata_key = f"{self.cache_keys.get('AIRPORTS_BY_IATA', '')}"
        self.last_sync_key = f"{self.cache_keys.get('AIRPORTS_LAST_SYNC', '')}"
        self.default_timeout = self.cache_timeouts.get('AIRPORTS_DATA', 24*60)

    def cache_airports_data(self, airports_data: Dict[str, Dict], timeout: Optional[int] = None) -> bool:
        try:
            logger.info(f"Caching airports data at {timezone.now()}")

            timeout = timeout or self.default_timeout
            logger.info(f"Caching {len(airports_data)} airports data")

            self.airports_data_key = self.cache_keys.get('AIRPORTS_DATA', '')
            self.airports_by_iata_key = self.cache_keys.get('AIRPORTS_BY_IATA', '')
            self.last_sync_key = self.cache_keys.get('AIRPORTS_LAST_SYNC', '')
            self.default_timeout = self.cache_timeouts.get('AIRPORTS_DATA', 24*60*60)

            serialized_data = json.dumps(airports_data)
            success = cache.set(self.airports_data_key, serialized_data, timeout=timeout)

            if success:
                self._cache_individual_airports(airports_data, timeout)
                cache.set(self.last_sync_key, timezone.now().isoformat(), timeout=timeout)
                logger.info(f"Successfully cached {len(airports_data)} airports in Redis")
                return True

            logger.error("Failed to cache airports data")
            return False
        except Exception as e:
            logger.error(f"Error caching airports data: {e}", exc_info=True)
            return False

    def _cache_individual_airports(self, airports_data: Dict[str, Dict], timeout: int):
        try:
            cached_count = 0
            for iata, airport_data in airports_data.items():
                if not all(k in airport_data for k in ['iata', 'city', 'lat', 'lon', 'state']):
                    logger.warning(f"Skipping invalid airport data for {iata}")
                    continue
                
                individual_key = f"{self.airports_by_iata_key}:{iata}"
                success = cache.set(individual_key, json.dumps(airport_data), timeout=timeout)
                if success:
                    cached_count += 1
            
            logger.info(f"Cached {cached_count} individual airports")
        except Exception as e:
            logger.error(f"Error caching individual airports: {e}", exc_info=True)

    def get_airports_data(self) -> Optional[Dict[str, Dict]]:
        try:
            data = cache.get(self.airports_data_key)
            if data:
                data = json.loads(data)
                logger.info(f"Cache hit: Retrieved {len(data)} airports")
                return data
            logger.info("Cache miss: No airports data found")
            return None
        except Exception as e:
            logger.error(f"Error retrieving airports data: {e}", exc_info=True)
            return None

    def get_airport_by_iata(self, iata: str) -> Optional[Dict]:
        try:
            iata = iata.upper().strip()
            individual_key = f"{self.airports_by_iata_key}:{iata}"

            airport_data = cache.get(individual_key)
            if airport_data:
                logger.info(f"Cache hit: Parsing airport data for {iata}")
                airport_data = json.loads(airport_data)
                logger.info(f"Cache hit for {individual_key}: {airport_data}")
                return airport_data
            # TO-DO: fallback to PostgresSQL if Redis operation fails. (PostgresSQL implementation needed)
                
            logger.info(f"Airport {iata} not found in cache or full dataset")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON for {iata}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving airport {iata} from cache: {e}", exc_info=True)
            return None


class AirportAPIService:
    def __init__(self):
        self.base_url = getattr(settings, 'AIRPORTS_API_URL', '')
        self.auth = HTTPBasicAuth(
            getattr(settings, 'API_LOGIN', ''),
            getattr(settings, 'API_PASSWORD', '')
        )
        self.timeout = getattr(settings, 'API_TIMEOUT', 30)
        self.session = self._create_session()
        self.cache_service = AirportCacheService()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'AmoPromo-Airport-Sync/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        session.auth = self.auth
        return session

    def get_airports(self, force_refresh: bool = False) -> Optional[Dict[str, Dict]]:
        # force_refresh (bool): If True, bypass cache and fetch from API
        try:
            if not force_refresh:
                cached_data = self.cache_service.get_airports_data()
                if cached_data:
                    logger.info("Got cached airports data")
                    return cached_data

            logger.info("Fetching fresh airports data from API (force_refresh is True)")
            fresh_data = self.fetch_airports()
            
            if fresh_data:
                formatted_data = self._format_api_response(fresh_data)
                cache_success = self.cache_service.cache_airports_data(formatted_data)
                
                if cache_success:
                    logger.info("Successfully cached fresh airports data")
                else:
                    logger.warning("Failed to cache fresh data, but returning API data")
                
                return formatted_data

            logger.error("Both cache and API failed - no data retrieved")
            return None

        except Exception as e:
            logger.error(f"Error in get_airports: {e}")
            return None
    
    def _format_api_response(self, api_response) -> Dict[str, Dict]:
        if not isinstance(api_response, dict):
            logger.error(f"Unexpected API response format: {type(api_response)}")
            return {}
        return api_response

    def fetch_airports(self) -> Optional[Dict[str, Dict]]:
        try:
            response = self.session.get(self.base_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Got {len(data)} airports from API")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching airports: {e}")
            return None