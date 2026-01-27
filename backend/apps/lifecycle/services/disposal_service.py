"""
Disposal Request Service

Business service for disposal request operations including:
- CRUD operations via BaseCRUDService
- Approval workflow management
- Technical appraisal management
- Disposal execution tracking
"""
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q
from apps.common.services.base_crud import BaseCRUDService
from apps.lifecycle.models import (
    DisposalRequest,
    DisposalItem,
    DisposalRequestStatus,
    DisposalType,
)


class DisposalRequestService(BaseCRUDService):
    """
    Service for Disposal Request operations.

    Extends BaseCRUDService with disposal workflow methods.
    """

    def __init__(self):
        super().__init__(DisposalRequest)

    def create_with_items(self, data: dict, user):
        """
        Create disposal request with items.

        Args:
            data: Dictionary containing disposal request data and items
            user: Current user creating the request

        Returns:
            Created DisposalRequest instance
        """
        items_data = data.pop('items', [])

        # Set applicant from user
        data['applicant'] = user
        data['organization_id'] = user.organization_id

        disposal_request = DisposalRequest.objects.create(**data)

        # Create items
        for idx, item_data in enumerate(items_data, start=1):
            item_data['sequence'] = idx
            item_data['organization_id'] = user.organization_id
            DisposalItem.objects.create(
                disposal_request=disposal_request,
                **item_data
            )

        return disposal_request

    def submit_for_approval(self, request_id: str):
        """
        Submit disposal request for approval.

        Args:
            request_id: Disposal request ID

        Returns:
            Updated DisposalRequest instance

        Raises:
            ValidationError: If request is not in draft status
        """
        request = self.get(request_id)

        if request.status != DisposalRequestStatus.DRAFT:
            raise ValidationError({
                'status': f'Cannot submit request with status {request.get_status_display()}'
            })

        request.status = DisposalRequestStatus.SUBMITTED
        request.save()

        return request

    def start_appraisal(self, request_id: str):
        """
        Start technical appraisal process.

        Args:
            request_id: Disposal request ID

        Returns:
            Updated DisposalRequest instance
        """
        request = self.get(request_id)

        if request.status != DisposalRequestStatus.SUBMITTED:
            raise ValidationError({
                'status': f'Cannot start appraisal for request with status {request.get_status_display()}'
            })

        request.status = DisposalRequestStatus.APPRAISING
        request.save()

        return request

    def record_appraisal(self, item_id: str, appraiser, result: str, residual_value):
        """
        Record technical appraisal for disposal item.

        Args:
            item_id: Disposal item ID
            appraiser: User performing appraisal
            result: Appraisal result description
            residual_value: Estimated residual value

        Returns:
            Updated DisposalItem instance
        """
        from apps.lifecycle.models import DisposalItem

        item = DisposalItem.objects.get(id=item_id)

        item.appraisal_result = result
        item.residual_value = residual_value
        item.appraised_by = appraiser
        item.appraised_at = timezone.now()
        item.save()

        # Check if all items are appraised
        request = item.disposal_request
        unappraised = request.items.filter(appraised_by__isnull=True)
        if not unappraised.exists():
            # All items appraised, move to approved status
            request.status = DisposalRequestStatus.APPROVED
            request.current_approver = None
            request.save()

        return item

    def approve(self, request_id: str, approver, decision: str, comment: str = None):
        """
        Approve or reject disposal request (after appraisal).

        Args:
            request_id: Disposal request ID
            approver: User approving the request
            decision: 'approved' or 'rejected'
            comment: Optional approval comment

        Returns:
            Updated DisposalRequest instance
        """
        request = self.get(request_id)

        if request.status not in [DisposalRequestStatus.APPRAISING, DisposalRequestStatus.SUBMITTED]:
            raise ValidationError({
                'status': f'Cannot approve request with status {request.get_status_display()}'
            })

        if decision == 'approved':
            # Ensure all items are appraised
            unappraised = request.items.filter(appraised_by__isnull=True)
            if unappraised.exists():
                raise ValidationError({
                    'status': 'Cannot approve request with unappraised items'
                })
            request.status = DisposalRequestStatus.APPROVED
        else:
            request.status = DisposalRequestStatus.REJECTED

        request.current_approver = None
        request.save()

        return request

    def start_execution(self, request_id: str):
        """
        Start disposal execution process.

        Args:
            request_id: Disposal request ID

        Returns:
            Updated DisposalRequest instance
        """
        request = self.get(request_id)

        if request.status != DisposalRequestStatus.APPROVED:
            raise ValidationError({
                'status': f'Cannot start execution for request with status {request.get_status_display()}'
            })

        request.status = DisposalRequestStatus.EXECUTING
        request.save()

        return request

    def execute_disposal(self, item_id: str, actual_value, buyer_info):
        """
        Record disposal execution for item.

        Args:
            item_id: Disposal item ID
            actual_value: Actual residual value received
            buyer_info: Buyer information

        Returns:
            Updated DisposalItem instance
        """
        from apps.lifecycle.models import DisposalItem

        item = DisposalItem.objects.get(id=item_id)

        item.disposal_executed = True
        item.executed_at = timezone.now()
        item.actual_residual_value = actual_value
        item.buyer_info = buyer_info
        item.save()

        # Check if all items are executed
        request = item.disposal_request
        unexecuted = request.items.filter(disposal_executed=False)
        if not unexecuted.exists():
            # All items executed, complete the request
            request.status = DisposalRequestStatus.COMPLETED
            request.save()

        return item

    def complete_request(self, request_id: str):
        """
        Mark disposal request as completed.

        Args:
            request_id: Disposal request ID

        Returns:
            Updated DisposalRequest instance
        """
        request = self.get(request_id)

        if request.status != DisposalRequestStatus.EXECUTING:
            raise ValidationError({
                'status': f'Cannot complete request with status {request.get_status_display()}'
            })

        # Verify all items are executed
        unexecuted = request.items.filter(disposal_executed=False)
        if unexecuted.exists():
            raise ValidationError({
                'status': 'Cannot complete request with unexecuted items'
            })

        request.status = DisposalRequestStatus.COMPLETED
        request.save()

        return request

    def cancel(self, request_id: str, reason: str = None):
        """
        Cancel disposal request.

        Args:
            request_id: Disposal request ID
            reason: Cancellation reason

        Returns:
            Updated DisposalRequest instance
        """
        request = self.get(request_id)

        if request.status in [DisposalRequestStatus.COMPLETED, DisposalRequestStatus.CANCELLED]:
            raise ValidationError({
                'status': f'Cannot cancel request with status {request.get_status_display()}'
            })

        request.status = DisposalRequestStatus.CANCELLED
        request.save()

        return request

    def get_by_status(self, status: str, organization_id: str = None):
        """
        Get disposal requests by status.

        Args:
            status: Status to filter by
            organization_id: Filter by organization

        Returns:
            QuerySet of disposal requests with given status
        """
        queryset = DisposalRequest.objects.filter(
            status=status,
            is_deleted=False
        )

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        return queryset.order_by('-created_at')

    def get_by_disposal_type(self, disposal_type: str, organization_id: str = None):
        """
        Get disposal requests by disposal type.

        Args:
            disposal_type: Disposal type to filter by
            organization_id: Filter by organization

        Returns:
            QuerySet of disposal requests with given type
        """
        queryset = DisposalRequest.objects.filter(
            disposal_type=disposal_type,
            is_deleted=False
        )

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        return queryset.order_by('-created_at')

    def get_pending_appraisal(self, organization_id: str = None):
        """
        Get all requests pending technical appraisal.

        Args:
            organization_id: Filter by organization

        Returns:
            QuerySet of requests awaiting appraisal
        """
        return self.get_by_status(DisposalRequestStatus.APPRAISING, organization_id)

    def get_approved_for_execution(self, organization_id: str = None):
        """
        Get all approved requests ready for execution.

        Args:
            organization_id: Filter by organization

        Returns:
            QuerySet of approved requests
        """
        return self.get_by_status(DisposalRequestStatus.APPROVED, organization_id)

    def get_unappraised_items(self, request_id: str):
        """
        Get items in a request that haven't been appraised yet.

        Args:
            request_id: Disposal request ID

        Returns:
            QuerySet of unappraised items
        """
        request = self.get(request_id)
        return request.items.filter(appraised_by__isnull=True)

    def calculate_total_net_value(self, request_id: str):
        """
        Calculate total net value from request items.

        Args:
            request_id: Disposal request ID

        Returns:
            Total net value as Decimal
        """
        request = self.get(request_id)
        return sum(item.net_value for item in request.items.all())

    def calculate_total_residual_value(self, request_id: str):
        """
        Calculate total appraised residual value.

        Args:
            request_id: Disposal request ID

        Returns:
            Total residual value as Decimal
        """
        request = self.get(request_id)
        total = 0
        for item in request.items.all():
            if item.residual_value:
                total += item.residual_value
        return total

    def get_disposal_statistics(self, organization_id: str = None):
        """
        Get disposal statistics summary.

        Args:
            organization_id: Filter by organization

        Returns:
            Dictionary with disposal statistics
        """
        queryset = DisposalRequest.objects.filter(is_deleted=False)

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        return {
            'total': queryset.count(),
            'draft': queryset.filter(status=DisposalRequestStatus.DRAFT).count(),
            'submitted': queryset.filter(status=DisposalRequestStatus.SUBMITTED).count(),
            'appraising': queryset.filter(status=DisposalRequestStatus.APPRAISING).count(),
            'approved': queryset.filter(status=DisposalRequestStatus.APPROVED).count(),
            'executing': queryset.filter(status=DisposalRequestStatus.EXECUTING).count(),
            'completed': queryset.filter(status=DisposalRequestStatus.COMPLETED).count(),
            'rejected': queryset.filter(status=DisposalRequestStatus.REJECTED).count(),
            'cancelled': queryset.filter(status=DisposalRequestStatus.CANCELLED).count(),
        }
