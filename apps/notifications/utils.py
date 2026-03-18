"""
Utility helpers for creating in-app notifications and sending email alerts.
"""

import logging

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

User = get_user_model()


def _send_email(recipient, title, message, link=''):
    """Send a plain-text notification email. Silently skips if email is not configured."""
    if not recipient.email:
        return

    # Check opt-out preference (UserProfile.email_notifications).
    try:
        if not recipient.profile.email_notifications:
            return
    except Exception:
        pass  # No profile yet — fall through and send.

    body_parts = [message]
    if link:
        base_url = getattr(settings, 'SITE_URL', '').rstrip('/')
        body_parts.append(f'\nView details: {base_url}{link}')

    try:
        send_mail(
            subject=f'[LabTrack] {title}',
            message='\n'.join(body_parts),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            fail_silently=False,
        )
    except Exception as exc:
        # Log the failure but never let an email error break the request.
        logger.warning('Failed to send notification email to %s: %s', recipient.email, exc)


def notify(recipient, title, message, level='info', link=''):
    """Create an in-app notification and send an email for a single user."""
    from apps.notifications.models import Notification

    if not (recipient and recipient.is_active):
        return

    Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        level=level,
        link=link,
    )

    _send_email(recipient, title, message, link)


def notify_admins(title, message, level='info', link=''):
    """Notify all active admin users (in-app + email)."""
    admins = User.objects.filter(role='ADMIN', is_active=True)
    for admin in admins:
        notify(admin, title, message, level, link)
