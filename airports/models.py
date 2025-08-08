from django.db import models
from django.utils import timezone

# Create your models here.
# 
# "AAX": {"iata": "AAX", "city": "Araxa", "lat": -19.568056, "lon": -46.92917, "state": "MG"}

class Airport(models.Model):

    iata = models.CharField(
        max_length=3,
        unique=True,
        db_index=True,
        help_text="3-letter IATA airport code ('GRU' or 'JFK')"
    )
    city = models.CharField(
        max_length=100,
        help_text="City where airport is located"
    )
    latitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7,
        help_text="Latitude coordinate for distance calculations"
    )
    longitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7,
        help_text="Longitude coordinate for distance calculations"
    )
    state = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="State/Province (mainly for domestic airports)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this airport is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_sync = models.DateTimeField(
        default=timezone.now,
        help_text="Last time this record was synced from the API"
    )

    class Meta:
        db_table = 'airports'
        ordering = ['iata']
        indexes = [
            models.Index(fields=['iata']),
            models.Index(fields=['city']),
            models.Index(fields=['is_active']),
            models.Index(fields=['last_sync']),
        ]

    def __str__(self):
        return f"{self.iata} - ({self.city})"

    def mark_as_inactive(self):
        """Mark airport as inactive (soft delete)"""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])
    
    def update_sync_time(self):
        """Update the last sync timestamp"""
        self.last_sync = timezone.now()
        self.save(update_fields=['last_sync'])