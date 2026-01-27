"""
ViewSets for inventory app.
"""
from apps.inventory.viewsets.task_viewsets import InventoryTaskViewSet
from apps.inventory.viewsets.scan_viewsets import InventoryScanViewSet
from apps.inventory.viewsets.snapshot_viewsets import InventorySnapshotViewSet
from apps.inventory.viewsets.difference_viewsets import InventoryDifferenceViewSet

__all__ = [
    'InventoryTaskViewSet',
    'InventoryScanViewSet',
    'InventorySnapshotViewSet',
    'InventoryDifferenceViewSet',
]
