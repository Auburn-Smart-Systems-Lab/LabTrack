from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration for the accounts app.

    Handles custom user model, authentication profiles,
    and role-based access control for lab members.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    label = 'accounts'

    def ready(self):
        import apps.accounts.signals  # noqa: F401
