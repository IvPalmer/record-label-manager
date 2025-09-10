import csv
import hashlib
import re
import chardet
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from datetime import datetime, date

from finances.models import Platform, Store, Country, DataSource, SourceFile, RevenueEvent, ImportBatch
from api.models import Label


class Command(BaseCommand):
    help = 'Import ALL detailed finance data from source CSV files'

    def add_arguments(self, parser):
        parser.add_argument('--label', type=str, required=True, help='Label name')
        parser.add_argument('--limit', type=int, help='Limit records for testing (optional)')

    def handle(self, *args, **options):
        label_name = options['label']
        limit = options.get('limit')
        
        # Get label
        try:
            label = Label.objects.get(name=label_name)
        except Label.DoesNotExist:
            raise CommandError(f'Label "{label_name}" does not exist.')
        
        # Setup reference data
        self.setup_reference_data()
        
        # Clear existing data
        self.stdout.write('Clearing existing finance data...')
        RevenueEvent.objects.filter(label=label).delete()
        SourceFile.objects.filter(label=label).delete()
        
        batch = ImportBatch.objects.create(label=label)
        self.stdout.write(f'Created import batch #{batch.id} for {label.name}')
        
        repo_root = Path(__file__).resolve().parents[4]
        sources_root = repo_root / "finance" / "sources" / "tropical-twista"
        
        total_records = 0
        
        try:
            # Import detailed Bandcamp data
            bandcamp_file = sources_root / "bandcamp" / "20000101-20250729_bandcamp_raw_data_Tropical-Twista-Records.csv"
            if bandcamp_file.exists():
                records = self.import_bandcamp_detailed(label, bandcamp_file, limit)
                total_records += records
                self.stdout.write(f'Imported {records} Bandcamp transactions')
            
            # Import detailed distribution data by quarter
            distribution_dir = sources_root / "distribution"
            for quarter_dir in sorted(distribution_dir.iterdir()):
                if quarter_dir.is_dir() and quarter_dir.name not in ['canonical', 'docs', 'raw']:
                    # Find the main CSV file for this quarter
                    csv_files = list(quarter_dir.rglob("*__converted.csv"))
                    if not csv_files:
                        csv_files = list(quarter_dir.rglob("*.csv"))
                    
                    main_file = None
                    for csv_file in csv_files:
                        # Skip cost files, prefer revenue files
                        if 'cost' in csv_file.name.lower() or 'tk_' in csv_file.name.lower():
                            continue
                        if '_rs_' in csv_file.name.lower() or 'revenue' in csv_file.name.lower() or '__converted' in csv_file.name:
                            main_file = csv_file
                            break
                    
                    if main_file:
                        records = self.import_distribution_detailed(label, main_file, quarter_dir.name, limit)
                        total_records += records
                        if records > 0:
                            self.stdout.write(f'Imported {records} records from {quarter_dir.name}')
            
            batch.finished_at = timezone.now()
            batch.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully imported {total_records} detailed records for {label.name}')
            )
            
        except Exception as e:
            batch.status = 'failed'
            batch.finished_at = timezone.now()
            batch.save()
            raise CommandError(f'Import failed: {e}')

    def setup_reference_data(self):
        """Create basic reference data"""
        Platform.objects.get_or_create(name='Bandcamp', defaults={'vendor_key': 'bandcamp'})
        Platform.objects.get_or_create(name='Distribution', defaults={'vendor_key': 'distribution'})
        
        DataSource.objects.get_or_create(name='bandcamp_detailed', defaults={'vendor': 'Bandcamp'})
        DataSource.objects.get_or_create(name='distribution_detailed', defaults={'vendor': 'Zebralution'})

    def import_bandcamp_detailed(self, label, csv_file, limit=None):
        """Import detailed Bandcamp transactions"""
        platform = Platform.objects.get(name='Bandcamp')
        datasource = DataSource.objects.get(name='bandcamp_detailed')
        
        # Create source file record
        source_file = SourceFile.objects.create(
            datasource=datasource,
            label=label,
            path=str(csv_file.relative_to(csv_file.parents[4])),
            sha256=self.compute_file_hash(csv_file),
            bytes=csv_file.stat().st_size,
            mtime=timezone.make_aware(datetime.fromtimestamp(csv_file.stat().st_mtime)),
            statement_type='bandcamp_detailed'
        )
        
        records_count = 0
        
        # Detect encoding
        with open(csv_file, 'rb') as f:
            raw_data = f.read(200000)
            encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
        
        with open(csv_file, 'r', encoding=encoding, errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row_idx, row in enumerate(reader):
                if limit and records_count >= limit:
                    break
                    
                try:
                    # Parse date - Bandcamp format: "M/D/YY H:MMam" or "M/D/YYYY H:MMam"
                    date_str = row.get('date', '').strip()
                    if not date_str:
                        continue
                    
                    # Parse date
                    occurred_at = self.parse_bandcamp_date(date_str)
                    if not occurred_at:
                        continue
                    
                    # Parse amounts
                    net_amount = self.parse_decimal(row.get('amount you received', '0'))
                    gross_amount = self.parse_decimal(row.get('item total', '0'))
                    quantity = int(row.get('quantity', '0') or '0')
                    
                    if net_amount <= 0 and gross_amount <= 0:
                        continue  # Skip zero transactions
                    
                    # Create row hash
                    row_hash = hashlib.sha256(
                        f"{source_file.id}:{row_idx}:{date_str}:{net_amount}:{row.get('item name', '')}".encode()
                    ).hexdigest()[:64]
                    
                    RevenueEvent.objects.create(
                        source_file=source_file,
                        label=label,
                        occurred_at=occurred_at,
                        platform=platform,
                        currency=row.get('currency', 'USD'),
                        product_type=row.get('item type', 'digital'),
                        quantity=quantity,
                        gross_amount=gross_amount,
                        net_amount=net_amount,
                        net_amount_base=net_amount * Decimal('0.85') if row.get('currency') == 'USD' else net_amount,
                        base_ccy='EUR',
                        track_artist_name=row.get('artist', ''),
                        track_title=row.get('item name', ''),
                        catalog_number='',  # Bandcamp doesn't have catalog numbers
                        row_hash=row_hash
                    )
                    records_count += 1
                    
                    if records_count % 1000 == 0:
                        self.stdout.write(f'  Processed {records_count} Bandcamp records...')
                    
                except Exception as e:
                    self.stdout.write(f'Error processing Bandcamp row {row_idx}: {e}')
                    continue
        
        return records_count

    def import_distribution_detailed(self, label, csv_file, quarter, limit=None):
        """Import detailed distribution transactions"""
        platform = Platform.objects.get(name='Distribution')
        datasource = DataSource.objects.get(name='distribution_detailed')
        
        # Parse quarter to get dates
        period_match = re.search(r'(20\d{2})-Q([1-4])', quarter)
        if not period_match:
            return 0
        
        year = int(period_match.group(1))
        quarter_num = int(period_match.group(2))
        
        # Create source file record
        source_file = SourceFile.objects.create(
            datasource=datasource,
            label=label,
            path=str(csv_file.relative_to(csv_file.parents[4])),
            sha256=self.compute_file_hash(csv_file),
            bytes=csv_file.stat().st_size,
            mtime=timezone.make_aware(datetime.fromtimestamp(csv_file.stat().st_mtime)),
            statement_type='distribution_detailed',
            period_start=date(year, (quarter_num-1)*3+1, 1),
            period_end=date(year+1, 1, 1) if quarter_num == 4 else date(year, quarter_num*3+1, 1)
        )
        
        records_count = 0
        
        # Detect encoding
        with open(csv_file, 'rb') as f:
            raw_data = f.read(200000)
            encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
        
        with open(csv_file, 'r', encoding=encoding, errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row_idx, row in enumerate(reader):
                if limit and records_count >= limit:
                    break
                    
                try:
                    # ONLY IMPORT COMPLETE TRACK ROWS (skip summary/total lines)
                    sale_type = row.get('Sale Type', '').strip()
                    track_artist = row.get('Track Artist', '').strip()
                    track_title = row.get('Track Title', '').strip()
                    isrc = row.get('ISRC', '').strip()
                    
                    # Skip if not a proper track transaction
                    if (sale_type != 'Track' or 
                        not track_artist or 
                        not track_title or 
                        not isrc or
                        'Exchange' in isrc):
                        continue  # Skip summary lines, currency lines, totals, etc.
                    
                    # Parse amounts - USE ROYALTY COLUMN (what label actually receives)
                    net_amount = self.extract_decimal_from_row(row, ['Royalty'])  # This is what you actually get!
                    gross_amount = self.extract_decimal_from_row(row, ['Value'])  # This is gross platform revenue
                    
                    if net_amount == 0:
                        net_amount = gross_amount
                        
                    quantity = self.extract_integer_from_row(row, ['Qty', 'Sales', 'Quantity'])
                    
                    if net_amount <= 0 and gross_amount <= 0:
                        continue  # Skip zero transactions
                    
                    # Use quarter start date as occurred_at
                    occurred_at = timezone.make_aware(datetime(year, (quarter_num-1)*3+1, 1))
                    
                    # Create row hash
                    row_hash = hashlib.sha256(
                        f"{source_file.id}:{row_idx}:{quarter}:{net_amount}:{row.get('Track Title', row.get('Track Artist', ''))}".encode()
                    ).hexdigest()[:64]
                    
                    RevenueEvent.objects.create(
                        source_file=source_file,
                        label=label,
                        occurred_at=occurred_at,
                        platform=platform,
                        currency='EUR',  # Distribution is typically EUR
                        product_type='digital',
                        quantity=quantity,
                        gross_amount=gross_amount,
                        net_amount=net_amount,
                        net_amount_base=net_amount,
                        base_ccy='EUR',
                        isrc=isrc,
                        upc_ean=row.get('EAN', ''),
                        track_artist_name=track_artist,
                        track_title=track_title,
                        catalog_number=row.get('Catalog', ''),
                        row_hash=row_hash
                    )
                    records_count += 1
                    
                    if records_count % 1000 == 0:
                        self.stdout.write(f'  Processed {records_count} {quarter} records...')
                    
                except Exception as e:
                    # Skip invalid rows silently for now
                    continue
        
        return records_count

    def parse_bandcamp_date(self, date_str):
        """Parse Bandcamp date format"""
        try:
            # Handle formats like "7/15/15 2:08am" or "7/15/2015 2:08am"
            date_part = date_str.split(' ')[0]  # Get just the date part
            parts = date_part.split('/')
            
            if len(parts) == 3:
                month, day, year = parts
                month, day = int(month), int(day)
                
                # Handle 2-digit vs 4-digit years
                year = int(year)
                if year < 100:
                    year += 2000 if year < 50 else 1900
                
                return timezone.make_aware(datetime(year, month, day))
                
        except (ValueError, IndexError):
            pass
        
        return None

    def parse_decimal(self, value_str):
        """Parse decimal amount, handling currency symbols"""
        if not value_str:
            return Decimal('0')
        
        # Clean the string
        cleaned = str(value_str).replace('$', '').replace('€', '').replace(',', '').strip()
        
        try:
            return Decimal(cleaned) if cleaned else Decimal('0')
        except (InvalidOperation, ValueError):
            return Decimal('0')

    def extract_decimal_from_row(self, row, column_names):
        """Extract decimal value trying multiple column names"""
        for col_name in column_names:
            if col_name in row and row[col_name]:
                return self.parse_decimal(row[col_name])
        return Decimal('0')

    def extract_integer_from_row(self, row, column_names):
        """Extract integer value trying multiple column names"""
        for col_name in column_names:
            if col_name in row and row[col_name]:
                try:
                    return int(float(row[col_name]))
                except (ValueError, TypeError):
                    continue
        return 0

    def compute_file_hash(self, file_path):
        """Compute SHA256 of file"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024*1024), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
