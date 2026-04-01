"""
Purchase Request Service

Business service for purchase request operations including:
- CRUD operations via BaseCRUDService
- Approval workflow management
- M18 system integration (stub)
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from apps.common.services.base_crud import BaseCRUDService
from apps.lifecycle.models import (
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseRequestStatus,
)
from apps.system.services.activity_log_service import ActivityLogService
from apps.system.services.timeline_highlight_service import build_reason_change
from apps.lifecycle.services.closed_loop_service import LifecycleClosedLoopService


def _normalize_free_text(value) -> str:
    return str(value or '').strip()


def _set_custom_field_text(instance, key: str, value) -> str:
    normalized_value = _normalize_free_text(value)
    custom_fields = dict(instance.custom_fields or {})

    if normalized_value:
        custom_fields[key] = normalized_value
    elif key in custom_fields:
        custom_fields.pop(key, None)

    instance.custom_fields = custom_fields
    return normalized_value


def _build_cancellation_description(record_no: str, reason: str = '') -> str:
    description = f'Purchase request {record_no} cancelled.'
    normalized_reason = _normalize_free_text(reason)
    if normalized_reason:
        description = f'{description} Cancellation reason: {normalized_reason}'
    return description


class PurchaseRequestService(BaseCRUDService):
    """
    Service for Purchase Request operations.

    Extends BaseCRUDService with purchase request workflow methods.
    """

    def __init__(self):
        super().__init__(PurchaseRequest)
        self.closed_loop_service = LifecycleClosedLoopService()

    @staticmethod
    def _normalize_total_amount(quantity, unit_price, total_amount):
        if total_amount not in (None, ''):
            return total_amount

        normalized_quantity = Decimal(str(quantity or 0))
        normalized_unit_price = Decimal(str(unit_price or '0'))
        return normalized_quantity * normalized_unit_price

    def _sync_items(
        self,
        *,
        purchase_request: PurchaseRequest,
        items_data: list[dict],
        organization_id: str,
    ):
        related_field_names = {
            field.name
            for field in PurchaseRequestItem._meta.fields
            if getattr(field, 'many_to_one', False) and field.name != 'purchase_request'
        }
        existing_items = {
            str(item.id): item
            for item in purchase_request.items.filter(is_deleted=False)
        }
        prepared_rows = []

        for index, item_data in enumerate(items_data or [], start=1):
            payload = dict(item_data or {})
            item_id = str(payload.pop('id', '') or '').strip()
            payload['sequence'] = index
            payload['organization_id'] = organization_id
            payload['total_amount'] = self._normalize_total_amount(
                payload.get('quantity'),
                payload.get('unit_price'),
                payload.get('total_amount'),
            )
            normalized_payload = {}
            for attr, value in payload.items():
                if attr in related_field_names and not hasattr(value, '_meta'):
                    normalized_payload[f'{attr}_id'] = value
                    continue
                normalized_payload[attr] = value
            prepared_rows.append((item_id, normalized_payload))

        submitted_ids = {
            item_id
            for item_id, _normalized_payload in prepared_rows
            if item_id
        }

        for item_id, item in existing_items.items():
            if item_id not in submitted_ids:
                item.delete()

        if submitted_ids:
            for offset, item_id in enumerate(sorted(submitted_ids), start=1):
                item = existing_items.get(item_id)
                if item is None:
                    continue
                item.sequence = 1000000 + offset
                item.save(update_fields=['sequence', 'updated_at'])

        for item_id, normalized_payload in prepared_rows:
            if item_id:
                item = existing_items.get(item_id)
                if item is None:
                    raise ValidationError({
                        'items': f'Purchase request item {item_id} does not belong to this request'
                    })

                for attr, value in normalized_payload.items():
                    if hasattr(item, attr):
                        setattr(item, attr, value)
                item.save()
                continue

            PurchaseRequestItem.objects.create(
                purchase_request=purchase_request,
                **normalized_payload,
            )

    def create_with_items(self, data: dict, items=None, user=None, organization_id: str = None):
        """
        Create purchase request with items.

        Args:
            data: Dictionary containing purchase request data and items
            user: Current user creating the request

        Returns:
            Created PurchaseRequest instance
        """
        payload = dict(data or {})
        if user is None and items is not None and not isinstance(items, (list, tuple)):
            user = items
            items_data = payload.pop('items', [])
        else:
            items_data = list(items or payload.pop('items', []))

        if user is None:
            raise ValidationError({'user': 'Current user is required'})

        effective_org_id = organization_id or getattr(user, 'organization_id', None)
        if not effective_org_id:
            raise ValidationError({'organization': 'Organization is required'})

        # Set applicant from user
        payload['applicant'] = user
        payload['organization_id'] = effective_org_id

        with transaction.atomic():
            purchase_request = PurchaseRequest.objects.create(**payload)
            self._sync_items(
                purchase_request=purchase_request,
                items_data=items_data,
                organization_id=str(effective_org_id),
            )

            ActivityLogService.log_create(
                actor=user,
                instance=purchase_request,
                organization=purchase_request.organization,
            )
        return purchase_request

    def update_with_items(
        self,
        request_id: str,
        data: dict,
        items=None,
        user=None,
        organization_id: str = None,
    ):
        payload = dict(data or {})
        items_data = None if items is None else list(items)
        if items_data is None and 'items' in payload:
            items_data = list(payload.pop('items') or [])

        purchase_request = self.get(request_id)
        effective_org_id = organization_id or getattr(purchase_request, 'organization_id', None)

        if purchase_request.status not in [PurchaseRequestStatus.DRAFT, PurchaseRequestStatus.REJECTED]:
            raise ValidationError({
                'status': f'Cannot edit request with status {purchase_request.get_status_display()}'
            })

        tracked_fields = set(payload.keys())
        before_snapshot = ActivityLogService.snapshot_instance(
            purchase_request,
            fields=tracked_fields,
        )

        with transaction.atomic():
            for attr, value in payload.items():
                if hasattr(purchase_request, attr):
                    setattr(purchase_request, attr, value)
            purchase_request.save()

            if items_data is not None:
                self._sync_items(
                    purchase_request=purchase_request,
                    items_data=items_data,
                    organization_id=str(effective_org_id or ''),
                )

        if user is not None:
            ActivityLogService.log_update(
                actor=user,
                before_snapshot=before_snapshot,
                instance=purchase_request,
                changed_fields=tracked_fields,
                organization=purchase_request.organization,
            )

        purchase_request.refresh_from_db()
        return purchase_request

    def submit_for_approval(self, request_id: str, actor=None):
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

        if request.status not in [PurchaseRequestStatus.DRAFT, PurchaseRequestStatus.REJECTED]:
            raise ValidationError({
                'status': f'Cannot submit request with status {request.get_status_display()}'
            })

        old_status = request.status
        request.status = PurchaseRequestStatus.SUBMITTED
        request.save()
        self.closed_loop_service.log_status_change(
            actor=actor,
            instance=request,
            old_status=old_status,
            new_status=request.status,
            description=f'Purchase request {request.request_no} submitted for approval.',
        )

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
            old_status = request.status
            request.status = PurchaseRequestStatus.APPROVED
            request.approved_by = approver
            request.approved_at = timezone.now()
        else:
            old_status = request.status
            request.status = PurchaseRequestStatus.REJECTED

        normalized_comment = _normalize_free_text(comment)
        request.approval_comment = normalized_comment
        request.current_approver = None
        request.save()
        self.closed_loop_service.log_status_change(
            actor=approver,
            instance=request,
            old_status=old_status,
            new_status=request.status,
            description=(
                f'Purchase request {request.request_no} approved.'
                if decision == 'approved'
                else f'Purchase request {request.request_no} rejected.'
            ),
            extra_changes=[build_reason_change('approval_comment', normalized_comment)],
        )

        return request

    def start_processing(self, request_id: str, actor=None):
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

        old_status = request.status
        request.status = PurchaseRequestStatus.PROCESSING
        request.save()
        self.closed_loop_service.log_status_change(
            actor=actor,
            instance=request,
            old_status=old_status,
            new_status=request.status,
            description=f'Purchase request {request.request_no} moved into processing.',
        )

        return request

    def complete(self, request_id: str, actor=None):
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

        old_status = request.status
        request.status = PurchaseRequestStatus.COMPLETED
        request.save()
        self.closed_loop_service.log_status_change(
            actor=actor,
            instance=request,
            old_status=old_status,
            new_status=request.status,
            description=f'Purchase request {request.request_no} completed.',
        )

        return request

    def cancel(self, request_id: str, reason: str = None, actor=None):
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

        old_status = request.status
        request.status = PurchaseRequestStatus.CANCELLED
        normalized_reason = _set_custom_field_text(request, 'cancel_reason', reason)
        request.approval_comment = normalized_reason or 'Cancelled'
        request.save()
        self.closed_loop_service.log_status_change(
            actor=actor,
            instance=request,
            old_status=old_status,
            new_status=request.status,
            description=_build_cancellation_description(request.request_no, normalized_reason),
            extra_changes=[build_reason_change('cancel_reason', normalized_reason)],
        )

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
