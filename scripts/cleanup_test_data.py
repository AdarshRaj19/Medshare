import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from app.models import Medicine, Conversation, Message
from django.conf import settings
from django.core.mail import send_mail

# Mark messages for test_ngo as read
ngo = User.objects.filter(username='test_ngo').first()
if ngo:
    updated = Message.objects.filter(conversation__ngo=ngo, is_read=False).exclude(sender=ngo).update(is_read=True)
    print('Marked messages as read for test_ngo:', updated)

# Delete test medicine and related conversations/messages
med = Medicine.objects.filter(name='TestMedForNotif').first()
if med:
    print('Deleting medicine and related conversations/messages...')
    med.delete()

# Delete test users
for uname in ['test_donor', 'test_ngo']:
    u = User.objects.filter(username=uname).first()
    if u:
        try:
            u.delete()
            print('Deleted user', uname)
        except Exception as e:
            print('Error deleting', uname, e)

# Try sending real email if SMTP configured
email_backend = getattr(settings, 'EMAIL_BACKEND', '')
if 'smtp' in email_backend.lower() and getattr(settings, 'EMAIL_HOST_USER', ''):
    try:
        send_mail('MedShare SMTP Test', 'This is an SMTP test from your MedShare instance.', settings.DEFAULT_FROM_EMAIL, ['ngo@example.com'], fail_silently=False)
        print('SMTP test email sent')
    except Exception as e:
        print('SMTP send failed:', e)
else:
    print('SMTP not configured; current EMAIL_BACKEND =', email_backend)
