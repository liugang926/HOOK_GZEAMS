"""
ViewSets for integration log management.

Provides ViewSets for IntegrationLog model following BaseModelViewSet pattern.
"""
from rest_framework import status
from rest_framework.decorators import action

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.responses.base import BaseResponse
from apps.integration.models import IntegrationLog
from apps.integration.serializers import (
    IntegrationLogListSerializer,
    IntegrationLogDetailSerializer,
    LogStatisticsSerializer,
)
from apps.integration.filters import IntegrationLogFilter
from apps.integration.services import IntegrationLogService


class IntegrationLogViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for IntegrationLog management.

    Provides standard CRUD operations plus:
    - statistics: Get log statistics
    - errors: Get recent error logs
    """

    queryset = IntegrationLog.objects.filter(is_deleted=False)
    filterset_class = IntegrationLogFilter

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return IntegrationLogListSerializer
        if self.action == 'retrieve':
            return IntegrationLogDetailSerializer
        return IntegrationLogListSerializer

    def perform_create(self, serializer):
        """Set organization and created_by on create."""
        organization_id = getattr(self.request, 'organization_id', None)
        serializer.save(
            created_by=self.request.user,
            organization_id=organization_id
        )

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get log statistics.

        GET /api/integration/logs/statistics/?days=30

        Response:
        {
            "success": true,
            "data": {
                "total": 1000,
                "success": 950,
                "failed": 50,
                "success_rate": 95.0,
                "avg_duration_ms": 250.5,
                "by_system": [...],
                "by_action": [...]
            }
        }
        """
        days = min(int(request.query_params.get('days', 30)), 365)

        service = IntegrationLogService(
            organization=getattr(request, 'organization', None),
            user=request.user
        )
        stats = service.get_statistics(days=days)

        return BaseResponse.success(data=stats)

    @action(detail=False, methods=['get'])
    def errors(self, request):
        """
        Get recent error logs.

        GET /api/integration/logs/errors/?limit=50

        Response:
        {
            "success": true,
            "data": {
                "count": 10,
                "results": [...]
            }
        }
        """
        limit = min(int(request.query_params.get('limit', 50)), 500)

        service = IntegrationLogService(
            organization=getattr(request, 'organization', None),
            user=request.user
        )
        error_logs = service.get_error_logs(limit=limit)

        serializer = IntegrationLogListSerializer(error_logs, many=True)

        return BaseResponse.success(data={
            'count': len(error_logs),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'])
    def slow(self, request):
        """
        Get slow requests (above threshold).

        GET /api/integration/logs/slow/?threshold_ms=5000&limit=50

        Response:
        {
            "success": true,
            "data": {
                "count": 5,
                "results": [...]
            }
        }
        """
        threshold_ms = int(request.query_params.get('threshold_ms', 5000))
        limit = min(int(request.query_params.get('limit', 50)), 200)

        service = IntegrationLogService(
            organization=getattr(request, 'organization', None),
            user=request.user
        )
        slow_logs = service.get_slow_requests(threshold_ms=threshold_ms, limit=limit)

        serializer = IntegrationLogListSerializer(slow_logs, many=True)

        return BaseResponse.success(data={
            'count': len(slow_logs),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'])
    def daily_stats(self, request):
        """
        Get daily statistics.

        GET /api/integration/logs/daily_stats/?days=7

        Response:
        {
            "success": true,
            "data": [...]
        }
        """
        days = min(int(request.query_params.get('days', 7)), 90)

        service = IntegrationLogService(
            organization=getattr(request, 'organization', None),
            user=request.user
        )
        daily_stats = service.get_daily_stats(days=days)

        return BaseResponse.success(data=daily_stats)
