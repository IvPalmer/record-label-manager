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
    help = 'Final Bandcamp import - only music sales, allow blank artists for valid sales'

    def handle(self, *args, **options):
        label = Label.objects.get(name="Tropical Twista Records")
        
        # Clear only Bandcamp
        self.stdout.write('Clearing Bandcamp data...')
        RevenueEvent.objects.filter(platform__name='Bandcamp').delete()
        
        platform = Platform.objects.get_or_create(name='Bandcamp')[0]
        datasource = DataSource.objects.get_or_create(name='bandcamp_final')[0]
        
        repo_root = Path(__file__).resolve().parents[4]
        canonical_file = repo_root / "finance/sources/tropical-twista/bandcamp/canonical/bandcamp_all.csv"
        
        source_file = SourceFile.objects.create(
            datasource=datasource,
            label=label,
            path=str(canonical_file),
            sha256="final",
            bytes=canonical_file.stat().st_size,
            mtime=timezone.now(),
            statement_type='bandcamp_final'
        )
        
        imported = 0
        total_revenue = Decimal('0')
        skipped_non_music = 0
        skipped_no_date = 0
        skipped_no_item = 0
        
        with open(canonical_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_idx, row in enumerate(reader):
                try:
                    date_str = row.get('date', '').strip()
                    item_name = row.get('item name', '').strip()
                    item_type = row.get('item type', '').strip()
                    amount_str = row.get('amount you received', '').strip()
                    currency = row.get('currency', 'USD')
                    artist = row.get('artist', '').strip()
                    
                    # Must have date
                    if not date_str:
                        skipped_no_date += 1
                        continue
                    
                    # Must have item name
                    if not item_name:
                        skipped_no_item += 1
                        continue
                    
                    # ONLY music items (allow blank artist for some sales)
                    if item_type.lower() not in ['album', 'track']:
                        skipped_non_music += 1
                        continue
                    
                    # Skip obvious non-music
                    if any(word in item_name.lower() for word in ['payout', 'payment', 'refund', 'shipping']):
                        skipped_non_music += 1
                        continue
                    
                    occurred_at = self.parse_bandcamp_date(date_str)
                    if not occurred_at:
                        continue
                    
                    amount = self.parse_decimal(amount_str)
                    total_revenue += amount
                    
                    # Import ALL valid music sales (even with blank artist or $0 amount)
                    RevenueEvent.objects.create(
                        source_file=source_file,
                        label=label,
                        occurred_at=occurred_at,
                        platform=platform,
                        currency=currency,
                        product_type=item_type,
                        quantity=int(row.get('quantity', '1') or '1'),
                        gross_amount=self.parse_decimal(row.get('item total', '0')),
                        net_amount=amount,
                        net_amount_base=amount * Decimal('0.85') if currency == 'USD' else amount,
                        base_ccy='EUR',
                        track_artist_name=artist or 'Various Artists',  # Fill blank artists
                        track_title=item_name,
                        row_hash=f"final:{row_idx}"[:64]
                    )
                    imported += 1
                    
                    if imported % 2000 == 0:
                        self.stdout.write(f'  {imported:,} records, ${float(total_revenue):,.2f} total')
                    
                except Exception:
                    continue
            
            self.stdout.write('')
            self.stdout.write(f'FINAL BANDCAMP IMPORT:')
            self.stdout.write(f'Imported: {imported:,} records')
            self.stdout.write(f'Total: ${float(total_revenue):,.2f}')
            self.stdout.write(f'Skipped non-music: {skipped_non_music:,}')
            self.stdout.write(f'Skipped no date: {skipped_no_date:,}')
            self.stdout.write(f'Skipped no item: {skipped_no_item:,}')

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
