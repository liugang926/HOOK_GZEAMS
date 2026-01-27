from django.apps import AppConfig


class DepreciationConfig(AppConfig):
    """Depreciation module configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.depreciation'
    verbose_name = 'Asset Depreciation'
