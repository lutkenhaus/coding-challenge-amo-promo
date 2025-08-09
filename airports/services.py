import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings
from django.utils import timezone
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class AirportAPIService:

    def __init__(self):
        self.base_url = settings.AIRPORTS_API_URL
        self.auth = HTTPBasicAuth(
            settings.API_LOGIN,
            settings.API_PASSWORD
        )
        self.timeout = settings.API_TIMEOUT
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'AmoPromo-Airport-Sync/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        session.auth = self.auth
        return session

    def fetch_airports(self) -> Optional[List[Dict]]:
        try:
            logger.info("Fetching airports from external API")

            response = self.session.get(
                self.base_url,
                timeout=self.timeout
            )
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            response.raise_for_status()

            data = response.json()

            airports_list = [
                {**value, "iata": key}
                for key, value in data.items()
            ]

            logger.info(f"Got {len(airports_data)} airports from API")
            return airports_data

        except requests.exceptions.Timeout:
        logger.error(f"Timeout while fetching airports (timeout: {self.timeout}s)")
        return None
        
        except requests.exceptions.ConnectionError:
            logger.error("Connection error: could not reach the API server")
            return None
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error while fetching airports: {e}")
            logger.error(f"Response content: {e.response.text if e.response else 'No response'}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error while fetching airports: {e}")
            return None
            
        except ValueError as e:
            logger.error(f"JSON decode error: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error while fetching airports: {e}")
            return None