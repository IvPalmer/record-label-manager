from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Populate dw.fact_revenue from raw.bandcamp_event_raw and staging.distribution_event'

    def handle(self, *args, **options):
        with connection.cursor() as cur:
            # Clear fact table
            cur.execute("TRUNCATE TABLE dw.fact_revenue")

            # Bandcamp (USD base)
            cur.execute(
                """
                INSERT INTO dw.fact_revenue (
                  occurred_at, source, platform, store, artist_name, track_title, isrc, catalog_number, upc_ean, quantity, revenue_base, base_ccy
                )
                SELECT 
                  DATE(occurred_at), 'bandcamp', 'Bandcamp', NULL,
                  artist, item_name, NULL, NULL, NULL,
                  quantity, amount_received, 'USD'
                FROM raw.bandcamp_event_raw
                WHERE item_type IN ('track','album','bundle')
                """
            )

            # Distribution (EUR base) from staging if available
            cur.execute("SELECT COUNT(*) FROM staging.distribution_event")
            staging_count = cur.fetchone()[0]
            if staging_count and staging_count > 0:
                cur.execute(
                    """
                    INSERT INTO dw.fact_revenue (
                      occurred_at, source, platform, store, artist_name, track_title, isrc, catalog_number, upc_ean, quantity, revenue_base, base_ccy
                    )
                    SELECT 
                      DATE(occurred_at), 'distribution', 'Distribution', store,
                      track_artist_name, track_title, isrc, catalog_number, upc_ean,
                      quantity, net_amount_eur, 'EUR'
                    FROM staging.distribution_event
                    """
                )
            else:
                # Fallback: build from normalized finances_revenueevent if staging is empty
                cur.execute(
                    """
                    INSERT INTO dw.fact_revenue (
                      occurred_at, source, platform, store, artist_name, track_title, isrc, catalog_number, upc_ean, quantity, revenue_base, base_ccy
                    )
                    SELECT 
                      DATE(rev.occurred_at) AS occurred_at,
                      'distribution' AS source,
                      'Distribution' AS platform,
                      s.name AS store,
                      rev.track_artist_name,
                      rev.track_title,
                      rev.isrc,
                      rev.catalog_number,
                      rev.upc_ean,
                      rev.quantity,
                      rev.net_amount_base,
                      rev.base_ccy
                    FROM finances_revenueevent rev
                    JOIN finances_platform p ON rev.platform_id = p.id
                    LEFT JOIN finances_store s ON rev.store_id = s.id
                    WHERE p.name = 'Distribution'
                    """
                )

        self.stdout.write(self.style.SUCCESS('DW fact_revenue built'))


