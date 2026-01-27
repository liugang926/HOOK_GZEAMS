"""
Configuration file for pytest.

Provides fixtures for integration module tests.
"""
import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.organizations.models import Organization
from apps.integration.models import (
    IntegrationConfig,
    IntegrationSyncTask,
    IntegrationLog,
    DataMappingTemplate,
)

User = get_user_model()


@pytest.fixture
def organization(db):
    """Create a test organization."""
    return Organization.objects.create(
        name='Test Organization',
        code='TEST_ORG',
        is_active=True
    )


@pytest.fixture
def user(db, organization):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        organization=organization,
        is_active=True
    )


@pytest.fixture
def admin_user(db, organization):
    """Create an admin user."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123',
        organization=organization
    )


@pytest.fixture
def integration_config(db, organization, user):
    """Create a test integration config."""
    return IntegrationConfig.objects.create(
        organization=organization,
        system_type='m18',
        system_name='Test M18 System',
        connection_config={
            'api_url': 'https://test.m18.com/api',
            'api_key': 'test_key',
        },
        enabled_modules=['procurement', 'finance'],
        sync_config={
            'auto_sync': True,
            'sync_interval': 3600
        },
        is_enabled=True,
        created_by=user
    )


@pytest.fixture
def integration_sync_task(db, organization, user, integration_config):
    """Create a test sync task."""
    return IntegrationSyncTask.objects.create(
        organization=organization,
        config=integration_config,
        task_id='test-task-001',
        module_type='procurement',
        direction='pull',
        business_type='purchase_order',
        sync_params={'start_date': '2024-01-01'},
        status='pending',
        created_by=user
    )


@pytest.fixture
def integration_log(db, organization, user, integration_sync_task):
    """Create a test integration log."""
    return IntegrationLog.objects.create(
        organization=organization,
        sync_task=integration_sync_task,
        system_type='m18',
        integration_type='m18_po',
        action='pull',
        request_method='GET',
        request_url='https://test.m18.com/api/po',
        request_headers={'Authorization': 'Bearer token'},
        request_body={},
        status_code=200,
        response_body={'data': []},
        success=True,
        duration_ms=250,
        business_type='purchase_order',
        created_by=user
    )


@pytest.fixture
def data_mapping_template(db, organization, user):
    """Create a test data mapping template."""
    return DataMappingTemplate.objects.create(
        organization=organization,
        system_type='m18',
        business_type='purchase_order',
        template_name='Test PO Mapping',
        field_mappings={
            'local_code': 'externalCode',
            'local_name': 'externalName',
        },
        value_mappings={
            'status': {
                '1': 'draft',
                '2': 'approved'
            }
        },
        transform_rules=[],
        is_active=True,
        created_by=user
    )


@pytest.fixture
def auth_client(db, client, user):
    """Create an authenticated test client."""
    client.force_authenticate(user=user)
    # Set organization in request
    client.organization = user.organization
    return client
