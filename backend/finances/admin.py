from django.contrib import admin
from django.db.models import Sum, Count
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponse
import csv

from .models import (
    Platform, Store, Country, DataSource, SourceFile, ImportBatch,
    RevenueEvent, CostEvent, Contract, ContractParty, RecoupmentAccount,
    PayoutRun, PayoutLine, PlatformRelease, PlatformTrack, FxRate
)


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor_key', 'revenue_count', 'total_revenue')
    search_fields = ('name', 'vendor_key')
    
    def revenue_count(self, obj):
        return obj.revenueevent_set.count()
    revenue_count.short_description = 'Revenue Events'
    
    def total_revenue(self, obj):
        total = obj.revenueevent_set.aggregate(Sum('net_amount_base'))['net_amount_base__sum'] or 0
        return f"€{total:.2f}"
    total_revenue.short_description = 'Total Revenue'


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'platform', 'vendor_key')
    list_filter = ('platform',)
    search_fields = ('name', 'vendor_key')


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'iso2')
    search_fields = ('name', 'iso2')


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'source_file_count')
    search_fields = ('name', 'vendor')
    
    def source_file_count(self, obj):
        return obj.sourcefile_set.count()
    source_file_count.short_description = 'Source Files'


@admin.register(SourceFile)
class SourceFileAdmin(admin.ModelAdmin):
    list_display = ('path', 'label', 'datasource', 'statement_type', 'period_display', 'bytes_display', 'registered_at')
    list_filter = ('datasource', 'label', 'statement_type', 'registered_at')
    search_fields = ('path', 'sha256')
    readonly_fields = ('sha256', 'bytes', 'mtime', 'registered_at')
    
    def period_display(self, obj):
        if obj.period_start and obj.period_end:
            return f"{obj.period_start} to {obj.period_end}"
        elif obj.period_start:
            return str(obj.period_start)
        return "-"
    period_display.short_description = 'Period'
    
    def bytes_display(self, obj):
        if obj.bytes > 1024 * 1024:
            return f"{obj.bytes / 1024 / 1024:.1f} MB"
        elif obj.bytes > 1024:
            return f"{obj.bytes / 1024:.1f} KB"
        return f"{obj.bytes} bytes"
    bytes_display.short_description = 'Size'


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'label', 'started_at', 'finished_at', 'status', 'duration')
    list_filter = ('label', 'status', 'started_at')
    readonly_fields = ('started_at', 'finished_at')
    
    def duration(self, obj):
        if obj.started_at and obj.finished_at:
            delta = obj.finished_at - obj.started_at
            return str(delta).split('.')[0]  # Remove microseconds
        return "-"
    duration.short_description = 'Duration'


@admin.register(RevenueEvent)
class RevenueEventAdmin(admin.ModelAdmin):
    list_display = ('occurred_at', 'platform', 'label', 'currency', 'net_amount', 'product_type', 'quantity')
    list_filter = ('platform', 'label', 'currency', 'product_type', 'occurred_at')
    search_fields = ('isrc', 'upc_ean', 'label_order_nr')
    readonly_fields = ('source_file', 'row_hash')
    date_hierarchy = 'occurred_at'
    
    actions = ['export_to_csv']
    
    def export_to_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="revenue_events.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Date', 'Platform', 'Store', 'Country', 'Currency', 'Product Type',
            'Quantity', 'Gross Amount', 'Net Amount', 'Net Amount (EUR)',
            'ISRC', 'UPC/EAN', 'Label Order Nr'
        ])
        
        for event in queryset:
            writer.writerow([
                event.occurred_at,
                event.platform.name if event.platform else '',
                event.store.name if event.store else '',
                event.country.name if event.country else '',
                event.currency,
                event.product_type,
                event.quantity,
                event.gross_amount,
                event.net_amount,
                event.net_amount_base,
                event.isrc,
                event.upc_ean,
                event.label_order_nr
            ])
        
        return response
    
    export_to_csv.short_description = "Export selected events to CSV"


@admin.register(CostEvent)
class CostEventAdmin(admin.ModelAdmin):
    list_display = ('occurred_at', 'platform', 'label', 'description', 'currency', 'amount')
    list_filter = ('platform', 'label', 'currency', 'occurred_at')
    readonly_fields = ('source_file',)
    date_hierarchy = 'occurred_at'


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('label', 'scope', 'release', 'track', 'effective_from', 'effective_to', 'basis', 'default_rate')
    list_filter = ('label', 'scope', 'basis', 'effective_from')
    search_fields = ('notes',)


@admin.register(ContractParty)
class ContractPartyAdmin(admin.ModelAdmin):
    list_display = ('artist', 'contract', 'role', 'rate', 'payee_name', 'payee_currency')
    list_filter = ('role', 'payee_currency')
    search_fields = ('artist__name', 'payee_name')


@admin.register(PayoutRun)  
class PayoutRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'label', 'period_display', 'base_currency', 'executed_at', 'status', 'total_amount')
    list_filter = ('label', 'status', 'base_currency', 'executed_at')
    readonly_fields = ('executed_at',)
    
    actions = ['export_payout_csv']
    
    def period_display(self, obj):
        return f"Q{obj.period_quarter} {obj.period_year}"
    period_display.short_description = 'Period'
    
    def total_amount(self, obj):
        total = obj.lines.aggregate(Sum('amount_base'))['amount_base__sum'] or 0
        return f"{obj.base_currency} {total:.2f}"
    total_amount.short_description = 'Total Amount'
    
    def export_payout_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="payout_runs.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Run ID', 'Label', 'Period', 'Artist', 'Release', 'Track',
            'Amount (Base)', 'Amount (Original)', 'Original Currency', 'FX Rate'
        ])
        
        for run in queryset:
            for line in run.lines.all():
                writer.writerow([
                    run.id,
                    run.label.name,
                    f"Q{run.period_quarter} {run.period_year}",
                    line.artist.name if line.artist else '',
                    line.release.title if line.release else '',
                    line.track.title if line.track else '',
                    line.amount_base,
                    line.amount_original,
                    line.original_currency,
                    line.fx_rate_used
                ])
        
        return response
    
    export_payout_csv.short_description = "Export payout details to CSV"


@admin.register(FxRate)
class FxRateAdmin(admin.ModelAdmin):
    list_display = ('date', 'from_ccy', 'to_ccy', 'rate')
    list_filter = ('from_ccy', 'to_ccy', 'date')
    search_fields = ('from_ccy', 'to_ccy')
    date_hierarchy = 'date'


# Register remaining models with basic admin
admin.site.register(RecoupmentAccount)
admin.site.register(PayoutLine)
admin.site.register(PlatformRelease)
admin.site.register(PlatformTrack)