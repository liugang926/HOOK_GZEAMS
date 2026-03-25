"""
URL configuration for permissions app.

Registers all permission-related ViewSets with the router.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.permissions.viewsets.field_permission_viewsets import FieldPermissionViewSet
from apps.permissions.viewsets.data_permission_viewsets import DataPermissionViewSet
from apps.permissions.viewsets.data_permission_expand_viewsets import DataPermissionExpandViewSet
from apps.permissions.viewsets.permission_audit_log_viewsets import PermissionAuditLogViewSet

# Create router for permissions app
router = DefaultRouter()
router.register(r'field-permissions', FieldPermissionViewSet, basename='field-permission')
router.register(r'data-permissions', DataPermissionViewSet, basename='data-permission')
router.register(r'data-permission-expands', DataPermissionExpandViewSet, basename='data-permission-expand')
router.register(r'audit-logs', PermissionAuditLogViewSet, basename='permission-audit-log')

app_name = 'permissions'

urlpatterns = [
    path('', include(router.urls)),
]

# Available URL patterns:
#
# Field Permissions:
# - GET /api/permissions/field-permissions/ - List field permissions
# - POST /api/permissions/field-permissions/ - Create field permission
# - GET /api/permissions/field-permissions/{id}/ - Retrieve field permission
# - PUT/PATCH /api/permissions/field-permissions/{id}/ - Update field permission
# - DELETE /api/permissions/field-permissions/{id}/ - Delete field permission
# - GET /api/permissions/field-permissions/by_content_type/ - Get by content type
# - POST /api/permissions/field-permissions/grant/ - Grant field permission
# - POST /api/permissions/field-permissions/revoke/ - Revoke field permissions
# - POST /api/permissions/field-permissions/batch-delete/ - Batch delete
# - POST /api/permissions/field-permissions/batch-restore/ - Batch restore
# - POST /api/permissions/field-permissions/batch-update/ - Batch update
# - GET /api/permissions/field-permissions/deleted/ - List deleted
#
# Data Permissions:
# - GET /api/permissions/data-permissions/ - List data permissions
# - POST /api/permissions/data-permissions/ - Create data permission
# - GET /api/permissions/data-permissions/{id}/ - Retrieve data permission
# - PUT/PATCH /api/permissions/data-permissions/{id}/ - Update data permission
# - DELETE /api/permissions/data-permissions/{id}/ - Delete data permission
# - GET /api/permissions/data-permissions/by_content_type/ - Get by content type
# - POST /api/permissions/data-permissions/grant/ - Grant data permission
# - POST /api/permissions/data-permissions/revoke/ - Revoke data permissions
# - POST /api/permissions/data-permissions/batch-delete/ - Batch delete
# - POST /api/permissions/data-permissions/batch-restore/ - Batch restore
# - POST /api/permissions/data-permissions/batch-update/ - Batch update
# - GET /api/permissions/data-permissions/deleted/ - List deleted
#
# Data Permission Expansions:
# - GET /api/permissions/data-permission-expands/ - List expansions
# - POST /api/permissions/data-permission-expands/ - Create expansion
# - GET /api/permissions/data-permission-expands/{id}/ - Retrieve expansion
# - PUT/PATCH /api/permissions/data-permission-expands/{id}/ - Update expansion
# - DELETE /api/permissions/data-permission-expands/{id}/ - Delete expansion
# - GET /api/permissions/data-permission-expands/by_data_permission/ - Get by data permission
# - POST /api/permissions/data-permission-expands/{id}/activate/ - Activate expansion
# - POST /api/permissions/data-permission-expands/{id}/deactivate/ - Deactivate expansion
#
# Audit Logs:
# - GET /api/permissions/audit-logs/ - List audit logs (read-only)
# - GET /api/permissions/audit-logs/{id}/ - Retrieve audit log
# - GET /api/permissions/audit-logs/by_user/ - Get by user
# - GET /api/permissions/audit-logs/statistics/ - Get statistics
