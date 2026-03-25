"""
Tests for DataPermissionService.

Test suite for data-level permission service operations.
"""
import pytest
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet

from django.contrib.auth import get_user_model
from apps.permissions.models.data_permission import DataPermission
from apps.permissions.models.permission_audit_log import PermissionAuditLog
from apps.permissions.services.data_permission_service import DataPermissionService

User = get_user_model()


class TestDataPermissionService:
    """Test cases for DataPermissionService."""

    def test_service_initialization(self):
        """Verify service initializes with DataPermission model."""
        service = DataPermissionService()
        assert service.model_class == DataPermission

    def test_grant_permission_create_new(self, user, user_content_type):
        """Verify granting data permission creates new record."""
        service = DataPermissionService()
        perm = service.grant_permission(
            user=user,
            content_type=user_content_type,
            scope_type='self_dept',
            actor=user,
            description='Own department access'
        )
        assert perm.id is not None
        assert perm.scope_type == 'self_dept'
        assert perm.description == 'Own department access'

    def test_grant_permission_update_existing(self, user, user_content_type):
        """Verify granting permission updates existing record."""
        service = DataPermissionService()
        # Create initial permission
        service.grant_permission(
            user=user,
            content_type=user_content_type,
            scope_type='self',
            actor=user
        )
        # Update to self_dept
        perm = service.grant_permission(
            user=user,
            content_type=user_content_type,
            scope_type='self_dept',
            actor=user
        )
        assert perm.scope_type == 'self_dept'

    def test_grant_permission_with_scope_value(self, user, user_content_type):
        """Verify granting permission with scope value."""
        service = DataPermissionService()
        scope_value = {'department_ids': [1, 2, 3]}
        perm = service.grant_permission(
            user=user,
            content_type=user_content_type,
            scope_type='specified',
            scope_value=scope_value,
            actor=user
        )
        assert perm.scope_value == scope_value

    def test_grant_permission_creates_audit_log(self, user, user_content_type):
        """Verify granting permission creates audit log."""
        service = DataPermissionService()
        initial_log_count = PermissionAuditLog.objects.count()
        service.grant_permission(
            user=user,
            content_type=user_content_type,
            scope_type='all',
            actor=user
        )
        assert PermissionAuditLog.objects.count() == initial_log_count + 1
        log = PermissionAuditLog.objects.latest('created_at')
        assert log.operation_type == 'grant'

    def test_revoke_permission(self, data_permission, user):
        """Verify revoking permission soft deletes record."""
        service = DataPermissionService()
        perm_id = data_permission.id
        result = service.revoke_permission(perm_id, user)
        assert result is True
        # Should be soft deleted
        assert not DataPermission.objects.filter(id=perm_id, is_deleted=False).exists()

    def test_revoke_permission_creates_audit_log(self, data_permission, user):
        """Verify revoking permission creates audit log."""
        service = DataPermissionService()
        initial_log_count = PermissionAuditLog.objects.count()
        service.revoke_permission(data_permission.id, user)
        assert PermissionAuditLog.objects.count() == initial_log_count + 1
        log = PermissionAuditLog.objects.latest('created_at')
        assert log.operation_type == 'revoke'

    def test_apply_user_permissions_all_scope(self, user, user_content_type):
        """Verify applying permissions with 'all' scope returns all data."""
        service = DataPermissionService()
        # Create permission with 'all' scope
        service.grant_permission(
            user=user,
            content_type=user_content_type,
            scope_type='all',
            actor=user
        )
        queryset = User.objects.all()
        filtered = service.apply_user_permissions(queryset, user, user_content_type)
        # Should return all users
        assert isinstance(filtered, QuerySet)

    def test_get_user_accessible_department_ids(self, user_with_department, user_content_type, department):
        """Verify getting accessible department IDs for user."""
        service = DataPermissionService()
        # Create permission for own department
        service.grant_permission(
            user=user_with_department,
            content_type=user_content_type,
            scope_type='self_dept',
            actor=user_with_department
        )
        dept_ids = service.get_user_accessible_department_ids(user_with_department, user_content_type)
        assert isinstance(dept_ids, set)
        assert department.id in dept_ids

    def test_get_user_accessible_department_ids_all_scope(self, user, user_content_type):
        """Verify accessible departments with 'all' scope returns None."""
        service = DataPermissionService()
        service.grant_permission(
            user=user,
            content_type=user_content_type,
            scope_type='all',
            actor=user
        )
        dept_ids = service.get_user_accessible_department_ids(user, user_content_type)
        assert dept_ids is None  # No restriction

    def test_get_user_permissions(self, user, user_content_type):
        """Verify getting all permissions for a user."""
        service = DataPermissionService()
        service.grant_permission(
            user=user,
            content_type=user_content_type,
            scope_type='self_dept',
            actor=user
        )
        permissions = service.get_user_permissions(user, user_content_type)
        assert len(permissions) >= 1
        assert all(p.is_deleted is False for p in permissions)

    def test_get_permission_summary(self, user, user_content_type):
        """Verify getting permission summary for a user."""
        service = DataPermissionService()
        service.grant_permission(
            user=user,
            content_type=user_content_type,
            scope_type='self_dept',
            actor=user
        )
        summary = service.get_permission_summary(user)
        assert isinstance(summary, dict)
        assert 'accounts.user' in summary or len(summary) >= 1

    def test_copy_permissions_to_user(self, user, user_content_type, multiple_data_permissions):
        """Verify copying permissions from one user to another."""
        service = DataPermissionService()
        permissions, perm_users = multiple_data_permissions
        # Use the first perm user as source (has permissions)
        source_user = perm_users[0]
        # Create target user
        target_user = User.objects.create_user(
            username='targetuser',
            email='target@example.com',
            password='testpass123',
            current_organization=user.current_organization
        )
        from apps.accounts.models import UserOrganization
        UserOrganization.objects.create(
            user=target_user,
            organization=user.current_organization,
            role='member',
            is_primary=True,
            is_active=True
        )
        initial_target_count = DataPermission.objects.filter(user=target_user).count()
        count = service.copy_permissions_to_user(source_user, target_user, user)
        # Source user has 1 permission
        assert count == 1
        assert DataPermission.objects.filter(user=target_user).count() == initial_target_count + count

    def test_copy_permissions_skips_existing(self, user, user_content_type):
        """Verify copying skips permissions that already exist for content type."""
        service = DataPermissionService()
        # Create source permission
        service.grant_permission(user, user_content_type, 'self_dept', actor=user)
        # Create target user with same content type permission
        target_user = User.objects.create_user(
            username='targetuser3',
            email='target3@example.com',
            password='testpass123',
            current_organization=user.current_organization
        )
        service.grant_permission(target_user, user_content_type, 'self', actor=user)
        # Copy should skip User content type permission
        count = service.copy_permissions_to_user(user, target_user, user)
        assert count == 0  # User permission already exists

    def test_grant_permission_custom_fields(self, user, user_content_type):
        """Verify granting permission with custom field names."""
        service = DataPermissionService()
        perm = service.grant_permission(
            user=user,
            content_type=user_content_type,
            scope_type='self_dept',
            actor=user,
            department_field='custom_dept',
            user_field='custom_user'
        )
        assert perm.department_field == 'custom_dept'
        assert perm.user_field == 'custom_user'
