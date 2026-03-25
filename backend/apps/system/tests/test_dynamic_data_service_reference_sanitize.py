"""
Unit tests for DynamicDataService reference payload sanitization.
"""
from types import SimpleNamespace

from apps.system.services.dynamic_data_service import DynamicDataService


def _service():
    return DynamicDataService('Asset')


def test_sanitize_reference_dict_value_extracts_id():
    service = _service()
    field_defs = {
        'supplier': SimpleNamespace(field_type='reference'),
        'asset_name': SimpleNamespace(field_type='text'),
    }
    payload = {
        'supplier': {
            'id': '4f5d3f6a-9b3e-4b2f-8d90-9876543210ab',
            'name': 'Supplier A',
        },
        'asset_name': 'Laptop',
    }

    sanitized = service._sanitize_reference_fields(payload, field_defs)

    assert sanitized['supplier'] == '4f5d3f6a-9b3e-4b2f-8d90-9876543210ab'
    assert sanitized['asset_name'] == 'Laptop'


def test_sanitize_reference_list_values_extracts_each_id():
    service = _service()
    field_defs = {
        'reviewers': SimpleNamespace(field_type='user'),
    }
    payload = {
        'reviewers': [
            {'id': '11111111-1111-1111-1111-111111111111', 'username': 'u1'},
            '22222222-2222-2222-2222-222222222222',
        ]
    }

    sanitized = service._sanitize_reference_fields(payload, field_defs)

    assert sanitized['reviewers'] == [
        '11111111-1111-1111-1111-111111111111',
        '22222222-2222-2222-2222-222222222222',
    ]
