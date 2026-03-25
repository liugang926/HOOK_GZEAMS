from apps.system.validators import (
    LayoutValidationError,
    normalize_layout_config_structure,
    sanitize_layout_config_field_codes,
    validate_layout_config_by_mode,
)


def test_normalize_layout_config_structure_supports_detail_region():
    config = {
        'sections': [
            {
                'type': 'detail-region',
                'relation_code': 'pickup_items',
                'field_code': 'items',
                'target_object_code': 'PickupItem',
                'detail_edit_mode': 'inline_table',
            }
        ]
    }

    normalized = normalize_layout_config_structure(config)
    section = normalized['sections'][0]

    assert section['type'] == 'detail-region'
    assert section['relationCode'] == 'pickup_items'
    assert section['fieldCode'] == 'items'
    assert section['targetObjectCode'] == 'PickupItem'
    assert section['detailEditMode'] == 'inline_table'
    assert section['columns'] == 1


def test_validate_layout_config_by_mode_accepts_detail_region():
    config = {
        'sections': [
            {
                'id': 'detail-items',
                'type': 'detail-region',
                'title': 'Items',
                'relationCode': 'pickup_items',
                'fieldCode': 'items',
                'targetObjectCode': 'PickupItem',
                'detailEditMode': 'inline_table',
                'toolbarConfig': {'allowCreate': True},
                'summaryRules': [{'field': 'quantity', 'aggregate': 'sum'}],
                'validationRules': [{'rule': 'min_rows', 'value': 1}],
            }
        ]
    }

    validate_layout_config_by_mode(config, 'edit')


def test_validate_layout_config_by_mode_rejects_missing_detail_region_field_code():
    config = {
        'sections': [
            {
                'id': 'detail-items',
                'type': 'detail-region',
                'relationCode': 'pickup_items',
            }
        ]
    }

    try:
        validate_layout_config_by_mode(config, 'edit')
    except LayoutValidationError as exc:
        assert 'fieldCode' in str(exc)
    else:
        raise AssertionError('Expected detail-region validation to fail without fieldCode')


def test_sanitize_layout_config_field_codes_sanitizes_detail_region_field_code():
    config = {
        'sections': [
            {
                'id': 'detail-items',
                'type': 'detail-region',
                'relationCode': 'pickup_items',
                'fieldCode': 'Items',
            }
        ]
    }

    sanitized = sanitize_layout_config_field_codes(config, {'items'})
    section = sanitized['sections'][0]

    assert section['fieldCode'] == 'items'


def test_normalize_layout_config_structure_supports_workflow_progress():
    config = {
        'sections': [
            {
                'type': 'workflow-progress',
                'status_field_code': 'status',
                'translation_key': 'common.documentWorkbench.sections.workflowProgress',
            }
        ]
    }

    normalized = normalize_layout_config_structure(config)
    section = normalized['sections'][0]

    assert section['type'] == 'workflow-progress'
    assert section['statusFieldCode'] == 'status'
    assert section['translationKey'] == 'common.documentWorkbench.sections.workflowProgress'
    assert section['columns'] == 1
    assert section['position'] == 'main'


def test_validate_layout_config_by_mode_accepts_workflow_progress():
    config = {
        'sections': [
            {
                'id': 'workflow-progress',
                'type': 'workflow-progress',
                'title': 'Workflow Progress',
                'statusFieldCode': 'status',
            }
        ]
    }

    validate_layout_config_by_mode(config, 'edit')


def test_validate_layout_config_by_mode_rejects_invalid_workflow_progress_status_field_code():
    config = {
        'sections': [
            {
                'id': 'workflow-progress',
                'type': 'workflow-progress',
                'statusFieldCode': '',
            }
        ]
    }

    try:
        validate_layout_config_by_mode(config, 'edit')
    except LayoutValidationError as exc:
        assert 'statusFieldCode' in str(exc)
    else:
        raise AssertionError('Expected workflow-progress validation to fail without statusFieldCode')
