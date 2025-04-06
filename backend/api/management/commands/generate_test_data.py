import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from api.models import (
    UserProfile, Label, Artist, Release, Track, 
    Mixtape, Document, CalendarEvent, Demo
)

class Command(BaseCommand):
    help = 'Generates test data for the Record Label Manager app'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating test data...')
        
        try:
            with transaction.atomic():
                # Create Admin user if it doesn't exist
                admin_user = self._create_admin_user()
                
                # Create some example labels
                labels = self._create_labels(admin_user)
                
                # Create some example artists
                artists = self._create_artists(labels)
                
                # Create releases and tracks
                releases = self._create_releases(labels)
                tracks = self._create_tracks(releases, artists, labels)
                
                # Create mixtapes
                mixtapes = self._create_mixtapes(artists, labels)
                
                # Create documents
                documents = self._create_documents(admin_user, labels)
                
                # Create calendar events
                events = self._create_calendar_events(admin_user, labels, releases)
                
                # Create demos
                demos = self._create_demos(admin_user, labels)
                
                self.stdout.write(self.style.SUCCESS('Successfully created test data!'))
                
                # Print summary
                self._print_summary(labels, artists, releases, tracks, mixtapes, documents, events, demos)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
    
    def _create_admin_user(self):
        try:
            admin_user = User.objects.get(username='admin')
            self.stdout.write('Admin user already exists')
        except User.DoesNotExist:
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpassword'
            )
            UserProfile.objects.create(
                user=admin_user,
                role='owner'
            )
            self.stdout.write('Created admin user')
        return admin_user
    
    def _create_labels(self, admin_user):
        labels = []
        label_data = [
            {
                'name': 'Bassline Records',
                'description': 'Electronic music label focusing on bass-heavy genres',
                'country': 'United Kingdom'
            },
            {
                'name': 'Melodic Horizons',
                'description': 'A label dedicated to melodic techno and deep house',
                'country': 'Germany'
            },
            {
                'name': 'Future Groove',
                'description': 'Forward-thinking electronic music label',
                'country': 'United States'
            }
        ]
        
        for data in label_data:
            label, created = Label.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'country': data['country'],
                    'owner': admin_user
                }
            )
            labels.append(label)
            if created:
                self.stdout.write(f'Created label: {label.name}')
            else:
                self.stdout.write(f'Label already exists: {label.name}')
        
        return labels
    
    def _create_artists(self, labels):
        artists = []
        artist_data = [
            {
                'name': 'Sarah Blue',
                'project': 'Ambient Blue',
                'bio': 'Ambient music producer with a focus on atmospheric soundscapes',
                'email': 'sarah@example.com',
                'country': 'Canada',
                'label_index': 1
            },
            {
                'name': 'James Davidson',
                'project': 'Bass Reactor',
                'bio': 'Bass music producer specializing in dubstep and drum & bass',
                'email': 'james@example.com',
                'country': 'United Kingdom',
                'label_index': 0 
            },
            {
                'name': 'Elena Kraft',
                'project': 'Melodic Wave',
                'bio': 'Melodic techno producer from Berlin',
                'email': 'elena@example.com',
                'country': 'Germany',
                'label_index': 1
            },
            {
                'name': 'Marcus Rhythm',
                'project': 'Future Beats',
                'bio': 'Experimental electronic music producer',
                'email': 'marcus@example.com',
                'country': 'United States',
                'label_index': 2
            }
        ]
        
        for data in artist_data:
            artist, created = Artist.objects.get_or_create(
                name=data['name'],
                project=data['project'],
                defaults={
                    'bio': data['bio'],
                    'email': data['email'],
                    'country': data['country']
                }
            )
            
            # Add label association
            label_index = data.get('label_index', 0)
            if label_index < len(labels):
                artist.labels.add(labels[label_index])
            
            artists.append(artist)
            if created:
                self.stdout.write(f'Created artist: {artist.name} ({artist.project})')
            else:
                self.stdout.write(f'Artist already exists: {artist.name}')
        
        return artists
    
    def _create_releases(self, labels):
        releases = []
        release_data = [
            {
                'title': 'Midnight Groove',
                'description': 'A collection of deep house tracks',
                'release_date': datetime.now().date() + timedelta(days=30),
                'status': 'scheduled',
                'catalog_number': 'MH001',
                'style': 'Deep House',
                'label_index': 1
            },
            {
                'title': 'Bass Explorations',
                'description': 'Heavy bass music compilation',
                'release_date': datetime.now().date() - timedelta(days=60),
                'status': 'released',
                'catalog_number': 'BR001',
                'style': 'Dubstep',
                'label_index': 0
            },
            {
                'title': 'Future Sounds Vol. 1',
                'description': 'Exploring the future of electronic music',
                'release_date': datetime.now().date() + timedelta(days=90),
                'status': 'draft',
                'catalog_number': 'FG001',
                'style': 'Experimental',
                'label_index': 2
            }
        ]
        
        for data in release_data:
            label_index = data.pop('label_index', 0)
            if label_index < len(labels):
                label = labels[label_index]
                
                release, created = Release.objects.get_or_create(
                    title=data['title'],
                    catalog_number=data['catalog_number'],
                    defaults={
                        'description': data['description'],
                        'release_date': data['release_date'],
                        'status': data['status'],
                        'style': data['style'],
                        'label': label,
                        'tags': ['electronic', data['style'].lower(), '2025']
                    }
                )
                
                releases.append(release)
                if created:
                    self.stdout.write(f'Created release: {release.title} ({release.catalog_number})')
                else:
                    self.stdout.write(f'Release already exists: {release.title}')
        
        return releases
    
    def _create_tracks(self, releases, artists, labels):
        tracks = []
        
        # Create 2-4 tracks for each release
        for release in releases:
            num_tracks = random.randint(2, 4)
            
            for i in range(1, num_tracks + 1):
                # Pick a random artist, preferably matching the label
                matching_artists = [a for a in artists if release.label in a.labels.all()]
                if not matching_artists:
                    matching_artists = artists
                
                artist = random.choice(matching_artists)
                
                # Create track
                track, created = Track.objects.get_or_create(
                    title=f'Track {i} on {release.title}',
                    release=release,
                    artist=artist,
                    defaults={
                        'src_code': f'{release.catalog_number}-{i:02d}',
                        'is_streaming_single': i == 1,  # Make first track a single
                        'streaming_release_date': release.release_date - timedelta(days=15) if i == 1 else None,
                        'label': release.label,
                        'tags': ['electronic', '2025']
                    }
                )
                
                tracks.append(track)
                if created:
                    self.stdout.write(f'Created track: {track.title}')
                else:
                    self.stdout.write(f'Track already exists: {track.title}')
        
        return tracks
    
    def _create_mixtapes(self, artists, labels):
        mixtapes = []
        mixtape_data = [
            {
                'title': 'Summer Vibes Mix',
                'description': 'A mixtape for summer parties',
                'release_date': datetime.now().date() - timedelta(days=30),
                'artist_index': 0,
                'label_index': 1
            },
            {
                'title': 'Bass Explorations Podcast',
                'description': 'Exploring the latest in bass music',
                'release_date': datetime.now().date() - timedelta(days=15),
                'artist_index': 1,
                'label_index': 0
            }
        ]
        
        for data in mixtape_data:
            artist_index = data.pop('artist_index', 0)
            label_index = data.pop('label_index', 0)
            
            if artist_index < len(artists) and label_index < len(labels):
                mixtape, created = Mixtape.objects.get_or_create(
                    title=data['title'],
                    artist=artists[artist_index],
                    defaults={
                        'description': data['description'],
                        'audio_url': f'https://example.com/mixtapes/{data["title"].lower().replace(" ", "-")}',
                        'release_date': data['release_date'],
                        'label': labels[label_index]
                    }
                )
                
                mixtapes.append(mixtape)
                if created:
                    self.stdout.write(f'Created mixtape: {mixtape.title}')
                else:
                    self.stdout.write(f'Mixtape already exists: {mixtape.title}')
        
        return mixtapes
    
    def _create_documents(self, user, labels):
        documents = []
        document_data = [
            {
                'title': 'Label Contract Template',
                'description': 'Standard contract for new artists',
                'label_index': 0
            },
            {
                'title': 'Release Checklist',
                'description': 'Checklist for preparing a new release',
                'label_index': 1
            },
            {
                'title': 'Promotional Guidelines',
                'description': 'Guidelines for promoting releases',
                'label_index': 2
            }
        ]
        
        for data in document_data:
            label_index = data.pop('label_index', 0)
            
            if label_index < len(labels):
                document, created = Document.objects.get_or_create(
                    title=data['title'],
                    label=labels[label_index],
                    defaults={
                        'description': data['description'],
                        'file_url': f'https://example.com/documents/{data["title"].lower().replace(" ", "-")}.pdf',
                        'uploaded_by': user
                    }
                )
                
                documents.append(document)
                if created:
                    self.stdout.write(f'Created document: {document.title}')
                else:
                    self.stdout.write(f'Document already exists: {document.title}')
        
        return documents
    
    def _create_calendar_events(self, user, labels, releases):
        events = []
        
        # Create release date events
        for release in releases:
            event, created = CalendarEvent.objects.get_or_create(
                title=f'Release: {release.title}',
                date=release.release_date,
                release=release,
                defaults={
                    'description': f'Official release date for {release.title}',
                    'label': release.label,
                    'created_by': user
                }
            )
            
            events.append(event)
            if created:
                self.stdout.write(f'Created calendar event: {event.title}')
            else:
                self.stdout.write(f'Calendar event already exists: {event.title}')
        
        # Create other events
        other_events = [
            {
                'title': 'Marketing Meeting',
                'description': 'Weekly marketing team meeting',
                'date': datetime.now().date() + timedelta(days=7),
                'label_index': 0
            },
            {
                'title': 'Artist Showcase',
                'description': 'Showcase event for label artists',
                'date': datetime.now().date() + timedelta(days=45),
                'label_index': 1
            }
        ]
        
        for data in other_events:
            label_index = data.pop('label_index', 0)
            
            if label_index < len(labels):
                event, created = CalendarEvent.objects.get_or_create(
                    title=data['title'],
                    date=data['date'],
                    label=labels[label_index],
                    defaults={
                        'description': data['description'],
                        'created_by': user
                    }
                )
                
                events.append(event)
                if created:
                    self.stdout.write(f'Created calendar event: {event.title}')
                else:
                    self.stdout.write(f'Calendar event already exists: {event.title}')
        
        return events
    
    def _create_demos(self, user, labels):
        demos = []
        demo_data = [
            {
                'title': 'Deep Journey',
                'artist_name': 'Underwater',
                'status': 'new',
                'label_index': 1
            },
            {
                'title': 'Bass Cannon',
                'artist_name': 'Heavy Hitter',
                'status': 'reviewed',
                'label_index': 0
            },
            {
                'title': 'Future Dreams',
                'artist_name': 'Tomorrow Sound',
                'status': 'accepted',
                'label_index': 2
            },
            {
                'title': 'Ambient Clouds',
                'artist_name': 'Sky Walker',
                'status': 'rejected',
                'label_index': 1
            }
        ]
        
        for data in demo_data:
            label_index = data.pop('label_index', 0)
            
            if label_index < len(labels):
                demo, created = Demo.objects.get_or_create(
                    title=data['title'],
                    artist_name=data['artist_name'],
                    defaults={
                        'audio_url': f'https://example.com/demos/{data["title"].lower().replace(" ", "-")}',
                        'status': data['status'],
                        'label': labels[label_index],
                        'submitted_by': user,
                        'review_notes': 'Sample review notes' if data['status'] in ['reviewed', 'accepted', 'rejected'] else ''
                    }
                )
                
                demos.append(demo)
                if created:
                    self.stdout.write(f'Created demo: {demo.title} by {demo.artist_name}')
                else:
                    self.stdout.write(f'Demo already exists: {demo.title}')
        
        return demos
    
    def _print_summary(self, labels, artists, releases, tracks, mixtapes, documents, events, demos):
        self.stdout.write('\nSummary of test data:')
        self.stdout.write(f'- {len(labels)} Labels')
        self.stdout.write(f'- {len(artists)} Artists')
        self.stdout.write(f'- {len(releases)} Releases')
        self.stdout.write(f'- {len(tracks)} Tracks')
        self.stdout.write(f'- {len(mixtapes)} Mixtapes')
        self.stdout.write(f'- {len(documents)} Documents')
        self.stdout.write(f'- {len(events)} Calendar Events')
        self.stdout.write(f'- {len(demos)} Demos')
