from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """Configuration for the dashboard app.

    Provides the main landing page with summary statistics,
    quick-action widgets, and recent activity overviews.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'
    label = 'dashboard'

    def ready(self):
        pass  # No signals needed for the dashboard app
