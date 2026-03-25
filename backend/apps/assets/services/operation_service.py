"""
Services for Asset Operation Models (Pickup, Transfer, Return, Loan).

All services inherit from BaseCRUDService for standard CRUD operations
and extend with business-specific methods.
"""
from typing import Dict, List, Optional, Any
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from apps.common.services.base_crud import BaseCRUDService
from apps.assets.models import (
    Asset,
    AssetPickup,
    PickupItem,
    AssetTransfer,
    TransferItem,
    AssetReturn,
    ReturnItem,
    AssetLoan,
    LoanItem,
)
from apps.projects.services import ProjectAssetService


def _extract_reference_id(value):
    """Normalize nested reference payloads into scalar ids."""
    if isinstance(value, dict):
        return value.get('id') or value.get('value') or value.get('code')
    return getattr(value, 'id', value)


def _normalize_item_id(value) -> str:
    return str(value or '').strip()


def _resolve_first_present(item_data: Dict[str, Any], *keys: str, fallback=None):
    for key in keys:
        if key not in item_data:
            continue
        value = _extract_reference_id(item_data.get(key))
        if value in (None, ''):
            continue
        return value
    return fallback


def _resolve_line_item_asset_id(item_data: Dict[str, Any], *, fallback=None):
    return _resolve_first_present(
        item_data,
        'asset_id',
        'assetId',
        'asset',
        fallback=fallback,
    )


def _resolve_line_item_location_id(item_data: Dict[str, Any], *, fallback=None):
    return _resolve_first_present(
        item_data,
        'to_location_id',
        'toLocationId',
        'to_location',
        'toLocation',
        fallback=fallback,
    )


def _resolve_line_item_project_allocation_id(item_data: Dict[str, Any], *, fallback=None):
    return _resolve_first_present(
        item_data,
        'project_allocation_id',
        'projectAllocationId',
        'project_allocation',
        'projectAllocation',
        fallback=fallback,
    )


def _is_blank_line_item(item_data: Dict[str, Any]) -> bool:
    if not isinstance(item_data, dict):
        return True

    for key, value in item_data.items():
        if key in {'id', '_isNew', '_is_new'}:
            continue
        normalized = _extract_reference_id(value)
        if normalized in (None, '', []):
            continue
        return False
    return True


def _ensure_asset_selected(item_data: Dict[str, Any], *, fallback=None):
    asset_id = _resolve_line_item_asset_id(item_data, fallback=fallback)
    if asset_id:
        return str(asset_id)
    if _is_blank_line_item(item_data):
        return ''
    raise ValidationError({
        'items': 'Asset is required for each line item'
    })


def _validate_unique_asset_selection(
    items: Optional[List[Dict[str, Any]]],
    *,
    existing_items: Optional[Dict[str, Any]] = None,
):
    seen_asset_ids = {}
    for index, raw_item in enumerate(items or []):
        item_data = raw_item or {}
        item_id = _normalize_item_id(item_data.get('id'))
        existing_item = existing_items.get(item_id) if existing_items and item_id else None
        asset_id = _resolve_line_item_asset_id(
            item_data,
            fallback=getattr(existing_item, 'asset_id', None),
        )
        if not asset_id:
            continue
        normalized_asset_id = str(asset_id)
        previous_index = seen_asset_ids.get(normalized_asset_id)
        if previous_index is not None:
            raise ValidationError({
                'items': (
                    'Duplicate asset selection is not allowed '
                    f'(rows {previous_index + 1} and {index + 1})'
                )
            })
        seen_asset_ids[normalized_asset_id] = index


def _get_asset_or_raise(asset_id: str, organization_id: str) -> Asset:
    try:
        return Asset.objects.get(
            id=asset_id,
            organization_id=organization_id,
            is_deleted=False
        )
    except Asset.DoesNotExist as exc:
        raise ValidationError({
            'asset': f'Asset with ID {asset_id} not found'
        }) from exc


def _get_operation_instance_or_raise(model_class, instance_id: str, organization_id: Optional[str]):
    queryset = model_class.all_objects.filter(id=instance_id, is_deleted=False)
    if organization_id:
        queryset = queryset.filter(organization_id=organization_id)
    return queryset.get()


def _get_project_allocation_or_raise(
    project_allocation_id: str,
    organization_id: str,
    *,
    asset_id: Optional[str] = None,
):
    from apps.projects.models import ProjectAsset

    try:
        allocation = ProjectAsset.objects.select_related('project').get(
            id=project_allocation_id,
            organization_id=organization_id,
            is_deleted=False,
        )
    except ProjectAsset.DoesNotExist as exc:
        raise ValidationError({
            'project_allocation_id': f'Project allocation {project_allocation_id} not found'
        }) from exc

    if asset_id and str(allocation.asset_id) != str(asset_id):
        raise ValidationError({
            'project_allocation_id': 'The selected project allocation does not belong to the current asset'
        })

    return allocation


