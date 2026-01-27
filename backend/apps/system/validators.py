"""
Layout validators for validating page layout configurations.

This module provides validation functions for layout JSON structures,
ensuring they conform to the expected schema before saving to database.
"""
from rest_framework.exceptions import ValidationError
from typing import Dict, Any, List


# Supported section types
VALID_SECTION_TYPES = ['section', 'tab', 'divider', 'collapse', 'column']

# Valid column span values (1-24, must be divisible by common grid systems)
VALID_SPANS = [1, 2, 3, 4, 6, 8, 12, 24]


class LayoutValidationError(ValidationError):
    """Custom exception for layout validation errors."""
    def __init__(self, message: str, field_path: str = ''):
        self.message = message
        self.field_path = field_path
        detail_message = f"{field_path}: {message}" if field_path else message
        super().__init__(detail_message)


def validate_layout_config(config: Dict[str, Any], layout_type: str = 'form') -> None:
    """
    Validate layout configuration structure.

    Args:
        config: Layout configuration dictionary
        layout_type: Type of layout (form, list, detail, search)

    Raises:
        LayoutValidationError: If configuration is invalid
    """
    if not isinstance(config, dict):
        raise LayoutValidationError("Configuration must be a JSON object")

    if layout_type in ['form', 'detail']:
        _validate_form_layout(config)
    elif layout_type == 'list':
        _validate_list_layout(config)
    elif layout_type == 'search':
        _validate_search_layout(config)


def _validate_form_layout(config: Dict[str, Any]) -> None:
    """Validate form/detail layout structure."""
    if 'sections' not in config:
        raise LayoutValidationError("Missing required field: sections")

    sections = config['sections']
    if not isinstance(sections, list):
        raise LayoutValidationError("sections must be an array")

    if not sections:
        raise LayoutValidationError("sections cannot be empty")

    for index, section in enumerate(sections):
        _validate_section(section, f"sections[{index}]")


def _validate_list_layout(config: Dict[str, Any]) -> None:
    """Validate list layout structure."""
    if 'columns' not in config:
        raise LayoutValidationError("Missing required field: columns")

    columns = config['columns']
    if not isinstance(columns, list):
        raise LayoutValidationError("columns must be an array")

    if not columns:
        raise LayoutValidationError("columns cannot be empty")

    for index, column in enumerate(columns):
        _validate_list_column(column, f"columns[{index}]")


def _validate_search_layout(config: Dict[str, Any]) -> None:
    """Validate search layout structure."""
    # Search layout is similar to form but with less strict validation
    if 'fields' in config:
        fields = config['fields']
        if not isinstance(fields, list):
            raise LayoutValidationError("fields must be an array")


def _validate_section(section: Dict[str, Any], path: str) -> None:
    """
    Validate a single section configuration.

    Args:
        section: Section configuration
        path: Field path for error messages
    """
    if not isinstance(section, dict):
        raise LayoutValidationError(f"{path} must be an object")

    if 'id' not in section:
        raise LayoutValidationError(f"{path} missing required field: id")

    if 'type' not in section:
        raise LayoutValidationError(f"{path} missing required field: type")

    section_type = section['type']

    if section_type not in VALID_SECTION_TYPES:
        raise LayoutValidationError(
            f"{path} has invalid type: {section_type}. "
            f"Valid types: {', '.join(VALID_SECTION_TYPES)}"
        )

    # Type-specific validation
    validators = {
        'section': _validate_basic_section,
        'tab': _validate_tab_section,
        'divider': _validate_divider_section,
        'collapse': _validate_collapse_section,
        'column': _validate_column_section,
    }

    validator = validators.get(section_type)
    if validator:
        validator(section, path)


def _validate_basic_section(section: Dict[str, Any], path: str) -> None:
    """Validate basic section type."""
    if 'fields' in section:
        fields = section['fields']
        if not isinstance(fields, list):
            raise LayoutValidationError(f"{path}.fields must be an array")

        for index, field in enumerate(fields):
            _validate_field(field, f"{path}.fields[{index}]")


def _validate_tab_section(section: Dict[str, Any], path: str) -> None:
    """Validate tab section type."""
    if 'tabs' not in section:
        raise LayoutValidationError(f"{path} missing required field: tabs")

    tabs = section['tabs']
    if not isinstance(tabs, list):
        raise LayoutValidationError(f"{path}.tabs must be an array")

    if not tabs:
        raise LayoutValidationError(f"{path}.tabs cannot be empty")

    for index, tab in enumerate(tabs):
        _validate_tab(tab, f"{path}.tabs[{index}]")


def _validate_tab(tab: Dict[str, Any], path: str) -> None:
    """Validate a single tab configuration."""
    if not isinstance(tab, dict):
        raise LayoutValidationError(f"{path} must be an object")

    if 'id' not in tab:
        raise LayoutValidationError(f"{path} missing required field: id")

    if 'title' not in tab:
        raise LayoutValidationError(f"{path} missing required field: title")

    if 'fields' in tab:
        fields = tab['fields']
        if not isinstance(fields, list):
            raise LayoutValidationError(f"{path}.fields must be an array")

        for index, field in enumerate(fields):
            _validate_field(field, f"{path}.fields[{index}]")


def _validate_divider_section(section: Dict[str, Any], path: str) -> None:
    """Validate divider section type (minimal validation)."""
    # Divider only needs id and type, which are already validated
    pass


