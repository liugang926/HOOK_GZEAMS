"""
ViewSets for integration sync task management.

Provides ViewSets for IntegrationSyncTask model following BaseModelViewSet pattern.
"""
from rest_framework import status
from rest_framework.decorators import action

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.responses.base import BaseResponse
from apps.integration.models import IntegrationSyncTask
from apps.integration.serializers import (
    IntegrationSyncTaskListSerializer,
    IntegrationSyncTaskDetailSerializer,
    CreateSyncTaskSerializer,
)
from apps.integration.filters import IntegrationSyncTaskFilter
from apps.integration.services import IntegrationSyncService
from apps.integration.constants import SyncStatus


class IntegrationSyncTaskViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for IntegrationSyncTask management.

    Provides standard CRUD operations plus:
    - cancel: Cancel a pending task
    - retry: Retry a failed task
    """

    queryset = IntegrationSyncTask.objects.filter(is_deleted=False)
    filterset_class = IntegrationSyncTaskFilter

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return IntegrationSyncTaskListSerializer
        if self.action == 'retrieve':
            return IntegrationSyncTaskDetailSerializer
        if self.action == 'create':
            return CreateSyncTaskSerializer
        return IntegrationSyncTaskListSerializer

    def perform_create(self, serializer):
        """Set organization and created_by on create."""
        organization_id = getattr(self.request, 'organization_id', None)
        serializer.save(
            created_by=self.request.user,
            organization_id=organization_id
        )

    def create(self, request, *args, **kwargs):
        """
        Create sync task using service layer.

        POST /api/integration/sync-tasks/
        """
        serializer = CreateSyncTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        config = serializer.validated_data['config_id']
        module_type = serializer.validated_data['module_type']
        direction = serializer.validated_data['direction']
        business_type = serializer.validated_data['business_type']
        sync_params = serializer.validated_data.get('sync_params') or {}

        service = IntegrationSyncService()
        task = service.create_sync_task(
            config=config,
            module_type=module_type,
            direction=direction,
            business_type=business_type,
            sync_params=sync_params,
            user=request.user
        )

        if request.data.get('execute') is True:
            service.execute_sync(task)
            task.refresh_from_db()

        return BaseResponse.success(
            data=IntegrationSyncTaskDetailSerializer(task).data,
            message='Sync task created successfully'
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a pending sync task.

        POST /api/integration/sync-tasks/{id}/cancel/

        Response:
        {
            "success": true,
            "message": "Task cancelled successfully"
        }
        """
        task = self.get_object()

        service = IntegrationSyncService()
        result = service.cancel_task(task)

        if result['success']:
            return BaseResponse.success(message=result['message'])
        else:
            return BaseResponse.error(
                code='CANCEL_FAILED',
                message=result['message'],
                http_status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """
        Retry a failed sync task.

        POST /api/integration/sync-tasks/{id}/retry/

        Creates a new task with the same parameters.

        Response:
        {
            "success": true,
            "message": "Retry task created",
            "data": {...}
        }
        """
        task = self.get_object()

        if task.status not in [SyncStatus.FAILED, SyncStatus.PARTIAL_SUCCESS]:
            return BaseResponse.error(
                code='INVALID_STATUS',
                message=f'Cannot retry task in status: {task.status}',
                http_status=status.HTTP_400_BAD_REQUEST
            )

        service = IntegrationSyncService()
        new_task = service.retry_task(task)

        return BaseResponse.success(
            data=IntegrationSyncTaskDetailSerializer(new_task).data,
            message='Retry task created successfully'
        )

    @action(detail=False, methods=['get'])
    def running(self, request):
        """
        Get all currently running sync tasks.

        GET /api/integration/sync-tasks/running/

        Response:
        {
            "success": true,
            "data": {
                "count": 2,
                "results": [...]
            }
        }
        """
        service = IntegrationSyncService()
        running_tasks = service.get_running_tasks()

        serializer = IntegrationSyncTaskListSerializer(running_tasks, many=True)

        return BaseResponse.success(data={
            'count': len(running_tasks),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'])
    def failed(self, request):
        """
        Get recent failed sync tasks.

        GET /api/integration/sync-tasks/failed/

        Response:
        {
            "success": true,
            "data": {
                "count": 5,
                "results": [...]
            }
        }
        """
        limit = min(int(request.query_params.get('limit', 10)), 100)

        service = IntegrationSyncService()
        failed_tasks = service.get_failed_tasks(limit=limit)

        serializer = IntegrationSyncTaskListSerializer(failed_tasks, many=True)

        return BaseResponse.success(data={
            'count': len(failed_tasks),
            'results': serializer.data
        })

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        Execute a sync task immediately.

        POST /api/integration/sync-tasks/{id}/execute/
        """
        task = self.get_object()

        if task.status not in [
            SyncStatus.PENDING,
            SyncStatus.FAILED,
            SyncStatus.PARTIAL_SUCCESS,
        ]:
            return BaseResponse.error(
                code='INVALID_STATUS',
                message=f'Cannot execute task in status: {task.status}',
                http_status=status.HTTP_400_BAD_REQUEST
            )

        service = IntegrationSyncService()
        result = service.execute_sync(task)
        task.refresh_from_db()

        return BaseResponse.success(
            data={
                'task': IntegrationSyncTaskDetailSerializer(task).data,
                'result': result,
            },
            message='Sync task executed'
        )
