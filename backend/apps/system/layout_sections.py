from __future__ import annotations

from typing import Any, Dict, List, Optional


SectionTitlePayload = Dict[str, str]
SectionDefinition = Dict[str, Any]

SECTION_TITLE_KEY_PREFIX = 'system.pageLayout.sections'


def _title_ref(translation_key: str) -> SectionTitlePayload:
    return {
        'translationKey': translation_key,
    }


def _section(
    section_id: str,
    *,
    title_key: Optional[str] = None,
    icon: str = 'Document',
    order: int = 0,
    field_codes: Optional[List[str]] = None,
    collapsible: bool = False,
    collapsed: bool = False,
    columns: int = 2,
    readonly: bool = False,
) -> SectionDefinition:
    translation_key = title_key or f'{SECTION_TITLE_KEY_PREFIX}.{section_id}'
    return {
        'id': section_id,
        'title': _title_ref(translation_key),
        'translation_key': translation_key,
        'icon': icon,
        'order': order,
        'field_codes': field_codes or [],
        'collapsible': collapsible,
        'collapsed': collapsed,
        'columns': columns,
        'readonly': readonly,
    }


SYSTEM_FIELD_CODES = {
    'id',
    'organization',
    'organization_id',
    'is_deleted',
    'deleted_at',
    'deleted_by',
    'created_at',
    'created_by',
    'updated_at',
    'updated_by',
    'custom_fields',
}

SYSTEM_FIELD_PREFIXES = ('created_', 'updated_', 'deleted_')

GENERIC_SECTION_DEFINITIONS: List[SectionDefinition] = [
    _section('basic', icon='InfoFilled', order=10),
    _section('financial', icon='Money', order=20),
    _section('supplier', icon='Shop', order=30),
    _section('usage', icon='UserFilled', order=40),
    _section('status', icon='CircleCheck', order=50),
    _section('details', icon='Document', order=60),
    _section(
        'system',
        icon='Setting',
        order=90,
        collapsible=True,
        collapsed=True,
        readonly=True,
    ),
]

OBJECT_SECTION_SCHEMAS: Dict[str, List[SectionDefinition]] = {
    'Asset': [
        _section(
            'basic',
            icon='InfoFilled',
            order=10,
            field_codes=[
                'asset_code',
                'qr_code',
                'rfid_code',
                'asset_name',
                'asset_category',
                'specification',
                'brand',
                'model',
                'unit',
                'serial_number',
                'images',
                'attachments',
                'remarks',
            ],
        ),
        _section(
            'financial',
            icon='Money',
            order=20,
            field_codes=[
                'purchase_price',
                'current_value',
                'accumulated_depreciation',
                'purchase_date',
                'depreciation_start_date',
                'useful_life',
                'residual_rate',
            ],
        ),
        _section(
            'supplier',
            icon='Shop',
            order=30,
            field_codes=[
                'supplier',
                'supplier_order_no',
                'invoice_no',
            ],
        ),
        _section(
            'usage',
            icon='UserFilled',
            order=40,
            field_codes=[
                'department',
                'location',
                'custodian',
                'user',
            ],
        ),
        _section(
            'status',
            icon='CircleCheck',
            order=50,
            field_codes=['asset_status'],
        ),
    ],
    'AssetCategory': [
        _section(
            'basic',
            icon='InfoFilled',
            order=10,
            field_codes=['code', 'name', 'parent', 'description'],
        ),
        _section(
            'financial',
            title_key=f'{SECTION_TITLE_KEY_PREFIX}.depreciation',
            icon='Money',
            order=20,
            field_codes=['depreciation_method', 'default_useful_life', 'residual_rate'],
        ),
    ],
}


def get_object_section_definitions(object_code: str) -> List[SectionDefinition]:
    explicit = OBJECT_SECTION_SCHEMAS.get(str(object_code or '').strip())
    if explicit:
        return [*explicit, GENERIC_SECTION_DEFINITIONS[-1]]
    return list(GENERIC_SECTION_DEFINITIONS)


def _find_explicit_section(object_code: str, field_code: str) -> Optional[SectionDefinition]:
    for section in OBJECT_SECTION_SCHEMAS.get(str(object_code or '').strip(), []):
        if field_code in section.get('field_codes', []):
            return section
    return None


def _is_system_field(field_code: str) -> bool:
    return field_code in SYSTEM_FIELD_CODES or field_code.startswith(SYSTEM_FIELD_PREFIXES)


def resolve_section_definition(object_code: str, field_code: str) -> SectionDefinition:
    code = str(field_code or '').strip()
    if not code:
        return GENERIC_SECTION_DEFINITIONS[0]

    explicit = _find_explicit_section(object_code, code)
    if explicit:
        return explicit

    if _is_system_field(code):
        return GENERIC_SECTION_DEFINITIONS[-1]

    lower_code = code.lower()

    if any(keyword in lower_code for keyword in ('price', 'amount', 'cost', 'value', 'budget', 'depreciation', 'residual', 'premium', 'fee', 'tax')):
        return next(section for section in GENERIC_SECTION_DEFINITIONS if section['id'] == 'financial')

    if any(keyword in lower_code for keyword in ('supplier', 'vendor', 'invoice', 'purchase_order', 'order_no')):
        return next(section for section in GENERIC_SECTION_DEFINITIONS if section['id'] == 'supplier')

    if any(keyword in lower_code for keyword in ('department', 'location', 'custodian', 'handler', 'borrower', 'receiver', 'requester', 'approver', 'user')):
        return next(section for section in GENERIC_SECTION_DEFINITIONS if section['id'] == 'usage')

    if any(keyword in lower_code for keyword in ('status', 'state', 'result', 'condition')):
        return next(section for section in GENERIC_SECTION_DEFINITIONS if section['id'] == 'status')

    if lower_code in {'code', 'name', 'title'} or lower_code.endswith('_code') or lower_code.endswith('_name'):
        return next(section for section in GENERIC_SECTION_DEFINITIONS if section['id'] == 'basic')

    return next(section for section in GENERIC_SECTION_DEFINITIONS if section['id'] == 'details')


def localize_section_title(title: SectionTitlePayload, locale: Optional[str] = None) -> SectionTitlePayload:
    del locale
    return dict(title or {})


def get_field_section_metadata(
    object_code: str,
    field_code: str,
    *,
    locale: Optional[str] = None,
) -> Dict[str, Any]:
    section = resolve_section_definition(object_code, field_code)
    title_payload = localize_section_title(section['title'], locale)
    return {
        'section_name': section['id'],
        'section_title': title_payload,
        'section_title_i18n': title_payload,
        'section_translation_key': section['translation_key'],
        'section_icon': section.get('icon'),
        'section_order': section.get('order', 0),
    }
