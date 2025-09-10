from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('finances', '0002_revenueevent_catalog_number_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "CREATE SCHEMA IF NOT EXISTS raw;\n"
                "CREATE SCHEMA IF NOT EXISTS staging;\n"
                "CREATE SCHEMA IF NOT EXISTS dw;\n"
            ),
            reverse_sql=(
                "DROP SCHEMA IF EXISTS dw CASCADE;\n"
                "DROP SCHEMA IF EXISTS staging CASCADE;\n"
                "DROP SCHEMA IF EXISTS raw CASCADE;\n"
            ),
        ),

        # RAW TABLES
        migrations.CreateModel(
            name='RawBandcampEvent',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('date_str', models.CharField(max_length=32)),
                ('occurred_at', models.DateTimeField(null=True, blank=True)),
                ('item_name', models.CharField(max_length=400, blank=True)),
                ('item_type', models.CharField(max_length=50, blank=True)),
                ('artist', models.CharField(max_length=200, blank=True)),
                ('quantity', models.IntegerField(default=0)),
                ('currency', models.CharField(max_length=3, default='USD')),
                ('item_total', models.DecimalField(max_digits=18, decimal_places=6, default=0)),
                ('amount_received', models.DecimalField(max_digits=18, decimal_places=6, default=0)),
                ('raw_row', models.JSONField(null=True, blank=True)),
            ],
            options={'db_table': 'raw.bandcamp_event_raw'},
        ),

        migrations.CreateModel(
            name='RawZebralutionEvent',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('period', models.CharField(max_length=16, blank=True)),
                ('shop', models.CharField(max_length=100, blank=True)),
                ('provider', models.CharField(max_length=100, blank=True)),
                ('artist', models.CharField(max_length=200, blank=True)),
                ('title', models.CharField(max_length=200, blank=True)),
                ('isrc', models.CharField(max_length=32, blank=True)),
                ('ean', models.CharField(max_length=32, blank=True)),
                ('label_order_nr', models.CharField(max_length=64, blank=True)),
                ('country', models.CharField(max_length=2, blank=True)),
                ('sales', models.IntegerField(default=0)),
                ('revenue_eur', models.DecimalField(max_digits=18, decimal_places=6, default=0)),
                ('rev_less_publ_eur', models.DecimalField(max_digits=18, decimal_places=6, default=0)),
                ('raw_row', models.JSONField(null=True, blank=True)),
            ],
            options={'db_table': 'raw.zebralution_event_raw'},
        ),

        migrations.CreateModel(
            name='RawLabelworxEvent',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('store_name', models.CharField(max_length=100, blank=True)),
                ('track_artist', models.CharField(max_length=200, blank=True)),
                ('track_title', models.CharField(max_length=200, blank=True)),
                ('isrc', models.CharField(max_length=32, blank=True)),
                ('catalog', models.CharField(max_length=64, blank=True)),
                ('qty', models.IntegerField(default=0)),
                ('royalty', models.DecimalField(max_digits=18, decimal_places=6, default=0)),
                ('value', models.DecimalField(max_digits=18, decimal_places=6, default=0)),
                ('format', models.CharField(max_length=50, blank=True)),
                ('raw_row', models.JSONField(null=True, blank=True)),
            ],
            options={'db_table': 'raw.labelworx_event_raw'},
        ),

        # STAGING: NORMALIZED DISTRIBUTION
        migrations.CreateModel(
            name='StagingDistributionEvent',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('occurred_at', models.DateTimeField(null=True, blank=True)),
                ('platform', models.CharField(max_length=100)),
                ('store', models.CharField(max_length=100, blank=True)),
                ('track_artist_name', models.CharField(max_length=200, blank=True)),
                ('track_title', models.CharField(max_length=200, blank=True)),
                ('isrc', models.CharField(max_length=32, blank=True)),
                ('upc_ean', models.CharField(max_length=32, blank=True)),
                ('catalog_number', models.CharField(max_length=64, blank=True)),
                ('quantity', models.IntegerField(default=0)),
                ('gross_amount_eur', models.DecimalField(max_digits=18, decimal_places=6, default=0)),
                ('net_amount_eur', models.DecimalField(max_digits=18, decimal_places=6, default=0)),
            ],
            options={'db_table': 'staging.distribution_event'},
        ),

        # DW: DIMS
        migrations.CreateModel(
            name='DwArtist',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200, unique=True)),
            ],
            options={'db_table': 'dw.dim_artist'},
        ),
        migrations.CreateModel(
            name='DwRelease',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('catalog_number', models.CharField(max_length=64, unique=True)),
            ],
            options={'db_table': 'dw.dim_release'},
        ),
        migrations.CreateModel(
            name='DwTrack',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('isrc', models.CharField(max_length=32, unique=True)),
                ('title', models.CharField(max_length=200)),
            ],
            options={'db_table': 'dw.dim_track'},
        ),

        # DW: FACT
        migrations.CreateModel(
            name='DwFactRevenue',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('occurred_at', models.DateField()),
                ('source', models.CharField(max_length=32)),
                ('platform', models.CharField(max_length=100)),
                ('store', models.CharField(max_length=100, blank=True)),
                ('artist_name', models.CharField(max_length=200, blank=True)),
                ('track_title', models.CharField(max_length=200, blank=True)),
                ('isrc', models.CharField(max_length=32, blank=True)),
                ('catalog_number', models.CharField(max_length=64, blank=True)),
                ('upc_ean', models.CharField(max_length=32, blank=True)),
                ('quantity', models.IntegerField(default=0)),
                ('revenue_base', models.DecimalField(max_digits=18, decimal_places=6, default=0)),
                ('base_ccy', models.CharField(max_length=3)),
            ],
            options={'db_table': 'dw.fact_revenue'},
        ),
    ]


