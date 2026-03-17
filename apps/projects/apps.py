from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    """Configuration for the projects app.

    Tracks lab projects, links them to equipment usage,
    manages project teams, timelines, and resource allocation.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.projects'
    label = 'projects'

    def ready(self):
        import apps.projects.signals  # noqa: F401
