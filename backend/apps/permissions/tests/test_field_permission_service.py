"""
Tests for FieldPermissionService.

Test suite for field-level permission service operations.
"""
import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from django.contrib.auth import get_user_model
from apps.permissions.models.field_permission import FieldPermission
from apps.permissions.models.permission_audit_log import PermissionAuditLog
from apps.permissions.services.field_permission_service import FieldPermissionService

User = get_user_model()


class TestFieldPermissionService:
    """Test cases for FieldPermissionService."""

    def test_service_initialization(self):
        """Verify service initializes with FieldPermission model."""
        service = FieldPermissionService()
        assert service.model_class == FieldPermission

    def test_grant_permission_create_new(self, user, user_content_type):
        """Verify granting permission creates new record."""
        service = FieldPermissionService()
        perm = service.grant_permission(
            user=user,
            content_type=user_content_type,
            field_name='phone',
            permission_type='masked',
            mask_rule='phone',
            actor=user,
            description='Mask phone number'
        )
        assert perm.id is not None
        assert perm.field_name == 'phone'
        assert perm.permission_type == 'masked'

    def test_grant_permission_update_existing(self, user, user_content_type):
        """Verify granting permission updates existing record."""
        service = FieldPermissionService()
        # Create initial permission
        service.grant_permission(
            user=user,
            content_type=user_content_type,
            field_name='email',
            permission_type='read',
            actor=user
        )
        # Update to masked
        perm = service.grant_permission(
            user=user,
            content_type=user_content_type,
            field_name='email',
            permission_type='masked',
            mask_rule='email',
            actor=user
        )
        assert perm.permission_type == 'masked'
        assert perm.mask_rule == 'email'

    def test_grant_permission_creates_audit_log(self, user, user_content_type):
        """Verify granting permission creates audit log."""
        service = FieldPermissionService()
        initial_log_count = PermissionAuditLog.objects.count()
        service.grant_permission(
            user=user,
            content_type=user_content_type,
            field_name='test',
            permission_type='hidden',
            actor=user
        )
        assert PermissionAuditLog.objects.count() == initial_log_count + 1
        log = PermissionAuditLog.objects.latest('created_at')
        assert log.operation_type == 'grant'

    def test_revoke_permission(self, field_permission, user):
        """Verify revoking permission soft deletes record."""
        service = FieldPermissionService()
        perm_id = field_permission.id
        result = service.revoke_permission(perm_id, user)
        assert result is True
        # Should be soft deleted
        assert not FieldPermission.objects.filter(id=perm_id, is_deleted=False).exists()

    def test_revoke_permission_creates_audit_log(self, field_permission, user):
        """Verify revoking permission creates audit log."""
        service = FieldPermissionService()
        initial_log_count = PermissionAuditLog.objects.count()
        service.revoke_permission(field_permission.id, user)
        assert PermissionAuditLog.objects.count() == initial_log_count + 1
        log = PermissionAuditLog.objects.latest('created_at')
        assert log.operation_type == 'revoke'

    def test_revoke_all_for_user(self, user, user_content_type, multiple_field_permissions):
        """Verify revoking all permissions for a user."""
        service = FieldPermissionService()
        initial_count = FieldPermission.objects.filter(user=user, is_deleted=False).count()
        count = service.revoke_all_for_user(user, user)
        assert count == initial_count
        assert FieldPermission.objects.filter(user=user, is_deleted=False).count() == 0

    def test_get_user_permissions(self, user, user_content_type, multiple_field_permissions):
        """Verify getting all permissions for a user."""
        service = FieldPermissionService()
        permissions = service.get_user_permissions(user, user_content_type)
        assert len(permissions) == len(multiple_field_permissions)
        assert all(p.user == user for p in permissions)

    def test_get_effective_permissions_dict(self, user, user_content_type):
        """Verify getting effective permissions as dictionary."""
        service = FieldPermissionService()
        # Create multiple permissions for different fields
        service.grant_permission(user, user_content_type, 'email', 'masked', actor=user, mask_rule='email')
        service.grant_permission(user, user_content_type, 'phone', 'hidden', actor=user)
        service.grant_permission(user, user_content_type, 'name', 'read', actor=user)

        perms_dict = service.get_effective_permissions_dict(user, user_content_type)
        assert perms_dict['email'] == 'masked'
        assert perms_dict['phone'] == 'hidden'
        assert perms_dict['name'] == 'read'

    def test_copy_permissions_to_user(self, user, user_content_type, multiple_field_permissions):
        """Verify copying permissions from one user to another."""
        service = FieldPermissionService()
        # Create target user
        target_user = User.objects.create_user(
            username='targetuser',
            email='target@example.com',
            password='testpass123',
            current_organization=user.current_organization
        )
        initial_target_count = FieldPermission.objects.filter(user=target_user).count()
        count = service.copy_permissions_to_user(user, target_user, user)
        assert count == len(multiple_field_permissions)
        assert FieldPermission.objects.filter(user=target_user).count() == initial_target_count + count

    def test_copy_permissions_skips_existing(self, user, user_content_type):
        """Verify copying skips permissions that already exist."""
        service = FieldPermissionService()
        # Create source permission
        service.grant_permission(user, user_content_type, 'email', 'masked', actor=user)
        # Create target user with same permission
        target_user = User.objects.create_user(
            username='targetuser2',
            email='target2@example.com',
            password='testpass123',
            current_organization=user.current_organization
        )
        service.grant_permission(target_user, user_content_type, 'email', 'read', actor=user)
        # Copy should skip email permission
        count = service.copy_permissions_to_user(user, target_user, user)
        assert count == 0  # Email already exists, so not copied

    def test_grant_permission_with_condition(self, user, user_content_type):
        """Verify granting permission with condition."""
        service = FieldPermissionService()
        condition = {'status': 'active'}
        perm = service.grant_permission(
            user=user,
            content_type=user_content_type,
            field_name='salary',
            permission_type='masked',
            actor=user,
            condition=condition
        )
        assert perm.condition == condition

    def test_grant_permission_with_priority(self, user, user_content_type):
        """Verify granting permission with priority."""
        service = FieldPermissionService()
        perm = service.grant_permission(
            user=user,
            content_type=user_content_type,
            field_name='sensitive_data',
            permission_type='hidden',
            actor=user,
            priority=100
        )
        assert perm.priority == 100

    def test_get_user_permissions_filters_by_content_type(self, user, user_content_type):
        """Verify getting permissions filters by content type."""
        service = FieldPermissionService()
        # Create permission for User model
        service.grant_permission(user, user_content_type, 'email', 'masked', actor=user)
        # Create permission for different model
        org_ct = ContentType.objects.get(app_label='organizations', model='organization')
        service.grant_permission(user, org_ct, 'name', 'read', actor=user)
        # Get only User permissions
        user_perms = service.get_user_permissions(user, user_content_type)
        assert all(p.content_type == user_content_type for p in user_perms)
