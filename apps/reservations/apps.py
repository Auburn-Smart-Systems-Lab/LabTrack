from django.apps import AppConfig


class ReservationsConfig(AppConfig):
    """Configuration for the reservations app.

    Manages advance booking of equipment and lab spaces,
    time-slot scheduling, and conflict detection.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reservations'
    label = 'reservations'

    def ready(self):
        import apps.reservations.signals  # noqa: F401
