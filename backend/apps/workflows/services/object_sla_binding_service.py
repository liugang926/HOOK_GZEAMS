"""
Object-level workflow SLA aggregation service.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, Iterable, Optional

from django.utils import timezone

from apps.workflows.models import WorkflowInstance, WorkflowTask
from apps.workflows.services.sla_service import SLAService


class ObjectSLABindingService:
    """Aggregate workflow SLA state for a business object record."""

    _STATUS_SEVERITY = {
        'escalated': 5,
        'overdue': 4,
        'approaching_sla': 3,
        'within_sla': 2,
        'completed': 1,
        'unknown': 0,
    }

    def __init__(self, sla_service: Optional[SLAService] = None):
        self.sla_service = sla_service or SLAService()

    def get_object_sla_summary(
        self,
        *,
        object_code: str,
        business_id: str,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return SLA summary for the latest workflow bound to the business record."""
        normalized_object_code = str(object_code or '').strip()
        normalized_business_id = str(business_id or '').strip()
        summary = self._build_empty_summary(
            object_code=normalized_object_code,
            business_id=normalized_business_id,
        )
        if not normalized_object_code or not normalized_business_id:
            return summary

        instance = self._get_target_instance(
            object_code=normalized_object_code,
            business_id=normalized_business_id,
            organization_id=organization_id,
        )
        if instance is None:
            return summary

        summary.update({
            'hasInstance': True,
            'instanceId': str(instance.id),
            'instanceNo': instance.instance_no,
            'instanceStatus': instance.status,
            'workflowName': getattr(instance.definition, 'name', '') or '',
            'currentNode': {
                'id': instance.current_node_id,
                'name': instance.current_node_name,
            },
        })

        active_tasks = list(self._get_active_tasks(instance))
        summary['activeTaskCount'] = len(active_tasks)

        if active_tasks:
            primary_task = self._select_primary_task(active_tasks)
            status_info = self.sla_service.get_task_sla_status(primary_task)
            summary.update({
                'status': status_info['status'],
                'dueDate': status_info['due_date'],
                'remainingHours': getattr(primary_task, 'remaining_hours', None),
                'hoursOverdue': status_info['hours_overdue'],
                'isEscalated': status_info['status'] == 'escalated',
                'activeTaskId': str(primary_task.id),
                'assignee': self._serialize_assignee(primary_task.assignee),
            })
            return summary

        if instance.status in WorkflowInstance.TERMINAL_STATUSES:
            summary.update({
                'status': 'completed',
                'completedAt': instance.completed_at or instance.updated_at,
            })
            return summary

        started_at = getattr(instance, 'started_at', None) or getattr(instance, 'created_at', None)
        if started_at:
            elapsed_hours = max((timezone.now() - started_at).total_seconds() / 3600, 0)
            hours_overdue = max(elapsed_hours - self.sla_service.DEFAULT_SLA_HOURS, 0)
            summary.update({
                'status': 'overdue' if hours_overdue > 0 else 'within_sla',
                'hoursOverdue': round(hours_overdue, 2),
                'remainingHours': round(max(self.sla_service.DEFAULT_SLA_HOURS - elapsed_hours, 0), 2),
            })

        return summary

    def _build_empty_summary(self, *, object_code: str, business_id: str) -> Dict[str, Any]:
        return {
            'objectCode': object_code,
            'businessId': business_id,
            'hasInstance': False,
            'instanceId': None,
            'instanceNo': None,
            'instanceStatus': None,
            'workflowName': '',
            'status': 'unknown',
            'dueDate': None,
            'remainingHours': None,
            'hoursOverdue': 0,
            'isEscalated': False,
            'assignee': None,
            'currentNode': None,
            'activeTaskId': None,
            'activeTaskCount': 0,
            'completedAt': None,
        }

    def _get_target_instance(
        self,
        *,
        object_code: str,
        business_id: str,
        organization_id: Optional[str],
    ) -> Optional[WorkflowInstance]:
        queryset = WorkflowInstance.objects.filter(
            is_deleted=False,
            business_object_code__iexact=object_code,
            business_id=business_id,
        ).select_related('definition')

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        active_instance = queryset.filter(
            status__in=WorkflowInstance.ACTIVE_STATUSES,
        ).order_by('-created_at').first()
        if active_instance is not None:
            return active_instance

        return queryset.order_by('-created_at').first()

    def _get_active_tasks(self, instance: WorkflowInstance) -> Iterable[WorkflowTask]:
        return WorkflowTask.objects.filter(
            is_deleted=False,
            instance=instance,
            status=WorkflowTask.STATUS_PENDING,
        ).select_related('assignee')

    def _select_primary_task(self, tasks: list[WorkflowTask]) -> WorkflowTask:
        def sort_key(task: WorkflowTask):
            status = self.sla_service.get_task_sla_status(task).get('status') or 'unknown'
            severity = -self._STATUS_SEVERITY.get(status, 0)
            due_date = task.due_date or (timezone.now() + timedelta(days=36500))
            created_at = task.created_at or timezone.now()
            return (severity, due_date, created_at)

        return sorted(tasks, key=sort_key)[0]

    @staticmethod
    def _serialize_assignee(user) -> Optional[Dict[str, Any]]:
        if user is None:
            return None

        display_name = ''
        if hasattr(user, 'get_full_name'):
            display_name = user.get_full_name() or ''
        display_name = display_name or getattr(user, 'username', '') or ''

        return {
            'id': str(user.id),
            'username': getattr(user, 'username', '') or '',
            'displayName': display_name,
        }
