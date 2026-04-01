"""Helpers for structured timeline highlights."""
from __future__ import annotations

from typing import Iterable, Optional


TIMELINE_HIGHLIGHT_META = {
    'cancel_reason': {'label': 'Cancellation Reason', 'tone': 'warning'},
    'approval_comment': {'label': 'Approval Comment', 'tone': 'info'},
    'from_approve_comment': {'label': 'Source Approval Comment', 'tone': 'info'},
    'to_approve_comment': {'label': 'Target Approval Comment', 'tone': 'info'},
    'reject_reason': {'label': 'Rejection Reason', 'tone': 'danger'},
    'inspection_result': {'label': 'Inspection Result', 'tone': 'success'},
    'verification_result': {'label': 'Verification Result', 'tone': 'success'},
    'return_comment': {'label': 'Return Comment', 'tone': 'info'},
    'asset_condition': {'label': 'Asset Condition', 'tone': 'warning'},
    'workflow_comment': {'label': 'Workflow Comment', 'tone': 'info'},
    'workflow_result': {'label': 'Workflow Result', 'tone': 'success'},
    'reason': {'label': 'Reason', 'tone': 'info'},
    'comment': {'label': 'Comment', 'tone': 'info'},
    'result': {'label': 'Result', 'tone': 'success'},
}

DESCRIPTION_PATTERNS = (
    ('Cancellation reason:', 'cancel_reason'),
    ('Comment:', 'approval_comment'),
)


def normalize_timeline_text(value) -> str:
    """Normalize free text for timeline payloads."""
    return str(value or '').strip()


def resolve_timeline_highlight_meta(field_code: str, field_label: Optional[str] = None) -> tuple[str, str]:
    """Resolve a human-readable label and tone for a highlight field."""
    normalized_code = normalize_timeline_text(field_code)
    meta = TIMELINE_HIGHLIGHT_META.get(normalized_code)
    if meta:
        return (
            str(field_label or meta.get('label') or normalized_code.replace('_', ' ').title()),
            str(meta.get('tone') or 'info'),
        )

    normalized_label = normalize_timeline_text(field_label) or normalized_code.replace('_', ' ').title() or 'Detail'
    fingerprint = f'{normalized_code} {normalized_label}'.lower()
    if 'cancel' in fingerprint:
        return normalized_label, 'warning'
    if 'reject' in fingerprint:
        return normalized_label, 'danger'
    if any(keyword in fingerprint for keyword in ('result', 'inspection', 'verification')):
        return normalized_label, 'success'
    return normalized_label, 'info'


def build_timeline_highlight(
    *,
    code: str,
    value,
    label: Optional[str] = None,
    tone: Optional[str] = None,
) -> Optional[dict]:
    """Build a structured timeline highlight payload."""
    normalized_code = normalize_timeline_text(code)
    normalized_value = normalize_timeline_text(value)
    if not normalized_code or not normalized_value:
        return None

    resolved_label, resolved_tone = resolve_timeline_highlight_meta(normalized_code, label)
    return {
        'code': normalized_code,
        'label': resolved_label,
        'value': normalized_value,
        'tone': normalize_timeline_text(tone) or resolved_tone,
    }


def build_reason_change(field_code: str, value, *, field_label: Optional[str] = None) -> Optional[dict]:
    """Build a reason-like change record that can be stored on activity logs."""
    highlight = build_timeline_highlight(code=field_code, value=value, label=field_label)
    if highlight is None:
        return None
    return {
        'fieldCode': highlight['code'],
        'fieldLabel': highlight['label'],
        'oldValue': '',
        'newValue': highlight['value'],
    }


def build_timeline_highlights_from_changes(changes: Optional[Iterable[dict]]) -> list[dict]:
    """Extract highlight payloads from activity-log change rows."""
    highlights = []
    for change in changes or []:
        if not isinstance(change, dict):
            continue
        field_code = normalize_timeline_text(change.get('fieldCode') or change.get('field_code'))
        field_label = normalize_timeline_text(change.get('fieldLabel') or change.get('field_label'))
        fingerprint = f'{field_code} {field_label}'.lower()
        if not field_code and not field_label:
            continue
        if field_code not in TIMELINE_HIGHLIGHT_META and not any(
            keyword in fingerprint for keyword in ('reason', 'comment', 'result', 'condition')
        ):
            continue
        highlights.append(
            build_timeline_highlight(
                code=field_code or field_label.lower().replace(' ', '_'),
                label=field_label or None,
                value=change.get('newValue'),
            )
        )
    return merge_timeline_highlights(highlights)


def build_timeline_highlights_from_description(description: Optional[str]) -> list[dict]:
    """Extract legacy reason-like payloads from description text."""
    normalized_description = normalize_timeline_text(description)
    if not normalized_description:
        return []

    lower_description = normalized_description.lower()
    highlights = []
    for marker, code in DESCRIPTION_PATTERNS:
        marker_lower = marker.lower()
        index = lower_description.find(marker_lower)
        if index < 0:
            continue
        value = normalized_description[index + len(marker):].strip()
        highlights.append(build_timeline_highlight(code=code, value=value))
    return merge_timeline_highlights(highlights)


def merge_timeline_highlights(*groups: Optional[Iterable[Optional[dict]]]) -> list[dict]:
    """Merge and de-duplicate highlight payloads while preserving order."""
    merged = []
    seen = set()
    for group in groups:
        for highlight in group or []:
            if not isinstance(highlight, dict):
                continue
            key = (
                normalize_timeline_text(highlight.get('code')),
                normalize_timeline_text(highlight.get('label')),
                normalize_timeline_text(highlight.get('value')),
            )
            if not key[0] or not key[2] or key in seen:
                continue
            seen.add(key)
            merged.append(
                {
                    'code': key[0],
                    'label': key[1] or key[0].replace('_', ' ').title(),
                    'value': key[2],
                    'tone': normalize_timeline_text(highlight.get('tone')) or 'info',
                }
            )
    return merged
