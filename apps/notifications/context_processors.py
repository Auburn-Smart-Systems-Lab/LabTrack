"""
Context processors for the notifications app.

Injects notification data into every template context so that
the base layout can display an unread-count badge and a dropdown
of recent unread notifications without each view needing to pass
them explicitly.
"""


def unread_notifications(request):
    """
    Adds the count and a short list of recent unread notifications for the
    currently authenticated user to the template context.

    Returns an empty/zero context for anonymous users.
    """
    if request.user.is_authenticated:
        try:
            from apps.notifications.models import Notification

            count = Notification.objects.filter(
                recipient=request.user, is_read=False
            ).count()

            recent = Notification.objects.filter(
                recipient=request.user, is_read=False
            ).order_by('-created_at')[:5]

            return {
                'unread_notification_count': count,
                'recent_notifications': recent,
            }
        except Exception:
            # Gracefully degrade if the table doesn't exist yet (before migrations).
            return {
                'unread_notification_count': 0,
                'recent_notifications': [],
            }

    return {
        'unread_notification_count': 0,
        'recent_notifications': [],
    }
