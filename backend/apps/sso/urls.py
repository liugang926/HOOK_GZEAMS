"""
SSO URL Configuration

URL routes for SSO module.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.sso.views.wework_views import (
    WeWorkConfigViewSet,
    UserMappingViewSet
)
from apps.sso.views.sync_views import SyncViewSet

app_name = 'sso'

router = DefaultRouter()
# WeWork configuration management (full CRUD + batch operations)
router.register(r'configs', WeWorkConfigViewSet, basename='wework_config')
# User mapping management (full CRUD + batch operations)
router.register(r'mappings', UserMappingViewSet, basename='user_mapping')
# Sync log management (full CRUD + batch operations)
router.register(r'sync', SyncViewSet, basename='sync')

urlpatterns = [
    path('', include(router.urls)),
]
