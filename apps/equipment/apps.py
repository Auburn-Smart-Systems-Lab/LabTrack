from django.apps import AppConfig


class EquipmentConfig(AppConfig):
    """Configuration for the equipment app.

    Manages lab equipment inventory including categories,
    items, conditions, and availability tracking.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.equipment'
    label = 'equipment'

    def ready(self):
        import apps.equipment.signals  # noqa: F401
