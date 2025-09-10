import csv
import hashlib
import re
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date

from finances.models import Platform, Store, Country, DataSource, SourceFile, RevenueEvent, ImportBatch
from api.models import Label


class Command(BaseCommand):
    help = 'Import ALL rows from ALL CSV files with proper format detection'

    def add_arguments(self, parser):
        parser.add_argument('--label', type=str, required=True, help='Label name')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be imported without saving')

    def handle(self, *args, **options):
        label_name = options['label']
        dry_run = options.get('dry_run', False)
        
        try:
            label = Label.objects.get(name=label_name)
        except Label.DoesNotExist:
            raise CommandError(f'Label "{label_name}" does not exist.')
        
        if not dry_run:
            self.stdout.write('Clearing existing data...')
            RevenueEvent.objects.filter(label=label).delete()
            SourceFile.objects.filter(label=label).delete()
        
        self.setup_reference_data()
        
        repo_root = Path(__file__).resolve().parents[4]
        sources_root = repo_root / "finance" / "sources" / "tropical-twista"
        
        batch = ImportBatch.objects.create(label=label) if not dry_run else None
        if batch:
            self.stdout.write(f'Created import batch #{batch.id}')
        
        total_imported = 0
        total_expected = 0
        
        try:
            # Import Bandcamp data
            bandcamp_file = sources_root / "bandcamp" / "20000101-20250729_bandcamp_raw_data_Tropical-Twista-Records.csv"
            if bandcamp_file.exists():
                expected, imported = self.import_bandcamp(label, bandcamp_file, dry_run)
                total_expected += expected
                total_imported += imported
                self.stdout.write(f'Bandcamp: {imported}/{expected} records')
            
            # Import Distribution data (detect format)
            distribution_dir = sources_root / "distribution"
            for quarter_dir in sorted(distribution_dir.iterdir()):
                if quarter_dir.is_dir():
                    for csv_file in quarter_dir.glob("*.csv"):
                        expected, imported = self.import_distribution_file(label, csv_file, quarter_dir.name, dry_run)
                        total_expected += expected  
                        total_imported += imported
                        self.stdout.write(f'{quarter_dir.name}: {imported}/{expected} records from {csv_file.name}')
            
            if batch and not dry_run:
                batch.finished_at = timezone.now()
                batch.save()
            
            self.stdout.write('')
            self.stdout.write(f'TOTAL: {total_imported}/{total_expected} records imported')
            completion_rate = (total_imported / total_expected * 100) if total_expected > 0 else 0
            self.stdout.write(f'Completion rate: {completion_rate:.1f}%')
            
        except Exception as e:
            if batch and not dry_run:
                batch.status = 'failed'
                batch.finished_at = timezone.now()
                batch.save()
            raise CommandError(f'Import failed: {e}')

    def setup_reference_data(self):
        Platform.objects.get_or_create(name='Bandcamp', defaults={'vendor_key': 'bandcamp'})
        Platform.objects.get_or_create(name='Distribution', defaults={'vendor_key': 'distribution'})
        DataSource.objects.get_or_create(name='bandcamp', defaults={'vendor': 'Bandcamp'})
        DataSource.objects.get_or_create(name='zebralution', defaults={'vendor': 'Zebralution'})
        DataSource.objects.get_or_create(name='labelworx', defaults={'vendor': 'Labelworx'})

    def detect_file_format(self, csv_file):
        """Detect if file is Zebralution or Labelworx format"""
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            first_line = f.readline()
            
            # Zebralution uses semicolons and has "Period" column
            if ';' in first_line and 'Period' in first_line:
                return 'zebralution'
            # Labelworx uses commas and has "Label Name" column  
            elif ',' in first_line and 'Label Name' in first_line:
                return 'labelworx'
            else:
                return 'unknown'

    def parse_period_from_filename(self, filename):
        """Extract year and quarter from filename"""
        # Match patterns like 2024-Q4, Q4-2024, etc.
        match = re.search(r'(20\d{2})[-_]?Q([1-4])|Q([1-4])[-_]?(20\d{2})', filename, re.IGNORECASE)
        if match:
            year = int(match.group(1) or match.group(4))
            quarter = int(match.group(2) or match.group(3))
            return year, quarter
        return None, None

    def import_bandcamp(self, label, csv_file, dry_run=False):
        """Import Bandcamp data"""
        expected_rows = sum(1 for _ in open(csv_file, 'r', encoding='utf-8', errors='ignore')) - 1
        imported_rows = 0
        
        if dry_run:
            return expected_rows, expected_rows
        
        platform = Platform.objects.get(name='Bandcamp')
        datasource = DataSource.objects.get(name='bandcamp')
        
        source_file = SourceFile.objects.create(
            datasource=datasource,
            label=label,
            path=str(csv_file.relative_to(csv_file.parents[4])),
            sha256=self.compute_file_hash(csv_file),
            bytes=csv_file.stat().st_size,
            mtime=timezone.make_aware(datetime.fromtimestamp(csv_file.stat().st_mtime)),
            statement_type='bandcamp'
        )
        
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row_idx, row in enumerate(reader):
                try:
                    # Parse date - check actual column name
                    date_str = row.get('date', '').strip()
                    if not date_str:
                        continue
                        
                    occurred_at = self.parse_bandcamp_date(date_str)
                    if not occurred_at:
                        continue
                    
                    # Parse amounts - use exact column names from file
                    net_amount = self.parse_decimal(row.get('amount you received', '0'))
                    gross_amount = self.parse_decimal(row.get('item total', '0'))
                    
                    # Skip only if both are missing/negative
                    if net_amount < 0 and gross_amount < 0:
                        continue
                    
                    row_hash = hashlib.sha256(
                        f"bandcamp:{row_idx}:{date_str}:{net_amount}:{row.get('item name', '')}".encode()
                    ).hexdigest()[:64]
                    
                    RevenueEvent.objects.create(
                        source_file=source_file,
                        label=label,
                        occurred_at=occurred_at,
                        platform=platform,
                        currency=row.get('currency', 'USD'),
                        product_type=row.get('item type', 'digital'),
                        quantity=int(row.get('quantity', '1') or '1'),
                        gross_amount=self.parse_decimal(row.get('item total', '0')),
                        net_amount=net_amount,
                        net_amount_base=net_amount,
                        base_ccy=row.get('currency', 'USD'),
                        track_artist_name=row.get('artist', ''),
                        track_title=row.get('item name', ''),
                        row_hash=row_hash
                    )
                    imported_rows += 1
                    
                except Exception as e:
                    continue
        
        return expected_rows, imported_rows

    def import_distribution_file(self, label, csv_file, period_folder, dry_run=False):
        """Import distribution file with format detection"""
        file_format = self.detect_file_format(csv_file)
        year, quarter = self.parse_period_from_filename(period_folder)
        
        if not year or not quarter:
            self.stdout.write(f'Could not parse period from {period_folder}')
            return 0, 0
        
        if file_format == 'zebralution':
            return self.import_zebralution_file(label, csv_file, year, quarter, dry_run)
        elif file_format == 'labelworx':
            return self.import_labelworx_file(label, csv_file, year, quarter, dry_run)
        else:
            self.stdout.write(f'Unknown format: {csv_file.name}')
            return 0, 0

    def import_zebralution_file(self, label, csv_file, year, quarter, dry_run=False):
        """Import Zebralution format (semicolon delimited)"""
        expected_rows = sum(1 for _ in open(csv_file, 'r', encoding='utf-8', errors='ignore')) - 1
        imported_rows = 0
        
        if dry_run:
            return expected_rows, expected_rows
        
        platform = Platform.objects.get(name='Distribution')
        datasource = DataSource.objects.get(name='zebralution')
        
        source_file = SourceFile.objects.create(
            datasource=datasource,
            label=label,
            path=str(csv_file.relative_to(csv_file.parents[4])),
            sha256=self.compute_file_hash(csv_file),
            bytes=csv_file.stat().st_size,
            mtime=timezone.make_aware(datetime.fromtimestamp(csv_file.stat().st_mtime)),
            statement_type='zebralution',
            period_start=date(year, (quarter-1)*3+1, 1)
        )
        
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            for row_idx, row in enumerate(reader):
                try:
                    artist = row.get('Artist', '').strip()
                    title = row.get('Title', '').strip()
                    isrc = row.get('ISRC', '').strip()
                    
                    if not artist or not title:
                        continue
                    
                    # Parse European format numbers (comma as decimal)
                    sales = int(row.get('Sales', '0') or '0')
                    revenue_net = self.parse_european_decimal(row.get('Rev.less Publ.EUR', '0'))
                    
                    if revenue_net <= 0:
                        continue
                    
                    row_hash = hashlib.sha256(
                        f"zebralution:{source_file.id}:{row_idx}:{artist}:{title}:{isrc}".encode()
                    ).hexdigest()[:64]
                    
                    # Determine store name
                    store_name = row.get('Shop', '').strip() or row.get('Provider', '').strip()
                    store_obj = None
                    if store_name:
                        store_obj, _ = Store.objects.get_or_create(platform=platform, name=store_name)

                    RevenueEvent.objects.create(
                        source_file=source_file,
                        label=label,
                        occurred_at=timezone.make_aware(datetime(year, (quarter-1)*3+1, 1)),
                        platform=platform,
                        store=store_obj,
                        currency='EUR',
                        product_type='digital',
                        quantity=sales,
                        gross_amount=self.parse_european_decimal(row.get('Revenue-EUR', '0')),
                        net_amount=revenue_net,
                        net_amount_base=revenue_net,
                        base_ccy='EUR',
                        track_artist_name=artist,
                        track_title=title,
                        catalog_number=row.get('Label Order-Nr', ''),
                        isrc=isrc,
                        row_hash=row_hash
                    )
                    imported_rows += 1
                    
                except Exception as e:
                    continue
        
        return expected_rows, imported_rows

    def import_labelworx_file(self, label, csv_file, year, quarter, dry_run=False):
        """Import Labelworx format (comma delimited)"""
        expected_rows = sum(1 for _ in open(csv_file, 'r', encoding='utf-8', errors='ignore')) - 1
        imported_rows = 0
        
        if dry_run:
            return expected_rows, expected_rows
        
        platform = Platform.objects.get(name='Distribution')
        datasource = DataSource.objects.get(name='labelworx')
        
        source_file = SourceFile.objects.create(
            datasource=datasource,
            label=label,
            path=str(csv_file.relative_to(csv_file.parents[4])),
            sha256=self.compute_file_hash(csv_file),
            bytes=csv_file.stat().st_size,
            mtime=timezone.make_aware(datetime.fromtimestamp(csv_file.stat().st_mtime)),
            statement_type='labelworx',
            period_start=date(year, (quarter-1)*3+1, 1)
        )
        
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row_idx, row in enumerate(reader):
                try:
                    # Import Track rows (be less strict)
                    sale_type = row.get('Sale Type', '').strip()
                    track_artist = row.get('Track Artist', '').strip()
                    track_title = row.get('Track Title', '').strip()
                    isrc = row.get('ISRC', '').strip()
                    
                    # Only skip if clearly not a track or has exchange rate data
                    if (sale_type and sale_type != 'Track') or 'Exchange' in (isrc or ''):
                        continue
                    
                    # Skip only if completely empty
                    if not track_artist and not track_title and not isrc:
                        continue
                    
                    # Parse English format numbers
                    qty = int(row.get('Qty', '0') or '0')
                    royalty = self.parse_decimal(row.get('Royalty', '0'))
                    
                    # Accept zero royalty (might be valid $0 transactions or promotional streams)
                    if royalty < 0:  # Only skip negative amounts
                        continue
                    
                    row_hash = hashlib.sha256(
                        f"labelworx:{source_file.id}:{row_idx}:{track_artist}:{track_title}:{isrc}".encode()
                    ).hexdigest()[:64]
                    
                    # Determine store name (canonicalize common variants)
                    store_name = (row.get('Store Name', '') or '').strip()
                    lower = store_name.lower()
                    if 'youtube' in lower:
                        store_name = 'YouTube'
                    elif 'apple music' in lower or 'itunes' in lower:
                        store_name = 'Apple Music'
                    elif 'spotify' in lower:
                        store_name = 'Spotify'
                    elif 'tiktok' in lower:
                        store_name = 'TikTok'
                    elif 'tidal' in lower:
                        store_name = 'TIDAL'
                    elif 'beatport' in lower:
                        store_name = 'Beatport'
                    
                    store_obj = None
                    if store_name:
                        store_obj, _ = Store.objects.get_or_create(platform=platform, name=store_name)

                    RevenueEvent.objects.create(
                        source_file=source_file,
                        label=label,
                        occurred_at=timezone.make_aware(datetime(year, (quarter-1)*3+1, 1)),
                        platform=platform,
                        store=store_obj,
                        currency='EUR',
                        product_type=row.get('Format', 'digital'),
                        quantity=qty,
                        gross_amount=self.parse_decimal(row.get('Value', '0')),
                        net_amount=royalty,
                        net_amount_base=royalty,
                        base_ccy='EUR',
                        track_artist_name=track_artist,
                        track_title=track_title,
                        catalog_number=row.get('Catalog', ''),
                        isrc=isrc,
                        row_hash=row_hash
                    )
                    imported_rows += 1
                    
                except Exception as e:
                    continue
        
        return expected_rows, imported_rows

    def parse_european_decimal(self, value_str):
        """Parse European format: 1,234 = 1.234"""
        if not value_str:
            return Decimal('0')
        cleaned = str(value_str).strip().replace(',', '.')
        try:
            return Decimal(cleaned)
        except:
            return Decimal('0')

    def parse_decimal(self, value_str):
        """Parse English format decimal"""
        if not value_str:
            return Decimal('0')
        cleaned = str(value_str).replace('$', '').replace('€', '').strip()
        try:
            return Decimal(cleaned)
        except:
            return Decimal('0')

    def parse_bandcamp_date(self, date_str):
        """Parse Bandcamp date format"""
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

    def compute_file_hash(self, file_path):
        """Compute SHA256 of file"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024*1024), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
