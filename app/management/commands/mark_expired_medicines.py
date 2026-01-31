from django.core.management.base import BaseCommand
from django.utils import timezone
from app.models import Medicine


class Command(BaseCommand):
    help = 'Auto-mark medicines as expired if their expiry date has passed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be expired without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        today = timezone.now().date()
        
        # Find medicines that are past expiry but not marked expired
        expired_medicines = Medicine.objects.filter(
            expiry_date__lt=today
        ).exclude(status='expired')
        
        count = expired_medicines.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('✓ No medicines to mark as expired'))
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'[DRY RUN] Would mark {count} medicines as expired:'))
            for med in expired_medicines[:10]:
                days_expired = (today - med.expiry_date).days
                self.stdout.write(f'  - {med.name} (Donor: {med.donor.username}, Expired {days_expired} days ago)')
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
        else:
            # Mark all as expired
            updated = 0
            for med in expired_medicines:
                med.mark_expired_if_needed()
                updated += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Marked {updated} medicines as expired')
            )
