from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Build staging.distribution_event from raw.zebralution_event_raw and raw.labelworx_event_raw'

    def handle(self, *args, **options):
        with connection.cursor() as cur:
            # Ensure staging table exists
            cur.execute(
                """
                CREATE SCHEMA IF NOT EXISTS staging;
                CREATE TABLE IF NOT EXISTS staging.distribution_event (
                  id BIGSERIAL PRIMARY KEY,
                  occurred_at timestamp NULL,
                  platform text NOT NULL,
                  store text NULL,
                  track_artist_name text NULL,
                  track_title text NULL,
                  isrc text NULL,
                  upc_ean text NULL,
                  catalog_number text NULL,
                  quantity integer DEFAULT 0,
                  gross_amount_eur numeric(18,6) DEFAULT 0,
                  net_amount_eur numeric(18,6) DEFAULT 0
                )
                """
            )

            # Clear staging
            cur.execute("TRUNCATE TABLE staging.distribution_event")

            # Rebuild from normalized finances_revenueevent to guarantee correct dates
            cur.execute(
                """
                INSERT INTO staging.distribution_event (
                  occurred_at, platform, store, track_artist_name, track_title, isrc, upc_ean, catalog_number,
                  quantity, gross_amount_eur, net_amount_eur
                )
                SELECT 
                  rev.occurred_at,
                  'Distribution',
                  s.name,
                  rev.track_artist_name,
                  rev.track_title,
                  rev.isrc,
                  rev.upc_ean,
                  rev.catalog_number,
                  rev.quantity,
                  rev.gross_amount,
                  rev.net_amount_base
                FROM finances_revenueevent rev
                JOIN finances_platform p ON rev.platform_id = p.id
                LEFT JOIN finances_store s ON rev.store_id = s.id
                WHERE p.name = 'Distribution'
                """
            )

        self.stdout.write(self.style.SUCCESS('Staging distribution built'))