def _find_unique_active_project_allocation(asset_id: str, organization_id: str):
    from apps.projects.models import ProjectAsset

    candidates = list(
        ProjectAsset.objects.select_related('project')
        .filter(
            organization_id=organization_id,
            asset_id=asset_id,
            is_deleted=False,
            return_status='in_use',
        )
        .order_by('-allocation_date', '-created_at')[:2]
    )
    if len(candidates) == 1:
        return candidates[0]
    return None


def _resolve_project_allocation_for_return(
    item_data: Dict[str, Any],
    *,
    organization_id: str,
    asset_id: str,
    fallback=None,
):
    project_allocation_id = _resolve_line_item_project_allocation_id(item_data, fallback=fallback)
    if project_allocation_id:
        allocation = _get_project_allocation_or_raise(
            str(project_allocation_id),
            organization_id,
            asset_id=asset_id,
        )
        if allocation.return_status != 'in_use':
            raise ValidationError({
                'project_allocation_id': 'Only active project allocations can be returned'
            })
        return allocation

    return _find_unique_active_project_allocation(str(asset_id), organization_id)


def _build_project_return_note(return_order: AssetReturn) -> str:
    note = f"Returned via {return_order.return_no}"
    reason = str(getattr(return_order, 'return_reason', '') or '').strip()
    if reason:
        note = f"{note}: {reason}"
    return note


def _build_project_return_rejection_note(return_order: AssetReturn, reason: str = '') -> str:
    note = f"Return rejected via {return_order.return_no}"
    normalized_reason = str(reason or getattr(return_order, 'reject_reason', '') or '').strip()
    if normalized_reason:
        note = f"{note}: {normalized_reason}"
    return note


def _prepare_line_item_operations(
    items: Optional[List[Dict[str, Any]]],
    *,
    existing_items: Dict[str, Any],
    parent_label: str,
):
    """
    Normalize nested line item payloads before applying mutations.

    We compute the full final state up front so updates can safely delete rows
    whose current asset occupancy would otherwise violate the parent+asset
    unique constraint during in-place replacement.
    """
    _validate_unique_asset_selection(items, existing_items=existing_items)

    operations = []
    submitted_ids = set()

    for raw_item in items or []:
        item_data = raw_item or {}
        item_id = _normalize_item_id(item_data.get('id'))
        existing_item = existing_items.get(item_id) if item_id else None

        if item_id and existing_item is None:
            raise ValidationError({
                'items': f'Line item {item_id} does not belong to this {parent_label}'
            })

        asset_id = _ensure_asset_selected(
            item_data,
            fallback=getattr(existing_item, 'asset_id', None),
        )
        normalized_asset_id = str(asset_id) if asset_id else ''

        if item_id:
            submitted_ids.add(item_id)

        operations.append({
            'item_data': item_data,
            'item_id': item_id,
            'existing_item': existing_item,
            'asset_id': normalized_asset_id,
        })

    deleted_ids = {
        item_id for item_id in existing_items.keys()
        if item_id not in submitted_ids
    }
    recreated_ids = {
        operation['item_id']
        for operation in operations
        if operation['item_id']
        and operation['asset_id']
        and str(operation['existing_item'].asset_id) != operation['asset_id']
    }

    return operations, deleted_ids, recreated_ids


# ========== Pickup Order Service ==========

