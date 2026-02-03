from django.core.management.base import BaseCommand
from app.models import Notification


class Command(BaseCommand):
    help = 'Remove old delivery-related notifications from database'

    def handle(self, *args, **options):
        # Old notification titles to remove
        old_titles = [
            'Pickup/Delivery Created',
            'Delivery Created',
            'Pickup Created',
            'Delivery Assigned',
            'Delivery Boy Assigned',
        ]

        total_deleted = 0
        for title in old_titles:
            count, _ = Notification.objects.filter(title=title).delete()
            if count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'Deleted {count} notification(s) with title: "{title}"')
                )
                total_deleted += count

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Total notifications cleaned: {total_deleted}')
        )
