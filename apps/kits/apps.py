from django.apps import AppConfig


class KitsConfig(AppConfig):
    """Configuration for the kits app.

    Manages lab kits that bundle multiple pieces of equipment
    and consumables into a single borrowable unit.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.kits'
    label = 'kits'

    def ready(self):
        import apps.kits.signals  # noqa: F401
