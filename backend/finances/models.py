from django.db import models


class Platform(models.Model):
    name = models.CharField(max_length=100, unique=True)
    vendor_key = models.CharField(max_length=100, blank=True)

    def __str__(self) -> str:
        return self.name


class Store(models.Model):
    platform = models.ForeignKey('finances.Platform', on_delete=models.CASCADE, related_name='stores')
    name = models.CharField(max_length=100)
    vendor_key = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ('platform', 'name')

    def __str__(self) -> str:
        return f"{self.platform.name} / {self.name}"


class Country(models.Model):
    iso2 = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name


class DataSource(models.Model):
    name = models.CharField(max_length=100, unique=True)
    vendor = models.CharField(max_length=100, blank=True)

    def __str__(self) -> str:
        return self.name


class SourceFile(models.Model):
    datasource = models.ForeignKey('finances.DataSource', on_delete=models.PROTECT)
    label = models.ForeignKey('api.Label', on_delete=models.CASCADE, related_name='source_files')
    path = models.CharField(max_length=512)
    sha256 = models.CharField(max_length=64)
    bytes = models.BigIntegerField()
    mtime = models.DateTimeField()
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    statement_type = models.CharField(max_length=32)
    correction_of = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['label', 'statement_type', 'period_start', 'period_end'])]

    def __str__(self) -> str:
        return f"{self.label.name}: {self.path}"


class ImportBatch(models.Model):
    label = models.ForeignKey('api.Label', on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='completed')


class PlatformRelease(models.Model):
    release = models.ForeignKey('api.Release', on_delete=models.CASCADE)
    platform = models.ForeignKey('finances.Platform', on_delete=models.CASCADE)
    upc_ean = models.CharField(max_length=32, blank=True)
    label_order_nr = models.CharField(max_length=64, blank=True)
    external_ids = models.JSONField(null=True, blank=True)

    class Meta:
        unique_together = ('release', 'platform')


class PlatformTrack(models.Model):
    track = models.ForeignKey('api.Track', on_delete=models.CASCADE)
    platform = models.ForeignKey('finances.Platform', on_delete=models.CASCADE)
    isrc = models.CharField(max_length=32, blank=True)
    external_ids = models.JSONField(null=True, blank=True)

    class Meta:
        unique_together = ('track', 'platform')


class FxRate(models.Model):
    date = models.DateField()
    from_ccy = models.CharField(max_length=3)
    to_ccy = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=18, decimal_places=9)

    class Meta:
        unique_together = ('date', 'from_ccy', 'to_ccy')


class RevenueEvent(models.Model):
    source_file = models.ForeignKey('finances.SourceFile', on_delete=models.PROTECT)
    label = models.ForeignKey('api.Label', on_delete=models.CASCADE)
    occurred_at = models.DateTimeField(null=True, blank=True)
    platform = models.ForeignKey('finances.Platform', on_delete=models.PROTECT)
    store = models.ForeignKey('finances.Store', on_delete=models.PROTECT, null=True, blank=True)
    country = models.ForeignKey('finances.Country', on_delete=models.PROTECT, null=True, blank=True)
    currency = models.CharField(max_length=3)
    product_type = models.CharField(max_length=20, blank=True)
    quantity = models.IntegerField(default=0)
    gross_amount = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    publisher_deduction = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    marketplace_fees = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    transaction_fees = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    net_amount = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    base_ccy = models.CharField(max_length=3, default='EUR')
    net_amount_base = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    release = models.ForeignKey('api.Release', on_delete=models.SET_NULL, null=True, blank=True)
    track = models.ForeignKey('api.Track', on_delete=models.SET_NULL, null=True, blank=True)
    isrc = models.CharField(max_length=32, blank=True)
    upc_ean = models.CharField(max_length=32, blank=True)
    label_order_nr = models.CharField(max_length=64, blank=True)
    track_artist_name = models.CharField(max_length=200, blank=True)
    track_title = models.CharField(max_length=200, blank=True)
    catalog_number = models.CharField(max_length=50, blank=True)
    row_hash = models.CharField(max_length=64, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=['label', 'occurred_at']),
            models.Index(fields=['platform', 'store']),
        ]


