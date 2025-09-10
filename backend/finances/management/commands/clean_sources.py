import csv
import re
from pathlib import Path
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Clean source CSV files by removing blank rows, summaries, and exchange rates'

    def handle(self, *args, **options):
        repo_root = Path(__file__).resolve().parents[4]
        sources_root = repo_root / "finance" / "sources" / "tropical-twista"
        
        total_original = 0
        total_cleaned = 0
        
        self.stdout.write('CLEANING SOURCE FILES:')
        self.stdout.write('Removing: blank rows, summary lines, exchange rates, totals')
        self.stdout.write('')
        
        # Clean Distribution files
        distribution_dir = sources_root / "distribution"
        for quarter_dir in sorted(distribution_dir.iterdir()):
            if quarter_dir.is_dir():
                for csv_file in quarter_dir.glob("*.csv"):
                    original, cleaned = self.clean_distribution_file(csv_file)
                    total_original += original
                    total_cleaned += cleaned
                    
                    saved = original - cleaned
                    percentage = (cleaned / original * 100) if original > 0 else 0
                    self.stdout.write(f'{quarter_dir.name}: {cleaned:,}/{original:,} ({percentage:.1f}%) - removed {saved:,} invalid rows')
        
        # Clean Bandcamp file
        bandcamp_file = sources_root / "bandcamp" / "20000101-20250729_bandcamp_raw_data_Tropical-Twista-Records.csv"
        if bandcamp_file.exists():
            original, cleaned = self.clean_bandcamp_file(bandcamp_file)
            total_original += original
            total_cleaned += cleaned
            
            saved = original - cleaned
            percentage = (cleaned / original * 100) if original > 0 else 0
            self.stdout.write(f'Bandcamp: {cleaned:,}/{original:,} ({percentage:.1f}%) - removed {saved:,} invalid rows')
        
        self.stdout.write('')
        self.stdout.write(f'OVERALL: {total_cleaned:,}/{total_original:,} ({(total_cleaned/total_original*100):.1f}%)')
        self.stdout.write(f'Removed {total_original - total_cleaned:,} invalid rows')

    def clean_distribution_file(self, csv_file):
        """Clean distribution CSV file"""
        # Detect format
        file_format = self.detect_format(csv_file)
        delimiter = ';' if file_format == 'zebralution' else ','
        
        # Read original
        original_rows = []
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            headers = reader.fieldnames
            for row in reader:
                original_rows.append(row)
        
        # Filter valid rows
        valid_rows = []
        for row in original_rows:
            if self.is_valid_distribution_row(row):
                valid_rows.append(row)
        
        # Write cleaned file
        backup_file = csv_file.with_suffix('.backup.csv')
        csv_file.rename(backup_file)  # Backup original
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if valid_rows:
                writer = csv.DictWriter(f, fieldnames=headers, delimiter=delimiter)
                writer.writeheader()
                writer.writerows(valid_rows)
        
        return len(original_rows), len(valid_rows)

    def clean_bandcamp_file(self, csv_file):
        """Clean Bandcamp CSV file"""
        # Read original
        original_rows = []
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            for row in reader:
                original_rows.append(row)
        
        # Filter valid rows
        valid_rows = []
        for row in original_rows:
            if self.is_valid_bandcamp_row(row):
                valid_rows.append(row)
        
        # Write cleaned file
        backup_file = csv_file.with_suffix('.backup.csv')
        csv_file.rename(backup_file)  # Backup original
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if valid_rows:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(valid_rows)
        
        return len(original_rows), len(valid_rows)

    def is_valid_distribution_row(self, row):
        """Check if distribution row contains valid transaction data"""
        # Get all row values as text
        values = [str(v or '').strip() for v in row.values()]
        
        # Skip completely empty rows
        if not any(values):
            return False
        
        # Skip rows that are clearly summaries/totals
        row_text = ' '.join(values).upper()
        
        skip_patterns = [
            'EXCHANGE RATE',
            'TOTAL',
            'SUM',
            'CURRENCY',
            'GBP',
            'USD',
            'EUR',
            '€',
            '$',
            '£'
        ]
        
        # Skip if it contains summary keywords and has few fields
        for pattern in skip_patterns:
            if pattern in row_text and len([v for v in values if v]) < 8:
                return False
        
        # For Zebralution: must have Artist and Title
        if ';' in str(row):
            artist = (row.get('Artist', '') or '').strip()
            title = (row.get('Title', '') or '').strip()
            if not artist or not title:
                return False
        
        # For Labelworx: must have Track Artist and Track Title
        else:
            track_artist = (row.get('Track Artist', '') or '').strip()
            track_title = (row.get('Track Title', '') or '').strip()
            sale_type = (row.get('Sale Type', '') or '').strip()
            
            # Must be a Track transaction with artist/title
            if sale_type != 'Track' or not track_artist or not track_title:
                return False
            
            # Skip exchange rate rows
            isrc = (row.get('ISRC', '') or '').strip()
            if 'Exchange' in isrc or 'exchange' in track_title.lower():
                return False
        
        return True

    def is_valid_bandcamp_row(self, row):
        """Check if Bandcamp row contains valid transaction data"""
        # Get all row values
        values = [str(v or '').strip() for v in row.values()]
        
        # Skip completely empty rows  
        if not any(values):
            return False
        
        # Must have date
        date_str = (row.get('date', '') or '').strip()
        if not date_str:
            return False
        
        # Must have item name
        item_name = (row.get('item name', '') or '').strip()
        if not item_name:
            return False
        
        # Skip admin transactions
        row_text = ' '.join(values).upper()
        if any(keyword in row_text for keyword in ['PAYOUT', 'PAYMENT', 'TRANSFER', 'ADMIN']):
            return False
        
        # Skip if paid to is not an email (these are usually payouts/admin)
        paid_to = (row.get('paid to', '') or '').strip()
        if paid_to and '@' not in paid_to and 'bandcamp' not in paid_to.lower():
            return False
        
        return True

    def detect_format(self, csv_file):
        """Detect if file is Zebralution or Labelworx"""
        try:
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline()
                if ';' in first_line and 'Period' in first_line:
                    return 'zebralution'
        except:
            pass
        return 'labelworx'
