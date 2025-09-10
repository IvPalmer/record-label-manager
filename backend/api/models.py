import uuid
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField

# User Role Choices
ROLE_CHOICES = (
    ('owner', 'Owner'),
    ('manager', 'Manager'),
    ('assistant', 'Assistant'),
)

# Release Status Choices
RELEASE_STATUS_CHOICES = (
    ('draft', 'Draft'),
    ('scheduled', 'Scheduled'),
    ('released', 'Released'),
)

# Demo Status Choices
DEMO_STATUS_CHOICES = (
    ('new', 'New'),
    ('reviewed', 'Reviewed'),
    ('accepted', 'Accepted'),
    ('rejected', 'Rejected'),
)


class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='owner')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} ({self.role})"


class Label(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_labels')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class Artist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)  # Real name
    project = models.CharField(max_length=100)  # Artistic name
    bio = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    image_url = models.URLField(blank=True)
    payment_address = models.TextField(blank=True)  # Added payment address
    labels = models.ManyToManyField(Label, related_name='artists')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.project


# Release Type Choices
RELEASE_TYPE_CHOICES = (
    ('album', 'Album'),
    ('ep', 'EP'),
    ('single', 'Single'),
    ('compilation', 'Compilation'),
)

class Release(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    cover_url = models.URLField(blank=True)  # Added cover URL
    release_date = models.DateField()
    pre_order_date = models.DateField(null=True, blank=True)  # Added pre-order date
    status = models.CharField(max_length=20, choices=RELEASE_STATUS_CHOICES, default='draft')
    catalog_number = models.CharField(max_length=20)
    type = models.CharField(max_length=20, choices=RELEASE_TYPE_CHOICES, default='single')  # Added release type
    style = models.CharField(max_length=100, blank=True)
    tags = ArrayField(models.CharField(max_length=50), blank=True, default=list)
    main_artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='main_releases', null=True, blank=True)  # Added main artist
    featuring_artists = models.ManyToManyField(Artist, related_name='featured_releases', blank=True)  # Added featuring artists
    soundcloud_url = models.URLField(blank=True)
    bandcamp_url = models.URLField(blank=True)
    google_drive_url = models.URLField(blank=True)  # Added Google Drive URL
    other_links = models.JSONField(blank=True, null=True)
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='releases')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} ({self.catalog_number})"


class Track(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    src_code = models.CharField(max_length=50, blank=True)  # ISRC code
    audio_url = models.URLField(blank=True)
    is_streaming_single = models.BooleanField(default=False)
    streaming_release_date = models.DateField(null=True, blank=True)
    tags = ArrayField(models.CharField(max_length=50), blank=True, default=list)
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='tracks')
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='tracks')  # Main artist
    featuring_artists = models.ManyToManyField(Artist, related_name='featured_tracks', blank=True)  # Added featuring artists
    remix_artist = models.ForeignKey(Artist, on_delete=models.SET_NULL, null=True, blank=True, related_name='remixed_tracks')  # Added remix artist
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='tracks')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.artist}"


class Mixtape(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    audio_url = models.URLField()
    release_date = models.DateField()
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='mixtapes')
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='mixtapes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.artist}"


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file_url = models.URLField()
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='documents')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_documents')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title


class CalendarEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='calendar_events')
    release = models.ForeignKey(Release, on_delete=models.SET_NULL, null=True, blank=True, related_name='calendar_events')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} ({self.date})"


class Demo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    audio_url = models.URLField()
    artist_name = models.CharField(max_length=200)  # Free text field for non-registered artists
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='demos')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_demos')
    status = models.CharField(max_length=20, choices=DEMO_STATUS_CHOICES, default='new')
    submitted_at = models.DateTimeField(auto_now_add=True)
    review_notes = models.TextField(blank=True)  # Added for review functionality
    
    def __str__(self):
        return f"{self.title} by {self.artist_name}"
