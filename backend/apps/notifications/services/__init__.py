"""
Notification Services Package

Exports service singletons for notification management.
"""
from .template_service import TemplateService, template_service
from .notification_service import NotificationService, notification_service


__all__ = [
    # Template service
    'TemplateService',
    'template_service',
    # Notification service
    'NotificationService',
    'notification_service',
]
