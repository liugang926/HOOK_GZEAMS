"""
ViewSets for integration configuration management.

Provides ViewSets for IntegrationConfig model following BaseModelViewSet pattern.
"""
from rest_framework import status
from rest_framework.decorators import action

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.responses.base import BaseResponse
from apps.integration.models import IntegrationConfig
from apps.integration.serializers import (
    IntegrationConfigListSerializer,
    IntegrationConfigDetailSerializer,
    IntegrationConfigCreateSerializer,
    IntegrationConfigUpdateSerializer,
    TestConnectionSerializer,
)
from apps.integration.filters import IntegrationConfigFilter
from apps.integration.services import IntegrationConfigService


class IntegrationConfigViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for IntegrationConfig management.

    Provides standard CRUD operations plus:
    - test_connection: Test connection to external system
    - health_check: Perform health check
    """

    queryset = IntegrationConfig.objects.filter(is_deleted=False)
    filterset_class = IntegrationConfigFilter

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return IntegrationConfigListSerializer
        if self.action == 'retrieve':
            return IntegrationConfigDetailSerializer
        if self.action == 'create':
            return IntegrationConfigCreateSerializer
        if self.action in ['update', 'partial_update']:
            return IntegrationConfigUpdateSerializer
        return IntegrationConfigListSerializer

    def perform_create(self, serializer):
        """Set organization and created_by on create."""
        organization_id = getattr(self.request, 'organization_id', None)
        serializer.save(
            created_by=self.request.user,
            organization_id=organization_id,
            health_status='unhealthy'
        )

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """
        Test connection to external system.

        POST /api/integration/configs/{id}/test_connection/

        Response:
        {
            "success": true,
            "message": "Connection successful",
            "data": {
                "response_time_ms": 245,
                "details": {...}
            }
        }
        """
        config = self.get_object()

        service = IntegrationConfigService(config.organization, request.user)
        result = service.test_connection(config)

        if result['success']:
            return BaseResponse.success(
                data={
                    'response_time_ms': result['response_time_ms'],
                    'details': result.get('details')
                },
                message=result['message']
            )
        else:
            return BaseResponse.error(
                code='CONNECTION_FAILED',
                message=result['message'],
                http_status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def health_check(self, request, pk=None):
        """
        Perform health check on integration config.

        POST /api/integration/configs/{id}/health_check/

        Response:
        {
            "success": true,
            "message": "Health check completed",
            "data": {
                "health_status": "healthy",
                "response_time_ms": 150
            }
        }
        """
        config = self.get_object()

        service = IntegrationConfigService(config.organization, request.user)
        result = service.health_check(config)

        # Refresh config to get updated health status
        config.refresh_from_db()

        return BaseResponse.success(
            data={
                'health_status': config.health_status,
                'last_health_check_at': config.last_health_check_at,
                'response_time_ms': result.get('response_time_ms')
            },
            message=result['message']
        )
