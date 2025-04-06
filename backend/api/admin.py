from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    UserProfile, Label, Artist, Release, Track, 
    Mixtape, Document, CalendarEvent, Demo
)

# Register admin classes for our models
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'

# Extend the User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    
    def get_role(self, obj):
        try:
            return obj.profile.role
        except UserProfile.DoesNotExist:
            return '-'
    get_role.short_description = 'Role'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class LabelReleaseInline(admin.TabularInline):
    model = Release
    fields = ('title', 'catalog_number', 'release_date', 'status')
    extra = 0
    verbose_name = "Release"
    verbose_name_plural = "Releases on this label"

class LabelArtistInline(admin.TabularInline):
    model = Artist.labels.through
    verbose_name = "Artist"
    verbose_name_plural = "Artists on this label"
    extra = 0

@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'owner', 'release_count', 'artist_count', 'created_at')
    search_fields = ('name', 'country')
    list_filter = ('created_at', 'country')
    inlines = [LabelReleaseInline, LabelArtistInline]
    
    def release_count(self, obj):
        count = Release.objects.filter(label=obj).count()
        if count > 0:
            # Make count clickable to view all releases for this label
            releases_url = reverse('admin:api_release_changelist') + f'?label__id__exact={obj.id}'
            return format_html('<a href="{}"><span style="color: green;">{}</span></a>', 
                               releases_url, count)
        return format_html('<span style="color: gray;">0</span>')
    
    def artist_count(self, obj):
        count = Artist.objects.filter(labels=obj).count()
        if count > 0:
            # Make count clickable to view all artists for this label
            artists_url = reverse('admin:api_artist_changelist') + f'?labels__id__exact={obj.id}'
            return format_html('<a href="{}"><span style="color: green;">{}</span></a>', 
                               artists_url, count)
        return format_html('<span style="color: gray;">0</span>')
    
    release_count.short_description = 'Releases'
    artist_count.short_description = 'Artists'

class ArtistTrackInline(admin.TabularInline):
    model = Track
    fields = ('title', 'release', 'audio_url', 'is_streaming_single', 'streaming_release_date')
    readonly_fields = ('release',)
    extra = 1
    verbose_name = "Track"
    verbose_name_plural = "Tracks by this artist"

@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'country', 'email', 'track_count', 'release_count', 'created_at')
    search_fields = ('name', 'project', 'email')
    list_filter = ('created_at', 'country', 'labels')
    filter_horizontal = ('labels',)
    readonly_fields = ('release_list',)
    fieldsets = (
        (None, {
            'fields': ('name', 'project', 'bio', 'email', 'country', 'image_url', 'labels')
        }),
        ('Releases Featuring This Artist', {
            'fields': ('release_list',)
        }),
    )
    inlines = [ArtistTrackInline]
    
    def track_count(self, obj):
        count = Track.objects.filter(artist=obj).count()
        if count > 0:
            # Make count clickable to view all tracks for this artist
            tracks_url = reverse('admin:api_track_changelist') + f'?artist__id__exact={obj.id}'
            return format_html('<a href="{}"><span style="color: green;">{}</span></a>', 
                               tracks_url, count)
        return format_html('<span style="color: gray;">0</span>')
    
    def release_count(self, obj):
        # Get unique releases that this artist has tracks on
        releases = Release.objects.filter(tracks__artist=obj).distinct().count()
        if releases > 0:
            # Make count clickable to view all releases featuring this artist
            releases_url = reverse('admin:api_release_changelist')
            return format_html('<a href="{}?tracks__artist__id__exact={}"><span style="color: green;">{}</span></a>', 
                               releases_url, obj.id, releases)
        return format_html('<span style="color: gray;">0</span>')
    
    def release_list(self, obj):
        releases = Release.objects.filter(tracks__artist=obj).distinct()
        if not releases:
            return "No releases found"
        
        result = "<table><tr><th>Title</th><th>Catalog #</th><th>Release Date</th><th>Status</th><th>Label</th><th>Tracks by Artist</th></tr>"
        for release in releases:
            track_count = Track.objects.filter(release=release, artist=obj).count()
            # Generate a link to the release admin page
            release_url = reverse('admin:api_release_change', args=[release.id])
            label_url = reverse('admin:api_label_change', args=[release.label.id])
            
            result += f"<tr><td><a href='{release_url}'><strong>{release.title}</strong></a></td>"
            result += f"<td>{release.catalog_number}</td>"
            result += f"<td>{release.release_date}</td><td>{release.status}</td>"
            result += f"<td><a href='{label_url}'>{release.label.name}</a></td>"
            result += f"<td>{track_count}</td></tr>"
        result += "</table>"
        return format_html(result)
    
    track_count.short_description = 'Tracks'
    release_count.short_description = 'Releases'
    release_list.short_description = 'Releases featuring this artist'

