"""Service helpers for inventory manual follow-up tasks."""

from __future__ import annotations

from typing import Optional

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from apps.common.services.base_crud import BaseCRUDService
from apps.inventory.models import InventoryDifference, InventoryFollowUp


class InventoryFollowUpService(BaseCRUDService):
    """Manage manual follow-up task lifecycle for inventory differences."""

    def __init__(self):
        super().__init__(InventoryFollowUp)

    def ensure_follow_up_task(
        self,
        *,
        diff: InventoryDifference,
        sender: User,
        assignee: User,
        action_code: str,
        reminder_count: int = 0,
        notification_id: str = '',
        notification_url: str = '',
        last_notified_at=None,
    ) -> InventoryFollowUp:
        """Create or refresh a pending follow-up task for a difference."""
        task = self.get_latest_for_difference(str(diff.id))
        now = timezone.now()
        if task is None:
            task = self.model_class.objects.create(
                organization_id=diff.organization_id,
                task_id=diff.task_id,
                difference_id=diff.id,
                asset_id=diff.asset_id,
                title=self._build_title(diff=diff, action_code=action_code),
                closure_type=diff.closure_type or '',
                linked_action_code=action_code or '',
                status=InventoryFollowUp.STATUS_PENDING,
                assignee_id=assignee.id if assignee else None,
                assigned_at=now if assignee else None,
                created_by=sender,
            )
        else:
            task.title = self._build_title(diff=diff, action_code=action_code)
            task.task_id = diff.task_id
            task.asset_id = diff.asset_id
            task.closure_type = diff.closure_type or ''
            task.linked_action_code = action_code or ''
            task.status = InventoryFollowUp.STATUS_PENDING
            task.assignee_id = assignee.id if assignee else None
            task.assigned_at = now if assignee else task.assigned_at or now
            task.completed_at = None
            task.completed_by = None
            update_fields = [
                'title',
                'task',
                'asset',
                'closure_type',
                'linked_action_code',
                'status',
                'assignee',
                'assigned_at',
                'completed_at',
                'completed_by',
                'updated_at',
            ]
            if sender and task.updated_by_id != sender.id:
                task.updated_by = sender
                update_fields.append('updated_by')
            task.save(update_fields=update_fields)

        notification_fields = []
        if reminder_count:
            task.reminder_count = reminder_count
            notification_fields.append('reminder_count')
        if notification_id:
            task.follow_up_notification_id = notification_id
            notification_fields.append('follow_up_notification_id')
        if notification_url:
            task.follow_up_notification_url = notification_url
            notification_fields.append('follow_up_notification_url')
        if last_notified_at:
            task.last_notified_at = last_notified_at
            notification_fields.append('last_notified_at')
        if notification_fields:
            if sender and task.updated_by_id != sender.id:
                task.updated_by = sender
                notification_fields.append('updated_by')
            notification_fields.append('updated_at')
            task.save(update_fields=notification_fields)
        return task

    def complete_follow_up(
        self,
        *,
        follow_up_id: str,
        user_id: str,
        completion_notes: str = '',
        evidence_refs: Optional[list[str]] = None,
    ) -> InventoryFollowUp:
        """Mark a follow-up task as completed."""
        task = self.get(follow_up_id, allow_deleted=False)
        if task.status == InventoryFollowUp.STATUS_CANCELLED:
            raise ValidationError(_('Cancelled follow-up tasks cannot be completed.'))
        if task.status == InventoryFollowUp.STATUS_COMPLETED:
            return task

        user = self._get_user(user_id)
        task.status = InventoryFollowUp.STATUS_COMPLETED
        task.completed_at = timezone.now()
        task.completed_by = user
        task.completion_notes = str(completion_notes or '').strip()
        if evidence_refs is not None:
            task.evidence_refs = list(evidence_refs)
        task.updated_by = user
        task.save(update_fields=[
            'status',
            'completed_at',
            'completed_by',
            'completion_notes',
            'evidence_refs',
            'updated_by',
            'updated_at',
        ])
        return task

    def reopen_follow_up(self, *, follow_up_id: str, user_id: str) -> InventoryFollowUp:
        """Reopen a completed or cancelled follow-up task."""
        task = self.get(follow_up_id, allow_deleted=False)
        user = self._get_user(user_id)
        task.status = InventoryFollowUp.STATUS_PENDING
        task.completed_at = None
        task.completed_by = None
        task.updated_by = user
        task.save(update_fields=[
            'status',
            'completed_at',
            'completed_by',
            'updated_by',
            'updated_at',
        ])
        return task

    def cancel_follow_ups_for_difference(self, *, difference_id: str, user_id: Optional[str] = None) -> int:
        """Cancel all open follow-up tasks for a difference."""
        queryset = self.model_class.objects.filter(
            difference_id=difference_id,
            is_deleted=False,
            status=InventoryFollowUp.STATUS_PENDING,
        )
        if not queryset.exists():
            return 0

        update_kwargs = {
            'status': InventoryFollowUp.STATUS_CANCELLED,
            'updated_at': timezone.now(),
        }
        if user_id:
            user = self._get_user(user_id)
            update_kwargs['updated_by_id'] = user.id
        return queryset.update(**update_kwargs)

    def get_latest_for_difference(self, difference_id: str) -> Optional[InventoryFollowUp]:
        """Return the latest non-deleted follow-up task for a difference."""
        return self.model_class.objects.filter(
            difference_id=difference_id,
            is_deleted=False,
        ).order_by('-created_at').first()

    def get_open_for_difference(self, difference_id: str) -> Optional[InventoryFollowUp]:
        """Return the latest open follow-up task for a difference."""
        return self.model_class.objects.filter(
            difference_id=difference_id,
            is_deleted=False,
            status=InventoryFollowUp.STATUS_PENDING,
        ).order_by('-created_at').first()

    @staticmethod
    def build_task_route(task: InventoryFollowUp) -> str:
        """Build the dynamic route for a follow-up task."""
        return f"/objects/InventoryFollowUp/{task.id}"

    @staticmethod
    def _build_title(*, diff: InventoryDifference, action_code: str) -> str:
        action_label = str(diff.get_closure_type_display() or action_code or _('Manual follow-up'))
        difference_type = str(diff.get_difference_type_display() or _('Difference'))
        return str(
            _('Inventory difference "{difference_type}" requires {action_label} follow-up.').format(
                difference_type=difference_type,
                action_label=action_label,
            )
        )

    @staticmethod
    def _get_user(user_id: str) -> User:
        user = User.all_objects.filter(id=user_id).first()
        if user is None:
            raise ValidationError(_('Execution user does not exist.'))
        return user
