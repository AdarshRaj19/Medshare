from .models import Notification


def global_ui_state(request):
    """
    Provide common template variables used across the site (base layout).
    """
    unread_notifications_count = 0

    if request.user.is_authenticated:
        unread_notifications_count = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()

    return {
        "unread_notifications_count": unread_notifications_count,
    }


