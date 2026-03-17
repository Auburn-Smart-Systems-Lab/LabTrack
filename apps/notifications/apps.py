from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Configuration for the notifications app.

    Delivers in-app and email notifications for due dates,
    overdue items, low stock alerts, and system events.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    label = 'notifications'

    def ready(self):
        import apps.notifications.signals  # noqa: F401
