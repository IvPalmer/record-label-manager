import csv
import hashlib
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from decimal import Decimal
from datetime import datetime
import chardet

from finances.models import Platform, DataSource, SourceFile, RevenueEvent
from api.models import Label


class Command(BaseCommand):
    help = 'Import with MINIMAL filtering to see what data we have'

    def handle(self, *args, **options):
        label = Label.objects.get(name="Tropical Twista Records")
        
        # Clear and test ONE large file
        RevenueEvent.objects.filter(label=label).delete()
        
        self.stdout.write('Testing 2023-Q2 (largest file) with minimal filtering...')
        
        platform = Platform.objects.get_or_create(name='Distribution')[0]
        datasource = DataSource.objects.get_or_create(name='test')[0]
        
        repo_root = Path(__file__).resolve().parents[4]
        test_file = repo_root / "finance/sources/tropical-twista/distribution/2023-Q2/Tropical Twista Records Q2 2023__converted.csv"
        
        source_file = SourceFile.objects.create(
            datasource=datasource,
            label=label,
            path=str(test_file),
            sha256="test",
            bytes=test_file.stat().st_size,
            mtime=timezone.now(),
            statement_type='test'
        )
        
        imported = 0
        skipped_no_data = 0
        skipped_exchange = 0
        skipped_other = 0
        
        with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row_idx, row in enumerate(reader):
                try:
                    track_artist = row.get('Track Artist', '').strip()
                    track_title = row.get('Track Title', '').strip()
                    isrc = row.get('ISRC', '').strip()
                    royalty = row.get('Royalty', '').strip()
                    
                    # Only skip exchange rates
                    if 'Exchange' in (isrc or '') or 'Exchange' in (track_title or ''):
                        skipped_exchange += 1
                        continue
                    
                    # Only skip completely empty rows
                    if not track_artist and not track_title and not isrc and not royalty:
                        skipped_no_data += 1
                        continue
                    
                    # Import everything else (including zero amounts)
                    try:
                        royalty_amount = float(royalty) if royalty else 0
                    except:
                        royalty_amount = 0
                    
                    row_hash = f"test:{row_idx}:{track_artist}:{track_title}:{isrc}"[:64]
                    
                    RevenueEvent.objects.create(
                        source_file=source_file,
                        label=label,
                        occurred_at=timezone.make_aware(datetime(2023, 4, 1)),
                        platform=platform,
                        currency='EUR',
                        product_type='test',
                        quantity=int(row.get('Qty', '0') or '0'),
                        gross_amount=Decimal(str(royalty_amount)),
                        net_amount=Decimal(str(royalty_amount)),
                        net_amount_base=Decimal(str(royalty_amount)),
                        base_ccy='EUR',
                        track_artist_name=track_artist or 'Unknown',
                        track_title=track_title or 'Unknown',
                        catalog_number=row.get('Catalog', ''),
                        isrc=isrc,
                        row_hash=row_hash
                    )
                    imported += 1
                    
                    if imported % 10000 == 0:
                        self.stdout.write(f'  Imported {imported:,} records...')
                    
                except Exception as e:
                    skipped_other += 1
                    continue
        
        self.stdout.write('')
        self.stdout.write(f'MINIMAL FILTER RESULTS:')
        self.stdout.write(f'  Imported: {imported:,}')
        self.stdout.write(f'  Skipped (no data): {skipped_no_data:,}')
        self.stdout.write(f'  Skipped (exchange): {skipped_exchange:,}')
        self.stdout.write(f'  Skipped (errors): {skipped_other:,}')
        self.stdout.write(f'  Total processed: {imported + skipped_no_data + skipped_exchange + skipped_other:,}')

    def parse_decimal(self, value_str):
        if not value_str:
            return Decimal('0')
        try:
            cleaned = str(value_str).replace('$', '').replace('€', '').strip()
            return Decimal(cleaned) if cleaned else Decimal('0')
        except:
            return Decimal('0')
