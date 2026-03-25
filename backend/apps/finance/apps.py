"""
Django app configuration for finance module.
"""
from django.apps import AppConfig


class FinanceConfig(AppConfig):
    """Configuration for the finance app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.finance'
    verbose_name = 'Finance Management'

    def ready(self):
        """Import signals when app is ready."""
        import apps.finance.signals  # noqa
