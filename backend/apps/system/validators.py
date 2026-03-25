"""
Layout validators for validating page layout configurations.

This module provides validation functions for layout JSON structures,
ensuring they conform to the expected schema before saving to database.

Unified Layout System:
- All layouts (edit/readonly/search) use sections-based structure
- List layouts are auto-generated from FieldDefinition.show_in_list
- Legacy layout_type is supported for backward compatibility
"""
from rest_framework.exceptions import ValidationError
from typing import Dict, Any, List
from uuid import uuid4


def _is_dict(v: Any) -> bool:
    return isinstance(v, dict)


def _is_list(v: Any) -> bool:
    return isinstance(v, list)


def _normalize_candidate(value: str) -> str:
    raw = (value or '').strip()
    if not raw:
        return ''
    raw = raw.replace('-', '_')
    raw = '_'.join(raw.split())
    out = []
    for ch in raw:
        if ch.isalnum() or ch == '_':
            out.append(ch)
        else:
            out.append('_')
    s = ''.join(out)
    while '__' in s:
        s = s.replace('__', '_')
    return s.strip('_').lower()


def _camel_to_snake(value: str) -> str:
    s = (value or '').strip()
    if not s:
        return ''
    out = []
    for ch in s:
        if ch.isupper():
            if out:
                out.append('_')
            out.append(ch.lower())
        else:
            out.append(ch)
    return _normalize_candidate(''.join(out))


def sanitize_layout_config_field_codes(
    config: Dict[str, Any],
    allowed_codes: set,
    *,
    strict_on_whitespace: bool = True,
) -> Dict[str, Any]:
    """
    Best-effort sanitize `fieldCode` values in sections-based layout configs.

    This prevents a high-impact data-quality issue where `fieldCode` is persisted
    as a human label (e.g. "asset code") instead of the canonical code (e.g. "asset_code"),
    which causes readonly/detail pages to render empty values.

    Scope:
    - Only touches configs that contain `sections` (edit/readonly/search forms).
    - Leaves list/table configs (`columns`) to their own rules (actions columns etc.).
    """
    if not _is_dict(config) or not allowed_codes:
        return config
    if not _is_list(config.get('sections')):
        return config

    def resolve_code(raw: str) -> str:
        if not raw:
            return raw
        if raw in allowed_codes:
            return raw
        if any(ch.isupper() for ch in raw):
            snake = _camel_to_snake(raw)
            if snake in allowed_codes:
                return snake
        normalized = _normalize_candidate(raw)
        if normalized in allowed_codes:
            return normalized
        return raw

    def sanitize_field(field: Any, path: str) -> Any:
        if not _is_dict(field):
            return field
        raw = str(field.get('fieldCode') or field.get('field_code') or field.get('field') or field.get('code') or '').strip()
        if not raw:
            return field

        resolved = resolve_code(raw)
        if resolved == raw and resolved not in allowed_codes:
            if strict_on_whitespace and (' ' in raw or '\t' in raw or '\n' in raw):
                raise LayoutValidationError(
                    "Invalid fieldCode: looks like a label (contains whitespace). Use canonical field code instead.",
                    field_path=f"{path}.fieldCode"
                )
            return field

        if resolved != raw:
            next_field = dict(field)
            next_field['fieldCode'] = resolved
            if 'field_code' in next_field:
                next_field['field_code'] = resolved
            if 'field' in next_field:
                next_field['field'] = resolved
            if 'code' in next_field:
                next_field['code'] = resolved
            return next_field

        return field

    def sanitize_section(section: Any, path: str) -> Any:
        if not _is_dict(section):
            return section
        stype = section.get('type') or 'section'
        next_section = dict(section)

        if stype == 'tab':
            tabs = next_section.get('tabs') or []
            if _is_list(tabs):
                next_tabs = []
                for i, tab in enumerate(tabs):
                    if _is_dict(tab):
                        nt = dict(tab)
                        fields = nt.get('fields') or []
                        if _is_list(fields):
                            nt['fields'] = [sanitize_field(f, f"{path}.tabs[{i}].fields[{j}]") for j, f in enumerate(fields)]
                        next_tabs.append(nt)
                    else:
                        next_tabs.append(tab)
                next_section['tabs'] = next_tabs
            return next_section

        if stype == 'collapse':
            items = next_section.get('items') or []
            if _is_list(items):
                next_items = []
                for i, item in enumerate(items):
                    if _is_dict(item):
                        ni = dict(item)
                        fields = ni.get('fields') or []
                        if _is_list(fields):
                            ni['fields'] = [sanitize_field(f, f"{path}.items[{i}].fields[{j}]") for j, f in enumerate(fields)]
                        next_items.append(ni)
                    else:
                        next_items.append(item)
                next_section['items'] = next_items
            return next_section

        if stype == 'detail-region':
            raw = str(
                next_section.get('fieldCode')
                or next_section.get('field_code')
                or ''
            ).strip()
            if not raw:
                return next_section

            resolved = resolve_code(raw)
            if resolved == raw and resolved not in allowed_codes:
                if strict_on_whitespace and (' ' in raw or '\t' in raw or '\n' in raw):
                    raise LayoutValidationError(
                        "Invalid fieldCode: looks like a label (contains whitespace). Use canonical field code instead.",
                        field_path=f"{path}.fieldCode"
                    )
                return next_section

            if resolved != raw:
                next_section['fieldCode'] = resolved
                if 'field_code' in next_section:
                    next_section["field_code"] = resolved
            return next_section

        if stype == 'workflow-progress':
            raw = str(
                next_section.get('statusFieldCode')
                or next_section.get('status_field_code')
                or ''
            ).strip()
            if not raw:
                return next_section

            resolved = resolve_code(raw)
            if resolved == raw and resolved not in allowed_codes:
                if strict_on_whitespace and (' ' in raw or '\t' in raw or '\n' in raw):
                    raise LayoutValidationError(
                        "Invalid statusFieldCode: looks like a label (contains whitespace). Use canonical field code instead.",
                        field_path=f"{path}.statusFieldCode"
                    )
                return next_section

            if resolved != raw:
                next_section['statusFieldCode'] = resolved
                if 'status_field_code' in next_section:
                    next_section['status_field_code'] = resolved
            return next_section

        fields = next_section.get('fields') or []
        if _is_list(fields):
            next_section['fields'] = [sanitize_field(f, f"{path}.fields[{i}]") for i, f in enumerate(fields)]
        return next_section

    next_config = dict(config)
    next_config['sections'] = [sanitize_section(s, f"sections[{i}]") for i, s in enumerate(config.get('sections') or [])]
    return next_config