class AssetPickupService(BaseCRUDService):
    """
    Service for Asset Pickup Order operations.

    Extends BaseCRUDService with:
    - Approval workflow
    - Asset status update on approval
    - Pickup completion tracking
    """

    def __init__(self):
        super().__init__(AssetPickup)

    def create_with_items(
        self,
        data: Dict,
        items: List[Dict],
        user,
        organization_id: str
    ) -> AssetPickup:
        """
        Create a pickup order with items.

        Args:
            data: Pickup order data
            items: List of items with asset_id and optional quantity/remark
            user: User creating the pickup
            organization_id: Organization ID

        Returns:
            Created pickup order
        """
        # Set applicant to current user if not specified
        if 'applicant_id' not in data and 'applicant' not in data:
            data['applicant_id'] = user.id

        # Set organization
        data['organization_id'] = organization_id

        with transaction.atomic():
            pickup = self.create(data, user)

            _validate_unique_asset_selection(items)

            # Create items with snapshots
            for item_data in items:
                asset_id = _ensure_asset_selected(item_data)
                if not asset_id:
                    continue

                asset = _get_asset_or_raise(asset_id, organization_id)

                # Validate asset is available for pickup
                if asset.asset_status not in ['idle', 'pending']:
                    raise ValidationError({
                        'asset': f'Asset {asset.asset_name} is not available (status: {asset.get_status_label()})'
                    })

                PickupItem.objects.create(
                    pickup=pickup,
                    asset=asset,
                    quantity=item_data.get('quantity', 1),
                    remark=item_data.get('remark', ''),
                    snapshot_original_location=asset.location,
                    snapshot_original_custodian=asset.custodian,
                    organization_id=organization_id
                )

            # Auto-start workflow if enabled
            self._auto_start_workflow(pickup, user, organization_id)

        return pickup

    def update_with_items(
        self,
        pickup_id: str,
        data: Dict,
        items: Optional[List[Dict]],
        user,
        organization_id: str
    ) -> AssetPickup:
        """
        Update a pickup order with diff-patch items logic.

        Items handling:
        - Item with 'id' matching existing item → update
        - Item without 'id' → create new
        - Existing items whose 'id' is not in submitted list → delete

        Args:
            pickup_id: Pickup order ID
            data: Pickup order updated fields
            items: List of items (None means skip items update)
            user: User performing the update
            organization_id: Organization ID

        Returns:
            Updated pickup order
        """
        with transaction.atomic():
            pickup = _get_operation_instance_or_raise(AssetPickup, pickup_id, organization_id)

            if pickup.status != 'draft':
                raise ValidationError({
                    'status': f'Cannot edit pickup with status {pickup.get_status_label()}'
                })

            # Update parent fields
            for attr, value in data.items():
                if hasattr(pickup, attr):
                    setattr(pickup, attr, value)
            pickup.save()

            # Diff-patch items
            if items is not None:
                existing_items = {str(item.id): item for item in pickup.items.all()}
                operations, deleted_ids, recreated_ids = _prepare_line_item_operations(
                    items,
                    existing_items=existing_items,
                    parent_label='pickup order',
                )

                for item_id in deleted_ids | recreated_ids:
                    existing_items[item_id].delete()

                for operation in operations:
                    item_data = operation['item_data']
                    item_id = operation['item_id']
                    existing_item = operation['existing_item']
                    asset_id = operation['asset_id']

                    if item_id and item_id not in recreated_ids:
                        if item_data.get('quantity') is not None:
                            existing_item.quantity = item_data['quantity']
                        if 'remark' in item_data:
                            existing_item.remark = item_data.get('remark', '')
                        existing_item.save()
                        continue

                    if not asset_id:
                        continue

                    asset = _get_asset_or_raise(asset_id, organization_id)
                    if asset.asset_status not in ['idle', 'pending']:
                        raise ValidationError({
                            'asset': f'Asset {asset.asset_name} is not available (status: {asset.get_status_label()})'
                        })

                    create_kwargs = {
                        'pickup': pickup,
                        'asset': asset,
                        'quantity': item_data.get(
                            'quantity',
                            existing_item.quantity if existing_item else 1,
                        ),
                        'remark': (
                            item_data.get('remark', '')
                            if existing_item is None
                            else item_data.get('remark', existing_item.remark)
                        ),
                        'snapshot_original_location': asset.location,
                        'snapshot_original_custodian': asset.custodian,
                        'organization_id': organization_id,
                    }
                    if existing_item is not None:
                        create_kwargs['id'] = item_id
                        create_kwargs['custom_fields'] = existing_item.custom_fields

                    PickupItem.objects.create(**create_kwargs)

        pickup.refresh_from_db()
        return pickup

    def _auto_start_workflow(self, pickup: AssetPickup, user, organization_id: str):
        """
        Automatically start workflow for pickup order if a workflow definition exists.

        Args:
            pickup: The pickup order instance
            user: User who created the pickup
            organization_id: Organization ID
        """
        try:
            from apps.workflows.models import WorkflowDefinition
            from apps.workflows.services.workflow_engine import WorkflowEngine

            # Find active workflow definition for asset pickup
            definition = WorkflowDefinition.objects.filter(
                organization_id=organization_id,
                business_object_code='asset_pickup',
                status='published',
                is_deleted=False
            ).first()

            if definition:
                # Start workflow instance
                engine = WorkflowEngine()
                success, instance, error = engine.start_workflow(
                    definition=definition,
                    business_object_code='asset_pickup',
                    business_id=str(pickup.id),
                    business_no=pickup.pickup_no,
                    initiator=user,
                    title=f'Asset Pickup: {pickup.pickup_no}',
                    description=f'Pickup order by {pickup.applicant.username if pickup.applicant else "Unknown"}',
                    priority='normal'
                )

                if success and instance:
                    # Link workflow instance when the model exposes a workflow field.
                    if hasattr(pickup, 'workflow_instance'):
                        pickup.workflow_instance = instance
                        pickup.save(update_fields=['workflow_instance'])
        except Exception as e:
            # Log error but don't fail the pickup creation
            # Workflow can be started manually later
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Failed to auto-start workflow for pickup {pickup.pickup_no}: {str(e)}')

    def submit_for_approval(self, pickup_id: str, user) -> AssetPickup:
        """
        Submit pickup order for approval.

        Args:
            pickup_id: Pickup order ID
            user: User submitting the request

        Returns:
            Updated pickup order
        """
        pickup = self.get(pickup_id, user=user)

        if pickup.status != 'draft':
            raise ValidationError({
                'status': f'Cannot submit pickup with status {pickup.get_status_label()}'
            })

        # Validate that pickup has items
        if pickup.items.count() == 0:
            raise ValidationError({
                'items': 'Cannot submit pickup order without items'
            })

        pickup.status = 'pending'
        pickup.save()

        return pickup

    def approve(
        self,
        pickup_id: str,
        user,
        approval: str,
        comment: str = ''
    ) -> AssetPickup:
        """
        Approve or reject a pickup order.

        Args:
            pickup_id: Pickup order ID
            user: User approving the request
            approval: 'approved' or 'rejected'
            comment: Optional approval comment

        Returns:
            Updated pickup order
        """
        pickup = self.get(pickup_id, user=user)

        if pickup.status != 'pending':
            raise ValidationError({
                'status': f'Cannot approve pickup with status {pickup.get_status_label()}'
            })

        pickup.approved_by = user
        pickup.approved_at = timezone.now()
        pickup.approval_comment = comment

        if approval == 'approved':
            pickup.status = 'approved'

            # Update asset status and custodian for all items
            for item in pickup.items.all():
                asset = item.asset
                asset.asset_status = 'in_use'
                asset.custodian = pickup.applicant
                asset.department = pickup.department
                asset.save()

                # Log status change
                self._log_asset_status_change(
                    asset,
                    'idle',
                    'in_use',
                    user,
                    f'Approved via pickup order {pickup.pickup_no}'
                )

        else:
            pickup.status = 'rejected'

        pickup.save()
        return pickup

    def complete_pickup(self, pickup_id: str, user) -> AssetPickup:
        """
        Mark pickup order as completed.

        Args:
            pickup_id: Pickup order ID
            user: User completing the pickup

        Returns:
            Updated pickup order
        """
        pickup = self.get(pickup_id, user=user)

        if pickup.status != 'approved':
            raise ValidationError({
                'status': f'Cannot complete pickup with status {pickup.get_status_label()}'
            })

        pickup.status = 'completed'
        pickup.completed_at = timezone.now()
        pickup.save()

        return pickup

    def cancel_pickup(self, pickup_id: str, user) -> AssetPickup:
        """
        Cancel a pickup order.

        Args:
            pickup_id: Pickup order ID
            user: User cancelling the request

        Returns:
            Updated pickup order
        """
        pickup = self.get(pickup_id, user=user)

        if pickup.status not in ['draft', 'pending']:
            raise ValidationError({
                'status': f'Cannot cancel pickup with status {pickup.get_status_label()}'
            })

        pickup.status = 'cancelled'
        pickup.save()

        return pickup

    def get_pending_approvals(self, organization_id: str) -> List[AssetPickup]:
        """Get all pending pickup orders for an organization."""
        return self.query(
            filters={'organization_id': organization_id, 'status': 'pending'},
            order_by='-created_at'
        )

    def _log_asset_status_change(
        self,
        asset: Asset,
        old_status: str,
        new_status: str,
        user,
        reason: str
    ):
        """Log asset status change."""
        from apps.assets.models import AssetStatusLog
        AssetStatusLog.objects.create(
            organization=asset.organization,
            asset=asset,
            old_status=old_status,
            new_status=new_status,
            reason=reason,
            created_by=user
        )


