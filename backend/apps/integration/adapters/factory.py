"""
Adapter factory for creating integration adapters.

Provides factory pattern for instantiating the appropriate adapter
based on system type.
"""
import logging
from typing import Optional

from apps.integration.adapters.base import BaseIntegrationAdapter
from apps.integration.models import IntegrationConfig
from apps.integration.constants import IntegrationSystemType

logger = logging.getLogger(__name__)


class AdapterFactory:
    """Factory class for creating integration adapters."""

    _adapters = {}

    @classmethod
    def register(cls, system_type: str, adapter_class: type):
        """
        Register an adapter class for a system type.

        Args:
            system_type: System type identifier (e.g., 'm18', 'sap')
            adapter_class: Adapter class (must inherit from BaseIntegrationAdapter)
        """
        cls._adapters[system_type] = adapter_class
        logger.info(f"Registered adapter for system type: {system_type}")

    @classmethod
    def unregister(cls, system_type: str):
        """
        Unregister an adapter class.

        Args:
            system_type: System type identifier
        """
        if system_type in cls._adapters:
            del cls._adapters[system_type]
            logger.info(f"Unregistered adapter for system type: {system_type}")

    @classmethod
    def create(cls, config: IntegrationConfig) -> BaseIntegrationAdapter:
        """
        Create an adapter instance for the given config.

        Args:
            config: IntegrationConfig instance

        Returns:
            Adapter instance

        Raises:
            ValueError: If no adapter is registered for the system type
        """
        system_type = config.system_type

        if system_type not in cls._adapters:
            raise ValueError(
                f"No adapter registered for system type: {system_type}. "
                f"Available types: {list(cls._adapters.keys())}"
            )

        adapter_class = cls._adapters[system_type]
        return adapter_class(config)

    @classmethod
    def is_registered(cls, system_type: str) -> bool:
        """
        Check if an adapter is registered for a system type.

        Args:
            system_type: System type identifier

        Returns:
            True if adapter is registered, False otherwise
        """
        return system_type in cls._adapters

    @classmethod
    def registered_types(cls) -> list:
        """
        Get list of registered system types.

        Returns:
            List of registered system type identifiers
        """
        return list(cls._adapters.keys())


def get_adapter(config: IntegrationConfig) -> Optional[BaseIntegrationAdapter]:
    """
    Convenience function to get an adapter for a config.

    Args:
        config: IntegrationConfig instance

    Returns:
        Adapter instance or None if not registered
    """
    try:
        return AdapterFactory.create(config)
    except ValueError:
        return None