class TrackInline(admin.TabularInline):
    model = Track
    fields = ('title', 'artist', 'is_streaming_single', 'streaming_release_date', 'audio_url')
    extra = 1
    verbose_name = "Track"
    verbose_name_plural = "Tracks on this release"

@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'catalog_number', 'release_date', 'status', 'label', 'artist_list_display', 'track_count')
    search_fields = ('title', 'catalog_number')
    list_filter = ('status', 'release_date', 'label')
    date_hierarchy = 'release_date'
    readonly_fields = ('created_at', 'track_count', 'artist_list_full')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'release_date', 'status', 'catalog_number', 'style', 'tags', 'label')
        }),
        ('Links', {
            'fields': ('soundcloud_url', 'bandcamp_url', 'other_links')
        }),
        ('Artists', {
            'fields': ('artist_list_full',)
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
    inlines = [TrackInline]
    
    def track_count(self, obj):
        count = Track.objects.filter(release=obj).count()
        if count > 0:
            # Make count clickable to view all tracks for this release
            tracks_url = reverse('admin:api_track_changelist') + f'?release__id__exact={obj.id}'
            return format_html('<a href="{}"><span style="color: green;">{}</span></a>', 
                               tracks_url, count)
        return format_html('<span style="color: gray;">0</span>')
    
    def artist_list_display(self, obj):
        # Get all unique artists from the tracks of this release
        artists = Artist.objects.filter(tracks__release=obj).distinct()
        if not artists:
            return "-"
        return ", ".join([artist.project for artist in artists[:3]]) + (
            " & more" if artists.count() > 3 else "")
    
    def artist_list_full(self, obj):
        # Get all unique artists from the tracks of this release
        artists = Artist.objects.filter(tracks__release=obj).distinct()
        if not artists:
            return "No artists found"
        
        result = "<table><tr><th>Artist</th><th>Tracks</th><th>Country</th><th>Actions</th></tr>"
        for artist in artists:
            track_count = Track.objects.filter(release=obj, artist=artist).count()
            # Generate a link to the artist admin page
            artist_url = reverse('admin:api_artist_change', args=[artist.id])
            
            result += f"<tr><td><a href='{artist_url}'><strong>{artist.project}</strong></a> ({artist.name})</td>"
            result += f"<td>{track_count}</td><td>{artist.country}</td>"
            
            # Add links to view tracks by this artist on this release
            track_list_url = reverse('admin:api_track_changelist')
            result += f"<td><a href='{track_list_url}?artist__id__exact={artist.id}&release__id__exact={obj.id}'>"
            result += f"View Tracks</a></td></tr>"
        result += "</table>"
        return format_html(result)
    
    track_count.short_description = 'Tracks'
    artist_list_display.short_description = 'Artists'
    artist_list_full.short_description = 'Artists on this release'

@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('title', 'release', 'artist', 'label', 'is_streaming_single')
    search_fields = ('title', 'src_code')
    list_filter = ('is_streaming_single', 'streaming_release_date', 'release', 'artist', 'label')
    readonly_fields = ('created_at',)

@admin.register(Mixtape)
class MixtapeAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'label', 'release_date')
    search_fields = ('title',)
    list_filter = ('release_date', 'artist', 'label')
    date_hierarchy = 'release_date'
    readonly_fields = ('created_at',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'label', 'uploaded_by', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('label', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'label', 'release', 'created_by')
    search_fields = ('title', 'description')
    list_filter = ('date', 'label')
    date_hierarchy = 'date'
    readonly_fields = ('created_at',)

@admin.register(Demo)
class DemoAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist_name', 'status', 'label', 'submitted_by', 'submitted_at')
    search_fields = ('title', 'artist_name')
    list_filter = ('status', 'label', 'submitted_at')
    readonly_fields = ('submitted_at',)
