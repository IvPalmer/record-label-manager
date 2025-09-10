from rest_framework import serializers
from .models import RevenueEvent, Platform


class RevenueEventSerializer(serializers.ModelSerializer):
    platform_name = serializers.CharField(source='platform.name', read_only=True)
    
    class Meta:
        model = RevenueEvent
        fields = [
            'id', 'occurred_at', 'platform_name', 'currency', 'net_amount', 'net_amount_base',
            'gross_amount', 'quantity', 'product_type', 'isrc', 'track_artist_name', 
            'track_title', 'catalog_number'
        ]


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform
        fields = ['id', 'name', 'vendor_key']