# ========== Transfer Order Service ==========

class AssetTransferService(BaseCRUDService):
    """
    Service for Asset Transfer Order operations.

    Extends BaseCRUDService with:
    - Dual approval workflow (from/to departments)
    - Asset transfer completion
    """

    def __init__(self):
        super().__init__(AssetTransfer)

    def create_with_items(
        self,
        data: Dict,
        items: List[Dict],
        user,
        organization_id: str
    ) -> AssetTransfer:
        """Create a transfer order with items."""
        # Validate departments are different
        if data.get('from_department') == data.get('to_department'):
            raise ValidationError({
                'to_department': 'Source and target departments must be different'
            })

        data['organization_id'] = organization_id

        with transaction.atomic():
            transfer = self.create(data, user)

            _validate_unique_asset_selection(items)

            # Create items with snapshots
            for item_data in items:
                asset_id = _ensure_asset_selected(item_data)
                if not asset_id:
                    continue

                asset = _get_asset_or_raise(asset_id, organization_id)

                TransferItem.objects.create(
                    transfer=transfer,
                    asset=asset,
                    from_location=asset.location,
                    from_custodian=asset.custodian,
                    to_location_id=_resolve_line_item_location_id(item_data),
                    remark=item_data.get('remark', ''),
                    organization_id=organization_id
                )

        return transfer

    def update_with_items(
        self,
        transfer_id: str,
        data: Dict,
        items: Optional[List[Dict]],
        user,
        organization_id: str
    ) -> AssetTransfer:
        """Update a transfer order with diff-patch items logic."""
        with transaction.atomic():
            transfer = _get_operation_instance_or_raise(AssetTransfer, transfer_id, organization_id)

            if transfer.status != 'draft':
                raise ValidationError({
                    'status': f'Cannot edit transfer with status {transfer.get_status_label()}'
                })

            for attr, value in data.items():
                if hasattr(transfer, attr):
                    setattr(transfer, attr, value)
            transfer.save()

            if items is not None:
                existing_items = {str(item.id): item for item in transfer.items.all()}
                operations, deleted_ids, recreated_ids = _prepare_line_item_operations(
                    items,
                    existing_items=existing_items,
                    parent_label='transfer order',
                )

                for item_id in deleted_ids | recreated_ids:
                    existing_items[item_id].delete()

                for operation in operations:
                    item_data = operation['item_data']
                    item_id = operation['item_id']
                    existing_item = operation['existing_item']
                    asset_id = operation['asset_id']

                    if item_id and item_id not in recreated_ids:
                        existing_item.to_location_id = _resolve_line_item_location_id(
                            item_data,
                            fallback=existing_item.to_location_id,
                        )
                        if 'remark' in item_data:
                            existing_item.remark = item_data.get('remark', '')
                        existing_item.save()
                        continue

                    if not asset_id:
                        continue

                    asset = _get_asset_or_raise(asset_id, organization_id)
                    create_kwargs = {
                        'transfer': transfer,
                        'asset': asset,
                        'from_location': asset.location,
                        'from_custodian': asset.custodian,
                        'to_location_id': _resolve_line_item_location_id(
                            item_data,
                            fallback=existing_item.to_location_id if existing_item else None,
                        ),
                        'remark': (
                            item_data.get('remark', '')
                            if existing_item is None
                            else item_data.get('remark', existing_item.remark)
                        ),
                        'organization_id': organization_id,
                    }
                    if existing_item is not None:
                        create_kwargs['id'] = item_id
                        create_kwargs['custom_fields'] = existing_item.custom_fields

                    TransferItem.objects.create(**create_kwargs)

        transfer.refresh_from_db()
        return transfer

    def submit_for_approval(self, transfer_id: str, user) -> AssetTransfer:
        """Submit transfer order for approval."""
        transfer = self.get(transfer_id, user=user)

        if transfer.status != 'draft':
            raise ValidationError({
                'status': f'Cannot submit transfer with status {transfer.get_status_label()}'
            })

        if transfer.items.count() == 0:
            raise ValidationError({
                'items': 'Cannot submit transfer order without items'
            })

        transfer.status = 'pending'
        transfer.save()

        return transfer

    def approve_from(
        self,
        transfer_id: str,
        user,
        comment: str = ''
    ) -> AssetTransfer:
        """Approve from source department."""
        transfer = self.get(transfer_id, user=user)

        if transfer.status != 'pending':
            raise ValidationError({
                'status': 'Transfer must be in pending status for source approval'
            })

        transfer.status = 'out_approved'
        transfer.from_approved_by = user
        transfer.from_approved_at = timezone.now()
        transfer.from_approve_comment = comment
        transfer.save()

        return transfer

    def approve_to(
        self,
        transfer_id: str,
        user,
        comment: str = ''
    ) -> AssetTransfer:
        """Approve from target department."""
        transfer = self.get(transfer_id, user=user)

        if transfer.status != 'out_approved':
            raise ValidationError({
                'status': 'Transfer must be approved by source department first'
            })

        transfer.status = 'approved'
        transfer.to_approved_by = user
        transfer.to_approved_at = timezone.now()
        transfer.to_approve_comment = comment
        transfer.save()

        return transfer

    def complete_transfer(self, transfer_id: str, user) -> AssetTransfer:
        """Complete the transfer and update assets."""
        transfer = self.get(transfer_id, user=user)

        if transfer.status != 'approved':
            raise ValidationError({
                'status': f'Cannot complete transfer with status {transfer.get_status_label()}'
            })

        with transaction.atomic():
            for item in transfer.items.all():
                asset = item.asset
                asset.department = transfer.to_department
                asset.location = item.to_location
                asset.custodian = None  # Clear custodian on transfer
                asset.save()

            transfer.status = 'completed'
            transfer.completed_at = timezone.now()
            transfer.save()

        return transfer

    def get_pending_transfers(self, organization_id: str) -> List[AssetTransfer]:
        """Get all pending transfers for an organization."""
        return self.query(
            filters={'organization_id': organization_id, 'status__in': ['pending', 'out_approved']},
            order_by='-created_at'
        )


