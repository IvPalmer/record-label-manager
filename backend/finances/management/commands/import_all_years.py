import csv
import hashlib
import chardet
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from decimal import Decimal
from datetime import datetime
import re

from finances.models import Platform, DataSource, SourceFile, RevenueEvent, ImportBatch
from api.models import Label


class Command(BaseCommand):
    help = 'Import ALL years (2015-2025) with format-aware validation'

    def add_arguments(self, parser):
        parser.add_argument('--label', type=str, required=True, help='Label name')

    def handle(self, *args, **options):
        label_name = options['label']
        
        try:
            label = Label.objects.get(name=label_name)
        except Label.DoesNotExist:
            raise CommandError(f'Label "{label_name}" does not exist.')
        
        self.stdout.write('Importing ALL years with format-specific validation...')
        RevenueEvent.objects.filter(label=label).delete()
        SourceFile.objects.filter(label=label).delete()
        
        self.setup_platforms()
        batch = ImportBatch.objects.create(label=label)
        
        repo_root = Path(__file__).resolve().parents[4]
        sources_root = repo_root / "finance" / "sources" / "tropical-twista"
        
        total_imported = 0
        
        try:
            # Import Bandcamp FIRST (2015-2025)
            bandcamp_file = sources_root / "bandcamp" / "20000101-20250729_bandcamp_raw_data_Tropical-Twista-Records.csv"
            if bandcamp_file.exists():
                imported = self.import_bandcamp_all_years(label, bandcamp_file)
                total_imported += imported
                self.stdout.write(f'Bandcamp (2015-2025): {imported:,} records')
            
            # Import Distribution files with format detection
            distribution_dir = sources_root / "distribution"
            for quarter_dir in sorted(distribution_dir.iterdir()):
                if quarter_dir.is_dir():
                    for csv_file in quarter_dir.glob("*.csv"):
                        if '.backup.csv' in csv_file.name:
                            continue
                        imported = self.import_distribution_format_aware(label, csv_file, quarter_dir.name)
                        total_imported += imported
                        if imported > 0:
                            self.stdout.write(f'{quarter_dir.name}: {imported:,} records')
            
            batch.finished_at = timezone.now()
            batch.save()
            
            self.stdout.write('')
            self.stdout.write(f'TOTAL ALL YEARS: {total_imported:,} records')
            
        except Exception as e:
            batch.status = 'failed'
            batch.finished_at = timezone.now()
            batch.save()
            raise CommandError(f'Import failed: {e}')

    def setup_platforms(self):
        Platform.objects.get_or_create(name='Distribution', defaults={'vendor_key': 'distribution'})
        Platform.objects.get_or_create(name='Bandcamp', defaults={'vendor_key': 'bandcamp'})
        DataSource.objects.get_or_create(name='zebralution', defaults={'vendor': 'Zebralution'})
        DataSource.objects.get_or_create(name='labelworx', defaults={'vendor': 'Labelworx'})
        DataSource.objects.get_or_create(name='bandcamp', defaults={'vendor': 'Bandcamp'})

    def import_bandcamp_all_years(self, label, csv_file):
        """Import all Bandcamp data (2015-2025)"""
        # Bandcamp files are UTF-16 encoded with BOM
        encoding = 'utf-16'
        
        platform = Platform.objects.get(name='Bandcamp')
        datasource = DataSource.objects.get(name='bandcamp')
        
        source_file = SourceFile.objects.create(
            datasource=datasource,
            label=label,
            path=str(csv_file.relative_to(csv_file.parents[4])),
            sha256=self.compute_hash(csv_file),
            bytes=csv_file.stat().st_size,
            mtime=timezone.make_aware(datetime.fromtimestamp(csv_file.stat().st_mtime)),
            statement_type='bandcamp'
        )
        
        imported = 0
        
        with open(csv_file, 'r', encoding=encoding, errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row_idx, row in enumerate(reader):
                try:
                    # Basic validation: must have date and item
                    date_str = row.get('date', '').strip()
                    item_name = row.get('item name', '').strip()
                    
                    if not date_str or not item_name:
                        continue
                    
                    # Skip admin rows
                    if 'payout' in item_name.lower() or 'payment' in item_name.lower():
                        continue
                    
                    occurred_at = self.parse_bandcamp_date(date_str)
                    if not occurred_at:
                        continue
                    
                    net_amount = self.parse_decimal(row.get('amount you received', '0'))
                    currency = row.get('currency', 'USD')
                    
                    # Fix USD to EUR conversion (use proper rate)
                    if currency == 'USD':
                        net_amount_eur = net_amount * Decimal('0.85')  # ~0.85 USD to EUR
                    else:
                        net_amount_eur = net_amount
                    
                    RevenueEvent.objects.create(
                        source_file=source_file,
                        label=label,
                        occurred_at=occurred_at,
                        platform=platform,
                        currency=currency,
                        product_type=row.get('item type', 'digital'),
                        quantity=int(row.get('quantity', '1') or '1'),
                        gross_amount=self.parse_decimal(row.get('item total', '0')),
                        net_amount=net_amount,
                        net_amount_base=net_amount_eur,
                        base_ccy='EUR',
                        track_artist_name=row.get('artist', '') or '',
                        track_title=row.get('item name', '') or '',
                        row_hash=f"bc_all:{row_idx}:{date_str}"[:64]
                    )
                    imported += 1
                    
                    if imported % 5000 == 0:
                        self.stdout.write(f'  Bandcamp: {imported:,} records...')
                        
                except Exception:
                    continue
        
        return imported

    def import_distribution_format_aware(self, label, csv_file, period):
        """Import distribution with format-specific validation"""
        year, quarter = self.parse_period(period)
        if not year or not quarter:
            return 0
        
        file_format = self.detect_format(csv_file)
        encoding = self.detect_encoding(csv_file)
        
        if file_format == 'zebralution':
            return self.import_zebralution_permissive(label, csv_file, year, quarter)
        else:
            return self.import_labelworx_clean(label, csv_file, year, quarter)

    def import_zebralution_permissive(self, label, csv_file, year, quarter):
        """Import Zebralution with permissive validation for older data"""
        platform = Platform.objects.get(name='Distribution')
        datasource = DataSource.objects.get(name='zebralution')
        
        source_file = SourceFile.objects.create(
            datasource=datasource,
            label=label,
            path=str(csv_file.relative_to(csv_file.parents[4])),
            sha256=self.compute_hash(csv_file),
            bytes=csv_file.stat().st_size,
            mtime=timezone.make_aware(datetime.fromtimestamp(csv_file.stat().st_mtime)),
            statement_type='zebralution'
        )
        
        imported = 0
        encoding = self.detect_encoding(csv_file)
        
        with open(csv_file, 'r', encoding=encoding, errors='ignore') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            for row_idx, row in enumerate(reader):
                try:
                    artist = (row.get('Artist', '') or '').strip()
                    title = (row.get('Title', '') or '').strip()
                    period = (row.get('Period', '') or '').strip()
                    
                    # Permissive: just need artist OR title
                    if not artist and not title:
                        continue
                    
                    # Skip obvious summaries only
                    if 'total' in artist.lower() or 'sum' in title.lower():
                        continue
                    
                    revenue_net = self.parse_european_decimal(row.get('Rev.less Publ.EUR', '0'))
                    
                    RevenueEvent.objects.create(
                        source_file=source_file,
                        label=label,
                        occurred_at=timezone.make_aware(datetime(year, (quarter-1)*3+1, 1)),
                        platform=platform,
                        currency='EUR',
                        product_type='stream',
                        quantity=int(row.get('Sales', '0') or '0'),
                        gross_amount=self.parse_european_decimal(row.get('Revenue-EUR', '0')),
                        net_amount=revenue_net,
                        net_amount_base=revenue_net,
                        base_ccy='EUR',
                        track_artist_name=artist or 'Unknown',
                        track_title=title or 'Unknown',
                        catalog_number=row.get('Label Order-Nr', '') or '',
                        isrc=row.get('ISRC', '') or '',
                        row_hash=f"zeb_perm:{source_file.id}:{row_idx}"[:64]
                    )
                    imported += 1
                    
                except Exception:
                    continue
        
        return imported

    def import_labelworx_clean(self, label, csv_file, year, quarter):
        """Import Labelworx with strict validation"""
        platform = Platform.objects.get(name='Distribution')
        datasource = DataSource.objects.get(name='labelworx')
        
        source_file = SourceFile.objects.create(
            datasource=datasource,
            label=label,
            path=str(csv_file.relative_to(csv_file.parents[4])),
            sha256=self.compute_hash(csv_file),
            bytes=csv_file.stat().st_size,
            mtime=timezone.make_aware(datetime.fromtimestamp(csv_file.stat().st_mtime)),
            statement_type='labelworx'
        )
        
        imported = 0
        
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row_idx, row in enumerate(reader):
                try:
                    track_artist = (row.get('Track Artist', '') or '').strip()
                    track_title = (row.get('Track Title', '') or '').strip()
                    sale_type = (row.get('Sale Type', '') or '').strip()
                    isrc = (row.get('ISRC', '') or '').strip()
                    
                    # Only Track transactions with artist/title
                    if sale_type != 'Track' or not track_artist or not track_title:
                        continue
                    
                    # Skip exchange rates
                    if 'Exchange' in (isrc or '') or 'exchange' in track_title.lower():
                        continue
                    
                    royalty = self.parse_decimal(row.get('Royalty', '0'))
                    
                    RevenueEvent.objects.create(
                        source_file=source_file,
                        label=label,
                        occurred_at=timezone.make_aware(datetime(year, (quarter-1)*3+1, 1)),
                        platform=platform,
                        currency='EUR',
                        product_type='stream',
                        quantity=int(row.get('Qty', '0') or '0'),
                        gross_amount=self.parse_decimal(row.get('Value', '0')),
                        net_amount=royalty,
                        net_amount_base=royalty,
                        base_ccy='EUR',
                        track_artist_name=track_artist,
                        track_title=track_title,
                        catalog_number=row.get('Catalog', '') or '',
                        isrc=isrc,
                        row_hash=f"lbx_clean:{source_file.id}:{row_idx}"[:64]
                    )
                    imported += 1
                    
                except Exception:
                    continue
        
        return imported

    def detect_format(self, csv_file):
        try:
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline()
                if ';' in first_line and 'Period' in first_line:
                    return 'zebralution'
        except:
            pass
        return 'labelworx'

    def detect_encoding(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(200000)
            result = chardet.detect(raw_data)
            return result.get('encoding', 'utf-8') or 'utf-8'
        except:
            return 'utf-8'

    def parse_period(self, period_str):
        match = re.search(r'(20\d{2}).*Q([1-4])', period_str)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None

    def parse_european_decimal(self, value_str):
        if not value_str:
            return Decimal('0')
        try:
            cleaned = str(value_str).strip().replace(',', '.')
            return Decimal(cleaned) if cleaned else Decimal('0')
        except:
            return Decimal('0')

    def parse_decimal(self, value_str):
        if not value_str:
            return Decimal('0')
        try:
            cleaned = str(value_str).replace('$', '').replace('€', '').strip()
            return Decimal(cleaned) if cleaned else Decimal('0')
        except:
            return Decimal('0')

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

    def compute_hash(self, file_path):
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024*1024), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
