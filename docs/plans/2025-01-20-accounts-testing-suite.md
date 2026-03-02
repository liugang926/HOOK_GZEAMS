# Accounts Module Testing Suite Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement comprehensive test coverage for the accounts module including models, services, ViewSets, and API endpoints.

**Architecture:** TDD approach with pytest, APITestCase for API testing, and fixtures for common test data. Tests will cover user management, organization membership, SSO fields, and authentication scenarios.

**Tech Stack:** pytest, pytest-django, factory_boy, Django REST Framework APITestCase

---

## Overview

The accounts module was recently implemented but has no test coverage. This plan adds:
1. Model tests for User and UserOrganization
2. Service layer tests for UserService
3. API endpoint tests for UserViewSet
4. Fixture setup via conftest.py

**Files to Create:**
- `backend/apps/accounts/tests/__init__.py`
- `backend/apps/accounts/tests/conftest.py`
- `backend/apps/accounts/tests/test_models.py`
- `backend/apps/accounts/tests/test_services.py`
- `backend/apps/accounts/tests/test_api.py`

---

## Task 1: Create Test Directory Structure and conftest.py

**Files:**
- Create: `backend/apps/accounts/tests/__init__.py`
- Create: `backend/apps/accounts/tests/conftest.py`

**Step 1: Create __init__.py**

```bash
mkdir -p backend/apps/accounts/tests
touch backend/apps/accounts/tests/__init__.py
```

**Step 2: Write conftest.py with fixtures**

```python
"""
Pytest Configuration for Accounts Tests

Fixtures and configuration for testing Accounts module.
"""
import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Configure Django settings before any Django imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

import pytest
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization
from apps.accounts.models import UserOrganization

User = get_user_model()


@pytest.fixture
def db():
    """Ensure database is available."""
    from django.db import connection
    connection.ensure_connection()


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
def user(organization):
    """Create a test user."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
    )
    # Add to organization
    UserOrganization.objects.create(
        user=user,
        organization=organization,
        role='member',
        is_primary=True
    )
    user.current_organization = organization
    user.save()
    return user


@pytest.fixture
def admin_user(organization):
    """Create an admin user."""
    user = User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='adminpass123',
        is_staff=True,
        is_superuser=True,
    )
    UserOrganization.objects.create(
        user=user,
        organization=organization,
        role='admin',
        is_primary=True
    )
    user.current_organization = organization
    user.save()
    return user


@pytest.fixture
def second_organization(db):
    """Create a second test organization for multi-org tests."""
    org = Organization.objects.create(
        name='Second Organization',
        code='SECOND_ORG',
        is_active=True
    )
    return org


@pytest.fixture
def api_client():
    """Create an API test client."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user, organization):
    """Create an authenticated API client with organization context."""
    api_client.force_authenticate(user=user)
    api_client.credentials(HTTP_X_ORGANIZATION_ID=str(organization.id))
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user, organization):
    """Create an authenticated admin API client."""
    api_client.force_authenticate(user=admin_user)
    api_client.credentials(HTTP_X_ORGANIZATION_ID=str(organization.id))
    return api_client
```

**Step 3: Verify fixtures load correctly**

Run: `docker-compose exec backend python -c "from apps.accounts.tests.conftest import User; print('Fixtures loaded')"`

Expected: No errors

**Step 4: Commit**

```bash
git add backend/apps/accounts/tests/__init__.py backend/apps/accounts/tests/conftest.py
git commit -m "test: add accounts test fixtures and conftest"
```

---

## Task 2: Implement Model Tests

**Files:**
- Create: `backend/apps/accounts/tests/test_models.py`

**Step 1: Write User model tests**

