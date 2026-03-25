from django.apps import AppConfig


class ConsumablesConfig(AppConfig):
    """Consumables app configuration"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.consumables'
    verbose_name = 'Consumables Management'
    verbose_name_plural = 'Consumables Management'
