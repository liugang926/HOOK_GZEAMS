"""
Django model managers for GZEAMS.

This module contains custom managers for different data access patterns:
- TenantManager: Organization-aware filtering for business data
- GlobalMetadataManager: No organization filtering for system metadata
"""
from django.db import models


class GlobalMetadataManager(models.Manager):
    """
    Manager for global system metadata models.

    This manager does NOT filter by organization, as metadata models
    like BusinessObject, FieldDefinition, and PageLayout are shared
    across all organizations in the system.

    Behavior:
    - DOES filter out soft-deleted records (is_deleted=False)
    - DOES NOT filter by organization_id

    Use this manager for models that represent:
    - System-wide metadata (BusinessObject, FieldDefinition, PageLayout)
    - Global configuration (DictionaryType, SequenceRule, SystemConfig)
    - Reference data shared across all organizations

    DO NOT use for business data like Asset, AssetPickup, etc.
    """

    def get_queryset(self):
        """
        Get queryset with soft-delete filtering only.

        Unlike TenantManager, this does NOT filter by organization.
        """
        queryset = super().get_queryset()

        # Only filter out soft-deleted records
        # DO NOT filter by organization - metadata is global
        queryset = queryset.filter(is_deleted=False)

        return queryset


class TenantManager(models.Manager):
    """
    Tenant-aware manager that automatically filters by organization.

    Uses thread-local storage to get current organization context.
    Automatically filters out soft-deleted records.

    NOTE: This is moved here from models.py for better organization.
    """

    def get_queryset(self):
        """
        Get queryset with automatic organization and soft-delete filtering.

        Returns:
            QuerySet: Filtered queryset
        """
        queryset = super().get_queryset()

        # Auto-filter by current organization from thread-local context
        from apps.common.middleware import get_current_organization
        org_id = get_current_organization()

        if org_id:
            queryset = queryset.filter(organization_id=org_id)

        # Auto-filter out soft-deleted records
        queryset = queryset.filter(is_deleted=False)

        return queryset
