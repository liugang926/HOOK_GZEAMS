"""
ViewSets for DataPermissionExpand model.
"""
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.permissions.models.data_permission_expand import DataPermissionExpand
from apps.permissions.serializers.data_permission_expand_serializers import (
    DataPermissionExpandSerializer,
    DataPermissionExpandCreateSerializer,
    DataPermissionExpandUpdateSerializer,
)
from apps.permissions.filters.data_permission_expand_filters import DataPermissionExpandFilter


class DataPermissionExpandViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for DataPermissionExpand management.

    Provides CRUD operations for extended data permission rules.
    """
    queryset = DataPermissionExpand.objects.select_related(
        'data_permission',
        'data_permission__content_type'
    ).all()
    filterset_class = DataPermissionExpandFilter
    lookup_field = 'id'

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return DataPermissionExpandCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DataPermissionExpandUpdateSerializer
        return DataPermissionExpandSerializer

    @action(detail=False, methods=['get'])
    def by_data_permission(self, request):
        """
        Get expansions for a specific data permission.

        Query params:
        - data_permission_id: UUID of the data permission
        """
        data_permission_id = request.query_params.get('data_permission_id')

        if not data_permission_id:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'data_permission_id is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        expansions = self.queryset.filter(
            data_permission_id=data_permission_id,
            is_active=True,
            is_deleted=False
        ).order_by('-priority')

        serializer = self.get_serializer(expansions, many=True)

        return Response({
            'success': True,
            'data': {
                'data_permission_id': data_permission_id,
                'expansions': serializer.data
            }
        })

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a permission expansion."""
        expansion = self.get_object()
        expansion.is_active = True
        expansion.save()

        serializer = self.get_serializer(expansion)
        return Response({
            'success': True,
            'message': 'Expansion activated',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a permission expansion."""
        expansion = self.get_object()
        expansion.is_active = False
        expansion.save()

        serializer = self.get_serializer(expansion)
        return Response({
            'success': True,
            'message': 'Expansion deactivated',
            'data': serializer.data
        })
