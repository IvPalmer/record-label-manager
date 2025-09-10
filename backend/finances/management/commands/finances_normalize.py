import csv
import hashlib
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
from decimal import Decimal
from datetime import datetime, date

from finances.models import (
    Platform, Store, Country, SourceFile, RevenueEvent, CostEvent, ImportBatch
)
from api.models import Label, Release, Track


class Command(BaseCommand):
    help = 'Normalize canonical finance data into the database'

    def add_arguments(self, parser):
        parser.add_argument('--label', type=str, required=True, help='Label name')
        parser.add_argument('--batch-id', type=int, help='Import batch ID (optional)')
        parser.add_argument('--force', action='store_true', help='Force re-import of existing data')

    def handle(self, *args, **options):
        label_name = options['label']
        
        # Get label
        try:
            label = Label.objects.get(name=label_name)
        except Label.DoesNotExist:
            raise CommandError(f'Label "{label_name}" does not exist.')
        
        # Create import batch
        batch = ImportBatch.objects.create(label=label)
        self.stdout.write(f'Created import batch #{batch.id} for {label.name}')
        
        try:
            self.normalize_data(label, batch, options.get('force', False))
            batch.finished_at = timezone.now()
            batch.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully normalized finance data for {label.name}')
            )
            
        except Exception as e:
            batch.status = 'failed'
            batch.finished_at = timezone.now()
            batch.save()
            raise CommandError(f'Normalization failed: {e}')

    @transaction.atomic
    def normalize_data(self, label, batch, force=False):
        # Setup reference data
        self.setup_reference_data()
        
        # Get source files for this label
        source_files = SourceFile.objects.filter(label=label).order_by('period_start', 'statement_type')
        
        total_records = 0
        
        for source_file in source_files:
            self.stdout.write(f'Processing: {source_file.path}')
            
            # Find canonical CSV file
            canonical_file = self.find_canonical_file(source_file)
            if not canonical_file:
                self.stdout.write(self.style.WARNING(f'No canonical file found for {source_file.path}'))
                continue
            
            # Process the file
            records_processed = self.process_canonical_file(source_file, canonical_file, force)
            total_records += records_processed
            
            self.stdout.write(f'  -> Processed {records_processed} records')
        
        self.stdout.write(f'Total records processed: {total_records}')

    def setup_reference_data(self):
        """Create basic reference data if missing"""
        # Platforms
        Platform.objects.get_or_create(name='Bandcamp', defaults={'vendor_key': 'bandcamp'})
        Platform.objects.get_or_create(name='Spotify', defaults={'vendor_key': 'spotify'})
        Platform.objects.get_or_create(name='Apple Music', defaults={'vendor_key': 'apple'})
        Platform.objects.get_or_create(name='Amazon Music', defaults={'vendor_key': 'amazon'})
        Platform.objects.get_or_create(name='YouTube Music', defaults={'vendor_key': 'youtube'})
        Platform.objects.get_or_create(name='Distribution', defaults={'vendor_key': 'distribution'})
        
        # Countries
        Country.objects.get_or_create(iso2='US', defaults={'name': 'United States'})
        Country.objects.get_or_create(iso2='BR', defaults={'name': 'Brazil'})
        Country.objects.get_or_create(iso2='DE', defaults={'name': 'Germany'})
        Country.objects.get_or_create(iso2='FR', defaults={'name': 'France'})
        Country.objects.get_or_create(iso2='UK', defaults={'name': 'United Kingdom'})

    def find_canonical_file(self, source_file):
        """Find the canonical CSV file for a source file"""
        # Base path from project root
        repo_root = Path(__file__).resolve().parents[4]
        
        # For bandcamp files
        if source_file.datasource.name == 'bandcamp':
            canonical_path = repo_root / "finance" / "sources" / "tropical-twista" / "bandcamp" / "canonical" / "bandcamp_all.csv"
            return canonical_path if canonical_path.exists() else None
        
        # For distribution files
        elif source_file.datasource.name == 'distribution':
            # Parse period from source file
            period = source_file.statement_type
            if source_file.period_start:
                year = source_file.period_start.year
                quarter = (source_file.period_start.month - 1) // 3 + 1
                canonical_path = repo_root / "finance" / "sources" / "tropical-twista" / "distribution" / "canonical" / str(year) / f"Q{quarter}" / f"{period}.csv"
                return canonical_path if canonical_path.exists() else None
        
        return None

    def process_canonical_file(self, source_file, canonical_file, force=False):
        """Process a canonical CSV file"""
        records_count = 0
        
        with open(canonical_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_idx, row in enumerate(reader):
                try:
                    # Create row hash for deduplication
                    row_hash = self.compute_row_hash(source_file, row)
                    
                    # Check if already exists
                    if not force and RevenueEvent.objects.filter(row_hash=row_hash).exists():
                        continue
                    
                    # Process row based on source type
                    if source_file.datasource.name == 'bandcamp':
                        revenue_event = self.process_bandcamp_row(source_file, row, row_hash)
                    elif source_file.datasource.name == 'distribution':
                        revenue_event = self.process_distribution_row(source_file, row, row_hash)
                    else:
                        continue
                    
                    if revenue_event:
                        records_count += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Error processing row {row_idx}: {e}')
                    )
                    continue
        
        return records_count

    def process_bandcamp_row(self, source_file, row, row_hash):
        """Process a Bandcamp CSV row"""
        # Get platform
        platform = Platform.objects.get(name='Bandcamp')
        
        # Parse date
        date_str = row.get('date', '').strip()
        if not date_str:
            return None
        
        try:
            # Bandcamp format: "M/D/YYYY HH:MM:SS timezone"
            date_part = date_str.split(' ')[0]
            month, day, year = date_part.split('/')
            occurred_at = datetime(int(year), int(month), int(day))
            occurred_at = timezone.make_aware(occurred_at)
        except (ValueError, IndexError):
            self.stdout.write(self.style.WARNING(f'Invalid date format: {date_str}'))
            return None
        
        # Parse amounts
        try:
            net_amount = Decimal(str(row.get('amount you received', '0')).replace('$', '').replace(',', '') or '0')
            gross_amount = Decimal(str(row.get('item total', '0')).replace('$', '').replace(',', '') or '0')
            quantity = int(row.get('quantity', '0') or '0')
        except (ValueError, TypeError):
            net_amount = gross_amount = Decimal('0')
            quantity = 0
        
        # Create revenue event
        revenue_event = RevenueEvent.objects.create(
            source_file=source_file,
            label=source_file.label,
            occurred_at=occurred_at,
            platform=platform,
            currency=row.get('currency', 'USD'),
            product_type=row.get('item type', ''),
            quantity=quantity,
            gross_amount=gross_amount,
            net_amount=net_amount,
            net_amount_base=net_amount,  # Assume USD for now
            base_ccy='USD',
            row_hash=row_hash
        )
        
        return revenue_event

    def process_distribution_row(self, source_file, row, row_hash):
        """Process a distribution CSV row"""
        # Get platform - try to map from distribution data
        platform = Platform.objects.get(name='Distribution')
        
        # Parse date (if available)
        occurred_at = None
        if source_file.period_start:
            # Use period start as default date
            occurred_at = timezone.make_aware(
                datetime.combine(source_file.period_start, datetime.min.time())
            )
        
        # Parse amounts based on column names
        try:
            # Try different column name patterns
            gross_amount = self.extract_decimal(row, ['Revenue-EUR', 'Revenue_EUR', 'Revenue EUR', 'Value', 'Gross'])
            net_amount = self.extract_decimal(row, ['Rev.less Publ.EUR', 'Rev_less_Publ_EUR', 'Royalty', 'Net'])
            
            if net_amount == 0:
                net_amount = gross_amount
                
            quantity = self.extract_integer(row, ['Sales', 'Qty', 'Quantity'])
            
        except (ValueError, TypeError):
            gross_amount = net_amount = Decimal('0')
            quantity = 0
        
        # Skip zero-value records
        if gross_amount == 0 and net_amount == 0:
            return None
        
        # Create revenue event
        revenue_event = RevenueEvent.objects.create(
            source_file=source_file,
            label=source_file.label,
            occurred_at=occurred_at,
            platform=platform,
            currency='EUR',  # Distribution data is typically in EUR
            product_type='digital',
            quantity=quantity,
            gross_amount=gross_amount,
            net_amount=net_amount,
            net_amount_base=net_amount,  # Already in EUR
            base_ccy='EUR',
            row_hash=row_hash
        )
        
        return revenue_event

    def extract_decimal(self, row, column_names):
        """Extract decimal value from row trying multiple column names"""
        for col_name in column_names:
            if col_name in row and row[col_name]:
                value_str = str(row[col_name]).replace(' ', '').replace(',', '.').replace('€', '').replace('$', '')
                try:
                    return Decimal(value_str)
                except (ValueError, TypeError):
                    continue
        return Decimal('0')

    def extract_integer(self, row, column_names):
        """Extract integer value from row trying multiple column names"""
        for col_name in column_names:
            if col_name in row and row[col_name]:
                try:
                    return int(float(row[col_name]))
                except (ValueError, TypeError):
                    continue
        return 0

    def compute_row_hash(self, source_file, row):
        """Compute unique hash for deduplication"""
        # Create a string with source file ID and key row data
        key_data = f"{source_file.id}:{row}"
        return hashlib.sha256(key_data.encode('utf-8')).hexdigest()[:64]
