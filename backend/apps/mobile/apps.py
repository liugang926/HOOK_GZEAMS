"""
Mobile Enhancement App Configuration
"""
from django.apps import AppConfig


class MobileConfig(AppConfig):
    """Mobile app configuration"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.mobile'
    verbose_name = 'Mobile Enhancement'
    verbose_name_plural = 'Mobile Enhancement'
