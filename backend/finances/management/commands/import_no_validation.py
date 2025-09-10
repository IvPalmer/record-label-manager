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
    help = 'Import ALL non-empty rows with NO validation (test maximum capture)'

    def add_arguments(self, parser):
        parser.add_argument('--label', type=str, required=True, help='Label name')
        parser.add_argument('--test-file', type=str, help='Test single file only')

    def handle(self, *args, **options):
        label_name = options['label']
        test_file = options.get('test_file')
        
        try:
            label = Label.objects.get(name=label_name)
        except Label.DoesNotExist:
            raise CommandError(f'Label "{label_name}" does not exist.')
        
        if test_file:
            self.stdout.write(f'Testing single file: {test_file}')
            # Test just 2023-Q2 to see maximum possible import
            repo_root = Path(__file__).resolve().parents[4]
            file_path = repo_root / "finance/sources/tropical-twista/distribution/2023-Q2/Tropical Twista Records Q2 2023__converted.csv"
            imported = self.import_file_no_validation(label, file_path, 2023, 2)
            self.stdout.write(f'Imported {imported:,} records from test file')
            return
        
        self.stdout.write('Importing ALL files with NO validation...')
        RevenueEvent.objects.filter(label=label).delete()
        SourceFile.objects.filter(label=label).delete()
        
        self.setup_platforms()
        
        repo_root = Path(__file__).resolve().parents[4]
        sources_root = repo_root / "finance" / "sources" / "tropical-twista"
        
        total_imported = 0
        
        # Import all distribution files
        distribution_dir = sources_root / "distribution"
        for quarter_dir in sorted(distribution_dir.iterdir()):
            if quarter_dir.is_dir():
                year, quarter = self.parse_period(quarter_dir.name)
                if year and quarter:
                    for csv_file in quarter_dir.glob("*.csv"):
                        imported = self.import_file_no_validation(label, csv_file, year, quarter)
                        total_imported += imported
                        if imported > 0:
                            self.stdout.write(f'{quarter_dir.name}: {imported:,} records')
        
        self.stdout.write(f'TOTAL DISTRIBUTION: {total_imported:,} records')

    def setup_platforms(self):
        Platform.objects.get_or_create(name='Distribution', defaults={'vendor_key': 'distribution'})
        DataSource.objects.get_or_create(name='distribution', defaults={'vendor': 'Distribution'})

    def import_file_no_validation(self, label, csv_file, year, quarter):
        """Import file with NO validation - just skip completely empty rows"""
        file_format = self.detect_format(csv_file)
        encoding = self.detect_encoding(csv_file)
        delimiter = ';' if file_format == 'zebralution' else ','
        
        platform = Platform.objects.get(name='Distribution')
        datasource = DataSource.objects.get(name='distribution')
        
        source_file = SourceFile.objects.create(
            datasource=datasource,
            label=label,
            path=str(csv_file),
            sha256=self.compute_hash(csv_file),
            bytes=csv_file.stat().st_size,
            mtime=timezone.now(),
            statement_type=file_format
        )
        
        imported = 0
        
        with open(csv_file, 'r', encoding=encoding, errors='ignore') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            
            for row_idx, row in enumerate(reader):
                # ONLY skip completely empty rows
                if not any(str(value or '').strip() for value in row.values()):
                    continue
                
                try:
                    # Import EVERYTHING else with minimal parsing
                    if file_format == 'zebralution':
                        revenue_net = self.parse_european_decimal(row.get('Rev.less Publ.EUR', '0'))
                        artist = row.get('Artist', '') or 'Unknown'
                        title = row.get('Title', '') or 'Unknown'
                    else:
                        revenue_net = self.parse_decimal(row.get('Royalty', '0'))
                        artist = row.get('Track Artist', '') or 'Unknown'
                        title = row.get('Track Title', '') or 'Unknown'
                    
                    RevenueEvent.objects.create(
                        source_file=source_file,
                        label=label,
                        occurred_at=timezone.make_aware(datetime(year, (quarter-1)*3+1, 1)),
                        platform=platform,
                        currency='EUR',
                        product_type='stream',
                        quantity=0,
                        gross_amount=Decimal('0'),
                        net_amount=revenue_net,
                        net_amount_base=revenue_net,
                        base_ccy='EUR',
                        track_artist_name=artist,
                        track_title=title,
                        isrc=row.get('ISRC', '') or '',
                        row_hash=f"{file_format}:{source_file.id}:{row_idx}"[:64]
                    )
                    imported += 1
                    
                    if imported % 50000 == 0:
                        self.stdout.write(f'  {imported:,} records...')
                        
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

    def compute_hash(self, file_path):
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024*1024), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