def _validate_collapse_section(section: Dict[str, Any], path: str) -> None:
    """Validate collapse section type."""
    if 'items' not in section:
        raise LayoutValidationError(f"{path} missing required field: items")

    items = section['items']
    if not isinstance(items, list):
        raise LayoutValidationError(f"{path}.items must be an array")

    if not items:
        raise LayoutValidationError(f"{path}.items cannot be empty")

    for index, item in enumerate(items):
        _validate_collapse_item(item, f"{path}.items[{index}]")


def _validate_collapse_item(item: Dict[str, Any], path: str) -> None:
    """Validate a single collapse item configuration."""
    if not isinstance(item, dict):
        raise LayoutValidationError(f"{path} must be an object")

    if 'id' not in item:
        raise LayoutValidationError(f"{path} missing required field: id")

    if 'title' not in item:
        raise LayoutValidationError(f"{path} missing required field: title")

    if 'fields' in item:
        fields = item['fields']
        if not isinstance(fields, list):
            raise LayoutValidationError(f"{path}.fields must be an array")

        for index, field in enumerate(fields):
            _validate_field(field, f"{path}.fields[{index}]")


def _validate_column_section(section: Dict[str, Any], path: str) -> None:
    """Validate column section type."""
    if 'columns' not in section:
        raise LayoutValidationError(f"{path} missing required field: columns")

    columns = section['columns']
    if not isinstance(columns, list):
        raise LayoutValidationError(f"{path}.columns must be an array")

    if not columns:
        raise LayoutValidationError(f"{path}.columns cannot be empty")

    for index, column in enumerate(columns):
        _validate_column_item(column, f"{path}.columns[{index}]")


def _validate_column_item(column: Dict[str, Any], path: str) -> None:
    """Validate a single column item configuration."""
    if not isinstance(column, dict):
        raise LayoutValidationError(f"{path} must be an object")

    if 'span' in column:
        span = column['span']
        if not isinstance(span, int) or span not in VALID_SPANS:
            raise LayoutValidationError(
                f"{path}.span must be one of {VALID_SPANS}"
            )

    if 'fields' in column:
        fields = column['fields']
        if not isinstance(fields, list):
            raise LayoutValidationError(f"{path}.fields must be an array")

        for index, field in enumerate(fields):
            _validate_field(field, f"{path}.fields[{index}]")


def _validate_list_column(column: Dict[str, Any], path: str) -> None:
    """Validate a list column configuration."""
    if not isinstance(column, dict):
        raise LayoutValidationError(f"{path} must be an object")

    required_fields = ['field_code', 'label']
    for field in required_fields:
        if field not in column:
            raise LayoutValidationError(f"{path} missing required field: {field}")

    if 'width' in column:
        width = column['width']
        if not isinstance(width, int) or width <= 0:
            raise LayoutValidationError(f"{path}.width must be a positive integer")


def _validate_field(field: Dict[str, Any], path: str) -> None:
    """
    Validate a field configuration.

    Args:
        field: Field configuration dictionary
        path: Field path for error messages
    """
    if not isinstance(field, dict):
        raise LayoutValidationError(f"{path} must be an object")

    required_fields = ['id', 'field_code', 'label', 'span']
    for required_field in required_fields:
        if required_field not in field:
            raise LayoutValidationError(f"{path} missing required field: {required_field}")

    # Validate span
    span = field['span']
    if not isinstance(span, int) or span not in VALID_SPANS:
        raise LayoutValidationError(
            f"{path}.span must be an integer between 1-24, "
            f"preferably one of {VALID_SPANS}"
        )


def get_default_layout_config(layout_type: str = 'form') -> Dict[str, Any]:
    """
    Get default layout configuration for a given layout type.

    Args:
        layout_type: Type of layout (form, list, detail, search)

    Returns:
        Default configuration dictionary
    """
    if layout_type == 'form':
        return {
            'sections': [
                {
                    'id': 'section-default',
                    'type': 'section',
                    'title': '基本信息',
                    'collapsible': True,
                    'collapsed': False,
                    'columns': 2,
                    'border': True,
                    'fields': []
                }
            ],
            'actions': [
                {'code': 'submit', 'label': '提交', 'type': 'primary', 'position': 'bottom-right'},
                {'code': 'cancel', 'label': '取消', 'type': 'default', 'position': 'bottom-right'}
            ]
        }
    elif layout_type == 'list':
        return {
            'columns': [],
            'actions': [
                {'code': 'create', 'label': '新建', 'type': 'primary', 'position': 'top-right'},
                {'code': 'delete', 'label': '删除', 'type': 'danger', 'position': 'toolbar'}
            ],
            'page_size': 20,
            'show_pagination': True
        }
    elif layout_type == 'detail':
        return {
            'sections': [
                {
                    'id': 'section-detail',
                    'type': 'section',
                    'title': '详细信息',
                    'collapsible': True,
                    'collapsed': False,
                    'columns': 2,
                    'border': True,
                    'fields': []
                }
            ]
        }
    elif layout_type == 'search':
        return {
            'fields': [],
            'layout': 'horizontal',  # horizontal | vertical
            'label_width': '100px'
        }

    return {}
def validate_and_sanitize_layout_config(config: Dict[str, Any], layout_type: str = 'form') -> Dict[str, Any]:
    """
    Validate and sanitize layout configuration.

    This function validates the configuration and adds any missing
    optional fields with default values.

    Args:
        config: Layout configuration dictionary
        layout_type: Type of layout

    Returns:
        Sanitized configuration dictionary

    Raises:
        LayoutValidationError: If configuration is invalid
    """
    # First validate
    validate_layout_config(config, layout_type)

    # Add defaults for optional fields
    sanitized = config.copy()

    if layout_type == 'form':
        # Ensure actions exist
        if 'actions' not in sanitized:
            sanitized['actions'] = []

    return sanitized
