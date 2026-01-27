"""
Notification URLs

URL configuration for notification API endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.notifications.viewsets import (
    NotificationTemplateViewSet,
    NotificationViewSet,
    NotificationLogViewSet,
    NotificationConfigViewSet,
    NotificationChannelViewSet,
    NotificationMessageViewSet,
    InAppMessageViewSet,
)

# Create router
router = DefaultRouter()

# Register ViewSets with URL prefixes
router.register(r'templates', NotificationTemplateViewSet, basename='notification-template')
router.register(r'configs', NotificationConfigViewSet, basename='notification-config')
router.register(r'logs', NotificationLogViewSet, basename='notification-log')
router.register(r'channels', NotificationChannelViewSet, basename='notification-channel')
router.register(r'messages', NotificationMessageViewSet, basename='notification-message')
router.register(r'inapp', InAppMessageViewSet, basename='inapp-message')
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
]

# App name for URL namespacing
app_name = 'notifications'
