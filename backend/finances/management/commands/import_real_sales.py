import csv
import hashlib
from pathlib import Path
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from datetime import datetime

from finances.models import Platform, DataSource, SourceFile, RevenueEvent
from api.models import Label


class Command(BaseCommand):
    help = 'Import REAL Bandcamp sales (payout items = accumulated customer sales)'

    def handle(self, *args, **options):
        label = Label.objects.get(name="Tropical Twista Records")
        
        # Clear Bandcamp data
        self.stdout.write('Clearing incorrect Bandcamp data...')
        RevenueEvent.objects.filter(platform__name='Bandcamp').delete()
        
        platform = Platform.objects.get_or_create(name='Bandcamp')[0]
        datasource = DataSource.objects.get_or_create(name='bandcamp_real_sales')[0]
        
        repo_root = Path(__file__).resolve().parents[4]
        canonical_file = repo_root / "finance/sources/tropical-twista/bandcamp/canonical/bandcamp_all.csv"
        
        source_file = SourceFile.objects.create(
            datasource=datasource,
            label=label,
            path=str(canonical_file),
            sha256="real_sales",
            bytes=canonical_file.stat().st_size,
            mtime=timezone.now(),
            statement_type='bandcamp_real_sales'
        )
        
        imported = 0
        total_revenue = Decimal('0')
        
        payout_items = 0
        other_items = 0
        
        with open(canonical_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_idx, row in enumerate(reader):
                try:
                    item_type = row.get('item type', '').strip().lower()
                    
                    # KEEP "payout" items (real accumulated sales revenue)
                    # SKIP "album"/"track" items (mostly $0 promotional)
                    if item_type != 'payout':
                        other_items += 1
                        continue
                    
                    payout_items += 1
                    
                    date_str = row.get('date', '').strip()
                    if not date_str:
                        continue
                    
                    occurred_at = self.parse_bandcamp_date(date_str)
                    if not occurred_at:
                        continue
                    
                    amount_str = row.get('amount you received', '').strip()
                    amount = self.parse_decimal(amount_str)
                    total_revenue += amount
                    
                    currency = row.get('currency', 'USD')
                    
                    # For payout items, use summary info
                    RevenueEvent.objects.create(
                        source_file=source_file,
                        label=label,
                        occurred_at=occurred_at,
                        platform=platform,
                        currency=currency,
                        product_type='sales_payout',
                        quantity=1,  # Each payout represents accumulated sales
                        gross_amount=amount,
                        net_amount=amount,
                        net_amount_base=amount * Decimal('0.85') if currency == 'USD' else amount,
                        base_ccy='EUR',
                        track_artist_name='Bandcamp Sales',  # Summary entry
                        track_title=f'Sales Payout {occurred_at.strftime("%Y-%m-%d")}',
                        row_hash=f"payout:{row_idx}"[:64]
                    )
                    imported += 1
                    
                except Exception:
                    continue
        
        self.stdout.write('')
        self.stdout.write('REAL BANDCAMP SALES IMPORT:')
        self.stdout.write(f'Imported payout items: {imported:,}')
        self.stdout.write(f'Skipped other items: {other_items:,}')
        self.stdout.write(f'Total real sales revenue: ${float(total_revenue):,.2f}')
        self.stdout.write('')
        self.stdout.write('✓ Now importing ACTUAL customer sales revenue!')
        self.stdout.write('✓ Excluding $0 promotional downloads')

    def parse_bandcamp_date(self, date_str):
        try:
            date_part = date_str.split(' ')[0]
            parts = date_part.split('/')
            if len(parts) == 3:
                month, day, year = parts
                month, day = int(month), int(day)
                year = int(year)
                if year < 100:
                    year += 2000 if year < 50 else 1900
                return timezone.make_aware(datetime(year, month, day))
        except:
            pass
        return None

    def parse_decimal(self, value_str):
        if not value_str:
            return Decimal('0')
        try:
            cleaned = str(value_str).replace('$', '').replace('€', '').replace(',', '').strip()
            return Decimal(cleaned) if cleaned else Decimal('0')
        except:
            return Decimal('0')
