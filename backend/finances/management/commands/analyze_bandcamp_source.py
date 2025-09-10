import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from collections import defaultdict


class Command(BaseCommand):
    help = 'Analyze Bandcamp source to find where revenue is hiding'

    def handle(self, *args, **options):
        repo_root = Path(__file__).resolve().parents[4]
        canonical_file = repo_root / "finance/sources/tropical-twista/bandcamp/canonical/bandcamp_all.csv"
        
        if not canonical_file.exists():
            self.stdout.write('Canonical file not found')
            return
        
        self.stdout.write('BANDCAMP CANONICAL FILE ANALYSIS:')
        self.stdout.write('=' * 50)
        
        item_types = defaultdict(int)
        revenue_by_type = defaultdict(float)
        total_revenue = 0
        
        with open(canonical_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                item_type = row.get('item type', '').strip()
                amount_str = row.get('amount you received', '').strip()
                
                # Count items by type
                item_types[item_type or 'BLANK'] += 1
                
                # Sum revenue by type
                try:
                    amount = float(amount_str.replace('$', '').replace(',', '')) if amount_str else 0
                    revenue_by_type[item_type or 'BLANK'] += amount
                    total_revenue += amount
                except:
                    pass
        
        self.stdout.write('ITEM TYPES AND REVENUE:')
        self.stdout.write('Type            | Count   | Revenue')
        self.stdout.write('-' * 40)
        
        for item_type in sorted(item_types.keys()):
            count = item_types[item_type]
            revenue = revenue_by_type[item_type]
            self.stdout.write(f'{item_type:15} | {count:6,} | ${revenue:8,.2f}')
        
        self.stdout.write('')
        self.stdout.write(f'TOTAL REVENUE: ${total_revenue:,.2f}')
        self.stdout.write('Expected: ~$29,744')
        
        if total_revenue > 25000:
            self.stdout.write('✓ Revenue is in the canonical file')
            self.stdout.write('Issue: Import filter is too strict')
        else:
            self.stdout.write('⚠️  Revenue missing from canonical file')
            self.stdout.write('Issue: Canonical processing problem')
        
        # Find the highest revenue type
        max_revenue_type = max(revenue_by_type.items(), key=lambda x: x[1])
        self.stdout.write('')
        self.stdout.write(f'HIGHEST REVENUE TYPE: "{max_revenue_type[0]}" (${max_revenue_type[1]:,.2f})')
        self.stdout.write('This is where most of your Bandcamp revenue comes from!')
