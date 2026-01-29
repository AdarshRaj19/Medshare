from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=User)
def ensure_profile_exists(sender, instance: User, created: bool, **kwargs):
    """
    Guarantee `user.profile` exists for authenticated template usage.
    This prevents site-wide template crashes when a User lacks a UserProfile.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)


