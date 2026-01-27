"""
Metadata Service - manages business objects, field definitions, and page layouts.

This service provides a high-level API for creating and managing metadata
without directly manipulating database models.
"""
from typing import Dict, List, Optional, Any
from django.db import transaction
from django.utils import timezone
from apps.system.models import BusinessObject, FieldDefinition, PageLayout
from apps.common.services.base_crud import BaseCRUDService


class MetadataService(BaseCRUDService):
    """
    Metadata Service for managing business object metadata.

    Inherits from BaseCRUDService which provides:
    - Standard CRUD methods (create, update, delete, get, query)
    - Organization isolation
    - Pagination support
    - Batch operations
    """

    def __init__(self):
        """Initialize with BusinessObject model."""
        super().__init__(BusinessObject)
        # Simple in-memory cache for metadata
        self._cache = {}

    @transaction.atomic
    def create_business_object(self, data: Dict) -> BusinessObject:
        """
        Create or update a business object with complete metadata.

        This method creates a business object along with its field definitions
        and page layouts in a single transaction.

        Args:
            data: Dictionary containing:
                - code: Business object code (unique)
                - name: Business object name
                - name_en: English name (optional)
                - description: Description (optional)
                - enable_workflow: Enable workflow flag (default: False)
                - enable_version: Enable version control (default: True)
                - enable_soft_delete: Enable soft delete (default: True)
                - fields: List of field definitions
                - page_layouts: List of page layouts

        Returns:
            BusinessObject: The created or updated business object
        """
        # Create or update business object
        obj, created = BusinessObject.objects.get_or_create(
            code=data['code'],
            defaults={
                'name': data['name'],
                'name_en': data.get('name_en', ''),
                'description': data.get('description', ''),
                'enable_workflow': data.get('enable_workflow', False),
                'enable_version': data.get('enable_version', True),
                'enable_soft_delete': data.get('enable_soft_delete', True),
            }
        )

        if not created:
            # Update existing object
            obj.name = data['name']
            obj.name_en = data.get('name_en', '')
            obj.description = data.get('description', '')
            obj.enable_workflow = data.get('enable_workflow', False)
            obj.enable_version = data.get('enable_version', True)
            obj.enable_soft_delete = data.get('enable_soft_delete', True)
            obj.save()

        # Create or update field definitions
        for field_data in data.get('fields', []):
            self._create_or_update_field(obj, field_data)

        # Create or update page layouts
        for layout_data in data.get('page_layouts', []):
            self._create_or_update_layout(obj, layout_data)

        # Clear cache
        self._clear_cache(obj.code)

        return obj

    def _create_or_update_field(self, obj: BusinessObject, data: Dict) -> FieldDefinition:
        """
        Create or update a field definition.

        Args:
            obj: Business object
            data: Field definition data

        Returns:
            FieldDefinition: The created or updated field
        """
        field, created = FieldDefinition.objects.get_or_create(
            business_object=obj,
            code=data['code'],
            defaults={
                'name': data['name'],
                'field_type': data.get('field_type', 'text'),
                'is_required': data.get('is_required', False),
                'is_unique': data.get('is_unique', False),
                'is_readonly': data.get('is_readonly', False),
                'is_system': data.get('is_system', False),
                'is_searchable': data.get('is_searchable', False),
                'show_in_list': data.get('show_in_list', False),
                'show_in_detail': data.get('show_in_detail', True),
                'show_in_filter': data.get('show_in_filter', False),
                'sort_order': data.get('sort_order', 0),
                'column_width': data.get('column_width'),
                'min_column_width': data.get('min_column_width'),
                'fixed': data.get('fixed', ''),
                'sortable': data.get('sortable', True),
                'default_value': data.get('default_value', ''),
                'options': data.get('options', []),
                'reference_object': data.get('reference_object', ''),
                'reference_display_field': data.get('reference_display_field', 'name'),
                'decimal_places': data.get('decimal_places', 2),
                'min_value': data.get('min_value'),
                'max_value': data.get('max_value'),
                'max_length': data.get('max_length', 255),
                'placeholder': data.get('placeholder', ''),
                'regex_pattern': data.get('regex_pattern', ''),
                'formula': data.get('formula', ''),
                'sub_table_fields': data.get('sub_table_fields', []),
            }
        )

        if not created:
            # Update existing field
            for key, value in data.items():
                if hasattr(field, key) and key not in ['business_object', 'code']:
                    setattr(field, key, value)
            field.save()

        return field

    def _create_or_update_layout(self, obj: BusinessObject, data: Dict) -> PageLayout:
        """
        Create or update a page layout.

        Args:
            obj: Business object
            data: Layout configuration data

        Returns:
            PageLayout: The created or updated layout
        """
        layout, created = PageLayout.objects.get_or_create(
            business_object=obj,
            layout_code=data['layout_code'],
            defaults={
                'layout_name': data.get('layout_name', data['layout_code']),
                'layout_type': data.get('layout_type', 'form'),
                'layout_config': data.get('layout_config', {}),
                'is_default': data.get('is_default', False),
                'is_active': data.get('is_active', True),
            }
        )

        if not created:
            # Update existing layout
            layout.layout_name = data.get('layout_name', data['layout_code'])
            layout.layout_type = data.get('layout_type', 'form')
            layout.layout_config = data.get('layout_config', {})
            layout.is_active = data.get('is_active', True)
            layout.save()

        # Set as default layout if specified
        if data.get('is_default'):
            if layout.layout_type == 'form':
                obj.default_form_layout = layout
            elif layout.layout_type == 'list':
                obj.default_list_layout = layout
            obj.save()

        return layout

    def get_business_object(self, code: str) -> Optional[BusinessObject]:
        """
        Get business object by code (with caching).

        Args:
            code: Business object code

        Returns:
            BusinessObject or None if not found
        """
        if code not in self._cache:
            try:
                obj = BusinessObject.objects.get(code=code, is_deleted=False)
                self._cache[code] = obj
            except BusinessObject.DoesNotExist:
                return None
        return self._cache[code]

    def get_field_definitions(self, obj_code: str) -> List[FieldDefinition]:
        """
        Get all field definitions for a business object.

        Args:
            obj_code: Business object code

        Returns:
            List of field definitions ordered by sort_order
        """
        obj = self.get_business_object(obj_code)
        if not obj:
            return []
        return list(obj.field_definitions.all().order_by('sort_order', 'code'))

    def get_page_layout(self, obj_code: str, layout_code: str) -> Optional[PageLayout]:
        """
        Get a specific page layout for a business object.

        Args:
            obj_code: Business object code
            layout_code: Layout code

        Returns:
            PageLayout or None if not found
        """
        obj = self.get_business_object(obj_code)
        if not obj:
            return None
        try:
            return obj.page_layouts.get(
                layout_code=layout_code,
                is_active=True
            )
        except PageLayout.DoesNotExist:
            return None

    def get_page_layouts(self, obj_code: str, layout_type: str = None) -> List[PageLayout]:
        """
        Get all page layouts for a business object.

        Args:
            obj_code: Business object code
            layout_type: Optional filter by layout type

        Returns:
            List of page layouts
        """
        obj = self.get_business_object(obj_code)
        if not obj:
            return []

        layouts = obj.page_layouts.filter(is_active=True)
        if layout_type:
            layouts = layouts.filter(layout_type=layout_type)

        return list(layouts)

    def delete_business_object(self, code: str) -> bool:
        """
        Delete a business object (soft delete).

        Args:
            code: Business object code

        Returns:
            True if deleted, False if not found
        """
        obj = self.get_business_object(code)
        if obj:
            obj.soft_delete()
            self._clear_cache(code)
            return True
        return False

    def _clear_cache(self, code: str = None):
        """
        Clear the metadata cache.

        Args:
            code: Specific code to clear, or None to clear all
        """
        if code:
            self._cache.pop(code, None)
        else:
            self._cache.clear()

    def export_business_object(self, code: str) -> Dict:
        """
        Export a business object definition as JSON-serializable dict.

        Args:
            code: Business object code

        Returns:
            Dictionary containing the complete business object definition
        """
        obj = self.get_business_object(code)
        if not obj:
            return None

        return {
            'code': obj.code,
            'name': obj.name,
            'name_en': obj.name_en,
            'description': obj.description,
            'enable_workflow': obj.enable_workflow,
            'enable_version': obj.enable_version,
            'enable_soft_delete': obj.enable_soft_delete,
            'table_name': obj.table_name,
            'fields': [
                {
                    'code': f.code,
                    'name': f.name,
                    'field_type': f.field_type,
                    'is_required': f.is_required,
                    'is_unique': f.is_unique,
                    'is_readonly': f.is_readonly,
                    'is_system': f.is_system,
                    'is_searchable': f.is_searchable,
                    'show_in_list': f.show_in_list,
                    'show_in_detail': f.show_in_detail,
                    'show_in_filter': f.show_in_filter,
                    'sort_order': f.sort_order,
                    'column_width': f.column_width,
                    'min_column_width': f.min_column_width,
                    'fixed': f.fixed,
                    'sortable': f.sortable,
                    'default_value': f.default_value,
                    'options': f.options,
                    'reference_object': f.reference_object,
                    'reference_display_field': f.reference_display_field,
                    'decimal_places': f.decimal_places,
                    'min_value': str(f.min_value) if f.min_value is not None else None,
                    'max_value': str(f.max_value) if f.max_value is not None else None,
                    'max_length': f.max_length,
                    'placeholder': f.placeholder,
                    'regex_pattern': f.regex_pattern,
                    'formula': f.formula,
                    'sub_table_fields': f.sub_table_fields,
                }
                for f in obj.field_definitions.all()
            ],
            'page_layouts': [
                {
                    'layout_code': l.layout_code,
                    'layout_name': l.layout_name,
                    'layout_type': l.layout_type,
                    'layout_config': l.layout_config,
                    'is_default': l.business_object.default_form_layout_id == l.id or
                                  l.business_object.default_list_layout_id == l.id,
                    'is_active': l.is_active,
                }
                for l in obj.page_layouts.all()
            ],
        }
