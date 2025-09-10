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
    help = 'Debug why parsing is failing on most rows'

    def handle(self, *args, **options):
        label = Label.objects.get(name="Tropical Twista Records")
        
        # Clear test data
        RevenueEvent.objects.filter(label=label, source_file__statement_type='debug').delete()
        
        platform = Platform.objects.get_or_create(name='Distribution')[0]
        datasource = DataSource.objects.get_or_create(name='debug')[0]
        
        repo_root = Path(__file__).resolve().parents[4]
        test_file = repo_root / "finance/sources/tropical-twista/distribution/2023-Q2/Tropical Twista Records Q2 2023__converted.csv"
        
        source_file = SourceFile.objects.create(
            datasource=datasource,
            label=label,
            path=str(test_file),
            sha256="debug",
            bytes=0,
            mtime=timezone.now(),
            statement_type='debug'
        )
        
        success_count = 0
        error_counts = {}
        
        with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row_idx, row in enumerate(reader):
                # Skip completely empty rows
                if not any(str(value or '').strip() for value in row.values()):
                    continue
                
                try:
                    # Try to parse each field and catch specific errors
                    track_artist = row.get('Track Artist', '') or 'Unknown'
                    track_title = row.get('Track Title', '') or 'Unknown'
                    
                    # Parse royalty with explicit error checking
                    royalty_str = row.get('Royalty', '0')
                    try:
                        royalty = Decimal(str(royalty_str)) if royalty_str else Decimal('0')
                    except Exception as e:
                        error_counts.setdefault(f'royalty_parse_{type(e).__name__}', 0)
                        error_counts[f'royalty_parse_{type(e).__name__}'] += 1
                        continue
                    
                    # Try to create the row hash
                    try:
                        row_hash = hashlib.sha256(
                            f"debug:{source_file.id}:{row_idx}:{track_artist}:{track_title}".encode('utf-8')
                        ).hexdigest()[:64]
                    except Exception as e:
                        error_counts.setdefault(f'hash_{type(e).__name__}', 0)
                        error_counts[f'hash_{type(e).__name__}'] += 1
                        continue
                    
                    # Try to create the database record
                    try:
                        RevenueEvent.objects.create(
                            source_file=source_file,
                            label=label,
                            occurred_at=timezone.make_aware(datetime(2023, 4, 1)),
                            platform=platform,
                            currency='EUR',
                            product_type='stream',
                            quantity=0,
                            gross_amount=Decimal('0'),
                            net_amount=royalty,
                            net_amount_base=royalty,
                            base_ccy='EUR',
                            track_artist_name=track_artist,
                            track_title=track_title,
                            isrc=row.get('ISRC', '') or '',
                            row_hash=row_hash
                        )
                        success_count += 1
                        
                    except Exception as e:
                        error_type = type(e).__name__
                        error_counts.setdefault(f'db_create_{error_type}', 0)
                        error_counts[f'db_create_{error_type}'] += 1
                        
                        # Log first few specific errors
                        if error_counts[f'db_create_{error_type}'] <= 3:
                            self.stdout.write(f'DB Error {error_counts[f"db_create_{error_type}"]}: {e}')
                        continue
                
                except Exception as e:
                    error_counts.setdefault(f'general_{type(e).__name__}', 0)
                    error_counts[f'general_{type(e).__name__}'] += 1
                    continue
                
                # Progress indicator
                if (row_idx + 1) % 100000 == 0:
                    self.stdout.write(f'Processed {row_idx + 1:,} rows, {success_count:,} successful')
        
        self.stdout.write('')
        self.stdout.write('DEBUG RESULTS:')
        self.stdout.write(f'Successfully imported: {success_count:,}')
        self.stdout.write(f'Total errors: {sum(error_counts.values()):,}')
        
        self.stdout.write('')
        self.stdout.write('Error breakdown:')
        for error_type, count in sorted(error_counts.items()):
            self.stdout.write(f'  {error_type}: {count:,}')

    def detect_encoding(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(200000)
            import chardet
            result = chardet.detect(raw_data)
            return result.get('encoding', 'utf-8') or 'utf-8'
        except:
            return 'utf-8'

    def compute_hash(self, file_path):
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024*1024), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
