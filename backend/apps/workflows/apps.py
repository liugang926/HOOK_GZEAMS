"""
Django app configuration for workflows app.
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WorkflowsConfig(AppConfig):
    """Configuration for the workflows application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.workflows'
    verbose_name = _('Workflows')
    verbose_name_plural = _('Workflows')

    def ready(self):
        """Import signal handlers when app is ready."""
        # Import signals here if needed in the future
        pass
