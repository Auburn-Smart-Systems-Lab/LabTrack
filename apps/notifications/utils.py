"""
Utility helpers for creating in-app notifications.
"""

from django.contrib.auth import get_user_model

User = get_user_model()


def notify(recipient, title, message, level='info', link=''):
    """Create an in-app notification for a single user."""
    from apps.notifications.models import Notification

    if recipient and recipient.is_active:
        Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            level=level,
            link=link,
        )


def notify_admins(title, message, level='info', link=''):
    """Send an in-app notification to all active admin users."""
    admins = User.objects.filter(role='ADMIN', is_active=True)
    for admin in admins:
        notify(admin, title, message, level, link)
