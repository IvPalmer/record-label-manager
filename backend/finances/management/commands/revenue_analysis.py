from django.core.management.base import BaseCommand
from django.db.models import Sum, Count, Q, Avg
from decimal import Decimal
from finances.models import RevenueEvent
from api.models import Label


class Command(BaseCommand):
    help = 'Generate detailed revenue analysis by artist, release, and platform'

    def add_arguments(self, parser):
        parser.add_argument('--label', type=str, required=True, help='Label name')
        parser.add_argument('--year', type=int, help='Filter by year (e.g., 2024)')
        parser.add_argument('--platform', type=str, help='Filter by platform (Bandcamp, Distribution)')
        parser.add_argument('--export-csv', type=str, help='Export to CSV file path')

    def handle(self, *args, **options):
        label_name = options['label']
        year_filter = options.get('year')
        platform_filter = options.get('platform')
        csv_export = options.get('export_csv')
        
        try:
            label = Label.objects.get(name=label_name)
        except Label.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Label "{label_name}" not found'))
            return
        
        # Build query
        queryset = RevenueEvent.objects.filter(label=label)
        
        if year_filter:
            queryset = queryset.filter(occurred_at__year=year_filter)
            
        if platform_filter:
            queryset = queryset.filter(platform__name__icontains=platform_filter)
        
        period_desc = f"{year_filter} " if year_filter else "All Time "
        platform_desc = f"({platform_filter}) " if platform_filter else ""
        
        self.stdout.write(f'\n=== 🎵 {label.name} Revenue Analysis ===')
        self.stdout.write(f'Period: {period_desc}{platform_desc}')
        
        # Overall stats
        total_stats = queryset.aggregate(
            total_revenue=Sum('net_amount_base'),
            total_transactions=Count('id'),
            avg_per_transaction=Avg('net_amount_base')
        )
        
        total_revenue = total_stats['total_revenue'] or 0
        total_transactions = total_stats['total_transactions'] or 0
        avg_transaction = total_stats['avg_per_transaction'] or 0
        
        self.stdout.write(f'Total Revenue: €{total_revenue:.2f}')
        self.stdout.write(f'Total Transactions: {total_transactions:,}')
        self.stdout.write(f'Average per Transaction: €{avg_transaction:.4f}')
        
        # Revenue by ISRC (representing individual tracks)
        self.stdout.write('\n📊 TOP TRACKS BY REVENUE (ISRC):')
        track_revenue = queryset.exclude(isrc='').exclude(
            isrc__icontains='Exchange'
        ).values('isrc').annotate(
            revenue=Sum('net_amount_base'),
            streams=Count('id'),
            platforms=Count('platform', distinct=True)
        ).order_by('-revenue')[:20]
        
        track_analysis = []
        cumulative = Decimal('0')
        
        for i, track in enumerate(track_revenue, 1):
            isrc = track['isrc']
            revenue = track['revenue'] or 0
            streams = track['streams']
            platforms = track['platforms']
            percentage = (revenue / total_revenue * 100) if total_revenue > 0 else 0
            cumulative += revenue
            
            track_data = {
                'rank': i,
                'isrc': isrc,
                'revenue': revenue,
                'streams': streams,
                'platforms': platforms,
                'percentage': percentage
            }
            track_analysis.append(track_data)
            
            self.stdout.write(
                f'{i:2}. {isrc}: €{revenue:.2f} ({percentage:.1f}%) - {streams:,} streams across {platforms} platform(s)'
            )
        
        cumulative_pct = (cumulative / total_revenue * 100) if total_revenue > 0 else 0
        self.stdout.write(f'\nTop 20 tracks represent €{cumulative:.2f} ({cumulative_pct:.1f}%) of total revenue')
        
        # Platform breakdown
        self.stdout.write('\n🌍 REVENUE BY PLATFORM:')
        platform_revenue = queryset.values('platform__name', 'currency').annotate(
            revenue_original=Sum('net_amount'),
            revenue_eur=Sum('net_amount_base'),
            transactions=Count('id')
        ).order_by('-revenue_eur')
        
        for platform in platform_revenue:
            name = platform['platform__name']
            currency = platform['currency']
            revenue_orig = platform['revenue_original'] or 0
            revenue_eur = platform['revenue_eur'] or 0
            transactions = platform['transactions']
            percentage = (revenue_eur / total_revenue * 100) if total_revenue > 0 else 0
            
            self.stdout.write(
                f'{name} ({currency}): {currency} {revenue_orig:.2f} → €{revenue_eur:.2f} ({percentage:.1f}%) - {transactions:,} transactions'
            )
        
        # Export to CSV if requested
        if csv_export:
            self.export_detailed_csv(queryset, csv_export, track_analysis)
            self.stdout.write(f'\n📁 Exported detailed analysis to: {csv_export}')
        
        # Show actionable insights
        self.stdout.write('\n💡 ACTIONABLE INSIGHTS:')
        self.stdout.write('1. Use ISRC codes above to identify your top-earning tracks')
        self.stdout.write('2. Cross-reference with your catalog to find artist names')
        self.stdout.write('3. Top 20 tracks represent majority of revenue - focus on these artists')
        self.stdout.write('4. Export data to CSV for detailed artist payout calculations')
        
        self.stdout.write(f'\n🔧 To export full analysis:')
        cmd_export = f'python manage.py revenue_analysis --label "{label_name}"'
        if year_filter:
            cmd_export += f' --year {year_filter}'
        if platform_filter:
            cmd_export += f' --platform "{platform_filter}"'
        cmd_export += ' --export-csv revenue_analysis.csv'
        self.stdout.write(f'   {cmd_export}')

    def export_detailed_csv(self, queryset, csv_file, track_analysis):
        """Export detailed revenue analysis to CSV"""
        import csv
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'ISRC', 'Revenue_EUR', 'Revenue_Percentage', 'Total_Streams', 
                'Platforms_Count', 'Avg_Per_Stream', 'Rank'
            ])
            
            # Track data
            for track in track_analysis:
                avg_per_stream = track['revenue'] / track['streams'] if track['streams'] > 0 else 0
                writer.writerow([
                    track['isrc'],
                    f"{track['revenue']:.2f}",
                    f"{track['percentage']:.1f}%",
                    track['streams'],
                    track['platforms'],
                    f"{avg_per_stream:.4f}",
                    track['rank']
                ])
