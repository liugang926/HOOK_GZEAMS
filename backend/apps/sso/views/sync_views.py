"""
Sync ViewSets

API viewsets for sync management.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.sso.models import SyncLog, WeWorkConfig
from apps.sso.serializers.sync_serializer import (
    SyncLogSerializer,
    SyncLogDetailSerializer,
    SyncTriggerSerializer,
    SyncConfigSerializer,
)
from apps.sso.filters import SyncLogFilter
from apps.common.middleware import get_current_organization


class SyncViewSet(BaseModelViewSetWithBatch):
    """Sync management API - inherits from BaseModelViewSetWithBatch."""

    queryset = SyncLog.objects.all()
    serializer_class = SyncLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = SyncLogFilter

    def get_serializer_class(self):
        """Select serializer based on action."""
        if self.action == 'retrieve':
            return SyncLogDetailSerializer
        return SyncLogSerializer

    @action(detail=False, methods=['post'])
    def trigger(self, request):
        """
        Manually trigger sync.

        Request body:
            sync_type: full/department/user (optional, default: full)
        """
        serializer = SyncTriggerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sync_type = serializer.validated_data.get('sync_type', 'full')

        # Get current organization
        organization = get_current_organization()
        if not organization:
            return Response({
                'success': False,
                'error': {
                    'code': 'ORGANIZATION_NOT_FOUND',
                    'message': 'Cannot determine current organization'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get WeWork config
        try:
            config = WeWorkConfig.objects.get(
                organization=organization,
                is_enabled=True
            )
        except WeWorkConfig.DoesNotExist:
            return Response({
                'success': False,
                'error': {
                    'code': 'WEWORK_NOT_CONFIGURED',
                    'message': 'WeWork is not configured or not enabled'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check for running sync
        running_log = SyncLog.objects.filter(
            organization=organization,
            status=SyncLog.StatusChoices.RUNNING
        ).first()

        if running_log:
            return Response({
                'success': False,
                'error': {
                    'code': 'CONFLICT',
                    'message': 'A sync task is already running',
                    'details': {'log_id': str(running_log.id)}
                }
            }, status=status.HTTP_409_CONFLICT)

        # Import sync service and trigger sync
        # For now, sync runs synchronously. In production, use Celery tasks.
        from apps.sso.services.wework_sync_service import WeWorkSyncService

        service = WeWorkSyncService(config)

        try:
            if sync_type == 'department':
                log = service.sync_departments_only()
            elif sync_type == 'user':
                log = service.sync_users_only()
            else:
                log = service.full_sync()

            return Response({
                'success': True,
                'message': 'Sync completed',
                'data': {
                    'log_id': str(log.id),
                    'sync_type': sync_type,
                    'status': log.status,
                    'stats': {
                        'total': log.total_count,
                        'created': log.created_count,
                        'updated': log.updated_count,
                        'deleted': log.deleted_count,
                        'failed': log.failed_count,
                    }
                }
            })

        except Exception as e:
            return Response({
                'success': False,
                'error': {
                    'code': 'SYNC_FAILED',
                    'message': str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get current sync status."""
        organization = get_current_organization()
        if not organization:
            return Response({
                'success': False,
                'error': {
                    'code': 'ORGANIZATION_NOT_FOUND',
                    'message': 'Cannot determine current organization'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        last_log = SyncLog.objects.filter(
            organization=organization
        ).order_by('-created_at').first()

        if not last_log:
            return Response({
                'success': True,
                'data': {
                    'status': 'never_synced',
                    'last_sync_time': None,
                    'stats': {}
                }
            })

        return Response({
            'success': True,
            'data': {
                'status': last_log.status,
                'last_sync_time': last_log.started_at,
                'stats': {
                    'total': last_log.total_count,
                    'created': last_log.created_count,
                    'updated': last_log.updated_count,
                    'deleted': last_log.deleted_count,
                    'failed': last_log.failed_count,
                }
            }
        })

    @action(detail=False, methods=['get'])
    def config(self, request):
        """Get sync configuration."""
        organization = get_current_organization()
        if not organization:
            return Response({
                'success': False,
                'error': {
                    'code': 'ORGANIZATION_NOT_FOUND',
                    'message': 'Cannot determine current organization'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            config = WeWorkConfig.objects.get(
                organization=organization,
                is_enabled=True
            )
            serializer = SyncConfigSerializer({
                'enabled': True,
                'corp_name': config.corp_name,
                'agent_id': config.agent_id,
                'auto_sync_enabled': True,
                'sync_department': config.sync_department,
                'sync_user': config.sync_user,
            })
            return Response({
                'success': True,
                'data': serializer.data
            })
        except WeWorkConfig.DoesNotExist:
            return Response({
                'success': True,
                'data': {
                    'enabled': False,
                    'message': 'WeWork is not configured or not enabled'
                }
            })
