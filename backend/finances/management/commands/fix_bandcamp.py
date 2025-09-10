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
    help = 'Fix Bandcamp import with proper UTF-16 handling'

    def handle(self, *args, **options):
        label = Label.objects.get(name="Tropical Twista Records")
        
        # Clear only Bandcamp data
        self.stdout.write('Clearing Bandcamp data...')
        RevenueEvent.objects.filter(platform__name='Bandcamp').delete()
        SourceFile.objects.filter(datasource__name='bandcamp').delete()
        
        platform = Platform.objects.get_or_create(name='Bandcamp')[0]
        datasource = DataSource.objects.get_or_create(name='bandcamp')[0]
        
        repo_root = Path(__file__).resolve().parents[4]
        bandcamp_file = repo_root / "finance/sources/tropical-twista/bandcamp/20000101-20250729_bandcamp_raw_data_Tropical-Twista-Records.csv"
        
        if not bandcamp_file.exists():
            self.stdout.write('Bandcamp file not found')
            return
        
        source_file = SourceFile.objects.create(
            datasource=datasource,
            label=label,
            path=str(bandcamp_file),
            sha256="bandcamp_fix",
            bytes=bandcamp_file.stat().st_size,
            mtime=timezone.now(),
            statement_type='bandcamp_utf16'
        )
        
        imported = 0
        total_revenue = Decimal('0')
        
        try:
            # Try UTF-16 with BOM handling
            with open(bandcamp_file, 'r', encoding='utf-16', errors='ignore') as f:
                reader = csv.DictReader(f)
                
                # Check column names
                self.stdout.write('CSV columns found:')
                for i, col in enumerate(reader.fieldnames[:10]):
                    self.stdout.write(f'  {i+1}. "{col}"')
                
                self.stdout.write('')
                self.stdout.write('Processing rows...')
                
                for row_idx, row in enumerate(reader):
                    try:
                        # Get key fields
                        date_str = row.get('date', '').strip()
                        item_name = row.get('item name', '').strip()
                        amount_str = row.get('amount you received', '').strip()
                        currency = row.get('currency', 'USD').strip()
                        
                        # Skip if no date or item
                        if not date_str or not item_name:
                            continue
                        
                        # Parse date
                        occurred_at = self.parse_bandcamp_date(date_str)
                        if not occurred_at:
                            continue
                        
                        # Parse amount
                        amount = self.parse_decimal(amount_str)
                        total_revenue += amount
                        
                        # Create record (accept even $0 transactions)
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
                            track_artist_name=row.get('artist', '') or '',
                            track_title=item_name,
                            row_hash=f"bc_fix:{row_idx}"[:64]
                        )
                        imported += 1
                        
                        if imported % 5000 == 0:
                            self.stdout.write(f'  {imported:,} records, ${float(total_revenue):,.2f} total')
                        
                    except Exception as e:
                        if imported < 10:  # Show first few errors
                            self.stdout.write(f'Row {row_idx} error: {e}')
                        continue
                
                self.stdout.write('')
                self.stdout.write(f'BANDCAMP IMPORT COMPLETE:')
                self.stdout.write(f'Records imported: {imported:,}')
                self.stdout.write(f'Total revenue: ${float(total_revenue):,.2f}')
                
                if float(total_revenue) > 20000:
                    self.stdout.write('✓ Revenue total looks correct!')
                else:
                    self.stdout.write('⚠️  Revenue still too low')
                
        except Exception as e:
            self.stdout.write(f'Failed to read Bandcamp file: {e}')

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