class CostEvent(models.Model):
    source_file = models.ForeignKey('finances.SourceFile', on_delete=models.PROTECT)
    label = models.ForeignKey('api.Label', on_delete=models.CASCADE)
    occurred_at = models.DateTimeField(null=True, blank=True)
    platform = models.ForeignKey('finances.Platform', on_delete=models.PROTECT, null=True, blank=True)
    description = models.CharField(max_length=200)
    currency = models.CharField(max_length=3)
    amount = models.DecimalField(max_digits=18, decimal_places=6)
    base_ccy = models.CharField(max_length=3, default='EUR')
    amount_base = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    release = models.ForeignKey('api.Release', on_delete=models.SET_NULL, null=True, blank=True)
    track = models.ForeignKey('api.Track', on_delete=models.SET_NULL, null=True, blank=True)


class Contract(models.Model):
    BASIS_CHOICES = (
        ('gross', 'gross'),
        ('net', 'net'),
        ('platform_net', 'platform_net'),
    )
    SCOPE_CHOICES = (
        ('release', 'release'),
        ('track', 'track'),
    )
    label = models.ForeignKey('api.Label', on_delete=models.CASCADE)
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES)
    release = models.ForeignKey('api.Release', on_delete=models.CASCADE, null=True, blank=True)
    track = models.ForeignKey('api.Track', on_delete=models.CASCADE, null=True, blank=True)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    basis = models.CharField(max_length=20, choices=BASIS_CHOICES, default='net')
    default_rate = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    notes = models.TextField(blank=True)


class ContractParty(models.Model):
    ROLE_CHOICES = (
        ('main', 'main'),
        ('featured', 'featured'),
        ('remixer', 'remixer'),
        ('label', 'label'),
    )
    contract = models.ForeignKey('finances.Contract', on_delete=models.CASCADE, related_name='parties')
    artist = models.ForeignKey('api.Artist', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='main')
    rate = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    payee_name = models.CharField(max_length=200, blank=True)
    payee_currency = models.CharField(max_length=3, blank=True)


class RecoupmentAccount(models.Model):
    TYPE_CHOICES = (
        ('advance', 'advance'),
        ('cost_pool', 'cost_pool'),
    )
    contract = models.ForeignKey('finances.Contract', on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    currency = models.CharField(max_length=3)
    opening_balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)


class PayoutRun(models.Model):
    label = models.ForeignKey('api.Label', on_delete=models.CASCADE)
    period_year = models.IntegerField()
    period_quarter = models.IntegerField()
    base_currency = models.CharField(max_length=3, default='EUR')
    executed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='draft')

    class Meta:
        unique_together = ('label', 'period_year', 'period_quarter')


class PayoutLine(models.Model):
    payout_run = models.ForeignKey('finances.PayoutRun', on_delete=models.CASCADE, related_name='lines')
    artist = models.ForeignKey('api.Artist', on_delete=models.CASCADE)
    contract = models.ForeignKey('finances.Contract', on_delete=models.SET_NULL, null=True, blank=True)
    release = models.ForeignKey('api.Release', on_delete=models.SET_NULL, null=True, blank=True)
    track = models.ForeignKey('api.Track', on_delete=models.SET_NULL, null=True, blank=True)
    revenue_event = models.ForeignKey('finances.RevenueEvent', on_delete=models.SET_NULL, null=True, blank=True)
    cost_event = models.ForeignKey('finances.CostEvent', on_delete=models.SET_NULL, null=True, blank=True)
    amount_base = models.DecimalField(max_digits=18, decimal_places=6)
    amount_original = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    original_currency = models.CharField(max_length=3, blank=True)
    fx_rate_used = models.DecimalField(max_digits=18, decimal_places=9, null=True, blank=True)


