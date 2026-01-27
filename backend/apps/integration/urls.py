"""
URL configuration for integration module.

Defines URL patterns for integration-related API endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.integration.viewsets import (
    IntegrationConfigViewSet,
    IntegrationSyncTaskViewSet,
    IntegrationLogViewSet,
    DataMappingTemplateViewSet,
)

router = DefaultRouter()
router.register(r'configs', IntegrationConfigViewSet, basename='integration-config')
router.register(r'sync-tasks', IntegrationSyncTaskViewSet, basename='integration-sync-task')
router.register(r'logs', IntegrationLogViewSet, basename='integration-log')
router.register(r'mappings', DataMappingTemplateViewSet, basename='data-mapping-template')

urlpatterns = [
    path('api/integration/', include(router.urls)),
]
