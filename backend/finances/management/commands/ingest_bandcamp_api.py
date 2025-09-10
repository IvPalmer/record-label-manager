from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from finances.services.bandcamp_curl_client import BandcampCurlAPI, BandcampCurlAPIError
from finances.models_etl import RawBandcampEvent
from dateutil import parser as dateparser


class Command(BaseCommand):
    help = 'Fetch Bandcamp sales via API and ingest into raw.bandcamp_event_raw (no CSVs)'

    def add_arguments(self, parser):
        parser.add_argument('--start', type=str, help='YYYY-MM-DD start date (default: 2016-01-01)')
        parser.add_argument('--end', type=str, help='YYYY-MM-DD end date (default: today)')

    def handle(self, *args, **options):
        start = options.get('start') or '2016-01-01'
        end = options.get('end') or timezone.now().date().isoformat()

        try:
            api = BandcampCurlAPI()
        except Exception as e:
            raise CommandError(f"Bandcamp API not configured: {e}")

        bands = api.get_my_bands()
        if not bands:
            raise CommandError('No Bandcamp band configured')

        band_id = int(bands[0]['id'])

        # Fetch in monthly windows to avoid API limits
        start_dt = datetime.strptime(start, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end, '%Y-%m-%d').date()

        cur = start_dt.replace(day=1)
        while cur <= end_dt:
            window_start = cur
            next_month = (cur.replace(day=28) + timedelta(days=4)).replace(day=1)
            window_end = min(end_dt, next_month - timedelta(days=1))

            self.stdout.write(f"Fetching {window_start} to {window_end}")
            try:
                rows = api.get_sales_report(band_id, window_start.isoformat(), window_end.isoformat())
            except BandcampCurlAPIError as e:
                self.stderr.write(self.style.ERROR(str(e)))
                rows = []

            # Upsert minimal fields into RAW
            for r in rows:
                # Parse date flexibly (e.g., '01 Feb 2016 13:23:00 GMT' or '2016-02-01')
                date_str = r.get('date') or window_start.isoformat()
                try:
                    dt = dateparser.parse(date_str)
                    if timezone.is_naive(dt):
                        occurred = timezone.make_aware(dt)
                    else:
                        occurred = dt.astimezone(timezone.get_current_timezone())
                except Exception:
                    occurred = timezone.make_aware(datetime.strptime(window_start.isoformat(), '%Y-%m-%d'))
                item_name = r.get('item_name') or ''
                artist = r.get('artist') or ''
                RawBandcampEvent.objects.update_or_create(
                    id=None,
                    defaults={
                        'date_str': date_str,
                        'occurred_at': occurred,
                        'item_name': item_name,
                        'item_type': r.get('item_type', ''),
                        'artist': artist,
                        'quantity': int(r.get('quantity') or 0),
                        'currency': r.get('currency', 'USD'),
                        'item_total': float(r.get('item_total') or 0),
                        'amount_received': float(r.get('amount_you_received') or 0),
                        'raw_row': r,
                    }
                )

            cur = next_month

        self.stdout.write(self.style.SUCCESS('Bandcamp API ingest completed'))


