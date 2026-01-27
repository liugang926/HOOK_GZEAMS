"""
Lifecycle Management Serializers

Provides serializers for all lifecycle management models:
- PurchaseRequest: Purchase request serializers
- AssetReceipt: Asset receipt and quality inspection serializers
- Maintenance: Maintenance record and plan serializers
- Disposal: Disposal request serializers
"""
from apps.lifecycle.serializers.purchase import (
    PurchaseRequestItemSerializer,
    PurchaseRequestListSerializer,
    PurchaseRequestDetailSerializer,
    PurchaseRequestCreateSerializer,
    PurchaseRequestUpdateSerializer,
)
from apps.lifecycle.serializers.receipt import (
    AssetReceiptItemSerializer,
    AssetReceiptListSerializer,
    AssetReceiptDetailSerializer,
    AssetReceiptCreateSerializer,
    AssetReceiptInspectionSerializer,
)
from apps.lifecycle.serializers.maintenance import (
    MaintenanceSerializer,
    MaintenanceListSerializer,
    MaintenanceDetailSerializer,
    MaintenanceCreateSerializer,
    MaintenanceAssignmentSerializer,
    MaintenanceCompletionSerializer,
    MaintenancePlanSerializer,
    MaintenancePlanListSerializer,
    MaintenanceTaskSerializer,
    MaintenanceTaskListSerializer,
    MaintenanceTaskDetailSerializer,
    MaintenanceTaskExecutionSerializer,
)
from apps.lifecycle.serializers.disposal import (
    DisposalItemSerializer,
    DisposalRequestListSerializer,
    DisposalRequestDetailSerializer,
    DisposalRequestCreateSerializer,
    DisposalRequestUpdateSerializer,
)

__all__ = [
    # Purchase Request
    'PurchaseRequestItemSerializer',
    'PurchaseRequestListSerializer',
    'PurchaseRequestDetailSerializer',
    'PurchaseRequestCreateSerializer',
    'PurchaseRequestUpdateSerializer',
    # Asset Receipt
    'AssetReceiptItemSerializer',
    'AssetReceiptListSerializer',
    'AssetReceiptDetailSerializer',
    'AssetReceiptCreateSerializer',
    'AssetReceiptInspectionSerializer',
    # Maintenance
    'MaintenanceSerializer',
    'MaintenanceListSerializer',
    'MaintenanceDetailSerializer',
    'MaintenanceCreateSerializer',
    'MaintenanceAssignmentSerializer',
    'MaintenanceCompletionSerializer',
    'MaintenancePlanSerializer',
    'MaintenancePlanListSerializer',
    'MaintenanceTaskSerializer',
    'MaintenanceTaskListSerializer',
    'MaintenanceTaskDetailSerializer',
    'MaintenanceTaskExecutionSerializer',
    # Disposal
    'DisposalItemSerializer',
    'DisposalRequestListSerializer',
    'DisposalRequestDetailSerializer',
    'DisposalRequestCreateSerializer',
    'DisposalRequestUpdateSerializer',
]
