import pytest

from apps.system.models import BusinessObject, FieldDefinition
from apps.system.services.layout_generator import LayoutGenerator


def _extract_section_field_codes(layout_config: dict) -> list[str]:
    codes: list[str] = []
    for section in layout_config.get('sections', []):
        for field in section.get('fields', []):
            code = field.get('fieldCode') or field.get('field_code') or field.get('prop')
            if code:
                codes.append(str(code))
    return codes


def _sections_by_id(layout_config: dict) -> dict[str, dict]:
    return {
        str(section.get('id') or section.get('name') or ''): section
        for section in layout_config.get('sections', [])
        if str(section.get('id') or section.get('name') or '').strip()
    }


@pytest.mark.django_db
def test_layout_generator_respects_visibility_flags_for_dynamic_object():
    business_object = BusinessObject.objects.create(
        code='LAYOUTFLAGBO',
        name='Layout Flag BO',
        is_hardcoded=False,
    )

    FieldDefinition.objects.create(
        business_object=business_object,
        code='name',
        name='Name',
        field_type='text',
        show_in_form=True,
        show_in_detail=True,
        show_in_list=True,
        sort_order=1,
    )
    FieldDefinition.objects.create(
        business_object=business_object,
        code='hidden_form',
        name='Hidden In Form',
        field_type='text',
        show_in_form=False,
        show_in_detail=True,
        show_in_list=True,
        sort_order=2,
    )
    FieldDefinition.objects.create(
        business_object=business_object,
        code='hidden_detail',
        name='Hidden In Detail',
        field_type='text',
        show_in_form=True,
        show_in_detail=False,
        show_in_list=True,
        sort_order=3,
    )
    FieldDefinition.objects.create(
        business_object=business_object,
        code='hidden_list',
        name='Hidden In List',
        field_type='text',
        show_in_form=True,
        show_in_detail=True,
        show_in_list=False,
        sort_order=4,
    )
    FieldDefinition.objects.create(
        business_object=business_object,
        code='maintenance_records',
        name='Maintenance Records',
        field_type='related_object',
        is_reverse_relation=True,
        show_in_form=True,
        show_in_detail=True,
        show_in_list=False,
        sort_order=5,
    )

    form_layout = LayoutGenerator.generate_form_layout(business_object)
    detail_layout = LayoutGenerator.generate_detail_layout(business_object)
    list_layout = LayoutGenerator.generate_list_layout(business_object)

    form_codes = _extract_section_field_codes(form_layout)
    detail_codes = _extract_section_field_codes(detail_layout)
    list_codes = [str(column.get('fieldCode') or '') for column in list_layout.get('columns', [])]

    assert 'name' in form_codes
    assert 'hidden_detail' in form_codes
    assert 'hidden_list' in form_codes
    assert 'hidden_form' not in form_codes
    assert 'maintenance_records' not in form_codes

    assert 'name' in detail_codes
    assert 'hidden_form' in detail_codes
    assert 'hidden_list' in detail_codes
    assert 'hidden_detail' not in detail_codes
    assert 'maintenance_records' not in detail_codes

    assert 'name' in list_codes
    assert 'hidden_form' in list_codes
    assert 'hidden_detail' in list_codes
    assert 'hidden_list' not in list_codes
    assert 'maintenance_records' not in list_codes


@pytest.mark.django_db
def test_layout_generator_uses_backend_section_schema_for_asset():
    business_object = BusinessObject.objects.create(
        code='Asset',
        name='Asset',
        is_hardcoded=False,
    )

    field_specs = [
        ('asset_code', 1),
        ('asset_name', 2),
        ('asset_category', 3),
        ('purchase_price', 4),
        ('supplier', 5),
        ('department', 6),
        ('asset_status', 7),
        ('created_at', 8),
    ]
    for code, sort_order in field_specs:
        FieldDefinition.objects.create(
            business_object=business_object,
            code=code,
            name=code,
            field_type='text',
            show_in_form=True,
            show_in_detail=True,
            show_in_list=True,
            sort_order=sort_order,
        )

    form_layout = LayoutGenerator.generate_form_layout(business_object)
    section_map = _sections_by_id(form_layout)

    assert list(section_map.keys()) == ['basic', 'financial', 'supplier', 'usage', 'status', 'system']
    assert section_map['basic']['title']['translationKey'] == 'system.pageLayout.sections.basic'
    assert section_map['financial']['title']['translationKey'] == 'system.pageLayout.sections.financial'

    basic_codes = [field['fieldCode'] for field in section_map['basic']['fields']]
    financial_codes = [field['fieldCode'] for field in section_map['financial']['fields']]
    supplier_codes = [field['fieldCode'] for field in section_map['supplier']['fields']]
    usage_codes = [field['fieldCode'] for field in section_map['usage']['fields']]
    status_codes = [field['fieldCode'] for field in section_map['status']['fields']]
    system_codes = [field['fieldCode'] for field in section_map['system']['fields']]

    assert basic_codes == ['asset_code', 'asset_name', 'asset_category']
    assert financial_codes == ['purchase_price']
    assert supplier_codes == ['supplier']
    assert usage_codes == ['department']
    assert status_codes == ['asset_status']
    assert system_codes == ['created_at']
