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
    help = 'Import Bandcamp using pipeline canonical output'

    def handle(self, *args, **options):
        label = Label.objects.get(name="Tropical Twista Records")
        
        # Clear Bandcamp data
        self.stdout.write('Clearing Bandcamp data...')
        RevenueEvent.objects.filter(platform__name='Bandcamp').delete()
        
        platform = Platform.objects.get_or_create(name='Bandcamp')[0]
        datasource = DataSource.objects.get_or_create(name='bandcamp_canonical')[0]
        
        repo_root = Path(__file__).resolve().parents[4]
        canonical_file = repo_root / "finance/sources/tropical-twista/bandcamp/canonical/bandcamp_all.csv"
        
        if not canonical_file.exists():
            self.stdout.write('Pipeline canonical file not found - run pipeline first')
            return
        
        source_file = SourceFile.objects.create(
            datasource=datasource,
            label=label,
            path=str(canonical_file),
            sha256="canonical",
            bytes=canonical_file.stat().st_size,
            mtime=timezone.now(),
            statement_type='bandcamp_canonical'
        )
        
        imported = 0
        total_revenue = Decimal('0')
        
        with open(canonical_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            self.stdout.write('Canonical columns:')
            for i, col in enumerate(reader.fieldnames[:10]):
                self.stdout.write(f'  {i+1}. "{col}"')
            
            self.stdout.write('')
            
            for row_idx, row in enumerate(reader):
                try:
                    # Use pipeline-processed data
                    date_str = row.get('date', '').strip()
                    occurred_at = self.parse_bandcamp_date(date_str)
                    if not occurred_at:
                        continue
                    
                    # Get amount from canonical file
                    amount_str = row.get('amount you received', '') or row.get('net amount', '')
                    amount = self.parse_decimal(amount_str)
                    total_revenue += amount
                    
                    item_name = row.get('item name', '') or ''
                    artist = row.get('artist', '') or ''
                    currency = row.get('currency', 'USD')
                    
                    RevenueEvent.objects.create(
                        source_file=source_file,
                        label=label,
                        occurred_at=occurred_at,
                        platform=platform,
                        currency=currency,
                        product_type=row.get('item type', 'digital'),
                        quantity=int(row.get('quantity', '1') or '1'),
                        gross_amount=self.parse_decimal(row.get('item total', '0')),
                        net_amount=amount,
                        net_amount_base=amount * Decimal('0.85') if currency == 'USD' else amount,
                        base_ccy='EUR',
                        track_artist_name=artist,
                        track_title=item_name,
                        row_hash=f"canonical:{row_idx}"[:64]
                    )
                    imported += 1
                    
                    if imported % 2000 == 0:
                        self.stdout.write(f'  {imported:,} records, ${float(total_revenue):,.2f} total')
                    
                except Exception as e:
                    continue
            
            self.stdout.write('')
            self.stdout.write(f'CANONICAL IMPORT RESULTS:')
            self.stdout.write(f'Records: {imported:,}')
            self.stdout.write(f'Total: ${float(total_revenue):,.2f}')
            self.stdout.write(f'Expected: ~$29,744')
            
            if float(total_revenue) > 25000:
                self.stdout.write('✓ Matches pipeline expectation!')
            else:
                self.stdout.write('⚠️  Still missing revenue - check canonical file content')

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
            cleaned = str(value_str).replace('$', '').replace('€', '').strip()
            return Decimal(cleaned) if cleaned else Decimal('0')
        except:
            return Decimal('0')