def _generate_layout_node_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


def _normalize_field_node(field: Any) -> Any:
    if not _is_dict(field):
        return field

    next_field = dict(field)
    next_field.setdefault('id', _generate_layout_node_id('field'))

    raw_code = (
        next_field.get('fieldCode')
        or next_field.get('field_code')
        or next_field.get('field')
        or next_field.get('code')
        or next_field.get('prop')
        or next_field.get('name')
        or ''
    )
    field_code = str(raw_code).strip()
    if field_code:
        next_field['fieldCode'] = field_code
        if not next_field.get('label'):
            next_field['label'] = field_code

    if 'span' not in next_field:
        next_field['span'] = 1

    return next_field


def _normalize_detail_region_section(section: Dict[str, Any]) -> Dict[str, Any]:
    next_section = dict(section)
    next_section.setdefault('columns', 1)
    next_section.setdefault('collapsible', True)
    next_section.setdefault('collapsed', False)

    relation_code = str(
        next_section.get('relationCode')
        or next_section.get('relation_code')
        or ''
    ).strip()
    if relation_code:
        next_section['relationCode'] = relation_code
        next_section['relation_code'] = relation_code

    field_code = str(
        next_section.get('fieldCode')
        or next_section.get('field_code')
        or ''
    ).strip()
    if field_code:
        next_section['fieldCode'] = field_code
        next_section['field_code'] = field_code

    target_object_code = str(
        next_section.get('targetObjectCode')
        or next_section.get('target_object_code')
        or ''
    ).strip()
    if target_object_code:
        next_section['targetObjectCode'] = target_object_code
        next_section['target_object_code'] = target_object_code

    detail_edit_mode = str(
        next_section.get('detailEditMode')
        or next_section.get('detail_edit_mode')
        or ''
    ).strip()
    if detail_edit_mode:
        next_section['detailEditMode'] = detail_edit_mode
        next_section['detail_edit_mode'] = detail_edit_mode

    toolbar_config = next_section.get('toolbarConfig', next_section.get('toolbar_config'))
    if _is_dict(toolbar_config):
        next_section['toolbarConfig'] = dict(toolbar_config)
        next_section['toolbar_config'] = dict(toolbar_config)

    summary_rules = next_section.get('summaryRules', next_section.get('summary_rules'))
    if _is_list(summary_rules):
        next_section['summaryRules'] = list(summary_rules)
        next_section['summary_rules'] = list(summary_rules)

    validation_rules = next_section.get('validationRules', next_section.get('validation_rules'))
    if _is_list(validation_rules):
        next_section['validationRules'] = list(validation_rules)
        next_section['validation_rules'] = list(validation_rules)

    return next_section


