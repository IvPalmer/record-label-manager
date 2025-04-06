from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    UserProfile, Label, Artist, Release, 
    Track, Mixtape, Document, CalendarEvent, Demo
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'role', 'created_at']
        read_only_fields = ['id', 'created_at']

class LabelSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Label
        fields = ['id', 'name', 'description', 'country', 'owner', 'owner_name', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_owner_name(self, obj):
        return obj.owner.get_full_name() or obj.owner.username

class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = [
            'id', 'name', 'project', 'bio', 'email', 
            'country', 'image_url', 'labels', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class ReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Release
        fields = [
            'id', 'title', 'description', 'release_date', 'status',
            'catalog_number', 'style', 'tags', 'soundcloud_url',
            'bandcamp_url', 'other_links', 'label', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class TrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Track
        fields = [
            'id', 'title', 'src_code', 'audio_url', 'is_streaming_single',
            'streaming_release_date', 'tags', 'release', 'artist', 'label', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class MixtapeSerializer(serializers.ModelSerializer):
    artist_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Mixtape
        fields = [
            'id', 'title', 'description', 'audio_url', 'release_date',
            'artist', 'artist_name', 'label', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_artist_name(self, obj):
        return obj.artist.project

class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'file_url', 
            'label', 'uploaded_by', 'uploaded_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() or obj.uploaded_by.username

class CalendarEventSerializer(serializers.ModelSerializer):
    release_title = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = CalendarEvent
        fields = [
            'id', 'title', 'description', 'date', 'label',
            'release', 'release_title', 'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_release_title(self, obj):
        if obj.release:
            return obj.release.title
        return None

class DemoSerializer(serializers.ModelSerializer):
    submitted_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Demo
        fields = [
            'id', 'title', 'audio_url', 'artist_name', 'label',
            'submitted_by', 'submitted_by_name', 'status', 
            'submitted_at', 'review_notes'
        ]
        read_only_fields = ['id', 'submitted_at']
    
    def get_submitted_by_name(self, obj):
        return obj.submitted_by.get_full_name() or obj.submitted_by.username
