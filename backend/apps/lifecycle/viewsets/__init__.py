"""
Lifecycle Management ViewSets

Provides ViewSets for all lifecycle management models:
- Purchase Request ViewSet: Purchase request CRUD and workflow actions
- Asset Receipt ViewSet: Asset receipt CRUD and inspection actions
- Maintenance ViewSet: Maintenance record CRUD and workflow actions
- Maintenance Plan ViewSet: Maintenance plan CRUD and scheduling actions
- Maintenance Task ViewSet: Maintenance task CRUD and execution actions
- Disposal Request ViewSet: Disposal request CRUD and workflow actions
"""
from apps.lifecycle.viewsets.lifecycle_viewset import (
    PurchaseRequestViewSet,
    AssetReceiptViewSet,
    MaintenanceViewSet,
    MaintenancePlanViewSet,
    MaintenanceTaskViewSet,
    DisposalRequestViewSet,
)

__all__ = [
    'PurchaseRequestViewSet',
    'AssetReceiptViewSet',
    'MaintenanceViewSet',
    'MaintenancePlanViewSet',
    'MaintenanceTaskViewSet',
    'DisposalRequestViewSet',
]
