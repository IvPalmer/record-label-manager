import csv
import hashlib
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date

from finances.models import Platform, Store, Country, DataSource, SourceFile, RevenueEvent, ImportBatch
from api.models import Label


class Command(BaseCommand):
    help = 'Simple one-pass finance data import (bypasses meta.json system)'

    def add_arguments(self, parser):
        parser.add_argument('--label', type=str, required=True, help='Label name')

    def handle(self, *args, **options):
        label_name = options['label']
        
        # Get label
        try:
            label = Label.objects.get(name=label_name)
        except Label.DoesNotExist:
            raise CommandError(f'Label "{label_name}" does not exist.')
        
        # Setup reference data
        self.setup_reference_data()
        
        # Import from the pipeline preview data (which we know is correct)
        repo_root = Path(__file__).resolve().parents[4]
        preview_dir = repo_root / "finance" / "pipeline" / "storage" / "warehouse" / "preview"
        
        batch = ImportBatch.objects.create(label=label)
        self.stdout.write(f'Created import batch #{batch.id} for {label.name}')
        
        total_records = 0
        
        try:
            with transaction.atomic():
                # Import distribution data
                dist_file = preview_dir / "tropical-twista_distribution_summary.csv"
                if dist_file.exists():
                    records = self.import_distribution_summary(label, dist_file)
                    total_records += records
                    self.stdout.write(f'Imported {records} distribution records')
                
                # Import bandcamp data  
                bc_file = preview_dir / "tropical-twista_bandcamp_quarterly.csv"
                if bc_file.exists():
                    records = self.import_bandcamp_quarterly(label, bc_file)
                    total_records += records
                    self.stdout.write(f'Imported {records} bandcamp records')
                
            batch.finished_at = timezone.now()
            batch.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully imported {total_records} records for {label.name}')
            )
            
        except Exception as e:
            batch.status = 'failed'
            batch.finished_at = timezone.now()
            batch.save()
            raise CommandError(f'Import failed: {e}')

    def setup_reference_data(self):
        """Create basic reference data"""
        # Platforms
        Platform.objects.get_or_create(name='Bandcamp', defaults={'vendor_key': 'bandcamp'})
        Platform.objects.get_or_create(name='Distribution', defaults={'vendor_key': 'distribution'})
        
        # Data sources
        DataSource.objects.get_or_create(name='distribution_summary', defaults={'vendor': 'Pipeline'})
        DataSource.objects.get_or_create(name='bandcamp_summary', defaults={'vendor': 'Pipeline'})
        
        # Countries
        Country.objects.get_or_create(iso2='US', defaults={'name': 'United States'})
        Country.objects.get_or_create(iso2='BR', defaults={'name': 'Brazil'})

    def import_distribution_summary(self, label, csv_file):
        """Import distribution summary data"""
        platform = Platform.objects.get(name='Distribution')
        datasource = DataSource.objects.get(name='distribution_summary')
        
        # Create a single source file record for the summary
        source_file = SourceFile.objects.create(
            datasource=datasource,
            label=label,
            path=str(csv_file.relative_to(csv_file.parents[4])),
            sha256=self.compute_file_hash(csv_file),
            bytes=csv_file.stat().st_size,
            mtime=timezone.make_aware(datetime.fromtimestamp(csv_file.stat().st_mtime)),
            statement_type='distribution_summary'
        )
        
        records_count = 0
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    year = int(row['year'])
                    quarter_str = str(row['quarter']).replace('Q', '')  # Remove 'Q' prefix if present
                    quarter = int(quarter_str)
                    
                    # Create date for the quarter
                    month = (quarter - 1) * 3 + 1
                    occurred_at = timezone.make_aware(datetime(year, month, 1))
                    
                    # Parse amounts
                    net_amount = Decimal(str(row['net_after_publ_eur'] or 0))
                    gross_amount = Decimal(str(row['revenue_eur'] or 0))
                    sales = int(row['sales'] or 0)
                    
                    # Create row hash
                    row_hash = hashlib.sha256(
                        f"{source_file.id}:{year}:{quarter}:{net_amount}".encode()
                    ).hexdigest()[:64]
                    
                    RevenueEvent.objects.create(
                        source_file=source_file,
                        label=label,
                        occurred_at=occurred_at,
                        platform=platform,
                        currency='EUR',
                        product_type='digital',
                        quantity=sales,
                        gross_amount=gross_amount,
                        net_amount=net_amount,
                        net_amount_base=net_amount,
                        base_ccy='EUR',
                        row_hash=row_hash
                    )
                    records_count += 1
                    
                except (ValueError, TypeError) as e:
                    self.stdout.write(f'Skipping invalid row: {e}')
                    continue
        
        return records_count

    def import_bandcamp_quarterly(self, label, csv_file):
        """Import bandcamp quarterly data"""
        platform = Platform.objects.get(name='Bandcamp')
        datasource = DataSource.objects.get(name='bandcamp_summary')
        
        # Create a single source file record for the summary
        source_file = SourceFile.objects.create(
            datasource=datasource,
            label=label,
            path=str(csv_file.relative_to(csv_file.parents[4])),
            sha256=self.compute_file_hash(csv_file),
            bytes=csv_file.stat().st_size,
            mtime=timezone.make_aware(datetime.fromtimestamp(csv_file.stat().st_mtime)),
            statement_type='bandcamp_summary'
        )
        
        records_count = 0
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    year = int(row['year'])
                    quarter = int(row['quarter'])
                    currency = row['currency']
                    
                    # Create date for the quarter
                    month = (quarter - 1) * 3 + 1
                    occurred_at = timezone.make_aware(datetime(year, month, 1))
                    
                    # Parse amount
                    net_amount = Decimal(str(row['net_amount'] or 0))
                    
                    # Create row hash
                    row_hash = hashlib.sha256(
                        f"{source_file.id}:{year}:{quarter}:{currency}:{net_amount}".encode()
                    ).hexdigest()[:64]
                    
                    RevenueEvent.objects.create(
                        source_file=source_file,
                        label=label,
                        occurred_at=occurred_at,
                        platform=platform,
                        currency=currency,
                        product_type='digital',
                        quantity=0,  # Not available in summary
                        gross_amount=net_amount,  # Use net as gross for bandcamp
                        net_amount=net_amount,
                        net_amount_base=net_amount * Decimal('0.85') if currency == 'USD' else net_amount,
                        base_ccy='EUR',
                        row_hash=row_hash
                    )
                    records_count += 1
                    
                except (ValueError, TypeError) as e:
                    self.stdout.write(f'Skipping invalid row: {e}')
                    continue
        
        return records_count

    def compute_file_hash(self, file_path):
        """Compute SHA256 of file"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024*1024), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
