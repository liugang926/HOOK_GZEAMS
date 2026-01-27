"""
Service for integration sync task management.

Provides business logic for managing IntegrationSyncTask instances.
"""
import logging
import uuid
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from apps.common.services.base_crud import BaseCRUDService
from apps.integration.models import IntegrationConfig, IntegrationSyncTask
from apps.integration.adapters import get_adapter
from apps.integration.constants import SyncStatus, SyncDirection

logger = logging.getLogger(__name__)


class IntegrationSyncService(BaseCRUDService):
    """Service for IntegrationSyncTask management."""

    def __init__(self):
        """Initialize service with IntegrationSyncTask model."""
        super().__init__(IntegrationSyncTask)

    def create_sync_task(
        self,
        config: IntegrationConfig,
        module_type: str,
        direction: str,
        business_type: str,
        sync_params: Optional[Dict[str, Any]] = None,
        user=None
    ) -> IntegrationSyncTask:
        """
        Create a new sync task.

        Args:
            config: IntegrationConfig instance
            module_type: Module type (procurement, finance, etc.)
            direction: Sync direction (pull, push, bidirectional)
            business_type: Business type (purchase_order, voucher, etc.)
            sync_params: Optional sync parameters

        Returns:
            Created IntegrationSyncTask instance
        """
        task_id = f"sync_{config.system_type}_{business_type}_{uuid.uuid4().hex[:8]}"

        task_data = {
            'config': config,
            'task_id': task_id,
            'module_type': module_type,
            'direction': direction,
            'business_type': business_type,
            'sync_params': sync_params or {},
            'status': SyncStatus.PENDING,
        }

        return self.create(task_data, user=user)

    def execute_sync(
        self,
        task: IntegrationSyncTask,
        sync_func: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Execute a sync task.

        Args:
            task: IntegrationSyncTask instance
            sync_func: Optional custom sync function

        Returns:
            Dict with execution results
        """
        from apps.integration.models import IntegrationLog

        # Update task status to running
        task.status = SyncStatus.RUNNING
        task.started_at = datetime.now()
        task.save(update_fields=['status', 'started_at'])

        try:
            adapter = get_adapter(task.config)

            if adapter is None:
                raise ValueError(f'No adapter available for system type: {task.config.system_type}')

            start_time = datetime.now()

            # Execute sync based on direction
            if task.direction == SyncDirection.PULL:
                if sync_func:
                    result = sync_func()
                else:
                    data = adapter.pull_data(task.business_type, task.sync_params)
                    result = {
                        'total': len(data),
                        'success': len(data),
                        'failed': 0,
                        'data': data
                    }
            elif task.direction == SyncDirection.PUSH:
                if sync_func:
                    result = sync_func()
                else:
                    result = adapter.push_data(task.business_type, task.sync_params.get('data', []))
            else:
                raise ValueError(f'Unsupported sync direction: {task.direction}')

            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Update task with results
            task.total_count = result.get('total', 0)
            task.success_count = result.get('success', 0)
            task.failed_count = result.get('failed', 0)
            task.duration_ms = duration_ms
            task.completed_at = end_time

            # Determine final status
            if task.failed_count == 0:
                task.status = SyncStatus.SUCCESS
            elif task.success_count > 0:
                task.status = SyncStatus.PARTIAL_SUCCESS
            else:
                task.status = SyncStatus.FAILED

            # Store error summary
            if 'errors' in result:
                task.error_summary = result['errors']

            task.save(
                update_fields=[
                    'status', 'total_count', 'success_count', 'failed_count',
                    'error_summary', 'duration_ms', 'completed_at'
                ]
            )

            # Update config last sync info
            task.config.last_sync_at = end_time
            task.config.last_sync_status = task.status
            task.config.save(update_fields=['last_sync_at', 'last_sync_status'])

            return {
                'status': task.status,
                'total': task.total_count,
                'success': task.success_count,
                'failed': task.failed_count,
                'errors': task.error_summary
            }

        except Exception as e:
            logger.error(f"Sync task {task.task_id} failed: {e}")

            # Update task as failed
            task.status = SyncStatus.FAILED
            task.completed_at = datetime.now()
            if task.started_at:
                task.duration_ms = int((task.completed_at - task.started_at).total_seconds() * 1000)
            task.error_summary = [{'error': str(e)}]
            task.save(update_fields=['status', 'completed_at', 'duration_ms', 'error_summary'])

            return {
                'status': SyncStatus.FAILED,
                'total': 0,
                'success': 0,
                'failed': 1,
                'errors': [str(e)]
            }

    def cancel_task(self, task: IntegrationSyncTask) -> Dict[str, Any]:
        """
        Cancel a pending sync task.

        Args:
            task: IntegrationSyncTask instance

        Returns:
            Dict with cancellation result
        """
        if task.status != SyncStatus.PENDING:
            return {
                'success': False,
                'message': f'Cannot cancel task in status: {task.status}'
            }

        task.status = SyncStatus.CANCELLED
        task.completed_at = datetime.now()
        task.save(update_fields=['status', 'completed_at'])

        return {
            'success': True,
            'message': 'Task cancelled successfully'
        }

    def retry_task(self, task: IntegrationSyncTask) -> IntegrationSyncTask:
        """
        Retry a failed sync task.

        Args:
            task: Original failed IntegrationSyncTask instance

        Returns:
            New IntegrationSyncTask instance for retry
        """
        if task.status not in [SyncStatus.FAILED, SyncStatus.PARTIAL_SUCCESS]:
            raise ValueError(f'Cannot retry task in status: {task.status}')

        # Create new task with same parameters
        new_task = self.create_sync_task(
            config=task.config,
            module_type=task.module_type,
            direction=task.direction,
            business_type=task.business_type,
            sync_params=task.sync_params
        )

        return new_task

    def get_running_tasks(self) -> list:
        """
        Get all running sync tasks for current organization.

        Returns:
            List of running IntegrationSyncTask instances
        """
        return list(self.query(filters={'status': SyncStatus.RUNNING}))

    def get_failed_tasks(self, limit: int = 10) -> list:
        """
        Get recent failed sync tasks for current organization.

        Args:
            limit: Maximum number of tasks to return

        Returns:
            List of failed IntegrationSyncTask instances
        """
        return list(self.query(
            filters={'status': SyncStatus.FAILED},
            order_by='-created_at'
        ))[:limit]