```python
"""
Tests for User and UserOrganization models.
"""
import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization
from apps.accounts.models import UserOrganization

User = get_user_model()


class UserTest:
    """Test User model."""

    def test_create_user(self, db):
        """Test creating a standard user."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_superuser(self, db):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        assert user.is_staff
        assert user.is_superuser

    def test_user_str_representation(self, db):
        """Test user string representation."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.first_name = 'Test'
        user.last_name = 'User'
        user.save()
        assert str(user) == 'testuser (Test User)'

    def test_sso_fields(self, db):
        """Test SSO integration fields are stored correctly."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            wework_userid='WW123',
            wework_unionid='WWU123',
            dingtalk_userid='DT123',
            dingtalk_unionid='DTU123',
            feishu_userid='FS123',
            feishu_unionid='FSU123',
        )
        assert user.wework_userid == 'WW123'
        assert user.dingtalk_userid == 'DT123'
        assert user.feishu_userid == 'FS123'

    def test_soft_delete(self, db):
        """Test User soft delete functionality."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user_id = user.id

        # Soft delete
        user.soft_delete(None)
        user.refresh_from_db()

        assert user.is_deleted
        assert user.deleted_at is not None

        # Should not appear in default queryset
        assert not User.objects.filter(id=user_id).exists()
        # But should exist with all
        assert User.all_objects.filter(id=user_id).exists()

    def test_get_accessible_organizations(self, user, organization, second_organization):
        """Test getting user's accessible organizations."""
        # Add user to second organization
        UserOrganization.objects.create(
            user=user,
            organization=second_organization,
            role='auditor'
        )

        orgs = user.get_accessible_organizations()
        assert orgs.count() == 2

    def test_get_org_role(self, user, organization):
        """Test getting user's role in an organization."""
        role = user.get_org_role(organization.id)
        assert role == 'member'

    def test_get_org_role_no_membership(self, user, second_organization):
        """Test getting role when user is not a member."""
        role = user.get_org_role(second_organization.id)
        assert role is None

    def test_get_primary_organization(self, user, organization):
        """Test getting user's primary organization."""
        primary = user.get_primary_organization()
        assert primary == organization

    def test_switch_organization(self, user, organization, second_organization):
        """Test switching user's current organization."""
        # Add to second org
        UserOrganization.objects.create(
            user=user,
            organization=second_organization,
            role='admin',
            is_primary=True
        )

        result = user.switch_organization(second_organization.id)
        assert result is True

        user.refresh_from_db()
        assert user.current_organization == second_organization

    def test_switch_organization_not_accessible(self, user, second_organization):
        """Test switching to non-accessible organization fails."""
        result = user.switch_organization(second_organization.id)
        assert result is False


class UserOrganizationTest:
    """Test UserOrganization model."""

    def test_create_user_organization(self, user, organization):
        """Test creating user-organization relationship."""
        user_org = UserOrganization.objects.create(
            user=user,
            organization=organization,
            role='admin'
        )
        assert user_org.user == user
        assert user_org.organization == organization
        assert user_org.role == 'admin'
        assert user_org.is_active

    def test_str_representation(self, user, organization):
        """Test string representation."""
        user_org = UserOrganization.objects.create(
            user=user,
            organization=organization,
            role='admin'
        )
        assert 'testuser' in str(user_org)
        assert 'Test Organization' in str(user_org)
        assert 'admin' in str(user_org)

    def test_only_one_primary_organization(self, user, organization, second_organization):
        """Test that only one organization can be primary."""
        # First org is already primary from fixture
        first_org = UserOrganization.objects.get(
            user=user, organization=organization
        )
        assert first_org.is_primary

        # Create second org as primary
        second_org = UserOrganization.objects.create(
            user=user,
            organization=second_organization,
            role='member',
            is_primary=True
        )

        # First should no longer be primary
        first_org.refresh_from_db()
        assert not first_org.is_primary
        assert second_org.is_primary

    def test_unique_user_organization(self, user, organization):
        """Test that user-org combination is unique."""
        UserOrganization.objects.create(
            user=user,
            organization=organization,
            role='member'
        )

        # Try to create duplicate
        with pytest.raises(Exception):  # IntegrityError
            UserOrganization.objects.create(
                user=user,
                organization=organization,
                role='admin'
            )

    def test_role_choices(self, db, organization):
        """Test that only valid roles can be set."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Valid roles should work
        for role in ['admin', 'member', 'auditor']:
            UserOrganization.objects.create(
                user=user,
                organization=organization,
                role=role
            )
```

**Step 2: Run model tests**

Run: `docker-compose exec backend pytest apps/accounts/tests/test_models.py -v`

Expected: Tests pass

**Step 3: Commit**

```bash
git add backend/apps/accounts/tests/test_models.py
git commit -m "test: add accounts model tests"
```

