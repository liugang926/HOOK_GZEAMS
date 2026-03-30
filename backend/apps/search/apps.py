"""Django application configuration for smart search."""
from django.apps import AppConfig


class SearchConfig(AppConfig):
    """Configuration for the smart search app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.search'
    verbose_name = 'Smart Search'

    def ready(self):
        """Register search signal handlers."""
        import apps.search.signals  # noqa: F401
