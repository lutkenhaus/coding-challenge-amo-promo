import json
import logging
from typing import Dict, Optional, List, Any
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

class AirportCacheService:

    def __init__(self):
        self.cache_keys = getattr(settings, 'CACHE_KEYS', {})
        self.cache_timeouts = getattr(settings, 'CACHE_TIMEOUTS', {})

        self.airports_data_key = self.cache_keys.get('AIRPORTS_DATA', 'airports:data:v1')
        self.airports_by_iata_key = self.cache_keys.get('AIRPORTS_BY_IATA', 'airports:by_iata:v1')
        self.last_sync_key = self.cache_keys.get('AIRPORTS_LAST_SYNC', 'airports:last_sync:v1')

        self.default_timeout = self.cache_keys.get('AIRPORTS_DATA', 24*60*60)

    def cache_airports_data(self, airports_data: Dict[str, Dict], timeout: Optional[int] = None) -> bool:
        try:
            timeout = timeout or self.default_timeout
            logger.info(f"Caching {len(airports_data)} airports data")
            success = cache.set(
                self.airports_data_key,
                airports_data,
                timeout=timeout
            )

            if success:
                self._cache_individual_airports(airports_data, timeout)

                cache.set(
                    self.last_sync_key,
                    timezone.now().isoformat(),
                    timeout=timeout
                )

                logger.info("Successfully cached airports data")
                return True
            else:
                logger.error("Failed to cache airports data")
                return False

        except Exception as e:
        logger.error(f"Error caching airports data: {e}")
        return False

    def _cache_individual_airports(self, airports_data: Dict[str, Dict], timeout: int):
        try:
            individual_cache = {}
            for iata, airport_data in airports_data.items():
                cache_key = f"{self.airports_by_iata_key}:{iata}"
                individual_cache[cache_key] = airport_data
            
            cache.set_many(individual_cache, timeout=timeout)
            
            logger.info(f"Cached {len(individual_cache)} individual airports")
            
        except Exception as e:
            logger.error(f"Error caching individual airports: {e}")

    def get_airports_data(self) -> Optional[Dict[str, Dict]]:
        try:
            data = cache.get(self.airports_data_key)
            
            if data:
                logger.info(f"Retrieved {len(data)} airports from cache")
                return data
            else:
                logger.info("No airports data found in cache")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving airports data from cache: {e}")
            return None

    def get_airport_by_iata(self, iata: str) -> Optional[Dict]:
        try:
            iata = iata.upper().strip()
            cache_key = f"{self.airports_by_iata_key}:{iata}"
            
            airport_data = cache.get(cache_key)
            
            if airport_data:
                logger.debug(f"Retrieved airport {iata} from cache")
                return airport_data
            else:
                all_airports = self.get_airports_data()
                if all_airports and iata in all_airports:
                    airport_data = all_airports[iata]
                    cache.set(cache_key, airport_data, timeout=self.default_timeout)
                    return airport_data
                
                logger.debug(f"Airport {iata} not found in cache")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving airport {iata} from cache: {e}")
            return None