---

## Task 3: Implement Service Layer Tests

**Files:**
- Create: `backend/apps/accounts/tests/test_services.py`

**Step 1: Write UserService tests**

```python
"""
Tests for UserService.
"""
import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization
from apps.accounts.models import UserOrganization
from apps.accounts.services.user_service import UserService

User = get_user_model()


class UserServiceTest:
    """Test UserService class."""

    def test_create_user(self, db, organization):
        """Test creating a user via service."""
        service = UserService()
        user_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
        }
        user = service.create(user_data, organization_id=organization.id)

        assert user.username == 'newuser'
        assert user.email == 'new@example.com'
        assert user.check_password('newpass123')

    def test_get_user_by_id(self, user):
        """Test getting user by ID."""
        service = UserService()
        retrieved = service.get(str(user.id))
        assert retrieved == user

    def test_update_user(self, user):
        """Test updating user via service."""
        service = UserService()
        updated = service.update(str(user.id), {
            'first_name': 'Updated',
            'last_name': 'Name'
        })

        user.refresh_from_db()
        assert user.first_name == 'Updated'
        assert user.last_name == 'Name'

    def test_soft_delete_user(self, user):
        """Test soft deleting user via service."""
        service = UserService()
        service.delete(str(user.id))

        user.refresh_from_db()
        assert user.is_deleted

    def test_activate_user(self, user):
        """Test activating a user."""
        user.is_active = False
        user.save()

        service = UserService()
        service.activate_user(str(user.id))

        user.refresh_from_db()
        assert user.is_active

    def test_deactivate_user(self, user):
        """Test deactivating a user."""
        service = UserService()
        service.deactivate_user(str(user.id))

        user.refresh_from_db()
        assert not user.is_active

    def test_get_accessible_users(self, user, organization):
        """Test getting users accessible to an organization."""
        service = UserService()
        users = service.get_accessible_users(organization.id)

        assert user in users

    def test_get_accessible_users_with_filters(self, user, organization):
        """Test filtering accessible users."""
        # Create another inactive user
        inactive = User.objects.create_user(
            username='inactive',
            email='inactive@example.com',
            password='pass123',
            is_active=False
        )
        UserOrganization.objects.create(
            user=inactive,
            organization=organization,
            role='member'
        )

        service = UserService()
        users = service.get_accessible_users(organization.id, {'is_active': True})

        assert user in users
        assert inactive not in users

    def test_add_to_organization(self, user, second_organization):
        """Test adding user to an organization."""
        service = UserService()
        user_org = service.add_to_organization(
            str(user.id),
            str(second_organization.id),
            role='auditor'
        )

        assert user_org.user == user
        assert user_org.organization == second_organization
        assert user_org.role == 'auditor'

    def test_remove_from_organization(self, user, organization):
        """Test removing user from an organization."""
        service = UserService()
        service.remove_from_organization(str(user.id), str(organization.id))

        exists = UserOrganization.objects.filter(
            user=user,
            organization=organization,
            is_active=True
        ).exists()
        assert not exists

    def test_switch_organization(self, user, organization, second_organization):
        """Test switching user's organization via service."""
        # Add to second org
        UserOrganization.objects.create(
            user=user,
            organization=second_organization,
            role='admin',
            is_primary=True
        )

        service = UserService()
        result = service.switch_organization(str(user.id), str(second_organization.id))

        assert result is True
        user.refresh_from_db()
        assert user.current_organization == second_organization

    def test_get_user_stats(self, user, organization):
        """Test getting user statistics for an organization."""
        service = UserService()
        stats = service.get_user_stats(str(organization.id))

        assert 'total' in stats
        assert 'active' in stats
        assert stats['total'] >= 1
        assert stats['active'] >= 1

    def test_query_with_pagination(self, user, organization):
        """Test querying users with pagination."""
        service = UserService()
        result = service.query(
            organization_id=organization.id,
            page=1,
            page_size=10
        )

        assert 'results' in result
        assert 'count' in result
        assert 'page' in result
        assert result['page'] == 1

    def test_batch_delete_users(self, db, organization):
        """Test batch deleting users."""
        users = []
        for i in range(3):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='pass123'
            )
            UserOrganization.objects.create(
                user=user,
                organization=organization,
                role='member'
            )
            users.append(user)

        service = UserService()
        user_ids = [str(u.id) for u in users]
        result = service.batch_delete(user_ids)

        assert result['total'] == 3
        assert result['succeeded'] == 3

        # Verify soft delete
        for user in users:
            user.refresh_from_db()
            assert user.is_deleted
```

