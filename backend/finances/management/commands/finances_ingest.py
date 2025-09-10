import os
import sys
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from finances.models import DataSource, SourceFile
from api.models import Label


class Command(BaseCommand):
    help = 'Run finance pipeline ingest and register source files'

    def add_arguments(self, parser):
        parser.add_argument('--label', type=str, required=True, help='Label name (e.g., "Tropical Twista Records")')
        parser.add_argument('--label-slug', type=str, help='Label slug for file paths (e.g., tropical-twista)')
        parser.add_argument(
            '--path', 
            type=str, 
            help='Path to label sources (default: finance/sources/{label-slug})'
        )

    def handle(self, *args, **options):
        label_name = options['label']
        label_slug = options.get('label_slug') or label_name.lower().replace(' ', '-').replace('records', '').strip('-')
        
        # Get or create label
        try:
            label = Label.objects.get(name=label_name)
        except Label.DoesNotExist:
            raise CommandError(f'Label "{label_name}" does not exist. Please create it first.')
        
        # Set up path
        repo_root = Path(__file__).resolve().parents[4]  # backend/finances/management/commands -> repo_root
        default_path = repo_root / "finance" / "sources" / label_slug
        path_option = options.get('path')
        source_path = Path(path_option) if path_option else default_path
        
        if not source_path.exists():
            raise CommandError(f'Source path does not exist: {source_path}')
        
        self.stdout.write(f'Running finance pipeline ingest for label: {label.name}')
        self.stdout.write(f'Source path: {source_path}')
        
        # Add the repo root to Python path so we can import finance.pipeline
        sys.path.insert(0, str(repo_root))
        
        try:
            from finance.pipeline.cli.ingest import ingest_distribution, ingest_bandcamp
            
            # Run the pipeline
            ingest_distribution(source_path)
            ingest_bandcamp(source_path)
            
            # Register source files in database
            self.register_source_files(label, source_path)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully ingested finance data for {label.name}')
            )
            
        except ImportError as e:
            raise CommandError(f'Failed to import finance pipeline: {e}')
        except Exception as e:
            raise CommandError(f'Pipeline execution failed: {e}')
        finally:
            # Clean up path
            if str(repo_root) in sys.path:
                sys.path.remove(str(repo_root))

    @transaction.atomic
    def register_source_files(self, label, source_path):
        """Register canonical source files in database"""
        import json
        from datetime import datetime
        
        # Get or create data sources
        bandcamp_ds, _ = DataSource.objects.get_or_create(
            name='bandcamp', 
            defaults={'vendor': 'Bandcamp'}
        )
        distribution_ds, _ = DataSource.objects.get_or_create(
            name='distribution', 
            defaults={'vendor': 'Zebralution'}
        )
        
        # Register bandcamp files
        bandcamp_meta_path = source_path / "bandcamp" / "canonical" / "meta.json"
        if bandcamp_meta_path.exists():
            self._register_from_meta(label, bandcamp_ds, bandcamp_meta_path)
        
        # Register distribution files
        distribution_canonical = source_path / "distribution" / "canonical"
        for meta_file in distribution_canonical.rglob("meta.json"):
            self._register_from_meta(label, distribution_ds, meta_file)

    def _register_from_meta(self, label, datasource, meta_path):
        """Register source files from meta.json"""
        import json
        from datetime import datetime
        
        try:
            with open(meta_path, 'r') as f:
                meta_data = json.load(f)
            
            # Handle both single dict and list of dicts
            if isinstance(meta_data, dict):
                meta_data = [meta_data]
            
            for meta in meta_data:
                # Parse period dates
                period_start = None
                period_end = None
                period_str = meta.get('period')
                if period_str and period_str != 'all':
                    if '-Q' in period_str:
                        year, quarter = period_str.split('-Q')
                        year = int(year)
                        quarter = int(quarter)
                        month_start = (quarter - 1) * 3 + 1
                        period_start = datetime(year, month_start, 1).date()
                        if quarter == 4:
                            period_end = datetime(year + 1, 1, 1).date()
                        else:
                            period_end = datetime(year, month_start + 3, 1).date()
                
                # Create or update source file record
                source_file, created = SourceFile.objects.get_or_create(
                    datasource=datasource,
                    label=label,
                    path=meta['path'],
                    sha256=meta['sha256'],
                    defaults={
                        'bytes': meta['bytes'],
                        'mtime': datetime.fromtimestamp(meta['mtime']),
                        'period_start': period_start,
                        'period_end': period_end,
                        'statement_type': meta.get('statement_type', 'unknown'),
                    }
                )
                
                if created:
                    self.stdout.write(f'Registered: {meta["path"]}')
                else:
                    self.stdout.write(f'Already exists: {meta["path"]}')
                    
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Failed to register from {meta_path}: {e}')
            )
