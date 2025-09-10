from django.core.management.base import BaseCommand
from django.db.models import Sum, Count, Max, Min
from finances.models import RevenueEvent


class Command(BaseCommand):
    help = 'Check Bandcamp data quality and totals'

    def handle(self, *args, **options):
        bc_records = RevenueEvent.objects.filter(platform__name='Bandcamp')
        
        self.stdout.write('BANDCAMP DATA ANALYSIS:')
        self.stdout.write('=' * 40)
        
        # Basic stats
        bc_count = bc_records.count()
        bc_total_usd = bc_records.aggregate(total=Sum('net_amount'))['total'] or 0
        bc_total_eur = bc_records.aggregate(total=Sum('net_amount_base'))['total'] or 0
        
        self.stdout.write(f'Records: {bc_count:,}')
        self.stdout.write(f'Total USD: ${float(bc_total_usd):,.2f}')
        self.stdout.write(f'Total EUR: €{float(bc_total_eur):,.2f}')
        self.stdout.write(f'Average per record: ${float(bc_total_usd / bc_count):,.2f}' if bc_count > 0 else '$0.00')
        
        # Amount distribution
        zero_count = bc_records.filter(net_amount=0).count()
        small_count = bc_records.filter(net_amount__gt=0, net_amount__lt=1).count()
        medium_count = bc_records.filter(net_amount__gte=1, net_amount__lt=10).count()
        large_count = bc_records.filter(net_amount__gte=10).count()
        
        self.stdout.write('')
        self.stdout.write('AMOUNT DISTRIBUTION:')
        self.stdout.write(f'Zero amounts: {zero_count:,} ({zero_count/bc_count*100:.1f}%)')
        self.stdout.write(f'Small (0-1): {small_count:,} ({small_count/bc_count*100:.1f}%)')
        self.stdout.write(f'Medium (1-10): {medium_count:,} ({medium_count/bc_count*100:.1f}%)')
        self.stdout.write(f'Large (10+): {large_count:,} ({large_count/bc_count*100:.1f}%)')
        
        # Top sales
        self.stdout.write('')
        self.stdout.write('TOP 10 BANDCAMP SALES:')
        top_sales = bc_records.order_by('-net_amount')[:10]
        for i, sale in enumerate(top_sales, 1):
            amount_usd = float(sale.net_amount)
            item_name = (sale.track_title or 'Unknown')[:50]
            artist_name = (sale.track_artist_name or 'Unknown')[:30]
            self.stdout.write(f'{i:2}. ${amount_usd:7.2f} - {artist_name} - {item_name}')
        
        # Expected vs actual
        self.stdout.write('')
        self.stdout.write('VALIDATION:')
        self.stdout.write('Expected Bandcamp total: ~$25,000-30,000 (from pipeline preview)')
        self.stdout.write(f'Actual total: ${float(bc_total_usd):,.2f}')
        
        if float(bc_total_usd) < 20000:
            self.stdout.write('⚠️  Total seems too low - check import logic')
            
            # Check for parsing issues
            with_amounts = bc_records.exclude(net_amount=0).count()
            self.stdout.write(f'Records with non-zero amounts: {with_amounts:,}/{bc_count:,} ({with_amounts/bc_count*100:.1f}%)')
            
        else:
            self.stdout.write('✓ Total looks reasonable')

        # Check years coverage
        years = bc_records.extra(
            select={'year': 'EXTRACT(year FROM occurred_at)'}
        ).values('year').annotate(count=Count('id')).order_by('year')
        
        self.stdout.write('')
        self.stdout.write('BANDCAMP BY YEAR:')
        for year_data in years:
            if year_data['year']:
                year = int(year_data['year'])
                count = year_data['count']
                year_revenue = bc_records.filter(occurred_at__year=year).aggregate(total=Sum('net_amount'))['total'] or 0
                self.stdout.write(f'{year}: {count:4,} records, ${float(year_revenue):7,.2f}')
