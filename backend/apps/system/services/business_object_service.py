"""
Business Object Service for hybrid architecture.

Provides unified access to both hardcoded Django models and low-code
custom business objects.
"""
from typing import Dict, List, Optional, Any
from django.db.models import QuerySet
from django.utils.module_loading import import_string

from apps.system.object_catalog import (
    get_hardcoded_model_map,
    get_hardcoded_object_definition,
    get_hardcoded_object_names,
    iter_hardcoded_object_definitions,
)
from apps.system.models import (
    BusinessObject,
    ModelFieldDefinition,
    FieldDefinition,
)
from apps.system.layout_sections import get_field_section_metadata
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

        if include_hardcoded:
            result['hardcoded'] = self._get_hardcoded_objects()

        if include_custom:
            queryset = BusinessObject.objects.filter(is_deleted=False)
            if organization_id:
                queryset = queryset.filter(organization_id=organization_id)
            result['custom'] = self._format_custom_objects(
                queryset.filter(is_hardcoded=False)
            )

        return result

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
        result = []

        # Add hardcoded objects
        hardcoded = self._get_hardcoded_objects()
        for obj in hardcoded:
            result.append({
                'value': obj['code'],
                'label': obj['name'],
                'label_en': obj.get('name_en', ''),
                'type': 'hardcoded',
                'app_label': obj.get('app_label', ''),
                'icon': self._get_object_icon(obj['code'])
            })

        # Add custom objects
        queryset = BusinessObject.objects.filter(
            is_deleted=False,
            is_hardcoded=False
        )
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        for obj in queryset:
            result.append({
                'value': obj.code,
                'label': obj.name,
                'label_en': obj.name_en or '',
                'type': 'custom',
                'icon': 'document'
            })

        return result

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
        # Check if it's a hardcoded model
        if self.is_hardcoded_model(object_code):
            return self._get_hardcoded_object_fields(
                object_code,
                context=context,
                include_relations=include_relations,
                locale=locale,
            )

        # Otherwise, it's a custom low-code object
        try:
            obj = BusinessObject.objects.get(code=object_code, is_deleted=False)
            return self._get_custom_object_fields(
                obj,
                context=context,
                include_relations=include_relations,
                locale=locale,
            )
        except BusinessObject.DoesNotExist:
            return {
                'error': f'Business object "{object_code}" not found'
            }

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
        obj = self.get_object_by_code(object_code)
        if obj and obj.is_hardcoded:
            return True
        return self._get_hardcoded_definition(object_code) is not None

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

    def _get_hardcoded_objects(self) -> List[Dict[str, Any]]:
        """Get list of hardcoded objects from registry."""
        result = []
        for definition in iter_hardcoded_object_definitions():
            # Try to get name from BusinessObject if registered
            code = definition.code
            name = definition.name
            name_en = definition.name_en
            model_path = definition.django_model_path

            try:
                obj = BusinessObject.objects.get(code=code)
                name = obj.name
                name_en = obj.name_en or ''
            except BusinessObject.DoesNotExist:
                pass

            result.append({
                'code': code,
                'name': name,
                'name_en': name_en,
                'app_label': definition.app_label,
                'model_path': model_path,
                'type': 'hardcoded'
            })

        return sorted(result, key=lambda x: x['code'])

    def _format_custom_objects(
        self,
        queryset: QuerySet
    ) -> List[Dict[str, Any]]:
        """Format custom low-code objects for API response."""
        return [{
            'code': obj.code,
            'name': obj.name,
            'name_en': obj.name_en or '',
            'table_name': obj.table_name,
            'field_count': obj.field_definitions.count(),
            'layout_count': obj.page_layouts.count(),
            'type': 'custom',
            'enable_workflow': obj.enable_workflow,
        } for obj in queryset]

    def _should_show_model_field_in_context(self, field_def: ModelFieldDefinition, context: str) -> bool:
        if context == 'list':
            return bool(getattr(field_def, 'show_in_list', True))
        if context == 'detail':
            return bool(getattr(field_def, 'show_in_detail', True))
        return bool(getattr(field_def, 'show_in_form', True))

    def _should_show_custom_field_in_context(self, field_def: FieldDefinition, context: str) -> bool:
        if context == 'list':
            return bool(getattr(field_def, 'show_in_list', False))
        if context == 'detail':
            return bool(getattr(field_def, 'show_in_detail', True))
        return bool(getattr(field_def, 'show_in_form', True))

    def _get_hardcoded_object_fields(
        self,
        object_code: str,
        *,
        context: str = 'form',
        include_relations: bool = False,
        locale: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get fields for a hardcoded object."""
        # Get BusinessObject metadata
        try:
            obj = BusinessObject.objects.get(code=object_code)
        except BusinessObject.DoesNotExist:
            definition = self._get_hardcoded_definition(object_code)
            if not definition:
                return {
                    'error': f'Business object "{object_code}" not registered'
                }
            obj = BusinessObject(
                code=definition.code,
                name=definition.name,
                name_en=definition.name_en,
                is_hardcoded=True,
                django_model_path=definition.django_model_path,
            )

        # Get the Django model class
        model_class = self.get_django_model(object_code)
        if not model_class:
            return {
                'error': f'Django model not found for: {object_code}'
            }

        normalized_context = context if context in {'form', 'detail', 'list'} else 'form'

        # Generate field definitions directly from Django model (real-time)
        # This ensures field type detection fixes are applied immediately
        fields = []
        for field in model_class._meta.get_fields():
            # Skip auto-generated relations unless explicitly requested.
            is_reverse_relation = bool(field.auto_created and getattr(field, 'one_to_many', False))
            if field.auto_created and not is_reverse_relation:
                continue
            if is_reverse_relation:
                if not include_relations:
                    continue
                relation_code = getattr(field, 'get_accessor_name', lambda: field.name)() or field.name
                fields.append({
                    'fieldName': relation_code,
                    'displayName': relation_code,
                    'displayNameEn': relation_code,
                    'fieldType': 'sub_table',
                    'djangoFieldType': field.__class__.__name__,
                    'isRequired': False,
                    'isReadonly': True,
                    'isEditable': False,
                    'isUnique': False,
                    'showInList': False,
                    'showInDetail': True,
                    'showInForm': False,
                    'sortOrder': 0,
                    'referenceModelPath': '',
                    'maxLength': None,
                    'decimalPlaces': None,
                    'isReverseRelation': True,
                    'reverseRelationModel': '',
                    'reverseRelationField': '',
                    'relationDisplayMode': 'tab_readonly',
                })
                continue

            if field.is_relation and not field.many_to_one and not field.one_to_many:
                continue

            # Use ModelFieldDefinition.from_django_field to get correct field type
            field_def = ModelFieldDefinition.from_django_field(obj, field)
            section_meta = get_field_section_metadata(object_code, field_def.field_name, locale=locale)

            if not self._should_show_model_field_in_context(field_def, normalized_context):
                continue

            fields.append({
                'fieldName': field_def.field_name,
                'displayName': field_def.display_name,
                'displayNameEn': field_def.display_name_en or '',
                'fieldType': field_def.field_type,
                'djangoFieldType': field_def.django_field_type,
                'isRequired': field_def.is_required,
                'isReadonly': field_def.is_readonly,
                'isEditable': field_def.is_editable,
                'isUnique': field_def.is_unique,
                'showInList': field_def.show_in_list,
                'showInDetail': field_def.show_in_detail,
                'showInForm': field_def.show_in_form,
                'sortOrder': field_def.sort_order,
                'referenceModelPath': field_def.reference_model_path,
                'maxLength': field_def.max_length,
                'decimalPlaces': field_def.decimal_places,
                'isReverseRelation': False,
                'sectionName': section_meta['section_name'],
                'sectionTitle': section_meta['section_title'],
                'sectionTitleI18n': section_meta['section_title_i18n'],
                'sectionTranslationKey': section_meta['section_translation_key'],
                'sectionIcon': section_meta['section_icon'],
            })

        return {
            'objectCode': obj.code,
            'objectName': obj.name,
            'objectNameEn': obj.name_en or '',
            'isHardcoded': True,
            'modelPath': obj.django_model_path,
            'fields': fields
        }

    def _get_custom_object_fields(
        self,
        obj: BusinessObject,
        *,
        context: str = 'form',
        include_relations: bool = False,
        locale: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get fields for a custom low-code object."""
        normalized_context = context if context in {'form', 'detail', 'list'} else 'form'
        rows = []
        queryset = obj.field_definitions.filter(is_deleted=False).order_by('sort_order')
        for f in queryset:
            if getattr(f, 'is_reverse_relation', False) and not include_relations:
                continue
            if not self._should_show_custom_field_in_context(f, normalized_context):
                continue
            section_meta = get_field_section_metadata(obj.code, f.code, locale=locale)
            rows.append(
                {
                    'field_name': f.code,
                    'display_name': f.name,
                    'field_type': f.field_type,
                    'is_required': f.is_required,
                    'is_readonly': f.is_readonly,
                    'is_unique': f.is_unique,
                    'show_in_list': f.show_in_list,
                    'show_in_detail': f.show_in_detail,
                    'show_in_form': f.show_in_form,
                    'sort_order': f.sort_order,
                    'options': f.options,
                    'reference_object': f.reference_object,
                    'formula': f.formula,
                    'is_reverse_relation': getattr(f, 'is_reverse_relation', False),
                    'reverse_relation_model': getattr(f, 'reverse_relation_model', ''),
                    'reverse_relation_field': getattr(f, 'reverse_relation_field', ''),
                    'relation_display_mode': getattr(f, 'relation_display_mode', 'tab_readonly'),
                    'section_name': section_meta['section_name'],
                    'section_title': section_meta['section_title'],
                    'section_title_i18n': section_meta['section_title_i18n'],
                    'section_translation_key': section_meta['section_translation_key'],
                    'section_icon': section_meta['section_icon'],
                }
            )

        return {
            'object_code': obj.code,
            'object_name': obj.name,
            'object_name_en': obj.name_en or '',
            'is_hardcoded': False,
            'table_name': obj.table_name,
            'fields': rows
        }

    def _get_object_icon(self, code: str) -> str:
        """Get icon name for an object code."""
        definition = self._get_hardcoded_definition(code)
        if definition:
            return definition.icon
        return 'document'

