"""
Layout Generator Service - Auto-generate default layouts from field definitions.

This service provides functionality to automatically generate default layout
configurations (list, form, detail) from ModelFieldDefinition or FieldDefinition
records when no explicit PageLayout exists.

This ensures all business objects have usable layouts immediately without
requiring manual layout configuration.
"""

from collections import OrderedDict
from typing import Dict, List, Any, Optional
from apps.system.models import BusinessObject, ModelFieldDefinition, FieldDefinition, PageLayout
from apps.system.layout_sections import get_object_section_definitions, resolve_section_definition


class LayoutGenerator:
    """
    Generate default layout configurations from field definitions.

    Supports both hardcoded objects (ModelFieldDefinition) and
    dynamic objects (FieldDefinition).
    """

    # Default column widths for different field types
    DEFAULT_COLUMN_WIDTHS = {
        'text': 150,
        'number': 120,
        'currency': 120,
        'percent': 100,
        'date': 140,
        'datetime': 160,
        'boolean': 80,
        'select': 120,
        'user': 120,
        'department': 150,
        'reference': 150,
        'status': 100,
    }

    # Fields that should always be included in list view
    DEFAULT_LIST_FIELDS = ['code', 'name', 'status', 'created_at']

    # Fields to exclude from auto-generated layouts
    EXCLUDED_FIELDS = ['id', 'organization', 'is_deleted', 'deleted_at', 'deleted_by']
    ACTION_LABEL = {
        'zh': '操作',
        'en': 'Actions',
    }

    @classmethod
    def _is_model_field_candidate(cls, field_def: ModelFieldDefinition) -> bool:
        return (
            field_def.field_name not in cls.EXCLUDED_FIELDS
            and getattr(field_def, 'field_type', '') != 'sub_table'
        )

    @classmethod
    def _is_dynamic_field_candidate(cls, field_def: FieldDefinition) -> bool:
        return (
            field_def.code not in cls.EXCLUDED_FIELDS
            and not getattr(field_def, 'is_reverse_relation', False)
            and getattr(field_def, 'field_type', '') != 'sub_table'
        )

    @classmethod
    def _select_model_fields_for_layout(
        cls,
        business_object: BusinessObject,
        visibility_attr: str,
    ) -> List[ModelFieldDefinition]:
        all_fields = [
            field_def
            for field_def in ModelFieldDefinition.objects.filter(
                business_object=business_object
            ).order_by('sort_order')
            if cls._is_model_field_candidate(field_def)
        ]
        visible_fields = [
            field_def for field_def in all_fields
            if getattr(field_def, visibility_attr, True)
        ]
        return visible_fields or all_fields

    @classmethod
    def _select_dynamic_fields_for_layout(
        cls,
        business_object: BusinessObject,
        visibility_attr: str,
    ) -> List[FieldDefinition]:
        all_fields = [
            field_def
            for field_def in FieldDefinition.objects.filter(
                business_object=business_object,
                is_deleted=False
            ).order_by('sort_order')
            if cls._is_dynamic_field_candidate(field_def)
        ]
        visible_fields = [
            field_def for field_def in all_fields
            if getattr(field_def, visibility_attr, True)
        ]
        return visible_fields or all_fields

    @classmethod
    def generate_list_layout(cls, business_object: BusinessObject) -> Dict[str, Any]:
        """
        Generate default list layout configuration.

        Creates a column configuration with:
        - Selection column
        - Default display fields (code, name, status, created_at)
        - Additional fields marked with show_in_list=True

        Args:
            business_object: BusinessObject instance

        Returns:
            Dictionary with list layout configuration
        """
        if business_object.is_hardcoded:
            columns = cls._generate_list_columns_from_model_fields(business_object)
        else:
            columns = cls._generate_list_columns_from_field_definitions(business_object)

        return {
            'columns': columns,
            'rowSelection': True,
            'pagination': True,
            'pageSize': 20
        }

    @classmethod
    def _generate_list_columns_from_model_fields(cls, business_object: BusinessObject) -> List[Dict[str, Any]]:
        """Generate list columns from ModelFieldDefinition records."""
        model_fields = cls._select_model_fields_for_layout(business_object, 'show_in_list')

        columns = []
        added_fields = set()

        # Add default fields first
        for field_name in cls.DEFAULT_LIST_FIELDS:
            field_def = next((f for f in model_fields if f.field_name == field_name), None)
            if field_def:
                columns.append(cls._model_field_to_column(field_def))
                added_fields.add(field_name)

        # Add the remaining fields so the generated system layout covers the full schema.
        for field_def in model_fields:
            if field_def.field_name not in added_fields:
                columns.append(cls._model_field_to_column(field_def))
                added_fields.add(field_def.field_name)

        # Add actions column
        columns.append({
            'fieldCode': 'actions',
            'prop': 'actions',
            'label': cls.ACTION_LABEL,
            'width': 180,
            'fixed': 'right',
            'type': 'actions',
            'slot': 'actions'
        })

        return columns

    @classmethod
    def _generate_list_columns_from_field_definitions(cls, business_object: BusinessObject) -> List[Dict[str, Any]]:
        """Generate list columns from FieldDefinition records."""
        field_definitions = cls._select_dynamic_fields_for_layout(business_object, 'show_in_list')

        columns = []
        added_fields = set()

        # Add default fields first
        for field_name in cls.DEFAULT_LIST_FIELDS:
            field_def = next((f for f in field_definitions if f.code == field_name), None)
            if field_def:
                columns.append(cls._field_definition_to_column(field_def))
                added_fields.add(field_name)

        # Add the remaining fields so the generated system layout covers the full schema.
        for field_def in field_definitions:
            if field_def.code not in added_fields:
                columns.append(cls._field_definition_to_column(field_def))
                added_fields.add(field_def.code)

        # Add actions column
        columns.append({
            'fieldCode': 'actions',
            'prop': 'actions',
            'label': cls.ACTION_LABEL,
            'width': 180,
            'fixed': 'right',
            'type': 'actions',
            'slot': 'actions'
        })

        return columns

    @classmethod
    def _model_field_to_column(cls, field_def: ModelFieldDefinition) -> Dict[str, Any]:
        """Convert ModelFieldDefinition to column configuration."""
        # ModelFieldDefinition does not always expose column sizing/fixed attrs
        # (especially in older schemas). Use safe getattr fallbacks.
        width = getattr(field_def, 'column_width', None) or cls.DEFAULT_COLUMN_WIDTHS.get(field_def.field_type, 150)

        column = {
            'fieldCode': field_def.field_name,
            'prop': field_def.field_name,
            'label': field_def.display_name or field_def.field_name,
            'width': width,
            'sortable': True,
            'visible': True,
            'type': cls._map_field_type_to_column_type(field_def.field_type)
        }

        # Add fixed position if specified
        fixed = getattr(field_def, 'fixed', None)
        if fixed:
            column['fixed'] = fixed

        # Determine if slot rendering is needed
        if field_def.field_type in ['user', 'department', 'reference']:
            column['slot'] = field_def.field_name
            column['requiresSlot'] = True

        return column

    @classmethod
    def _field_definition_to_column(cls, field_def: FieldDefinition) -> Dict[str, Any]:
        """Convert FieldDefinition to column configuration."""
        width = field_def.column_width or cls.DEFAULT_COLUMN_WIDTHS.get(field_def.field_type, 150)

        column = {
            'fieldCode': field_def.code,
            'prop': field_def.code,
            'label': field_def.name,
            'width': width,
            'sortable': field_def.sortable if hasattr(field_def, 'sortable') else True,
            'visible': True,
            'type': cls._map_field_type_to_column_type(field_def.field_type)
        }

        # Add fixed position if specified
        if field_def.fixed:
            column['fixed'] = field_def.fixed

        # Add min column width if specified
        if field_def.min_column_width:
            column['minWidth'] = field_def.min_column_width

        # Determine if slot rendering is needed
        if field_def.field_type in ['user', 'department', 'reference', 'asset']:
            column['slot'] = field_def.code
            column['requiresSlot'] = True

        return column

    @classmethod
    def _map_field_type_to_column_type(cls, field_type: str) -> str:
        """Map field type to column display type."""
        type_mapping = {
            'text': 'text',
            'textarea': 'text',
            'number': 'number',
            'currency': 'currency',
            'percent': 'percent',
            'date': 'date',
            'datetime': 'datetime',
            'boolean': 'tag',
            'select': 'tag',
            'multi_select': 'tag',
            'radio': 'tag',
            'user': 'slot',
            'department': 'slot',
            'reference': 'slot',
            'asset': 'slot',
            'status': 'tag',
            'image': 'image',
            'file': 'link',
        }
        return type_mapping.get(field_type, 'text')

    @classmethod
    def generate_form_layout(cls, business_object: BusinessObject) -> Dict[str, Any]:
        """
        Generate default form layout configuration.

        Groups fields into logical sections:
        - Basic Info (基本信息)
        - Details (详细信息)
        - System Info (系统信息) - created_at, updated_at, etc.

        Args:
            business_object: BusinessObject instance

        Returns:
            Dictionary with form layout configuration
        """
        if business_object.is_hardcoded:
            return cls._generate_form_from_model_fields(business_object, 'show_in_form')
        else:
            return cls._generate_form_from_field_definitions(business_object, 'show_in_form')

    @classmethod
    def _generate_form_from_model_fields(
        cls,
        business_object: BusinessObject,
        visibility_attr: str,
    ) -> Dict[str, Any]:
        """Generate form layout from ModelFieldDefinition records."""
        model_fields = cls._select_model_fields_for_layout(business_object, visibility_attr)
        return {
            'sections': cls._build_form_sections(
                business_object.code,
                model_fields,
                lambda field_def: cls._model_field_to_form_field(field_def),
                readonly=False,
            )
        }

    @classmethod
    def _generate_form_from_field_definitions(
        cls,
        business_object: BusinessObject,
        visibility_attr: str,
    ) -> Dict[str, Any]:
        """Generate form layout from FieldDefinition records."""
        field_definitions = cls._select_dynamic_fields_for_layout(business_object, visibility_attr)
        return {
            'sections': cls._build_form_sections(
                business_object.code,
                field_definitions,
                lambda field_def: cls._field_definition_to_form_field(field_def),
                readonly=False,
            )
        }

    @classmethod
    def _build_form_sections(
        cls,
        object_code: str,
        fields: List[Any],
        field_builder,
        *,
        readonly: bool,
    ) -> List[Dict[str, Any]]:
        sections = OrderedDict()
        for section in get_object_section_definitions(object_code):
            sections[section['id']] = {
                'id': section['id'],
                'name': section['id'],
                'type': 'section',
                'title': section['title'],
                'icon': section.get('icon'),
                'columns': section.get('columns', 2),
                'column': section.get('columns', 2),
                'collapsible': section.get('collapsible', False),
                'collapsed': section.get('collapsed', False),
                'order': section.get('order', 0),
                'fields': [],
            }

        for field_def in fields:
            field_code = getattr(field_def, 'field_name', None) or getattr(field_def, 'code', None)
            if not field_code:
                continue

            section_definition = resolve_section_definition(object_code, str(field_code))
            section = sections.setdefault(
                section_definition['id'],
                {
                    'id': section_definition['id'],
                    'name': section_definition['id'],
                    'type': 'section',
                    'title': section_definition['title'],
                    'icon': section_definition.get('icon'),
                    'columns': section_definition.get('columns', 2),
                    'column': section_definition.get('columns', 2),
                    'collapsible': section_definition.get('collapsible', False),
                    'collapsed': section_definition.get('collapsed', False),
                    'order': section_definition.get('order', 999),
                    'fields': [],
                },
            )
            field_config = field_builder(field_def)
            field_config['sectionName'] = section_definition['id']
            field_config['sectionTitle'] = section_definition['title']
            if readonly or section_definition.get('readonly'):
                field_config['readonly'] = True
            section['fields'].append(field_config)

        ordered = [
            section
            for section in sorted(sections.values(), key=lambda item: (item.get('order', 0), item.get('id', '')))
            if section.get('fields')
        ]
        for section in ordered:
            section.pop('order', None)
        return ordered

    @classmethod
    def _model_field_to_form_field(cls, field_def: ModelFieldDefinition) -> Dict[str, Any]:
        """Convert ModelFieldDefinition to form field configuration."""
        config = {
            'fieldCode': field_def.field_name,
            'prop': field_def.field_name,
            'label': field_def.display_name or field_def.field_name,
            'fieldType': field_def.field_type,
            'required': field_def.is_required,
            'readonly': field_def.is_readonly,
            'span': 12  # Default half width (2 columns per row)
        }

        # Add reference config for ForeignKey fields
        if field_def.field_type == 'reference' and field_def.reference_model_path:
            config['referenceObject'] = field_def.reference_model_path
            config['displayField'] = field_def.reference_display_field or 'name'

        # Add number field constraints
        if field_def.field_type in ['number', 'currency']:
            if field_def.max_digits:
                config['maxDigits'] = field_def.max_digits
            if field_def.decimal_places:
                config['decimalPlaces'] = field_def.decimal_places

        # Add text field constraints
        if field_def.max_length:
            config['maxLength'] = field_def.max_length

        # Mark for slot rendering if needed
        if field_def.field_type in ['user', 'department', 'reference']:
            config['type'] = 'slot'

        # Extract field choices from Django model for select-type fields
        options = cls._get_django_field_choices(field_def)
        if options:
            config['options'] = options
            # If field has choices, it should be rendered as select
            if config['fieldType'] == 'text':
                config['fieldType'] = 'select'

        return config

    @classmethod
    def _get_django_field_choices(cls, field_def: ModelFieldDefinition) -> Optional[List[Dict[str, Any]]]:
        """
        Extract field choices from Django model for select-type fields.
        
        Args:
            field_def: ModelFieldDefinition instance
            
        Returns:
            List of options in format [{'value': 'v', 'label': 'Label'}, ...]
        """
        try:
            # Get the business object to find the Django model
            business_object = field_def.business_object
            if not business_object or not business_object.django_model_path:
                return None
                
            from django.utils.module_loading import import_string
            model_class = import_string(business_object.django_model_path)
            
            if not model_class:
                return None
                
            # Get the field from the model
            try:
                field = model_class._meta.get_field(field_def.field_name)
            except Exception:
                return None
            
            # Check if field has choices
            if hasattr(field, 'choices') and field.choices:
                choices = field.choices
                # Handle both tuple and list formats
                if isinstance(choices, (list, tuple)) and len(choices) > 0:
                    return [
                        {'value': choice[0], 'label': str(choice[1])}
                        for choice in choices
                    ]
            
            return None
        except Exception:
            return None

    @classmethod
    def _field_definition_to_form_field(cls, field_def: FieldDefinition) -> Dict[str, Any]:
        """Convert FieldDefinition to form field configuration."""
        config = {
            'fieldCode': field_def.code,
            'prop': field_def.code,
            'label': field_def.name,
            'fieldType': field_def.field_type,
            'required': field_def.is_required,
            'readonly': field_def.is_readonly,
            'span': field_def.span if hasattr(field_def, 'span') else 12
        }

        # Add reference config
        if field_def.field_type == 'reference' and field_def.reference_object:
            config['referenceObject'] = field_def.reference_object

        # Add options for select fields
        if field_def.options:
            config['options'] = field_def.options

        # Add validation constraints
        if hasattr(field_def, 'min_value') and field_def.min_value is not None:
            config['min'] = field_def.min_value
        if hasattr(field_def, 'max_value') and field_def.max_value is not None:
            config['max'] = field_def.max_value
        if hasattr(field_def, 'max_length') and field_def.max_length:
            config['maxLength'] = field_def.max_length

        # Add placeholder
        if hasattr(field_def, 'placeholder') and field_def.placeholder:
            config['placeholder'] = field_def.placeholder

        # Add default value
        if hasattr(field_def, 'default_value') and field_def.default_value:
            config['defaultValue'] = field_def.default_value

        # Mark for slot rendering if needed
        if field_def.field_type in ['user', 'department', 'reference', 'subtable']:
            config['type'] = 'slot'

        return config

    @classmethod
    def generate_detail_layout(cls, business_object: BusinessObject) -> Dict[str, Any]:
        """
        Generate default detail layout configuration.

        Similar to form layout but optimized for readonly display.

        Args:
            business_object: BusinessObject instance

        Returns:
            Dictionary with detail layout configuration
        """
        if business_object.is_hardcoded:
            model_fields = cls._select_model_fields_for_layout(business_object, 'show_in_detail')
            sections = cls._build_form_sections(
                business_object.code,
                model_fields,
                lambda field_def: cls._model_field_to_form_field(field_def),
                readonly=True,
            )
        else:
            field_definitions = cls._select_dynamic_fields_for_layout(business_object, 'show_in_detail')
            sections = cls._build_form_sections(
                business_object.code,
                field_definitions,
                lambda field_def: cls._field_definition_to_form_field(field_def),
                readonly=True,
            )

        return {'sections': sections}

    @classmethod
    def generate_all_layouts(cls, business_object: BusinessObject) -> Dict[str, Dict[str, Any]]:
        """
        Generate all default layouts for a business object.

        Args:
            business_object: BusinessObject instance

        Returns:
            Dictionary with all layout types
        """
        return {
            'list': cls.generate_list_layout(business_object),
            'form': cls.generate_form_layout(business_object),
            'detail': cls.generate_detail_layout(business_object),
        }

    @classmethod
    def get_or_generate_layout(cls, business_object: BusinessObject, layout_type: str, view_mode: str = '') -> Dict[str, Any]:
        """
        Get existing layout or generate default one.

        First checks if a PageLayout record exists. If not, generates
        a default layout configuration on-the-fly.

        Args:
            business_object: BusinessObject instance
            layout_type: Type of layout ('list', 'form', 'detail')
            view_mode: Optional view mode filter ('Detail', 'Compact').
                       When specified, only layouts matching this view_mode are returned.

        Returns:
            Layout configuration dictionary
        """
        # Try to get existing layout from database
        try:
            filters = {
                'business_object': business_object,
                'layout_type': layout_type,
                'is_active': True,
            }
            if view_mode:
                filters['view_mode'] = view_mode

            existing_layout = PageLayout.objects.filter(
                **filters
            ).order_by('-is_default', '-updated_at', '-created_at').first()

            if existing_layout and existing_layout.layout_config:
                return existing_layout.layout_config
        except Exception:
            pass

        # Generate default layout
        if layout_type == 'list':
            return cls.generate_list_layout(business_object)
        elif layout_type == 'form':
            return cls.generate_form_layout(business_object)
        elif layout_type == 'detail':
            return cls.generate_detail_layout(business_object)

        return {}
