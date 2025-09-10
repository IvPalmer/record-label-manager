# Improved data model with separate tables for different revenue sources

from django.db import models
from decimal import Decimal


class DistributionRevenue(models.Model):
    """Streaming revenue from distribution partners (Zebralution, etc.)"""
    source_file = models.ForeignKey('finances.SourceFile', on_delete=models.PROTECT)
    label = models.ForeignKey('api.Label', on_delete=models.CASCADE)
    
    # Period info
    occurred_at = models.DateField()  # Quarter/month level
    year = models.IntegerField()
    quarter = models.IntegerField()
    
    # Track info
    catalog_number = models.CharField(max_length=50, blank=True)
    release_artist = models.CharField(max_length=200, blank=True) 
    release_name = models.CharField(max_length=200, blank=True)
    track_artist = models.CharField(max_length=200, blank=True)
    track_title = models.CharField(max_length=200, blank=True)
    mix_name = models.CharField(max_length=200, blank=True)
    isrc = models.CharField(max_length=32, blank=True)
    ean = models.CharField(max_length=32, blank=True)
    
    # Platform info
    store_name = models.CharField(max_length=100, blank=True)  # Spotify, Apple Music, etc.
    sale_type = models.CharField(max_length=20, blank=True)    # Stream, Track, etc.
    format_type = models.CharField(max_length=20, blank=True)  # Stream, Digital, etc.
    
    # Financial data
    quantity = models.IntegerField(default=0)          # Number of streams
    value_gross = models.DecimalField(max_digits=18, decimal_places=6, default=0)    # Gross platform revenue
    deal_percentage = models.DecimalField(max_digits=6, decimal_places=4, default=0) # Platform deal (0.95 = 95%)
    royalty_net = models.DecimalField(max_digits=18, decimal_places=6, default=0)    # What you actually receive
    
    # Deduplication
    row_hash = models.CharField(max_length=64, unique=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['label', 'occurred_at']),
            models.Index(fields=['track_artist', 'track_title']),
            models.Index(fields=['year', 'quarter']),
            models.Index(fields=['store_name']),
        ]


class BandcampRevenue(models.Model):
    """Direct sales revenue from Bandcamp"""
    source_file = models.ForeignKey('finances.SourceFile', on_delete=models.PROTECT)
    label = models.ForeignKey('api.Label', on_delete=models.CASCADE)
    
    # Transaction info
    transaction_date = models.DateTimeField()
    transaction_id = models.CharField(max_length=50, blank=True)
    
    # Item info
    item_type = models.CharField(max_length=20, blank=True)  # album, track
    item_name = models.CharField(max_length=200, blank=True)
    artist_name = models.CharField(max_length=200, blank=True) 
    
    # Financial data
    currency = models.CharField(max_length=3, default='USD')
    item_price = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    quantity = models.IntegerField(default=1)
    sub_total = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    transaction_fee = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    amount_received = models.DecimalField(max_digits=18, decimal_places=6, default=0)  # Net to you
    amount_received_eur = models.DecimalField(max_digits=18, decimal_places=6, default=0)  # EUR equivalent
    
    # Buyer info (optional for analysis)
    buyer_country = models.CharField(max_length=100, blank=True)
    buyer_country_code = models.CharField(max_length=2, blank=True)
    
    # Deduplication
    row_hash = models.CharField(max_length=64, unique=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['label', 'transaction_date']),
            models.Index(fields=['artist_name']),
            models.Index(fields=['item_name']),
        ]


# Consolidated view for analytics (database view)
class ConsolidatedRevenue(models.Model):
    """Database view that combines both revenue sources for analysis"""
    
    # Source identification
    revenue_source = models.CharField(max_length=20)  # 'distribution' or 'bandcamp'
    
    # Common fields
    label = models.ForeignKey('api.Label', on_delete=models.CASCADE)
    date = models.DateField()
    year = models.IntegerField()
    quarter = models.IntegerField()
    month = models.IntegerField()
    
    # Track identification
    artist_name = models.CharField(max_length=200)
    track_name = models.CharField(max_length=200) 
    catalog_number = models.CharField(max_length=50, blank=True)
    isrc = models.CharField(max_length=32, blank=True)
    
    # Platform
    platform = models.CharField(max_length=100)
    
    # Metrics
    streams = models.IntegerField(default=0)      # For distribution
    downloads = models.IntegerField(default=0)    # For bandcamp
    revenue_eur = models.DecimalField(max_digits=18, decimal_places=6)
    
    class Meta:
        managed = False  # Database view, not managed by Django
        db_table = 'consolidated_revenue_view'
