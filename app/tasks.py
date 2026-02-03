from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import date, timedelta

from .models import Notification, Medicine

@shared_task
def send_notification_email_task(notification_id):
    try:
        notif = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        return

    user = notif.user
    if not user or not user.email:
        return

    subject = notif.title or 'Notification from MedShare'
    message = notif.message or ''
    send_mail(subject, message, getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@medshare.com'), [user.email], fail_silently=True)

@shared_task
def expire_medicines_task(days=30):
    today = date.today()
    threshold_date = today + timedelta(days=days)

    expired_qs = Medicine.objects.filter(expiry_date__lt=today).exclude(status='expired')
    expiring_qs = Medicine.objects.filter(expiry_date__range=(today, threshold_date)).exclude(status='expired')

    for med in expired_qs:
        med.status = 'expired'
        med.save()
        Notification.objects.create(user=med.donor, title='Medicine expired', message=f'Your medicine "{med.name}" expired on {med.expiry_date}.')

    for med in expiring_qs:
        Notification.objects.create(user=med.donor, title='Medicine expiring soon', message=f'Your medicine "{med.name}" will expire on {med.expiry_date}.')