# ========== Return Order Service ==========

class AssetReturnService(BaseCRUDService):
    """
    Service for Asset Return Order operations.

    Extends BaseCRUDService with:
    - Return confirmation
    - Asset status update on completion
    """

    def __init__(self):
        super().__init__(AssetReturn)

    def create_with_items(
        self,
        data: Dict,
        items: List[Dict],
        user,
        organization_id: str
    ) -> AssetReturn:
        """Create a return order with items."""
        # Set returner to current user
        if 'returner_id' not in data and 'returner' not in data:
            data['returner_id'] = user.id

        data['organization_id'] = organization_id

        with transaction.atomic():
            return_order = self.create(data, user)

            _validate_unique_asset_selection(items)

            # Create items
            for item_data in items:
                asset_id = _ensure_asset_selected(item_data)
                if not asset_id:
                    continue

                asset = _get_asset_or_raise(asset_id, organization_id)
                project_allocation = _resolve_project_allocation_for_return(
                    item_data,
                    organization_id=organization_id,
                    asset_id=str(asset.id),
                )

                # Validate asset custodian
                if asset.custodian_id != user.id:
                    raise ValidationError({
                        'asset': f'Asset {asset.asset_name} is not assigned to you'
                    })

                ReturnItem.objects.create(
                    asset_return=return_order,
                    asset=asset,
                    project_allocation=project_allocation,
                    asset_status=item_data.get('asset_status') or item_data.get('assetStatus', 'idle'),
                    condition_description=item_data.get('condition_description') or item_data.get('conditionDescription', ''),
                    remark=item_data.get('remark', ''),
                    organization_id=organization_id
                )

        return return_order

    def update_with_items(
        self,
        return_id: str,
        data: Dict,
        items: Optional[List[Dict]],
        user,
        organization_id: str
    ) -> AssetReturn:
        """Update a return order with diff-patch items logic."""
        with transaction.atomic():
            return_order = _get_operation_instance_or_raise(AssetReturn, return_id, organization_id)

            if return_order.status != 'draft':
                raise ValidationError({
                    'status': f'Cannot edit return with status {return_order.get_status_label()}'
                })

            for attr, value in data.items():
                if hasattr(return_order, attr):
                    setattr(return_order, attr, value)
            return_order.save()

            if items is not None:
                existing_items = {str(item.id): item for item in return_order.items.all()}
                operations, deleted_ids, recreated_ids = _prepare_line_item_operations(
                    items,
                    existing_items=existing_items,
                    parent_label='return order',
                )

                for item_id in deleted_ids | recreated_ids:
                    existing_items[item_id].delete()

                for operation in operations:
                    item_data = operation['item_data']
                    item_id = operation['item_id']
                    existing_item = operation['existing_item']
                    asset_id = operation['asset_id']

                    if item_id and item_id not in recreated_ids:
                        asset_status = item_data.get('asset_status')
                        if asset_status is None:
                            asset_status = item_data.get('assetStatus')
                        project_allocation = _resolve_project_allocation_for_return(
                            item_data,
                            organization_id=organization_id,
                            asset_id=str(existing_item.asset_id),
                            fallback=getattr(existing_item, 'project_allocation_id', None),
                        )
                        if asset_status is not None:
                            existing_item.asset_status = asset_status
                        existing_item.project_allocation = project_allocation
                        if 'condition_description' in item_data or 'conditionDescription' in item_data:
                            existing_item.condition_description = (
                                item_data.get('condition_description')
                                if 'condition_description' in item_data
                                else item_data.get('conditionDescription', '')
                            )
                        if 'remark' in item_data:
                            existing_item.remark = item_data.get('remark', '')
                        existing_item.save()
                        continue

                    if not asset_id:
                        continue

                    asset = _get_asset_or_raise(asset_id, organization_id)
                    project_allocation = _resolve_project_allocation_for_return(
                        item_data,
                        organization_id=organization_id,
                        asset_id=str(asset.id),
                        fallback=getattr(existing_item, 'project_allocation_id', None) if existing_item is not None else None,
                    )
                    if asset.custodian_id != user.id:
                        raise ValidationError({
                            'asset': f'Asset {asset.asset_name} is not assigned to you'
                        })

                    asset_status = item_data.get('asset_status')
                    if asset_status is None:
                        asset_status = item_data.get('assetStatus')
                    if asset_status is None and existing_item is not None:
                        asset_status = existing_item.asset_status
                    if asset_status is None:
                        asset_status = 'idle'

                    if 'condition_description' in item_data:
                        condition_description = item_data.get('condition_description')
                    elif 'conditionDescription' in item_data:
                        condition_description = item_data.get('conditionDescription', '')
                    elif existing_item is not None:
                        condition_description = existing_item.condition_description
                    else:
                        condition_description = ''

                    create_kwargs = {
                        'asset_return': return_order,
                        'asset': asset,
                        'project_allocation': project_allocation,
                        'asset_status': asset_status,
                        'condition_description': condition_description,
                        'remark': (
                            item_data.get('remark', '')
                            if existing_item is None
                            else item_data.get('remark', existing_item.remark)
                        ),
                        'organization_id': organization_id,
                    }
                    if existing_item is not None:
                        create_kwargs['id'] = item_id
                        create_kwargs['custom_fields'] = existing_item.custom_fields

                    ReturnItem.objects.create(**create_kwargs)

        return_order.refresh_from_db()
        return return_order

    def confirm_return(
        self,
        return_id: str,
        user,
    ) -> AssetReturn:
        """
        Confirm and complete a return order.

        Args:
            return_id: Return order ID
            user: User confirming the return

        Returns:
            Updated return order
        """
        return_order = self.get(return_id, user=user)

        if return_order.status != 'pending':
            raise ValidationError({
                'status': f'Cannot confirm return with status {return_order.get_status_label()}'
            })

        with transaction.atomic():
            project_asset_service = ProjectAssetService()
            for item in return_order.items.all():
                asset = item.asset
                asset.asset_status = item.asset_status
                asset.custodian = None
                asset.location = return_order.return_location
                asset.save()

                project_allocation = item.project_allocation
                if project_allocation is None:
                    project_allocation = _find_unique_active_project_allocation(
                        str(item.asset_id),
                        str(return_order.organization_id),
                    )
                    if project_allocation is not None:
                        item.project_allocation = project_allocation
                        item.save(update_fields=['project_allocation', 'updated_at'])

                if project_allocation is not None:
                    project_asset_service.mark_returned(
                        str(project_allocation.id),
                        return_date=return_order.return_date,
                        note=_build_project_return_note(return_order),
                        organization_id=str(return_order.organization_id),
                        user=user,
                    )

            return_order.status = 'completed'
            return_order.confirmed_by = user
            return_order.confirmed_at = timezone.now()
            return_order.completed_at = timezone.now()
            return_order.save()

        return return_order

    def reject_return(
        self,
        return_id: str,
        user,
        reason: str = ''
    ) -> AssetReturn:
        """Reject a return order."""
        return_order = self.get(return_id, user=user)

        if return_order.status != 'pending':
            raise ValidationError({
                'status': f'Cannot reject return with status {return_order.get_status_label()}'
            })

        with transaction.atomic():
            project_asset_service = ProjectAssetService()
            for item in return_order.items.all():
                project_allocation = item.project_allocation
                if project_allocation is None:
                    project_allocation = _find_unique_active_project_allocation(
                        str(item.asset_id),
                        str(return_order.organization_id),
                    )
                    if project_allocation is not None:
                        item.project_allocation = project_allocation
                        item.save(update_fields=['project_allocation', 'updated_at'])

                if project_allocation is not None:
                    project_asset_service.record_return_rejection(
                        str(project_allocation.id),
                        note=_build_project_return_rejection_note(return_order, reason),
                        organization_id=str(return_order.organization_id),
                        user=user,
                    )

            return_order.status = 'rejected'
            return_order.reject_reason = reason
            return_order.save(update_fields=['status', 'reject_reason', 'updated_at'])

        return return_order

    def get_pending_returns(self, organization_id: str) -> List[AssetReturn]:
        """Get all pending returns for an organization."""
        return self.query(
            filters={'organization_id': organization_id, 'status': 'pending'},
            order_by='-created_at'
        )


