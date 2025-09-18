from django.db import models


class RawBandcampEvent(models.Model):
    id = models.BigAutoField(primary_key=True)
    date_str = models.CharField(max_length=32)
    occurred_at = models.DateTimeField(null=True, blank=True)
    item_name = models.CharField(max_length=400, blank=True)
    item_type = models.CharField(max_length=50, blank=True)
    artist = models.CharField(max_length=200, blank=True)
    quantity = models.IntegerField(default=0)
    currency = models.CharField(max_length=3, default='USD')
    item_total = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    amount_received = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    raw_row = models.JSONField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'raw"."bandcamp_event_raw'


class RawZebralutionEvent(models.Model):
    id = models.BigAutoField(primary_key=True)
    period = models.CharField(max_length=16, blank=True)
    shop = models.CharField(max_length=100, blank=True)
    provider = models.CharField(max_length=100, blank=True)
    artist = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=200, blank=True)
    isrc = models.CharField(max_length=32, blank=True)
    ean = models.CharField(max_length=32, blank=True)
    label_order_nr = models.CharField(max_length=64, blank=True)
    country = models.CharField(max_length=2, blank=True)
    sales = models.IntegerField(default=0)
    revenue_eur = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    rev_less_publ_eur = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    raw_row = models.JSONField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'raw"."zebralution_event_raw'


class RawLabelworxEvent(models.Model):
    id = models.BigAutoField(primary_key=True)
    store_name = models.CharField(max_length=100, blank=True)
    track_artist = models.CharField(max_length=200, blank=True)
    track_title = models.CharField(max_length=200, blank=True)
    isrc = models.CharField(max_length=32, blank=True)
    catalog = models.CharField(max_length=64, blank=True)
    qty = models.IntegerField(default=0)
    royalty = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    value = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    format = models.CharField(max_length=50, blank=True)
    raw_row = models.JSONField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'raw"."labelworx_event_raw'


class StagingDistributionEvent(models.Model):
    id = models.BigAutoField(primary_key=True)
    occurred_at = models.DateTimeField(null=True, blank=True)
    platform = models.CharField(max_length=100)
    store = models.CharField(max_length=100, blank=True)
    track_artist_name = models.CharField(max_length=200, blank=True)
    track_title = models.CharField(max_length=200, blank=True)
    isrc = models.CharField(max_length=32, blank=True)
    upc_ean = models.CharField(max_length=32, blank=True)
    catalog_number = models.CharField(max_length=64, blank=True)
    quantity = models.IntegerField(default=0)
    gross_amount_eur = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    net_amount_eur = models.DecimalField(max_digits=18, decimal_places=6, default=0)

    class Meta:
        managed = False
        db_table = 'staging"."distribution_event'


class DwFactRevenue(models.Model):
    id = models.BigAutoField(primary_key=True)
    occurred_at = models.DateField()
    source = models.CharField(max_length=32)
    platform = models.CharField(max_length=100)
    store = models.CharField(max_length=100, blank=True)
    artist_name = models.CharField(max_length=200, blank=True)
    track_title = models.CharField(max_length=200, blank=True)
    isrc = models.CharField(max_length=32, blank=True)
    catalog_number = models.CharField(max_length=64, blank=True)
    upc_ean = models.CharField(max_length=32, blank=True)
    quantity = models.IntegerField(default=0)
    revenue_base = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    base_ccy = models.CharField(max_length=3)
    revenue_brl = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    revenue_usd = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    revenue_eur = models.DecimalField(max_digits=18, decimal_places=6, default=0)

    class Meta:
        managed = False
        # Important: schema-qualified table name for Postgres
        # Use the special quoting pattern so Django does not quote the dot
        db_table = 'dw"."fact_revenue'