**Step 2: Run service tests**

Run: `docker-compose exec backend pytest apps/accounts/tests/test_services.py -v`

Expected: Tests pass

**Step 3: Commit**

```bash
git add backend/apps/accounts/tests/test_services.py
git commit -m "test: add accounts service layer tests"
```

---

## Task 4: Implement API Endpoint Tests

**Files:**
- Create: `backend/apps/accounts/tests/test_api.py`

**Step 1: Write UserViewSet API tests**

```python
"""
Tests for Accounts API endpoints.
"""
import pytest
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization
from apps.accounts.models import UserOrganization

User = get_user_model()


class UserListAPITest:
    """Test user list API endpoints."""

    def test_list_users_unauthorized(self, api_client):
        """Test that unauthorized users cannot list users."""
        url = '/api/auth/users/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_users_authorized(self, authenticated_client, user):
        """Test listing users as authenticated user."""
        url = '/api/auth/users/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'results' in response.data['data'] or 'count' in response.data['data']

    def test_list_users_pagination(self, authenticated_client):
        """Test user list pagination."""
        url = '/api/auth/users/?page=1&page_size=10'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_list_users_search(self, authenticated_client, user):
        """Test searching users."""
        url = '/api/auth/users/?search=test'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_create_user(self, admin_client, organization):
        """Test creating a new user."""
        url = '/api/auth/users/'
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
        }
        response = admin_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True

    def test_create_user_password_mismatch(self, admin_client):
        """Test creating user with mismatched passwords fails."""
        url = '/api/auth/users/'
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'different',
        }
        response = admin_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class UserDetailAPITest:
    """Test user detail API endpoints."""

    def test_get_user_detail(self, authenticated_client, user):
        """Test getting single user details."""
        url = f'/api/auth/users/{user.id}/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['username'] == 'testuser'

    def test_update_user(self, authenticated_client, user):
        """Test updating a user."""
        url = f'/api/auth/users/{user.id}/'
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com'
        }
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.first_name == 'Updated'

    def test_delete_user_soft_delete(self, authenticated_client, user):
        """Test that DELETE performs soft delete."""
        url = f'/api/auth/users/{user.id}/'
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.is_deleted

    def test_delete_self_forbidden(self, authenticated_client, user):
        """Test that user cannot delete themselves."""
        url = f'/api/auth/users/{user.id}/'
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'own account' in response.data['error']['message'].lower()


class UserMeAPITest:
    """Test /me endpoints."""

    def test_get_current_user(self, authenticated_client, user):
        """Test getting current user info."""
        url = '/api/auth/users/me/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['username'] == 'testuser'

    def test_get_current_user_unauthorized(self, api_client):
        """Test that unauthorized users cannot get current user."""
        url = '/api/auth/users/me/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_change_password(self, authenticated_client, user):
        """Test changing password."""
        url = '/api/auth/users/me/change-password/'
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass456',
            'new_password_confirm': 'newpass456'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_change_password_wrong_old(self, authenticated_client, user):
        """Test changing password with wrong old password fails."""
        url = '/api/auth/users/me/change-password/'
        data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass456',
            'new_password_confirm': 'newpass456'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_mismatch(self, authenticated_client, user):
        """Test changing password with mismatched confirmation fails."""
        url = '/api/auth/users/me/change-password/'
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass456',
            'new_password_confirm': 'different'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class UserActionAPITest:
    """Test user action endpoints."""

    def test_activate_user(self, admin_client, user):
        """Test activating a user."""
        user.is_active = False
        user.save()

        url = f'/api/auth/users/{user.id}/activate/'
        response = admin_client.post(url)
        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.is_active

    def test_deactivate_user(self, admin_client):
        """Test deactivating a user."""
        # Create a separate user to deactivate
        org = Organization.objects.first()
        target_user = User.objects.create_user(
            username='target',
            email='target@example.com',
            password='pass123'
        )
        UserOrganization.objects.create(
            user=target_user,
            organization=org,
            role='member'
        )

        url = f'/api/auth/users/{target_user.id}/deactivate/'
        response = admin_client.post(url)
        assert response.status_code == status.HTTP_200_OK

        target_user.refresh_from_db()
        assert not target_user.is_active

    def test_deactivate_self_forbidden(self, authenticated_client, user):
        """Test that user cannot deactivate themselves."""
        url = f'/api/auth/users/{user.id}/deactivate/'
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_user_organizations(self, authenticated_client, user, organization):
        """Test getting user's organizations."""
        url = f'/api/auth/users/{user.id}/organizations/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) >= 1

    def test_switch_organization(self, authenticated_client, user, second_organization):
        """Test switching user's organization."""
        # Add user to second org
        UserOrganization.objects.create(
            user=user,
            organization=second_organization,
            role='admin'
        )

        url = f'/api/auth/users/{user.id}/switch-org/'
        data = {'organization_id': str(second_organization.id)}
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_switch_org_forbidden_for_other_user(self, authenticated_client, admin_user, organization):
        """Test that user cannot switch another user's organization."""
        url = f'/api/auth/users/{admin_user.id}/switch-org/'
        data = {'organization_id': str(organization.id)}
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_accessible_users(self, authenticated_client, user, organization):
        """Test getting accessible users endpoint."""
        url = '/api/auth/users/accessible/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data['data']

    def test_get_stats(self, authenticated_client, organization):
        """Test getting user statistics."""
        url = '/api/auth/users/stats/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'total' in response.data['data']


class OrganizationFilterAPITest:
    """Test organization-based filtering."""

    def test_users_filtered_by_organization(self, authenticated_client, user, second_organization):
        """Test that users are filtered by current organization."""
        # user is only in first organization
        url = '/api/auth/users/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        # Should only see users from current org
        results = response.data['data'].get('results', response.data['data'])
        if results:
            for u in results:
                assert u['username'] == 'testuser'  # Only our test user
```

