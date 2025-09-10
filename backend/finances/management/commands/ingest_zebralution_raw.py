import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from finances.models_etl import RawZebralutionEvent


class Command(BaseCommand):
    help = 'Ingest Zebralution CSVs into raw.zebralution_event_raw (no transformations)'

    def add_arguments(self, parser):
        parser.add_argument('--root', type=str, required=True, help='Folder with Zebralution CSV files')
        parser.add_argument('--truncate', action='store_true', help='Truncate raw table before import')

    def handle(self, *args, **options):
        root = Path(options['root'])
        files = list(root.glob('**/*.csv'))

        # optional truncate
        from django.db import connection
        if options.get('truncate'):
            with connection.cursor() as cur:
                cur.execute('TRUNCATE TABLE raw.zebralution_event_raw')

        for f in files:
            # Only true Zebralution files: semicolon header containing 'Period'
            try:
                with open(f, 'r', encoding='utf-8', errors='ignore') as testfh:
                    header = testfh.readline()
                if ';' not in header or 'Period' not in header:
                    continue
            except Exception:
                continue

            with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
                reader = csv.DictReader(fh, delimiter=';')
                for row in reader:
                    RawZebralutionEvent.objects.create(
                        period=row.get('Period', ''),
                        shop=row.get('Shop', ''),
                        provider=row.get('Provider', ''),
                        artist=row.get('Artist', ''),
                        title=row.get('Title', ''),
                        isrc=row.get('ISRC', ''),
                        ean=row.get('EAN', ''),
                        label_order_nr=row.get('Label Order-Nr', ''),
                        country=row.get('Country', ''),
                        sales=int((row.get('Sales') or '0').replace(',', '.') or 0),
                        revenue_eur=(row.get('Revenue-EUR', '0').replace(',', '.') or 0),
                        rev_less_publ_eur=(row.get('Rev.less Publ.EUR', '0').replace(',', '.') or 0),
                        raw_row=row,
                    )
        self.stdout.write(self.style.SUCCESS('Zebralution raw ingest completed'))


