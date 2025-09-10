import csv
import re
from pathlib import Path
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Strict cleaning - only keep rows with valid track data, remove all totals/summaries'

    def handle(self, *args, **options):
        repo_root = Path(__file__).resolve().parents[4]
        sources_root = repo_root / "finance" / "sources" / "tropical-twista"
        
        self.stdout.write('STRICT SOURCE CLEANING:')
        self.stdout.write('Only keeping rows with complete track information')
        self.stdout.write('')
        
        # Clean Distribution files
        distribution_dir = sources_root / "distribution"
        for quarter_dir in sorted(distribution_dir.iterdir()):
            if quarter_dir.is_dir():
                for csv_file in quarter_dir.glob("*.csv"):
                    if '.backup.csv' in csv_file.name:
                        continue
                    
                    original, cleaned = self.strict_clean_distribution(csv_file)
                    percentage = (cleaned / original * 100) if original > 0 else 0
                    self.stdout.write(f'{quarter_dir.name}: {cleaned:,}/{original:,} ({percentage:.1f}%)')
        
        # Clean Bandcamp
        bandcamp_file = sources_root / "bandcamp" / "20000101-20250729_bandcamp_raw_data_Tropical-Twista-Records.csv"
        if bandcamp_file.exists() and '.backup.csv' not in bandcamp_file.name:
            original, cleaned = self.strict_clean_bandcamp(bandcamp_file)
            percentage = (cleaned / original * 100) if original > 0 else 0
            self.stdout.write(f'Bandcamp: {cleaned:,}/{original:,} ({percentage:.1f}%)')

    def strict_clean_distribution(self, csv_file):
        """Ultra strict distribution cleaning"""
        file_format = self.detect_format(csv_file)
        delimiter = ';' if file_format == 'zebralution' else ','
        
        # Read all rows first
        all_rows = []
        headers = None
        
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            headers = reader.fieldnames
            for row in reader:
                all_rows.append(row)
        
        original_count = len(all_rows)
        
        # Find where real data ends (before totals/summaries)
        valid_rows = []
        
        for i, row in enumerate(all_rows):
            # Stop processing at first sign of summary data
            if self.is_summary_row(row, file_format):
                self.stdout.write(f'  Stopping at row {i+1} (found summary data)')
                break
            
            # Only keep rows with complete track data
            if self.has_complete_track_data(row, file_format):
                valid_rows.append(row)
        
        # Write cleaned file
        backup_file = csv_file.with_suffix('.backup.csv')
        if not backup_file.exists():
            csv_file.rename(backup_file)  # Backup original only once
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                if valid_rows:
                    writer = csv.DictWriter(f, fieldnames=headers, delimiter=delimiter)
                    writer.writeheader()
                    writer.writerows(valid_rows)
        
        return original_count, len(valid_rows)

    def strict_clean_bandcamp(self, csv_file):
        """Ultra strict Bandcamp cleaning"""
        all_rows = []
        headers = None
        
        # Try different encodings for Bandcamp
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(csv_file, 'r', encoding=encoding, errors='ignore') as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames
                    all_rows = list(reader)
                break
            except:
                continue
        
        original_count = len(all_rows)
        
        # Only keep valid sales transactions
        valid_rows = []
        
        for row in all_rows:
            if self.is_valid_bandcamp_transaction(row):
                valid_rows.append(row)
        
        # Write cleaned file
        backup_file = csv_file.with_suffix('.backup.csv')
        if not backup_file.exists():
            csv_file.rename(backup_file)
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                if valid_rows:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(valid_rows)
        
        return original_count, len(valid_rows)

    def is_summary_row(self, row, file_format):
        """Detect summary/total rows that appear at end of spreadsheets"""
        values = [str(v or '').strip() for v in row.values()]
        row_text = ' '.join(values).upper()
        
        # Common summary patterns
        summary_indicators = [
            'TOTAL',
            'SUM',
            'SUBTOTAL', 
            'GRAND TOTAL',
            'EXCHANGE RATE',
            'CURRENCY',
            'GBP',
            'USD TOTAL',
            'EUR TOTAL',
            '€',
            '$',
            '£'
        ]
        
        # Check if row contains summary indicators
        for indicator in summary_indicators:
            if indicator in row_text:
                return True
        
        # Check for number-only rows (common at end of spreadsheets)
        non_empty_values = [v for v in values if v]
        if len(non_empty_values) <= 3 and all(self.is_number_like(v) for v in non_empty_values):
            return True
        
        # For Zebralution: if no Artist/Title, it's likely a summary
        if file_format == 'zebralution':
            artist = (row.get('Artist', '') or '').strip()
            title = (row.get('Title', '') or '').strip()
            if not artist and not title:
                return True
        
        # For Labelworx: if no Track Artist/Title or wrong Sale Type
        else:
            sale_type = (row.get('Sale Type', '') or '').strip()
            track_artist = (row.get('Track Artist', '') or '').strip()
            track_title = (row.get('Track Title', '') or '').strip()
            
            if sale_type != 'Track' or not track_artist or not track_title:
                return True
        
        return False

    def has_complete_track_data(self, row, file_format):
        """Check if row has complete track information"""
        if file_format == 'zebralution':
            artist = (row.get('Artist', '') or '').strip()
            title = (row.get('Title', '') or '').strip()
            period = (row.get('Period', '') or '').strip()
            
            # Must have artist, title, and valid period
            return (artist and title and period and 
                    re.match(r'20\d{2}-\d{2}', period))
        
        else:  # Labelworx
            track_artist = (row.get('Track Artist', '') or '').strip()
            track_title = (row.get('Track Title', '') or '').strip()
            sale_type = (row.get('Sale Type', '') or '').strip()
            isrc = (row.get('ISRC', '') or '').strip()
            
            # Must have track info, be a Track type, and not be exchange data
            return (track_artist and track_title and 
                    sale_type == 'Track' and
                    'Exchange' not in (isrc or ''))

    def is_valid_bandcamp_transaction(self, row):
        """Check if Bandcamp row is a real sales transaction"""
        date_str = (row.get('date', '') or '').strip()
        item_name = (row.get('item name', '') or '').strip()
        paid_to = (row.get('paid to', '') or '').strip()
        item_type = (row.get('item type', '') or '').strip()
        
        # Must have date and item
        if not date_str or not item_name:
            return False
        
        # Must be a real sale (not payout/admin)
        if not item_type or item_type.lower() in ['payout', 'payment', 'transfer']:
            return False
        
        # Skip admin transactions (paid to non-email addresses usually)
        if paid_to and '@' not in paid_to and 'bandcamp' not in paid_to.lower():
            return False
        
        # Skip if item name suggests admin activity
        if any(word in item_name.lower() for word in ['payout', 'payment', 'admin', 'total', 'balance']):
            return False
        
        return True

    def is_number_like(self, value):
        """Check if value looks like a number"""
        try:
            float(value.replace(',', '.').replace('€', '').replace('$', '').replace('£', ''))
            return True
        except:
            return False

    def detect_format(self, csv_file):
        try:
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline()
                if ';' in first_line and 'Period' in first_line:
                    return 'zebralution'
        except:
            pass
        return 'labelworx'
