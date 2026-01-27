"""
ViewSets for PermissionAuditLog model.
"""
from django.db import models
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from apps.common.viewsets.base import BaseModelViewSet
from apps.permissions.models.permission_audit_log import PermissionAuditLog
from apps.permissions.serializers.permission_audit_log_serializers import (
    PermissionAuditLogSerializer,
    PermissionAuditLogDetailSerializer,
)
from apps.permissions.filters.permission_audit_log_filters import PermissionAuditLogFilter


class PermissionAuditLogViewSet(BaseModelViewSet):
    """
    ViewSet for PermissionAuditLog (read-only).

    Provides read-only access to permission audit logs.
    Audit logs are created automatically by the system.
    """
    queryset = PermissionAuditLog.objects.select_related(
        'actor',
        'target_user',
        'content_type'
    ).all()
    filterset_class = PermissionAuditLogFilter
    lookup_field = 'id'
    http_method_names = ['get', 'head', 'options']  # Read-only

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return PermissionAuditLogDetailSerializer
        return PermissionAuditLogSerializer

    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """
        Get audit logs for a specific user.

        Query params:
        - user_id: UUID of the user (as actor or target)
        """
        user_id = request.query_params.get('user_id')

        if not user_id:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'user_id is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get logs where user is either actor or target
        logs = self.queryset.filter(
            is_deleted=False
        ).filter(
            models.Q(actor_id=user_id) | models.Q(target_user_id=user_id)
        ).order_by('-created_at')

        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': serializer.data
            })

        serializer = self.get_serializer(logs, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get audit log statistics.

        Query params:
        - user_id: Optional user ID to filter by
        - days: Number of days to look back (default: 30)
        """
        from django.db.models import Count, Q
        from django.utils import timezone
        from datetime import timedelta

        user_id = request.query_params.get('user_id')
        days = int(request.query_params.get('days', 30))

        since = timezone.now() - timedelta(days=days)

        # Build base queryset
        queryset = self.queryset.filter(
            created_at__gte=since,
            is_deleted=False
        )

        if user_id:
            queryset = queryset.filter(
                Q(actor_id=user_id) | Q(target_user_id=user_id)
            )

        # Get statistics
        total_count = queryset.count()
        operation_counts = queryset.values('operation_type').annotate(
            count=Count('id')
        ).order_by('-count')

        result_counts = queryset.values('result').annotate(
            count=Count('id')
        ).order_by('-count')

        target_type_counts = queryset.values('target_type').annotate(
            count=Count('id')
        ).order_by('-count')

        return Response({
            'success': True,
            'data': {
                'period_days': days,
                'total_count': total_count,
                'by_operation': list(operation_counts),
                'by_result': list(result_counts),
                'by_target_type': list(target_type_counts),
            }
        })
