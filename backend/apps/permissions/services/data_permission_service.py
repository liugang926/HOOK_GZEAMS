"""
DataPermissionService - Service for managing data-level permissions.

Provides business logic for data scope and row-level permission operations.
"""
from typing import Dict, List, Optional, Set
from django.db.models import QuerySet
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.common.services.base_crud import BaseCRUDService
from apps.permissions.models.data_permission import DataPermission
from apps.permissions.models.permission_audit_log import PermissionAuditLog

User = get_user_model()


class DataPermissionService(BaseCRUDService):
    """
    Service for managing DataPermission entities.

    Extends BaseCRUDService with data permission-specific operations.
    """

    def __init__(self):
        """Initialize service with DataPermission model."""
        super().__init__(DataPermission)

    def grant_permission(
        self,
        user: User,
        content_type: ContentType,
        scope_type: str,
        actor: User,
        scope_value: Optional[Dict] = None,
        department_field: str = "department",
        user_field: str = "created_by",
        description: str = ""
    ) -> DataPermission:
        """
        Grant data permission to a user.

        Args:
            user: User to grant permission to
            content_type: ContentType of the model
            scope_type: Type of data scope (all/self_dept/self_and_sub/specified/custom/self)
            actor: User granting the permission
            scope_value: Configuration for scope (dept IDs, custom filter, etc.)
            department_field: Field name for department reference
            user_field: Field name for user reference
            description: Description of the permission

        Returns:
            Created DataPermission instance

        Raises:
            ValidationError: If validation fails
        """
        # Get organization from user
        organization = user.current_organization if hasattr(user, 'current_organization') else None

        # Check if permission already exists
        existing = DataPermission.objects.filter(
            content_type=content_type,
            user=user,
            is_deleted=False
        ).first()

        if existing:
            # Update existing permission
            existing.scope_type = scope_type
            existing.scope_value = scope_value or {}
            existing.department_field = department_field
            existing.user_field = user_field
            existing.description = description
            existing.save()

            # Log the modification
            PermissionAuditLog.log_modify(
                actor=actor,
                permission_details={
                    'type': 'data_permission',
                    'content_type': content_type.model,
                    'scope_type': scope_type,
                },
                content_object=existing
            )

            return existing

        # Create new permission
        permission = DataPermission(
            user=user,
            content_type=content_type,
            scope_type=scope_type,
            scope_value=scope_value or {},
            department_field=department_field,
            user_field=user_field,
            description=description,
            created_by=actor,
            organization=organization
        )

        permission.full_clean()
        permission.save()

        # Log the grant
        PermissionAuditLog.log_grant(
            actor=actor,
            target_user=user,
            permission_details={
                'type': 'data_permission',
                'content_type': content_type.model,
                'scope_type': scope_type,
            },
            content_object=permission
        )

        return permission

    def revoke_permission(
        self,
        permission_id: str,
        actor: User
    ) -> bool:
        """
        Revoke a data permission.

        Args:
            permission_id: ID of the permission to revoke
            actor: User revoking the permission

        Returns:
            True if successfully revoked

        Raises:
            DataPermission.DoesNotExist: If permission not found
        """
        permission = DataPermission.objects.get(id=permission_id, is_deleted=False)

        # Log before revoking
        PermissionAuditLog.log_revoke(
            actor=actor,
            target_user=permission.user,
            permission_details={
                'type': 'data_permission',
                'content_type': permission.content_type.model,
                'scope_type': permission.scope_type,
            },
            content_object=permission
        )

        # Soft delete
        permission.soft_delete(user=actor)

        return True

    def apply_user_permissions(
        self,
        queryset: QuerySet,
        user: User,
        content_type: ContentType
    ) -> QuerySet:
        """
        Apply data permissions to a queryset for a user.

        Args:
            queryset: QuerySet to filter
            user: User to apply permissions for
            content_type: ContentType of the model

        Returns:
            Filtered QuerySet
        """
        # Get effective permission
        perm = DataPermission.get_effective_permission(user, content_type)

        if hasattr(perm, 'apply_to_queryset'):
            return perm.apply_to_queryset(queryset, user)

        # Default: return only user's own data
        return queryset.filter(created_by=user)

    def get_user_accessible_department_ids(
        self,
        user: User,
        content_type: ContentType
    ) -> Optional[Set[int]]:
        """
        Get department IDs the user can access data from.

        Args:
            user: User to check permissions for
            content_type: ContentType of the model

        Returns:
            Set of department IDs, or None for all access, or empty set for own data only
        """
        perm = DataPermission.get_effective_permission(user, content_type)

        if hasattr(perm, 'get_scope_department_ids'):
            return perm.get_scope_department_ids(user)

        return set()  # Default: own data only

    def get_user_permissions(
        self,
        user: User,
        content_type: Optional[ContentType] = None
    ) -> List[DataPermission]:
        """
        Get all data permissions for a user.

        Args:
            user: User to get permissions for
            content_type: Optional ContentType filter

        Returns:
            List of DataPermission instances
        """
        queryset = DataPermission.objects.filter(
            user=user,
            is_deleted=False
        )

        if content_type:
            queryset = queryset.filter(content_type=content_type)

        return queryset.select_related('content_type')

    def get_permission_summary(
        self,
        user: User
    ) -> Dict[str, List[Dict]]:
        """
        Get a summary of all data permissions for a user.

        Args:
            user: User to get summary for

        Returns:
            Dictionary with permission summaries by content type
        """
        # Get all permissions for user
        permissions = DataPermission.objects.filter(
            user=user,
            is_deleted=False
        ).select_related('content_type')

        summary = {}
        for perm in permissions:
            model_key = f'{perm.content_type.app_label}.{perm.content_type.model}'

            if model_key not in summary:
                summary[model_key] = []

            summary[model_key].append({
                'id': str(perm.id),
                'scope_type': perm.scope_type,
                'scope_type_display': perm.get_scope_type_display(),
                'is_user_based': True,
                'description': perm.description,
            })

        return summary

    def copy_permissions_to_user(
        self,
        source_user: User,
        target_user: User,
        actor: User
    ) -> int:
        """
        Copy data permissions from one user to another.

        Args:
            source_user: User to copy permissions from
            target_user: User to copy permissions to
            actor: User performing the operation

        Returns:
            Number of permissions copied
        """
        source_permissions = DataPermission.objects.filter(
            user=source_user,
            is_deleted=False
        )

        count = 0
        for source_perm in source_permissions:
            # Check if target already has this permission for this content type
            existing = DataPermission.objects.filter(
                user=target_user,
                content_type=source_perm.content_type,
                is_deleted=False
            ).first()

            if not existing:
                target_org = target_user.current_organization if hasattr(target_user, 'current_organization') else None
                DataPermission.objects.create(
                    user=target_user,
                    content_type=source_perm.content_type,
                    scope_type=source_perm.scope_type,
                    scope_value=source_perm.scope_value,
                    department_field=source_perm.department_field,
                    user_field=source_perm.user_field,
                    description=source_perm.description,
                    created_by=actor,
                    organization=target_org
                )
                count += 1

        return count
