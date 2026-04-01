"""
ViewSets for Lifecycle Management.

All ViewSets inherit from BaseModelViewSetWithBatch for standard CRUD operations
and extend with custom actions for business workflows.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.responses.base import BaseResponse
from apps.lifecycle.models import (
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseRequestStatus,
    AssetReceipt,
    AssetReceiptItem,
    AssetReceiptStatus,
    Maintenance,
    MaintenanceStatus,
    MaintenancePlan,
    MaintenanceTask,
    MaintenanceTaskStatus,
    DisposalRequest,
    DisposalItem,
    DisposalRequestStatus,
    AssetWarranty,
    AssetWarrantyStatus,
)
from apps.lifecycle.serializers import (
    # Purchase request serializers
    PurchaseRequestListSerializer,
    PurchaseRequestDetailSerializer,
    PurchaseRequestCreateSerializer,
    PurchaseRequestUpdateSerializer,
    PurchaseRequestItemSerializer,
    # Asset receipt serializers
    AssetReceiptListSerializer,
    AssetReceiptDetailSerializer,
    AssetReceiptCreateSerializer,
    AssetReceiptInspectionSerializer,
    AssetReceiptItemSerializer,
    # Maintenance serializers
    MaintenanceListSerializer,
    MaintenanceDetailSerializer,
    MaintenanceCreateSerializer,
    MaintenanceAssignmentSerializer,
    MaintenanceCompletionSerializer,
    # Maintenance plan serializers
    MaintenancePlanListSerializer,
    MaintenancePlanSerializer,
    # Maintenance task serializers
    MaintenanceTaskListSerializer,
    MaintenanceTaskDetailSerializer,
    MaintenanceTaskExecutionSerializer,
    # Disposal request serializers
    DisposalRequestListSerializer,
    DisposalRequestDetailSerializer,
    DisposalRequestCreateSerializer,
    DisposalRequestUpdateSerializer,
    DisposalItemSerializer,
    # Asset warranty serializers
    AssetWarrantyListSerializer,
    AssetWarrantyDetailSerializer,
    AssetWarrantyCreateSerializer,
    AssetWarrantyUpdateSerializer,
)
from apps.lifecycle.filters import (
    PurchaseRequestFilter,
    AssetReceiptFilter,
    MaintenanceFilter,
    MaintenancePlanFilter,
    MaintenanceTaskFilter,
    DisposalRequestFilter,
    AssetWarrantyFilter,
)
from apps.lifecycle.services import (
    PurchaseRequestService,
    AssetReceiptService,
    MaintenanceService,
    MaintenancePlanService,
    MaintenanceTaskService,
    DisposalRequestService,
    LifecycleClosedLoopService,
)


# ========== Purchase Request ViewSet ==========

class PurchaseRequestViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Purchase Request operations.

    Provides:
    - Standard CRUD operations
    - Approval workflow actions
    - M18 sync integration
    - Batch operations
    """
    queryset = PurchaseRequest.objects.all()
    filterset_class = PurchaseRequestFilter
    search_fields = ['request_no', 'reason']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return PurchaseRequestListSerializer
        elif self.action == 'create':
            return PurchaseRequestCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PurchaseRequestUpdateSerializer
        return PurchaseRequestDetailSerializer

    def create(self, request, *args, **kwargs):
        """Create purchase request with items."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = PurchaseRequestService()
        instance = service.create_with_items(serializer.validated_data, request.user)

        serializer = PurchaseRequestDetailSerializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Submit purchase request for approval.

        POST /api/lifecycle/purchase-requests/{id}/submit/
        """
        service = PurchaseRequestService()
        instance = service.submit_for_approval(pk, actor=request.user)
        serializer = PurchaseRequestDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Request submitted for approval')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve or reject purchase request.

        POST /api/lifecycle/purchase-requests/{id}/approve/
        Body: { decision: 'approved'|'rejected', comment: '' }
        """
        decision = request.data.get('decision')
        comment = request.data.get('comment')

        if decision not in ['approved', 'rejected']:
            return BaseResponse.error(message='Decision must be approved or rejected')

        service = PurchaseRequestService()
        instance = service.approve(pk, request.user, decision, comment)
        serializer = PurchaseRequestDetailSerializer(instance)

        msg = 'Request approved' if decision == 'approved' else 'Request rejected'
        return BaseResponse.success(data=serializer.data, message=msg)

    @action(detail=True, methods=['post'])
    def start_processing(self, request, pk=None):
        """
        Mark purchase request as processing (after M18 sync).

        POST /api/lifecycle/purchase-requests/{id}/start_processing/
        """
        service = PurchaseRequestService()
        instance = service.start_processing(pk, actor=request.user)
        serializer = PurchaseRequestDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Request marked as processing')

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark purchase request as completed.

        POST /api/lifecycle/purchase-requests/{id}/complete/
        """
        service = PurchaseRequestService()
        instance = service.complete(pk, actor=request.user)
        serializer = PurchaseRequestDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Request completed')

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel purchase request.

        POST /api/lifecycle/purchase-requests/{id}/cancel/
        """
        reason = request.data.get('reason', 'Cancelled')
        service = PurchaseRequestService()
        instance = service.cancel(pk, reason, actor=request.user)
        serializer = PurchaseRequestDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Request cancelled')

    @action(detail=True, methods=['post'])
    def push_to_m18(self, request, pk=None):
        """
        Push purchase request to M18 ERP system.

        POST /api/lifecycle/purchase-requests/{id}/push_to_m18/
        """
        service = PurchaseRequestService()
        instance = service.push_to_m18(pk)
        serializer = PurchaseRequestDetailSerializer(instance)
        return BaseResponse.success(
            data=serializer.data,
            message=f'Pushed to M18 as {instance.m18_purchase_order_no}'
        )

    @action(detail=False, methods=['get'])
    def pending_approval(self, request):
        """
        Get all pending purchase requests.

        GET /api/lifecycle/purchase-requests/pending_approval/
        """
        service = PurchaseRequestService()
        queryset = service.get_pending_approvals(organization_id=request.user.organization_id)
        serializer = PurchaseRequestListSerializer(queryset, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """
        Get purchase request items.

        GET /api/lifecycle/purchase-requests/{id}/items/
        """
        instance = self.get_object()
        items = instance.items.all()
        serializer = PurchaseRequestItemSerializer(items, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Get closed-loop timeline for a purchase request and downstream objects."""
        service = LifecycleClosedLoopService()
        timeline = service.build_purchase_request_timeline(self.get_object())
        return BaseResponse.success(data=timeline)


