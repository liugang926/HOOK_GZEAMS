"""
Mobile Enhancement ViewSets.

Provides ViewSets for all mobile models with custom actions.
All ViewSets inherit from BaseModelViewSetWithBatch.
"""
from apps.mobile.viewsets.device import (
    MobileDeviceViewSet,
    DeviceSecurityLogViewSet,
)
from apps.mobile.viewsets.sync import (
    DataSyncViewSet,
    SyncConflictViewSet,
    SyncLogViewSet,
)
from apps.mobile.viewsets.approval import (
    MobileApprovalViewSet,
    ApprovalDelegateViewSet,
)

__all__ = [
    # Device
    'MobileDeviceViewSet',
    'DeviceSecurityLogViewSet',
    # Sync
    'DataSyncViewSet',
    'SyncConflictViewSet',
    'SyncLogViewSet',
    # Approval
    'MobileApprovalViewSet',
    'ApprovalDelegateViewSet',
]
