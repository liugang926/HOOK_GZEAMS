"""
ViewSets for Asset Operation Models (Pickup, Transfer, Return, Loan).

All ViewSets inherit from BaseModelViewSetWithBatch for standard CRUD operations
and batch operation support.
"""
from django.shortcuts import get_object_or_404
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
    AssetTransferUpdateSerializer,
    AssetTransferSerializer,
    TransferApprovalSerializer,
    TransferItemSerializer,
    # Return serializers
    AssetReturnListSerializer,
    AssetReturnDetailSerializer,
    AssetReturnCreateSerializer,
    AssetReturnUpdateSerializer,
    AssetReturnSerializer,
    ReturnConfirmSerializer,
    ReturnItemSerializer,
    # Loan serializers
    AssetLoanListSerializer,
    AssetLoanDetailSerializer,
    AssetLoanCreateSerializer,
    AssetLoanUpdateSerializer,
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


def _get_operation_instance(model_class, pk, organization_id=None):
    queryset = model_class.all_objects.filter(is_deleted=False)
    if organization_id:
        queryset = queryset.filter(organization_id=organization_id)
    return get_object_or_404(queryset, id=pk)


class _BaseLineItemReadOnlyViewSet(BaseModelViewSetWithBatch):
    """
    Read-only line-item ViewSet used by ObjectRouter related tabs.

    Line items are edited through their parent documents via the unified `items`
    payload, so we only expose GET endpoints here. The dedicated serializers keep
    relation tables aligned with the same field names used by the parent detail API.
    """

    http_method_names = ['get', 'head', 'options']

    def get_serializer_class(self):
        return self.serializer_class


class PickupItemViewSet(_BaseLineItemReadOnlyViewSet):
    queryset = PickupItem.objects.select_related(
        'pickup',
        'asset',
        'snapshot_original_location',
        'snapshot_original_custodian',
        'organization',
        'created_by',
        'updated_by',
    ).order_by('created_at', 'id')
    serializer_class = PickupItemSerializer


class TransferItemViewSet(_BaseLineItemReadOnlyViewSet):
    queryset = TransferItem.objects.select_related(
        'transfer',
        'asset',
        'from_location',
        'from_custodian',
        'to_location',
        'organization',
        'created_by',
        'updated_by',
    ).order_by('created_at', 'id')
    serializer_class = TransferItemSerializer


class ReturnItemViewSet(_BaseLineItemReadOnlyViewSet):
    queryset = ReturnItem.objects.select_related(
        'asset_return',
        'asset',
        'organization',
        'created_by',
        'updated_by',
    ).order_by('created_at', 'id')
    serializer_class = ReturnItemSerializer


