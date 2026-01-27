"""
Purchase Request Service

Business service for purchase request operations including:
- CRUD operations via BaseCRUDService
- Approval workflow management
- M18 system integration (stub)
"""
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q
from apps.common.services.base_crud import BaseCRUDService
from apps.lifecycle.models import (
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseRequestStatus,
)


class PurchaseRequestService(BaseCRUDService):
    """
    Service for Purchase Request operations.

    Extends BaseCRUDService with purchase request workflow methods.
    """

    def __init__(self):
        super().__init__(PurchaseRequest)

    def create_with_items(self, data: dict, user):
        """
        Create purchase request with items.

        Args:
            data: Dictionary containing purchase request data and items
            user: Current user creating the request

        Returns:
            Created PurchaseRequest instance
        """
        items_data = data.pop('items', [])

        # Set applicant from user
        data['applicant'] = user
        data['organization_id'] = user.organization_id

        purchase_request = PurchaseRequest.objects.create(**data)

        # Create items
        for idx, item_data in enumerate(items_data, start=1):
            item_data['sequence'] = idx
            item_data['organization_id'] = user.organization_id
            PurchaseRequestItem.objects.create(
                purchase_request=purchase_request,
                **item_data
            )

        return purchase_request

    def submit_for_approval(self, request_id: str):
        """
        Submit purchase request for approval.

        Args:
            request_id: Purchase request ID

        Returns:
            Updated PurchaseRequest instance

        Raises:
            ValidationError: If request is not in draft status
        """
        request = self.get(request_id)

        if request.status != PurchaseRequestStatus.DRAFT:
            raise ValidationError({
                'status': f'Cannot submit request with status {request.get_status_display()}'
            })

        request.status = PurchaseRequestStatus.SUBMITTED
        request.save()

        return request

    def approve(self, request_id: str, approver, decision: str, comment: str = None):
        """
        Approve or reject purchase request.

        Args:
            request_id: Purchase request ID
            approver: User approving the request
            decision: 'approved' or 'rejected'
            comment: Optional approval comment

        Returns:
            Updated PurchaseRequest instance

        Raises:
            ValidationError: If request is not in submitted status
        """
        request = self.get(request_id)

        if request.status != PurchaseRequestStatus.SUBMITTED:
            raise ValidationError({
                'status': f'Cannot approve request with status {request.get_status_display()}'
            })

        if decision == 'approved':
            request.status = PurchaseRequestStatus.APPROVED
            request.approved_by = approver
            request.approved_at = timezone.now()
        else:
            request.status = PurchaseRequestStatus.REJECTED

        request.approval_comment = comment or ''
        request.current_approver = None
        request.save()

        return request

    def start_processing(self, request_id: str):
        """
        Mark purchase request as processing (after M18 sync).

        Args:
            request_id: Purchase request ID

        Returns:
            Updated PurchaseRequest instance
        """
        request = self.get(request_id)

        if request.status != PurchaseRequestStatus.APPROVED:
            raise ValidationError({
                'status': f'Cannot start processing request with status {request.get_status_display()}'
            })

        request.status = PurchaseRequestStatus.PROCESSING
        request.save()

        return request

    def complete(self, request_id: str):
        """
        Mark purchase request as completed.

        Args:
            request_id: Purchase request ID

        Returns:
            Updated PurchaseRequest instance
        """
        request = self.get(request_id)

        if request.status != PurchaseRequestStatus.PROCESSING:
            raise ValidationError({
                'status': f'Cannot complete request with status {request.get_status_display()}'
            })

        request.status = PurchaseRequestStatus.COMPLETED
        request.save()

        return request

    def cancel(self, request_id: str, reason: str = None):
        """
        Cancel purchase request.

        Args:
            request_id: Purchase request ID
            reason: Cancellation reason

        Returns:
            Updated PurchaseRequest instance
        """
        request = self.get(request_id)

        if request.status in [PurchaseRequestStatus.COMPLETED, PurchaseRequestStatus.CANCELLED]:
            raise ValidationError({
                'status': f'Cannot cancel request with status {request.get_status_display()}'
            })

        request.status = PurchaseRequestStatus.CANCELLED
        request.approval_comment = reason or 'Cancelled'
        request.save()

        return request

    def push_to_m18(self, request_id: str):
        """
        Push purchase request to M18 ERP system.

        STUB IMPLEMENTATION: Returns mock M18 order number.

        Args:
            request_id: Purchase request ID

        Returns:
            Updated PurchaseRequest with M18 sync info
        """
        request = self.get(request_id)

        if request.status != PurchaseRequestStatus.APPROVED:
            raise ValidationError({
                'status': 'Can only push approved requests to M18'
            })

        # STUB: Simulate M18 sync
        # In production, this would call the M18 adapter
        mock_order_no = f"M18-PO-{timezone.now().strftime('%Y%m%d%H%M%S')}"

        request.m18_purchase_order_no = mock_order_no
        request.pushed_to_m18_at = timezone.now()
        request.m18_sync_status = 'synced'
        request.save()

        return request

    def get_pending_approvals(self, organization_id: str = None):
        """
        Get all pending purchase requests requiring approval.

        Args:
            organization_id: Filter by organization

        Returns:
            QuerySet of pending purchase requests
        """
        queryset = PurchaseRequest.objects.filter(
            status=PurchaseRequestStatus.SUBMITTED,
            is_deleted=False
        )

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        return queryset.order_by('-created_at')

    def get_by_status(self, status: str, organization_id: str = None):
        """
        Get purchase requests by status.

        Args:
            status: Status to filter by
            organization_id: Filter by organization

        Returns:
            QuerySet of purchase requests with given status
        """
        queryset = PurchaseRequest.objects.filter(
            status=status,
            is_deleted=False
        )

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        return queryset.order_by('-created_at')

    def calculate_total_amount(self, request_id: str):
        """
        Calculate total amount from request items.

        Args:
            request_id: Purchase request ID

        Returns:
            Total amount as Decimal
        """
        request = self.get(request_id)
        return request.calculate_total_amount()
