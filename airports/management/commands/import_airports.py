from django.core.management.base import BaseCommand
from django.conf import settings
import requests
from requests.auth import HTTPBasicAuth
from airports.models import Airport
from airports.services import AirportCacheService

class Command(BaseCommand):
    help = 'Import airports from external API and cache in database'
    
    def add_arguments(self, parser):

        # TO-DO: decide if the airports should be created everytime, or upserted.
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Force update all airports even if they exist',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Starting airport import...')
        
        # TO-DO: add error handling techniques (rate-limiting, retries, batch processing, etc...).
        api_url = getattr(settings, 'AIRPORTS_API_URL', '')
        auth = HTTPBasicAuth(
            getattr(settings, 'API_LOGIN', ''),
            getattr(settings, 'API_PASSWORD', '')
        )
        timeout = getattr(settings, 'API_TIMEOUT', 30)
        
        try:
            response = requests.get(api_url, auth=auth, timeout=timeout)
            response.raise_for_status()
            
            try:
                airports_data = response.json()
            except ValueError as e:
                self.stdout.write(self.style.ERROR(f'Invalid JSON: {str(e)}'))
                return
                
            if not isinstance(airports_data, dict):
                self.stdout.write(self.style.ERROR('API response is not a dictionary'))
                return


            # TO-DO: use Django's transaction management, to prevent database errors.
            # from django.db import transaction
            # with transaction.atomic():
            # ...

            cache_service = AirportCacheService()
            created_count = 0
            
            if options['dry_run']:
                self.stdout.write(f"API Response Status: {response.status_code}")
                self.stdout.write(f"Content-Type: {response.headers.get('Content-Type')}")
                self.stdout.write(f"Sample Data: {response.text[:200]}...")
                for iata, airport_data in airports_data.items():
                    self.stdout.write(f"Would process: {airport_data.get('iata', 'N/A')} - {airport_data.get('city', 'N/A')}")
                return
                
            try:
                success = cache_service.cache_airports_data(airports_data)
                if success:
                    created_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f"Error caching airports"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error processing: {str(e)}"))

            if not options['dry_run']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Import completed! Created: {created_count}'
                    )
                )
            
        except requests.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'API request failed: {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Import failed: {str(e)}')
            )