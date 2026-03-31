"""
Inventory task closure summary service.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from django.utils.translation import gettext_lazy as _

from apps.common.mixins.workflow_status import WorkflowStatusMixin
from apps.inventory.models import InventoryTask
from apps.inventory.services.difference_service import DifferenceService


class InventoryTaskClosureService:
    """Build a normalized closure payload for inventory task workbenches."""

    def __init__(self, difference_service: Optional[DifferenceService] = None):
        self.difference_service = difference_service or DifferenceService()

    def build_summary(self, task: InventoryTask) -> Dict[str, Any]:
        """Return a stable closure summary for a single inventory task."""
        owner = self._resolve_owner(task)
        difference_summary = (
            self.difference_service.get_difference_summary(str(task.id))
            if task.status == InventoryTask.STATUS_COMPLETED
            else None
        )

        stage = self._resolve_stage(task, difference_summary)
        blocker = self._resolve_blocker(task, difference_summary)
        completion = self._resolve_completion(task, difference_summary)

        return {
            'objectCode': 'InventoryTask',
            'businessId': str(task.id),
            'hasSummary': True,
            'status': task.status,
            'approvalStatus': getattr(task, 'approval_status', None),
            'workflowInstanceId': (
                str(task.workflow_instance_id)
                if getattr(task, 'workflow_instance_id', None)
                else None
            ),
            'owner': owner,
            'stage': stage,
            'blocker': blocker,
            'completion': completion,
            'completionDisplay': self._format_completion(completion),
            'metrics': {
                'progressPercentage': task.progress_percentage,
                'totalCount': int(task.total_count or 0),
                'scannedCount': int(task.scanned_count or 0),
                'differenceSummary': difference_summary or {},
            },
        }

    def _resolve_stage(
        self,
        task: InventoryTask,
        difference_summary: Optional[Dict[str, Any]],
    ) -> str:
        if task.status == InventoryTask.STATUS_CANCELLED:
            return str(_('Cancelled'))
        if task.approval_status == WorkflowStatusMixin.APPROVAL_REJECTED:
            return str(_('Approval rejected'))
        if task.status == InventoryTask.STATUS_PENDING_APPROVAL:
            return str(_('Awaiting approval'))
        if task.status == InventoryTask.STATUS_DRAFT:
            return str(_('Draft'))
        if task.status == InventoryTask.STATUS_PENDING:
            return str(_('Ready to start'))
        if task.status == InventoryTask.STATUS_IN_PROGRESS:
            return str(_('Inventory in progress'))
        if difference_summary:
            return str(difference_summary.get('closure_stage_label') or _('Closed'))
        return str(_('Closed'))

    def _resolve_blocker(
        self,
        task: InventoryTask,
        difference_summary: Optional[Dict[str, Any]],
    ) -> str:
        if task.status == InventoryTask.STATUS_CANCELLED:
            return str(_('Task was cancelled before closed-loop completion.'))
        if task.approval_status == WorkflowStatusMixin.APPROVAL_REJECTED:
            return str(_('Update the task and resubmit it for approval before execution can begin.'))
        if task.status == InventoryTask.STATUS_PENDING_APPROVAL:
            return str(_('Workflow approval is still pending.'))
        if task.status == InventoryTask.STATUS_DRAFT:
            return str(_('Submit the task for approval before execution can begin.'))
        if task.status == InventoryTask.STATUS_PENDING:
            return str(_('Inventory execution has not started yet.'))
        if task.status == InventoryTask.STATUS_IN_PROGRESS:
            return str(_('Complete the inventory round before exception closure can begin.'))
        if difference_summary:
            return str(difference_summary.get('closure_blocker') or '')
        return ''

    def _resolve_completion(
        self,
        task: InventoryTask,
        difference_summary: Optional[Dict[str, Any]],
    ) -> float:
        if task.status == InventoryTask.STATUS_COMPLETED and difference_summary is not None:
            return float(difference_summary.get('closure_progress') or 0)
        if task.status == InventoryTask.STATUS_IN_PROGRESS:
            return float(task.progress_percentage or 0)
        return 0.0

    def _resolve_owner(self, task: InventoryTask) -> str:
        primary_executor = (
            task.executors_relation.filter(is_deleted=False, is_primary=True)
            .select_related('executor')
            .first()
        )
        if primary_executor and primary_executor.executor:
            return str(
                primary_executor.executor.get_full_name()
                or primary_executor.executor.username
                or primary_executor.executor_id
            ).strip()

        creator = getattr(task, 'created_by', None)
        if creator is not None:
            return str(
                creator.get_full_name()
                or getattr(creator, 'username', '')
                or getattr(creator, 'id', '')
            ).strip()

        return ''

    @staticmethod
    def _format_completion(completion: float) -> str:
        normalized = round(float(completion or 0), 2)
        if normalized.is_integer():
            return f'{int(normalized)}%'
        return f'{normalized}%'
