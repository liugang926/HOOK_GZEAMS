"""
FieldPermissionService - Service for managing field-level permissions.

Provides business logic for field permission operations.
"""
from typing import Dict, List, Optional
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

from apps.common.services.base_crud import BaseCRUDService
from apps.permissions.models.field_permission import FieldPermission
from apps.permissions.models.permission_audit_log import PermissionAuditLog

User = get_user_model()


class FieldPermissionService(BaseCRUDService):
    """
    Service for managing FieldPermission entities.

    Extends BaseCRUDService with field permission-specific operations.
    """

    def __init__(self):
        """Initialize service with FieldPermission model."""
        super().__init__(FieldPermission)

    def grant_permission(
        self,
        user: User,
        content_type: ContentType,
        field_name: str,
        permission_type: str,
        actor: User,
        mask_rule: Optional[str] = None,
        condition: Optional[Dict] = None,
        priority: int = 0,
        description: str = ""
    ) -> FieldPermission:
        """
        Grant field permission to a user.

        Args:
            user: User to grant permission to
            content_type: ContentType of the model
            field_name: Name of the field
            permission_type: Type of permission (read/write/hidden/masked)
            actor: User granting the permission
            mask_rule: Mask rule for masked permissions
            condition: Optional condition for applying permission
            priority: Priority for conflict resolution
            description: Description of the permission

        Returns:
            Created FieldPermission instance

        Raises:
            ValidationError: If validation fails
        """
        # Get organization from user
        organization = user.current_organization if hasattr(user, 'current_organization') else None

        # Check if permission already exists
        existing = FieldPermission.objects.filter(
            content_type=content_type,
            field_name=field_name,
            user=user,
            is_deleted=False
        ).first()

        if existing:
            # Update existing permission
            existing.permission_type = permission_type
            existing.mask_rule = mask_rule
            existing.condition = condition
            existing.priority = priority
            existing.description = description
            existing.save()

            # Log the modification
            PermissionAuditLog.log_modify(
                actor=actor,
                permission_details={
                    'type': 'field_permission',
                    'content_type': content_type.model,
                    'field_name': field_name,
                    'permission_type': permission_type,
                },
                content_object=existing
            )

            return existing

        # Create new permission
        permission = FieldPermission(
            user=user,
            content_type=content_type,
            field_name=field_name,
            permission_type=permission_type,
            mask_rule=mask_rule,
            condition=condition,
            priority=priority,
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
                'type': 'field_permission',
                'content_type': content_type.model,
                'field_name': field_name,
                'permission_type': permission_type,
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
        Revoke a field permission.

        Args:
            permission_id: ID of the permission to revoke
            actor: User revoking the permission

        Returns:
            True if successfully revoked

        Raises:
            FieldPermission.DoesNotExist: If permission not found
        """
        permission = FieldPermission.objects.get(id=permission_id, is_deleted=False)

        # Log before revoking
        PermissionAuditLog.log_revoke(
            actor=actor,
            target_user=permission.user,
            permission_details={
                'type': 'field_permission',
                'content_type': permission.content_type.model,
                'field_name': permission.field_name,
                'permission_type': permission.permission_type,
            },
            content_object=permission
        )

        # Soft delete
        permission.soft_delete(user=actor)

        return True

    def revoke_all_for_user(self, user: User, actor: User) -> int:
        """
        Revoke all field permissions for a user.

        Args:
            user: User to revoke permissions from
            actor: User revoking the permissions

        Returns:
            Number of permissions revoked
        """
        permissions = FieldPermission.objects.filter(
            user=user,
            is_deleted=False
        )

        count = 0
        for permission in permissions:
            self.revoke_permission(permission.id, actor)
            count += 1

        return count

    def get_user_permissions(self, user: User, content_type: Optional[ContentType] = None) -> List[FieldPermission]:
        """
        Get all field permissions for a user.

        Args:
            user: User to get permissions for
            content_type: Optional ContentType filter

        Returns:
            List of FieldPermission instances
        """
        queryset = FieldPermission.objects.filter(
            user=user,
            is_deleted=False
        )

        if content_type:
            queryset = queryset.filter(content_type=content_type)

        return queryset.select_related('content_type').order_by('-priority')

    def copy_permissions_to_user(
        self,
        source_user: User,
        target_user: User,
        actor: User
    ) -> int:
        """
        Copy field permissions from one user to another.

        Args:
            source_user: User to copy permissions from
            target_user: User to copy permissions to
            actor: User performing the operation

        Returns:
            Number of permissions copied
        """
        source_permissions = FieldPermission.objects.filter(
            user=source_user,
            is_deleted=False
        )

        count = 0
        for source_perm in source_permissions:
            # Check if target already has this permission
            existing = FieldPermission.objects.filter(
                user=target_user,
                content_type=source_perm.content_type,
                field_name=source_perm.field_name,
                is_deleted=False
            ).first()

            if not existing:
                target_org = target_user.current_organization if hasattr(target_user, 'current_organization') else None
                FieldPermission.objects.create(
                    user=target_user,
                    content_type=source_perm.content_type,
                    field_name=source_perm.field_name,
                    permission_type=source_perm.permission_type,
                    mask_rule=source_perm.mask_rule,
                    condition=source_perm.condition,
                    priority=source_perm.priority,
                    description=source_perm.description,
                    created_by=actor,
                    organization=target_org
                )
                count += 1

        return count

    def get_effective_permissions_dict(
        self,
        user: User,
        content_type: ContentType
    ) -> Dict[str, str]:
        """
        Get effective field permissions for a user as a dictionary.

        Args:
            user: User to get permissions for
            content_type: ContentType to check

        Returns:
            Dictionary mapping field names to permission types
        """
        permissions = {}

        # Get user-specific permissions
        user_perms = FieldPermission.objects.filter(
            user=user,
            content_type=content_type,
            is_deleted=False
        )
        for perm in user_perms:
            permissions[perm.field_name] = perm.permission_type

        return permissions
