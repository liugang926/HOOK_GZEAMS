"""
Django app configuration for permissions app.
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PermissionsConfig(AppConfig):
    """Configuration for permissions app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.permissions'
    verbose_name = _('Permissions')
    verbose_name_plural = _('Permissions')

    def ready(self):
        """Perform initialization when app is ready."""
        # Import signal handlers if needed
        # from apps.permissions import signals
        pass
