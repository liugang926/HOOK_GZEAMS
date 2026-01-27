from django.apps import AppConfig


class LifecycleConfig(AppConfig):
    """Lifecycle app configuration"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.lifecycle'
    verbose_name = 'Lifecycle Management'
    verbose_name_plural = 'Lifecycle Management'
