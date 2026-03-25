"""
PermissionEngine - Core permission evaluation engine.

Central service for checking and applying field-level and data-level permissions.
Uses caching for performance optimization.
"""
from typing import Dict, List, Set, Any, Optional
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import Q, QuerySet
from django.conf import settings

from apps.permissions.models import (
    FieldPermission,
    DataPermission,
    DataPermissionExpand,
    PermissionAuditLog,
)

User = get_user_model()

# Cache timeout in seconds (default 5 minutes)
CACHE_TIMEOUT = getattr(settings, 'PERMISSION_CACHE_TIMEOUT', 300)


class PermissionEngine:
    """
    Core permission evaluation engine.

    Provides methods for:
    - Checking field-level permissions (read/write/hidden/masked)
    - Applying data-level filters to querysets
    - Masking sensitive field values
    - Caching permission results for performance
    """

    def __init__(self, user: User, organization_id: Optional[int] = None):
        """
        Initialize permission engine for a user.

        Args:
            user: User instance to evaluate permissions for
            organization_id: Organization ID (optional, defaults to user's org)
        """
        self.user = user
        # Try to get organization_id from various possible attributes
        self.organization_id = organization_id or getattr(user, 'current_organization_id', None) or getattr(user, 'organization_id', None)

        # Cache for this instance
        self._field_permissions_cache: Dict[str, Dict[str, str]] = {}
        self._data_permissions_cache: Dict[str, Any] = {}

    @staticmethod
    def get_cache_key(user_id: int, content_type_id: int, permission_type: str) -> str:
        """
        Generate cache key for permission data.

        Args:
            user_id: User ID
            content_type_id: ContentType ID
            permission_type: Type of permission ('field' or 'data')

        Returns:
            Cache key string
        """
        return f'perm:{permission_type}:{user_id}:{content_type_id}'

    @staticmethod
    def invalidate_user_cache(user_id: int):
        """
        Invalidate all cached permissions for a user.

        Args:
            user_id: User ID to invalidate cache for
        """
        # Delete all permission cache keys for this user
        # In production with Redis, use pattern matching or scan
        keys_to_delete = []
        for content_type in ContentType.objects.all():
            keys_to_delete.append(PermissionEngine.get_cache_key(user_id, content_type.id, 'field'))
            keys_to_delete.append(PermissionEngine.get_cache_key(user_id, content_type.id, 'data'))

        cache.delete_many(keys_to_delete)

    def get_field_permissions(self, content_type: ContentType, action: str = 'view') -> Dict[str, str]:
        """
        Get field permissions for a content type.

        Returns a dict mapping field names to permission types.

        Args:
            content_type: ContentType to get permissions for
            action: Action being performed ('view' or 'edit')

        Returns:
            Dict of {field_name: permission_type}
            Permission types: 'read', 'write', 'hidden', 'masked'
        """
        cache_key = self.get_cache_key(self.user.id, content_type.id, 'field')

        # Check cache first
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        # Get user-specific permissions
        field_perms = {}
        user_perms = FieldPermission.objects.filter(
            user=self.user,
            content_type=content_type,
            is_deleted=False
        )
        for perm in user_perms:
            field_perms[perm.field_name] = perm.permission_type

        # Store in cache
        cache.set(cache_key, field_perms, CACHE_TIMEOUT)

        return field_perms

    def check_field_permission(self, content_type: ContentType, field_name: str, action: str = 'view') -> str:
        """
        Check permission for a specific field.

        Args:
            content_type: ContentType of the model
            field_name: Name of the field to check
            action: Action being performed ('view' or 'edit')

        Returns:
            Permission type: 'read', 'write', 'hidden', 'masked', or None (no restriction)
        """
        field_perms = self.get_field_permissions(content_type, action)

        permission = field_perms.get(field_name)

        # Map permission type to action check
        if action == 'view':
            # For viewing: read and write are allowed, masked is allowed with masking
            if permission in ('read', 'write', None):
                return 'read'
            elif permission == 'masked':
                return 'masked'
            else:  # hidden
                return 'hidden'

        elif action == 'edit':
            # For editing: only write is allowed
            if permission == 'write':
                return 'write'
            else:
                return 'denied'

        return permission or 'read'

    def apply_field_permissions(self, data: List[Dict], content_type: ContentType, action: str = 'view') -> List[Dict]:
        """
        Apply field permissions to a list of records.

        Filters out hidden fields and masks sensitive data.

        Args:
            data: List of record dictionaries
            content_type: ContentType of the records
            action: Action being performed ('view' or 'edit')

        Returns:
            Filtered list of records with permissions applied
        """
        field_perms = self.get_field_permissions(content_type, action)

        result = []
        for record in data:
            filtered_record = {}
            for field_name, value in record.items():
                perm = field_perms.get(field_name)

                if perm == 'hidden':
                    continue  # Skip this field

                elif perm == 'masked' and value is not None:
                    # Apply masking
                    masked_perm = FieldPermission.objects.filter(
                        content_type=content_type,
                        field_name=field_name,
                        is_deleted=False
                    ).first()

                    if masked_perm and masked_perm.mask_rule:
                        filtered_record[field_name] = masked_perm.apply_mask(value)
                    else:
                        filtered_record[field_name] = '***'
                else:
                    # Include field as-is (read or write permission, or no restriction)
                    filtered_record[field_name] = value

            result.append(filtered_record)

        return result

    def get_data_scope(self, content_type: ContentType) -> Dict[str, Any]:
        """
        Get data scope for a content type.

        Returns scope configuration for filtering querysets.

        Args:
            content_type: ContentType to get scope for

        Returns:
            Dict with keys: scope_type, scope_value, department_field, user_field
        """
        cache_key = self.get_cache_key(self.user.id, content_type.id, 'data')

        # Check cache first
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        # Get effective data permission
        perm = DataPermission.get_effective_permission(self.user, content_type)

        scope_config = {
            'scope_type': perm.scope_type if hasattr(perm, 'scope_type') else 'self',
            'department_field': getattr(perm, 'department_field', 'department'),
            'user_field': getattr(perm, 'user_field', 'created_by'),
        }

        if hasattr(perm, 'scope_value'):
            scope_config['scope_value'] = perm.scope_value

        # Store in cache
        cache.set(cache_key, scope_config, CACHE_TIMEOUT)

        return scope_config

    def apply_data_scope(self, queryset: QuerySet, content_type: ContentType) -> QuerySet:
        """
        Apply data scope filtering to a queryset.

        Args:
            queryset: QuerySet to filter
            content_type: ContentType of the model

        Returns:
            Filtered QuerySet
        """
        # Get effective data permission
        perm = DataPermission.get_effective_permission(self.user, content_type)

        if hasattr(perm, 'apply_to_queryset'):
            return perm.apply_to_queryset(queryset, self.user)

        # Default behavior: own data only
        return queryset.filter(created_by=self.user)

    def get_viewable_department_ids(self, content_type: ContentType) -> Set[int]:
        """
        Get department IDs the user can view data from.

        Args:
            content_type: ContentType to check permissions for

        Returns:
            Set of department IDs
        """
        scope = self.get_data_scope(content_type)

        if scope['scope_type'] == 'all':
            return None  # No restriction

        elif scope['scope_type'] == 'self':
            return set()  # Own data only

        elif scope['scope_type'] in ('self_dept', 'self_and_sub'):
            # Get user's primary department
            from apps.organizations.models import UserDepartment
            user_dept = UserDepartment.objects.filter(
                user=self.user,
                is_primary=True,
                is_deleted=False
            ).first()

            if not user_dept:
                return set()

            dept_ids = {user_dept.department_id}

            if scope['scope_type'] == 'self_and_sub':
                # Add descendant departments
                descendants = user_dept.department.get_descendants()
                dept_ids.update(d.id for d in descendants)

            return dept_ids

        elif scope['scope_type'] == 'specified':
            return set(scope.get('scope_value', {}).get('department_ids', []))

        return set()

    def can_view_field(self, content_type: ContentType, field_name: str) -> bool:
        """
        Check if user can view a field.

        Args:
            content_type: ContentType of the model
            field_name: Name of the field

        Returns:
            True if field is visible (not hidden)
        """
        permission = self.check_field_permission(content_type, field_name, 'view')
        return permission != 'hidden'

    def can_edit_field(self, content_type: ContentType, field_name: str) -> bool:
        """
        Check if user can edit a field.

        Args:
            content_type: ContentType of the model
            field_name: Name of the field

        Returns:
            True if field is editable
        """
        permission = self.check_field_permission(content_type, field_name, 'edit')
        return permission == 'write'

    def mask_sensitive_data(self, data: Dict, content_type: ContentType) -> Dict:
        """
        Mask sensitive fields in a data dictionary.

        Args:
            data: Dictionary of field-value pairs
            content_type: ContentType of the model

        Returns:
            Dictionary with sensitive fields masked
        """
        field_perms = self.get_field_permissions(content_type, 'view')

        result = {}
        for field_name, value in data.items():
            perm = field_perms.get(field_name)

            if perm == 'masked' and value is not None:
                # Apply masking
                masked_perm = FieldPermission.objects.filter(
                    content_type=content_type,
                    field_name=field_name,
                    is_deleted=False
                ).first()

                if masked_perm:
                    result[field_name] = masked_perm.apply_mask(value)
                else:
                    result[field_name] = '***'
            elif perm == 'hidden':
                # Skip hidden fields
                continue
            else:
                result[field_name] = value

        return result

    def get_accessible_fields(self, content_type: ContentType, action: str = 'view') -> List[str]:
        """
        Get list of accessible field names for a content type.

        Args:
            content_type: ContentType to check
            action: Action being performed

        Returns:
            List of accessible field names
        """
        field_perms = self.get_field_permissions(content_type, action)

        accessible = []
        for field_name, perm in field_perms.items():
            if action == 'view':
                if perm in ('read', 'write', 'masked'):
                    accessible.append(field_name)
            elif action == 'edit':
                if perm == 'write':
                    accessible.append(field_name)

        return accessible

    def get_hidden_fields(self, content_type: ContentType) -> List[str]:
        """
        Get list of hidden field names for a content type.

        Args:
            content_type: ContentType to check

        Returns:
            List of hidden field names
        """
        field_perms = self.get_field_permissions(content_type, 'view')

        return [field for field, perm in field_perms.items() if perm == 'hidden']

    def get_masked_fields(self, content_type: ContentType) -> Dict[str, str]:
        """
        Get list of masked field names with their mask rules.

        Args:
            content_type: ContentType to check

        Returns:
            Dict of {field_name: mask_rule}
        """
        field_perms = self.get_field_permissions(content_type, 'view')

        masked = {}
        for field_name, perm in field_perms.items():
            if perm == 'masked':
                perm_obj = FieldPermission.objects.filter(
                    content_type=content_type,
                    field_name=field_name,
                    is_deleted=False
                ).first()
                if perm_obj:
                    masked[field_name] = perm_obj.mask_rule or 'default'

        return masked

    @classmethod
    def batch_check_permissions(cls, users: List[User], content_type: ContentType,
                                action: str = 'view') -> Dict[int, Dict[str, str]]:
        """
        Batch check permissions for multiple users.

        Args:
            users: List of User instances
            content_type: ContentType to check
            action: Action being performed

        Returns:
            Dict mapping user_id to their field permissions
        """
        result = {}

        for user in users:
            engine = cls(user)
            result[user.id] = engine.get_field_permissions(content_type, action)

        return result

    @classmethod
    def get_permission_summary(cls, user: User, content_type: ContentType) -> Dict[str, Any]:
        """
        Get a complete permission summary for a user and content type.

        Args:
            user: User instance
            content_type: ContentType to summarize

        Returns:
            Dict with field permissions, data scope, and other metadata
        """
        engine = cls(user)

        return {
            'user_id': str(user.id),
            'content_type': content_type.model,
            'field_permissions': engine.get_field_permissions(content_type),
            'data_scope': engine.get_data_scope(content_type),
            'accessible_fields_view': engine.get_accessible_fields(content_type, 'view'),
            'accessible_fields_edit': engine.get_accessible_fields(content_type, 'edit'),
            'hidden_fields': engine.get_hidden_fields(content_type),
            'masked_fields': engine.get_masked_fields(content_type),
        }

    def log_permission_check(self, target_type: str, permission_details: Dict,
                             result: str = 'success', **kwargs):
        """
        Log a permission check to the audit log.

        Args:
            target_type: Type of permission being checked
            permission_details: Details about the permission
            result: Result of the check
            **kwargs: Additional audit log fields
        """
        PermissionAuditLog.log_check(
            user=self.user,
            target_type=target_type,
            permission_details=permission_details,
            result=result,
            organization_id=self.organization_id,
            **kwargs
        )
