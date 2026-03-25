"""
Base integration adapter class.

Provides abstract interface for all ERP integration adapters.
Subclasses must implement all abstract methods to integrate with external systems.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging

from apps.integration.models import IntegrationConfig, DataMappingTemplate

logger = logging.getLogger(__name__)


class BaseIntegrationAdapter(ABC):
    """
    Abstract base class for integration adapters.

    All ERP system adapters must inherit from this class and implement
    the required methods.
    """

    def __init__(self, config: IntegrationConfig):
        """
        Initialize adapter with integration configuration.

        Args:
            config: IntegrationConfig instance containing connection settings
        """
        self.config = config
        self.organization = config.organization
        self.connection_config = config.connection_config
        self.system_type = config.system_type

    @property
    @abstractmethod
    def adapter_type(self) -> str:
        """Return the adapter type identifier (e.g., 'm18', 'sap')."""
        pass

    @property
    @abstractmethod
    def adapter_name(self) -> str:
        """Return the adapter display name."""
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to external system.

        Returns:
            Dict with keys:
                - success (bool): Connection test result
                - message (str): Result message
                - response_time_ms (int): Response time in milliseconds
                - details (dict): Additional details (optional)
        """
        pass

    @abstractmethod
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.

        Returns:
            Dict of HTTP headers for authentication
        """
        pass

    @abstractmethod
    def pull_data(
        self,
        business_type: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Pull data from external system.

        Args:
            business_type: Type of business object (e.g., 'purchase_order')
            params: Optional query parameters

        Returns:
            List of data records from external system
        """
        pass

    @abstractmethod
    def push_data(
        self,
        business_type: str,
        data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Push data to external system.

        Args:
            business_type: Type of business object (e.g., 'voucher')
            data: List of data records to push

        Returns:
            Dict with keys:
                - success (bool): Push result
                - total (int): Total records
                - succeeded (int): Success count
                - failed (int): Failure count
                - errors (list): Error details
        """
        pass

    def map_to_local(
        self,
        business_type: str,
        external_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map external system data to local format.

        Uses DataMappingTemplate if available, otherwise returns data as-is.

        Args:
            business_type: Type of business object
            external_data: Data from external system

        Returns:
            Mapped data in local format
        """
        try:
            mapping = DataMappingTemplate.objects.filter(
                organization=self.organization,
                system_type=self.system_type,
                business_type=business_type,
                is_active=True
            ).first()

            if not mapping:
                return external_data

            result = {}
            field_mappings = mapping.field_mappings or {}

            # Apply field mappings
            for local_field, external_field in field_mappings.items():
                if isinstance(external_field, str):
                    # Simple field mapping
                    result[local_field] = external_data.get(external_field)
                elif isinstance(external_field, dict):
                    # Nested field mapping
                    result[local_field] = self._get_nested_value(
                        external_data,
                        external_field.get('path', ''),
                        external_field.get('default')
                    )

            # Apply value mappings
            value_mappings = mapping.value_mappings or {}
            for field_name, value_map in value_mappings.items():
                if field_name in result:
                    original_value = result[field_name]
                    if str(original_value) in value_map:
                        result[field_name] = value_map[str(original_value)]

            # Copy unmapped fields
            for key, value in external_data.items():
                if key not in field_mappings:
                    result[key] = value

            return result

        except Exception as e:
            logger.error(f"Error mapping data: {e}")
            return external_data

    def map_to_external(
        self,
        business_type: str,
        local_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map local data to external system format.

        Args:
            business_type: Type of business object
            local_data: Local data format

        Returns:
            Data in external system format
        """
        try:
            mapping = DataMappingTemplate.objects.filter(
                organization=self.organization,
                system_type=self.system_type,
                business_type=business_type,
                is_active=True
            ).first()

            if not mapping:
                return local_data

            result = {}
            field_mappings = mapping.field_mappings or {}

            # Reverse field mappings
            reverse_mappings = {v: k for k, v in field_mappings.items()}

            for local_field, external_field in reverse_mappings.items():
                result[external_field] = local_data.get(local_field)

            # Copy unmapped fields
            for key, value in local_data.items():
                if key not in reverse_mappings:
                    result[key] = value

            # Apply value mappings (reverse)
            value_mappings = mapping.value_mappings or {}
            for field_name, value_map in value_mappings.items():
                reverse_value_map = {v: k for k, v in value_map.items()}
                if field_name in result and str(result[field_name]) in reverse_value_map:
                    result[field_name] = reverse_value_map[str(result[field_name])]

            return result

        except Exception as e:
            logger.error(f"Error mapping to external format: {e}")
            return local_data

    def _get_nested_value(
        self,
        data: Dict[str, Any],
        path: str,
        default: Any = None
    ) -> Any:
        """
        Get nested value from dict using dot notation.

        Args:
            data: Source dictionary
            path: Dot-separated path (e.g., 'user.name')
            default: Default value if path not found

        Returns:
            Value at path or default
        """
        keys = path.split('.')
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default

        return value if value is not None else default

    def log_request(
        self,
        sync_task,
        action: str,
        request_method: str,
        request_url: str,
        request_headers: Dict[str, str],
        request_body: Dict[str, Any],
        status_code: Optional[int] = None,
        response_body: Optional[Dict[str, Any]] = None,
        success: bool = False,
        error_message: str = '',
        duration_ms: Optional[int] = None
    ):
        """
        Create an integration log entry.

        Args:
            sync_task: Associated sync task
            action: Action type (pull/push)
            request_method: HTTP method
            request_url: Request URL
            request_headers: Request headers
            request_body: Request body
            status_code: HTTP status code
            response_body: Response body
            success: Request success status
            error_message: Error message if failed
            duration_ms: Request duration in milliseconds
        """
        from apps.integration.models import IntegrationLog

        IntegrationLog.objects.create(
            organization=self.organization,
            sync_task=sync_task,
            system_type=self.system_type,
            integration_type=f"{self.system_type}_{sync_task.business_type if sync_task else 'unknown'}",
            action=action,
            request_method=request_method,
            request_url=request_url,
            request_headers=request_headers,
            request_body=request_body,
            status_code=status_code,
            response_body=response_body or {},
            success=success,
            error_message=error_message,
            duration_ms=duration_ms,
            business_type=sync_task.business_type if sync_task else '',
        )
