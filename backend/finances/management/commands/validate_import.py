import csv
import chardet
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db.models import Count

from finances.models import RevenueEvent, SourceFile
from api.models import Label


class Command(BaseCommand):
    help = 'Validate that all CSV rows are being imported correctly'

    def add_arguments(self, parser):
        parser.add_argument('--label', type=str, required=True, help='Label name')

    def handle(self, *args, **options):
        label_name = options['label']
        
        try:
            label = Label.objects.get(name=label_name)
        except Label.DoesNotExist:
            self.stdout.write(f'Label "{label_name}" does not exist.')
            return
        
        self.stdout.write('IMPORT VALIDATION REPORT')
        self.stdout.write('=' * 50)
        
        repo_root = Path(__file__).resolve().parents[4]
        sources_root = repo_root / "finance" / "sources" / "tropical-twista"
        
        total_expected = 0
        total_imported = 0
        files_with_issues = []
        
        # Validate Distribution files
        self.stdout.write('')
        self.stdout.write('DISTRIBUTION FILES:')
        distribution_dir = sources_root / "distribution"
        
        for quarter_dir in sorted(distribution_dir.iterdir()):
            if quarter_dir.is_dir():
                for csv_file in quarter_dir.glob("*.csv"):
                    expected = self.count_csv_rows(csv_file)
                    imported = self.count_imported_rows(csv_file, label)
                    
                    total_expected += expected
                    total_imported += imported
                    
                    status = "✓" if imported >= expected * 0.9 else "✗"
                    completion = (imported / expected * 100) if expected > 0 else 0
                    
                    self.stdout.write(f'{status} {quarter_dir.name:12} {csv_file.name:40} {imported:6,}/{expected:6,} ({completion:5.1f}%)')
                    
                    if completion < 90:
                        files_with_issues.append((csv_file, expected, imported, completion))
        
        # Validate Bandcamp
        self.stdout.write('')
        self.stdout.write('BANDCAMP FILE:')
        bandcamp_file = sources_root / "bandcamp" / "20000101-20250729_bandcamp_raw_data_Tropical-Twista-Records.csv"
        
        if bandcamp_file.exists():
            expected = self.count_csv_rows(bandcamp_file)
            imported = self.count_imported_bandcamp(bandcamp_file, label)
            
            total_expected += expected
            total_imported += imported
            
            status = "✓" if imported >= expected * 0.9 else "✗"
            completion = (imported / expected * 100) if expected > 0 else 0
            
            self.stdout.write(f'{status} {"Bandcamp":12} {bandcamp_file.name:40} {imported:6,}/{expected:6,} ({completion:5.1f}%)')
            
            if completion < 90:
                files_with_issues.append((bandcamp_file, expected, imported, completion))
        
        # Summary
        self.stdout.write('')
        self.stdout.write('OVERALL SUMMARY:')
        self.stdout.write(f'Total Expected: {total_expected:,} rows')
        self.stdout.write(f'Total Imported: {total_imported:,} records')
        overall_completion = (total_imported / total_expected * 100) if total_expected > 0 else 0
        self.stdout.write(f'Overall Completion: {overall_completion:.1f}%')
        
        # Issues report
        if files_with_issues:
            self.stdout.write('')
            self.stdout.write('FILES WITH ISSUES (< 90% import rate):')
            for file_path, expected, imported, completion in files_with_issues:
                self.stdout.write(f'  {file_path.name}: {completion:.1f}% - Missing {expected - imported:,} rows')
                
                # Sample what's being skipped
                self.stdout.write('    Sample skipped rows:')
                self.analyze_skipped_rows(file_path, expected, imported)
        else:
            self.stdout.write('')
            self.stdout.write('✓ All files imported successfully (>90% completion rate)')
        
        # Recommend actions
        self.stdout.write('')
        self.stdout.write('RECOMMENDATIONS:')
        if overall_completion < 95:
            self.stdout.write('1. Check import logic for overly strict filtering')
            self.stdout.write('2. Verify CSV file formats and encoding')
            self.stdout.write('3. Consider separate importers for different formats')
        else:
            self.stdout.write('✓ Import appears complete and accurate')

    def count_csv_rows(self, csv_file):
        """Count actual data rows in CSV file"""
        try:
            encoding = self.detect_encoding(csv_file)
            with open(csv_file, 'r', encoding=encoding, errors='ignore') as f:
                # Count lines minus header
                return sum(1 for _ in f) - 1
        except Exception as e:
            self.stdout.write(f'Error counting rows in {csv_file.name}: {e}')
            return 0

    def count_imported_rows(self, csv_file, label):
        """Count imported rows from this file"""
        try:
            file_path = str(csv_file.relative_to(csv_file.parents[4]))
            source_files = SourceFile.objects.filter(label=label, path__contains=csv_file.name)
            
            if source_files.exists():
                return RevenueEvent.objects.filter(source_file__in=source_files).count()
            else:
                return 0
        except:
            return 0

    def count_imported_bandcamp(self, csv_file, label):
        """Count imported Bandcamp records"""
        try:
            source_files = SourceFile.objects.filter(
                label=label, 
                datasource__name='bandcamp'
            )
            return RevenueEvent.objects.filter(source_file__in=source_files).count()
        except:
            return 0

    def analyze_skipped_rows(self, csv_file, expected, imported):
        """Show sample of what rows are being skipped"""
        try:
            encoding = self.detect_encoding(csv_file)
            delimiter = ';' if 'Period' in open(csv_file, 'r', encoding=encoding, errors='ignore').readline() else ','
            
            with open(csv_file, 'r', encoding=encoding, errors='ignore') as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                
                # Show first few rows that might be skipped
                for i, row in enumerate(reader):
                    if i >= 3:  # Just show first 3
                        break
                    
                    first_col = next(iter(row.values()), '')
                    if not str(first_col or '').strip():
                        self.stdout.write(f'      Empty row: {dict(list(row.items())[:3])}')
                    else:
                        # Show sample of what might be valid but skipped
                        sample_data = {k: v for k, v in list(row.items())[:3] if v}
                        self.stdout.write(f'      Sample row: {sample_data}')
                        
        except Exception as e:
            self.stdout.write(f'      Error analyzing: {e}')

    def detect_encoding(self, file_path):
        """Detect file encoding"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(200000)
            result = chardet.detect(raw_data)
            return result.get('encoding', 'utf-8') or 'utf-8'
        except:
            return 'utf-8'
