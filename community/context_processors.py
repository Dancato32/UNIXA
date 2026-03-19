from community.models import Notification


def unread_notifications(request):
    """Inject unread notification count into every template context."""
    if request.user.is_authenticated:
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        return {'unread_notif_count': count}
    return {'unread_notif_count': 0}
