from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q, Avg, Min, Max
from django.http import HttpResponse
from decimal import Decimal
from django.utils import timezone
from datetime import datetime, timedelta
import csv
import json

from .models import RevenueEvent, Platform, SourceFile
from .models_etl import DwFactRevenue
from .serializers import RevenueEventSerializer, PlatformSerializer
from api.models import Label


class RevenueAnalysisViewSet(viewsets.ViewSet):
    """
    ViewSet for comprehensive revenue analytics
    Updated to handle both CSV and API-sourced data
    """

    def get_queryset(self):
        # Return unfiltered revenue events - frontend handles all filtering
        return RevenueEvent.objects.select_related('platform', 'store', 'source_file').all()

    def get_dw_queryset(self):
        """Return unfiltered data warehouse facts - frontend handles all filtering"""
        return DwFactRevenue.objects.all()

    def canonical_store(self, store_name: str) -> str:
        if not store_name:
            return ''
        name = (store_name or '').strip()
        lower = name.lower()
        # Consolidate common brand variants
        if 'youtube' in lower:
            return 'YouTube'
        if 'apple music' in lower or 'applemusic' in lower or 'itunes' in lower:
            return 'Apple Music'
        if 'amazon' in lower:
            return 'Amazon Music'
        if 'google play' in lower:
            return 'Google Play'
        if 'tiktok' in lower:
            return 'TikTok'
        if 'deezer' in lower:
            return 'Deezer'
        if 'tidal' in lower:
            return 'TIDAL'
        if 'spotify' in lower:
            return 'Spotify'
        if 'beatport' in lower:
            return 'Beatport'
        if 'qobuz' in lower:
            return 'Qobuz'
        if 'yandex' in lower:
            return 'Yandex'
        if 'netease' in lower:
            return 'Netease'
        if 'traxsource' in lower:
            return 'Traxsource'
        if 'juno' in lower:
            return 'Juno'
        return name

    @action(detail=False, methods=['get'])
    def status(self, request):
        """Return ingestion/build progress across raw, staging, and DW."""
        try:
            from django.db import connection
            with connection.cursor() as cur:
                cur.execute("SELECT COALESCE(count(*),0) FROM raw.bandcamp_event_raw")
                raw_bandcamp = cur.fetchone()[0]
                cur.execute("SELECT COALESCE(count(*),0) FROM raw.zebralution_event_raw")
                raw_zebra = cur.fetchone()[0]
                cur.execute("SELECT COALESCE(count(*),0) FROM raw.labelworx_event_raw")
                raw_labelworx = cur.fetchone()[0]
                cur.execute("SELECT COALESCE(count(*),0), COALESCE(sum(net_amount_eur),0) FROM staging.distribution_event")
                staging_row = cur.fetchone()
                staging_count = staging_row[0] if staging_row else 0
                staging_sum = str(staging_row[1]) if staging_row else '0'
                cur.execute("SELECT COALESCE(count(*),0), COALESCE(sum(revenue_base),0) FROM dw.fact_revenue")
                dw_row = cur.fetchone()
                dw_count = dw_row[0] if dw_row else 0
                dw_sum = str(dw_row[1]) if dw_row else '0'
        except Exception:
            raw_bandcamp = raw_zebra = raw_labelworx = 0
            staging_count = 0
            staging_sum = '0'
            dw_count = 0
            dw_sum = '0'
        return Response({
            'raw': {
                'bandcamp': raw_bandcamp,
                'zebralution': raw_zebra,
                'labelworx': raw_labelworx,
            },
            'staging': {
                'distribution_events': staging_count,
                'sum_net_eur': staging_sum,
            },
            'dw': {
                'fact_revenue_rows': dw_count,
                'sum_revenue_base': dw_sum,
            }
        })

    @action(detail=False, methods=['get'])
    def monthly_overview(self, request):
        """Get monthly aggregated overview data for the main table"""
        # Get currency parameter
        currency = request.GET.get('currency', 'BRL').upper()
        if currency not in ['BRL', 'USD', 'EUR']:
            currency = 'BRL'
        
        # Map currency to field name
        currency_field_map = {
            'BRL': 'revenue_brl',
            'USD': 'revenue_usd', 
            'EUR': 'revenue_eur'
        }
        currency_field = currency_field_map[currency]
        
        queryset = self.get_dw_queryset()
        
        # Group by month and aggregate
        from django.db.models.functions import TruncMonth
        monthly_data = queryset.annotate(
            month=TruncMonth('occurred_at')
        ).values('month').annotate(
            total_revenue=Sum(currency_field),
            total_downloads=Sum('quantity', filter=Q(platform='Bandcamp') | Q(store__icontains='Beatport')),
            total_streams=Sum('quantity', filter=~Q(platform='Bandcamp') & ~Q(store__icontains='Beatport')),
            total_transactions=Count('id'),
            unique_artists=Count('artist_name', distinct=True),
            unique_tracks=Count('track_title', distinct=True),
            unique_catalogs=Count('catalog_number', distinct=True),
            avg_per_transaction=Avg(currency_field)
        ).order_by('-month')
        
        # Add platform breakdown for each month
        result_data = []
        for month_data in monthly_data:
            month_date = month_data['month']
            if not month_date:
                continue
                
            # Get platform breakdown for this month
            month_platforms = queryset.filter(
                occurred_at__year=month_date.year,
                occurred_at__month=month_date.month
            ).values('platform', 'store').annotate(
                revenue=Sum(currency_field),
                quantity=Sum('quantity')
            ).order_by('-revenue')
            
            # Get top release for this month
            top_release = queryset.filter(
                occurred_at__year=month_date.year,
                occurred_at__month=month_date.month
            ).exclude(track_title='').values('track_title').annotate(
                revenue=Sum(currency_field)
            ).order_by('-revenue').first()
            
            # Get top platforms for this month
            top_platforms = []
            total_month_revenue = month_data['total_revenue'] or 0
            
            for platform in month_platforms[:3]:  # Top 3 platforms
                platform_name = platform['platform']
                store_name = self.canonical_store(platform.get('store'))
                display_name = 'Bandcamp' if platform_name == 'Bandcamp' else (store_name or platform_name)
                
                platform_revenue = platform['revenue'] or 0
                percentage = (platform_revenue / total_month_revenue * 100) if total_month_revenue > 0 else 0
                quantity = platform['quantity'] or 0
                
                # Determine if it's downloads or streams
                is_download_platform = platform_name == 'Bandcamp' or 'beatport' in (store_name or '').lower()
                metric_type = 'downloads' if is_download_platform else 'streams'
                
                top_platforms.append({
                    'name': display_name,
                    'revenue': str(platform_revenue),
                    'percentage': round(percentage, 1),
                    'quantity': quantity,
                    'metric_type': metric_type
                })
            
            result_data.append({
                'month': str(month_date),
                'year': month_date.year,
                'month_name': month_date.strftime('%B %Y'),
                'total_revenue': str(month_data['total_revenue'] or 0),
                'total_downloads': month_data['total_downloads'] or 0,
                'total_streams': month_data['total_streams'] or 0,
                'total_transactions': month_data['total_transactions'] or 0,
                'unique_artists': month_data['unique_artists'] or 0,
                'unique_tracks': month_data['unique_tracks'] or 0,
                'unique_catalogs': month_data['unique_catalogs'] or 0,
                'avg_per_transaction': str(month_data['avg_per_transaction'] or 0),
                'top_release': top_release['track_title'] if top_release else 'N/A',
                'top_platforms': top_platforms
            })
        
        return Response(result_data)

    @action(detail=False, methods=['get'])
    def detailed_overview(self, request):
        """Get detailed overview data for the main table"""
        # Get currency parameter
        currency = request.GET.get('currency', 'BRL').upper()
        if currency not in ['BRL', 'USD', 'EUR']:
            currency = 'BRL'
        
        # Map currency to field name
        currency_field_map = {
            'BRL': 'revenue_brl',
            'USD': 'revenue_usd', 
            'EUR': 'revenue_eur'
        }
        currency_field = currency_field_map[currency]
        # Switch to DW-backed fact table for unified data
        queryset = self.get_dw_queryset()
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 100))
        
        # Calculate pagination
        offset = (page - 1) * page_size
        total_count = queryset.count()
        
        # Get paginated results - order by the selected currency field
        events = queryset.order_by(f'-{currency_field}')[offset:offset + page_size]
        
        detailed_data = []
        for event in events:
            # Determine vendor and data source
            vendor = 'Bandcamp' if (event.platform == 'Bandcamp') else 'Distribution'
            data_source = 'API' if event.source == 'bandcamp' else 'CSV'
            
            # Extract date components
            occurred_at = event.occurred_at
            year = occurred_at.year if occurred_at else None
            month = occurred_at.month if occurred_at else None
            quarter = ((month - 1) // 3 + 1) if month else None
            date = event.occurred_at if occurred_at else None
            
            # Determine streams vs downloads
            streams = event.quantity if vendor == 'Distribution' else 0
            downloads = event.quantity if vendor == 'Bandcamp' else 0
            # Display name: Bandcamp has no platform/store; Distribution shows store if available, otherwise platform name
            platform_display = 'Bandcamp' if event.platform == 'Bandcamp' else (event.store or event.platform or '')
            
            detailed_data.append({
                'id': event.id,
                'vendor': vendor,
                'data_source': data_source,  # New field to show API vs CSV
                'year': year,
                'quarter': quarter,
                'month': month,
                'date': str(date) if date else '',
                'catalog_number': event.catalog_number or '',
                'release_name': '', # Not in current data
                'release_artist': '', # Not in current data  
                'track_artist': event.artist_name or '',
                'track_name': event.track_title or '',
                'isrc': event.isrc or '',
                'upc_ean': event.upc_ean or '',
                'platform': platform_display,
                'downloads': downloads,
                'streams': streams,
                'revenue': str(getattr(event, currency_field)),
                'currency': currency,
                'original_amount': str(event.revenue_base),
                'source_file': ''
            })
        
        return Response({
            'data': detailed_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size
            }
        })

    @action(detail=False, methods=['get'])
    def data_source_summary(self, request):
        """Get summary of data sources (API vs CSV)"""
        queryset = self.get_queryset()
        
        # Group by data source type
        api_data = queryset.filter(source_file__datasource__name__icontains='api').aggregate(
            revenue=Sum('net_amount_base'),
            count=Count('id')
        )
        
        csv_data = queryset.exclude(source_file__datasource__name__icontains='api').aggregate(
            revenue=Sum('net_amount_base'),
            count=Count('id')
        )
        
        total_revenue = queryset.aggregate(total=Sum('net_amount_base'))['total'] or Decimal('0')
        
        return Response({
            'api_source': {
                'revenue': str(api_data['revenue'] or 0),
                'count': api_data['count'],
                'percentage': float((api_data['revenue'] or 0) / total_revenue * 100) if total_revenue > 0 else 0
            },
            'csv_source': {
                'revenue': str(csv_data['revenue'] or 0),
                'count': csv_data['count'],
                'percentage': float((csv_data['revenue'] or 0) / total_revenue * 100) if total_revenue > 0 else 0
            },
            'total_revenue': str(total_revenue)
        })

    @action(detail=False, methods=['get'])
    def monthly_revenue_chart(self, request):
        """Get daily revenue data for line chart with more granular view"""
        # Get currency parameter
        currency = request.GET.get('currency', 'BRL').upper()
        if currency not in ['BRL', 'USD', 'EUR']:
            currency = 'BRL'
        
        # Map currency to field name
        currency_field_map = {
            'BRL': 'revenue_brl',
            'USD': 'revenue_usd', 
            'EUR': 'revenue_eur'
        }
        currency_field = currency_field_map[currency]
        
        queryset = self.get_dw_queryset()
        
        # Aggregate by month, and use store name for distribution
        from django.db.models.functions import TruncMonth
        daily_data = queryset.annotate(
            period=TruncMonth('occurred_at')
        ).values('period', 'platform', 'store').annotate(
            revenue=Sum(currency_field),
            transactions=Count('id')
        ).order_by('period', 'platform', 'store')
        
        # Build daily chart data
        chart_data = {}
        
        # First pass: collect all platforms and determine date range
        all_platforms = set()
        min_date = None
        max_date = None
        
        for item in daily_data:
            if item['period']:
                date_obj = item['period']
                platform_name = item['platform']
                store_name = self.canonical_store(item.get('store'))
                
                # Track date range
                if min_date is None or date_obj < min_date:
                    min_date = date_obj
                if max_date is None or date_obj > max_date:
                    max_date = date_obj
                
                # Bandcamp single series; Distribution broken down by store
                key = 'Bandcamp' if platform_name == 'Bandcamp' else (store_name or None)
                if key:
                    all_platforms.add(key)
        
        # Generate continuous monthly timeline from min to max date
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        
        chart_data = {}
        if min_date and max_date:
            current_date = min_date
            while current_date <= max_date:
                date_str = str(current_date)
                chart_data[date_str] = {'period': date_str}
                for platform in all_platforms:
                    chart_data[date_str][platform] = None
                current_date += relativedelta(months=1)
        
        # Second pass: add actual revenue data
        for item in daily_data:
            if item['period'] and item['revenue']:
                date_str = str(item['period'])
                platform_name = item['platform']
                store_name = self.canonical_store(item.get('store'))
                revenue = float(item['revenue'])
                
                # Bandcamp single series; Distribution broken down by store
                key = 'Bandcamp' if platform_name == 'Bandcamp' else (store_name or None)
                if key and revenue > 0:
                    if chart_data[date_str][key] is None:
                        chart_data[date_str][key] = revenue
                    else:
                        chart_data[date_str][key] += revenue
        
        # Apply top 5 distribution platforms + Others aggregation
        # 1) Calculate totals per platform (excluding Bandcamp)
        platform_totals = {}
        for row in chart_data.values():
            for k, v in row.items():
                if k == 'period':
                    continue
                if k != 'Bandcamp' and v is not None:
                    platform_totals[k] = platform_totals.get(k, 0) + v
        
        # 2) Get top 5 distribution platforms by total revenue
        top5_platforms = sorted(platform_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        top5_keys = {k for k, _ in top5_platforms}
        
        # 3) Build final chart data with top 5 + Others
        chart_list = []
        for date_key in sorted(chart_data.keys()):
            row = chart_data[date_key]
            out = {'period': row['period']}
            
            # Always include Bandcamp if it exists
            if 'Bandcamp' in row:
                out['Bandcamp'] = row['Bandcamp']
            
            # Add top 5 distribution platforms
            others_total = 0
            others_has_data = False
            for k, v in row.items():
                if k == 'period' or k == 'Bandcamp':
                    continue
                if k in top5_keys:
                    out[k] = v
                else:
                    if v is not None:
                        others_total += v
                        others_has_data = True
            
            # Add Others only if there's actual data (not just null values)
            if others_has_data:
                out['Others'] = others_total if others_total > 0 else None
            
            chart_list.append(out)
        
        return Response(chart_list)

    @action(detail=False, methods=['get'])
    def platform_pie_chart(self, request):
        """Get platform revenue data for pie chart"""
        # Get currency parameter
        currency = request.GET.get('currency', 'BRL').upper()
        if currency not in ['BRL', 'USD', 'EUR']:
            currency = 'BRL'
        
        # Map currency to field name
        currency_field_map = {
            'BRL': 'revenue_brl',
            'USD': 'revenue_usd', 
            'EUR': 'revenue_eur'
        }
        currency_field = currency_field_map[currency]
        
        queryset = self.get_dw_queryset()
        
        # Aggregate by effective display name:
        #  - 'Bandcamp' stays as Bandcamp
        #  - Distribution is shown per store name (Spotify, Apple Music, etc.)
        platform_data = queryset.values('platform', 'store').annotate(
            revenue=Sum(currency_field),
            transactions=Count('id')
        ).order_by('-revenue')
        
        total_revenue = queryset.aggregate(total=Sum(currency_field))['total'] or Decimal('0')
        
        # Collapse into a simple name -> totals mapping
        aggregated = {}
        colors = {
            'Bandcamp': '#408294',
            'Distribution': '#667eea', 
            'Spotify': '#1DB954',
            'Apple Music': '#C0C0C0',
            'iTunes': '#A2AAAD',
            'YouTube': '#FF0000',
            'YouTube Music': '#B71C1C',
            'TikTok': '#FF6B00',
            'TIDAL': '#000000',
            'Beatport': '#A8E00F',
            'Amazon Music': '#FF9900',
            'Deezer': '#0F9ED8'
        }
        
        for row in platform_data:
            platform_name = row['platform']
            store_name = self.canonical_store(row.get('store'))
            display_name = 'Bandcamp' if platform_name == 'Bandcamp' else (store_name or 'Distribution')
            if display_name not in aggregated:
                aggregated[display_name] = {'revenue': Decimal('0'), 'transactions': 0}
            aggregated[display_name]['revenue'] += row['revenue'] or Decimal('0')
            aggregated[display_name]['transactions'] += row['transactions'] or 0
        
        # Return ALL platforms sorted by revenue - let frontend handle filtering
        sorted_items = sorted(aggregated.items(), key=lambda kv: kv[1]['revenue'], reverse=True)
        pie_data = []
        for name, stats in sorted_items:
            revenue = float(stats['revenue'] or 0)
            percentage = (stats['revenue'] / total_revenue * 100) if total_revenue > 0 else 0
            pie_data.append({
                'name': name,
                'value': revenue,
                'percentage': round(percentage, 1),
                'color': colors.get(name, '#95a5a6'),
                'transactions': stats['transactions']
            })
        
        return Response(pie_data)

    @action(detail=False, methods=['get'])
    def filter_options(self, request):
        """Get available filter options"""
        queryset = self.get_dw_queryset()
        
        # Get unique values for filters
        years = queryset.extra(
            select={'year': 'EXTRACT(year FROM occurred_at)'}
        ).values('year').distinct().order_by('-year')
        
        platforms = queryset.values('platform').distinct().order_by('platform')
        
        artists = queryset.exclude(artist_name='').values(
            'artist_name'
        ).distinct().order_by('artist_name')[:100]  # Limit for performance
        
        catalogs = queryset.exclude(catalog_number='').values(
            'catalog_number'
        ).distinct().order_by('catalog_number')
        
        # Get data source types
        source_types = [
            {'value': 'all', 'label': 'All Sources'},
            {'value': 'api', 'label': 'API Data'},
            {'value': 'csv', 'label': 'CSV Data'}
        ]
        
        return Response({
            'years': [{'value': int(y['year']), 'label': str(int(y['year']))} for y in years if y['year']],
            'quarters': [
                {'value': 1, 'label': 'Q1'},
                {'value': 2, 'label': 'Q2'},
                {'value': 3, 'label': 'Q3'},
                {'value': 4, 'label': 'Q4'}
            ],
            'months': [
                {'value': i, 'label': f'Month {i}'} for i in range(1, 13)
            ],
            'platforms': [{'value': p['platform'], 'label': p['platform']} for p in platforms],
            'artists': [{'value': a['artist_name'], 'label': a['artist_name']} for a in artists],
            'catalogs': [{'value': c['catalog_number'], 'label': c['catalog_number']} for c in catalogs],
            'source_types': source_types
        })

    # Keep the existing methods for other tabs
    @action(detail=False, methods=['get'])
    def revenue_overview(self, request):
        """Get overall revenue statistics"""
        queryset = self.get_queryset()
        
        overview = queryset.aggregate(
            total_revenue_eur=Sum('net_amount_base'),
            total_transactions=Count('id'),
            avg_per_transaction=Avg('net_amount_base')
        )
        
        return Response({
            'total_revenue_eur': str(overview['total_revenue_eur'] or 0),
            'total_transactions': overview['total_transactions'] or 0,
            'avg_per_transaction': str(overview['avg_per_transaction'] or 0)
        })

    @action(detail=False, methods=['get'])
    def kpi_summary(self, request):
        """Get KPI summary data for dashboard cards"""
        queryset = self.get_queryset()
        dw_qs = self.get_dw_queryset()
        
        # Basic aggregations
        total_stats = queryset.aggregate(
            total_revenue=Sum('net_amount_base'),
            total_transactions=Count('id'),
            avg_per_transaction=Avg('net_amount_base')
        )
        
        # Count unique artists and tracks
        unique_artists = queryset.exclude(track_artist_name='').values('track_artist_name').distinct().count()
        unique_tracks = queryset.exclude(track_title='').values('track_title').distinct().count()
        
        # Platform breakdown
        platform_stats = queryset.values('platform__name').annotate(
            revenue=Sum('net_amount_base'),
            transactions=Count('id')
        ).order_by('-revenue')
        
        # Top performing data
        top_artist = queryset.exclude(track_artist_name='').values('track_artist_name').annotate(
            revenue=Sum('net_amount_base')
        ).order_by('-revenue').first()
        
        top_track = queryset.exclude(track_title='').values('track_title', 'track_artist_name').annotate(
            revenue=Sum('net_amount_base')
        ).order_by('-revenue').first()
        
        # Revenue analysis by time periods (use timezone-aware datetimes)
        from django.db.models import F
        
        now = timezone.now()
        current_month = now.replace(day=1)
        last_month = current_month - timedelta(days=32)
        last_month = last_month.replace(day=1)
        
        # Construct aware year boundaries
        current_tz = timezone.get_current_timezone()
        current_year = timezone.make_aware(datetime(now.year, 1, 1), current_tz)
        last_year = timezone.make_aware(datetime(now.year - 1, 1, 1), current_tz)
        last_year_end = timezone.make_aware(datetime(now.year - 1, 12, 31, 23, 59, 59), current_tz)
        
        # Current month vs last month
        current_month_revenue = queryset.filter(
            occurred_at__gte=current_month
        ).aggregate(revenue=Sum('net_amount_base'))['revenue'] or 0
        
        last_month_revenue = queryset.filter(
            occurred_at__gte=last_month,
            occurred_at__lt=current_month
        ).aggregate(revenue=Sum('net_amount_base'))['revenue'] or 0
        
        monthly_growth_rate = 0
        if last_month_revenue > 0:
            monthly_growth_rate = ((current_month_revenue - last_month_revenue) / last_month_revenue) * 100
        
        # Current year vs last year
        current_year_revenue = queryset.filter(
            occurred_at__gte=current_year
        ).aggregate(revenue=Sum('net_amount_base'))['revenue'] or 0
        
        last_year_revenue = queryset.filter(
            occurred_at__gte=last_year,
            occurred_at__lte=last_year_end
        ).aggregate(revenue=Sum('net_amount_base'))['revenue'] or 0
        
        yearly_growth_rate = 0
        if last_year_revenue > 0:
            yearly_growth_rate = ((current_year_revenue - last_year_revenue) / last_year_revenue) * 100
        
        # Average monthly revenue (last 12 months)
        twelve_months_ago = current_month - timedelta(days=365)
        avg_monthly_revenue = queryset.filter(
            occurred_at__gte=twelve_months_ago
        ).aggregate(revenue=Sum('net_amount_base'))['revenue'] or 0
        avg_monthly_revenue = avg_monthly_revenue / 12
        
        # Bandcamp and Distribution totals from DW - already in BRL
        bandcamp_total_brl = dw_qs.filter(platform='Bandcamp').aggregate(total=Sum('revenue_brl'))['total'] or 0
        distribution_total_brl = dw_qs.exclude(platform='Bandcamp').aggregate(total=Sum('revenue_brl'))['total'] or 0
        overall_total_brl = bandcamp_total_brl + distribution_total_brl
        
        # Total revenue from DW (already in BRL)
        total_revenue_brl = dw_qs.aggregate(total=Sum('revenue_brl'))['total'] or 0
        avg_per_transaction_brl = total_revenue_brl / (total_stats['total_transactions'] or 1)

        return Response({
            'total_revenue': str(total_revenue_brl),
            'total_transactions': total_stats['total_transactions'] or 0,
            'unique_artists': unique_artists,
            'unique_tracks': unique_tracks,
            'avg_per_transaction': str(avg_per_transaction_brl),
            'bandcamp_total': str(bandcamp_total_brl),
            'distribution_total': str(distribution_total_brl),
            'overall_total': str(overall_total_brl),
            'monthly_growth_rate': round(monthly_growth_rate, 1),
            'yearly_growth_rate': round(yearly_growth_rate, 1),
            'current_month_revenue': str(current_month_revenue),
            'last_month_revenue': str(last_month_revenue),
            'current_year_revenue': str(current_year_revenue),
            'last_year_revenue': str(last_year_revenue),
            'avg_monthly_revenue': str(avg_monthly_revenue),
            'top_artist': {
                'name': top_artist['track_artist_name'] if top_artist else 'N/A',
                'revenue': str(top_artist['revenue']) if top_artist else '0'
            },
            'top_track': {
                'title': top_track['track_title'] if top_track else 'N/A',
                'artist': top_track['track_artist_name'] if top_track else 'N/A',
                'revenue': str(top_track['revenue']) if top_track else '0'
            },
            'platform_breakdown': [
                {
                    'name': p['platform__name'],
                    'revenue': str(p['revenue']),
                    'transactions': p['transactions'],
                    'percentage': round((p['revenue'] / (total_stats['total_revenue'] or 1)) * 100, 1)
                }
                for p in platform_stats
            ]
        })

    @action(detail=False, methods=['get'])
    def currency_data(self, request):
        """Get revenue data in all currencies (BRL, USD, EUR)"""
        currency = request.GET.get('currency', 'BRL').upper()
        
        if currency not in ['BRL', 'USD', 'EUR']:
            currency = 'BRL'
        
        # Map currency to field name
        currency_field_map = {
            'BRL': 'revenue_brl',
            'USD': 'revenue_usd', 
            'EUR': 'revenue_eur'
        }
        
        currency_field = currency_field_map[currency]
        
        queryset = self.get_dw_queryset()
        
        # Get totals in selected currency
        bandcamp_total = queryset.filter(platform='Bandcamp').aggregate(
            total=Sum(currency_field)
        )['total'] or 0
        
        distribution_total = queryset.exclude(platform='Bandcamp').aggregate(
            total=Sum(currency_field)
        )['total'] or 0
        
        overall_total = bandcamp_total + distribution_total
        
        return Response({
            'currency': currency,
            'overall_total': str(overall_total),
            'bandcamp_total': str(bandcamp_total),
            'distribution_total': str(distribution_total)
        })

    @action(detail=False, methods=['get'])
    def revenue_by_artist(self, request):
        """Get revenue breakdown by artist"""
        queryset = self.get_queryset()
        limit = int(request.query_params.get('limit', 50))
        
        total_revenue = queryset.aggregate(total=Sum('net_amount_base'))['total'] or Decimal('0')
        
        artist_revenue = queryset.exclude(track_artist_name='').values(
            'track_artist_name'
        ).annotate(
            revenue=Sum('net_amount_base'),
            tracks_count=Count('isrc', distinct=True),
            transactions=Count('id')
        ).order_by('-revenue')[:limit]
        
        artists_data = []
        for artist in artist_revenue:
            revenue = artist['revenue'] or Decimal('0')
            percentage = (revenue / total_revenue * 100) if total_revenue > 0 else 0
            
            artists_data.append({
                'artist_name': artist['track_artist_name'],
                'revenue': str(revenue),
                'tracks_count': artist['tracks_count'],
                'transactions': artist['transactions'],
                'percentage': f"{percentage:.1}"
            })
        
        return Response({
            'artists': artists_data,
            'total_revenue': str(total_revenue)
        })

    @action(detail=False, methods=['get'])
    def revenue_by_track(self, request):
        """Get revenue breakdown by track"""
        queryset = self.get_queryset()
        limit = int(request.query_params.get('limit', 50))
        
        total_revenue = queryset.aggregate(total=Sum('net_amount_base'))['total'] or Decimal('0')
        
        track_revenue = queryset.exclude(isrc='').exclude(
            isrc__icontains='Exchange'
        ).values('isrc', 'track_artist_name', 'track_title', 'catalog_number').annotate(
            revenue=Sum('net_amount_base'),
            streams=Count('id'),
            avg_per_stream=Avg('net_amount_base')
        ).order_by('-revenue')[:limit]
        
        tracks_data = []
        for track in track_revenue:
            revenue = track['revenue'] or Decimal('0')
            percentage = (revenue / total_revenue * 100) if total_revenue > 0 else 0
            
            tracks_data.append({
                'isrc': track['isrc'],
                'artist_name': track['track_artist_name'] or 'Unknown Artist',
                'track_title': track['track_title'] or 'Unknown Track',
                'catalog_number': track['catalog_number'] or '',
                'revenue': str(revenue),
                'streams': track['streams'],
                'percentage': f"{percentage:.1}",
                'avg_per_stream': str(track['avg_per_stream'] or Decimal('0'))
            })
        
        return Response({
            'tracks': tracks_data,
            'total_revenue': str(total_revenue)
        })