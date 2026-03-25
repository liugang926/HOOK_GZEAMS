"""
Disposal Request Service

Business service for disposal request operations including:
- CRUD operations via BaseCRUDService
- Approval workflow management
- Technical appraisal management
- Disposal execution tracking
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from apps.common.services.base_crud import BaseCRUDService
from apps.assets.services.asset_service import AssetService
from apps.lifecycle.models import (
    DisposalRequest,
    DisposalItem,
    DisposalRequestStatus,
    DisposalType,
)
from apps.system.services.activity_log_service import ActivityLogService
from apps.lifecycle.services.closed_loop_service import LifecycleClosedLoopService


class DisposalRequestService(BaseCRUDService):
    """
    Service for Disposal Request operations.

    Extends BaseCRUDService with disposal workflow methods.
    """

    def __init__(self):
        super().__init__(DisposalRequest)
        self.closed_loop_service = LifecycleClosedLoopService()
        self.asset_service = AssetService()

    @staticmethod
    def _normalize_detail_amounts(item_data: dict) -> dict:
        payload = dict(item_data or {})
        asset = payload.get('asset')

        purchase_price = getattr(asset, 'purchase_price', None)
        current_value = getattr(asset, 'current_value', None)
        accumulated_depreciation = getattr(asset, 'accumulated_depreciation', None)

        if payload.get('original_value') in (None, '') and purchase_price not in (None, ''):
            payload['original_value'] = purchase_price
        if payload.get('net_value') in (None, ''):
            payload['net_value'] = current_value if current_value not in (None, '') else purchase_price
        if payload.get('accumulated_depreciation') in (None, ''):
            if accumulated_depreciation not in (None, ''):
                payload['accumulated_depreciation'] = accumulated_depreciation
            elif purchase_price not in (None, '') and payload.get('net_value') not in (None, ''):
                payload['accumulated_depreciation'] = Decimal(str(purchase_price)) - Decimal(str(payload['net_value']))

        return payload

    @staticmethod
    def _has_meaningful_value(value) -> bool:
        return value not in (None, '')

    def _sync_appraisal_progress(self, *, item: DisposalItem, normalized_payload: dict, actor) -> bool:
        changed = False
        appraisal_input_present = False

        for attr in ('appraisal_result', 'residual_value'):
            if attr not in normalized_payload:
                continue
            appraisal_input_present = True
            value = normalized_payload[attr]
            if getattr(item, attr, None) != value:
                setattr(item, attr, value)
                changed = True

        if appraisal_input_present and (
            self._has_meaningful_value(normalized_payload.get('appraisal_result'))
            or self._has_meaningful_value(normalized_payload.get('residual_value'))
        ):
            if actor is not None and item.appraised_by_id != getattr(actor, 'id', None):
                item.appraised_by = actor
                changed = True
            if item.appraised_at is None:
                item.appraised_at = timezone.now()
                changed = True

        if changed:
            item.save()

        return changed

    def _sync_execution_progress(self, *, item: DisposalItem, normalized_payload: dict) -> bool:
        changed = False
        execution_input_present = False

        for attr in ('actual_residual_value', 'buyer_info'):
            if attr not in normalized_payload:
                continue
            execution_input_present = True
            value = normalized_payload[attr]
            if getattr(item, attr, None) != value:
                setattr(item, attr, value)
                changed = True

        if normalized_payload.get('disposal_executed') is True or execution_input_present:
            if not item.disposal_executed:
                item.disposal_executed = True
                changed = True
            if item.executed_at is None:
                item.executed_at = timezone.now()
                changed = True

        if changed:
            item.save()

        return changed

    def _sync_items(
        self,
        *,
        disposal_request: DisposalRequest,
        items_data: list[dict],
        organization_id: str,
        stage: str = 'full',
        actor=None,
    ) -> dict:
        related_field_names = {
            field.name
            for field in DisposalItem._meta.fields
            if getattr(field, 'many_to_one', False) and field.name != 'disposal_request'
        }
        existing_items = {
            str(item.id): item
            for item in disposal_request.items.filter(is_deleted=False)
        }
        prepared_rows: list[tuple[str, dict]] = []
        updated_items = 0

        for index, item_data in enumerate(items_data or [], start=1):
            payload = self._normalize_detail_amounts(item_data)
            item_id = str(payload.pop('id', '') or '').strip()
            if stage == 'full':
                payload['sequence'] = index
                payload['organization_id'] = organization_id
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

        if stage == 'full':
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
            if stage in {'appraisal', 'execution'} and not item_id:
                raise ValidationError({
                    'items': 'Existing disposal item id is required during appraisal/execution updates'
                })

            if item_id:
                item = existing_items.get(item_id)
                if item is None:
                    raise ValidationError({
                        'items': f'Disposal item {item_id} does not belong to this request'
                    })

                if stage == 'appraisal':
                    if self._sync_appraisal_progress(item=item, normalized_payload=normalized_payload, actor=actor):
                        updated_items += 1
                    continue

                if stage == 'execution':
                    if self._sync_execution_progress(item=item, normalized_payload=normalized_payload):
                        updated_items += 1
                    continue

                for attr, value in normalized_payload.items():
                    if hasattr(item, attr):
                        setattr(item, attr, value)
                item.save()
                updated_items += 1
                continue

            if stage != 'full':
                raise ValidationError({
                    'items': 'Cannot create disposal items outside draft/rejected editing'
                })

            DisposalItem.objects.create(
                disposal_request=disposal_request,
                **normalized_payload,
            )
            updated_items += 1

        return {
            'updated_items': updated_items,
        }

    def create_with_items(
        self,
        data: dict,
        items=None,
        user=None,
        organization_id: str = None,
    ):
        """
        Create disposal request with items.

        Args:
            data: Dictionary containing disposal request data and items
            user: Current user creating the request

        Returns:
            Created DisposalRequest instance
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

        if 'applicant_id' not in payload and 'applicant' not in payload:
            payload['applicant'] = user
        payload['organization_id'] = effective_org_id

        with transaction.atomic():
            disposal_request = DisposalRequest.objects.create(**payload)
            self._sync_items(
                disposal_request=disposal_request,
                items_data=items_data,
                organization_id=str(effective_org_id),
            )

            ActivityLogService.log_create(
                actor=user,
                instance=disposal_request,
                organization=disposal_request.organization,
            )
        return disposal_request

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

        disposal_request = self.get(request_id)
        effective_org_id = organization_id or getattr(disposal_request, 'organization_id', None)
        status = disposal_request.status

        allow_master_updates = status in [DisposalRequestStatus.DRAFT, DisposalRequestStatus.REJECTED]
        detail_stage = 'full'
        if status == DisposalRequestStatus.APPRAISING:
            detail_stage = 'appraisal'
        elif status == DisposalRequestStatus.EXECUTING:
            detail_stage = 'execution'
        elif not allow_master_updates:
            raise ValidationError({
                'status': f'Cannot edit request with status {disposal_request.get_status_display()}'
            })

        tracked_fields = set(payload.keys()) if allow_master_updates else set()
        before_snapshot = (
            ActivityLogService.snapshot_instance(
                disposal_request,
                fields=tracked_fields,
            )
            if tracked_fields else {}
        )
        sync_summary = {'updated_items': 0}

        with transaction.atomic():
            if allow_master_updates:
                for attr, value in payload.items():
                    if hasattr(disposal_request, attr):
                        setattr(disposal_request, attr, value)
                disposal_request.save()

            if items_data is not None:
                sync_summary = self._sync_items(
                    disposal_request=disposal_request,
                    items_data=items_data,
                    organization_id=str(effective_org_id or ''),
                    stage=detail_stage,
                    actor=user,
                )

        if user is not None and tracked_fields:
            ActivityLogService.log_update(
                actor=user,
                before_snapshot=before_snapshot,
                instance=disposal_request,
                changed_fields=tracked_fields,
                organization=disposal_request.organization,
            )

        disposal_request.refresh_from_db()
        if user is not None and sync_summary.get('updated_items'):
            total_items = disposal_request.items.filter(is_deleted=False).count()
            if detail_stage == 'appraisal':
                appraised_items = disposal_request.items.filter(
                    is_deleted=False,
                    appraised_by__isnull=False,
                ).count()
                self.closed_loop_service.log_custom_action(
                    actor=user,
                    instance=disposal_request,
                    description=(
                        f'Updated appraisal details for {sync_summary["updated_items"]} disposal item(s). '
                        f'({appraised_items}/{total_items} appraised)'
                    ),
                    changes=[
                        {
                            'fieldCode': 'appraised_items',
                            'fieldLabel': 'Appraised Items',
                            'oldValue': max(appraised_items - sync_summary['updated_items'], 0),
                            'newValue': appraised_items,
                        }
                    ],
                )
            elif detail_stage == 'execution':
                executed_items = disposal_request.items.filter(
                    is_deleted=False,
                    disposal_executed=True,
                ).count()
                self.closed_loop_service.log_custom_action(
                    actor=user,
                    instance=disposal_request,
                    description=(
                        f'Updated execution details for {sync_summary["updated_items"]} disposal item(s). '
                        f'({executed_items}/{total_items} executed)'
                    ),
                    changes=[
                        {
                            'fieldCode': 'executed_items',
                            'fieldLabel': 'Executed Items',
                            'oldValue': max(executed_items - sync_summary['updated_items'], 0),
                            'newValue': executed_items,
                        }
                    ],
                )

        return disposal_request

    def submit_for_approval(self, request_id: str, actor=None):
        """
        Submit disposal request for approval.

        Args:
            request_id: Disposal request ID

        Returns:
            Updated DisposalRequest instance

        Raises:
            ValidationError: If request is not editable for resubmission
        """
        request = self.get(request_id)

        if request.status not in [DisposalRequestStatus.DRAFT, DisposalRequestStatus.REJECTED]:
            raise ValidationError({
                'status': f'Cannot submit request with status {request.get_status_display()}'
            })

        old_status = request.status
        request.status = DisposalRequestStatus.SUBMITTED
        request.save()
        self.closed_loop_service.log_status_change(
            actor=actor,
            instance=request,
            old_status=old_status,
            new_status=request.status,
            description=f'Disposal request {request.request_no} submitted for approval.',
        )

        return request

    def start_appraisal(self, request_id: str, actor=None):
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

        old_status = request.status
        request.status = DisposalRequestStatus.APPRAISING
        request.save()
        self.closed_loop_service.log_status_change(
            actor=actor,
            instance=request,
            old_status=old_status,
            new_status=request.status,
            description=f'Disposal request {request.request_no} entered appraisal.',
        )

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
            old_status = request.status
            request.status = DisposalRequestStatus.APPROVED
            request.current_approver = None
            request.save()
            self.closed_loop_service.log_status_change(
                actor=appraiser,
                instance=request,
                old_status=old_status,
                new_status=request.status,
                description=f'Disposal request {request.request_no} auto-approved after all items were appraised.',
            )

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
            old_status = request.status
            request.status = DisposalRequestStatus.APPROVED
        else:
            old_status = request.status
            request.status = DisposalRequestStatus.REJECTED

        request.current_approver = None
        request.save()
        self.closed_loop_service.log_status_change(
            actor=approver,
            instance=request,
            old_status=old_status,
            new_status=request.status,
            description=(
                f'Disposal request {request.request_no} approved.'
                if decision == 'approved'
                else f'Disposal request {request.request_no} rejected.'
            ),
        )

        return request

    def start_execution(self, request_id: str, actor=None):
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

        old_status = request.status
        request.status = DisposalRequestStatus.EXECUTING
        request.save()
        self._mark_assets_as_scrapped(request, actor)
        self.closed_loop_service.log_status_change(
            actor=actor,
            instance=request,
            old_status=old_status,
            new_status=request.status,
            description=f'Disposal request {request.request_no} entered execution.',
        )

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
            old_status = request.status
            request.status = DisposalRequestStatus.COMPLETED
            request.save()
            self.closed_loop_service.log_status_change(
                actor=item.appraised_by,
                instance=request,
                old_status=old_status,
                new_status=request.status,
                description=f'Disposal request {request.request_no} completed after all items were executed.',
            )

        return item

    def complete_request(self, request_id: str, actor=None):
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

        old_status = request.status
        request.status = DisposalRequestStatus.COMPLETED
        request.save()
        self.closed_loop_service.log_status_change(
            actor=actor,
            instance=request,
            old_status=old_status,
            new_status=request.status,
            description=f'Disposal request {request.request_no} completed.',
        )

        return request

    def cancel(self, request_id: str, reason: str = None, actor=None):
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

        previous_status = request.status
        request.status = DisposalRequestStatus.CANCELLED
        request.save()
        if previous_status == DisposalRequestStatus.EXECUTING:
            self._restore_assets_after_cancel(request, actor, reason)
        self.closed_loop_service.log_status_change(
            actor=actor,
            instance=request,
            old_status=previous_status,
            new_status=request.status,
            description=f'Disposal request {request.request_no} cancelled.',
        )

        return request

    def _mark_assets_as_scrapped(self, request: DisposalRequest, actor):
        for item in request.items.filter(is_deleted=False).select_related('asset'):
            asset = item.asset
            if asset is None:
                continue
            if asset.asset_status == 'scrapped':
                continue

            custom_fields = dict(item.custom_fields or {})
            custom_fields['asset_previous_status'] = asset.asset_status
            item.custom_fields = custom_fields
            item.save(update_fields=['custom_fields', 'updated_at'])

            self.asset_service.change_status(
                str(asset.id),
                'scrapped',
                actor or request.applicant,
                reason=f'Disposal request {request.request_no} entered execution',
            )

    def _restore_assets_after_cancel(self, request: DisposalRequest, actor, reason: str = None):
        for item in request.items.filter(is_deleted=False).select_related('asset'):
            asset = item.asset
            if asset is None or asset.asset_status != 'scrapped':
                continue

            previous_status = str((item.custom_fields or {}).get('asset_previous_status') or '').strip()
            if not previous_status:
                continue

            self.asset_service.change_status(
                str(asset.id),
                previous_status,
                actor or request.applicant,
                reason=reason or f'Disposal request {request.request_no} cancelled',
            )

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
