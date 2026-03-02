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

    normalized = normalize_layout_config_structure(layout_config)
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
