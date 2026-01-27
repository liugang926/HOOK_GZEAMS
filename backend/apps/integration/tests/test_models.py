"""
Tests for integration models.

Tests all models in the integration module following BaseModel patterns.
"""
import pytest
from django.utils import timezone

from apps.integration.models import (
    IntegrationConfig,
    IntegrationSyncTask,
    IntegrationLog,
    DataMappingTemplate,
)
from apps.integration.constants import (
    HealthStatus,
    SyncStatus,
)


@pytest.mark.django_db
class TestIntegrationConfigModel:
    """IntegrationConfig model tests."""

    def test_create_config(self, organization, user):
        """Test creating an integration config."""
        config = IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='Test M18',
            connection_config={'api_url': 'https://test.m18.com/api'},
            created_by=user
        )

        assert config.organization == organization
        assert config.system_type == 'm18'
        assert config.health_status == HealthStatus.UNHEALTHY
        assert config.is_deleted is False
        assert config.created_at is not None
        assert config.created_by == user

    def test_soft_delete(self, organization, user):
        """Test soft delete of config."""
        config = IntegrationConfig.objects.create(
            organization=organization,
            system_type='sap',
            system_name='Test SAP',
            created_by=user
        )
        config_id = config.id

        # Soft delete
        config.soft_delete()

        # Not in normal query
        assert not IntegrationConfig.objects.filter(id=config_id).exists()

        # Found in all_objects
        assert IntegrationConfig.all_objects.filter(id=config_id).exists()

    def test_unique_constraint(self, organization, user):
        """Test unique constraint on organization + system_type."""
        IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='First M18',
            created_by=user
        )

        # Should violate unique constraint
        with pytest.raises(Exception):  # IntegrityError
            IntegrationConfig.objects.create(
                organization=organization,
                system_type='m18',
                system_name='Second M18',
                created_by=user
            )


@pytest.mark.django_db
class TestIntegrationSyncTaskModel:
    """IntegrationSyncTask model tests."""

    def test_create_sync_task(self, organization, user, integration_config):
        """Test creating a sync task."""
        task = IntegrationSyncTask.objects.create(
            organization=organization,
            config=integration_config,
            task_id='test-task-001',
            module_type='procurement',
            direction='pull',
            business_type='purchase_order',
            created_by=user
        )

        assert task.config == integration_config
        assert task.status == SyncStatus.PENDING
        assert task.total_count == 0
        assert task.success_count == 0
        assert task.failed_count == 0

    def test_task_execution_flow(self, organization, user, integration_config):
        """Test task status workflow."""
        task = IntegrationSyncTask.objects.create(
            organization=organization,
            config=integration_config,
            task_id='test-task-002',
            module_type='procurement',
            direction='pull',
            business_type='purchase_order',
            created_by=user
        )

        # Update to running
        task.status = SyncStatus.RUNNING
        task.started_at = timezone.now()
        task.save()

        # Complete task
        task.status = SyncStatus.SUCCESS
        task.completed_at = timezone.now()
        task.total_count = 100
        task.success_count = 95
        task.failed_count = 5
        task.duration_ms = 5000
        task.save()

        # Verify
        task.refresh_from_db()
        assert task.status == SyncStatus.SUCCESS
        assert task.duration_ms == 5000
        assert task.completed_at is not None


@pytest.mark.django_db
class TestIntegrationLogModel:
    """IntegrationLog model tests."""

    def test_create_log(self, organization, user, integration_sync_task):
        """Test creating an integration log."""
        log = IntegrationLog.objects.create(
            organization=organization,
            sync_task=integration_sync_task,
            system_type='m18',
            integration_type='m18_po',
            action='pull',
            request_method='GET',
            request_url='https://test.m18.com/api/po',
            request_headers={'Authorization': 'Bearer token'},
            status_code=200,
            response_body={'data': []},
            success=True,
            duration_ms=250,
            created_by=user
        )

        assert log.success is True
        assert log.status_code == 200
        assert log.duration_ms == 250
        assert log.sync_task == integration_sync_task


@pytest.mark.django_db
class TestDataMappingTemplateModel:
    """DataMappingTemplate model tests."""

    def test_create_mapping_template(self, organization, user):
        """Test creating a mapping template."""
        template = DataMappingTemplate.objects.create(
            organization=organization,
            system_type='m18',
            business_type='purchase_order',
            template_name='Test Mapping',
            field_mappings={
                'local_code': 'externalCode',
                'local_name': 'externalName'
            },
            value_mappings={
                'status': {'1': 'draft', '2': 'approved'}
            },
            transform_rules=[],
            is_active=True,
            created_by=user
        )

        assert template.organization == organization
        assert template.system_type == 'm18'
        assert template.business_type == 'purchase_order'
        assert template.is_active is True

    def test_unique_constraint(self, organization, user):
        """Test unique constraint on organization + system_type + business_type."""
        DataMappingTemplate.objects.create(
            organization=organization,
            system_type='m18',
            business_type='purchase_order',
            template_name='First Mapping',
            created_by=user
        )

        # Should violate unique constraint
        with pytest.raises(Exception):  # IntegrityError
            DataMappingTemplate.objects.create(
                organization=organization,
                system_type='m18',
                business_type='purchase_order',
                template_name='Second Mapping',
                created_by=user
            )
