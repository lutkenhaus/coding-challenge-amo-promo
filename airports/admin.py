from django.contrib import admin
from .models import Airport

# Register your models here.

@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ('iata', 'city', 'state', 'lat', 'lon')
    search_fields = ('iata', 'city')
    list_filter = ('state',)