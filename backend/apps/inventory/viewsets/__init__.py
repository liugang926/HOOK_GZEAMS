"""
ViewSets for inventory app.
"""
from apps.inventory.viewsets.task_viewsets import InventoryTaskViewSet
from apps.inventory.viewsets.scan_viewsets import InventoryScanViewSet
from apps.inventory.viewsets.snapshot_viewsets import InventorySnapshotViewSet
from apps.inventory.viewsets.difference_viewsets import InventoryDifferenceViewSet
from apps.inventory.viewsets.follow_up_runtime_viewsets import InventoryFollowUpViewSet
from apps.inventory.viewsets.reconciliation_viewsets import (
    InventoryReconciliationViewSet,
    InventoryReportViewSet,
)

__all__ = [
    'InventoryTaskViewSet',
    'InventoryScanViewSet',
    'InventorySnapshotViewSet',
    'InventoryDifferenceViewSet',
    'InventoryFollowUpViewSet',
    'InventoryReconciliationViewSet',
    'InventoryReportViewSet',
]
