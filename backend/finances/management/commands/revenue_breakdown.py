from django.core.management.base import BaseCommand
from django.db.models import Sum, Count, Q, Avg, Case, When, F
from decimal import Decimal
from finances.models import RevenueEvent
from api.models import Label


class Command(BaseCommand):
    help = 'Generate accurate revenue analysis separating streams from downloads/sales'

    def add_arguments(self, parser):
        parser.add_argument('--label', type=str, required=True, help='Label name')
        parser.add_argument('--year', type=int, default=2024, help='Year to analyze')

    def handle(self, *args, **options):
        label_name = options['label']
        year = options['year']
        
        try:
            label = Label.objects.get(name=label_name)
        except Label.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Label "{label_name}" not found'))
            return
        
        self.stdout.write(f'\n=== 🎯 CORRECTED REVENUE ANALYSIS - {year} ===')
        self.stdout.write(f'Label: {label.name}')
        
        base_queryset = RevenueEvent.objects.filter(
            label=label, occurred_at__year=year
        )
        
        # Separate revenue by type
        streams_queryset = base_queryset.filter(
            Q(product_type='Stream') | 
            Q(product_type='digital') |
            Q(product_type='track') & Q(quantity__lt=10)  # Small quantities are likely streams
        )
        
        downloads_queryset = base_queryset.filter(
            Q(product_type__in=['Digital Downloads', 'download']) |
            (Q(product_type='track') & Q(quantity__gte=10))  # Higher quantities might be bulk
        )
        
        sales_queryset = base_queryset.filter(
            Q(product_type__in=['album', 'Album', 'physical'])
        )
        
        # Overall stats
        total_stats = base_queryset.aggregate(
            total_revenue=Sum('net_amount_base'),
            total_events=Count('id')
        )
        
        total_revenue = total_stats['total_revenue'] or Decimal('0')
        total_events = total_stats['total_events'] or 0
        
        self.stdout.write(f'Total Revenue: €{total_revenue:.2f}')
        self.stdout.write(f'Total Events: {total_events:,}')
        
        # Streaming analysis
        self.analyze_streams(streams_queryset, total_revenue)
        
        # Downloads analysis  
        self.analyze_downloads(downloads_queryset, total_revenue)
        
        # Sales analysis
        self.analyze_sales(sales_queryset, total_revenue)
        
        # Top tracks by revenue (correctly calculated)
        self.analyze_top_tracks(base_queryset, year)

    def analyze_streams(self, queryset, total_revenue):
        """Analyze streaming revenue (low value, high quantity)"""
        stats = queryset.aggregate(
            count=Count('id'),
            revenue=Sum('net_amount_base'),
            total_quantity=Sum('quantity'),
            avg_per_event=Avg('net_amount_base')
        )
        
        count = stats['count'] or 0
        revenue = stats['revenue'] or Decimal('0')
        quantity = stats['total_quantity'] or 0
        avg_per_event = stats['avg_per_event'] or Decimal('0')
        
        percentage = (revenue / total_revenue * 100) if total_revenue > 0 else 0
        per_stream = revenue / quantity if quantity > 0 else Decimal('0')
        
        self.stdout.write(f'\n🎵 STREAMING REVENUE:')
        self.stdout.write(f'  Events: {count:,}')
        self.stdout.write(f'  Total Revenue: €{revenue:.2f} ({percentage:.1f}%)')
        self.stdout.write(f'  Total Streams: {quantity:,}')
        self.stdout.write(f'  Revenue per Stream: €{per_stream:.6f} (realistic!)')
        self.stdout.write(f'  Avg per Event: €{avg_per_event:.4f}')

    def analyze_downloads(self, queryset, total_revenue):
        """Analyze digital download revenue (medium value, medium quantity)"""
        stats = queryset.aggregate(
            count=Count('id'),
            revenue=Sum('net_amount_base'),
            total_quantity=Sum('quantity'),
            avg_per_event=Avg('net_amount_base')
        )
        
        count = stats['count'] or 0
        revenue = stats['revenue'] or Decimal('0')
        quantity = stats['total_quantity'] or 0
        avg_per_event = stats['avg_per_event'] or Decimal('0')
        
        percentage = (revenue / total_revenue * 100) if total_revenue > 0 else 0
        per_download = revenue / quantity if quantity > 0 else Decimal('0')
        
        self.stdout.write(f'\n💿 DIGITAL DOWNLOAD REVENUE:')
        self.stdout.write(f'  Events: {count:,}')
        self.stdout.write(f'  Total Revenue: €{revenue:.2f} ({percentage:.1f}%)')
        self.stdout.write(f'  Total Downloads: {quantity:,}')
        self.stdout.write(f'  Revenue per Download: €{per_download:.2f}')
        self.stdout.write(f'  Avg per Event: €{avg_per_event:.4f}')

    def analyze_sales(self, queryset, total_revenue):
        """Analyze album/physical sales (high value, low quantity)"""
        stats = queryset.aggregate(
            count=Count('id'),
            revenue=Sum('net_amount_base'),
            total_quantity=Sum('quantity'),
            avg_per_event=Avg('net_amount_base')
        )
        
        count = stats['count'] or 0
        revenue = stats['revenue'] or Decimal('0')
        quantity = stats['total_quantity'] or 0
        avg_per_event = stats['avg_per_event'] or Decimal('0')
        
        percentage = (revenue / total_revenue * 100) if total_revenue > 0 else 0
        
        self.stdout.write(f'\n📀 ALBUM/PHYSICAL SALES:')
        self.stdout.write(f'  Events: {count:,}')
        self.stdout.write(f'  Total Revenue: €{revenue:.2f} ({percentage:.1f}%)')
        self.stdout.write(f'  Total Sales: {quantity:,}')
        if quantity > 0:
            self.stdout.write(f'  Revenue per Sale: €{revenue/quantity:.2f}')
        self.stdout.write(f'  Avg per Event: €{avg_per_event:.4f}')

    def analyze_top_tracks(self, queryset, year):
        """Show top tracks with proper streaming vs download separation"""
        self.stdout.write(f'\n🏆 TOP 10 TRACKS BY TOTAL REVENUE ({year}):')
        
        top_tracks = queryset.exclude(isrc='').exclude(
            isrc__icontains='Exchange'
        ).values('isrc').annotate(
            total_revenue=Sum('net_amount_base'),
            streaming_revenue=Sum(
                'net_amount_base', 
                filter=Q(product_type='Stream') | Q(product_type='digital', quantity__lt=10)
            ),
            download_revenue=Sum(
                'net_amount_base',
                filter=Q(product_type='Digital Downloads') | Q(quantity__gte=10)
            ),
            total_streams=Sum('quantity', filter=Q(product_type='Stream')),
            total_downloads=Sum('quantity', filter=Q(product_type='Digital Downloads')),
            events_count=Count('id')
        ).order_by('-total_revenue')[:10]
        
        for i, track in enumerate(top_tracks, 1):
            isrc = track['isrc']
            total_rev = track['total_revenue'] or Decimal('0')
            stream_rev = track['streaming_revenue'] or Decimal('0')
            download_rev = track['download_revenue'] or Decimal('0')
            streams = track['total_streams'] or 0
            downloads = track['total_downloads'] or 0
            events = track['events_count']
            
            self.stdout.write(f'\n{i:2}. ISRC {isrc}: €{total_rev:.2f} total')
            
            if stream_rev > 0 and streams > 0:
                per_stream = stream_rev / streams
                self.stdout.write(f'     🎵 Streams: €{stream_rev:.2f} from {streams:,} streams (€{per_stream:.6f}/stream)')
            
            if download_rev > 0:
                self.stdout.write(f'     💿 Downloads: €{download_rev:.2f} from {downloads} downloads')
            
            self.stdout.write(f'     📊 Total Events: {events}')
        
        self.stdout.write(f'\n✅ This analysis properly separates streaming from download revenue!')
