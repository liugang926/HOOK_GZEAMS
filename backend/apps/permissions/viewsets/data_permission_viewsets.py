"""
ViewSets for DataPermission model.
"""
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.contrib.contenttypes.models import ContentType

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.permissions.models.data_permission import DataPermission
from apps.permissions.serializers.data_permission_serializers import (
    DataPermissionSerializer,
    DataPermissionDetailSerializer,
    DataPermissionCreateSerializer,
    DataPermissionUpdateSerializer,
)
from apps.permissions.filters.data_permission_filters import DataPermissionFilter


class DataPermissionViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for DataPermission management.

    Provides CRUD operations for data-level (row-level) permissions.
    Includes batch operations and permission caching invalidation.
    """
    # Use all_objects to bypass organization filtering in TenantManager
    # Permissions are user-scoped, not organization-scoped
    queryset = DataPermission.all_objects.filter(is_deleted=False)
    filterset_class = DataPermissionFilter
    lookup_field = 'id'

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return DataPermissionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DataPermissionUpdateSerializer
        elif self.action == 'retrieve':
            return DataPermissionDetailSerializer
        return DataPermissionSerializer

    def perform_create(self, serializer):
        """Set created_by and invalidate cache."""
        instance = serializer.save(created_by=self.request.user)

        # Invalidate cache for affected user
        if instance.user:
            from apps.permissions.services.permission_engine import PermissionEngine
            PermissionEngine.invalidate_user_cache(instance.user.id)

        # Log the permission grant
        from apps.permissions.models.permission_audit_log import PermissionAuditLog
        PermissionAuditLog.log_grant(
            actor=self.request.user,
            target_user=instance.user,
            permission_details={
                'type': 'data_permission',
                'content_type': instance.content_type.model,
                'scope_type': instance.scope_type,
            },
            content_object=instance
        )

    def perform_update(self, serializer):
        """Update and invalidate cache."""
        instance = serializer.save()

        # Invalidate cache for affected user
        if instance.user:
            from apps.permissions.services.permission_engine import PermissionEngine
            PermissionEngine.invalidate_user_cache(instance.user.id)

        # Log the permission modification
        from apps.permissions.models.permission_audit_log import PermissionAuditLog
        PermissionAuditLog.log_modify(
            actor=self.request.user,
            permission_details={
                'type': 'data_permission',
                'content_type': instance.content_type.model,
                'scope_type': instance.scope_type,
            },
            content_object=instance
        )

    def perform_destroy(self, instance):
        """Soft delete and invalidate cache."""
        from apps.permissions.models.permission_audit_log import PermissionAuditLog

        # Log before deletion
        PermissionAuditLog.log_revoke(
            actor=self.request.user,
            target_user=instance.user,
            permission_details={
                'type': 'data_permission',
                'content_type': instance.content_type.model,
                'scope_type': instance.scope_type,
            },
            content_object=instance
        )

        # Soft delete
        instance.soft_delete(user=self.request.user)

        # Invalidate cache for affected user
        if instance.user:
            from apps.permissions.services.permission_engine import PermissionEngine
            PermissionEngine.invalidate_user_cache(instance.user.id)

    @action(detail=False, methods=['get'])
    def by_content_type(self, request):
        """
        Get data permissions for a specific content type.

        Query params:
        - app_label: App label of the model
        - model: Model name
        - user_id: Optional user ID (defaults to current user)
        """
        app_label = request.query_params.get('app_label')
        model = request.query_params.get('model')
        user_id = request.query_params.get('user_id')

        if not app_label or not model:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'app_label and model are required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            content_type = ContentType.objects.get(
                app_label=app_label,
                model=model.lower()
            )
        except ContentType.DoesNotExist:
            return Response({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': f'ContentType {app_label}.{model} not found'
                }
            }, status=status.HTTP_404_NOT_FOUND)

        # Get user to check permissions for
        user = request.user
        if user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id, is_deleted=False)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'User not found'
                    }
                }, status=status.HTTP_404_NOT_FOUND)

        # Get data permission scope
        from apps.permissions.services.permission_engine import PermissionEngine
        engine = PermissionEngine(user)
        scope = engine.get_data_scope(content_type)

        return Response({
            'success': True,
            'data': {
                'content_type': f'{app_label}.{model}',
                'user_id': str(user.id),
                'data_scope': scope,
            }
        })

    @action(detail=False, methods=['post'])
    def grant(self, request):
        """
        Grant data permission to user or role.

        Request body:
        {
            "user_id": "uuid" or "role_code": "code",
            "content_type": {"app_label": "...", "model": "..."},
            "scope_type": "all|self_dept|self_and_sub|specified|custom|self",
            "scope_value": {...},
            "department_field": "department",
            "user_field": "created_by"
        }
        """
        serializer = DataPermissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(created_by=request.user)

        return Response({
            'success': True,
            'message': 'Data permission granted',
            'data': DataPermissionDetailSerializer(instance).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def revoke(self, request):
        """
        Revoke data permission from user or role.

        Request body:
        {
            "ids": ["uuid1", "uuid2"]
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

        for perm_id in ids:
            try:
                instance = DataPermission.objects.get(id=perm_id, is_deleted=False)
                self.perform_destroy(instance)
                results.append({'id': str(perm_id), 'success': True})
                succeeded += 1
            except DataPermission.DoesNotExist:
                results.append({'id': str(perm_id), 'success': False, 'error': 'Not found'})
                failed += 1

        return Response({
            'success': True,
            'message': f'Data permissions revoked: {succeeded} succeeded, {failed} failed',
            'summary': {
                'total': len(ids),
                'succeeded': succeeded,
                'failed': failed
            },
            'results': results
        }, status=status.HTTP_200_OK if failed == 0 else status.HTTP_207_MULTI_STATUS)