def _normalize_workflow_progress_section(section: Dict[str, Any]) -> Dict[str, Any]:
    next_section = dict(section)
    next_section.setdefault('columns', 1)
    next_section.setdefault('position', 'main')
    next_section.setdefault('collapsible', False)
    next_section.setdefault('collapsed', False)
    next_section.setdefault('showTitle', False)
    next_section.setdefault('show_title', False)

    status_field_code = str(
        next_section.get('statusFieldCode')
        or next_section.get('status_field_code')
        or 'status'
    ).strip()
    if status_field_code:
        next_section['statusFieldCode'] = status_field_code
        next_section['status_field_code'] = status_field_code

    translation_key = str(
        next_section.get('translationKey')
        or next_section.get('translation_key')
        or ''
    ).strip()
    if translation_key:
        next_section['translationKey'] = translation_key
        next_section['translation_key'] = translation_key

    return next_section


def _normalize_section_node(section: Any) -> Any:
    if not _is_dict(section):
        return section

    next_section = dict(section)
    next_section.setdefault('id', _generate_layout_node_id('section'))

    section_type = str(next_section.get('type') or 'section').strip() or 'section'
    next_section['type'] = section_type

    if section_type == 'detail-region':
        return _normalize_detail_region_section(next_section)

    if section_type == 'workflow-progress':
        return _normalize_workflow_progress_section(next_section)

    if section_type == 'tab':
        tabs = next_section.get('tabs')
        if not _is_list(tabs):
            tabs = []
        next_tabs = []
        for tab in tabs:
            if not _is_dict(tab):
                continue
            next_tab = dict(tab)
            next_tab.setdefault('id', _generate_layout_node_id('tab'))
            fields = next_tab.get('fields')
            if not _is_list(fields):
                fields = []
            next_tab['fields'] = [_normalize_field_node(field) for field in fields]
            next_tabs.append(next_tab)
        next_section['tabs'] = next_tabs
        return next_section

    if section_type == 'collapse':
        items = next_section.get('items')
        if not _is_list(items):
            items = []
        next_items = []
        for item in items:
            if not _is_dict(item):
                continue
            next_item = dict(item)
            next_item.setdefault('id', _generate_layout_node_id('collapse'))
            fields = next_item.get('fields')
            if not _is_list(fields):
                fields = []
            next_item['fields'] = [_normalize_field_node(field) for field in fields]
            next_items.append(next_item)
        next_section['items'] = next_items
        return next_section

    fields = next_section.get('fields')
    if not _is_list(fields):
        fields = []
    next_section['fields'] = [_normalize_field_node(field) for field in fields]
    return next_section


