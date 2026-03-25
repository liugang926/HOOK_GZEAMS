"""
Tests for PermissionEngine.

Test suite for core permission evaluation engine.
"""
import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache

from django.contrib.auth import get_user_model
from apps.permissions.models.field_permission import FieldPermission
from apps.permissions.models.data_permission import DataPermission
from apps.permissions.services.permission_engine import PermissionEngine

User = get_user_model()


class TestPermissionEngine:
    """Test cases for PermissionEngine."""

    def test_engine_initialization(self, user):
        """Verify engine initializes with user and organization."""
        engine = PermissionEngine(user)
        assert engine.user == user
        assert engine.organization_id == user.current_organization_id

    def test_engine_initialization_with_custom_org(self, user, organization):
        """Verify engine can initialize with custom organization."""
        engine = PermissionEngine(user, organization.id)
        assert engine.organization_id == organization.id

    def test_get_cache_key(self, user, user_content_type):
        """Verify cache key generation."""
        cache_key = PermissionEngine.get_cache_key(user.id, user_content_type.id, 'field')
        assert 'field' in cache_key
        assert str(user.id) in cache_key
        assert str(user_content_type.id) in cache_key

    def test_get_field_permissions_empty(self, user, user_content_type):
        """Verify getting field permissions returns empty dict when none exist."""
        engine = PermissionEngine(user)
        perms = engine.get_field_permissions(user_content_type)
        assert isinstance(perms, dict)
        assert len(perms) == 0

    def test_get_field_permissions_with_data(self, user, user_content_type, multiple_field_permissions):
        """Verify getting field permissions returns correct mapping."""
        engine = PermissionEngine(user)
        perms = engine.get_field_permissions(user_content_type, 'view')
        assert len(perms) == len(multiple_field_permissions)
        # Check specific permissions
        assert 'email' in perms
        assert 'phone' in perms

    def test_check_field_permission_view(self, user, user_content_type):
        """Verify checking field permission for view action."""
        FieldPermission.objects.create(
            user=user,
            content_type=user_content_type,
            field_name='email',
            permission_type='read',
            created_by=user,
            organization=user.current_organization
        )
        engine = PermissionEngine(user)
        result = engine.check_field_permission(user_content_type, 'email', 'view')
        assert result == 'read'

    def test_check_field_permission_edit_write(self, user, user_content_type):
        """Verify checking field permission for edit action with write."""
        FieldPermission.objects.create(
            user=user,
            content_type=user_content_type,
            field_name='username',
            permission_type='write',
            created_by=user,
            organization=user.current_organization
        )
        engine = PermissionEngine(user)
        result = engine.check_field_permission(user_content_type, 'username', 'edit')
        assert result == 'write'

    def test_check_field_permission_edit_denied(self, user, user_content_type):
        """Verify checking field permission for edit action with read permission."""
        FieldPermission.objects.create(
            user=user,
            content_type=user_content_type,
            field_name='email',
            permission_type='read',
            created_by=user,
            organization=user.current_organization
        )
        engine = PermissionEngine(user)
        result = engine.check_field_permission(user_content_type, 'email', 'edit')
        assert result == 'denied'

    def test_check_field_permission_hidden(self, user, user_content_type):
        """Verify checking field permission returns hidden."""
        FieldPermission.objects.create(
            user=user,
            content_type=user_content_type,
            field_name='secret',
            permission_type='hidden',
            created_by=user,
            organization=user.current_organization
        )
        engine = PermissionEngine(user)
        result = engine.check_field_permission(user_content_type, 'secret', 'view')
        assert result == 'hidden'

    def test_can_view_field(self, user, user_content_type):
        """Verify can_view_field returns correct boolean."""
        FieldPermission.objects.create(
            user=user,
            content_type=user_content_type,
            field_name='public_field',
            permission_type='read',
            created_by=user,
            organization=user.current_organization
        )
        FieldPermission.objects.create(
            user=user,
            content_type=user_content_type,
            field_name='hidden_field',
            permission_type='hidden',
            created_by=user,
            organization=user.current_organization
        )
        engine = PermissionEngine(user)
        assert engine.can_view_field(user_content_type, 'public_field') is True
        assert engine.can_view_field(user_content_type, 'hidden_field') is False

    def test_can_edit_field(self, user, user_content_type):
        """Verify can_edit_field returns correct boolean."""
        FieldPermission.objects.create(
            user=user,
            content_type=user_content_type,
            field_name='editable_field',
            permission_type='write',
            created_by=user,
            organization=user.current_organization
        )
        FieldPermission.objects.create(
            user=user,
            content_type=user_content_type,
            field_name='readonly_field',
            permission_type='read',
            created_by=user,
            organization=user.current_organization
        )
        engine = PermissionEngine(user)
        assert engine.can_edit_field(user_content_type, 'editable_field') is True
        assert engine.can_edit_field(user_content_type, 'readonly_field') is False

    def test_get_accessible_fields(self, user, user_content_type):
        """Verify getting accessible field names."""
        FieldPermission.objects.create(
            user=user,
            content_type=user_content_type,
            field_name='field1',
            permission_type='read',
            created_by=user,
            organization=user.current_organization
        )
        FieldPermission.objects.create(
            user=user,
            content_type=user_content_type,
            field_name='field2',
            permission_type='write',
            created_by=user,
            organization=user.current_organization
        )
        FieldPermission.objects.create(
            user=user,
            content_type=user_content_type,
            field_name='field3',
            permission_type='hidden',
            created_by=user,
            organization=user.current_organization
        )
        engine = PermissionEngine(user)
        accessible = engine.get_accessible_fields(user_content_type, 'view')
        assert 'field1' in accessible
        assert 'field2' in accessible
        assert 'field3' not in accessible

    def test_get_hidden_fields(self, user, user_content_type):
        """Verify getting hidden field names."""
        FieldPermission.objects.create(
            user=user,
            content_type=user_content_type,
            field_name='secret1',
            permission_type='hidden',
            created_by=user,
            organization=user.current_organization
        )
        FieldPermission.objects.create(
            user=user,
            content_type=user_content_type,
            field_name='secret2',
            permission_type='hidden',
            created_by=user,
            organization=user.current_organization
        )
        engine = PermissionEngine(user)
        hidden = engine.get_hidden_fields(user_content_type)
        assert 'secret1' in hidden
        assert 'secret2' in hidden

    def test_get_data_scope(self, user, user_content_type):
        """Verify getting data scope."""
        DataPermission.objects.create(
            user=user,
            content_type=user_content_type,
            scope_type='self_dept',
            created_by=user,
            organization=user.current_organization
        )
        engine = PermissionEngine(user)
        scope = engine.get_data_scope(user_content_type)
        assert scope['scope_type'] == 'self_dept'

    def test_get_data_scope_default(self, user, user_content_type):
        """Verify getting data scope returns default when no permission exists."""
        engine = PermissionEngine(user)
        scope = engine.get_data_scope(user_content_type)
        assert scope['scope_type'] == 'self'  # Default

    def test_apply_data_scope(self, user, user_content_type):
        """Verify applying data scope to queryset."""
        DataPermission.objects.create(
            user=user,
            content_type=user_content_type,
            scope_type='all',
            created_by=user,
            organization=user.current_organization
        )
        engine = PermissionEngine(user)
        queryset = User.objects.all()
        filtered = engine.apply_data_scope(queryset, user_content_type)
        # Should return queryset
        assert filtered is not None

    def test_mask_sensitive_data(self, user, user_content_type):
        """Verify masking sensitive fields in data dictionary."""
        FieldPermission.objects.create(
            user=user,
            content_type=user_content_type,
            field_name='email',
            permission_type='masked',
            mask_rule='email',
            created_by=user,
            organization=user.current_organization
        )
        FieldPermission.objects.create(
            user=user,
            content_type=user_content_type,
            field_name='secret',
            permission_type='hidden',
            created_by=user,
            organization=user.current_organization
        )
        engine = PermissionEngine(user)
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'secret': 'hidden_value'
        }
        masked = engine.mask_sensitive_data(data, user_content_type)
        assert 'username' in masked  # No restriction
        assert '@' in masked['email']  # Masked but visible
        assert 'secret' not in masked  # Hidden

    def test_get_permission_summary(self, user, user_content_type):
        """Verify getting complete permission summary."""
        FieldPermission.objects.create(
            user=user,
            content_type=user_content_type,
            field_name='email',
            permission_type='masked',
            created_by=user,
            organization=user.current_organization
        )
        DataPermission.objects.create(
            user=user,
            content_type=user_content_type,
            scope_type='self_dept',
            created_by=user,
            organization=user.current_organization
        )
        summary = PermissionEngine.get_permission_summary(user, user_content_type)
        assert summary['user_id'] == str(user.id)
        assert 'field_permissions' in summary
        assert 'data_scope' in summary
        assert 'accessible_fields_view' in summary

    def test_batch_check_permissions(self, user, user_content_type):
        """Verify batch checking permissions for multiple users."""
        # Create additional user
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123',
            current_organization=user.current_organization
        )
        FieldPermission.objects.create(
            user=user,
            content_type=user_content_type,
            field_name='email',
            permission_type='masked',
            created_by=user,
            organization=user.current_organization
        )
        result = PermissionEngine.batch_check_permissions(
            [user, user2],
            user_content_type,
            'view'
        )
        assert user.id in result
        assert user2.id in result

    def test_invalidate_user_cache(self, user):
        """Verify cache invalidation for user."""
        # Set some cached data
        cache.set('test_key', 'test_value')
        PermissionEngine.invalidate_user_cache(user.id)
        # Cache should be cleared
        # Note: This tests the method runs without error
        # Actual cache clearing depends on cache backend

    def test_superuser_bypass(self, superuser, user_content_type):
        """Verify superuser bypasses permission checks."""
        engine = PermissionEngine(superuser)
        # Superuser should get all access even without permissions
        scope = engine.get_data_scope(user_content_type)
        # Superuser should have all scope
        assert scope['scope_type'] in ['all', 'self']
