"""
Runtime layout normalization helpers.

These helpers are intentionally fault-tolerant so legacy layout payloads can
still be rendered at runtime even when missing strict schema fields.
"""
from typing import Any, Dict, Set

from apps.system.models import ModelFieldDefinition, FieldDefinition
from apps.system.validators import (
    normalize_layout_config_structure,
    sanitize_layout_config_field_codes,
)


DEFAULT_WORKFLOW_PROGRESS_SECTION = {
    'id': 'workflow_progress',
    'name': 'workflow_progress',
    'type': 'workflow-progress',
    'title': {
        'translationKey': 'common.documentWorkbench.sections.workflowProgress',
    },
    'translationKey': 'common.documentWorkbench.sections.workflowProgress',
    'columns': 1,
    'column': 1,
    'position': 'main',
    'collapsible': False,
    'collapsed': False,
    'showTitle': False,
    'renderAsCard': False,
    'statusFieldCode': 'status',
    'status_field_code': 'status',
}


def supports_default_workflow_progress(business_object) -> bool:
    return bool(
        getattr(business_object, 'enable_workflow', False)
        and getattr(business_object, 'object_role', 'root') == 'root'
        and getattr(business_object, 'allow_standalone_route', True)
        and not getattr(business_object, 'inherit_workflow', False)
    )


def inject_default_workflow_progress_section(business_object, layout_config: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(layout_config, dict):
        return layout_config
    if not supports_default_workflow_progress(business_object):
        return layout_config
    if bool(layout_config.get('disableDefaultWorkflowProgress') or layout_config.get('disable_default_workflow_progress')):
        return layout_config

    sections = layout_config.get('sections')
    if not isinstance(sections, list):
        return layout_config
    if any(str(section.get('type') or '').strip() == 'workflow-progress' for section in sections):
        return layout_config

    next_config = dict(layout_config)
    next_config['sections'] = [dict(DEFAULT_WORKFLOW_PROGRESS_SECTION), *sections]
    return normalize_layout_config_structure(next_config)


def resolve_allowed_layout_field_codes(business_object) -> Set[str]:
    allowed_codes: Set[str] = set()
    try:
        allowed_codes.update(
            ModelFieldDefinition.objects.filter(
                business_object=business_object
            ).values_list('field_name', flat=True)
        )
    except Exception:
        pass
    try:
        allowed_codes.update(
            FieldDefinition.objects.filter(
                business_object=business_object
            ).values_list('code', flat=True)
        )
    except Exception:
        pass
    return {str(code).strip() for code in allowed_codes if str(code).strip()}


def normalize_layout_config_for_runtime(business_object, layout_config: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(layout_config, dict):
        return layout_config

    normalized = inject_default_workflow_progress_section(
        business_object,
        normalize_layout_config_structure(layout_config)
    )
    allowed_codes = resolve_allowed_layout_field_codes(business_object)
    if not allowed_codes:
        return normalized
    try:
        # Runtime path should not throw for legacy bad labels in fieldCode.
        return sanitize_layout_config_field_codes(
            normalized,
            allowed_codes,
            strict_on_whitespace=False
        )
    except Exception:
        return normalized
