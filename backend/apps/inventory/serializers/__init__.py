"""
Serializers for inventory app.
"""
from apps.inventory.serializers.task_serializers import (
    InventoryTaskExecutorSerializer,
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
    InventoryDifferenceAssignOwnerSerializer,
    InventoryDifferenceSubmitReviewSerializer,
    InventoryDifferenceDraftSerializer,
    InventoryDifferenceDecisionSerializer,
    InventoryDifferenceExecuteSerializer,
    InventoryDifferenceFollowUpSerializer,
    InventoryDifferenceIgnoreSerializer,
    InventoryDifferenceCloseSerializer,
    InventoryDifferenceCompleteFollowUpSerializer,
    InventoryDifferenceReopenFollowUpSerializer,
)
from apps.inventory.serializers.follow_up_runtime_serializers import (
    InventoryFollowUpSerializer,
    InventoryFollowUpListSerializer,
    InventoryFollowUpCompleteSerializer,
    InventoryFollowUpReopenSerializer,
)
from apps.inventory.serializers.reconciliation_serializers import (
    InventoryReconciliationSerializer,
    InventoryReconciliationListSerializer,
    InventoryReconciliationCreateSerializer,
    InventoryReconciliationDecisionSerializer,
    InventoryReportSerializer,
    InventoryReportListSerializer,
    InventoryReportCreateSerializer,
    InventoryReportDecisionSerializer,
)

__all__ = [
    # Task serializers
    'InventoryTaskExecutorSerializer',
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
    'InventoryDifferenceAssignOwnerSerializer',
    'InventoryDifferenceSubmitReviewSerializer',
    'InventoryDifferenceDraftSerializer',
    'InventoryDifferenceDecisionSerializer',
    'InventoryDifferenceExecuteSerializer',
    'InventoryDifferenceFollowUpSerializer',
    'InventoryDifferenceIgnoreSerializer',
    'InventoryDifferenceCloseSerializer',
    'InventoryDifferenceCompleteFollowUpSerializer',
    'InventoryDifferenceReopenFollowUpSerializer',
    # Follow-up serializers
    'InventoryFollowUpSerializer',
    'InventoryFollowUpListSerializer',
    'InventoryFollowUpCompleteSerializer',
    'InventoryFollowUpReopenSerializer',
    # Reconciliation and report serializers
    'InventoryReconciliationSerializer',
    'InventoryReconciliationListSerializer',
    'InventoryReconciliationCreateSerializer',
    'InventoryReconciliationDecisionSerializer',
    'InventoryReportSerializer',
    'InventoryReportListSerializer',
    'InventoryReportCreateSerializer',
    'InventoryReportDecisionSerializer',
]
