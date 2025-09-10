from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date

from finances.models import (
    RevenueEvent, PayoutRun, PayoutLine, Contract, ContractParty
)
from api.models import Label, Artist


class Command(BaseCommand):
    help = 'Calculate artist payouts for a given period'

    def add_arguments(self, parser):
        parser.add_argument('--label', type=str, required=True, help='Label name')
        parser.add_argument('--period', type=str, required=True, help='Period in format YYYY-Q# (e.g., 2024-Q4)')
        parser.add_argument('--preview', action='store_true', help='Preview mode (no database changes)')
        parser.add_argument('--default-rate', type=float, default=0.5, help='Default artist split rate (0.0-1.0)')

    def handle(self, *args, **options):
        label_name = options['label']
        period = options['period']
        preview = options.get('preview', False)
        default_rate = Decimal(str(options.get('default_rate', 0.5)))
        
        # Parse period
        try:
            year_str, quarter_str = period.split('-Q')
            year = int(year_str)
            quarter = int(quarter_str)
            if not (1 <= quarter <= 4):
                raise ValueError()
        except ValueError:
            raise CommandError('Period must be in format YYYY-Q# (e.g., 2024-Q4)')
        
        # Get label
        try:
            label = Label.objects.get(name=label_name)
        except Label.DoesNotExist:
            raise CommandError(f'Label "{label_name}" does not exist.')
        
        # Check if payout already exists
        existing_payout = PayoutRun.objects.filter(
            label=label, period_year=year, period_quarter=quarter
        ).first()
        
        if existing_payout and not preview:
            self.stdout.write(
                self.style.WARNING(f'Payout already exists for {period}: Run #{existing_payout.id}')
            )
            return
        
        self.stdout.write(f'Calculating payout for {label.name} - {period}')
        if preview:
            self.stdout.write(self.style.WARNING('PREVIEW MODE - No changes will be saved'))
        
        # Calculate date range for the quarter
        start_month = (quarter - 1) * 3 + 1
        start_date = date(year, start_month, 1)
        
        if quarter == 4:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, start_month + 3, 1)
        
        # Get revenue events for the period
        revenue_events = RevenueEvent.objects.filter(
            label=label,
            occurred_at__date__gte=start_date,
            occurred_at__date__lt=end_date
        ).select_related('platform', 'release', 'track')
        
        self.stdout.write(f'Found {revenue_events.count()} revenue events in period')
        
        # Group by release/track and calculate totals
        payout_calculations = self.calculate_payouts(revenue_events, default_rate)
        
        # Display summary
        self.display_payout_summary(payout_calculations)
        
        # Create payout run if not in preview mode
        if not preview:
            with transaction.atomic():
                payout_run = PayoutRun.objects.create(
                    label=label,
                    period_year=year,
                    period_quarter=quarter,
                    base_currency='EUR'
                )
                
                self.create_payout_lines(payout_run, payout_calculations)
                
                self.stdout.write(
                    self.style.SUCCESS(f'Created payout run #{payout_run.id}')
                )
        
    def calculate_payouts(self, revenue_events, default_rate):
        """Calculate payout amounts for artists"""
        # Group events by artist/release/track
        payout_data = {}
        
        for event in revenue_events:
            # Try to identify the artist - this is a simplified approach
            # In a real system, you'd have proper artist-release-track relationships
            artist_key = 'Unknown Artist'  # Default
            
            # For now, we'll create a single payout per platform
            # In practice, you'd need proper artist mapping
            key = f"{event.platform.name}_{event.currency}"
            
            if key not in payout_data:
                payout_data[key] = {
                    'platform': event.platform.name,
                    'currency': event.currency,
                    'total_revenue': Decimal('0'),
                    'events_count': 0,
                    'artist_payout': Decimal('0')
                }
            
            payout_data[key]['total_revenue'] += event.net_amount
            payout_data[key]['events_count'] += 1
            payout_data[key]['artist_payout'] += event.net_amount * default_rate
        
        return payout_data
    
    def display_payout_summary(self, payout_calculations):
        """Display payout summary"""
        self.stdout.write('\n=== PAYOUT CALCULATION SUMMARY ===')
        
        total_revenue = Decimal('0')
        total_artist_payout = Decimal('0')
        
        for key, data in payout_calculations.items():
            self.stdout.write(f"\n{data['platform']} ({data['currency']}):")
            self.stdout.write(f"  Events: {data['events_count']}")
            self.stdout.write(f"  Total Revenue: {data['currency']} {data['total_revenue']:.2f}")
            self.stdout.write(f"  Artist Payout: {data['currency']} {data['artist_payout']:.2f}")
            
            # Convert to EUR for totals (simplified - would need FX rates)
            if data['currency'] == 'EUR':
                total_revenue += data['total_revenue']
                total_artist_payout += data['artist_payout']
            else:
                # Assume 1 USD = 0.85 EUR for demo purposes
                # In production, use proper FX rates
                fx_rate = Decimal('0.85') if data['currency'] == 'USD' else Decimal('1.0')
                total_revenue += data['total_revenue'] * fx_rate
                total_artist_payout += data['artist_payout'] * fx_rate
        
        self.stdout.write('\n=== TOTALS (EUR equivalent) ===')
        self.stdout.write(f"Total Revenue: €{total_revenue:.2f}")
        self.stdout.write(f"Total Artist Payout: €{total_artist_payout:.2f}")
        self.stdout.write(f"Label Share: €{(total_revenue - total_artist_payout):.2f}")
        
    def create_payout_lines(self, payout_run, payout_calculations):
        """Create payout line items"""
        # This is a simplified version - in practice you'd have:
        # - Proper artist contracts
        # - Individual artist payouts
        # - Recoupment handling
        # - Proper FX conversion
        
        from api.models import Artist
        
        # Get or create placeholder artist
        placeholder_artist, _ = Artist.objects.get_or_create(
            name='Various Artists',
            defaults={
                'project': 'Various Artists',
                'bio': 'Placeholder for multiple artists payouts',
                'email': 'payouts@tropicaltwista.com',
                'country': 'BR'
            }
        )
        
        # For now, create summary lines per platform
        for key, data in payout_calculations.items():
            # Create a generic "Various Artists" entry for demo
            # In practice, you'd iterate through actual artists
            PayoutLine.objects.create(
                payout_run=payout_run,
                artist=placeholder_artist,
                amount_base=data['artist_payout'],
                amount_original=data['artist_payout'],
                original_currency=data['currency'],
                fx_rate_used=Decimal('1.0')  # Would be actual FX rate
            )
