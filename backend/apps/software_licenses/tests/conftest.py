# backend/apps/software_licenses/tests/conftest.py

import pytest
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.software_licenses.models import Software, SoftwareLicense
from apps.assets.models import Asset, AssetCategory


@pytest.fixture
def org(db):
    """Create test organization"""
    return Organization.objects.create(
        name='Test Organization',
        code='TESTORG'
    )


@pytest.fixture
def user(org):
    """Create test user"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        organization=org
    )


@pytest.fixture
def software(org, user):
    """Create test software"""
    return Software.objects.create(
        organization=org,
        code='TESTSOFT',
        name='Test Software',
        version='1.0',
        created_by=user
    )


@pytest.fixture
def software_license(org, user, software):
    """Create test software license"""
    return SoftwareLicense.objects.create(
        organization=org,
        license_no='LIC-TEST-001',
        software=software,
        total_units=10,
        used_units=0,
        purchase_date='2026-01-01',
        created_by=user
    )


@pytest.fixture
def asset_category(org):
    """Create test asset category"""
    return AssetCategory.objects.create(
        organization=org,
        code='PC',
        name='Computer'
    )


@pytest.fixture
def asset(org, user, asset_category):
    """Create test asset"""
    return Asset.objects.create(
        organization=org,
        asset_code='PC001',
        asset_name='Test PC',
        asset_category=asset_category,
        purchase_price=5000,
        purchase_date='2026-01-01',
        created_by=user
    )


@pytest.fixture
def api_client():
    """Create API client"""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def auth_client(api_client, user):
    """Create authenticated API client"""
    api_client.force_authenticate(user=user)
    return api_client
