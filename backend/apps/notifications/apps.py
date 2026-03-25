"""
Notifications App Configuration
"""
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Notifications app configuration."""

    name = 'apps.notifications'
    verbose_name = 'Notifications'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        """Import signals when app is ready."""
        # import apps.notifications.signals  # noqa
        pass
