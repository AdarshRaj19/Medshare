from django.db.models import Q
from .models import Notification, Message


def global_ui_state(request):
    """
    Provide common template variables used across the site (base layout).
    Includes unread notifications and unread messages count.
    """
    unread_notifications_count = 0
    unread_messages_count = 0

    if request.user.is_authenticated:
        unread_notifications_count = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()

        # Messages not sent by the user and not marked read
        unread_messages_count = Message.objects.filter(
            Q(conversation__donor=request.user) | Q(conversation__ngo=request.user),
            is_read=False
        ).exclude(sender=request.user).count()

    # Suppress flash messages on messaging pages to avoid duplicating chat content
    suppress_flash_messages = False
    try:
        path = request.path or ''
        if path.startswith('/messages/') or path.startswith('/messages'):
            suppress_flash_messages = True
    except Exception:
        suppress_flash_messages = False

    return {
        "unread_notifications_count": unread_notifications_count,
        "unread_messages_count": unread_messages_count,
        "suppress_flash_messages": suppress_flash_messages,
    }


