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
        queryset = RevenueEvent.objects.select_related('platform', 'store', 'source_file').all()
        
        # Apply filters
        year = self.request.query_params.get('year')
        if year and year != 'all':
            queryset = queryset.filter(occurred_at__year=year)
        
        quarter = self.request.query_params.get('quarter')
        if quarter and quarter != 'all':
            queryset = queryset.extra(
                where=["EXTRACT(quarter FROM occurred_at) = %s"],
                params=[quarter]
            )
        
        month = self.request.query_params.get('month')
        if month and month != 'all':
            queryset = queryset.filter(occurred_at__month=month)
        
        platform = self.request.query_params.get('platform')
        if platform and platform != 'all':
            queryset = queryset.filter(platform__name__icontains=platform)
        
        artist = self.request.query_params.get('artist')
        if artist:
            queryset = queryset.filter(track_artist_name__icontains=artist)
        
        track = self.request.query_params.get('track')
        if track:
            queryset = queryset.filter(track_title__icontains=track)
        
        catalog = self.request.query_params.get('catalog')
        if catalog:
            queryset = queryset.filter(catalog_number__icontains=catalog)
        
        # Filter by data source type (CSV vs API)
        source_type = self.request.query_params.get('source_type')
        if source_type == 'api':
            queryset = queryset.filter(source_file__datasource__name__icontains='api')
        elif source_type == 'csv':
            queryset = queryset.exclude(source_file__datasource__name__icontains='api')
        
        return queryset

    def get_dw_queryset(self):
        queryset = DwFactRevenue.objects.all()

        year = self.request.query_params.get('year')
        if year and year != 'all':
            queryset = queryset.filter(occurred_at__year=year)

        quarter = self.request.query_params.get('quarter')
        if quarter and quarter != 'all':
            # quarter from month math
            queryset = queryset.extra(
                where=["EXTRACT(quarter FROM occurred_at) = %s"],
                params=[quarter]
            )

        month = self.request.query_params.get('month')
        if month and month != 'all':
            queryset = queryset.filter(occurred_at__month=month)

        platform = self.request.query_params.get('platform')
        if platform and platform != 'all':
            queryset = queryset.filter(platform__icontains=platform)

        artist = self.request.query_params.get('artist')
        if artist:
            queryset = queryset.filter(artist_name__icontains=artist)

        track = self.request.query_params.get('track')
        if track:
            queryset = queryset.filter(track_title__icontains=track)

        catalog = self.request.query_params.get('catalog')
        if catalog:
            queryset = queryset.filter(catalog_number__icontains=catalog)

        # Map source_type to dw source column
        source_type = self.request.query_params.get('source_type')
        if source_type == 'api':
            queryset = queryset.filter(source__icontains='bandcamp')
        elif source_type == 'csv':
            queryset = queryset.exclude(source__icontains='bandcamp')

        return queryset

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
    def detailed_overview(self, request):
        """Get detailed overview data for the main table"""
        # Switch to DW-backed fact table for unified data
        queryset = self.get_dw_queryset()
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 100))
        
        # Calculate pagination
        offset = (page - 1) * page_size
        total_count = queryset.count()
        
        # Get paginated results
        events = queryset.order_by('-revenue_base')[offset:offset + page_size]
        
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
                'revenue': str(event.revenue_base),
                'currency': event.base_ccy,
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
        queryset = self.get_dw_queryset()
        
        # Aggregate by month, and use store name for distribution
        from django.db.models.functions import TruncMonth
        daily_data = queryset.annotate(
            period=TruncMonth('occurred_at')
        ).values('period', 'platform', 'store').annotate(
            revenue=Sum('revenue_base'),
            transactions=Count('id')
        ).order_by('period', 'platform', 'store')
        
        # Build daily chart data
        chart_data = {}
        
        for item in daily_data:
            if item['period'] and item['revenue']:
                # 'period' is a date when using TruncMonth on a DateField in DW
                date_str = str(item['period'])
                platform_name = item['platform']
                store_name = self.canonical_store(item.get('store'))
                revenue = float(item['revenue'])
                
                if date_str not in chart_data:
                    chart_data[date_str] = {'period': date_str}
                
                # Only add if revenue > 0
                if revenue > 0:
                    # Bandcamp single series; Distribution broken down by store
                    key = 'Bandcamp' if platform_name == 'Bandcamp' else (store_name or None)
                    if not key:
                        continue
                    chart_data[date_str][key] = chart_data[date_str].get(key, 0) + revenue
        
        # Group distribution series to top 5 stores + Others across the entire span
        # 1) compute totals per key (excluding Bandcamp)
        totals = {}
        for row in chart_data.values():
            for k, v in row.items():
                if k == 'period':
                    continue
                if k != 'Bandcamp':
                    totals[k] = totals.get(k, 0) + (v or 0)
        top5 = set(sorted(totals.items(), key=lambda x: x[1], reverse=True)[:5])
        top5_keys = {k for k, _ in top5}
        
        # 2) build final list with Others
        chart_list = []
        for date_key in sorted(chart_data.keys()):
            row = chart_data[date_key]
            out = {'period': row['period']}
            others_total = 0
            for k, v in row.items():
                if k == 'period':
                    continue
                if k == 'Bandcamp' or k in top5_keys:
                    out[k] = v
                else:
                    others_total += v or 0
            if others_total > 0:
                out['Others'] = others_total
            chart_list.append(out)
        
        return Response(chart_list)

    @action(detail=False, methods=['get'])
    def platform_pie_chart(self, request):
        """Get platform revenue data for pie chart"""
        queryset = self.get_dw_queryset()
        
        # Aggregate by effective display name:
        #  - 'Bandcamp' stays as Bandcamp
        #  - Distribution is shown per store name (Spotify, Apple Music, etc.)
        platform_data = queryset.values('platform', 'store').annotate(
            revenue=Sum('revenue_base'),
            transactions=Count('id')
        ).order_by('-revenue')
        
        total_revenue = queryset.aggregate(total=Sum('revenue_base'))['total'] or Decimal('0')
        
        # Collapse into a simple name -> totals mapping
        aggregated = {}
        colors = {
            'Bandcamp': '#408294',
            'Distribution': '#667eea', 
            'Spotify': '#1DB954',
            'Apple Music': '#FA243C',
            'iTunes': '#A2AAAD',
            'YouTube': '#FF0000',
            'YouTube Music': '#FF0000',
            'TikTok': '#69C9D0',
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
        
        # Top 5 + Others
        sorted_items = sorted(aggregated.items(), key=lambda kv: kv[1]['revenue'], reverse=True)
        # Top 5 + Others (always ensure exactly 5 platforms before Others when available)
        top5 = sorted_items[:5]
        others = sorted_items[5:]
        others_total = sum((v['revenue'] for _, v in others), Decimal('0'))
        others_tx = sum((v['transactions'] for _, v in others), 0)
        pie_data = []
        for name, stats in top5:
            revenue = float(stats['revenue'] or 0)
            percentage = (stats['revenue'] / total_revenue * 100) if total_revenue > 0 else 0
            pie_data.append({
                'name': name,
                'value': revenue,
                'percentage': round(percentage, 1),
                'color': colors.get(name, '#95a5a6'),
                'transactions': stats['transactions']
            })
        if others_total > 0:
            pct = (others_total / total_revenue * 100) if total_revenue > 0 else 0
            pie_data.append({
                'name': 'Others',
                'value': float(others_total),
                'percentage': round(pct, 1),
                'color': '#9CA3AF',
                'transactions': others_tx
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
        
        # Bandcamp and Distribution totals from DW
        bandcamp_total = dw_qs.filter(platform='Bandcamp').aggregate(total=Sum('revenue_base'))['total'] or 0
        distribution_total = dw_qs.exclude(platform='Bandcamp').aggregate(total=Sum('revenue_base'))['total'] or 0

        return Response({
            'total_revenue': str(total_stats['total_revenue'] or 0),
            'total_transactions': total_stats['total_transactions'] or 0,
            'unique_artists': unique_artists,
            'unique_tracks': unique_tracks,
            'avg_per_transaction': str(total_stats['avg_per_transaction'] or 0),
            'bandcamp_total': str(bandcamp_total),
            'distribution_total': str(distribution_total),
            'overall_total': str((bandcamp_total or 0) + (distribution_total or 0)),
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