from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.core.management import call_command

from django.contrib.auth import get_user_model
from app.models import Medicine, Notification, UserProfile

User = get_user_model()

class ExpiryCommandTests(TestCase):
    def setUp(self):
        self.donor = User.objects.create_user(username='exp_donor', password='testpass')
        UserProfile.objects.update_or_create(user=self.donor, defaults={'role':'donor'})

        today = timezone.now().date()
        # expired medicine
        self.med_expired = Medicine.objects.create(donor=self.donor, name='MedExpired', quantity=1, expiry_date=today - timedelta(days=1))
        # expiring soon
        self.med_expiring = Medicine.objects.create(donor=self.donor, name='MedExpiring', quantity=1, expiry_date=today + timedelta(days=10))
        # far future
        self.med_ok = Medicine.objects.create(donor=self.donor, name='MedOk', quantity=1, expiry_date=today + timedelta(days=365))

    def test_expire_command_creates_notifications_and_marks_expired(self):
        # run command with default 30-day threshold
        call_command('expire_medicines')

        # expired medicine should be marked
        m = Medicine.objects.get(pk=self.med_expired.pk)
        self.assertEqual(m.status, 'expired')

        # notifications for expired and expiring
        notes = Notification.objects.filter(user=self.donor)
        titles = set(notes.values_list('title', flat=True))
        self.assertIn('Medicine expired', titles)
        self.assertIn('Medicine expiring soon', titles)

        # ensure far-future medicine did not get notified
        self.assertFalse(notes.filter(message__icontains='MedOk').exists())
