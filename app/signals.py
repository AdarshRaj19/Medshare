
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .models import UserProfile, Notification, Medicine, PickupDelivery

# Notify on PickupDelivery status changes
@receiver(post_save, sender=PickupDelivery)
def pickup_delivery_status_notification(sender, instance: PickupDelivery, created: bool, **kwargs):
    if created:
        # Notify NGO and Donor on creation/assignment
        Notification.objects.create(
            user=instance.ngo,
            title='Pickup/Delivery Created',
            message=f"Pickup/Delivery for {instance.medicine.name} has been created.",
        )
        Notification.objects.create(
            user=instance.donor,
            title='Pickup/Delivery Created',
            message=f"Pickup/Delivery for {instance.medicine.name} has been created.",
        )
        # Only notify delivery boy if attribute exists (for future compatibility)
        delivery_boy = getattr(instance, 'delivery_boy', None)
        if delivery_boy:
            Notification.objects.create(
                user=delivery_boy,
                title='Delivery Assigned',
                message=f"You have been assigned to deliver {instance.medicine.name}.",
            )
    else:
        # Status change notifications
        if instance.status == 'picked_up':
            Notification.objects.create(
                user=instance.ngo,
                title='Medicine Picked Up',
                message=f"Your medicine {instance.medicine.name} has been picked up.",
            )
            Notification.objects.create(
                user=instance.donor,
                title='Medicine Picked Up',
                message=f"Your medicine {instance.medicine.name} has been picked up.",
            )
        elif instance.status == 'in_transit':
            Notification.objects.create(
                user=instance.ngo,
                title='In Transit',
                message=f"Your medicine {instance.medicine.name} is in transit.",
            )
            Notification.objects.create(
                user=instance.donor,
                title='In Transit',
                message=f"Your medicine {instance.medicine.name} is in transit.",
            )
        elif instance.status == 'delivered':
            Notification.objects.create(
                user=instance.ngo,
                title='Delivered',
                message=f"Your medicine {instance.medicine.name} has been delivered.",
            )
            Notification.objects.create(
                user=instance.donor,
                title='Delivered',
                message=f"Your medicine {instance.medicine.name} has been delivered.",
            )
        elif instance.status == 'unable_to_pickup':
            Notification.objects.create(
                user=instance.ngo,
                title='Unable to Pickup',
                message=f"Delivery failed for {instance.medicine.name}. Reason: {instance.unable_to_pickup_reason or 'Not specified'}.",
            )
            Notification.objects.create(
                user=instance.donor,
                title='Unable to Pickup',
                message=f"Delivery failed for {instance.medicine.name}. Reason: {instance.unable_to_pickup_reason or 'Not specified'}.",
            )

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .models import UserProfile, Notification, Medicine, PickupDelivery


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


