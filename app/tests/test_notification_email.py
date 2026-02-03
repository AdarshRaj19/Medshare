from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core import mail

from app.models import Notification, UserProfile

User = get_user_model()

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class NotificationEmailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='noteuser', email='user@example.com', password='testpass')
        UserProfile.objects.update_or_create(user=self.user, defaults={'role':'donor','preferred_contact_method':'email'})

    def test_notification_sends_email_on_create(self):
        Notification.objects.create(user=self.user, title='Test Note', message='This is a test')
        # One email should be in outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Test Note', mail.outbox[0].subject)
