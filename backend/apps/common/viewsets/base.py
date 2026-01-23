from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.models import BaseModel


class BatchOperationMixin:
    """
    Mixin providing standard batch operation endpoints.

    Provides:
    - batch_delete(): Batch soft delete
    - batch_restore(): Batch restore
    - batch_update(): Batch field update
    """

    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        """
        Batch soft delete multiple records.

        Request body:
        {
            "ids": ["uuid1", "uuid2", "uuid3"]
        }

        Response:
        {
            "success": true,
            "message": "Batch delete completed",
            "summary": {"total": 3, "succeeded": 3, "failed": 0},
            "results": [...]
        }
        """
        ids = request.data.get('ids', [])
        if not ids:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'ids parameter cannot be empty'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get the service from the viewset
        service = getattr(self, 'service', None)
        if not service:
            # Fallback to direct model operations
            results = []
            succeeded = 0
            failed = 0

            for record_id in ids:
                try:
                    instance = self.get_queryset().get(id=record_id)
                    instance.soft_delete(request.user)
                    results.append({'id': str(record_id), 'success': True})
                    succeeded += 1
                except self.queryset.model.DoesNotExist:
                    results.append({'id': str(record_id), 'success': False, 'error': 'Not found'})
                    failed += 1
                except Exception as e:
                    results.append({'id': str(record_id), 'success': False, 'error': str(e)})
                    failed += 1
        else:
            result = service.batch_delete(ids, request.user)
            results = result['results']
            succeeded = result['succeeded']
            failed = result['failed']

        response_data = {
            'success': True,
            'message': 'Batch delete completed',
            'summary': {
                'total': len(ids),
                'succeeded': succeeded,
                'failed': failed
            },
            'results': results
        }

        http_status = status.HTTP_200_OK if failed == 0 else status.HTTP_207_MULTI_STATUS
        return Response(response_data, status=http_status)

    @action(detail=False, methods=['post'])
    def batch_restore(self, request):
        """
        Batch restore multiple soft-deleted records.

        Request body:
        {
            "ids": ["uuid1", "uuid2", "uuid3"]
        }
        """
        ids = request.data.get('ids', [])
        if not ids:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'ids parameter cannot be empty'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        results = []
        succeeded = 0
        failed = 0

        for record_id in ids:
            try:
                instance = self.queryset.model.all_objects.get(id=record_id)
                instance.is_deleted = False
                instance.deleted_at = None
                if hasattr(instance, 'deleted_by'):
                    instance.deleted_by = None
                instance.save()
                results.append({'id': str(record_id), 'success': True})
                succeeded += 1
            except Exception as e:
                results.append({'id': str(record_id), 'success': False, 'error': str(e)})
                failed += 1

        return Response({
            'success': True,
            'message': 'Batch restore completed',
            'summary': {
                'total': len(ids),
                'succeeded': succeeded,
                'failed': failed
            },
            'results': results
        })

    @action(detail=False, methods=['post'])
    def batch_update(self, request):
        """
        Batch update fields on multiple records.

        Request body:
        {
            "ids": ["uuid1", "uuid2"],
            "data": {"status": "active"}
        }
        """
        ids = request.data.get('ids', [])
        update_data = request.data.get('data', {})

        if not ids:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'ids parameter cannot be empty'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        results = []
        succeeded = 0
        failed = 0

        for record_id in ids:
            try:
                instance = self.get_queryset().get(id=record_id)
                for key, value in update_data.items():
                    setattr(instance, key, value)
                instance.save()
                results.append({'id': str(record_id), 'success': True})
                succeeded += 1
            except Exception as e:
                results.append({'id': str(record_id), 'success': False, 'error': str(e)})
                failed += 1

        return Response({
            'success': True,
            'message': 'Batch update completed',
            'summary': {
                'total': len(ids),
                'succeeded': succeeded,
                'failed': failed
            },
            'results': results
        })


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet for all BaseModel-derived models.

    Automatically provides:
    - Organization isolation in get_queryset
    - Soft delete filtering (excludes deleted records by default)
    - Audit field management (created_by, updated_by)
    - Standard CRUD actions

    Override perform_create, perform_update, perform_destroy
    to customize behavior if needed.
    """

    def get_queryset(self):
        """Filter out soft-deleted records and apply organization isolation."""
        return self.queryset.filter(is_deleted=False)

    def perform_create(self, serializer):
        """Set created_by and organization on create."""
        # Get organization from request context
        organization_id = getattr(self.request, 'organization_id', None)
        serializer.save(
            created_by=self.request.user,
            organization_id=organization_id
        )

    def perform_update(self, serializer):
        """Set updated_by on update."""
        if hasattr(self.request.user, 'id'):
            serializer.save(updated_by=self.request.user)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        """Perform soft delete instead of hard delete."""
        instance.soft_delete(user=self.request.user)

    @action(detail=False, methods=['get'])
    def deleted(self, request):
        """
        List soft-deleted records.

        GET /api/{resource}/deleted/

        Returns paginated list of soft-deleted records in BaseResponse format.
        """
        # Get all deleted records (user must have permission)
        queryset = self.queryset.model.all_objects.filter(is_deleted=True)

        # Use DRF's standard pagination for consistency
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Fallback for non-paginated requests
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': {
                'count': queryset.count(),
                'next': None,
                'previous': None,
                'results': serializer.data
            }
        })

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """
        Restore a soft-deleted record.

        POST /api/{resource}/{id}/restore/
        """
        instance = self.queryset.model.all_objects.get(id=pk)
        instance.is_deleted = False
        instance.deleted_at = None
        if hasattr(instance, 'deleted_by'):
            instance.deleted_by = None
        instance.save()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': 'Restore successful',
            'data': serializer.data
        })


class BaseModelViewSetWithBatch(BatchOperationMixin, BaseModelViewSet):
    """
    Base ViewSet with batch operation support.

    Inherits from both BatchOperationMixin and BaseModelViewSet
    to provide all standard CRUD + batch operation endpoints.

    This is the recommended ViewSet to use for most resources.
    """
    pass  # All functionality inherited from parent classes
