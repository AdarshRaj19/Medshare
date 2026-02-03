from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta

from app.models import Medicine, Notification


class Command(BaseCommand):
    help = 'Mark expired medicines and notify donors of expiring medicines (default threshold=30 days)'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30, help='Threshold days to consider expiring soon')

    def handle(self, *args, **options):
        days = options.get('days', 30)
        today = date.today()
        threshold_date = today + timedelta(days=days)

        expired_qs = Medicine.objects.filter(expiry_date__lt=today).exclude(status='expired')
        expiring_qs = Medicine.objects.filter(expiry_date__range=(today, threshold_date)).exclude(status='expired')

        expired_count = 0
        expiring_count = 0

        for med in expired_qs:
            med.status = 'expired'
            med.save()
            Notification.objects.create(
                user=med.donor,
                title='Medicine expired',
                message=f'Your medicine "{med.name}" expired on {med.expiry_date}.',
            )
            expired_count += 1

        for med in expiring_qs:
            # Create a notification for expiring soon
            Notification.objects.create(
                user=med.donor,
                title='Medicine expiring soon',
                message=f'Your medicine "{med.name}" will expire on {med.expiry_date}.',
            )
            expiring_count += 1

        self.stdout.write(self.style.SUCCESS(f'Processed expired ({expired_count}) and expiring ({expiring_count}) medicines.'))