# ========== Asset Receipt ViewSet ==========

class AssetReceiptViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Asset Receipt operations.

    Provides:
    - Standard CRUD operations
    - Inspection workflow actions
    - Asset card generation
    - Batch operations
    """
    queryset = AssetReceipt.objects.all()
    filterset_class = AssetReceiptFilter
    search_fields = ['receipt_no', 'supplier', 'delivery_no']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return AssetReceiptListSerializer
        elif self.action == 'create':
            return AssetReceiptCreateSerializer
        elif self.action == 'inspect':
            return AssetReceiptInspectionSerializer
        return AssetReceiptDetailSerializer

    def create(self, request, *args, **kwargs):
        """Create asset receipt with items."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = AssetReceiptService()
        instance = service.create_with_items(serializer.validated_data, request.user)

        serializer = AssetReceiptDetailSerializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def submit_inspection(self, request, pk=None):
        """
        Submit asset receipt for inspection.

        POST /api/lifecycle/asset-receipts/{id}/submit_inspection/
        """
        service = AssetReceiptService()
        instance = service.submit_for_inspection(pk, actor=request.user)
        serializer = AssetReceiptDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Receipt submitted for inspection')

    @action(detail=True, methods=['post'])
    def inspect(self, request, pk=None):
        """
        Record inspection result for asset receipt.

        POST /api/lifecycle/asset-receipts/{id}/inspect/
        Body: { result: '', passed: true }
        """
        result = request.data.get('result', '')
        passed = request.data.get('passed', True)

        service = AssetReceiptService()
        instance = service.record_inspection_result(pk, request.user, result, passed)
        serializer = AssetReceiptDetailSerializer(instance)

        msg = 'Inspection passed' if passed else 'Inspection failed'
        return BaseResponse.success(data=serializer.data, message=msg)

    @action(detail=True, methods=['post'])
    def generate_assets(self, request, pk=None):
        """
        Generate asset cards from passed receipt items.

        POST /api/lifecycle/asset-receipts/{id}/generate_assets/
        """
        service = AssetReceiptService()
        result = service.generate_asset_cards(pk, user=request.user)
        serializer = AssetReceiptDetailSerializer(result['receipt'])
        return BaseResponse.success(
            data=serializer.data,
            message=f"Generated {result['generated_count']} asset card(s)"
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel asset receipt.

        POST /api/lifecycle/asset-receipts/{id}/cancel/
        """
        service = AssetReceiptService()
        reason = request.data.get('reason', request.data.get('comment', ''))
        instance = service.cancel(pk, reason=reason, actor=request.user)
        serializer = AssetReceiptDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Receipt cancelled')

    @action(detail=False, methods=['get'])
    def pending_inspection(self, request):
        """
        Get all receipts pending inspection.

        GET /api/lifecycle/asset-receipts/pending_inspection/
        """
        service = AssetReceiptService()
        queryset = service.get_pending_inspection(organization_id=request.user.organization_id)
        serializer = AssetReceiptListSerializer(queryset, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """
        Get asset receipt items.

        GET /api/lifecycle/asset-receipts/{id}/items/
        """
        instance = self.get_object()
        items = instance.items.all()
        serializer = AssetReceiptItemSerializer(items, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """
        Get receipt items summary.

        GET /api/lifecycle/asset-receipts/{id}/summary/
        """
        service = AssetReceiptService()
        summary = service.get_receipt_items_summary(pk)
        return BaseResponse.success(data=summary)

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Get closed-loop timeline for an asset receipt and downstream objects."""
        service = LifecycleClosedLoopService()
        timeline = service.build_receipt_timeline(self.get_object())
        return BaseResponse.success(data=timeline)


# ========== Maintenance ViewSet ==========

class MaintenanceViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Maintenance operations.

    Provides:
    - Standard CRUD operations
    - Maintenance workflow actions
    - Technician assignment
    - Work completion and verification
    """
    queryset = Maintenance.objects.all()
    filterset_class = MaintenanceFilter
    search_fields = ['maintenance_no', 'fault_description']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return MaintenanceListSerializer
        elif self.action == 'create':
            return MaintenanceCreateSerializer
        elif self.action == 'assign':
            return MaintenanceAssignmentSerializer
        elif self.action == 'complete_work':
            return MaintenanceCompletionSerializer
        return MaintenanceDetailSerializer

    def create(self, request, *args, **kwargs):
        """Create maintenance record with reporter from user."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = MaintenanceService()
        instance = service.create(serializer.validated_data, request.user)

        serializer = MaintenanceDetailSerializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """
        Assign technician to maintenance record.

        POST /api/lifecycle/maintenance/{id}/assign/
        Body: { technician_id: '' }
        """
        from apps.accounts.models import User

        technician_id = request.data.get('technician_id')
        try:
            technician = User.objects.get(id=technician_id)
        except User.DoesNotExist:
            return BaseResponse.error(message='Technician not found')

        service = MaintenanceService()
        instance = service.assign_technician(pk, technician)
        serializer = MaintenanceDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Technician assigned')

    @action(detail=True, methods=['post'])
    def start_work(self, request, pk=None):
        """
        Mark maintenance as in progress.

        POST /api/lifecycle/maintenance/{id}/start_work/
        """
        service = MaintenanceService()
        instance = service.start_work(pk)
        serializer = MaintenanceDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Work started')

    @action(detail=True, methods=['post'])
    def complete_work(self, request, pk=None):
        """
        Complete maintenance work.

        POST /api/lifecycle/maintenance/{id}/complete_work/
        """
        serializer = self.get_serializer(instance=self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        service = MaintenanceService()
        instance = service.complete_work(pk, serializer.validated_data, user=request.user)
        serializer = MaintenanceDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Work completed')

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """
        Verify completed maintenance work.

        POST /api/lifecycle/maintenance/{id}/verify/
        Body: { result: '' }
        """
        result = request.data.get('result', '')

        service = MaintenanceService()
        instance = service.verify(pk, request.user, result)
        serializer = MaintenanceDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Maintenance verified')

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel maintenance record.

        POST /api/lifecycle/maintenance/{id}/cancel/
        """
        reason = request.data.get('reason', 'Cancelled')
        service = MaintenanceService()
        instance = service.cancel(pk, reason, user=request.user)
        serializer = MaintenanceDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Maintenance cancelled')

    @action(detail=False, methods=['get'])
    def pending_assignment(self, request):
        """
        Get all maintenance records pending technician assignment.

        GET /api/lifecycle/maintenance/pending_assignment/
        """
        service = MaintenanceService()
        queryset = service.get_pending_assignment(organization_id=request.user.organization_id)
        serializer = MaintenanceListSerializer(queryset, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=False, methods=['get'])
    def urgent(self, request):
        """
        Get all urgent priority maintenance records.

        GET /api/lifecycle/maintenance/urgent/
        """
        service = MaintenanceService()
        queryset = service.get_urgent_maintenance(organization_id=request.user.organization_id)
        serializer = MaintenanceListSerializer(queryset, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get maintenance statistics summary.

        GET /api/lifecycle/maintenance/statistics/
        """
        service = MaintenanceService()
        stats = service.get_maintenance_statistics(organization_id=request.user.organization_id)
        return BaseResponse.success(data=stats)


# ========== Maintenance Plan ViewSet ==========

class MaintenancePlanViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Maintenance Plan operations.

    Provides:
    - Standard CRUD operations
    - Plan activation/pausing
    - Task generation
    - Batch operations
    """
    queryset = MaintenancePlan.objects.all()
    filterset_class = MaintenancePlanFilter
    search_fields = ['plan_code', 'plan_name', 'maintenance_content']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return MaintenancePlanListSerializer
        return MaintenancePlanSerializer

    def create(self, request, *args, **kwargs):
        """Create maintenance plan with organization from user."""
        service = MaintenancePlanService()
        data = request.data.copy()
        instance = service.create(data, request.user)
        serializer = MaintenancePlanSerializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate maintenance plan.

        POST /api/lifecycle/maintenance-plans/{id}/activate/
        """
        service = MaintenancePlanService()
        instance = service.activate(pk)
        serializer = MaintenancePlanSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Plan activated')

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """
        Pause maintenance plan.

        POST /api/lifecycle/maintenance-plans/{id}/pause/
        """
        service = MaintenancePlanService()
        instance = service.pause(pk)
        serializer = MaintenancePlanSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Plan paused')

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """
        Archive maintenance plan.

        POST /api/lifecycle/maintenance-plans/{id}/archive/
        """
        service = MaintenancePlanService()
        instance = service.archive(pk)
        serializer = MaintenancePlanSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Plan archived')

    @action(detail=True, methods=['post'])
    def generate_tasks(self, request, pk=None):
        """
        Generate maintenance tasks from plan.

        POST /api/lifecycle/maintenance-plans/{id}/generate_tasks/
        """
        service = MaintenancePlanService()
        tasks = service.generate_tasks(pk)
        return BaseResponse.success(
            data={'generated_count': len(tasks)},
            message=f'{len(tasks)} tasks generated'
        )

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get all active maintenance plans.

        GET /api/lifecycle/maintenance-plans/active/
        """
        service = MaintenancePlanService()
        queryset = service.get_active_plans(organization_id=request.user.organization_id)
        serializer = MaintenancePlanListSerializer(queryset, many=True)
        return BaseResponse.success(data=serializer.data)


# ========== Maintenance Task ViewSet ==========

class MaintenanceTaskViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Maintenance Task operations.

    Provides:
    - Standard CRUD operations
    - Task execution actions
    - Executor assignment
    - Task verification
    """
    queryset = MaintenanceTask.objects.all()
    filterset_class = MaintenanceTaskFilter
    search_fields = ['task_no', 'maintenance_content']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return MaintenanceTaskListSerializer
        elif self.action == 'execute':
            return MaintenanceTaskExecutionSerializer
        return MaintenanceTaskDetailSerializer

    @action(detail=True, methods=['post'])
    def assign_executor(self, request, pk=None):
        """
        Assign executor to maintenance task.

        POST /api/lifecycle/maintenance-tasks/{id}/assign_executor/
        """
        service = MaintenanceTaskService()
        instance = service.assign_executor(pk, request.user)
        serializer = MaintenanceTaskDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Executor assigned')

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        Complete maintenance task execution.

        POST /api/lifecycle/maintenance-tasks/{id}/execute/
        """
        serializer = self.get_serializer(instance=self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        service = MaintenanceTaskService()
        instance = service.complete_execution(pk, serializer.validated_data, request.user)
        serializer = MaintenanceTaskDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Task executed')

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """
        Verify completed maintenance task.

        POST /api/lifecycle/maintenance-tasks/{id}/verify/
        """
        result = request.data.get('result', '')

        service = MaintenanceTaskService()
        instance = service.verify(pk, request.user, result)
        serializer = MaintenanceTaskDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Task verified')

    @action(detail=True, methods=['post'])
    def skip(self, request, pk=None):
        """
        Skip maintenance task.

        POST /api/lifecycle/maintenance-tasks/{id}/skip/
        """
        reason = request.data.get('reason', 'Skipped')
        service = MaintenanceTaskService()
        instance = service.skip(pk, reason)
        serializer = MaintenanceTaskDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Task skipped')

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """
        Get all overdue maintenance tasks.

        GET /api/lifecycle/maintenance-tasks/overdue/
        """
        service = MaintenanceTaskService()
        queryset = service.get_overdue_tasks(organization_id=request.user.organization_id)
        serializer = MaintenanceTaskListSerializer(queryset, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=False, methods=['get'])
    def today(self, request):
        """
        Get tasks scheduled for today.

        GET /api/lifecycle/maintenance-tasks/today/
        """
        service = MaintenanceTaskService()
        queryset = service.get_today_tasks(organization_id=request.user.organization_id)
        serializer = MaintenanceTaskListSerializer(queryset, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=False, methods=['get'])
    def due_soon(self, request):
        """
        Get tasks due within specified days.

        GET /api/lifecycle/maintenance-tasks/due_soon/?days=7
        """
        service = MaintenancePlanService()
        days = int(request.query_params.get('days', 7))
        queryset = service.get_due_tasks(organization_id=request.user.organization_id, days=days)
        serializer = MaintenanceTaskListSerializer(queryset, many=True)
        return BaseResponse.success(data=serializer.data)


# ========== Disposal Request ViewSet ==========

class DisposalRequestViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Disposal Request operations.

    Provides:
    - Standard CRUD operations
    - Approval workflow actions
    - Technical appraisal management
    - Disposal execution tracking
    - Batch operations
    """
    queryset = DisposalRequest.objects.all()
    filterset_class = DisposalRequestFilter
    search_fields = ['request_no', 'disposal_reason']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return DisposalRequestListSerializer
        elif self.action == 'create':
            return DisposalRequestCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DisposalRequestUpdateSerializer
        return DisposalRequestDetailSerializer

    def create(self, request, *args, **kwargs):
        """Create disposal request with items."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = DisposalRequestService()
        instance = service.create_with_items(serializer.validated_data, request.user)

        serializer = DisposalRequestDetailSerializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Submit disposal request for approval.

        POST /api/lifecycle/disposal-requests/{id}/submit/
        """
        service = DisposalRequestService()
        instance = service.submit_for_approval(pk, actor=request.user)
        serializer = DisposalRequestDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Request submitted')

    @action(detail=True, methods=['post'])
    def start_appraisal(self, request, pk=None):
        """
        Start technical appraisal process.

        POST /api/lifecycle/disposal-requests/{id}/start_appraisal/
        """
        service = DisposalRequestService()
        instance = service.start_appraisal(pk, actor=request.user)
        serializer = DisposalRequestDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Appraisal process started')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve or reject disposal request.

        POST /api/lifecycle/disposal-requests/{id}/approve/
        Body: { decision: 'approved'|'rejected', comment: '' }
        """
        decision = request.data.get('decision')
        comment = request.data.get('comment')

        if decision not in ['approved', 'rejected']:
            return BaseResponse.error(message='Decision must be approved or rejected')

        service = DisposalRequestService()
        instance = service.approve(pk, request.user, decision, comment)
        serializer = DisposalRequestDetailSerializer(instance)

        msg = 'Request approved' if decision == 'approved' else 'Request rejected'
        return BaseResponse.success(data=serializer.data, message=msg)

    @action(detail=True, methods=['post'], url_path='approve-pass')
    def approve_pass(self, request, pk=None):
        """Approve a disposal request without requiring a request payload."""
        service = DisposalRequestService()
        instance = service.approve(pk, request.user, 'approved', request.data.get('comment'))
        serializer = DisposalRequestDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Request approved')

    @action(detail=True, methods=['post'])
    def start_execution(self, request, pk=None):
        """
        Start disposal execution process.

        POST /api/lifecycle/disposal-requests/{id}/start_execution/
        """
        service = DisposalRequestService()
        instance = service.start_execution(pk, actor=request.user)
        serializer = DisposalRequestDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Execution started')

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark disposal request as completed.

        POST /api/lifecycle/disposal-requests/{id}/complete/
        """
        service = DisposalRequestService()
        instance = service.complete_request(pk, actor=request.user)
        serializer = DisposalRequestDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Disposal completed')

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel disposal request.

        POST /api/lifecycle/disposal-requests/{id}/cancel/
        """
        reason = request.data.get('reason', 'Cancelled')
        service = DisposalRequestService()
        instance = service.cancel(pk, reason, actor=request.user)
        serializer = DisposalRequestDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Request cancelled')

    @action(detail=False, methods=['get'])
    def pending_appraisal(self, request):
        """
        Get all requests pending technical appraisal.

        GET /api/lifecycle/disposal-requests/pending_appraisal/
        """
        service = DisposalRequestService()
        queryset = service.get_pending_appraisal(organization_id=request.user.organization_id)
        serializer = DisposalRequestListSerializer(queryset, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=False, methods=['get'])
    def approved_for_execution(self, request):
        """
        Get all approved requests ready for execution.

        GET /api/lifecycle/disposal-requests/approved_for_execution/
        """
        service = DisposalRequestService()
        queryset = service.get_approved_for_execution(organization_id=request.user.organization_id)
        serializer = DisposalRequestListSerializer(queryset, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """
        Get disposal request items.

        GET /api/lifecycle/disposal-requests/{id}/items/
        """
        instance = self.get_object()
        items = instance.items.all()
        serializer = DisposalItemSerializer(items, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get disposal statistics summary.

        GET /api/lifecycle/disposal-requests/statistics/
        """
        service = DisposalRequestService()
        stats = service.get_disposal_statistics(organization_id=request.user.organization_id)
        return BaseResponse.success(data=stats)

    @action(detail=True, methods=['post'])
    def record_appraisal(self, request, pk=None):
        """
        Record technical appraisal for a disposal item.

        POST /api/lifecycle/disposal-requests/{id}/record_appraisal/
        Body: { item_id: '', result: '', residual_value: 0 }
        """
        from apps.lifecycle.models import DisposalItem

        item_id = request.data.get('item_id')
        result = request.data.get('result', '')
        residual_value = request.data.get('residual_value')

        if not item_id:
            return BaseResponse.error(message='item_id is required')

        service = DisposalRequestService()
        item = service.record_appraisal(item_id, request.user, result, residual_value)

        # Check if all items are appraised
        unappraised = service.get_unappraised_items(pk)
        msg = 'Appraisal recorded'
        if not unappraised.exists():
            msg += '. All items appraised, request can be approved.'

        return BaseResponse.success(message=msg)

    @action(detail=True, methods=['post'])
    def execute_disposal(self, request, pk=None):
        """
        Record disposal execution for an item.

        POST /api/lifecycle/disposal-requests/{id}/execute_disposal/
        Body: { item_id: '', actual_value: 0, buyer_info: '' }
        """
        from apps.lifecycle.models import DisposalItem

        item_id = request.data.get('item_id')
        actual_value = request.data.get('actual_value', 0)
        buyer_info = request.data.get('buyer_info', '')

        if not item_id:
            return BaseResponse.error(message='item_id is required')

        service = DisposalRequestService()
        item = service.execute_disposal(item_id, actual_value, buyer_info)

        # Check if all items are executed
        request_obj = self.get_object()
        unexecuted = request_obj.items.filter(disposal_executed=False)
        msg = 'Disposal executed'
        if not unexecuted.exists():
            msg += '. All items executed, request can be completed.'

        return BaseResponse.success(message=msg)


# ========== Asset Warranty ViewSet ==========

class AssetWarrantyViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Asset Warranty operations.

    Provides:
    - Standard CRUD operations
    - Warranty lifecycle actions (activate, expire, renew, cancel)
    - Expiring soon listing
    - Batch operations
    """
    queryset = AssetWarranty.objects.all()
    filterset_class = AssetWarrantyFilter
    search_fields = ['warranty_no', 'warranty_provider', 'contract_no']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return AssetWarrantyListSerializer
        elif self.action == 'create':
            return AssetWarrantyCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AssetWarrantyUpdateSerializer
        return AssetWarrantyDetailSerializer

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate warranty.

        POST /api/lifecycle/asset-warranties/{id}/activate/
        """
        instance = self.get_object()
        if instance.status not in [AssetWarrantyStatus.DRAFT]:
            return BaseResponse.error(message='Only draft warranties can be activated')

        from django.utils import timezone
        instance.status = AssetWarrantyStatus.ACTIVE
        instance.activated_at = timezone.now()
        instance.save()

        serializer = AssetWarrantyDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Warranty activated')

    @action(detail=True, methods=['post'])
    def expire(self, request, pk=None):
        """
        Mark warranty as expired.

        POST /api/lifecycle/asset-warranties/{id}/expire/
        """
        instance = self.get_object()
        if instance.status not in [AssetWarrantyStatus.ACTIVE, AssetWarrantyStatus.EXPIRING]:
            return BaseResponse.error(message='Only active/expiring warranties can be expired')

        from django.utils import timezone
        instance.status = AssetWarrantyStatus.EXPIRED
        instance.expired_at = timezone.now()
        instance.save()

        serializer = AssetWarrantyDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Warranty expired')

    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """
        Renew warranty with new end date.

        POST /api/lifecycle/asset-warranties/{id}/renew/
        Body: { end_date: '2027-01-01', warranty_cost: 5000 }
        """
        instance = self.get_object()
        if instance.status not in [
            AssetWarrantyStatus.ACTIVE,
            AssetWarrantyStatus.EXPIRING,
            AssetWarrantyStatus.EXPIRED
        ]:
            return BaseResponse.error(message='Cannot renew warranty in current status')

        new_end_date = request.data.get('end_date')
        if not new_end_date:
            return BaseResponse.error(message='end_date is required')

        instance.end_date = new_end_date
        instance.status = AssetWarrantyStatus.ACTIVE
        if request.data.get('warranty_cost'):
            instance.warranty_cost = request.data['warranty_cost']
        instance.save()

        serializer = AssetWarrantyDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Warranty renewed')

    @action(detail=True, methods=['post'])
    def record_claim(self, request, pk=None):
        """
        Record a warranty claim.

        POST /api/lifecycle/asset-warranties/{id}/record_claim/
        """
        instance = self.get_object()
        if instance.status not in [AssetWarrantyStatus.ACTIVE, AssetWarrantyStatus.EXPIRING]:
            return BaseResponse.error(message='Can only claim on active warranties')

        from django.utils import timezone
        instance.claim_count += 1
        instance.last_claim_date = timezone.now().date()
        instance.status = AssetWarrantyStatus.CLAIMED
        instance.save()

        serializer = AssetWarrantyDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Claim recorded')

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel warranty.

        POST /api/lifecycle/asset-warranties/{id}/cancel/
        """
        instance = self.get_object()
        instance.status = AssetWarrantyStatus.CANCELLED
        instance.save()

        serializer = AssetWarrantyDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data, message='Warranty cancelled')

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """
        Get warranties expiring within 30 days.

        GET /api/lifecycle/asset-warranties/expiring_soon/
        """
        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            status=AssetWarrantyStatus.ACTIVE,
            end_date__lte=today + timedelta(days=30),
            end_date__gte=today
        )
        serializer = AssetWarrantyListSerializer(queryset, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get warranty statistics summary.

        GET /api/lifecycle/asset-warranties/statistics/
        """
        from django.db.models import Count, Sum

        qs = self.get_queryset()
        stats = {
            'total': qs.count(),
            'active': qs.filter(status=AssetWarrantyStatus.ACTIVE).count(),
            'expiring': qs.filter(status=AssetWarrantyStatus.EXPIRING).count(),
            'expired': qs.filter(status=AssetWarrantyStatus.EXPIRED).count(),
            'total_cost': qs.aggregate(total=Sum('warranty_cost'))['total'] or 0,
            'total_claims': qs.aggregate(total=Sum('claim_count'))['total'] or 0,
        }
        return BaseResponse.success(data=stats)
