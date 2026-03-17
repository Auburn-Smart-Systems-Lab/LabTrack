from django.apps import AppConfig


class IncidentsConfig(AppConfig):
    """Configuration for the incidents app.

    Records equipment damage, safety incidents, maintenance
    requests, and tracks their resolution lifecycle.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.incidents'
    label = 'incidents'

    def ready(self):
        import apps.incidents.signals  # noqa: F401
