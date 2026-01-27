"""
Notification ViewSets Package

Contains all ViewSets for the notification module.
"""
from .notification_viewsets import (
    NotificationTemplateViewSet,
    NotificationViewSet,
    NotificationLogViewSet,
    NotificationConfigViewSet,
    NotificationChannelViewSet,
    NotificationMessageViewSet,
    InAppMessageViewSet,
)
from .notification_viewsets import (
    SendNotificationAction,
    BatchSendNotificationAction,
    MarkAsReadAction,
    MarkAllAsReadAction,
    GetUnreadCountAction,
)


__all__ = [
    # ViewSets
    'NotificationTemplateViewSet',
    'NotificationViewSet',
    'NotificationLogViewSet',
    'NotificationConfigViewSet',
    'NotificationChannelViewSet',
    'NotificationMessageViewSet',
    'InAppMessageViewSet',
    # Custom actions
    'SendNotificationAction',
    'BatchSendNotificationAction',
    'MarkAsReadAction',
    'MarkAllAsReadAction',
    'GetUnreadCountAction',
]
