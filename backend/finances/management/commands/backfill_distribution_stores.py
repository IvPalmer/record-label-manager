import csv
from pathlib import Path
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from finances.models import SourceFile, RevenueEvent, Store, Platform


def normalize(s: str) -> str:
    if not s:
        return ''
    # Lowercase, strip, collapse spaces for robust matching
    return ' '.join(str(s).lower().strip().split())


class Command(BaseCommand):
    help = 'Backfill Store for Distribution revenue events by reading original CSVs (Labelworx/Zebralution)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Do not write to DB, just report')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        repo_root = Path(__file__).resolve().parents[4]

        # Only distribution sources that should have store info
        sourcefiles = SourceFile.objects.filter(datasource__name__in=['labelworx', 'zebralution'])
        total_events = 0
        updated_events = 0

        for sf in sourcefiles:
            # Resolve stored path; handle cases where historical imports didn't include the 'finance/' prefix
            csv_path = (repo_root / sf.path).resolve()
            if not csv_path.exists():
                alt_path = (repo_root / 'finance' / sf.path).resolve()
                if alt_path.exists():
                    csv_path = alt_path
                else:
                    self.stdout.write(self.style.WARNING(f"Missing file for SourceFile {sf.id}: {csv_path}"))
                    continue

            if sf.datasource.name == 'labelworx':
                mapping = self._build_labelworx_mapping(csv_path)
            elif sf.datasource.name == 'zebralution':
                mapping = self._build_zebralution_mapping(csv_path)
            else:
                continue

            dist_platform = Platform.objects.get(name='Distribution')

            # Query events for this sourcefile without store set
            events_qs = RevenueEvent.objects.filter(source_file=sf, platform=dist_platform, store__isnull=True)
            total_events += events_qs.count()

            with transaction.atomic():
                for ev in events_qs.iterator(chunk_size=1000):
                    key = (
                        normalize(ev.isrc),
                        normalize(ev.track_title),
                        normalize(ev.track_artist_name),
                    )
                    store_name = mapping.get(key)
                    if not store_name:
                        # Try with ISRC only fallback
                        store_name = mapping.get((normalize(ev.isrc), '', ''))
                    if not store_name:
                        continue
                    store_obj, _ = Store.objects.get_or_create(platform=dist_platform, name=store_name)
                    if not dry_run:
                        ev.store = store_obj
                        ev.save(update_fields=['store'])
                    updated_events += 1

            self.stdout.write(f"Processed SourceFile {sf.id} ({sf.datasource.name}) - updated {updated_events} so far")

        self.stdout.write(self.style.SUCCESS(f"Backfill complete. Examined {total_events} events, updated {updated_events}."))

    def _build_labelworx_mapping(self, csv_path: Path):
        mapping = {}
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for row in reader:
                isrc = normalize(row.get('ISRC', ''))
                title = normalize(row.get('Track Title', ''))
                artist = normalize(row.get('Track Artist', ''))
                store = row.get('Store Name', '')
                if not store:
                    continue
                key = (isrc, title, artist)
                mapping[key] = store
                if isrc and (isrc, '', '') not in mapping:
                    mapping[(isrc, '', '')] = store
        return mapping

    def _build_zebralution_mapping(self, csv_path: Path):
        mapping = {}
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                isrc = normalize(row.get('ISRC', ''))
                title = normalize(row.get('Title', ''))
                artist = normalize(row.get('Artist', ''))
                store = row.get('Shop', '') or row.get('Provider', '')
                if not store:
                    continue
                key = (isrc, title, artist)
                mapping[key] = store
                if isrc and (isrc, '', '') not in mapping:
                    mapping[(isrc, '', '')] = store
        return mapping


