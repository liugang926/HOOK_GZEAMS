"""
Serializers for inventory app.
"""
from apps.inventory.serializers.task_serializers import (
    InventoryTaskListSerializer,
    InventoryTaskDetailSerializer,
    InventoryTaskCreateSerializer,
    InventoryTaskUpdateSerializer,
    InventoryTaskStartSerializer,
    InventoryTaskCompleteSerializer,
)
from apps.inventory.serializers.scan_serializers import (
    InventoryScanListSerializer,
    InventoryScanDetailSerializer,
    InventoryScanCreateSerializer,
    InventoryScanUpdateSerializer,
    InventoryBatchScanSerializer,
    InventoryScanValidateSerializer,
)
from apps.inventory.serializers.snapshot_serializers import (
    InventorySnapshotSerializer,
    InventorySnapshotListSerializer,
)
from apps.inventory.serializers.difference_serializers import (
    InventoryDifferenceSerializer,
    InventoryDifferenceListSerializer,
    InventoryDifferenceResolveSerializer,
)

__all__ = [
    # Task serializers
    'InventoryTaskListSerializer',
    'InventoryTaskDetailSerializer',
    'InventoryTaskCreateSerializer',
    'InventoryTaskUpdateSerializer',
    'InventoryTaskStartSerializer',
    'InventoryTaskCompleteSerializer',
    # Scan serializers
    'InventoryScanListSerializer',
    'InventoryScanDetailSerializer',
    'InventoryScanCreateSerializer',
    'InventoryScanUpdateSerializer',
    'InventoryBatchScanSerializer',
    'InventoryScanValidateSerializer',
    # Snapshot serializers
    'InventorySnapshotSerializer',
    'InventorySnapshotListSerializer',
    # Difference serializers
    'InventoryDifferenceSerializer',
    'InventoryDifferenceListSerializer',
    'InventoryDifferenceResolveSerializer',
]