def normalize_layout_config_structure(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Best-effort normalization for sections-based layouts.

    Adds missing ids/default keys for sections and fields so legacy payloads
    can still pass strict validation.
    """
    if not _is_dict(config):
        return config

    next_config = dict(config)
    sections = next_config.get('sections')
    if not _is_list(sections):
        return next_config

    next_config['sections'] = [_normalize_section_node(section) for section in sections]
    return next_config


# Supported section types
VALID_SECTION_TYPES = ['section', 'tab', 'divider', 'collapse', 'column', 'card', 'default', 'fieldset', 'detail-region', 'workflow-progress']

VALID_DETAIL_EDIT_MODES = ['inline_table', 'nested_form', 'readonly_table']

# Valid column span values (1-24, must be divisible by common grid systems)
VALID_SPANS = [1, 2, 3, 4, 6, 8, 12, 24]

# Layout modes (new unified system)
LAYOUT_MODES = ['edit', 'readonly', 'search']

# Legacy layout types (for backward compatibility)
LEGACY_LAYOUT_TYPES = ['form', 'list', 'detail', 'search']

# Legacy type to mode mapping
LEGACY_TYPE_TO_MODE = {
    'form': 'edit',
    'detail': 'readonly',
    'list': 'edit',  # List layouts are auto-generated
    'search': 'search',
}


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
        layout_type: Type of layout (form, list, detail, search) - legacy, use mode instead

    Raises:
        LayoutValidationError: If configuration is invalid

    Note:
        This function supports legacy layout_type for backward compatibility.
        Internally converts to mode and validates accordingly.
    """
    if not isinstance(config, dict):
        raise LayoutValidationError("Configuration must be a JSON object")

    # Convert legacy layout_type to mode
    mode = LEGACY_TYPE_TO_MODE.get(layout_type, layout_type)

    # All modes now use sections-based configuration
    if mode in ['edit', 'readonly']:
        _validate_sections_layout(config)
    elif mode == 'search':
        _validate_search_layout(config)


def validate_layout_config_by_mode(config: Dict[str, Any], mode: str = 'edit') -> None:
    """
    Validate layout configuration structure using the new mode-based system.

    Args:
        config: Layout configuration dictionary
        mode: Layout mode (edit, readonly, search)

    Raises:
        LayoutValidationError: If configuration is invalid
    """
    if not isinstance(config, dict):
        raise LayoutValidationError("Configuration must be a JSON object")

    if mode not in LAYOUT_MODES:
        raise LayoutValidationError(
            f"Invalid mode: {mode}. Valid modes: {', '.join(LAYOUT_MODES)}"
        )

    # All modes use sections-based configuration
    if mode in ['edit', 'readonly']:
        _validate_sections_layout(config)
    elif mode == 'search':
        _validate_search_layout(config)


def _validate_sections_layout(config: Dict[str, Any]) -> None:
    """
    Validate sections-based layout structure.

    This is used for both edit and readonly modes since they share
    the same sections-based structure.
    """
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
        'detail-region': _validate_detail_region_section,
        'workflow-progress': _validate_workflow_progress_section,
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


def _validate_detail_region_section(section: Dict[str, Any], path: str) -> None:
    """Validate master-detail region sections embedded in aggregate layouts."""
    relation_code = str(
        section.get('relationCode')
        or section.get('relation_code')
        or ''
    ).strip()
    if not relation_code:
        raise LayoutValidationError(f"{path} missing required field: relationCode")

    field_code = str(
        section.get('fieldCode')
        or section.get('field_code')
        or ''
    ).strip()
    if not field_code:
        raise LayoutValidationError(f"{path} missing required field: fieldCode")

    detail_edit_mode = str(
        section.get('detailEditMode')
        or section.get('detail_edit_mode')
        or ''
    ).strip()
    if detail_edit_mode and detail_edit_mode not in VALID_DETAIL_EDIT_MODES:
        raise LayoutValidationError(
            f"{path}.detailEditMode must be one of {', '.join(VALID_DETAIL_EDIT_MODES)}"
        )

    toolbar_config = section.get('toolbarConfig', section.get('toolbar_config'))
    if toolbar_config is not None and not isinstance(toolbar_config, dict):
        raise LayoutValidationError(f"{path}.toolbarConfig must be an object")

    summary_rules = section.get('summaryRules', section.get('summary_rules'))
    if summary_rules is not None and not isinstance(summary_rules, list):
        raise LayoutValidationError(f"{path}.summaryRules must be an array")

    validation_rules = section.get('validationRules', section.get('validation_rules'))
    if validation_rules is not None and not isinstance(validation_rules, list):
        raise LayoutValidationError(f"{path}.validationRules must be an array")


def _validate_workflow_progress_section(section: Dict[str, Any], path: str) -> None:
    status_field_code = str(
        section.get('statusFieldCode')
        or section.get('status_field_code')
        or ''
    ).strip()
    if not status_field_code:
        raise LayoutValidationError(f"{path}.statusFieldCode must be a non-empty string")


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
    
    Note:
        Supports both camelCase (fieldCode) and snake_case (field_code) 
        for frontend compatibility.
    """
    if not isinstance(field, dict):
        raise LayoutValidationError(f"{path} must be an object")

    # Support both camelCase and snake_case for field names (frontend compatibility)
    # Check for id (required)
    if 'id' not in field:
        raise LayoutValidationError(f"{path} missing required field: id")
    
    # Check for field_code or fieldCode (required)
    if 'field_code' not in field and 'fieldCode' not in field:
        raise LayoutValidationError(f"{path} missing required field: field_code (or fieldCode)")
    
    # Check for label (required)
    if 'label' not in field:
        raise LayoutValidationError(f"{path} missing required field: label")
    
    # Check for span (required)
    if 'span' not in field:
        raise LayoutValidationError(f"{path} missing required field: span")

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
