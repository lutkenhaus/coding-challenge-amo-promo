from django.core.management.base import BaseCommand
from django.core.cache import cache
from airports.models import Airport

class Command(BaseCommand):
    help = 'Clear airport cache and optionally database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-db',
            action='store_true',
            help='Also clear airport database records',
        )
    
    def handle(self, *args, **options):
        cache.clear()
        self.stdout.write(self.style.SUCCESS('Cache cleared successfully'))
        
        if options['clear_db']:
            count = Airport.objects.count()
            Airport.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted {count} airport records from database')
            )