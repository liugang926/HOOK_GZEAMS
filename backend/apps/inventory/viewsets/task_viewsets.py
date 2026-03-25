"""
ViewSets for Inventory Task model.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.responses.base import success_response, error_response
from apps.inventory.models import InventoryTask
from apps.inventory.serializers import (
    InventoryTaskListSerializer,
    InventoryTaskDetailSerializer,
    InventoryTaskCreateSerializer,
    InventoryTaskUpdateSerializer,
    InventoryTaskStartSerializer,
    InventoryTaskCompleteSerializer,
)
from apps.inventory.filters import InventoryTaskFilter
from apps.inventory.services import InventoryService


class InventoryTaskViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for inventory task management.

    Provides:
    - Standard CRUD operations
    - Start inventory task action
    - Complete inventory task action
    - Cancel inventory task action
    - Progress tracking
    - Executor management
    """

    queryset = InventoryTask.objects.all()
    filterset_class = InventoryTaskFilter
    search_fields = ['task_code', 'task_name', 'description']

    def get_serializer_class(self):
        """Get appropriate serializer based on action."""
        if self.action == 'list':
            return InventoryTaskListSerializer
        elif self.action == 'retrieve':
            return InventoryTaskDetailSerializer
        elif self.action == 'create':
            return InventoryTaskCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return InventoryTaskUpdateSerializer
        return InventoryTaskDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single task with standard response format."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Create a new inventory task.

        Automatically generates snapshots based on inventory type.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = InventoryService()
        try:
            task = service.create_task(
                task_name=serializer.validated_data['task_name'],
                inventory_type=serializer.validated_data['inventory_type'],
                organization_id=request.user.organization_id,
                created_by_id=str(request.user.id),
                description=serializer.validated_data.get('description'),
                department_id=serializer.validated_data.get('department'),
                category_id=serializer.validated_data.get('category'),
                sample_ratio=serializer.validated_data.get('sample_ratio'),
                planned_date=serializer.validated_data.get('planned_date'),
                notes=serializer.validated_data.get('notes'),
                executor_ids=serializer.validated_data.get('executor_ids', []),
                primary_executor_id=serializer.validated_data.get('primary_executor_id'),
            )

            response_serializer = InventoryTaskDetailSerializer(task)
            return success_response(
                data=response_serializer.data,
                message=_('Inventory task created successfully.'),
                http_status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to create inventory task.'),
                details={'error': str(e)}
            )

    @action(detail=True, methods=['post'], url_path='start')
    def start(self, request, pk=None):
        """
        Start an inventory task.

        POST /api/inventory/tasks/{id}/start/
        """
        task = self.get_object()
        serializer = InventoryTaskStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = InventoryService()
        try:
            updated_task = service.start_task(str(task.id), str(request.user.id))
            response_serializer = InventoryTaskDetailSerializer(updated_task)
            return success_response(
                data=response_serializer.data,
                message=_('Inventory task started successfully.')
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to start inventory task.'),
                details={'error': str(e)}
            )

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """
        Complete an inventory task.

        Automatically generates differences for discrepancies.

        POST /api/inventory/tasks/{id}/complete/
        """
        task = self.get_object()
        serializer = InventoryTaskCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = InventoryService()
        try:
            updated_task = service.complete_task(
                str(task.id),
                str(request.user.id),
                serializer.validated_data.get('notes')
            )
            response_serializer = InventoryTaskDetailSerializer(updated_task)
            return success_response(
                data=response_serializer.data,
                message=_('Inventory task completed successfully.')
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to complete inventory task.'),
                details={'error': str(e)}
            )

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """
        Cancel an inventory task.

        POST /api/inventory/tasks/{id}/cancel/
        """
        task = self.get_object()
        reason = request.data.get('reason', '')

        service = InventoryService()
        try:
            updated_task = service.cancel_task(str(task.id), str(request.user.id), reason)
            response_serializer = InventoryTaskDetailSerializer(updated_task)
            return success_response(
                data=response_serializer.data,
                message=_('Inventory task cancelled successfully.')
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to cancel inventory task.'),
                details={'error': str(e)}
            )

    @action(detail=True, methods=['get'], url_path='progress')
    def progress(self, request, pk=None):
        """
        Get detailed progress information for a task.

        GET /api/inventory/tasks/{id}/progress/
        """
        task = self.get_object()
        service = InventoryService()
        progress_data = service.get_task_progress(str(task.id))
        return success_response(data=progress_data)

    @action(detail=True, methods=['get'], url_path='statistics')
    def statistics(self, request, pk=None):
        """
        Get comprehensive statistics for a task.

        GET /api/inventory/tasks/{id}/statistics/
        """
        task = self.get_object()
        service = InventoryService()

        # Update statistics first
        service.update_statistics(str(task.id))

        # Get progress data
        progress_data = service.get_task_progress(str(task.id))

        # Get scan summary
        from apps.inventory.services import ScanService
        scan_service = ScanService()
        scan_summary = scan_service.get_scan_summary(str(task.id))

        # Get snapshot summary
        from apps.inventory.services import SnapshotService
        snapshot_service = SnapshotService()
        snapshot_summary = snapshot_service.get_snapshot_summary(str(task.id))

        # Get difference summary
        from apps.inventory.services import DifferenceService
        diff_service = DifferenceService()
        diff_summary = diff_service.get_difference_summary(str(task.id))

        return success_response(data={
            'progress': progress_data,
            'scans': scan_summary,
            'snapshots': snapshot_summary,
            'differences': diff_summary,
        })

    @action(detail=True, methods=['post'], url_path='executors')
    def add_executors(self, request, pk=None):
        """
        Add executors to an inventory task.

        POST /api/inventory/tasks/{id}/executors/
        """
        task = self.get_object()
        executor_ids = request.data.get('executor_ids', [])
        primary_executor_id = request.data.get('primary_executor_id')

        if not executor_ids:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Executor IDs are required.')
            )

        service = InventoryService()
        try:
            executors = service.add_executors_to_task(
                str(task.id),
                executor_ids,
                primary_executor_id
            )
            return success_response(
                data={'executors_added': len(executors)},
                message=_('Executors added successfully.')
            )
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to add executors.'),
                details={'error': str(e)}
            )

    @action(detail=True, methods=['delete'], url_path='executors/(?P<executor_id>[^/.]+)')
    def remove_executor(self, request, pk=None, executor_id=None):
        """
        Remove an executor from an inventory task.

        DELETE /api/inventory/tasks/{id}/executors/{executor_id}/
        """
        task = self.get_object()
        service = InventoryService()
        try:
            service.remove_executor_from_task(str(task.id), executor_id)
            return success_response(message=_('Executor removed successfully.'))
        except Exception as e:
            return error_response(
                code='VALIDATION_ERROR',
                message=_('Failed to remove executor.'),
                details={'error': str(e)}
            )

    @action(detail=True, methods=['post'], url_path='refresh-stats')
    def refresh_stats(self, request, pk=None):
        """
        Refresh task statistics from current data.

        POST /api/inventory/tasks/{id}/refresh-stats/
        """
        task = self.get_object()
        service = InventoryService()
        try:
            updated_task = service.update_statistics(str(task.id))
            response_serializer = InventoryTaskDetailSerializer(updated_task)
            return success_response(
                data=response_serializer.data,
                message=_('Statistics refreshed successfully.')
            )
        except Exception as e:
            return error_response(
                code='SERVER_ERROR',
                message=_('Failed to refresh statistics.'),
                details={'error': str(e)}
            )