**Step 2: Run API tests**

Run: `docker-compose exec backend pytest apps/accounts/tests/test_api.py -v`

Expected: Tests pass

**Step 3: Commit**

```bash
git add backend/apps/accounts/tests/test_api.py
git commit -m "test: add accounts API endpoint tests"
```

---

## Task 5: Run Full Test Suite and Verify Coverage

**Files:**
- Modify: None (verification step)

**Step 1: Run all accounts tests**

Run: `docker-compose exec backend pytest apps/accounts/tests/ -v --tb=short`

Expected: All tests pass

**Step 2: Run with coverage report**

Run: `docker-compose exec backend pytest apps/accounts/tests/ -v --cov=apps.accounts --cov-report=term-missing`

Expected: Coverage report shows percentage

**Step 3: Run entire project tests to ensure no regressions**

Run: `docker-compose exec backend pytest apps/ -v --tb=short`

Expected: All existing tests still pass

**Step 4: Commit test configuration updates**

```bash
# If pytest.ini or setup.cfg needs updates
git add backend/pytest.ini 2>/dev/null || true
git add backend/setup.cfg 2>/dev/null || true
git commit -m "test: configure pytest for accounts module"
```

---

## Completion Checklist

After all tasks complete:

- [ ] All model tests pass (User, UserOrganization)
- [ ] All service tests pass (UserService methods)
- [ ] All API tests pass (UserViewSet endpoints)
- [ ] Test coverage >= 80% for accounts module
- [ ] No regressions in existing tests
- [ ] Fixtures work correctly with pytest-django

---

## Notes for Implementation

1. **Database Setup**: Tests use pytest-django which handles database transaction rollback automatically.

2. **Authentication**: Tests use `force_authenticate` for API testing to avoid actual JWT validation complexity in tests.

3. **Organization Context**: The `HTTP_X_ORGANIZATION_ID` header simulates the middleware that sets `request.organization_id`.

4. **Soft Delete**: Verify that deleted users are filtered from querysets but still exist in database with `is_deleted=True`.

5. **Multi-Tenant**: Ensure tests verify that users only see data from their current organization.
