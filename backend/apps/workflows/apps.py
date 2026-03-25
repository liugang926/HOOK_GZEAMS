"""
Django app configuration for workflows app.
"""
import logging

from django.apps import AppConfig
from django.db.models.signals import post_save, pre_save
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class WorkflowsConfig(AppConfig):
    """Configuration for the workflows application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.workflows'
    verbose_name = _('Workflows')
    verbose_name_plural = _('Workflows')

    def ready(self):
        """Import signal handlers when app is ready."""
        from apps.common.services.redis_service import redis_service
        from apps.workflows.models import WorkflowInstance, WorkflowTask
        from apps.workflows.signals import (
            workflow_started,
            workflow_completed,
            workflow_rejected,
            workflow_cancelled,
        )
        from apps.workflows.services.business_state_sync import BusinessStateSyncService
        from apps.workflows.services.notification_service import notification_service

        sync_service = BusinessStateSyncService()

        def _on_workflow_started(sender, instance, **kwargs):
            """Sync business doc status when workflow starts."""
            try:
                sync_service.sync_business_status(instance)
                redis_service.on_workflow_started(instance)
            except Exception:
                logger.exception('Workflow started handler failed for instance %s', getattr(instance, 'id', None))

        def _on_workflow_completed(sender, instance, **kwargs):
            """Sync business doc status when workflow completes."""
            try:
                sync_service.sync_business_status(instance)
                notification_service.notify_workflow_completed(instance)
                redis_service.on_workflow_completed(instance)
            except Exception:
                logger.exception('Workflow completed handler failed for instance %s', getattr(instance, 'id', None))

        def _on_workflow_rejected(sender, instance, **kwargs):
            """Sync business doc status when workflow is rejected."""
            try:
                sync_service.sync_business_status(instance)
                rejected_task = instance.tasks.filter(
                    status=WorkflowTask.STATUS_REJECTED
                ).select_related('completed_by').order_by('-completed_at').first()
                rejector = rejected_task.completed_by if rejected_task else None
                notification_service.notify_workflow_rejected(instance, rejector)
                redis_service.on_workflow_rejected(instance)
            except Exception:
                logger.exception('Workflow rejected handler failed for instance %s', getattr(instance, 'id', None))

        def _on_workflow_cancelled(sender, instance, **kwargs):
            """Sync business doc status when workflow is cancelled."""
            try:
                sync_service.sync_business_status(instance)
                cancelled_by = kwargs.get('user') or getattr(instance, 'terminated_by', None)
                notification_service.notify_workflow_cancelled(
                    instance,
                    cancelled_by,
                    getattr(instance, 'termination_reason', '') or ''
                )
                redis_service.on_workflow_cancelled(instance)
            except Exception:
                logger.exception('Workflow cancelled handler failed for instance %s', getattr(instance, 'id', None))

        def _capture_previous_task_state(sender, instance, **kwargs):
            """Store task state before save so post-save handlers can detect transitions."""
            instance._previous_status = None
            instance._previous_assignee_id = None

            if not instance.pk:
                return

            previous_task = sender.all_objects.filter(pk=instance.pk).only('status', 'assignee_id').first()
            if previous_task:
                instance._previous_status = previous_task.status
                instance._previous_assignee_id = previous_task.assignee_id

        def _on_task_saved(sender, instance, created, **kwargs):
            """Send task notifications and invalidate task caches on task lifecycle changes."""
            previous_status = getattr(instance, '_previous_status', None)
            previous_assignee_id = getattr(instance, '_previous_assignee_id', None)

            try:
                if instance.status == WorkflowTask.STATUS_PENDING and (
                    created or previous_assignee_id != instance.assignee_id
                ):
                    notification_service.notify_task_assigned(instance, [instance.assignee])
                    redis_service.on_task_assigned(instance)
                    if previous_assignee_id and previous_assignee_id != instance.assignee_id:
                        redis_service.invalidate_user_tasks_cache(str(previous_assignee_id))

                if (
                    instance.status in WorkflowTask.COMPLETED_STATUSES and
                    previous_status not in WorkflowTask.COMPLETED_STATUSES
                ):
                    notification_service.notify_task_completed(instance, instance.completed_by)
                    redis_service.on_task_completed(instance)
            except Exception:
                logger.exception('Task lifecycle handler failed for task %s', getattr(instance, 'id', None))

        workflow_started.connect(
            _on_workflow_started,
            sender=WorkflowInstance,
            weak=False,
            dispatch_uid='workflows.workflow_started.handlers'
        )
        workflow_completed.connect(
            _on_workflow_completed,
            sender=WorkflowInstance,
            weak=False,
            dispatch_uid='workflows.workflow_completed.handlers'
        )
        workflow_rejected.connect(
            _on_workflow_rejected,
            sender=WorkflowInstance,
            weak=False,
            dispatch_uid='workflows.workflow_rejected.handlers'
        )
        workflow_cancelled.connect(
            _on_workflow_cancelled,
            sender=WorkflowInstance,
            weak=False,
            dispatch_uid='workflows.workflow_cancelled.handlers'
        )
        pre_save.connect(
            _capture_previous_task_state,
            sender=WorkflowTask,
            weak=False,
            dispatch_uid='workflows.workflow_task.pre_save'
        )
        post_save.connect(
            _on_task_saved,
            sender=WorkflowTask,
            weak=False,
            dispatch_uid='workflows.workflow_task.post_save'
        )
