import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from finances.models_etl import RawLabelworxEvent


class Command(BaseCommand):
    help = 'Ingest Labelworx CSVs into raw.labelworx_event_raw (no transformations)'

    def add_arguments(self, parser):
        parser.add_argument('--root', type=str, required=True, help='Folder with Labelworx CSV files')
        parser.add_argument('--batch-size', type=int, default=1000)
        parser.add_argument('--max-files', type=int, default=0, help='Limit number of files (0 = no limit)')

    def handle(self, *args, **options):
        root = Path(options['root'])
        files = sorted(root.glob('**/*.csv'))
        max_files = options.get('max_files') if 'max_files' in options else options.get('max-files')
        if max_files and max_files > 0:
            files = files[: max_files]

        file_idx = 0
        for f in files:
            file_idx += 1
            # Pre-count rows for progress
            try:
                total = max(0, sum(1 for _ in open(f, 'r', encoding='utf-8', errors='ignore')) - 1)
            except Exception:
                total = 0
            processed = 0
            buffer = []
            batch_size = options.get('batch_size') if 'batch_size' in options else options.get('batch-size', 1000)
            self.stdout.write(f"[Labelworx {file_idx}/{len(files)}] {f.name} - {total} rows")
            with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    processed += 1
                    try:
                        buffer.append(
                            RawLabelworxEvent(
                                store_name=row.get('Store Name', ''),
                                track_artist=row.get('Track Artist', ''),
                                track_title=row.get('Track Title', ''),
                                isrc=row.get('ISRC', ''),
                                catalog=row.get('Catalog', ''),
                                qty=int(row.get('Qty', '0') or 0),
                                royalty=row.get('Royalty', '0') or 0,
                                value=row.get('Value', '0') or 0,
                                format=row.get('Format', ''),
                                raw_row=row,
                            )
                        )
                        if len(buffer) >= batch_size:
                            RawLabelworxEvent.objects.bulk_create(buffer, batch_size=batch_size)
                            buffer.clear()
                    except Exception:
                        # Skip bad row, continue
                        continue
                    if processed % max(1, batch_size * 2) == 0 and total:
                        pct = processed * 100.0 / total
                        self.stdout.write(f"  {processed}/{total} ({pct:.1f}%)", ending='\r')
                        self.stdout.flush()
                if buffer:
                    RawLabelworxEvent.objects.bulk_create(buffer, batch_size=batch_size)
            self.stdout.write("")
        self.stdout.write(self.style.SUCCESS('Labelworx raw ingest completed'))


