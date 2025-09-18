from django.core.management.base import BaseCommand
from django.db import connection
from finances.services.exchange_rate_service import ExchangeRateService


class Command(BaseCommand):
    help = 'Populate dw.fact_revenue from raw.bandcamp_event_raw and staging.distribution_event'

    def handle(self, *args, **options):
        # Get current exchange rates
        usd_to_brl_rate = ExchangeRateService.get_rate_to_brl('USD')
        eur_to_brl_rate = ExchangeRateService.get_rate_to_brl('EUR')
        
        # Calculate cross rates (BRL as base)
        brl_to_usd_rate = 1 / usd_to_brl_rate  # ~0.185
        brl_to_eur_rate = 1 / eur_to_brl_rate  # ~0.158
        
        # Calculate USD/EUR cross rate
        usd_to_eur_rate = brl_to_eur_rate / brl_to_usd_rate  # ~0.854
        eur_to_usd_rate = 1 / usd_to_eur_rate  # ~1.171
        
        self.stdout.write(f'Exchange rates:')
        self.stdout.write(f'  USD->BRL: {usd_to_brl_rate}, BRL->USD: {brl_to_usd_rate}')
        self.stdout.write(f'  EUR->BRL: {eur_to_brl_rate}, BRL->EUR: {brl_to_eur_rate}')
        self.stdout.write(f'  USD->EUR: {usd_to_eur_rate}, EUR->USD: {eur_to_usd_rate}')
        
        with connection.cursor() as cur:
            # Clear fact table
            cur.execute("TRUNCATE TABLE dw.fact_revenue")

            # Bandcamp (USD base) - convert to all currencies
            cur.execute(
                """
                INSERT INTO dw.fact_revenue (
                  occurred_at, source, platform, store, artist_name, track_title, isrc, catalog_number, upc_ean, quantity, 
                  revenue_base, base_ccy, revenue_brl, revenue_usd, revenue_eur
                )
                SELECT 
                  DATE(occurred_at), 'bandcamp', 'Bandcamp', NULL,
                  artist, item_name, NULL, NULL, NULL,
                  quantity, amount_received, 'USD', 
                  amount_received * %s,  -- BRL
                  amount_received,       -- USD (original)
                  amount_received * %s   -- EUR
                FROM raw.bandcamp_event_raw
                WHERE item_type IN ('track','album','bundle')
                """,
                [float(usd_to_brl_rate), float(usd_to_eur_rate)]
            )

            # Distribution (EUR base) from staging if available - convert to all currencies
            cur.execute("SELECT COUNT(*) FROM staging.distribution_event")
            staging_count = cur.fetchone()[0]
            if staging_count and staging_count > 0:
                cur.execute(
                    """
                    INSERT INTO dw.fact_revenue (
                      occurred_at, source, platform, store, artist_name, track_title, isrc, catalog_number, upc_ean, quantity, 
                      revenue_base, base_ccy, revenue_brl, revenue_usd, revenue_eur
                    )
                    SELECT 
                      DATE(occurred_at), 'distribution', 'Distribution', store,
                      track_artist_name, track_title, isrc, catalog_number, upc_ean,
                      quantity, net_amount_eur, 'EUR', 
                      net_amount_eur * %s,  -- BRL
                      net_amount_eur * %s,  -- USD
                      net_amount_eur        -- EUR (original)
                    FROM staging.distribution_event
                    """,
                    [float(eur_to_brl_rate), float(eur_to_usd_rate)]
                )
            else:
                # Fallback: build from normalized finances_revenueevent if staging is empty
                cur.execute(
                    """
                    INSERT INTO dw.fact_revenue (
                      occurred_at, source, platform, store, artist_name, track_title, isrc, catalog_number, upc_ean, quantity, 
                      revenue_base, base_ccy, revenue_brl, revenue_usd, revenue_eur
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
                      rev.base_ccy,
                      -- BRL conversion
                      CASE 
                        WHEN rev.base_ccy = 'USD' THEN rev.net_amount_base * %s
                        WHEN rev.base_ccy = 'EUR' THEN rev.net_amount_base * %s
                        ELSE rev.net_amount_base
                      END,
                      -- USD conversion
                      CASE 
                        WHEN rev.base_ccy = 'USD' THEN rev.net_amount_base
                        WHEN rev.base_ccy = 'EUR' THEN rev.net_amount_base * %s
                        ELSE rev.net_amount_base * %s
                      END,
                      -- EUR conversion
                      CASE 
                        WHEN rev.base_ccy = 'EUR' THEN rev.net_amount_base
                        WHEN rev.base_ccy = 'USD' THEN rev.net_amount_base * %s
                        ELSE rev.net_amount_base * %s
                      END
                    FROM finances_revenueevent rev
                    JOIN finances_platform p ON rev.platform_id = p.id
                    LEFT JOIN finances_store s ON rev.store_id = s.id
                    WHERE p.name = 'Distribution'
                    """,
                    [
                        float(usd_to_brl_rate), float(eur_to_brl_rate),  # BRL conversion
                        float(eur_to_usd_rate), float(brl_to_usd_rate),  # USD conversion
                        float(usd_to_eur_rate), float(brl_to_eur_rate)   # EUR conversion
                    ]
                )

        self.stdout.write(self.style.SUCCESS('DW fact_revenue built'))


