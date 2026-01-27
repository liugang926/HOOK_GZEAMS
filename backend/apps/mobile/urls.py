"""
URL Configuration for Mobile Enhancement Module.

Defines URL routes for all mobile ViewSets including:
- Device management endpoints
- Data synchronization endpoints
- Conflict resolution endpoints
- Mobile approval endpoints
- Delegation management endpoints
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.mobile.viewsets import (
    # Device
    MobileDeviceViewSet,
    DeviceSecurityLogViewSet,
    # Sync
    DataSyncViewSet,
    SyncConflictViewSet,
    SyncLogViewSet,
    # Approval
    MobileApprovalViewSet,
    ApprovalDelegateViewSet,
)

# Create router for mobile endpoints
router = DefaultRouter()
router.trailing_slash = '/'

# ========== Device Routes ==========
router.register(r'devices', MobileDeviceViewSet, basename='mobile-device')
router.register(r'security-logs', DeviceSecurityLogViewSet, basename='device-security-log')

# ========== Sync Routes ==========
router.register(r'sync', DataSyncViewSet, basename='data-sync')
router.register(r'conflicts', SyncConflictViewSet, basename='sync-conflict')
router.register(r'sync-logs', SyncLogViewSet, basename='sync-log')

# ========== Approval Routes ==========
router.register(r'approvals', MobileApprovalViewSet, basename='mobile-approval')
router.register(r'delegates', ApprovalDelegateViewSet, basename='approval-delegate')

app_name = 'mobile'

urlpatterns = [
    path('', include(router.urls)),
]

# ========== URL Summary ==========
"""
Device Management Endpoints:
- GET    /api/mobile/devices/                    List devices
- POST   /api/mobile/devices/                    Create device
- GET    /api/mobile/devices/{id}/               Get device details
- PUT    /api/mobile/devices/{id}/               Update device
- DELETE /api/mobile/devices/{id}/               Delete device
- POST   /api/mobile/devices/register/           Register new device
- POST   /api/mobile/devices/{id}/unbind/        Unbind device
- GET    /api/mobile/devices/my_devices/         Get current user's devices
- POST   /api/mobile/devices/batch_unbind/       Batch unbind devices

Security Log Endpoints (Read-only):
- GET    /api/mobile/security-logs/              List security logs
- GET    /api/mobile/security-logs/{id}/         Get log details

Data Sync Endpoints:
- GET    /api/mobile/sync/                       List offline data
- POST   /api/mobile/sync/                       Create offline data
- POST   /api/mobile/sync/upload/                Upload offline data
- POST   /api/mobile/sync/download/              Download server changes
- POST   /api/mobile/sync/resolve_conflict/      Resolve conflict
- GET    /api/mobile/sync/pending_count/         Get pending count
- POST   /api/mobile/sync/sync_all/              Full synchronization

Conflict Endpoints:
- GET    /api/mobile/conflicts/                  List conflicts
- GET    /api/mobile/conflicts/pending/          Get pending conflicts
- POST   /api/mobile/conflicts/{id}/resolve/     Resolve specific conflict

Sync Log Endpoints (Read-only):
- GET    /api/mobile/sync-logs/                  List sync logs
- GET    /api/mobile/sync-logs/{id}/             Get log details

Approval Endpoints:
- GET    /api/mobile/approvals/pending/          Get pending approvals
- POST   /api/mobile/approvals/approve/          Execute approval
- POST   /api/mobile/approvals/batch_approve/    Batch approve
- POST   /api/mobile/approvals/delegate/         Set up delegation
- POST   /api/mobile/approvals/{id}/revoke/      Revoke delegation
- GET    /api/mobile/approvals/my_delegations/   Get user's delegations

Delegate Endpoints:
- GET    /api/mobile/delegates/                  List delegations
- GET    /api/mobile/delegates/active/           Get active delegations
- POST   /api/mobile/delegates/{id}/activate/    Activate delegation
- POST   /api/mobile/delegates/{id}/deactivate/  Deactivate delegation
"""
