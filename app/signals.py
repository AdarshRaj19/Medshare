from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from .models import UserProfile
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

from .models import Notification, Medicine


@receiver(post_save, sender=User)
def ensure_profile_exists(sender, instance: User, created: bool, **kwargs):
    """
    Guarantee `user.profile` exists for authenticated template usage.
    This prevents site-wide template crashes when a User lacks a UserProfile.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=Medicine)
def auto_mark_expired_medicine(sender, instance: Medicine, **kwargs):
    """Auto-mark medicines as expired when saved (if expiry date has passed)"""
    instance.mark_expired_if_needed()


@receiver(post_save, sender=Notification)
def send_notification_email(sender, instance: Notification, created: bool, **kwargs):
    """Send email for new notifications if the user prefers email contact."""
    if not created:
        return

    user = instance.user
    if not user:
        return

    try:
        profile = user.profile
    except Exception:
        profile = None

    preferred = getattr(profile, 'preferred_contact_method', 'email') if profile else 'email'
    if preferred in ('email', 'both'):
        # If Celery is available, send email asynchronously via task
        try:
            from .tasks import send_notification_email_task
            send_notification_email_task.delay(instance.id)
        except Exception:
            # Fallback to synchronous send
            subject = instance.title or 'Notification from MedShare'
            message = instance.message or ''
            recipient = [user.email] if user.email else []
            if recipient:
                send_mail(subject, message, getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@medshare.com'), recipient, fail_silently=True)


