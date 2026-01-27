"""
Pytest configuration and fixtures for Permissions module tests.

This module provides reusable fixtures for testing permissions functionality.
"""
import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Configure Django settings before any Django imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')

import django
django.setup()

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient

from apps.organizations.models import Organization, Department, UserDepartment
from apps.permissions.models.field_permission import FieldPermission
from apps.permissions.models.data_permission import DataPermission
from apps.permissions.models.permission_audit_log import PermissionAuditLog
from apps.accounts.models import UserOrganization

User = get_user_model()


@pytest.fixture
def organization(db):
    """Create a test organization."""
    org = Organization.objects.create(
        name='Test Organization',
        code='TEST_ORG',
        is_active=True
    )
    return org


@pytest.fixture
def department(db, organization):
    """Create a test department."""
    dept = Department.objects.create(
        organization=organization,
        name='Test Department',
        code='TEST_DEPT',
        parent=None,
        is_active=True
    )
    return dept


@pytest.fixture
def user(db, organization):
    """Create a test user with organization membership."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        current_organization=organization
    )
    UserOrganization.objects.create(
        user=user,
        organization=organization,
        role='member',
        is_primary=True,
        is_active=True
    )
    return user


@pytest.fixture
def admin_user(db, organization):
    """Create a test admin user with organization membership."""
    admin = User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='adminpass123',
        is_staff=True,
        current_organization=organization
    )
    UserOrganization.objects.create(
        user=admin,
        organization=organization,
        role='admin',
        is_primary=True,
        is_active=True
    )
    return admin


@pytest.fixture
def superuser(db, organization):
    """Create a superuser for testing admin bypass."""
    su = User.objects.create_superuser(
        username='superuser',
        email='super@example.com',
        password='superpass123',
        current_organization=organization
    )
    UserOrganization.objects.create(
        user=su,
        organization=organization,
        role='admin',
        is_primary=True,
        is_active=True
    )
    return su


@pytest.fixture
def user_with_department(db, organization, department):
    """Create a user with department membership."""
    user = User.objects.create_user(
        username='deptuser',
        email='dept@example.com',
        password='deptpass123',
        current_organization=organization
    )
    UserOrganization.objects.create(
        user=user,
        organization=organization,
        role='member',
        is_primary=True,
        is_active=True
    )
    UserDepartment.objects.create(
        user=user,
        department=department,
        is_primary=True,
        organization=organization
    )
    return user


@pytest.fixture
def user_content_type(db):
    """Get ContentType for User model."""
    return ContentType.objects.get_for_model(User)


@pytest.fixture
def field_permission(db, user, user_content_type):
    """Create a test field permission."""
    perm = FieldPermission.objects.create(
        user=user,
        content_type=user_content_type,
        field_name='email',
        permission_type='masked',
        mask_rule='email',
        priority=0,
        description='Mask email field for privacy',
        created_by=user,
        organization=user.current_organization
    )
    return perm


@pytest.fixture
def data_permission(db, user, user_content_type):
    """Create a test data permission."""
    perm = DataPermission.objects.create(
        user=user,
        content_type=user_content_type,
        scope_type='self_dept',
        department_field='department',
        user_field='created_by',
        description='Allow access to own department data',
        created_by=user,
        organization=user.current_organization
    )
    return perm


@pytest.fixture
def api_client():
    """Create an API client for testing."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user, organization):
    """Create an authenticated API client with organization context."""
    api_client.force_authenticate(user=user)
    api_client.credentials(HTTP_X_ORGANIZATION_ID=str(organization.id))
    return api_client


@pytest.fixture
def admin_authenticated_client(api_client, admin_user, organization):
    """Create an authenticated admin API client."""
    api_client.force_authenticate(user=admin_user)
    api_client.credentials(HTTP_X_ORGANIZATION_ID=str(organization.id))
    return api_client


@pytest.fixture
def permission_audit_log(db, user, field_permission):
    """Create a test permission audit log."""
    log = PermissionAuditLog.objects.create(
        actor=user,
        target_user=user,
        operation_type='grant',
        target_type='field_permission',
        permission_details={
            'field_name': 'email',
            'permission_type': 'masked'
        },
        content_object=field_permission,
        result='success',
        organization=user.current_organization
    )
    return log


@pytest.fixture
def multiple_field_permissions(db, user, user_content_type):
    """Create multiple field permissions for testing."""
    permissions = []
    fields_config = [
        ('email', 'masked', 'email'),
        ('phone', 'masked', 'phone'),
        ('first_name', 'read', None),
        ('last_name', 'hidden', None),
    ]
    for field_name, perm_type, mask_rule in fields_config:
        perm = FieldPermission.objects.create(
            user=user,
            content_type=user_content_type,
            field_name=field_name,
            permission_type=perm_type,
            mask_rule=mask_rule,
            priority=len(permissions),
            created_by=user,
            organization=user.current_organization
        )
        permissions.append(perm)
    return permissions


@pytest.fixture
def multiple_data_permissions(db, user, user_content_type):
    """Create multiple data permissions for testing using different content types."""
    permissions = []
    scopes = ['self', 'self_dept', 'all', 'specified']
    # Get Organization content type for variety
    from apps.organizations.models import Organization
    org_content_type = ContentType.objects.get_for_model(Organization)
    content_types = [user_content_type, org_content_type, user_content_type, org_content_type]
    users = []
    for i, scope_type in enumerate(scopes):
        # Create different user for each permission to avoid unique constraint
        perm_user = User.objects.create_user(
            username=f'datapermuser{i}',
            email=f'dataperm{i}@example.com',
            password='testpass123',
            current_organization=user.current_organization
        )
        from apps.accounts.models import UserOrganization
        UserOrganization.objects.create(
            user=perm_user,
            organization=user.current_organization,
            role='member',
            is_primary=True,
            is_active=True
        )
        perm = DataPermission.objects.create(
            user=perm_user,
            content_type=content_types[i],
            scope_type=scope_type,
            scope_value={'department_ids': [1, 2, 3]} if scope_type == 'specified' else {},
            description=f'Test {scope_type} permission',
            created_by=user,
            organization=user.current_organization
        )
        permissions.append(perm)
        users.append(perm_user)
    return permissions, users
