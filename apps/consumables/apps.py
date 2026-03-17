from django.apps import AppConfig


class ConsumablesConfig(AppConfig):
    """Configuration for the consumables app.

    Manages lab consumable inventory (chemicals, components,
    materials), stock levels, usage tracking, and reorder alerts.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.consumables'
    label = 'consumables'

    def ready(self):
        import apps.consumables.signals  # noqa: F401
