from django.apps import AppConfig


class BorrowingConfig(AppConfig):
    """Configuration for the borrowing app.

    Handles equipment check-out and check-in workflows,
    due dates, overdue tracking, and return confirmations.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.borrowing'
    label = 'borrowing'

    def ready(self):
        import apps.borrowing.signals  # noqa: F401
