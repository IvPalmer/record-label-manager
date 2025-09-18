import csv
import hashlib
from pathlib import Path
from decimal import Decimal
from datetime import datetime, date

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from finances.models import Platform, Store, SourceFile, RevenueEvent, DataSource
from api.models import Label


class Command(BaseCommand):
    help = 'Rebuild Distribution RevenueEvent strictly from source spreadsheets (Labelworx + Zebralution) using exact store names.'

    def add_arguments(self, parser):
        parser.add_argument('--label', type=str, required=True, help='Label name (as in api.Label)')
        parser.add_argument('--root', type=str, required=False, default='', help='Root folder for sources (defaults to finance/sources/<label-slug>/distribution)')
        parser.add_argument('--dry-run', action='store_true', help='Scan and report without modifying the database')

    def handle(self, *args, **options):
        label_name = options['label']
        dry_run = options.get('dry_run', False)
        try:
            label = Label.objects.get(name=label_name)
        except Label.DoesNotExist:
            raise CommandError(f'Label "{label_name}" not found')

        platform, _ = Platform.objects.get_or_create(name='Distribution', defaults={'vendor_key': 'distribution'})

        repo_root = Path(__file__).resolve().parents[4]
        if options.get('root'):
            root = Path(options['root'])
        else:
            # infer directory: finance/sources/<something>/distribution
            # Use the tropical-twista dir if present
            default_dir = repo_root / 'finance' / 'sources'
            # pick the first subdir that contains 'distribution'
            candidates = list(default_dir.glob('**/distribution'))
            if not candidates:
                raise CommandError('Could not locate sources distribution folder; pass --root')
            root = candidates[0]

        if not root.exists():
            raise CommandError(f'Sources root not found: {root}')

        self.stdout.write(f'Using sources: {root}')

        # Wipe existing Distribution events for this label
        if not dry_run:
            deleted, _ = RevenueEvent.objects.filter(label=label, platform=platform).delete()
            self.stdout.write(f'Deleted {deleted} existing distribution events for {label_name}')

        total_rows = 0
        imported_rows = 0

        # Helpers
        def parse_decimal(value: str) -> Decimal:
            if value is None:
                return Decimal('0')
            s = str(value).replace('€', '').replace('$', '').strip()
            try:
                return Decimal(s)
            except Exception:
                try:
                    return Decimal(s.replace(',', '.'))
                except Exception:
                    try:
                        return Decimal(s.replace(',', ''))
                    except Exception:
                        return Decimal('0')

        # Datasource records for traceability
        lw_ds, _ = DataSource.objects.get_or_create(name='labelworx', defaults={'vendor': 'Labelworx'})
        zb_ds, _ = DataSource.objects.get_or_create(name='zebralution', defaults={'vendor': 'Zebralution'})

        # Walk CSVs
        for csv_path in sorted(root.glob('**/*.csv')):
            quarter_dir = csv_path.parent.name
            with open(csv_path, 'r', encoding='utf-8', errors='ignore') as fh:
                first = fh.readline()
            # Detect format by header
            is_zebralution = (';' in first and 'Period' in first)
            # Rewind and process
            with open(csv_path, 'r', encoding='utf-8', errors='ignore') as fh:
                if is_zebralution:
                    # Normalize header by stripping whitespace
                    header = [h.strip() for h in first.strip().split(';')]
                    fh.seek(0)
                    next(fh)  # skip header row
                    reader = csv.DictReader(fh, fieldnames=header, delimiter=';')
                    datasource = zb_ds
                else:
                    # Normalize header to avoid trailing spaces in 'Store Name'
                    header = [h.strip() for h in first.strip().split(',')]
                    fh.seek(0)
                    next(fh)  # skip header row
                    reader = csv.DictReader(fh, fieldnames=header)
                    datasource = lw_ds

                # Prepare SourceFile for this physical file
                if not dry_run:
                    source_file = SourceFile.objects.create(
                        datasource=datasource,
                        label=label,
                        path=str(csv_path.relative_to(repo_root)),
                        sha256='rebuild',
                        bytes=csv_path.stat().st_size,
                        mtime=timezone.make_aware(datetime.fromtimestamp(csv_path.stat().st_mtime)),
                        statement_type=datasource.name,
                        period_start=None,
                    )
                else:
                    source_file = None

                for row in reader:
                    total_rows += 1
                    try:
                        if is_zebralution:
                            # Use exact Shop from file; if empty, skip (no substitution with provider)
                            store_name = (row.get('Shop') or '').strip()
                            provider = (row.get('Provider') or '').strip()
                            if not store_name:
                                # Fallback: derive from provider only if it clearly matches a store brand
                                plower = provider.lower()
                                if any(k in plower for k in ['spotify', 'youtube', 'apple', 'itunes', 'tiktok', 'tidal', 'deezer', 'amazon', 'beatport', 'soundcloud', 'snap', 'instagram', 'facebook', 'qobuz', 'yandex', 'netease', 'juno', 'traxsource']):
                                    store_name = provider
                                else:
                                    store_name = '(unknown)'
                            # Use Period Sold for actual sale date, fallback to Period for reporting period
                            period_sold = row.get('Period Sold', '').strip()
                            period_reporting = row.get('Period', '').strip()
                            occurred_at = self._parse_month(period_sold or period_reporting)
                            qty = int((row.get('Sales') or '0').replace(',', '.')) if row.get('Sales') else 0
                            net_eur = parse_decimal(row.get('Rev.less Publ.EUR', '0'))
                            gross_eur = parse_decimal(row.get('Revenue-EUR', '0'))
                            artist = row.get('Artist', '')
                            title = row.get('Title', '')
                            isrc = row.get('ISRC', '')
                            catalog = row.get('Label Order-Nr', '')
                        else:
                            store_name = (row.get('Store Name') or '').strip()
                            if not store_name:
                                continue
                            # Labelworx quarter date from folder name like 2024-Q2
                            q_date = self._parse_quarter(quarter_dir)
                            occurred_at = q_date
                            qty = int(row.get('Qty', '0') or '0')
                            net_eur = parse_decimal(row.get('Royalty', '0'))
                            gross_eur = parse_decimal(row.get('Value', '0'))
                            artist = row.get('Track Artist', '')
                            title = row.get('Track Title', '')
                            isrc = row.get('ISRC', '')
                            catalog = row.get('Catalog', '')

                        if occurred_at is None:
                            continue

                        # Create Store with exact name from spreadsheet
                        store_obj, _ = Store.objects.get_or_create(platform=platform, name=store_name)

                        # Skip completely empty money rows
                        if net_eur == 0 and gross_eur == 0:
                            continue

                        if not dry_run:
                            # Ensure row_hash fits in 64 chars by hashing the identifying tuple
                            hash_input = f"rebuild|{datasource.name}|{csv_path.name}|{total_rows}".encode('utf-8', 'ignore')
                            row_hash = hashlib.sha256(hash_input).hexdigest()
                            RevenueEvent.objects.create(
                                source_file=source_file,
                                label=label,
                                occurred_at=timezone.make_aware(datetime(occurred_at.year, occurred_at.month, getattr(occurred_at, 'day', 1))),
                                platform=platform,
                                store=store_obj,
                                currency='EUR',
                                product_type='digital',
                                quantity=qty,
                                gross_amount=gross_eur,
                                net_amount=net_eur,
                                net_amount_base=net_eur,
                                base_ccy='EUR',
                                track_artist_name=artist,
                                track_title=title,
                                catalog_number=catalog,
                                isrc=isrc,
                                row_hash=row_hash
                            )
                        imported_rows += 1
                    except Exception:
                        continue

        self.stdout.write(f'Scanned rows: {total_rows}, imported: {imported_rows}')

    def _parse_month(self, period_str: str):
        try:
            # Expect formats like YYYY-MM
            parts = str(period_str).strip().split('-')
            if len(parts) == 2:
                y, m = int(parts[0]), int(parts[1])
                return date(y, m, 1)
        except Exception:
            return None
        return None

    def _parse_quarter(self, folder_name: str):
        # Expect "YYYY-QN"
        try:
            if '-' in folder_name and folder_name.upper().startswith('20'):
                y, q = folder_name.split('-')
                y = int(y)
                q = int(q.replace('Q', '').replace('q', ''))
                month = (q - 1) * 3 + 1
                return date(y, month, 1)
        except Exception:
            return None
        return None