class LoanItemViewSet(_BaseLineItemReadOnlyViewSet):
    queryset = LoanItem.objects.select_related(
        'loan',
        'asset',
        'organization',
        'created_by',
        'updated_by',
    ).order_by('created_at', 'id')
    serializer_class = LoanItemSerializer


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
        elif self.action in {'update', 'partial_update'}:
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

    def update(self, request, *args, **kwargs):
        """Update pickup order with nested items."""
        partial = kwargs.pop('partial', False)
        organization_id = getattr(request, 'organization_id', None)
        pk = kwargs.get('pk') or kwargs.get('id')
        instance = _get_operation_instance(AssetPickup, pk, organization_id)
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        items = data.pop('items', None)
        serializer = self.get_serializer(instance, data=data, partial=True if not partial else partial)
        serializer.is_valid(raise_exception=True)

        pickup = self.service.update_with_items(
            pk, serializer.validated_data, items, request.user, organization_id
        )

        response_serializer = AssetPickupDetailSerializer(pickup)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Pickup order updated successfully'
        )

    def partial_update(self, request, *args, **kwargs):
        """Partial update pickup order with nested items."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

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
            update_fields = []
            if pickup.status != 'pending':
                pickup.status = 'pending'
                update_fields.append('status')

            if hasattr(pickup, 'workflow_instance_id'):
                pickup.workflow_instance_id = (
                    str(workflow_instance.id) if workflow_instance else None
                )
                update_fields.append('workflow_instance_id')
            elif hasattr(pickup, 'workflow_instance'):
                pickup.workflow_instance = workflow_instance
                update_fields.append('workflow_instance')

            if update_fields:
                pickup.save(update_fields=update_fields + ['updated_at'])

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

    @action(detail=True, methods=['post'], url_path='approve-pass')
    def approve_pass(self, request, pk=None):
        """Approve a pickup order without requiring a request payload."""
        pickup = self.service.approve(
            pk,
            request.user,
            'approved',
            request.data.get('comment', '')
        )

        response_serializer = AssetPickupDetailSerializer(pickup)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Pickup order approved'
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
        reason = request.data.get('reason', request.data.get('comment', ''))
        pickup = self.service.cancel_pickup(pk, request.user, reason)
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
        elif self.action in {'update', 'partial_update'}:
            return AssetTransferUpdateSerializer
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

    def update(self, request, *args, **kwargs):
        """Update transfer order with nested items."""
        partial = kwargs.pop('partial', False)
        organization_id = getattr(request, 'organization_id', None)
        pk = kwargs.get('pk') or kwargs.get('id')
        instance = _get_operation_instance(AssetTransfer, pk, organization_id)
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        items = data.pop('items', None)
        serializer = self.get_serializer(instance, data=data, partial=True if not partial else partial)
        serializer.is_valid(raise_exception=True)

        transfer = self.service.update_with_items(
            pk, serializer.validated_data, items, request.user, organization_id
        )

        response_serializer = AssetTransferDetailSerializer(transfer)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Transfer order updated successfully'
        )

    def partial_update(self, request, *args, **kwargs):
        """Partial update transfer order with nested items."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

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

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """Compatibility alias that advances transfer approval by current stage."""
        comment = request.data.get('comment', '')
        transfer = self.get_object()

        if transfer.status == 'pending':
            transfer = self.service.approve_from(pk, request.user, comment)
            message = 'Source department approved'
        elif transfer.status == 'out_approved':
            transfer = self.service.approve_to(pk, request.user, comment)
            message = 'Target department approved - transfer ready for completion'
        else:
            return BaseResponse.error(
                code='VALIDATION_ERROR',
                message=f'Cannot approve transfer with status {transfer.get_status_label()}',
                http_status=status.HTTP_400_BAD_REQUEST
            )

        response_serializer = AssetTransferDetailSerializer(transfer)
        return BaseResponse.success(
            data=response_serializer.data,
            message=message
        )

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """Compatibility alias for transfer rejection."""
        comment = request.data.get('comment') or request.data.get('reason', '')
        transfer = self.service.reject_transfer(pk, request.user, comment)
        response_serializer = AssetTransferDetailSerializer(transfer)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Transfer order rejected'
        )

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """Cancel a transfer order."""
        reason = request.data.get('reason', request.data.get('comment', ''))
        transfer = self.service.cancel_transfer(pk, request.user, reason)
        response_serializer = AssetTransferDetailSerializer(transfer)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Transfer order cancelled'
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
        elif self.action in {'update', 'partial_update'}:
            return AssetReturnUpdateSerializer
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

    def update(self, request, *args, **kwargs):
        """Update return order with nested items."""
        partial = kwargs.pop('partial', False)
        organization_id = getattr(request, 'organization_id', None)
        pk = kwargs.get('pk') or kwargs.get('id')
        instance = _get_operation_instance(AssetReturn, pk, organization_id)
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        items = data.pop('items', None)
        serializer = self.get_serializer(instance, data=data, partial=True if not partial else partial)
        serializer.is_valid(raise_exception=True)

        return_order = self.service.update_with_items(
            pk, serializer.validated_data, items, request.user, organization_id
        )

        response_serializer = AssetReturnDetailSerializer(return_order)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Return order updated successfully'
        )

    def partial_update(self, request, *args, **kwargs):
        """Partial update return order with nested items."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        """Submit return order for approval."""
        return_order = self.service.submit_for_approval(pk, request.user)
        response_serializer = AssetReturnDetailSerializer(return_order)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Return order submitted for approval'
        )

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """Cancel return order."""
        reason = request.data.get('reason', request.data.get('comment', ''))
        return_order = self.service.cancel_return(pk, request.user, reason)
        response_serializer = AssetReturnDetailSerializer(return_order)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Return order cancelled'
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

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """Compatibility alias for return confirmation."""
        return self.confirm(request, pk=pk)

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """Compatibility alias for return completion."""
        return self.confirm(request, pk=pk)

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
        elif self.action in {'update', 'partial_update'}:
            return AssetLoanUpdateSerializer
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

    def update(self, request, *args, **kwargs):
        """Update loan order with nested items."""
        partial = kwargs.pop('partial', False)
        organization_id = getattr(request, 'organization_id', None)
        pk = kwargs.get('pk') or kwargs.get('id')
        instance = _get_operation_instance(AssetLoan, pk, organization_id)
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        items = data.pop('items', None)
        serializer = self.get_serializer(instance, data=data, partial=True if not partial else partial)
        serializer.is_valid(raise_exception=True)

        loan = self.service.update_with_items(
            pk, serializer.validated_data, items, request.user, organization_id
        )

        response_serializer = AssetLoanDetailSerializer(loan)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Loan order updated successfully'
        )

    def partial_update(self, request, *args, **kwargs):
        """Partial update loan order with nested items."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        """Submit loan order for approval."""
        loan = self.service.submit_for_approval(pk, request.user)
        response_serializer = AssetLoanDetailSerializer(loan)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Loan order submitted for approval'
        )

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """Cancel loan order."""
        reason = request.data.get('reason', request.data.get('comment', ''))
        loan = self.service.cancel_loan(pk, request.user, reason)
        response_serializer = AssetLoanDetailSerializer(loan)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Loan order cancelled'
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

    @action(detail=True, methods=['post'], url_path='approve-pass')
    def approve_pass(self, request, pk=None):
        """Approve a loan order without requiring a request payload."""
        loan = self.service.approve_loan(
            pk,
            request.user,
            'approved',
            request.data.get('comment', '')
        )

        response_serializer = AssetLoanDetailSerializer(loan)
        return BaseResponse.success(
            data=response_serializer.data,
            message='Loan approved'
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

    @action(detail=True, methods=['post'], url_path='return')
    def return_assets(self, request, pk=None):
        """Compatibility alias for loan return confirmation."""
        condition = request.data.get('condition', 'good')
        comment = request.data.get('comment') or request.data.get('remark', '')
        loan = self.service.confirm_return(pk, request.user, condition, comment)

        return_date = request.data.get('return_date') or request.data.get('returnDate')
        if return_date:
            from django.utils.dateparse import parse_date

            parsed_return_date = parse_date(str(return_date))
            if parsed_return_date:
                loan.actual_return_date = parsed_return_date
                loan.save(update_fields=['actual_return_date', 'updated_at'])

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
