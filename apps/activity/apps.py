from django.apps import AppConfig


class ActivityConfig(AppConfig):
    """Configuration for the activity app.

    Records an audit trail of all significant user actions
    across the system for accountability and reporting.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.activity'
    label = 'activity'

    def ready(self):
        import apps.activity.signals  # noqa: F401
