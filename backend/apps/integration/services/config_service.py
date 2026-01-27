"""
Service for integration configuration management.

Provides business logic for managing IntegrationConfig instances.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from apps.common.services.base_crud import BaseCRUDService
from apps.integration.models import IntegrationConfig
from apps.integration.adapters import get_adapter
from apps.integration.constants import HealthStatus, SyncStatus

logger = logging.getLogger(__name__)


class IntegrationConfigService(BaseCRUDService):
    """Service for IntegrationConfig management."""

    def __init__(self):
        """Initialize service with IntegrationConfig model."""
        super().__init__(IntegrationConfig)

    def test_connection(self, config: IntegrationConfig) -> Dict[str, Any]:
        """
        Test connection to external system.

        Args:
            config: IntegrationConfig instance to test

        Returns:
            Dict with test results
        """
        try:
            adapter = get_adapter(config)

            if adapter is None:
                return {
                    'success': False,
                    'message': f'No adapter available for system type: {config.system_type}',
                    'response_time_ms': None,
                    'details': None
                }

            # Perform connection test
            start_time = datetime.now()
            result = adapter.test_connection()
            end_time = datetime.now()

            response_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Update health status based on result
            if result.get('success'):
                config.health_status = HealthStatus.HEALTHY
            else:
                config.health_status = HealthStatus.UNHEALTHY
            config.last_health_check_at = end_time
            config.save(update_fields=['health_status', 'last_health_check_at'])

            return {
                'success': result.get('success', False),
                'message': result.get('message', 'Connection test completed'),
                'response_time_ms': response_time_ms,
                'details': result.get('details')
            }

        except Exception as e:
            logger.error(f"Connection test failed: {e}")

            # Update health status to unhealthy
            config.health_status = HealthStatus.UNHEALTHY
            config.last_health_check_at = datetime.now()
            config.save(update_fields=['health_status', 'last_health_check_at'])

            return {
                'success': False,
                'message': f'Connection test failed: {str(e)}',
                'response_time_ms': None,
                'details': None
            }

    def get_enabled_configs(self) -> List[IntegrationConfig]:
        """
        Get all enabled integration configs for current organization.

        Returns:
            List of enabled IntegrationConfig instances
        """
        return list(self.query(
            filters={'is_enabled': True},
            order_by='system_type'
        ))

    def get_by_system_type(self, system_type: str) -> Optional[IntegrationConfig]:
        """
        Get config by system type for current organization.

        Args:
            system_type: System type identifier

        Returns:
            IntegrationConfig instance or None
        """
        results = self.query(filters={'system_type': system_type})
        return results.first() if results.exists() else None

    def health_check(self, config: IntegrationConfig) -> Dict[str, Any]:
        """
        Perform health check on integration config.

        Args:
            config: IntegrationConfig instance

        Returns:
            Dict with health status and details
        """
        return self.test_connection(config)
