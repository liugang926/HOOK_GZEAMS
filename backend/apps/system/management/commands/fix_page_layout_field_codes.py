"""
Fix legacy/invalid field codes stored inside PageLayout.layout_config.

Why:
- Some historical layout configs were saved with `fieldCode` mistakenly set to a label
  (e.g. "asset code") instead of the canonical backend field code (e.g. "asset_code").
- This breaks the low-code runtime in readonly/detail pages: the field renders but has no value.

Strategy:
- Build a canonical field registry per business object from:
  - ModelFieldDefinition.field_name + display_name (hardcoded models)
  - FieldDefinition.code + name (custom low-code fields)
- Walk the layout_config tree and normalize field entries:
  - Ensure `fieldCode` exists (from `field`/`code`/`prop`)
  - If fieldCode does not match a known code, try:
    - normalize("asset code") -> "asset_code"
    - match by label/name against known field display names
    - camelCase prop -> snake_case (best-effort)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.system.models import (
    BusinessObject,
    FieldDefinition,
    ModelFieldDefinition,
    PageLayout,
)


def _is_dict(v: Any) -> bool:
    return isinstance(v, dict)


def _is_list(v: Any) -> bool:
    return isinstance(v, list)


def _normalize_candidate(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    raw = raw.replace("-", "_")
    raw = "_".join(raw.split())
    out = []
    for ch in raw:
        if ch.isalnum() or ch == "_":
            out.append(ch)
        else:
            out.append("_")
    s = "".join(out)
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_").lower()


def _camel_to_snake(value: str) -> str:
    s = (value or "").strip()
    if not s:
        return ""
    out = []
    for ch in s:
        if ch.isupper():
            if out:
                out.append("_")
            out.append(ch.lower())
        else:
            out.append(ch)
    return _normalize_candidate("".join(out))


@dataclass
class FieldRegistry:
    codes: set
    normalized_to_code: Dict[str, str]
    label_to_code: Dict[str, str]


def _build_field_registry(object_code: str) -> FieldRegistry:
    bo = BusinessObject.objects.filter(code=object_code).first()
    if not bo:
        return FieldRegistry(codes=set(), normalized_to_code={}, label_to_code={})

    codes: set = set()
    normalized_to_code: Dict[str, str] = {}
    label_to_code: Dict[str, str] = {}

    # Hardcoded model fields
    for fd in ModelFieldDefinition.objects.filter(business_object=bo).only("field_name", "display_name"):
        code = (fd.field_name or "").strip()
        if not code:
            continue
        codes.add(code)
        normalized_to_code[_normalize_candidate(code)] = code
        if fd.display_name:
            label_to_code[(fd.display_name or "").strip().lower()] = code

    # Custom low-code fields
    for fd in FieldDefinition.objects.filter(business_object=bo).only("code", "name"):
        code = (fd.code or "").strip()
        if not code:
            continue
        codes.add(code)
        normalized_to_code[_normalize_candidate(code)] = code
        if fd.name:
            label_to_code[(fd.name or "").strip().lower()] = code

    return FieldRegistry(codes=codes, normalized_to_code=normalized_to_code, label_to_code=label_to_code)


def _extract_field_entry_code(entry: Any) -> str:
    if isinstance(entry, str):
        return entry.strip()
    if not _is_dict(entry):
        return ""
    return str(
        entry.get("fieldCode")
        or entry.get("field_code")
        or entry.get("field")
        or entry.get("code")
        or entry.get("prop")
        or entry.get("name")
        or ""
    ).strip()


def _resolve_code(entry: Any, registry: FieldRegistry) -> Tuple[str, Optional[str]]:
    """
    Returns (resolved_code, reason) where reason is None when no change is applied.
    """
    raw = _extract_field_entry_code(entry)
    if not raw:
        return "", None

    if raw in registry.codes:
        return raw, None

    # 1) normalize spaces/punctuation
    normalized = _normalize_candidate(raw)
    if normalized in registry.codes:
        return normalized, f'normalize("{raw}") -> "{normalized}"'
    if normalized in registry.normalized_to_code:
        resolved = registry.normalized_to_code[normalized]
        return resolved, f'normalizeMap("{raw}") -> "{resolved}"'

    # 2) camelCase -> snake_case
    if any(ch.isupper() for ch in raw):
        snake = _camel_to_snake(raw)
        if snake in registry.codes:
            return snake, f'camelToSnake("{raw}") -> "{snake}"'
        if snake in registry.normalized_to_code:
            resolved = registry.normalized_to_code[snake]
            return resolved, f'camelToSnakeMap("{raw}") -> "{resolved}"'

    # 3) label/name match
    if _is_dict(entry):
        label = (entry.get("label") or entry.get("name") or "").strip()
        if label:
            key = label.lower()
            if key in registry.label_to_code:
                resolved = registry.label_to_code[key]
                return resolved, f'label("{label}") -> "{resolved}"'

    return raw, None


def _walk_and_fix_layout_config(config: Any, registry: FieldRegistry) -> Tuple[Any, List[str], int]:
    """
    Returns (new_config, messages, changes_count)
    """
    messages: List[str] = []
    changes = 0

    def fix_field_entry(entry: Any) -> Any:
        nonlocal changes
        if isinstance(entry, str):
            resolved, reason = _resolve_code(entry, registry)
            if reason:
                changes += 1
                messages.append(f"field: {entry} -> {resolved} ({reason})")
            return resolved

        if not _is_dict(entry):
            return entry

        resolved, reason = _resolve_code(entry, registry)
        next_entry = dict(entry)
        # Canonicalize key name used by frontend designer/runtime.
        next_entry["fieldCode"] = resolved
        # Preserve legacy keys, but keep them consistent if present.
        if "field" in next_entry:
            next_entry["field"] = resolved
        if "code" in next_entry:
            next_entry["code"] = resolved
        if "prop" in next_entry and next_entry.get("prop") == entry.get("prop"):
            # Only overwrite prop if it was being used as the identifier.
            raw = str(entry.get("prop") or "").strip()
            if raw and raw == _extract_field_entry_code(entry):
                next_entry["prop"] = resolved

        if reason:
            changes += 1
            messages.append(f"field: {entry.get('fieldCode') or entry.get('field') or entry.get('prop')} -> {resolved} ({reason})")

        return next_entry

    def fix_section(section: Any) -> Any:
        if not _is_dict(section):
            return section
        next_section = dict(section)
        stype = next_section.get("type") or "section"

        if stype == "tab":
            tabs = next_section.get("tabs") or []
            if _is_list(tabs):
                next_tabs = []
                for tab in tabs:
                    if _is_dict(tab):
                        nt = dict(tab)
                        fields = nt.get("fields") or []
                        if _is_list(fields):
                            nt["fields"] = [fix_field_entry(f) for f in fields]
                        next_tabs.append(nt)
                    else:
                        next_tabs.append(tab)
                next_section["tabs"] = next_tabs
            return next_section

        if stype == "collapse":
            items = next_section.get("items") or []
            if _is_list(items):
                next_items = []
                for item in items:
                    if _is_dict(item):
                        ni = dict(item)
                        fields = ni.get("fields") or []
                        if _is_list(fields):
                            ni["fields"] = [fix_field_entry(f) for f in fields]
                        next_items.append(ni)
                    else:
                        next_items.append(item)
                next_section["items"] = next_items
            return next_section

        fields = next_section.get("fields") or []
        if _is_list(fields):
            next_section["fields"] = [fix_field_entry(f) for f in fields]
        return next_section

    if not _is_dict(config):
        return config, messages, changes

    next_config = dict(config)

    # Sections-based config (form/detail/search)
    if _is_list(next_config.get("sections")):
        next_config["sections"] = [fix_section(s) for s in next_config.get("sections") or []]

    # Columns-based config (list tables)
    if _is_list(next_config.get("columns")):
        next_cols = []
        for col in next_config.get("columns") or []:
            if not _is_dict(col):
                next_cols.append(col)
                continue
            nc = dict(col)
            raw = str(nc.get("fieldCode") or nc.get("prop") or "").strip()
            resolved, reason = _resolve_code({"prop": raw, "label": nc.get("label")}, registry)
            if resolved:
                nc["fieldCode"] = resolved
            if reason:
                changes += 1
                messages.append(f"column: {raw} -> {resolved} ({reason})")
            next_cols.append(nc)
        next_config["columns"] = next_cols

    return next_config, messages, changes


class Command(BaseCommand):
    help = "Scan and fix PageLayout.layout_config field codes for a business object."

    def add_arguments(self, parser):
        parser.add_argument("--object-code", type=str, help="Business object code (e.g. Asset)")
        parser.add_argument("--layout-id", type=str, help="Specific PageLayout id to fix")
        parser.add_argument("--limit", type=int, default=0, help="Limit number of layouts to scan")
        parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")
        parser.add_argument("--only-modes", type=str, default="", help="Comma modes to include (e.g. edit,readonly,search)")

    def handle(self, *args, **options):
        object_code = (options.get("object_code") or "").strip()
        layout_id = (options.get("layout_id") or "").strip()
        limit = int(options.get("limit") or 0)
        apply = bool(options.get("apply"))
        only_modes = [m.strip() for m in (options.get("only_modes") or "").split(",") if m.strip()]

        qs = PageLayout.objects.filter(is_deleted=False)
        if object_code:
            qs = qs.filter(business_object__code=object_code)
        if layout_id:
            qs = qs.filter(id=layout_id)
        if only_modes:
            qs = qs.filter(mode__in=only_modes)
        if limit and limit > 0:
            qs = qs[:limit]

        if object_code:
            registry = _build_field_registry(object_code)
        else:
            registry = FieldRegistry(codes=set(), normalized_to_code={}, label_to_code={})

        total = 0
        changed = 0
        changed_fields = 0

        with transaction.atomic():
            for layout in qs:
                total += 1
                bo_code = layout.business_object.code
                if not object_code:
                    registry = _build_field_registry(bo_code)

                new_config, messages, changes_count = _walk_and_fix_layout_config(layout.layout_config, registry)
                if changes_count > 0 and new_config != layout.layout_config:
                    changed += 1
                    changed_fields += changes_count
                    self.stdout.write(self.style.WARNING(
                        f"[{bo_code}] layout={layout.id} code={layout.layout_code} mode={layout.mode} changes={changes_count}"
                    ))
                    for msg in messages[:30]:
                        self.stdout.write(f"  - {msg}")
                    if len(messages) > 30:
                        self.stdout.write(f"  - ... ({len(messages) - 30} more)")

                    if apply:
                        layout.layout_config = new_config
                        layout.save(update_fields=["layout_config", "updated_at"])

            if not apply:
                # Ensure dry-run never mutates.
                transaction.set_rollback(True)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Scanned={total}, LayoutsChanged={changed}, FieldFixes={changed_fields}, Apply={apply}"
        ))

