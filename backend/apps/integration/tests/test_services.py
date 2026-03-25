"""
Tests for integration services.

Tests all services in the integration module.
"""
import pytest
from unittest.mock import Mock, patch

from apps.integration.models import IntegrationConfig, IntegrationLog
from apps.integration.services.config_service import IntegrationConfigService
from apps.integration.services.sync_service import IntegrationSyncService
from apps.integration.services.log_service import IntegrationLogService
from apps.integration.constants import HealthStatus, SyncStatus


@pytest.mark.django_db
class TestIntegrationConfigService:
    """IntegrationConfigService tests."""

    def test_create_config(self, organization, user):
        """Test creating a config via service."""
        service = IntegrationConfigService()

        config_data = {
            'organization': organization,
            'system_type': 'm18',
            'system_name': 'Test M18',
            'connection_config': {'api_url': 'https://test.com'}
        }

        config = service.create(config_data, user=user)

        assert config.system_type == 'm18'
        assert config.organization == organization
        assert config.created_by == user

    def test_get_enabled_configs(self, organization, user):
        """Test getting enabled configs."""
        service = IntegrationConfigService()

        # Create multiple configs with different system types
        system_types = ['m18', 'sap', 'kingdee']
        for i, sys_type in enumerate(system_types):
            IntegrationConfig.objects.create(
                organization=organization,
                system_type=sys_type,
                system_name=f'Test {sys_type.upper()}-{i}',
                is_enabled=(i < 2),  # First two enabled
                created_by=user
            )

        # Get enabled configs
        enabled_configs = service.get_enabled_configs()

        assert len(enabled_configs) == 2
        assert all(c.is_enabled for c in enabled_configs)

    @patch('apps.integration.services.config_service.get_adapter')
    def test_test_connection_success(self, mock_get_adapter, organization, user):
        """Test successful connection test."""
        # Mock adapter
        mock_adapter = Mock()
        mock_adapter.test_connection.return_value = {
            'success': True,
            'message': 'Connection successful',
            'details': {'version': '2.0'}
        }
        mock_get_adapter.return_value = mock_adapter

        config = IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='Test M18',
            created_by=user
        )

        service = IntegrationConfigService()
        result = service.test_connection(config)

        assert result['success'] is True
        assert 'response_time_ms' in result

        # Check health status updated
        config.refresh_from_db()
        assert config.health_status == HealthStatus.HEALTHY

    @patch('apps.integration.services.config_service.get_adapter')
    def test_test_connection_failure(self, mock_get_adapter, organization, user):
        """Test failed connection test."""
        # Mock adapter failure
        mock_get_adapter.return_value = None

        config = IntegrationConfig.objects.create(
            organization=organization,
            system_type='unknown_type',
            system_name='Test Unknown',
            created_by=user
        )

        service = IntegrationConfigService()
        result = service.test_connection(config)

        assert result['success'] is False
        assert 'No adapter available' in result['message']


@pytest.mark.django_db
class TestIntegrationSyncService:
    """IntegrationSyncService tests."""

    def test_create_sync_task(self, organization, user, integration_config):
        """Test creating a sync task."""
        service = IntegrationSyncService()

        task = service.create_sync_task(
            config=integration_config,
            module_type='procurement',
            direction='pull',
            business_type='purchase_order',
            sync_params={'start_date': '2024-01-01'},
            user=user
        )

        assert task.config == integration_config
        assert task.module_type == 'procurement'
        assert task.direction == 'pull'
        assert task.status == SyncStatus.PENDING
        assert task.task_id.startswith('sync_')

    def test_cancel_task(self, organization, user, integration_config):
        """Test canceling a pending task."""
        service = IntegrationSyncService()

        task = service.create_sync_task(
            config=integration_config,
            module_type='procurement',
            direction='pull',
            business_type='purchase_order',
            user=user
        )

        result = service.cancel_task(task)

        assert result['success'] is True

        task.refresh_from_db()
        assert task.status == SyncStatus.CANCELLED

    def test_cancel_running_task_fails(self, organization, user, integration_config):
        """Test that canceling a running task fails."""
        from django.utils import timezone

        service = IntegrationSyncService()

        task = service.create_sync_task(
            config=integration_config,
            module_type='procurement',
            direction='pull',
            business_type='purchase_order',
            user=user
        )

        # Set to running
        task.status = SyncStatus.RUNNING
        task.started_at = timezone.now()
        task.save()

        result = service.cancel_task(task)

        assert result['success'] is False
        assert 'Cannot cancel' in result['message']

    def test_retry_task(self, organization, user, integration_config):
        """Test retrying a failed task."""
        service = IntegrationSyncService()

        # Create original task and mark as failed
        task = service.create_sync_task(
            config=integration_config,
            module_type='procurement',
            direction='pull',
            business_type='purchase_order',
            user=user
        )
        task.status = SyncStatus.FAILED
        task.save()

        # Create retry task
        new_task = service.retry_task(task)

        assert new_task.config == integration_config
        assert new_task.module_type == task.module_type
        assert new_task.direction == task.direction
        assert new_task.business_type == task.business_type
        assert new_task.status == SyncStatus.PENDING
        assert new_task.id != task.id


@pytest.mark.django_db
class TestIntegrationLogService:
    """IntegrationLogService tests."""

    def test_get_statistics(self, organization, user, integration_log):
        """Test getting log statistics."""
        service = IntegrationLogService()

        stats = service.get_statistics(days=30)

        assert 'total' in stats
        assert 'success' in stats
        assert 'failed' in stats
        assert 'success_rate' in stats
        assert stats['total'] >= 1

    def test_get_error_logs(self, organization, user, integration_sync_task):
        """Test getting error logs."""
        service = IntegrationLogService()

        # Create a failed log
        IntegrationLog.objects.create(
            organization=organization,
            sync_task=integration_sync_task,
            system_type='m18',
            integration_type='m18_po',
            action='pull',
            request_method='GET',
            request_url='https://test.com/fail',
            status_code=500,
            success=False,
            error_message='Server error',
            duration_ms=1000,
            created_by=user
        )

        error_logs = service.get_error_logs(limit=10)

        assert len(error_logs) >= 1
        assert all(not log.success for log in error_logs)

    def test_get_logs_by_task(self, organization, user, integration_log):
        """Test getting logs by task."""
        service = IntegrationLogService()

        logs = service.get_logs_by_task(integration_log.sync_task.task_id)

        assert len(logs) >= 1
        assert all(log.sync_task == integration_log.sync_task for log in logs)

    def test_get_slow_requests(self, organization, user, integration_sync_task):
        """Test getting slow requests."""
        service = IntegrationLogService()

        # Create a slow log
        IntegrationLog.objects.create(
            organization=organization,
            sync_task=integration_sync_task,
            system_type='m18',
            integration_type='m18_po',
            action='pull',
            request_method='GET',
            request_url='https://test.com/slow',
            status_code=200,
            success=True,
            duration_ms=10000,  # 10 seconds
            created_by=user
        )

        slow_logs = service.get_slow_requests(threshold_ms=5000, limit=10)

        assert len(slow_logs) >= 1
        assert all(log.duration_ms >= 5000 for log in slow_logs)
