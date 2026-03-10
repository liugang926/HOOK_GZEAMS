"""
Business Object Service for hybrid architecture.

Provides unified access to both hardcoded Django models and low-code
custom business objects.
"""
from typing import Dict, List, Optional, Any
from django.utils.module_loading import import_string

from apps.system.object_catalog import (
    get_hardcoded_model_map,
    get_hardcoded_object_definition,
    get_hardcoded_object_names,
)
from apps.system.models import (
    BusinessObject,
    ModelFieldDefinition,
)
from apps.system.services.business_object_query_service import BusinessObjectQueryService
from apps.system.services.hardcoded_object_sync_service import HardcodedObjectSyncService


HARDCODED_OBJECT_NAMES = get_hardcoded_object_names()
CORE_HARDcoded_MODELS = get_hardcoded_model_map()


class BusinessObjectService:
    """
    Service for managing business objects in the hybrid architecture.

    Handles both hardcoded Django models and low-code custom objects,
    providing a unified interface for the metadata engine.
    """

    @staticmethod
    def _iter_supported_model_fields(model_class):
        for field in model_class._meta.get_fields():
            is_reverse_relation = bool(field.auto_created and getattr(field, 'one_to_many', False))
            if is_reverse_relation:
                continue
            if field.auto_created and not getattr(field, 'concrete', False):
                continue
            if getattr(field, 'many_to_many', False):
                continue
            if field.is_relation and not getattr(field, 'many_to_one', False) and not getattr(field, 'one_to_one', False):
                continue
            yield field

    def __init__(self):
        self.hardcoded_object_sync_service = HardcodedObjectSyncService()
        self.query_service = BusinessObjectQueryService()

    def get_all_objects(
        self,
        organization_id: Optional[str] = None,
        include_hardcoded: bool = True,
        include_custom: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all business objects, grouped by type.

        Args:
            organization_id: Filter by organization (for custom objects)
            include_hardcoded: Include hardcoded Django models
            include_custom: Include low-code custom objects

        Returns:
            Dict with 'hardcoded' and 'custom' lists
        """
        result = {
            'hardcoded': [],
            'custom': []
        }
        return self.query_service.get_all_objects(
            organization_id=organization_id,
            include_hardcoded=include_hardcoded,
            include_custom=include_custom,
        )

    def get_model_class(self, object_code: str):
        """
        Backward-compatible alias used by older callers.

        The service's canonical method is `get_django_model`, but several
        runtime call sites still reference `get_model_class`.
        """
        return self.get_django_model(object_code)

    def get_reference_options(
        self,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get objects available for reference field selection.

        Returns a flat list with type indicator for UI display.

        Args:
            organization_id: Filter by organization (for custom objects)

        Returns:
            List of objects with 'value', 'label', and 'type' keys
        """
        return self.query_service.get_reference_options(organization_id=organization_id)

    def get_object_fields(
        self,
        object_code: str,
        organization_id: Optional[str] = None,
        *,
        context: str = 'form',
        include_relations: bool = False,
        locale: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get field definitions for a specific business object.

        Args:
            object_code: Business object code
            organization_id: Organization context

        Returns:
            Dict with object info and fields list
        """
        return self.query_service.get_object_fields(
            object_code,
            context=context,
            include_relations=include_relations,
            locale=locale,
        )

    def get_object_by_code(
        self,
        code: str,
        organization_id: Optional[str] = None
    ) -> Optional[BusinessObject]:
        """
        Get a business object by code.

        For hardcoded models, returns the BusinessObject metadata.
        For custom objects, returns the actual BusinessObject instance.

        Args:
            code: Object code
            organization_id: Organization context

        Returns:
            BusinessObject instance or None
        """
        try:
            return BusinessObject.objects.get(code=code, is_deleted=False)
        except BusinessObject.DoesNotExist:
            return None

    def _get_hardcoded_definition(self, object_code: str):
        return get_hardcoded_object_definition(object_code)

    def _get_hardcoded_model_path(self, object_code: str) -> Optional[str]:
        obj = self.get_object_by_code(object_code)
        if obj and obj.is_hardcoded and obj.django_model_path:
            return obj.django_model_path

        definition = self._get_hardcoded_definition(object_code)
        if definition:
            return definition.django_model_path
        return None

    def is_hardcoded_model(self, object_code: str) -> bool:
        """Check if an object code refers to a hardcoded model."""
        return self.query_service.is_hardcoded_model(object_code)

    def get_django_model(self, object_code: str):
        """
        Get the Django model class for a hardcoded object.

        Args:
            object_code: Object code

        Returns:
            Django model class or None
        """
        if not self.is_hardcoded_model(object_code):
            return None

        model_path = self._get_hardcoded_model_path(object_code)
        if not model_path:
            return None

        try:
            return import_string(model_path)
        except ImportError:
            return None

    def register_hardcoded_object(
        self,
        code: str,
        name: str,
        name_en: str = '',
        organization_id: Optional[str] = None
    ) -> BusinessObject:
        """
        Register a hardcoded model as a BusinessObject.

        Args:
            code: Object code (must be in CORE_HARDcoded_MODELS)
            name: Display name
            name_en: English display name
            organization_id: Organization (None for system-wide)

        Returns:
            Created or updated BusinessObject
        """
        definition = self._get_hardcoded_definition(code)
        if not definition:
            raise ValueError(f'Unknown hardcoded model: {code}')
        sync_result = self.hardcoded_object_sync_service.ensure_business_object(
            definition,
            overwrite_existing=True,
        )
        obj = sync_result.business_object

        updated_fields = []
        if obj.name != (name or definition.name):
            obj.name = name or definition.name
            updated_fields.append('name')
        if obj.name_en != (name_en or definition.name_en):
            obj.name_en = name_en or definition.name_en
            updated_fields.append('name_en')
        if organization_id and obj.organization_id != organization_id:
            obj.organization_id = organization_id
            updated_fields.append('organization')
        if updated_fields:
            obj.save(update_fields=updated_fields + ['updated_at'])

        return obj

    def sync_model_fields(
        self,
        object_code: str,
        organization_id: Optional[str] = None
    ) -> int:
        """
        Sync model fields for a hardcoded object.

        Creates/updates ModelFieldDefinition entries based on
        Django model metadata.

        Args:
            object_code: Object code (must be hardcoded)
            organization_id: Organization context

        Returns:
            Number of fields synced
        """
        model_class = self.get_django_model(object_code)
        if not model_class:
            raise ValueError(f'Cannot find Django model for: {object_code}')

        # Get or create BusinessObject
        obj = self.get_object_by_code(object_code)
        if not obj:
            raise ValueError(f'Business object not registered: {object_code}')

        # Get fields from the model
        fields = list(self._iter_supported_model_fields(model_class))
        canonical_field_names = {field.name for field in fields}

        # Sync each field
        count = 0
        for index, field in enumerate(fields, start=1):
            field_def = ModelFieldDefinition.from_django_field(obj, field)
            field_def.sort_order = index

            # Special handling for JSONField-based file/image fields
            # Fields named 'images' or containing 'image' should use 'image' type
            # Fields named 'attachments' or containing 'attachment' should use 'file' type
            field_name_lower = field.name.lower()
            if field_name_lower in ('images', 'image') or field_name_lower.endswith('_image') or field_name_lower.endswith('_images'):
                field_def.field_type = 'image'
            elif field_name_lower in ('attachments', 'attachment') or field_name_lower.endswith('_attachment') or field_name_lower.endswith('_attachments'):
                field_def.field_type = 'file'

            # Get or update
            existing = ModelFieldDefinition.all_objects.filter(
                business_object=obj,
                field_name=field.name
            ).first()

            if existing:
                # Update only mutable fields (including field_type for correct mapping)
                existing.display_name = field_def.display_name
                existing.display_name_en = field_def.display_name_en
                existing.field_type = field_def.field_type
                existing.sort_order = field_def.sort_order
                existing.is_deleted = False
                existing.save()
            else:
                # Set organization if provided
                if organization_id:
                    field_def.organization_id = organization_id
                field_def.save()

            count += 1

        ModelFieldDefinition.objects.filter(
            business_object=obj,
            is_deleted=False,
        ).exclude(field_name__in=canonical_field_names).update(is_deleted=True)

        return count