# ========== Loan Order Service ==========

class AssetLoanService(BaseCRUDService):
    """
    Service for Asset Loan Order operations.

    Extends BaseCRUDService with:
    - Loan approval workflow
    - Borrow confirmation
    - Return confirmation
    - Overdue checking
    """

    def __init__(self):
        super().__init__(AssetLoan)

    def create_with_items(
        self,
        data: Dict,
        items: List[Dict],
        user,
        organization_id: str
    ) -> AssetLoan:
        """Create a loan order with items."""
        # Validate dates
        from datetime import timedelta

        borrow_date = data.get('borrow_date')
        return_date = data.get('expected_return_date')

        if borrow_date and return_date and return_date < borrow_date:
            raise ValidationError({
                'expected_return_date': 'Return date must be after borrow date'
            })

        # Limit loan duration to 90 days
        if borrow_date and return_date:
            max_date = borrow_date + timedelta(days=90)
            if return_date > max_date:
                raise ValidationError({
                    'expected_return_date': 'Loan duration cannot exceed 90 days'
                })

        # Set borrower to current user
        if 'borrower_id' not in data and 'borrower' not in data:
            data['borrower_id'] = user.id

        data['organization_id'] = organization_id

        with transaction.atomic():
            loan = self.create(data, user)

            _validate_unique_asset_selection(items)

            # Create items
            for item_data in items:
                asset_id = _ensure_asset_selected(item_data)
                if not asset_id:
                    continue

                asset = _get_asset_or_raise(asset_id, organization_id)

                # Validate asset is available
                if asset.asset_status not in ['idle', 'pending']:
                    raise ValidationError({
                        'asset': f'Asset {asset.asset_name} is not available'
                    })

                LoanItem.objects.create(
                    loan=loan,
                    asset=asset,
                    remark=item_data.get('remark', ''),
                    organization_id=organization_id
                )

        return loan

    def update_with_items(
        self,
        loan_id: str,
        data: Dict,
        items: Optional[List[Dict]],
        user,
        organization_id: str
    ) -> AssetLoan:
        """Update a loan order with diff-patch items logic."""
        with transaction.atomic():
            loan = _get_operation_instance_or_raise(AssetLoan, loan_id, organization_id)

            if loan.status != 'draft':
                raise ValidationError({
                    'status': f'Cannot edit loan with status {loan.get_status_label()}'
                })

            for attr, value in data.items():
                if hasattr(loan, attr):
                    setattr(loan, attr, value)
            loan.save()

            if items is not None:
                existing_items = {str(item.id): item for item in loan.items.all()}
                operations, deleted_ids, recreated_ids = _prepare_line_item_operations(
                    items,
                    existing_items=existing_items,
                    parent_label='loan order',
                )

                for item_id in deleted_ids | recreated_ids:
                    existing_items[item_id].delete()

                for operation in operations:
                    item_data = operation['item_data']
                    item_id = operation['item_id']
                    existing_item = operation['existing_item']
                    asset_id = operation['asset_id']

                    if item_id and item_id not in recreated_ids:
                        if 'remark' in item_data:
                            existing_item.remark = item_data.get('remark', '')
                        existing_item.save()
                        continue

                    if not asset_id:
                        continue

                    asset = _get_asset_or_raise(asset_id, organization_id)
                    if asset.asset_status not in ['idle', 'pending']:
                        raise ValidationError({
                            'asset': f'Asset {asset.asset_name} is not available'
                        })

                    create_kwargs = {
                        'loan': loan,
                        'asset': asset,
                        'remark': (
                            item_data.get('remark', '')
                            if existing_item is None
                            else item_data.get('remark', existing_item.remark)
                        ),
                        'organization_id': organization_id,
                    }
                    if existing_item is not None:
                        create_kwargs['id'] = item_id
                        create_kwargs['custom_fields'] = existing_item.custom_fields

                    LoanItem.objects.create(**create_kwargs)

        loan.refresh_from_db()
        return loan

    def approve_loan(
        self,
        loan_id: str,
        user,
        approval: str,
        comment: str = ''
    ) -> AssetLoan:
        """Approve or reject a loan order."""
        loan = self.get(loan_id, user=user)

        if loan.status != 'pending':
            raise ValidationError({
                'status': f'Cannot approve loan with status {loan.get_status_label()}'
            })

        loan.approved_by = user
        loan.approved_at = timezone.now()
        loan.approval_comment = comment

        if approval == 'approved':
            loan.status = 'approved'
        else:
            loan.status = 'rejected'

        loan.save()
        return loan

    def confirm_borrow(self, loan_id: str, user) -> AssetLoan:
        """Confirm that assets have been lent out."""
        loan = self.get(loan_id, user=user)

        if loan.status != 'approved':
            raise ValidationError({
                'status': f'Cannot confirm borrow with status {loan.get_status_label()}'
            })

        with transaction.atomic():
            # Update asset status
            for item in loan.items.all():
                asset = item.asset
                asset.asset_status = 'in_use'
                asset.custodian = loan.borrower
                asset.save()

            loan.status = 'borrowed'
            loan.lent_by = user
            loan.lent_at = timezone.now()
            loan.save()

        return loan

    def confirm_return(
        self,
        loan_id: str,
        user,
        condition: str = 'good',
        comment: str = ''
    ) -> AssetLoan:
        """Confirm that assets have been returned."""
        loan = self.get(loan_id, user=user)

        if loan.status not in ['borrowed', 'overdue']:
            raise ValidationError({
                'status': f'Cannot confirm return with status {loan.get_status_label()}'
            })

        with transaction.atomic():
            # Update asset status based on condition
            for item in loan.items.all():
                asset = item.asset
                if condition == 'good':
                    asset.asset_status = 'idle'
                elif condition in ['minor_damage', 'major_damage']:
                    asset.asset_status = 'maintenance'
                elif condition == 'lost':
                    asset.asset_status = 'lost'

                asset.custodian = None
                asset.save()

            loan.status = 'returned'
            loan.actual_return_date = timezone.now().date()
            loan.return_confirmed_by = user
            loan.returned_at = timezone.now()
            loan.asset_condition = condition
            loan.return_comment = comment
            loan.save()

        return loan

    def check_overdue_loans(self, organization_id: str) -> int:
        """
        Check and update overdue loans.

        Returns:
            Number of loans marked as overdue
        """
        today = timezone.now().date()
        overdue_loans = AssetLoan.objects.filter(
            organization_id=organization_id,
            status='borrowed',
            expected_return_date__lt=today,
            is_deleted=False
        )

        count = overdue_loans.update(status='overdue')
        return count

    def get_overdue_loans(self, organization_id: str) -> List[AssetLoan]:
        """Get all overdue loans for an organization."""
        return self.query(
            filters={'organization_id': organization_id, 'status': 'overdue'},
            order_by='-expected_return_date'
        )

    def get_active_loans(self, organization_id: str) -> List[AssetLoan]:
        """Get all active (borrowed) loans for an organization."""
        return self.query(
            filters={'organization_id': organization_id, 'status': 'borrowed'},
            order_by='-expected_return_date'
        )
