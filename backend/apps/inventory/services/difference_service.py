"""
Difference service for managing inventory differences.
"""
import uuid
from typing import List, Dict, Optional, Any
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.common.services.base_crud import BaseCRUDService
from apps.inventory.models import (
    InventoryDifference,
    InventoryFollowUp,
    InventorySnapshot,
    InventoryScan,
    InventoryTask,
)
from apps.assets.models import Asset
from apps.accounts.models import User
from apps.notifications.models import Notification
from apps.notifications.services import notification_service
from apps.inventory.services.follow_up_runtime_service import InventoryFollowUpService


class DifferenceService(BaseCRUDService):
    """Service for inventory difference management."""

    MANUAL_FOLLOW_UP_NOTIFICATION_TYPE = 'inventory_difference_follow_up'

    ACTIVE_STATUSES = [
        InventoryDifference.STATUS_PENDING,
        InventoryDifference.STATUS_CONFIRMED,
        InventoryDifference.STATUS_IN_REVIEW,
        InventoryDifference.STATUS_APPROVED,
        InventoryDifference.STATUS_EXECUTING,
    ]
    EXECUTABLE_STATUSES = [
        InventoryDifference.STATUS_CONFIRMED,
        InventoryDifference.STATUS_APPROVED,
    ]
    CLOSEABLE_STATUSES = [
        InventoryDifference.STATUS_RESOLVED,
        InventoryDifference.STATUS_IGNORED,
    ]
    DRAFTABLE_STATUSES = [
        InventoryDifference.STATUS_PENDING,
        InventoryDifference.STATUS_CONFIRMED,
        InventoryDifference.STATUS_IN_REVIEW,
        InventoryDifference.STATUS_APPROVED,
        InventoryDifference.STATUS_EXECUTING,
        InventoryDifference.STATUS_RESOLVED,
        InventoryDifference.STATUS_IGNORED,
    ]

    def __init__(self):
        super().__init__(InventoryDifference)
        self.follow_up_service = InventoryFollowUpService()

    def generate_differences(self, task_id: str) -> List[InventoryDifference]:
        """
        Generate differences for a task by comparing snapshots and scans.

        Args:
            task_id: Task ID

        Returns:
            List of created InventoryDifference instances
        """
        task = InventoryTask.objects.get(id=task_id)

        with transaction.atomic():
            # Get all snapshots for the task
            snapshots = InventorySnapshot.objects.filter(
                task_id=task_id,
                is_deleted=False
            ).select_related('asset')

            # Get all scans for the task
            scans = {
                scan.asset_id: scan
                for scan in InventoryScan.objects.filter(
                    task_id=task_id,
                    is_deleted=False
                )
            }

            differences_to_create = []

            for snapshot in snapshots:
                asset_id = snapshot.asset_id
                scan = scans.get(asset_id)

                # Check for missing assets
                if scan is None:
                    differences_to_create.append(
                        self._create_missing_difference(snapshot)
                    )
                else:
                    # Check for location change
                    if self._has_location_changed(snapshot, scan):
                        differences_to_create.append(
                            self._create_location_difference(snapshot, scan)
                        )

                    # Check for custodian change
                    if self._has_custodian_changed(snapshot, scan):
                        differences_to_create.append(
                            self._create_custodian_difference(snapshot, scan)
                        )

                    # Check for damaged status
                    if scan.scan_status == 'damaged':
                        differences_to_create.append(
                            self._create_damaged_difference(snapshot, scan)
                        )

            # Check for surplus (scanned assets not in snapshot)
            scanned_asset_ids = set(scans.keys())
            snapshot_asset_ids = {s.asset_id for s in snapshots}
            surplus_asset_ids = scanned_asset_ids - snapshot_asset_ids

            for asset_id in surplus_asset_ids:
                scan = scans[asset_id]
                differences_to_create.append(
                    self._create_surplus_difference(task, scan)
                )

            # Create all differences
            if differences_to_create:
                InventoryDifference.objects.bulk_create(differences_to_create)

            return list(InventoryDifference.objects.filter(
                task_id=task_id,
                is_deleted=False
            ))

    def _create_missing_difference(self, snapshot: InventorySnapshot) -> InventoryDifference:
        """Create a missing asset difference record."""
        return InventoryDifference(
            id=uuid.uuid4(),
            task_id=snapshot.task_id,
            asset_id=snapshot.asset_id,
            difference_type=InventoryDifference.TYPE_MISSING,
            description=_("Asset not scanned during inventory"),
            expected_quantity=1,
            actual_quantity=0,
            quantity_difference=-1,
            expected_location=snapshot.location_name or '',
            actual_location='',
            expected_custodian=snapshot.custodian_name or '',
            actual_custodian='',
            status=InventoryDifference.STATUS_PENDING,
            organization_id=snapshot.organization_id,
        )

    def _create_location_difference(
        self,
        snapshot: InventorySnapshot,
        scan: InventoryScan
    ) -> InventoryDifference:
        """Create a location change difference record."""
        return InventoryDifference(
            id=uuid.uuid4(),
            task_id=snapshot.task_id,
            asset_id=snapshot.asset_id,
            difference_type=InventoryDifference.TYPE_LOCATION_MISMATCH,
            description=_("Asset location changed from {expected} to {actual}").format(
                expected=snapshot.location_name or '',
                actual=scan.actual_location_name or ''
            ),
            expected_location=snapshot.location_name or '',
            actual_location=scan.actual_location_name or '',
            expected_custodian=snapshot.custodian_name or '',
            actual_custodian=scan.actual_custodian_name or '',
            status=InventoryDifference.STATUS_PENDING,
            organization_id=snapshot.organization_id,
        )

    def _create_custodian_difference(
        self,
        snapshot: InventorySnapshot,
        scan: InventoryScan
    ) -> InventoryDifference:
        """Create a custodian change difference record."""
        return InventoryDifference(
            id=uuid.uuid4(),
            task_id=snapshot.task_id,
            asset_id=snapshot.asset_id,
            difference_type=InventoryDifference.TYPE_CUSTODIAN_MISMATCH,
            description=_("Asset custodian changed from {expected} to {actual}").format(
                expected=snapshot.custodian_name or '',
                actual=scan.actual_custodian_name or ''
            ),
            expected_location=snapshot.location_name or '',
            actual_location=scan.actual_location_name or '',
            expected_custodian=snapshot.custodian_name or '',
            actual_custodian=scan.actual_custodian_name or '',
            status=InventoryDifference.STATUS_PENDING,
            organization_id=snapshot.organization_id,
        )

    def _create_damaged_difference(
        self,
        snapshot: InventorySnapshot,
        scan: InventoryScan
    ) -> InventoryDifference:
        """Create a damaged asset difference record."""
        return InventoryDifference(
            id=uuid.uuid4(),
            task_id=snapshot.task_id,
            asset_id=snapshot.asset_id,
            difference_type=InventoryDifference.TYPE_DAMAGED,
            description=_("Asset reported as damaged"),
            expected_quantity=1,
            actual_quantity=1,
            quantity_difference=0,
            expected_location=snapshot.location_name or '',
            actual_location=scan.actual_location_name or '',
            expected_custodian=snapshot.custodian_name or '',
            actual_custodian=scan.actual_custodian_name or '',
            status=InventoryDifference.STATUS_PENDING,
            organization_id=snapshot.organization_id,
        )

    def _create_surplus_difference(self, task: InventoryTask, scan: InventoryScan) -> InventoryDifference:
        """Create a surplus asset difference record."""
        return InventoryDifference(
            id=uuid.uuid4(),
            task_id=task.id,
            asset_id=scan.asset_id,
            difference_type=InventoryDifference.TYPE_SURPLUS,
            description=_("Asset scanned but not in inventory snapshot"),
            expected_quantity=0,
            actual_quantity=1,
            quantity_difference=1,
            expected_location='',
            actual_location=scan.actual_location_name or '',
            expected_custodian='',
            actual_custodian=scan.actual_custodian_name or '',
            status=InventoryDifference.STATUS_PENDING,
            organization_id=task.organization_id,
        )

    def _has_location_changed(self, snapshot: InventorySnapshot, scan: InventoryScan) -> bool:
        """Check if location has changed."""
        return (
            scan.actual_location_name and
            scan.actual_location_name != snapshot.location_name
        )

    def _has_custodian_changed(self, snapshot: InventorySnapshot, scan: InventoryScan) -> bool:
        """Check if custodian has changed."""
        return (
            scan.actual_custodian_name and
            scan.actual_custodian_name != snapshot.custodian_name
        )

    def resolve_difference(
        self,
        difference_id: str,
        user_id: str,
        status: str,
        resolution: Optional[str] = None
    ) -> InventoryDifference:
        """
        Resolve a difference.

        Args:
            difference_id: Difference ID
            user_id: User ID resolving the difference
            status: New status (resolved or ignored)
            resolution: Optional resolution description

        Returns:
            Updated InventoryDifference instance
        """
        diff = self.get(difference_id)

        if diff.status not in self.ACTIVE_STATUSES:
            raise ValidationError(_("Difference is not in an active status."))

        if status not in [InventoryDifference.STATUS_RESOLVED, InventoryDifference.STATUS_IGNORED]:
            raise ValidationError(_("Invalid status value."))

        with transaction.atomic():
            diff.status = status
            diff.resolution = resolution or diff.resolution or ''
            diff.resolved_by_id = user_id
            diff.resolved_at = timezone.now()
            if status == InventoryDifference.STATUS_IGNORED and not diff.closure_type:
                diff.closure_type = InventoryDifference.CLOSURE_TYPE_INVALID
            diff.save(
                update_fields=[
                    'status',
                    'resolution',
                    'resolved_by',
                    'resolved_at',
                    'closure_type',
                ]
            )

            # Optionally sync asset data based on resolution
            if status == InventoryDifference.STATUS_RESOLVED:
                self._sync_asset_from_difference(diff)

        return diff

    def confirm_difference(
        self,
        difference_id: str,
        user_id: str,
        owner_id: Optional[str] = None,
    ) -> InventoryDifference:
        """Confirm a new difference and optionally assign the initial owner."""
        diff = self._get_transition_difference(
            difference_id,
            allowed_statuses=[InventoryDifference.STATUS_PENDING],
            action_label=_('confirm'),
        )
        diff.status = InventoryDifference.STATUS_CONFIRMED
        if owner_id:
            diff.owner_id = owner_id
        diff.save(update_fields=['status', 'owner'])
        return diff

    def assign_owner(
        self,
        difference_id: str,
        owner_id: str,
    ) -> InventoryDifference:
        """Assign or update the owner of a difference."""
        diff = self._get_transition_difference(
            difference_id,
            allowed_statuses=self.ACTIVE_STATUSES + self.CLOSEABLE_STATUSES,
            action_label=_('assign owner'),
        )
        if diff.status == InventoryDifference.STATUS_CLOSED:
            raise ValidationError(_("Closed differences cannot be reassigned."))
        diff.owner_id = owner_id
        diff.save(update_fields=['owner'])
        return diff

    def submit_review(
        self,
        difference_id: str,
        user_id: str,
        resolution: Optional[str] = None,
        closure_type: Optional[str] = None,
        linked_action_code: Optional[str] = None,
        evidence_refs: Optional[List[str]] = None,
    ) -> InventoryDifference:
        """Submit a confirmed difference for review."""
        diff = self._get_transition_difference(
            difference_id,
            allowed_statuses=[
                InventoryDifference.STATUS_PENDING,
                InventoryDifference.STATUS_CONFIRMED,
            ],
            action_label=_('submit review'),
        )
        next_resolution = (resolution if resolution is not None else diff.resolution or '').strip()
        if not next_resolution:
            raise ValidationError(_("Resolution is required before submitting review."))

        if closure_type:
            self._validate_closure_type(closure_type)

        diff.status = InventoryDifference.STATUS_IN_REVIEW
        diff.resolution = next_resolution
        diff.reviewed_by_id = user_id
        diff.reviewed_at = timezone.now()
        if closure_type:
            diff.closure_type = closure_type
        if linked_action_code is not None:
            diff.linked_action_code = linked_action_code.strip()
        if evidence_refs is not None:
            diff.evidence_refs = self._normalize_evidence_refs(evidence_refs)
        diff.save(
            update_fields=[
                'status',
                'resolution',
                'reviewed_by',
                'reviewed_at',
                'closure_type',
                'linked_action_code',
                'evidence_refs',
            ]
        )
        return diff

    def save_draft(
        self,
        difference_id: str,
        *,
        resolution: Optional[str] = None,
        closure_type: Optional[str] = None,
        linked_action_code: Optional[str] = None,
        evidence_refs: Optional[List[str]] = None,
        closure_notes: Optional[str] = None,
    ) -> InventoryDifference:
        """Save editable handling fields without changing the difference status."""
        diff = self._get_transition_difference(
            difference_id,
            allowed_statuses=self.DRAFTABLE_STATUSES,
            action_label=_('save draft'),
        )

        update_fields: List[str] = []
        if resolution is not None:
            diff.resolution = resolution.strip()
            update_fields.append('resolution')
        if closure_type is not None:
            normalized_closure_type = closure_type.strip()
            if normalized_closure_type:
                self._validate_closure_type(normalized_closure_type)
            diff.closure_type = normalized_closure_type
            update_fields.append('closure_type')
        if linked_action_code is not None:
            normalized_linked_action_code = linked_action_code.strip()
            if normalized_linked_action_code != str(diff.linked_action_code or '').strip():
                self._clear_linked_action_execution(diff)
                update_fields.append('custom_fields')
            diff.linked_action_code = normalized_linked_action_code
            update_fields.append('linked_action_code')
        if evidence_refs is not None:
            diff.evidence_refs = self._normalize_evidence_refs(evidence_refs)
            update_fields.append('evidence_refs')
        if closure_notes is not None:
            diff.closure_notes = closure_notes.strip()
            update_fields.append('closure_notes')

        if update_fields:
            diff.save(update_fields=update_fields)

        return diff

    def approve_resolution(
        self,
        difference_id: str,
        user_id: str,
        closure_notes: Optional[str] = None,
    ) -> InventoryDifference:
        """Approve a difference resolution and move it to execution."""
        diff = self._get_transition_difference(
            difference_id,
            allowed_statuses=[InventoryDifference.STATUS_IN_REVIEW],
            action_label=_('approve'),
        )
        diff.status = InventoryDifference.STATUS_APPROVED
        diff.approved_by_id = user_id
        diff.approved_at = timezone.now()
        if closure_notes is not None:
            diff.closure_notes = closure_notes
        diff.save(update_fields=['status', 'approved_by', 'approved_at', 'closure_notes'])
        return diff

    def reject_resolution(
        self,
        difference_id: str,
        closure_notes: Optional[str] = None,
    ) -> InventoryDifference:
        """Reject a submitted resolution and return the difference to confirmed state."""
        diff = self._get_transition_difference(
            difference_id,
            allowed_statuses=[InventoryDifference.STATUS_IN_REVIEW],
            action_label=_('reject'),
        )
        diff.status = InventoryDifference.STATUS_CONFIRMED
        if closure_notes is not None:
            diff.closure_notes = closure_notes
        diff.save(update_fields=['status', 'closure_notes'])
        return diff

    def execute_resolution(
        self,
        difference_id: str,
        user_id: str,
        resolution: Optional[str] = None,
        sync_asset: bool = True,
        linked_action_code: Optional[str] = None,
    ) -> InventoryDifference:
        """Execute an approved resolution and mark the difference as resolved."""
        diff = self._get_transition_difference(
            difference_id,
            allowed_statuses=self.EXECUTABLE_STATUSES,
            action_label=_('execute'),
        )
        next_resolution = (resolution if resolution is not None else diff.resolution or '').strip()
        if not next_resolution:
            raise ValidationError(_("Resolution is required before execution."))

        with transaction.atomic():
            diff.status = InventoryDifference.STATUS_EXECUTING
            diff.resolution = next_resolution
            if linked_action_code is not None:
                diff.linked_action_code = linked_action_code.strip()
            diff.save(update_fields=['status', 'resolution', 'linked_action_code'])

            if sync_asset:
                self._sync_asset_from_difference(diff)

            linked_action_execution = self._execute_linked_action(
                diff=diff,
                user_id=user_id,
                sync_asset=sync_asset,
            )

            diff.status = InventoryDifference.STATUS_RESOLVED
            diff.resolved_by_id = user_id
            diff.resolved_at = timezone.now()
            if linked_action_execution:
                self._store_linked_action_execution(diff, linked_action_execution)
            diff.save(update_fields=['status', 'resolved_by', 'resolved_at', 'custom_fields'])

        return diff

    def ignore_difference(
        self,
        difference_id: str,
        user_id: str,
        resolution: Optional[str] = None,
        closure_notes: Optional[str] = None,
    ) -> InventoryDifference:
        """Mark a difference as ignored without syncing asset data."""
        diff = self.resolve_difference(
            difference_id=difference_id,
            user_id=user_id,
            status=InventoryDifference.STATUS_IGNORED,
            resolution=resolution,
        )
        if closure_notes is not None:
            diff.closure_notes = closure_notes
            diff.save(update_fields=['closure_notes'])
        return diff

    def close_difference(
        self,
        difference_id: str,
        user_id: str,
        closure_notes: Optional[str] = None,
        evidence_refs: Optional[List[str]] = None,
    ) -> InventoryDifference:
        """Close a resolved or ignored difference."""
        diff = self._get_transition_difference(
            difference_id,
            allowed_statuses=self.CLOSEABLE_STATUSES,
            action_label=_('close'),
        )
        open_follow_up = self.follow_up_service.get_open_for_difference(str(diff.id))
        if open_follow_up is not None:
            raise ValidationError(_("Manual follow-up must be completed before closing the difference."))
        diff.status = InventoryDifference.STATUS_CLOSED
        diff.closed_by_id = user_id
        diff.closure_completed_at = timezone.now()
        if closure_notes is not None:
            diff.closure_notes = closure_notes
        if evidence_refs is not None:
            diff.evidence_refs = self._normalize_evidence_refs(evidence_refs)
        diff.save(
            update_fields=[
                'status',
                'closed_by',
                'closure_completed_at',
                'closure_notes',
                'evidence_refs',
            ]
        )
        return diff

    def send_follow_up(
        self,
        difference_id: str,
        user_id: str,
    ) -> InventoryDifference:
        """Send or resend a manual follow-up inbox notification for a difference."""
        diff = self.get(difference_id)
        execution_state = {}
        if isinstance(diff.custom_fields, dict):
            execution_state = diff.custom_fields.get('linked_action_execution') or {}
        if not isinstance(execution_state, dict) or execution_state.get('status') != 'manual_follow_up':
            raise ValidationError(_("Current difference does not require manual follow-up."))

        updated_execution = self._append_manual_follow_up_notification(
            diff=diff,
            user_id=user_id,
            action_code=str(execution_state.get('action_code') or diff.linked_action_code or '').strip(),
            execution_state=execution_state,
            is_reminder=True,
        )
        self._store_linked_action_execution(diff, updated_execution)
        diff.save(update_fields=['custom_fields'])
        return diff

    def complete_follow_up(
        self,
        *,
        difference_id: str,
        user_id: str,
        completion_notes: Optional[str] = None,
        evidence_refs: Optional[List[str]] = None,
    ) -> InventoryDifference:
        """Complete the open manual follow-up task for a difference."""
        diff = self.get(difference_id)
        follow_up_task = self.follow_up_service.get_open_for_difference(str(diff.id))
        if follow_up_task is None:
            raise ValidationError(_("Current difference does not have an open manual follow-up task."))

        completed_task = self.follow_up_service.complete_follow_up(
            follow_up_id=str(follow_up_task.id),
            user_id=user_id,
            completion_notes=str(completion_notes or '').strip(),
            evidence_refs=self._normalize_evidence_refs(evidence_refs) if evidence_refs is not None else None,
        )
        execution_state = self._build_follow_up_execution_state(
            diff=diff,
            base_execution=self._get_execution_state(diff),
            follow_up_task=completed_task,
            can_send_follow_up=False,
            message_suffix=str(_('Manual follow-up completed.')),
        )
        self._store_linked_action_execution(diff, execution_state)
        diff.save(update_fields=['custom_fields'])
        return diff

    def reopen_follow_up(
        self,
        *,
        difference_id: str,
        user_id: str,
    ) -> InventoryDifference:
        """Reopen the latest manual follow-up task for a difference."""
        diff = self.get(difference_id)
        follow_up_task = self.follow_up_service.get_latest_for_difference(str(diff.id))
        if follow_up_task is None:
            raise ValidationError(_("Current difference does not have a manual follow-up task."))

        reopened_task = self.follow_up_service.reopen_follow_up(
            follow_up_id=str(follow_up_task.id),
            user_id=user_id,
        )
        execution_state = self._build_follow_up_execution_state(
            diff=diff,
            base_execution=self._get_execution_state(diff),
            follow_up_task=reopened_task,
            can_send_follow_up=True,
            message_suffix=str(_('Manual follow-up reopened.')),
        )
        self._store_linked_action_execution(diff, execution_state)
        diff.save(update_fields=['custom_fields'])
        return diff

    def batch_resolve_differences(
        self,
        difference_ids: List[str],
        user_id: str,
        status: str,
        resolution: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Batch resolve differences.

        Args:
            difference_ids: List of difference IDs
            user_id: User ID resolving the differences
            status: New status (resolved or ignored)
            resolution: Optional resolution description

        Returns:
            Dictionary with results summary
        """
        results = {
            'total': len(difference_ids),
            'succeeded': 0,
            'failed': 0,
            'errors': []
        }

        for diff_id in difference_ids:
            try:
                self.resolve_difference(diff_id, user_id, status, resolution)
                results['succeeded'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'difference_id': diff_id,
                    'error': str(e)
                })

        return results

    def _get_transition_difference(
        self,
        difference_id: str,
        *,
        allowed_statuses: List[str],
        action_label: str,
    ) -> InventoryDifference:
        diff = self.get(difference_id)
        if diff.status not in allowed_statuses:
            raise ValidationError(
                _("Difference cannot {action} from status \"{status}\".").format(
                    action=action_label,
                    status=diff.status,
                )
            )
        return diff

    def _validate_closure_type(self, closure_type: str) -> None:
        allowed_types = {choice for choice, _label in InventoryDifference.CLOSURE_TYPE_CHOICES}
        if closure_type not in allowed_types:
            raise ValidationError(_("Invalid closure type value."))

    def _store_linked_action_execution(
        self,
        diff: InventoryDifference,
        execution_state: Dict[str, Any],
    ) -> None:
        custom_fields = dict(diff.custom_fields or {})
        custom_fields['linked_action_execution'] = execution_state
        diff.custom_fields = custom_fields

    def _clear_linked_action_execution(self, diff: InventoryDifference) -> None:
        custom_fields = dict(diff.custom_fields or {})
        custom_fields.pop('linked_action_execution', None)
        diff.custom_fields = custom_fields
        self.follow_up_service.cancel_follow_ups_for_difference(difference_id=str(diff.id))

    def _execute_linked_action(
        self,
        *,
        diff: InventoryDifference,
        user_id: str,
        sync_asset: bool,
    ) -> Dict[str, Any]:
        action_code = str(diff.linked_action_code or '').strip()
        if not action_code:
            return {}

        executed_at = timezone.now().isoformat()

        if action_code in {
            InventoryDifference.CLOSURE_TYPE_LOCATION_CORRECTION,
            InventoryDifference.CLOSURE_TYPE_CUSTODIAN_CORRECTION,
        }:
            if not sync_asset:
                raise ValidationError(_("Selected linked action requires asset sync to remain enabled."))
            if not diff.asset_id:
                raise ValidationError(_("Selected linked action requires a related asset."))
            return {
                'action_code': action_code,
                'status': 'executed',
                'target_object_code': 'Asset',
                'target_id': str(diff.asset_id),
                'target_url': f'/objects/Asset/{diff.asset_id}',
                'message': str(_('Asset correction applied successfully.')),
                'executed_at': executed_at,
            }

        automated_asset_actions = {'asset.create_maintenance', 'asset.create_disposal'}
        if action_code in automated_asset_actions:
            user = self._get_execution_user(user_id)
            asset = self._get_linked_action_asset(diff)

            from apps.lifecycle.services.lifecycle_action_service import LifecycleActionService

            action_result = LifecycleActionService().execute_action(
                object_code='Asset',
                action_code=action_code,
                instance=asset,
                user=user,
                payload={},
            )
            return {
                'action_code': action_code,
                'status': 'executed',
                'target_object_code': str(
                    action_result.get('target_object_code') or action_result.get('targetObjectCode') or ''
                ),
                'target_id': str(action_result.get('target_id') or action_result.get('targetId') or ''),
                'target_url': str(action_result.get('target_url') or action_result.get('targetUrl') or ''),
                'message': str(action_result.get('message') or '').strip(),
                'executed_at': executed_at,
            }

        manual_messages = {
            InventoryDifference.CLOSURE_TYPE_CREATE_CARD: str(
                _('Linked action recorded for manual asset card creation follow-up.')
            ),
            InventoryDifference.CLOSURE_TYPE_FINANCIAL_ADJUSTMENT: str(
                _('Linked action recorded for manual financial adjustment follow-up.')
            ),
            InventoryDifference.CLOSURE_TYPE_INVALID: str(
                _('No automated downstream action is required for an invalid difference.')
            ),
        }
        return self._append_manual_follow_up_notification(
            diff=diff,
            user_id=user_id,
            action_code=action_code,
            execution_state={
                'action_code': action_code,
                'status': 'manual_follow_up',
                'message': manual_messages.get(
                    action_code,
                    str(_('Linked action recorded for manual follow-up.')),
                ),
                'executed_at': executed_at,
            },
            is_reminder=False,
        )

    def _append_manual_follow_up_notification(
        self,
        *,
        diff: InventoryDifference,
        user_id: str,
        action_code: str,
        execution_state: Optional[Dict[str, Any]] = None,
        is_reminder: bool,
    ) -> Dict[str, Any]:
        state = dict(execution_state or {})
        state['action_code'] = action_code
        state['status'] = 'manual_follow_up'
        state['executed_at'] = str(state.get('executed_at') or timezone.now().isoformat())

        requires_follow_up = self._manual_follow_up_requires_notification(action_code)
        state['can_send_follow_up'] = requires_follow_up

        if not requires_follow_up:
            return state

        sender = self._get_execution_user(user_id)
        recipient = self._get_manual_follow_up_recipient(diff, sender)
        notification = self._create_manual_follow_up_notification(
            diff=diff,
            sender=sender,
            recipient=recipient,
            action_code=action_code,
        )

        assignee_name = self._get_user_display_name(recipient)
        follow_up_count = int(state.get('follow_up_sent_count') or 0) + 1
        notified_at = timezone.now().isoformat()
        follow_up_message = (
            _('Follow-up reminder sent to {assignee}.')
            if is_reminder
            else _('Follow-up assigned to {assignee}.')
        )

        state.update({
            'follow_up_assignee_id': str(recipient.id),
            'follow_up_assignee_name': assignee_name,
            'follow_up_notification_id': str(notification.id),
            'follow_up_notification_url': '/notifications/center',
            'follow_up_last_sent_at': notified_at,
            'follow_up_sent_count': follow_up_count,
        })
        state['message'] = (
            f"{state.get('message', '').strip()} "
            f"{str(follow_up_message).format(assignee=assignee_name)}"
        ).strip()
        follow_up_task = self.follow_up_service.ensure_follow_up_task(
            diff=diff,
            sender=sender,
            assignee=recipient,
            action_code=action_code,
            reminder_count=follow_up_count,
            notification_id=str(notification.id),
            notification_url='/notifications/center',
            last_notified_at=timezone.now(),
        )
        return self._build_follow_up_execution_state(
            diff=diff,
            base_execution=state,
            follow_up_task=follow_up_task,
            can_send_follow_up=requires_follow_up,
        )

    @staticmethod
    def _manual_follow_up_requires_notification(action_code: str) -> bool:
        return action_code != InventoryDifference.CLOSURE_TYPE_INVALID

    def _get_manual_follow_up_recipient(self, diff: InventoryDifference, sender: User) -> User:
        owner = getattr(diff, 'owner', None)
        if owner is not None:
            return owner
        created_by = getattr(diff, 'created_by', None)
        if created_by is not None:
            return created_by
        return sender

    def _create_manual_follow_up_notification(
        self,
        *,
        diff: InventoryDifference,
        sender: User,
        recipient: User,
        action_code: str,
    ) -> Notification:
        title = str(
            _('Inventory difference follow-up required: {task_code}').format(
                task_code=getattr(getattr(diff, 'task', None), 'task_code', '') or str(diff.id),
            )
        )
        action_label = str(diff.get_closure_type_display() or action_code or _('Manual follow-up'))
        content = str(
            _('Difference "{difference_type}" requires manual follow-up for "{action_label}".').format(
                difference_type=str(diff.get_difference_type_display()),
                action_label=action_label,
            )
        )
        variables = {
            'title': title,
            'content': content,
            'actionUrl': f'/objects/InventoryItem/{diff.id}',
            'objectCode': 'InventoryItem',
            'objectId': str(diff.id),
            'differenceId': str(diff.id),
            'taskCode': getattr(getattr(diff, 'task', None), 'task_code', ''),
            'differenceType': str(diff.get_difference_type_display()),
            'linkedActionCode': action_code,
            'closureType': diff.closure_type,
            'assigneeName': self._get_user_display_name(recipient),
        }

        notification = None
        try:
            result = notification_service.send(
                recipient=recipient,
                notification_type=self.MANUAL_FOLLOW_UP_NOTIFICATION_TYPE,
                variables=variables,
                channels=['inbox'],
                priority='high',
                sender=sender,
            )
            result_items = result.get('results', []) if isinstance(result, dict) else []
            notification_id = None
            if result_items and isinstance(result_items[0], dict):
                notification_id = result_items[0].get('notification_id')
            if notification_id:
                notification = Notification.all_objects.filter(id=notification_id, is_deleted=False).first()
            if notification is not None:
                update_fields = []
                if diff.organization_id and notification.organization_id != diff.organization_id:
                    notification.organization_id = diff.organization_id
                    update_fields.append('organization')
                if sender.id and notification.created_by_id != sender.id:
                    notification.created_by_id = sender.id
                    update_fields.append('created_by')
                if notification.title != title:
                    notification.title = title
                    update_fields.append('title')
                if notification.content != content:
                    notification.content = content
                    update_fields.append('content')
                expected_data = dict(notification.data or {})
                expected_data.update({
                    'variables': variables,
                    'objectCode': 'InventoryItem',
                    'objectId': str(diff.id),
                    'actionUrl': f'/objects/InventoryItem/{diff.id}',
                })
                if notification.data != expected_data:
                    notification.data = expected_data
                    update_fields.append('data')
                if update_fields:
                    update_fields.append('updated_at')
                    notification.save(update_fields=update_fields)
        except Exception:
            notification = None

        if notification is not None:
            return notification

        return Notification.objects.create(
            organization_id=diff.organization_id,
            recipient=recipient,
            notification_type=self.MANUAL_FOLLOW_UP_NOTIFICATION_TYPE,
            priority='high',
            channel='inbox',
            title=title,
            content=content,
            data=variables,
            status='success',
            sent_at=timezone.now(),
            created_by=sender,
            sender=sender,
        )

    @staticmethod
    def _get_user_display_name(user: User) -> str:
        full_name = str(getattr(user, 'get_full_name', lambda: '')() or '').strip()
        return full_name or str(getattr(user, 'username', '') or getattr(user, 'email', '') or user.id)

    @staticmethod
    def _get_execution_user(user_id: str) -> User:
        user = User.all_objects.filter(id=user_id).first()
        if user is None:
            raise ValidationError(_("Execution user does not exist."))
        return user

    @staticmethod
    def _get_execution_state(diff: InventoryDifference) -> Dict[str, Any]:
        if isinstance(diff.custom_fields, dict):
            execution_state = diff.custom_fields.get('linked_action_execution') or {}
            if isinstance(execution_state, dict):
                return dict(execution_state)
        return {}

    def _build_follow_up_execution_state(
        self,
        *,
        diff: InventoryDifference,
        base_execution: Optional[Dict[str, Any]],
        follow_up_task: InventoryFollowUp,
        can_send_follow_up: bool,
        message_suffix: str = '',
    ) -> Dict[str, Any]:
        state = dict(base_execution or {})
        state.update({
            'status': 'manual_follow_up',
            'can_send_follow_up': can_send_follow_up,
            'follow_up_task_id': str(follow_up_task.id),
            'follow_up_task_code': follow_up_task.follow_up_code,
            'follow_up_task_status': follow_up_task.status,
            'follow_up_task_url': self.follow_up_service.build_task_route(follow_up_task),
            'follow_up_completed_at': follow_up_task.completed_at.isoformat() if follow_up_task.completed_at else '',
        })
        if message_suffix:
            state['message'] = f"{str(state.get('message') or '').strip()} {message_suffix}".strip()
        return state

    @staticmethod
    def _get_linked_action_asset(diff: InventoryDifference) -> Asset:
        asset = getattr(diff, 'asset', None)
        if asset is None:
            raise ValidationError(_("Selected linked action requires a related asset."))
        return asset

    @staticmethod
    def _normalize_evidence_refs(evidence_refs: Optional[List[str]]) -> List[str]:
        if not evidence_refs:
            return []
        normalized_refs = []
        for item in evidence_refs:
            value = str(item or '').strip()
            if value:
                normalized_refs.append(value)
        return normalized_refs

    def _sync_asset_from_difference(self, diff: InventoryDifference) -> None:
        """
        Sync asset data based on resolved difference.

        Args:
            diff: InventoryDifference instance
        """
        try:
            asset = Asset.objects.get(id=diff.asset_id, is_deleted=False)

            # Sync location for location changes
            if diff.difference_type == InventoryDifference.TYPE_LOCATION_MISMATCH:
                from apps.assets.models import Location
                location_id = getattr(diff, 'actual_location_id', '') or ''
                actual_location_name = str(diff.actual_location or '').strip()
                try:
                    if location_id:
                        asset.location = Location.objects.get(id=location_id)
                    elif actual_location_name:
                        asset.location = Location.objects.get(
                            name=actual_location_name,
                            organization_id=diff.organization_id,
                            is_deleted=False,
                        )
                except Location.DoesNotExist:
                    pass

            # Sync custodian for custodian changes
            if diff.difference_type == InventoryDifference.TYPE_CUSTODIAN_MISMATCH:
                from apps.accounts.models import User
                custodian_id = getattr(diff, 'actual_custodian_id', '') or ''
                actual_custodian_name = str(diff.actual_custodian or '').strip()
                try:
                    if custodian_id:
                        asset.custodian = User.objects.get(id=custodian_id, is_deleted=False)
                    elif actual_custodian_name:
                        asset.custodian = User.objects.filter(
                            organization_id=diff.organization_id,
                            is_deleted=False,
                        ).filter(
                            username=actual_custodian_name,
                        ).first() or User.objects.filter(
                            organization_id=diff.organization_id,
                            is_deleted=False,
                            first_name=actual_custodian_name,
                        ).first() or asset.custodian
                except User.DoesNotExist:
                    pass

            # Update status for damaged assets
            if diff.difference_type == InventoryDifference.TYPE_DAMAGED:
                asset.status = 'damaged'

            asset.save()

        except Asset.DoesNotExist:
            # Asset might have been deleted
            pass

    def get_difference_summary(self, task_id: str) -> Dict[str, Any]:
        """
        Get summary of differences for a task.

        Args:
            task_id: Task ID

        Returns:
            Dictionary with difference summary
        """
        differences = InventoryDifference.objects.filter(
            task_id=task_id,
            is_deleted=False
        )

        total = differences.count()
        status_counts = {
            status_code: differences.filter(status=status_code).count()
            for status_code, _label in InventoryDifference.RESOLUTION_STATUS_CHOICES
        }
        type_counts = {
            diff_type: differences.filter(difference_type=diff_type).count()
            for diff_type, _label in InventoryDifference.DIFFERENCE_TYPE_CHOICES
        }
        pending_confirmation_count = status_counts.get(InventoryDifference.STATUS_PENDING, 0)
        pending_review_count = status_counts.get(InventoryDifference.STATUS_CONFIRMED, 0)
        pending_approval_count = status_counts.get(InventoryDifference.STATUS_IN_REVIEW, 0)
        pending_execution_count = status_counts.get(InventoryDifference.STATUS_APPROVED, 0)
        executing_count = status_counts.get(InventoryDifference.STATUS_EXECUTING, 0)
        pending_closure_count = (
            status_counts.get(InventoryDifference.STATUS_RESOLVED, 0) +
            status_counts.get(InventoryDifference.STATUS_IGNORED, 0)
        )
        follow_up_task_difference_ids = set(
            InventoryFollowUp.all_objects.filter(
                task_id=task_id,
                is_deleted=False,
            ).values_list('difference_id', flat=True)
        )
        open_follow_up_difference_ids = set(
            InventoryFollowUp.all_objects.filter(
                task_id=task_id,
                is_deleted=False,
                status=InventoryFollowUp.STATUS_PENDING,
            ).values_list('difference_id', flat=True)
        )
        legacy_manual_follow_up_total_count = differences.filter(
            custom_fields__linked_action_execution__can_send_follow_up=True,
        ).exclude(
            id__in=follow_up_task_difference_ids,
        ).count()
        legacy_manual_follow_up_open_count = differences.filter(
            custom_fields__linked_action_execution__can_send_follow_up=True,
        ).exclude(
            status=InventoryDifference.STATUS_CLOSED,
        ).exclude(
            id__in=open_follow_up_difference_ids,
        ).count()
        manual_follow_up_total_count = len(follow_up_task_difference_ids) + legacy_manual_follow_up_total_count
        manual_follow_up_open_count = len(open_follow_up_difference_ids) + legacy_manual_follow_up_open_count
        active_count = (
            pending_confirmation_count +
            pending_review_count +
            pending_approval_count +
            pending_execution_count +
            executing_count
        )
        closed_count = status_counts.get(InventoryDifference.STATUS_CLOSED, 0)
        closure_progress = round((closed_count / total) * 100, 2) if total else 100

        closure_stage_label = _("No differences")
        closure_blocker = ''
        if total == 0:
            closure_stage_label = _("No differences")
        elif pending_confirmation_count > 0:
            closure_stage_label = _("Awaiting confirmation")
            closure_blocker = _("Some differences have not been confirmed.")
        elif pending_review_count > 0:
            closure_stage_label = _("Awaiting review submission")
            closure_blocker = _("Some confirmed differences still need review submission.")
        elif pending_approval_count > 0:
            closure_stage_label = _("Awaiting approval")
            closure_blocker = _("Some submitted differences still require approval.")
        elif pending_execution_count > 0 or executing_count > 0:
            closure_stage_label = _("Awaiting execution")
            closure_blocker = _("Approved differences still need execution or asset sync.")
        elif manual_follow_up_open_count > 0:
            closure_stage_label = _("Awaiting follow-up")
            closure_blocker = _("Manual downstream follow-up is still pending completion.")
        elif pending_closure_count > 0:
            closure_stage_label = _("Awaiting closure")
            closure_blocker = _("Resolved or ignored differences still need formal closure.")
        else:
            closure_stage_label = _("Closed")

        return {
            'task_id': task_id,
            'total_differences': total,
            'pending': status_counts.get(InventoryDifference.STATUS_PENDING, 0),
            'confirmed': status_counts.get(InventoryDifference.STATUS_CONFIRMED, 0),
            'in_review': status_counts.get(InventoryDifference.STATUS_IN_REVIEW, 0),
            'approved': status_counts.get(InventoryDifference.STATUS_APPROVED, 0),
            'executing': executing_count,
            'resolved': status_counts.get(InventoryDifference.STATUS_RESOLVED, 0),
            'ignored': status_counts.get(InventoryDifference.STATUS_IGNORED, 0),
            'closed': closed_count,
            'active_count': active_count,
            'pending_confirmation_count': pending_confirmation_count,
            'pending_review_count': pending_review_count,
            'pending_approval_count': pending_approval_count,
            'pending_execution_count': pending_execution_count,
            'pending_closure_count': pending_closure_count,
            'manual_follow_up_total_count': manual_follow_up_total_count,
            'manual_follow_up_open_count': manual_follow_up_open_count,
            'closure_progress': closure_progress,
            'closure_stage_label': str(closure_stage_label),
            'closure_blocker': str(closure_blocker),
            'by_type': type_counts,
        }

    def get_differences_by_type(
        self,
        task_id: str,
        difference_type: str
    ) -> List[InventoryDifference]:
        """
        Get differences filtered by type.

        Args:
            task_id: Task ID
            difference_type: Difference type filter

        Returns:
            List of InventoryDifference instances
        """
        return list(InventoryDifference.objects.filter(
            task_id=task_id,
            difference_type=difference_type,
            is_deleted=False
        ).select_related('asset', 'task', 'resolved_by', 'owner', 'reviewed_by', 'approved_by', 'closed_by'))

    def get_pending_differences(self, task_id: str) -> List[InventoryDifference]:
        """
        Get all pending differences for a task.

        Args:
            task_id: Task ID

        Returns:
            List of pending InventoryDifference instances
        """
        return list(InventoryDifference.objects.filter(
            task_id=task_id,
            status__in=self.ACTIVE_STATUSES,
            is_deleted=False
        ).select_related('asset', 'task', 'owner'))

    def delete_differences_for_task(self, task_id: str) -> int:
        """
        Soft delete all differences for a task.

        Args:
            task_id: Task ID

        Returns:
            Number of differences deleted
        """
        count = InventoryDifference.objects.filter(
            task_id=task_id,
            is_deleted=False
        ).update(is_deleted=True, deleted_at=timezone.now())

        return count
