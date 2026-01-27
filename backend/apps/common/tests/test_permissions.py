"""
Tests for permission classes.
"""
import pytest
from unittest.mock import Mock, patch
from rest_framework import permissions


class TestBasePermission:
    """Test BasePermission class."""

    def test_allows_options_requests(self):
        """Test that OPTIONS requests are always allowed."""
        from apps.common.permissions.base import BasePermission

        permission = BasePermission()

        request = Mock()
        request.method = 'OPTIONS'
        request.user = None

        view = Mock()

        assert permission.has_permission(request, view) is True

    def test_requires_authentication(self):
        """Test that unauthenticated requests are denied."""
        from apps.common.permissions.base import BasePermission

        permission = BasePermission()

        request = Mock()
        request.method = 'GET'
        request.user = None

        view = Mock()

        assert permission.has_permission(request, view) is False

    def test_allows_authenticated_users(self, db, user):
        """Test that authenticated users are allowed."""
        from apps.common.permissions.base import BasePermission

        permission = BasePermission()

        request = Mock()
        request.method = 'GET'
        request.user = user
        request.organization_id = None

        view = Mock()

        assert permission.has_permission(request, view) is True

    def test_superuser_always_allowed(self, db, superuser):
        """Test that superusers always have permission."""
        from apps.common.permissions.base import BasePermission

        permission = BasePermission()

        request = Mock()
        request.method = 'DELETE'
        request.user = superuser
        request.organization_id = None

        view = Mock()

        assert permission.has_permission(request, view) is True


class TestBasePermissionObjectLevel:
    """Test BasePermission object-level permissions."""

    def test_superuser_object_access(self, db, superuser, organization):
        """Test superuser has object-level access."""
        from apps.common.permissions.base import BasePermission
        from apps.organizations.models import Department

        dept = Department.objects.create(
            name='Test',
            code='TEST',
            organization=organization
        )

        permission = BasePermission()

        request = Mock()
        request.user = superuser
        request.organization_id = str(organization.id)

        view = Mock()

        assert permission.has_object_permission(request, view, dept) is True

    def test_denies_cross_org_access(self, db, user, organization, second_organization):
        """Test that cross-organization access is denied."""
        from apps.common.permissions.base import BasePermission
        from apps.organizations.models import Department

        # Department in different organization
        dept = Department.objects.create(
            name='Other Dept',
            code='OTHER',
            organization=second_organization
        )

        permission = BasePermission()

        request = Mock()
        request.user = user
        request.organization_id = str(organization.id)
        request.method = 'GET'

        view = Mock()

        assert permission.has_object_permission(request, view, dept) is False

    def test_allows_read_operations(self, db, user, organization):
        """Test that read operations are allowed for org members."""
        from apps.common.permissions.base import BasePermission
        from apps.organizations.models import Department

        dept = Department.objects.create(
            name='Read Test',
            code='READ_TEST',
            organization=organization
        )

        permission = BasePermission()

        request = Mock()
        request.user = user
        request.organization_id = str(organization.id)
        request.method = 'GET'

        view = Mock()

        assert permission.has_object_permission(request, view, dept) is True


class TestIsAdminOrReadOnly:
    """Test IsAdminOrReadOnly permission."""

    def test_allows_read_for_anyone(self, db, user):
        """Test that read access is allowed for any authenticated user."""
        from apps.common.permissions.base import IsAdminOrReadOnly

        permission = IsAdminOrReadOnly()

        request = Mock()
        request.method = 'GET'
        request.user = user

        view = Mock()

        assert permission.has_permission(request, view) is True

    def test_denies_write_for_non_admin(self, db, user):
        """Test that write access is denied for non-admin users."""
        from apps.common.permissions.base import IsAdminOrReadOnly

        permission = IsAdminOrReadOnly()

        request = Mock()
        request.method = 'POST'
        request.user = user

        view = Mock()

        assert permission.has_permission(request, view) is False

    def test_allows_write_for_admin(self, db, admin_user):
        """Test that write access is allowed for admin users."""
        from apps.common.permissions.base import IsAdminOrReadOnly

        permission = IsAdminOrReadOnly()

        request = Mock()
        request.method = 'POST'
        request.user = admin_user

        view = Mock()

        assert permission.has_permission(request, view) is True


class TestIsOwnerOrReadOnly:
    """Test IsOwnerOrReadOnly permission."""

    def test_allows_read_for_non_owners(self, db, user, organization):
        """Test that read access is allowed for non-owners."""
        from apps.common.permissions.base import IsOwnerOrReadOnly
        from apps.organizations.models import Department

        dept = Department.objects.create(
            name='Owner Test',
            code='OWNER_TEST',
            organization=organization
        )

        permission = IsOwnerOrReadOnly()

        request = Mock()
        request.user = user
        request.method = 'GET'

        view = Mock()

        assert permission.has_object_permission(request, view, dept) is True

    def test_allows_write_for_owner(self, db, user, organization):
        """Test that write access is allowed for owner."""
        from apps.common.permissions.base import IsOwnerOrReadOnly
        from apps.organizations.models import Department

        dept = Department.objects.create(
            name='Owner Write Test',
            code='OWNER_WRITE',
            organization=organization,
            created_by=user
        )

        permission = IsOwnerOrReadOnly()

        request = Mock()
        request.user = user
        request.method = 'PUT'

        view = Mock()

        assert permission.has_object_permission(request, view, dept) is True


class TestIsOrganizationMember:
    """Test IsOrganizationMember permission."""

    def test_requires_authentication(self):
        """Test that authentication is required."""
        from apps.common.permissions.base import IsOrganizationMember

        permission = IsOrganizationMember()

        request = Mock()
        request.user = None

        view = Mock()

        assert permission.has_permission(request, view) is False

    def test_allows_member(self, db, user, organization):
        """Test that organization members are allowed."""
        from apps.common.permissions.base import IsOrganizationMember

        permission = IsOrganizationMember()

        request = Mock()
        request.user = user
        request.organization_id = str(organization.id)

        view = Mock()

        assert permission.has_permission(request, view) is True

    def test_denies_non_member(self, db, user, second_organization):
        """Test that non-members are denied."""
        from apps.common.permissions.base import IsOrganizationMember

        permission = IsOrganizationMember()

        request = Mock()
        request.user = user
        request.organization_id = str(second_organization.id)

        view = Mock()

        assert permission.has_permission(request, view) is False


class TestAllowOptionsPermission:
    """Test AllowOptionsPermission."""

    def test_allows_options(self):
        """Test that OPTIONS requests are allowed."""
        from apps.common.permissions.base import AllowOptionsPermission

        permission = AllowOptionsPermission()

        request = Mock()
        request.method = 'OPTIONS'

        view = Mock()

        assert permission.has_permission(request, view) is True

    def test_denies_other_methods(self):
        """Test that other methods are denied."""
        from apps.common.permissions.base import AllowOptionsPermission

        permission = AllowOptionsPermission()

        for method in ['GET', 'POST', 'PUT', 'DELETE']:
            request = Mock()
            request.method = method

            view = Mock()

            assert permission.has_permission(request, view) is False
