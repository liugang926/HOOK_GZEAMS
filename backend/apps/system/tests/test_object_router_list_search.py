import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.system.models import BusinessObject, DynamicData, FieldDefinition


def _build_authed_client(org, user):
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))
    return client


@pytest.mark.django_db
def test_object_router_list_keyword_search_matches_dynamic_and_legacy_json_fields():
    org = Organization.objects.create(name='Search Org', code='search-org')
    user = User.objects.create_user(username='search-user', password='pass123456', organization=org)
    bo = BusinessObject.objects.create(code='SEARCHOBJ', name='Search Object', is_hardcoded=False)
    FieldDefinition.objects.create(
        business_object=bo,
        code='title',
        name='Title',
        field_type='text',
        is_searchable=True,
        show_in_list=True,
        show_in_form=True,
        show_in_detail=True,
        sort_order=1,
    )

    dynamic_record = DynamicData.objects.create(
        business_object=bo,
        organization=org,
        data_no='SEARCH0001',
        dynamic_fields={'title': 'Alpha Laptop'},
        custom_fields={},
    )
    legacy_record = DynamicData.objects.create(
        business_object=bo,
        organization=org,
        data_no='SEARCH0002',
        dynamic_fields={},
        custom_fields={'title': 'Legacy Printer'},
    )

    client = _build_authed_client(org, user)

    dynamic_resp = client.get('/api/system/objects/SEARCHOBJ/', {'search': 'Alpha'})
    assert dynamic_resp.status_code == 200
    dynamic_results = dynamic_resp.json()['data']['results']
    assert [item['id'] for item in dynamic_results] == [str(dynamic_record.id)]

    legacy_resp = client.get('/api/system/objects/SEARCHOBJ/', {'search': 'Legacy'})
    assert legacy_resp.status_code == 200
    legacy_results = legacy_resp.json()['data']['results']
    assert [item['id'] for item in legacy_results] == [str(legacy_record.id)]


@pytest.mark.django_db
def test_object_router_list_selected_field_filter_supports_text_contains_search():
    org = Organization.objects.create(name='Field Search Org', code='field-search-org')
    user = User.objects.create_user(username='field-search-user', password='pass123456', organization=org)
    bo = BusinessObject.objects.create(code='FIELDSEARCHOBJ', name='Field Search Object', is_hardcoded=False)
    FieldDefinition.objects.create(
        business_object=bo,
        code='title',
        name='Title',
        field_type='text',
        is_searchable=True,
        show_in_list=True,
        show_in_form=True,
        show_in_detail=True,
        sort_order=1,
    )

    matched = DynamicData.objects.create(
        business_object=bo,
        organization=org,
        data_no='FIELD0001',
        dynamic_fields={'title': 'Office Desk Alpha'},
        custom_fields={},
    )
    DynamicData.objects.create(
        business_object=bo,
        organization=org,
        data_no='FIELD0002',
        dynamic_fields={'title': 'Warehouse Shelf'},
        custom_fields={},
    )

    client = _build_authed_client(org, user)

    response = client.get('/api/system/objects/FIELDSEARCHOBJ/', {'title': 'Desk'})
    assert response.status_code == 200

    results = response.json()['data']['results']
    assert [item['id'] for item in results] == [str(matched.id)]

