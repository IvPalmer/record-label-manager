import csv
import hashlib
import chardet
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from datetime import datetime
import re

from finances.models import Platform, DataSource, SourceFile, RevenueEvent, ImportBatch
from api.models import Label


class Command(BaseCommand):
    help = 'Import with smart validation based on common columns'

    def add_arguments(self, parser):
        parser.add_argument('--label', type=str, required=True, help='Label name')

    def handle(self, *args, **options):
        label_name = options['label']
        
        try:
            label = Label.objects.get(name=label_name)
        except Label.DoesNotExist:
            raise CommandError(f'Label "{label_name}" does not exist.')
        
        # Clear existing data
        self.stdout.write('Clearing existing data...')
        RevenueEvent.objects.filter(label=label).delete()
        SourceFile.objects.filter(label=label).delete()
        
        self.setup_platforms()
        batch = ImportBatch.objects.create(label=label)
        
        repo_root = Path(__file__).resolve().parents[4]
        sources_root = repo_root / "finance" / "sources" / "tropical-twista"
        
        total_imported = 0
        
        try:
            # Import all distribution files
            distribution_dir = sources_root / "distribution"
            for quarter_dir in sorted(distribution_dir.iterdir()):
                if quarter_dir.is_dir():
                    for csv_file in quarter_dir.glob("*.csv"):
                        imported = self.import_distribution_validated(label, csv_file, quarter_dir.name)
                        total_imported += imported
                        if imported > 0:
                            self.stdout.write(f'{quarter_dir.name}: {imported:,} valid records')
            
            # Import Bandcamp
            bandcamp_file = sources_root / "bandcamp" / "20000101-20250729_bandcamp_raw_data_Tropical-Twista-Records.csv"
            if bandcamp_file.exists():
                imported = self.import_bandcamp_validated(label, bandcamp_file)
                total_imported += imported
                if imported > 0:
                    self.stdout.write(f'Bandcamp: {imported:,} valid records')
            
            batch.finished_at = timezone.now()
            batch.save()
            
            self.stdout.write('')
            self.stdout.write(f'TOTAL IMPORTED: {total_imported:,} valid records')
            
        except Exception as e:
            batch.status = 'failed'
            batch.finished_at = timezone.now()
            batch.save()
            raise CommandError(f'Import failed: {e}')

    def setup_platforms(self):
        Platform.objects.get_or_create(name='Distribution', defaults={'vendor_key': 'distribution'})
        Platform.objects.get_or_create(name='Bandcamp', defaults={'vendor_key': 'bandcamp'})
        DataSource.objects.get_or_create(name='distribution', defaults={'vendor': 'Distribution'})
        DataSource.objects.get_or_create(name='bandcamp', defaults={'vendor': 'Bandcamp'})

    def is_valid_distribution_row(self, row):
        """Simple structural validation - check if row has enough data"""
        # Count non-empty columns
        values = [str(value or '').strip() for value in row.values()]
        non_empty_count = sum(1 for value in values if value)
        
        # Skip rows with less than 8 filled columns (too sparse)
        if non_empty_count < 8:
            return False
        
        # Skip only clear summary/total rows by checking specific patterns
        row_text = ' '.join(values).upper()
        skip_patterns = ['EXCHANGE RATE', 'TOTAL INCOME', 'SUM TOTAL', '€', '$', 'GBP', 'CURRENCY']
        
        # Skip if it's clearly a summary line (contains currency symbols alone or totals)
        if any(pattern in row_text for pattern in skip_patterns) and len(row_text.split()) < 10:
            return False
            
        return True

    def is_valid_bandcamp_row(self, row):
        """Simple structural validation for Bandcamp"""
        # Count non-empty columns  
        values = [str(value or '').strip() for value in row.values()]
        non_empty_count = sum(1 for value in values if value)
        
        # Must have at least 6 columns filled
        if non_empty_count < 6:
            return False
        
        # Must have date field
        date_str = (row.get('date', '') or '').strip()
        if not date_str:
            return False
        
        # Skip admin transactions only
        row_text = ' '.join(values).upper()
        if 'PAYOUT' in row_text or 'PAYMENT' in row_text:
            return False
            
        return True

    def import_distribution_validated(self, label, csv_file, period):
        """Import distribution file with validation"""
        year, quarter = self.parse_period(period)
        if not year or not quarter:
            return 0
        
        # Detect format and encoding
        file_format = self.detect_format(csv_file)
        encoding = self.detect_encoding(csv_file)
        
        platform = Platform.objects.get(name='Distribution')
        datasource = DataSource.objects.get(name='distribution')
        
        source_file = SourceFile.objects.create(
            datasource=datasource,
            label=label,
            path=str(csv_file.relative_to(csv_file.parents[4])),
            sha256=self.compute_hash(csv_file),
            bytes=csv_file.stat().st_size,
            mtime=timezone.make_aware(datetime.fromtimestamp(csv_file.stat().st_mtime)),
            statement_type=file_format
        )
        
        imported = 0
        delimiter = ';' if file_format == 'zebralution' else ','
        
        with open(csv_file, 'r', encoding=encoding, errors='ignore') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            
            for row_idx, row in enumerate(reader):
                if not self.is_valid_distribution_row(row):
                    continue
                
                try:
                    if file_format == 'zebralution':
                        event = self.create_zebralution_event(source_file, label, row, year, quarter, platform)
                    else:
                        event = self.create_labelworx_event(source_file, label, row, year, quarter, platform)
                    
                    if event:
                        imported += 1
                        
                except Exception:
                    continue
        
        return imported

    def create_zebralution_event(self, source_file, label, row, year, quarter, platform):
        """Create revenue event from Zebralution format"""
        artist = row.get('Artist', '').strip()
        title = row.get('Title', '').strip()
        revenue_net = self.parse_european_decimal(row.get('Rev.less Publ.EUR', '0'))
        
        return RevenueEvent.objects.create(
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
            track_artist_name=artist,
            track_title=title,
            catalog_number=row.get('Label Order-Nr', ''),
            isrc=row.get('ISRC', ''),
            row_hash=f"zeb:{source_file.id}:{row['Artist']}:{row['Title']}"[:64]
        )

    def create_labelworx_event(self, source_file, label, row, year, quarter, platform):
        """Create revenue event from Labelworx format"""
        track_artist = row.get('Track Artist', '').strip()
        track_title = row.get('Track Title', '').strip()
        royalty = self.parse_decimal(row.get('Royalty', '0'))
        
        return RevenueEvent.objects.create(
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
            catalog_number=row.get('Catalog', ''),
            isrc=row.get('ISRC', ''),
            row_hash=f"lbx:{source_file.id}:{track_artist}:{track_title}"[:64]
        )

    def import_bandcamp_validated(self, label, csv_file):
        """Import Bandcamp with proper encoding detection"""
        encoding = self.detect_encoding(csv_file)
        
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
                if not self.is_valid_bandcamp_row(row):
                    continue
                
                try:
                    date_str = row.get('date', '').strip()
                    occurred_at = self.parse_bandcamp_date(date_str)
                    if not occurred_at:
                        continue
                    
                    net_amount = self.parse_decimal(row.get('amount you received', '0'))
                    
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
                        net_amount_base=net_amount * Decimal('0.85') if row.get('currency') == 'USD' else net_amount,
                        base_ccy='EUR',
                        track_artist_name=row.get('artist', ''),
                        track_title=row.get('item name', ''),
                        row_hash=f"bc:{row_idx}:{date_str}:{net_amount}"[:64]
                    )
                    imported += 1
                    
                except Exception:
                    continue
        
        return imported

    def detect_format(self, csv_file):
        """Detect Zebralution vs Labelworx format"""
        try:
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline()
                if ';' in first_line and 'Period' in first_line:
                    return 'zebralution'
                elif ',' in first_line and 'Track Artist' in first_line:
                    return 'labelworx'
        except:
            pass
        return 'labelworx'  # Default

    def detect_encoding(self, file_path):
        """Detect file encoding"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(200000)
            result = chardet.detect(raw_data)
            return result.get('encoding', 'utf-8') or 'utf-8'
        except:
            return 'utf-8'

    def parse_period(self, period_str):
        """Extract year and quarter from period string"""
        match = re.search(r'(20\d{2}).*Q([1-4])', period_str)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None

    def parse_european_decimal(self, value_str):
        """Parse European format: 1,234 means 1.234"""
        if not value_str:
            return Decimal('0')
        try:
            cleaned = str(value_str).strip().replace(',', '.')
            return Decimal(cleaned) if cleaned else Decimal('0')
        except:
            return Decimal('0')

    def parse_decimal(self, value_str):
        """Parse standard decimal"""
        if not value_str:
            return Decimal('0')
        try:
            cleaned = str(value_str).replace('$', '').replace('€', '').strip()
            return Decimal(cleaned) if cleaned else Decimal('0')
        except:
            return Decimal('0')

    def parse_bandcamp_date(self, date_str):
        """Parse Bandcamp date"""
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
        """Compute file hash"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024*1024), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
