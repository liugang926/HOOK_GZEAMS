"""
ViewSets for Asset Operation Models (Pickup, Transfer, Return, Loan).

All ViewSets inherit from BaseModelViewSetWithBatch for standard CRUD operations
and batch operation support.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.responses.base import BaseResponse
from apps.assets.models import (
    AssetPickup,
    PickupItem,
    AssetTransfer,
    TransferItem,
    AssetReturn,
    ReturnItem,
    AssetLoan,
    LoanItem,
)
from apps.assets.serializers.operation import (
    # Pickup serializers
    AssetPickupListSerializer,
    AssetPickupDetailSerializer,
    AssetPickupCreateSerializer,
    AssetPickupUpdateSerializer,
    AssetPickupSerializer,
    PickupApprovalSerializer,
    PickupItemSerializer,
    # Transfer serializers
    AssetTransferListSerializer,
    AssetTransferDetailSerializer,
    AssetTransferCreateSerializer,
    AssetTransferSerializer,
    TransferApprovalSerializer,
    TransferItemSerializer,
    # Return serializers
    AssetReturnListSerializer,
    AssetReturnDetailSerializer,
    AssetReturnCreateSerializer,
    AssetReturnSerializer,
    ReturnConfirmSerializer,
    ReturnItemSerializer,
    # Loan serializers
    AssetLoanListSerializer,
    AssetLoanDetailSerializer,
    AssetLoanCreateSerializer,
    AssetLoanSerializer,
    LoanApprovalSerializer,
    LoanReturnConfirmSerializer,
    LoanItemSerializer,
)
from apps.assets.services.operation_service import (
    AssetPickupService,
    AssetTransferService,
    AssetReturnService,
    AssetLoanService,
)
from apps.assets.services.workflow_integration import AssetWorkflowIntegration
from apps.assets.filters.operation import (
    AssetPickupFilter,
    AssetTransferFilter,
    AssetReturnFilter,
    AssetLoanFilter,
)


# ========== Pickup Order ViewSet ==========

class AssetPickupViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Asset Pickup Order operations.

    Provides:
    - Standard CRUD operations (inherited)
    - Batch operations (inherited)
    - approve(): Approve or reject pickup order
    - submit(): Submit for approval
    - complete(): Mark as completed
    - cancel(): Cancel pickup order
    - items(): Manage pickup items
    """
    queryset = AssetPickup.objects.select_related(
        'applicant', 'department', 'approved_by', 'created_by'
    ).all()
    filterset_class = AssetPickupFilter
    service = AssetPickupService()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return AssetPickupListSerializer
        elif self.action == 'create':
            return AssetPickupCreateSerializer
        elif self.action == 'update':
            return AssetPickupUpdateSerializer
        elif self.action == 'retrieve':
            return AssetPickupDetailSerializer
        return AssetPickupSerializer

    def create(self, request, *args, **kwargs):
        """Create pickup order with items."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items = serializer.validated_data.pop('items', [])

        organization_id = getattr(request, 'organization_id', None)

        pickup = self.service.create_with_items(
            serializer.validated_data,
            items,
            request.user,
            organization_id
        )

        response_serializer = AssetPickupDetailSerializer(pickup)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Pickup order created successfully',
            http_status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        """
        Submit pickup order for approval.

        Integrates with workflow engine:
        - If a workflow is defined for asset_pickup, starts the workflow
        - If no workflow is defined, auto-approves immediately
        """
        pickup = self.get_object()

        organization_id = getattr(request, 'organization_id', None) or pickup.organization_id

        # Try to start workflow integration
        success, workflow_instance, error = AssetWorkflowIntegration.start_operation_workflow(
            process_key=AssetWorkflowIntegration.PROCESS_PICKUP,
            operation_instance=pickup,
            initiator=request.user,
            organization_id=str(organization_id)
        )

        if not success and workflow_instance is None:
            # No workflow configured, auto-approve using legacy flow
            pickup = self.service.submit_for_approval(pk, request.user)
            pickup = self.service.approve(pk, request.user, 'approved', 'Auto-approved (no workflow)')
        elif not success:
            return BaseResponse.error(
                code='WORKFLOW_START_FAILED',
                message=error or 'Failed to start workflow'
            )
        else:
            # Workflow started successfully, update pickup status
            pickup = self.service.submit_for_approval(pk, request.user)
            pickup.status = 'pending'
            pickup.workflow_instance_id = str(workflow_instance.id) if workflow_instance else None
            pickup.save(update_fields=['status', 'workflow_instance_id', 'updated_at'])

        response_serializer = AssetPickupDetailSerializer(pickup)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Pickup order submitted for approval'
        )

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """Approve or reject pickup order."""
        serializer = PickupApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pickup = self.service.approve(
            pk,
            request.user,
            serializer.validated_data['approval'],
            serializer.validated_data.get('comment', '')
        )

        response_serializer = AssetPickupDetailSerializer(pickup)
        message = 'Pickup order approved' if serializer.validated_data['approval'] == 'approved' else 'Pickup order rejected'
        return BaseResponse.success(
            data=response_serializer.data,
            message=message
        )

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """Mark pickup order as completed."""
        pickup = self.service.complete_pickup(pk, request.user)
        response_serializer = AssetPickupDetailSerializer(pickup)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Pickup order completed'
        )

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """Cancel pickup order."""
        pickup = self.service.cancel_pickup(pk, request.user)
        response_serializer = AssetPickupDetailSerializer(pickup)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Pickup order cancelled'
        )

    @action(detail=True, methods=['get', 'post'], url_path='items')
    def items(self, request, pk=None):
        """Manage pickup items."""
        pickup = self.get_object()

        if request.method == 'GET':
            items = pickup.items.all()
            serializer = PickupItemSerializer(items, many=True)
            return BaseResponse.success(data=serializer.data)

        # POST - Add item
        serializer = PickupItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        asset_id = serializer.validated_data.pop('asset_id')
        from apps.assets.models import Asset
        try:
            asset = Asset.objects.get(id=asset_id)
            serializer.validated_data['asset'] = asset
            serializer.validated_data['snapshot_original_location'] = asset.location
            serializer.validated_data['snapshot_original_custodian'] = asset.custodian
        except Asset.DoesNotExist:
            return Response({
                'success': False,
                'error': {'code': 'NOT_FOUND', 'message': 'Asset not found'}
            }, status=status.HTTP_404_NOT_FOUND)

        serializer.save(pickup=pickup)
        return BaseResponse.success(
            data=serializer.data,
            message='Item added successfully',
            http_status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='workflow-callback')
    def workflow_callback(self, request, pk=None):
        """
        Handle workflow completion callback.

        Called by workflow engine when a workflow instance is completed.
        Updates the pickup order status based on workflow result.
        """
        from apps.workflows.models import WorkflowInstance

        pickup = self.get_object()
        workflow_instance_id = request.data.get('workflow_instance_id')

        if not workflow_instance_id:
            return BaseResponse.error(
                code='MISSING_WORKFLOW_ID',
                message='Workflow instance ID is required'
            )

        try:
            workflow_instance = WorkflowInstance.objects.get(id=workflow_instance_id)

            # Handle based on workflow status
            if workflow_instance.status == WorkflowInstance.STATUS_APPROVED:
                success, error = AssetWorkflowIntegration.handle_workflow_completion(workflow_instance)
            elif workflow_instance.status == WorkflowInstance.STATUS_REJECTED:
                success, error = AssetWorkflowIntegration.handle_workflow_rejection(workflow_instance)
            else:
                return BaseResponse.error(
                    code='INVALID_WORKFLOW_STATUS',
                    message=f'Workflow status {workflow_instance.status} not handled'
                )

            if success:
                pickup.refresh_from_db()
                response_serializer = AssetPickupDetailSerializer(pickup)
                return BaseResponse.success(
                    data=response_serializer.data,
                    message='Operation completed after workflow processing'
                )
            else:
                return BaseResponse.error(
                    code='WORKFLOW_PROCESSING_FAILED',
                    message=error or 'Failed to process workflow result'
                )
        except WorkflowInstance.DoesNotExist:
            return BaseResponse.error(
                code='WORKFLOW_NOT_FOUND',
                message='Workflow instance not found'
            )


# ========== Transfer Order ViewSet ==========

class AssetTransferViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Asset Transfer Order operations.

    Provides:
    - Standard CRUD operations (inherited)
    - Batch operations (inherited)
    - approve_from(): Approve from source department
    - approve_to(): Approve from target department
    - submit(): Submit for approval
    - complete(): Complete the transfer
    """
    queryset = AssetTransfer.objects.select_related(
        'from_department', 'to_department',
        'from_approved_by', 'to_approved_by', 'created_by'
    ).all()
    filterset_class = AssetTransferFilter
    service = AssetTransferService()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return AssetTransferListSerializer
        elif self.action == 'create':
            return AssetTransferCreateSerializer
        elif self.action == 'retrieve':
            return AssetTransferDetailSerializer
        return AssetTransferSerializer

    def create(self, request, *args, **kwargs):
        """Create transfer order with items."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items = serializer.validated_data.pop('items', [])
        organization_id = getattr(request, 'organization_id', None)

        transfer = self.service.create_with_items(
            serializer.validated_data,
            items,
            request.user,
            organization_id
        )

        response_serializer = AssetTransferDetailSerializer(transfer)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Transfer order created successfully',
            http_status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        """Submit transfer order for approval."""
        transfer = self.service.submit_for_approval(pk, request.user)
        response_serializer = AssetTransferDetailSerializer(transfer)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Transfer order submitted for approval'
        )

    @action(detail=True, methods=['post'], url_path='approve-from')
    def approve_from(self, request, pk=None):
        """Approve from source department."""
        serializer = TransferApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        transfer = self.service.approve_from(
            pk,
            request.user,
            serializer.validated_data.get('comment', '')
        )

        response_serializer = AssetTransferDetailSerializer(transfer)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Source department approved'
        )

    @action(detail=True, methods=['post'], url_path='approve-to')
    def approve_to(self, request, pk=None):
        """Approve from target department."""
        serializer = TransferApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        transfer = self.service.approve_to(
            pk,
            request.user,
            serializer.validated_data.get('comment', '')
        )

        response_serializer = AssetTransferDetailSerializer(transfer)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Target department approved - transfer ready for completion'
        )

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """Complete the transfer and update assets."""
        transfer = self.service.complete_transfer(pk, request.user)
        response_serializer = AssetTransferDetailSerializer(transfer)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Transfer completed'
        )


# ========== Return Order ViewSet ==========

class AssetReturnViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Asset Return Order operations.

    Provides:
    - Standard CRUD operations (inherited)
    - Batch operations (inherited)
    - confirm(): Confirm and complete return
    - reject(): Reject return
    """
    queryset = AssetReturn.objects.select_related(
        'returner', 'return_location',
        'confirmed_by', 'created_by'
    ).all()
    filterset_class = AssetReturnFilter
    service = AssetReturnService()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return AssetReturnListSerializer
        elif self.action == 'create':
            return AssetReturnCreateSerializer
        elif self.action == 'retrieve':
            return AssetReturnDetailSerializer
        return AssetReturnSerializer

    def create(self, request, *args, **kwargs):
        """Create return order with items."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items = serializer.validated_data.pop('items', [])
        organization_id = getattr(request, 'organization_id', None)

        return_order = self.service.create_with_items(
            serializer.validated_data,
            items,
            request.user,
            organization_id
        )

        response_serializer = AssetReturnDetailSerializer(return_order)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Return order created successfully',
            http_status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        """Confirm and complete return order."""
        return_order = self.service.confirm_return(pk, request.user)
        response_serializer = AssetReturnDetailSerializer(return_order)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Return confirmed and completed'
        )

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """Reject return order."""
        reason = request.data.get('reason', '')
        return_order = self.service.reject_return(pk, request.user, reason)
        response_serializer = AssetReturnDetailSerializer(return_order)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Return order rejected'
        )


# ========== Loan Order ViewSet ==========

class AssetLoanViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Asset Loan Order operations.

    Provides:
    - Standard CRUD operations (inherited)
    - Batch operations (inherited)
    - approve(): Approve or reject loan
    - confirm_borrow(): Confirm assets have been lent
    - confirm_return(): Confirm assets have been returned
    - check_overdue(): Check and mark overdue loans
    """
    queryset = AssetLoan.objects.select_related(
        'borrower', 'approved_by', 'lent_by',
        'return_confirmed_by', 'created_by'
    ).all()
    filterset_class = AssetLoanFilter
    service = AssetLoanService()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return AssetLoanListSerializer
        elif self.action == 'create':
            return AssetLoanCreateSerializer
        elif self.action == 'retrieve':
            return AssetLoanDetailSerializer
        return AssetLoanSerializer

    def create(self, request, *args, **kwargs):
        """Create loan order with items."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items = serializer.validated_data.pop('items', [])
        organization_id = getattr(request, 'organization_id', None)

        loan = self.service.create_with_items(
            serializer.validated_data,
            items,
            request.user,
            organization_id
        )

        response_serializer = AssetLoanDetailSerializer(loan)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Loan order created successfully',
            http_status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """Approve or reject loan order."""
        serializer = LoanApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        loan = self.service.approve_loan(
            pk,
            request.user,
            serializer.validated_data['approval'],
            serializer.validated_data.get('comment', '')
        )

        response_serializer = AssetLoanDetailSerializer(loan)
        message = 'Loan approved' if serializer.validated_data['approval'] == 'approved' else 'Loan rejected'
        return BaseResponse.success(
            data=response_serializer.data,
            message=message
        )

    @action(detail=True, methods=['post'], url_path='confirm-borrow')
    def confirm_borrow(self, request, pk=None):
        """Confirm that assets have been lent out."""
        loan = self.service.confirm_borrow(pk, request.user)
        response_serializer = AssetLoanDetailSerializer(loan)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Asset loan confirmed'
        )

    @action(detail=True, methods=['post'], url_path='confirm-return')
    def confirm_return(self, request, pk=None):
        """Confirm that assets have been returned."""
        serializer = LoanReturnConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        loan = self.service.confirm_return(
            pk,
            request.user,
            serializer.validated_data.get('condition', 'good'),
            serializer.validated_data.get('comment', '')
        )

        response_serializer = AssetLoanDetailSerializer(loan)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Asset return confirmed'
        )

    @action(detail=False, methods=['post'], url_path='check-overdue')
    def check_overdue(self, request):
        """Check and mark overdue loans."""
        organization_id = getattr(request, 'organization_id', None)
        count = self.service.check_overdue_loans(organization_id)
        return BaseResponse.success(
            data={'updated_count': count},
            message=f'Updated {count} overdue loans'
        )
