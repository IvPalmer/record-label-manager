import csv
from pathlib import Path
from collections import Counter, defaultdict

from django.core.management.base import BaseCommand
from django.db.models import Count

from finances.models import RevenueEvent, SourceFile


class Command(BaseCommand):
    help = 'Audit that DB captures all relevant columns from source CSVs and report missing coverage'

    def handle(self, *args, **options):
        repo_root = Path(__file__).resolve().parents[4]

        report = {
            'labelworx': self.audit_labelworx(repo_root),
            'zebralution': self.audit_zebralution(repo_root),
            'bandcamp': self.audit_bandcamp(repo_root),
        }

        # DB coverage stats
        db_stats = RevenueEvent.objects.aggregate(
            total=Count('id'),
        )
        nullable_counts = {
            'store_missing': RevenueEvent.objects.filter(platform__name='Distribution', store__isnull=True).count(),
            'isrc_missing': RevenueEvent.objects.filter(isrc='').count(),
            'catalog_missing': RevenueEvent.objects.filter(catalog_number='').count(),
            'artist_missing': RevenueEvent.objects.filter(track_artist_name='').count(),
            'title_missing': RevenueEvent.objects.filter(track_title='').count(),
        }

        self.stdout.write('DB COVERAGE:')
        self.stdout.write(str({**db_stats, **nullable_counts}))
        self.stdout.write('\nSOURCE FIELD AUDIT:')
        for k, v in report.items():
            self.stdout.write(f"\n== {k.upper()} ==")
            for key, val in v.items():
                self.stdout.write(f"{key}: {val}")

    def audit_labelworx(self, repo_root: Path):
        info = {}
        files = list((repo_root / 'finance' / 'sources' / 'tropical-twista' / 'distribution').glob('**/*Labelworx*'))
        # Fall back to known folder patterns
        if not files:
            files = list((repo_root / 'finance' / 'sources' / 'tropical-twista' / 'distribution').glob('**/*__converted.csv'))
        required = ['Store Name', 'Track Artist', 'Track Title', 'ISRC', 'Catalog', 'Qty', 'Royalty', 'Value']
        present_counts = Counter()
        sample_row = {}
        for f in files[:5]:
            with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
                reader = csv.DictReader(fh)
                present_counts.update(set(reader.fieldnames or []))
                for row in reader:
                    sample_row = row
                    break
        info['required_fields_present'] = {k: (k in present_counts) for k in required}
        info['sample_row'] = {k: sample_row.get(k) for k in required if sample_row}
        return info

    def audit_zebralution(self, repo_root: Path):
        info = {}
        files = list((repo_root / 'finance' / 'sources' / 'tropical-twista' / 'distribution').glob('**/*-1027_rs_*.csv'))
        required = ['Shop', 'Provider', 'Artist', 'Title', 'ISRC', 'Label Order-Nr', 'EAN', 'Sales', 'Revenue-EUR', 'Rev.less Publ.EUR', 'Country', 'Period']
        present_counts = Counter()
        sample_row = {}
        for f in files[:5]:
            with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
                reader = csv.DictReader(fh, delimiter=';')
                present_counts.update(set(reader.fieldnames or []))
                for row in reader:
                    sample_row = row
                    break
        info['required_fields_present'] = {k: (k in present_counts) for k in required}
        info['sample_row'] = {k: sample_row.get(k) for k in required if sample_row}
        return info

    def audit_bandcamp(self, repo_root: Path):
        info = {}
        files = list((repo_root / 'finance' / 'sources' / 'tropical-twista' / 'bandcamp').glob('**/*.csv'))
        required = ['date', 'item name', 'item total', 'amount you received', 'item type', 'artist', 'currency', 'quantity']
        present_counts = Counter()
        sample_row = {}
        for f in files[:1]:
            with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
                reader = csv.DictReader(fh)
                present_counts.update(set(reader.fieldnames or []))
                for row in reader:
                    sample_row = row
                    break
        info['required_fields_present'] = {k: (k in present_counts) for k in required}
        info['sample_row'] = {k: sample_row.get(k) for k in required if sample_row}
        return info


