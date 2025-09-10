from django.core.management.base import BaseCommand
from django.db.models import Q
from finances.models import RevenueEvent


class Command(BaseCommand):
    help = 'Clean up blank entries in revenue data'

    def handle(self, *args, **options):
        self.stdout.write('CLEANING BLANK ENTRIES...')
        
        # Find blank Bandcamp entries
        blank_bandcamp = RevenueEvent.objects.filter(
            platform__name='Bandcamp',
            track_artist_name='',
            track_title=''
        )
        
        blank_count = blank_bandcamp.count()
        self.stdout.write(f'Found {blank_count} blank Bandcamp entries')
        
        if blank_count > 0:
            # Show sample before deletion
            self.stdout.write('Sample blank entries:')
            for entry in blank_bandcamp[:3]:
                amount = float(entry.net_amount) if entry.net_amount else 0
                date = entry.occurred_at.date() if entry.occurred_at else 'No date'
                self.stdout.write(f'  {date}: ${amount:.2f}')
            
            # Delete blank entries
            deleted_count = blank_bandcamp.delete()[0]
            self.stdout.write(f'Deleted {deleted_count} blank entries')
        
        # Also clean Distribution entries with obviously invalid data
        invalid_dist = RevenueEvent.objects.filter(
            platform__name='Distribution'
        ).filter(
            Q(track_artist_name='Unknown') & Q(track_title='Unknown') |
            Q(isrc__icontains='Exchange') |
            Q(track_title__icontains='Exchange')
        )
        
        invalid_count = invalid_dist.count()
        if invalid_count > 0:
            self.stdout.write(f'Found {invalid_count} invalid Distribution entries')
            deleted_count = invalid_dist.delete()[0]
            self.stdout.write(f'Deleted {deleted_count} invalid entries')
        
        # Final summary
        total_remaining = RevenueEvent.objects.count()
        self.stdout.write('')
        self.stdout.write(f'CLEANUP COMPLETE')
        self.stdout.write(f'Total clean records: {total_remaining:,}')
        
        bc_final = RevenueEvent.objects.filter(platform__name='Bandcamp').count()
        dist_final = RevenueEvent.objects.filter(platform__name='Distribution').count()
        
        self.stdout.write(f'Bandcamp: {bc_final:,} records')
        self.stdout.write(f'Distribution: {dist_final:,} records')
