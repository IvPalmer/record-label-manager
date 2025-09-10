import csv
from pathlib import Path
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Debug why import is rejecting most rows'

    def handle(self, *args, **options):
        repo_root = Path(__file__).resolve().parents[4]
        
        # Check 2023-Q2 (the 1M+ row file)
        q2_file = repo_root / "finance/sources/tropical-twista/distribution/2023-Q2/Tropical Twista Records Q2 2023__converted.csv"
        
        self.stdout.write('DEBUGGING 2023-Q2 FILE:')
        
        total_rows = 0
        track_rows = 0
        with_artist = 0
        with_title = 0
        with_isrc = 0
        empty_royalty = 0
        zero_royalty = 0
        valid_complete = 0
        
        with open(q2_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total_rows += 1
                
                sale_type = row.get('Sale Type', '').strip()
                track_artist = row.get('Track Artist', '').strip()
                track_title = row.get('Track Title', '').strip()
                isrc = row.get('ISRC', '').strip()
                royalty = row.get('Royalty', '').strip()
                
                if sale_type == 'Track':
                    track_rows += 1
                    
                if track_artist:
                    with_artist += 1
                    
                if track_title:
                    with_title += 1
                    
                if isrc:
                    with_isrc += 1
                    
                if not royalty:
                    empty_royalty += 1
                elif royalty == '0' or royalty == '0.0':
                    zero_royalty += 1
                
                # Count rows that would pass current strict filtering
                if (sale_type == 'Track' and track_artist and track_title and isrc and 
                    'Exchange' not in isrc and royalty and float(royalty or '0') > 0):
                    valid_complete += 1
                
                if total_rows >= 10000:  # Sample first 10k for speed
                    break
        
        self.stdout.write(f'Sample of {total_rows:,} rows:')
        self.stdout.write(f'  Sale Type = "Track": {track_rows:,} ({track_rows/total_rows*100:.1f}%)')
        self.stdout.write(f'  Has Track Artist: {with_artist:,} ({with_artist/total_rows*100:.1f}%)')
        self.stdout.write(f'  Has Track Title: {with_title:,} ({with_title/total_rows*100:.1f}%)')
        self.stdout.write(f'  Has ISRC: {with_isrc:,} ({with_isrc/total_rows*100:.1f}%)')
        self.stdout.write(f'  Empty Royalty: {empty_royalty:,} ({empty_royalty/total_rows*100:.1f}%)')
        self.stdout.write(f'  Zero Royalty: {zero_royalty:,} ({zero_royalty/total_rows*100:.1f}%)')
        self.stdout.write(f'  Would pass strict filter: {valid_complete:,} ({valid_complete/total_rows*100:.1f}%)')
        
        # Check Bandcamp
        self.stdout.write('')
        self.stdout.write('DEBUGGING BANDCAMP:')
        bandcamp_file = repo_root / "finance/sources/tropical-twista/bandcamp/20000101-20250729_bandcamp_raw_data_Tropical-Twista-Records.csv"
        
        total_bc = 0
        with_date = 0
        with_amount = 0
        valid_amount = 0
        
        with open(bandcamp_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total_bc += 1
                
                date_str = row.get('date', '').strip()
                amount_str = row.get('amount you received', '').strip()
                
                if date_str:
                    with_date += 1
                if amount_str:
                    with_amount += 1
                    try:
                        amount = float(amount_str.replace('$', '').replace('€', ''))
                        if amount >= 0:  # Include zero amounts
                            valid_amount += 1
                    except:
                        pass
                
                if total_bc >= 1000:  # Sample first 1k
                    break
        
        self.stdout.write(f'Sample of {total_bc:,} rows:')
        self.stdout.write(f'  Has date: {with_date:,} ({with_date/total_bc*100:.1f}%)')
        self.stdout.write(f'  Has amount field: {with_amount:,} ({with_amount/total_bc*100:.1f}%)')
        self.stdout.write(f'  Valid amounts (>=0): {valid_amount:,} ({valid_amount/total_bc*100:.1f}%)')
        
        self.stdout.write('')
        self.stdout.write('RECOMMENDATIONS:')
        self.stdout.write('1. Remove ISRC requirement (many valid tracks missing ISRC)')
        self.stdout.write('2. Accept zero amounts (valid $0 transactions)')
        self.stdout.write('3. Fix Bandcamp date parsing')
        self.stdout.write('4. Accept rows with partial data (artist OR title)')
