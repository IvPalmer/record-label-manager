import logging
from datetime import datetime, timedelta
from decimal import Decimal
from dateutil import parser as dateutil_parser
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction

from finances.models import Platform, DataSource, SourceFile, RevenueEvent
from finances.services.bandcamp_curl_client import BandcampCurlAPI, BandcampCurlAPIError
from api.models import Label

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetch Bandcamp sales data via API instead of CSV import'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            default=None,
            help='Start date for data fetch (YYYY-MM-DD). Defaults to 1 year ago.'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            default=None,
            help='End date for data fetch (YYYY-MM-DD). Defaults to today.'
        )
        parser.add_argument(
            '--band-id',
            type=int,
            default=None,
            help='Specific band ID to fetch. If not provided, will fetch from all available bands.'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing Bandcamp data before importing new data'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )
        parser.add_argument(
            '--label-name',
            type=str,
            default='Tropical Twista Records',
            help='Label name to associate with the imported data'
        )

    def handle(self, *args, **options):
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        
        # Get or validate label
        try:
            label = Label.objects.get(name=options['label_name'])
        except Label.DoesNotExist:
            raise CommandError(f"Label '{options['label_name']}' not found")

        # Set default date range
        end_date = options['end_date'] or datetime.now().strftime('%Y-%m-%d')
        start_date = options['start_date'] or (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        self.stdout.write(f"Fetching Bandcamp data from {start_date} to {end_date}")

        # Initialize Bandcamp API (using curl client)
        try:
            api = BandcampCurlAPI()
        except ValueError as e:
            raise CommandError(f"API configuration error: {e}")

        # Clear existing data if requested
        if options['clear_existing']:
            if options['dry_run']:
                self.stdout.write("DRY RUN: Would clear existing Bandcamp data")
            else:
                self.stdout.write('Clearing existing Bandcamp data...')
                RevenueEvent.objects.filter(platform__name='Bandcamp').delete()
                self.stdout.write(self.style.SUCCESS('Existing Bandcamp data cleared'))

        # Get bands to fetch from
        bands_to_fetch = []
        if options['band_id']:
            bands_to_fetch = [{'id': options['band_id'], 'name': f'Band {options["band_id"]}'}]
        else:
            bands_data = api.get_my_bands()
            if not bands_data:
                raise CommandError("Failed to fetch bands from Bandcamp API")
            bands_to_fetch = bands_data

        self.stdout.write(f"Found {len(bands_to_fetch)} band(s) to fetch data from")

        # Set up database objects
        platform, _ = Platform.objects.get_or_create(name='Bandcamp')
        datasource, _ = DataSource.objects.get_or_create(
            name='bandcamp_api',
            defaults={'vendor': 'Bandcamp API'}
        )

        total_imported = 0
        total_revenue = Decimal('0')
        total_skipped = 0

        # Fetch data for each band
        for band_info in bands_to_fetch:
            band_id = band_info.get('id')
            band_name = band_info.get('name', f'Band {band_id}')
            
            self.stdout.write(f"\nFetching data for band: {band_name} (ID: {band_id})")

            try:
                # Fetch sales data from API
                sales_data = api.get_sales_report(band_id, start_date, end_date)
                
                if not sales_data:
                    self.stdout.write(f"No sales data found for band {band_name}")
                    continue

                self.stdout.write(f"Retrieved {len(sales_data)} sales records")

                if options['dry_run']:
                    self.stdout.write("DRY RUN: Would import the following data:")
                    for i, record in enumerate(sales_data[:5]):  # Show first 5 records
                        self.stdout.write(f"  {i+1}. {record.get('item_name')} - {record.get('artist')} - ${record.get('amount_you_received', 0)}")
                    if len(sales_data) > 5:
                        self.stdout.write(f"  ... and {len(sales_data) - 5} more records")
                    continue

                # Create source file record
                source_file = SourceFile.objects.create(
                    datasource=datasource,
                    label=label,
                    path=f"api://bandcamp/band/{band_id}/{start_date}_{end_date}",
                    sha256=f"api_fetch_{timezone.now().timestamp()}",
                    bytes=len(str(sales_data)),
                    mtime=timezone.now(),
                    statement_type='api_fetch',
                    period_start=datetime.strptime(start_date, '%Y-%m-%d').date(),
                    period_end=datetime.strptime(end_date, '%Y-%m-%d').date()
                )

                # Process and import each sales record
                band_imported = 0
                band_revenue = Decimal('0')
                band_skipped = 0

                with transaction.atomic():
                    for record in sales_data:
                        try:
                            imported, revenue, skipped = self._process_sales_record(
                                record, source_file, label, platform
                            )
                            if imported:
                                band_imported += 1
                                band_revenue += revenue
                            else:
                                band_skipped += 1
                                
                        except Exception as e:
                            logger.error(f"Error processing record {record.get('unique_bc_id')}: {e}")
                            band_skipped += 1
                            continue

                self.stdout.write(
                    f"Band {band_name}: Imported {band_imported} records, "
                    f"${float(band_revenue):.2f} total, {band_skipped} skipped"
                )

                total_imported += band_imported
                total_revenue += band_revenue
                total_skipped += band_skipped

            except BandcampCurlAPIError as e:
                self.stdout.write(
                    self.style.ERROR(f"API error for band {band_name}: {e}")
                )
                continue
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Unexpected error for band {band_name}: {e}")
                )
                continue

        # Final summary
        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS("\nDRY RUN COMPLETED"))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\nBANDCAMP API IMPORT COMPLETED:\n"
                f"Total imported: {total_imported:,} records\n"
                f"Total revenue: ${float(total_revenue):,.2f}\n"
                f"Total skipped: {total_skipped:,}"
            ))

    def _process_sales_record(self, record, source_file, label, platform):
        """
        Process a single sales record and create RevenueEvent
        Returns (imported, revenue, skipped) counts
        """
        try:
            # Parse date
            date_str = record.get('date', '') or ''
            if isinstance(date_str, str):
                date_str = date_str.strip()
            if not date_str:
                return False, Decimal('0'), True
            
            occurred_at = self._parse_bandcamp_date(date_str)
            if not occurred_at:
                return False, Decimal('0'), True

            # Validate required fields
            item_name = (record.get('item_name', '') or '').strip()
            item_type = (record.get('item_type', '') or '').strip()
            
            if not item_name:
                return False, Decimal('0'), True

            # Only process music items
            if item_type.lower() not in ['album', 'track']:
                return False, Decimal('0'), True

            # Skip obvious non-music items
            if any(word in item_name.lower() for word in ['payout', 'payment', 'refund', 'shipping']):
                return False, Decimal('0'), True

            # Parse amounts
            net_amount = Decimal(str(record.get('amount_you_received', 0)))
            gross_amount = Decimal(str(record.get('item_total', 0)))
            
            # Convert to base currency (EUR) - using same rate as original import
            currency = record.get('currency', 'USD')
            base_rate = Decimal('0.85') if currency == 'USD' else Decimal('1.0')
            net_amount_base = net_amount * base_rate

            # Create unique row hash
            unique_id = record.get('unique_bc_id', '')
            row_hash = f"api:{unique_id}"[:64] if unique_id else f"api:{timezone.now().timestamp()}"

            # Create revenue event
            revenue_event = RevenueEvent.objects.create(
                source_file=source_file,
                label=label,
                occurred_at=occurred_at,
                platform=platform,
                currency=currency,
                product_type=item_type,
                quantity=int(record.get('quantity', 1)),
                gross_amount=gross_amount,
                net_amount=net_amount,
                net_amount_base=net_amount_base,
                base_ccy='EUR',
                track_artist_name=record.get('artist') or 'Various Artists',
                track_title=item_name,
                isrc=record.get('isrc') or '',
                upc_ean=record.get('upc') or '',
                catalog_number=record.get('catalog_number') or '',
                row_hash=row_hash
            )

            return True, net_amount_base, False

        except Exception as e:
            logger.error(f"Error processing sales record: {e}")
            return False, Decimal('0'), True

    def _parse_bandcamp_date(self, date_str):
        """
        Parse Bandcamp date string to Django timezone-aware datetime
        """
        try:
            # Use dateutil parser which handles many formats automatically
            dt = dateutil_parser.parse(date_str)
            
            # Ensure it's timezone-aware
            if dt.tzinfo is None:
                return timezone.make_aware(dt)
            else:
                return dt
                
        except Exception as e:
            logger.error(f"Error parsing date '{date_str}': {e}")
            
            # Fallback: try manual parsing for MM/DD/YYYY format
            try:
                date_part = date_str.split(' ')[0]
                parts = date_part.split('/')
                if len(parts) == 3:
                    month, day, year = parts
                    month, day = int(month), int(day)
                    year = int(year)
                    if year < 100:
                        year += 2000 if year < 50 else 1900
                    return timezone.make_aware(datetime(year, month, day))
            except:
                pass
        
        return None
