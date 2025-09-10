# Clean data model with separate tables for each distributor

from django.db import models


class ZebralutionRevenue(models.Model):
    """Zebralution distribution data (2021-2022)"""
    source_file = models.ForeignKey('finances.SourceFile', on_delete=models.PROTECT)
    label = models.ForeignKey('api.Label', on_delete=models.CASCADE)
    
    # Period (2021-09 format)
    period = models.CharField(max_length=10)
    year = models.IntegerField()
    month = models.IntegerField()
    quarter = models.IntegerField()
    
    # Track identification  
    artist = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    isrc = models.CharField(max_length=32, blank=True)
    ean = models.CharField(max_length=32, blank=True)
    label_order_nr = models.CharField(max_length=50, blank=True)  # TTR069
    
    # Platform
    shop = models.CharField(max_length=100)  # AppleMusic, Spotify, etc.
    country = models.CharField(max_length=2, blank=True)
    
    # Revenue (converted from European format)
    sales = models.IntegerField(default=0)  # Stream count
    revenue_eur = models.DecimalField(max_digits=18, decimal_places=9, default=0)      # Gross
    revenue_net_eur = models.DecimalField(max_digits=18, decimal_places=9, default=0)  # Net to label
    
    row_hash = models.CharField(max_length=64, unique=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['year', 'quarter']),
            models.Index(fields=['artist', 'title']),
            models.Index(fields=['isrc']),
        ]


class LabelworxRevenue(models.Model):
    """Labelworx distribution data (2023-2025)"""
    source_file = models.ForeignKey('finances.SourceFile', on_delete=models.PROTECT)
    label = models.ForeignKey('api.Label', on_delete=models.CASCADE)
    
    # Derived from file path (since not in data)
    year = models.IntegerField()
    quarter = models.IntegerField()
    
    # Track identification
    catalog_number = models.CharField(max_length=50, blank=True)
    release_artist = models.CharField(max_length=200, blank=True)
    release_name = models.CharField(max_length=200, blank=True)
    track_artist = models.CharField(max_length=200)
    track_title = models.CharField(max_length=200)
    mix_name = models.CharField(max_length=200, blank=True)
    isrc = models.CharField(max_length=32, blank=True)
    ean = models.CharField(max_length=32, blank=True)
    
    # Platform  
    store_name = models.CharField(max_length=100)  # SoundCloud, Spotify, etc.
    format_type = models.CharField(max_length=20, blank=True)  # Stream
    sale_type = models.CharField(max_length=20, blank=True)    # Track
    
    # Revenue (already in correct format)
    qty = models.IntegerField(default=0)  # Stream count
    value = models.DecimalField(max_digits=18, decimal_places=9, default=0)    # Gross 
    deal = models.DecimalField(max_digits=5, decimal_places=2, default=0)      # Deal % (0.95)
    royalty = models.DecimalField(max_digits=18, decimal_places=9, default=0)  # Net to label
    
    row_hash = models.CharField(max_length=64, unique=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['year', 'quarter']),
            models.Index(fields=['track_artist', 'track_title']),
            models.Index(fields=['isrc']),
            models.Index(fields=['catalog_number']),
        ]


class BandcampRevenue(models.Model):
    """Bandcamp direct sales (2015-2025)"""
    source_file = models.ForeignKey('finances.SourceFile', on_delete=models.PROTECT)
    label = models.ForeignKey('api.Label', on_delete=models.CASCADE)
    
    # Transaction info
    transaction_date = models.DateTimeField()
    year = models.IntegerField()
    quarter = models.IntegerField()
    month = models.IntegerField()
    
    # Item info
    item_type = models.CharField(max_length=20)    # album, track
    item_name = models.CharField(max_length=200)
    artist = models.CharField(max_length=200)
    
    # Financial
    currency = models.CharField(max_length=3)
    item_price = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    quantity = models.IntegerField(default=1)
    amount_received = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    amount_received_eur = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    
    # Buyer info (for analytics)
    buyer_country = models.CharField(max_length=100, blank=True)
    buyer_country_code = models.CharField(max_length=2, blank=True)
    
    row_hash = models.CharField(max_length=64, unique=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['year', 'quarter']),
            models.Index(fields=['artist']),
            models.Index(fields=['transaction_date']),
        ]


# Unified view for analytics (database view)
class ConsolidatedAnalytics(models.Model):
    """Read-only view combining all revenue sources"""
    
    vendor = models.CharField(max_length=20)      # Zebralution, Labelworx, Bandcamp
    year = models.IntegerField()
    quarter = models.IntegerField()
    month = models.IntegerField(null=True)
    
    track_artist = models.CharField(max_length=200)
    track_title = models.CharField(max_length=200)
    isrc = models.CharField(max_length=32, blank=True)
    catalog_number = models.CharField(max_length=50, blank=True)
    
    platform = models.CharField(max_length=100)   # Spotify, Apple Music, Bandcamp
    streams = models.IntegerField(default=0)
    downloads = models.IntegerField(default=0)
    revenue_eur = models.DecimalField(max_digits=18, decimal_places=6)
    
    class Meta:
        managed = False  # Database view
        db_table = 'consolidated_analytics'
