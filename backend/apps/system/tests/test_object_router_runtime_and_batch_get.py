import pytest
from django.db import connection
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.system.models import BusinessObject, FieldDefinition, PageLayout

pytestmark = pytest.mark.skipif(
    connection.vendor == 'sqlite',
    reason='System migrations and router tests require PostgreSQL features (e.g., ON CONFLICT).',
)


@pytest.mark.django_db
def test_object_router_runtime_returns_layout_and_fields():
    org = Organization.objects.create(name='Test Org', code='test-org')
    user = User.objects.create(username='testuser', organization=org)

    bo = BusinessObject.objects.create(code='TESTOBJ', name='Test Object', is_hardcoded=False)
    FieldDefinition.objects.create(
        business_object=bo,
        code='name',
        name='Name',
        field_type='text',
        show_in_form=True,
        show_in_detail=True,
    )

    shared_form = PageLayout.objects.create(
        business_object=bo,
        layout_code='TESTOBJ_form',
        layout_name='Shared Form',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={
            'sections': [
                {
                    'id': 's-form',
                    'name': 's-form',
                    'title': 'Form',
                    'columns': 2,
                    'fields': [
                        {'fieldCode': 'name', 'label': 'Name (Form)', 'span': 12},
                    ],
                }
            ]
        },
    )
    # Legacy readonly layout should be ignored by runtime readonly under shared model.
    PageLayout.objects.create(
        business_object=bo,
        layout_code='TESTOBJ_detail',
        layout_name='Detail',
        layout_type='detail',
        mode='readonly',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={
            'sections': [
                {
                    'id': 's1',
                    'name': 's1',
                    'title': 'Detail',
                    'columns': 2,
                    'fields': [
                        {'fieldCode': 'name', 'label': 'Name', 'span': 12, 'readonly': True},
                    ],
                }
            ]
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get('/api/system/objects/TESTOBJ/runtime/?mode=readonly')
    assert resp.status_code == 200

    payload = resp.json()
    assert payload['success'] is True
    data = payload['data']
    assert data['objectCode'] == 'TESTOBJ'
    assert data['mode'] == 'readonly'
    assert isinstance(data.get('permissions'), dict)
    assert {'view', 'add', 'change', 'delete'}.issubset(set(data['permissions'].keys()))

    fields = data['fields']
    assert isinstance(fields.get('editableFields'), list)
    assert any(f.get('code') == 'name' for f in fields['editableFields'])
    assert fields.get('context') == 'form'

    layout = data['layout']
    assert isinstance(layout.get('layoutConfig'), dict)
    assert isinstance(layout['layoutConfig'].get('sections'), list)
    assert str(layout.get('id')) == str(shared_form.id)
    assert (layout.get('layoutType') or layout.get('layout_type')) == 'form'


@pytest.mark.django_db
def test_object_router_batch_get_returns_ordered_results():
    org = Organization.objects.create(name='Batch Org', code='batch-org')
    user = User.objects.create(username='batchuser', organization=org)

    # Register hardcoded object meta via BusinessObject row (ObjectRegistry reads DB first).
    BusinessObject.objects.create(
        code='Organization',
        name='Organization',
        is_hardcoded=True,
        django_model_path='apps.organizations.models.Organization',
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post(
        '/api/system/objects/Organization/batch-get/',
        {'ids': [str(org.id)]},
        format='json',
    )
    assert resp.status_code == 200

    payload = resp.json()
    assert payload['success'] is True
    results = payload['data']['results']
    assert len(results) == 1
    assert results[0]['id'] == str(org.id)


@pytest.mark.django_db
def test_object_router_runtime_prefers_published_layout_over_draft_custom():
    org = Organization.objects.create(name='Runtime Priority Org', code='runtime-priority-org')
    user = User.objects.create(username='runtimepriorityuser', organization=org)

    bo = BusinessObject.objects.create(code='RTPRIOBJ', name='Runtime Priority Object', is_hardcoded=False)
    FieldDefinition.objects.create(
        business_object=bo,
        code='name',
        name='Name',
        field_type='text',
        show_in_form=True,
        show_in_detail=True,
    )

    draft_custom = PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code='rtpriobj_form_custom_draft',
        layout_name='Draft Custom Form',
        layout_type='form',
        mode='edit',
        status='draft',
        is_default=False,
        is_active=True,
        layout_config={
            'sections': [
                {
                    'id': 's-draft',
                    'type': 'section',
                    'title': 'Draft Form',
                    'fields': [
                        {'fieldCode': 'name', 'label': 'Name (Draft Form)', 'span': 12},
                    ],
                }
            ]
        },
    )
    published_default = PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code='rtpriobj_form_default_published',
        layout_name='Published Default Form',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={
            'sections': [
                {
                    'id': 's-published',
                    'type': 'section',
                    'title': 'Published Form',
                    'fields': [
                        {'fieldCode': 'name', 'label': 'Name (Published Form)', 'span': 12},
                    ],
                }
            ]
        },
    )
    # Legacy detail layout should not be selected for readonly runtime.
    PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code='rtpriobj_detail_default_published',
        layout_name='Published Default Detail Legacy',
        layout_type='detail',
        mode='readonly',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={
            'sections': [
                {
                    'id': 's-detail',
                    'type': 'section',
                    'title': 'Published Detail Legacy',
                    'fields': [
                        {'fieldCode': 'name', 'label': 'Name (Legacy Detail)', 'span': 12, 'readonly': True},
                    ],
                }
            ]
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get('/api/system/objects/RTPRIOBJ/runtime/?mode=readonly')
    assert resp.status_code == 200

    payload = resp.json()
    assert payload['success'] is True
    layout = payload['data']['layout']
    assert str(layout['id']) == str(published_default.id)
    assert str(layout['id']) != str(draft_custom.id)
    assert (layout.get('layoutType') or layout.get('layout_type')) == 'form'


@pytest.mark.django_db
def test_object_router_runtime_list_uses_field_driven_columns_not_legacy_list_layout():
    org = Organization.objects.create(name='Runtime List Org', code='runtime-list-org')
    user = User.objects.create(username='runtimelistuser', organization=org)

    bo = BusinessObject.objects.create(code='RTLISTOBJ', name='Runtime List Object', is_hardcoded=False)
    FieldDefinition.objects.create(
        business_object=bo,
        code='name',
        name='Name',
        field_type='text',
        show_in_list=True,
        show_in_form=True,
        show_in_detail=True,
        sort_order=1,
    )
    FieldDefinition.objects.create(
        business_object=bo,
        code='hidden_note',
        name='Hidden Note',
        field_type='text',
        show_in_list=False,
        show_in_form=True,
        show_in_detail=True,
        sort_order=2,
    )

    # Legacy list layout should no longer drive runtime list columns.
    PageLayout.objects.create(
        business_object=bo,
        layout_code='rtlistobj_list_legacy_default',
        layout_name='Legacy List',
        layout_type='list',
        mode='edit',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={
            'columns': [
                {'fieldCode': 'legacy_only', 'label': 'Legacy Only', 'width': 180, 'visible': True},
            ]
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get('/api/system/objects/RTLISTOBJ/runtime/?mode=list')
    assert resp.status_code == 200

    payload = resp.json()
    assert payload['success'] is True
    data = payload['data']
    assert data['mode'] == 'list'
    assert data['fields']['context'] == 'list'

    layout = data['layout']
    assert (layout.get('layoutType') or layout.get('layout_type')) == 'list'
    layout_config = layout.get('layoutConfig') or layout.get('layout_config') or {}
    columns = layout_config.get('columns') or []
    field_codes = {
        str(col.get('fieldCode') or col.get('field_code') or col.get('prop') or '')
        for col in columns
    }

    assert 'name' in field_codes
    assert 'hidden_note' not in field_codes
    assert 'legacy_only' not in field_codes
