import pytest
from django.db import connection
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.system.models import BusinessObject, ModelFieldDefinition
from apps.system.services.object_registry import ObjectRegistry

pytestmark = pytest.mark.skipif(
    connection.vendor == 'sqlite',
    reason='Hardcoded object router fallback tests require PostgreSQL test stack.',
)


def _extract_editable_fields(response_json):
    data = response_json.get('data', {}) if isinstance(response_json, dict) else {}
    editable_fields = data.get('editableFields')
    if editable_fields is None:
        editable_fields = data.get('editable_fields')
    return editable_fields or []


def _extract_reverse_relations(response_json):
    data = response_json.get('data', {}) if isinstance(response_json, dict) else {}
    reverse_relations = data.get('reverseRelations')
    if reverse_relations is None:
        reverse_relations = data.get('reverse_relations')
    return reverse_relations or []


def _field_code(item):
    return item.get('fieldCode') or item.get('field_code') or item.get('code')


def _field_type(item):
    return item.get('fieldType') or item.get('field_type')


def _upsert_business_object(code: str, name: str, model_path: str):
    BusinessObject.objects.update_or_create(
        code=code,
        defaults={
            'name': name,
            'name_en': name,
            'is_hardcoded': True,
            'django_model_path': model_path,
        },
    )
    ObjectRegistry.invalidate_cache(code)


@pytest.mark.django_db
def test_object_router_fields_falls_back_to_live_model_when_hardcoded_metadata_missing():
    org = Organization.objects.create(name='Hardcoded Fallback Org', code='hardcoded-fallback-org')
    user = User.objects.create_user(
        username='hardcoded_fallback_user',
        password='pass123456',
        organization=org,
    )

    bo = BusinessObject.objects.create(
        code='Asset',
        name='Asset',
        is_hardcoded=True,
        django_model_path='apps.assets.models.Asset',
    )

    ModelFieldDefinition.objects.filter(business_object=bo).delete()

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

    response = client.get('/api/system/objects/Asset/fields/?context=form')
    assert response.status_code == 200
    assert response.data['success'] is True

    editable_fields = _extract_editable_fields(response.json())
    assert editable_fields

    field_codes = {_field_code(item) for item in editable_fields}
    assert 'asset_name' in field_codes
    assert 'images' in field_codes
    assert 'attachments' in field_codes

    images_field = next(item for item in editable_fields if _field_code(item) == 'images')
    attachments_field = next(item for item in editable_fields if _field_code(item) == 'attachments')
    assert _field_type(images_field) == 'image'
    assert _field_type(attachments_field) == 'file'


@pytest.mark.django_db
def test_object_registry_sync_repairs_existing_image_and_file_field_types():
    bo = BusinessObject.objects.create(
        code='Asset',
        name='Asset',
        is_hardcoded=True,
        django_model_path='apps.assets.models.Asset',
    )

    ModelFieldDefinition.objects.create(
        business_object=bo,
        field_name='images',
        display_name='Images',
        field_type='json',
        django_field_type='JSONField',
        is_required=False,
        is_readonly=False,
        is_editable=True,
        is_unique=False,
        show_in_list=False,
        show_in_detail=True,
        show_in_form=True,
        sort_order=10,
    )
    ModelFieldDefinition.objects.create(
        business_object=bo,
        field_name='attachments',
        display_name='Attachments',
        field_type='json',
        django_field_type='JSONField',
        is_required=False,
        is_readonly=False,
        is_editable=True,
        is_unique=False,
        show_in_list=False,
        show_in_detail=True,
        show_in_form=True,
        sort_order=11,
    )

    synced_count = ObjectRegistry._sync_model_fields(bo)

    assert synced_count > 0
    assert ModelFieldDefinition.objects.get(business_object=bo, field_name='images').field_type == 'image'
    assert ModelFieldDefinition.objects.get(business_object=bo, field_name='attachments').field_type == 'file'


@pytest.mark.django_db
def test_object_router_fields_use_relation_definitions_for_hardcoded_reverse_relations():
    org = Organization.objects.create(name='Hardcoded Relation Org', code='hardcoded-relation-org')
    user = User.objects.create_user(
        username='hardcoded_relation_user',
        password='pass123456',
        organization=org,
    )

    _upsert_business_object('Asset', 'Asset', 'apps.assets.models.Asset')
    _upsert_business_object('AssetTransfer', 'Asset Transfer', 'apps.assets.models.AssetTransfer')
    _upsert_business_object('Maintenance', 'Maintenance', 'apps.lifecycle.models.Maintenance')

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id), HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9')

    response = client.get('/api/system/objects/Asset/fields/?context=detail&include_relations=true')
    assert response.status_code == 200
    assert response.data['success'] is True

    reverse_relations = _extract_reverse_relations(response.json())
    assert reverse_relations

    relation_codes = {_field_code(item) for item in reverse_relations}
    assert 'transfer_orders' in relation_codes
    assert 'transfer_items' not in relation_codes

    transfer_relation = next(item for item in reverse_relations if _field_code(item) == 'transfer_orders')
    assert (transfer_relation.get('targetObjectCode') or transfer_relation.get('target_object_code')) == 'AssetTransfer'
    assert (transfer_relation.get('reverseRelationModel') or transfer_relation.get('reverse_relation_model')) == 'apps.assets.models.AssetTransfer'


@pytest.mark.django_db
def test_object_router_runtime_exposes_reference_display_metadata_for_hardcoded_fields():
    org = Organization.objects.create(name='Hardcoded Runtime Field Org', code='hardcoded-runtime-field-org')
    user = User.objects.create_user(
        username='hardcoded_runtime_field_user',
        password='pass123456',
        organization=org,
    )

    _upsert_business_object('Asset', 'Asset', 'apps.assets.models.Asset')

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

    response = client.get('/api/system/objects/Asset/runtime/?mode=list')
    assert response.status_code == 200
    assert response.data['success'] is True

    fields_payload = response.json().get('data', {}).get('fields', {})
    editable_fields = fields_payload.get('editableFields')
    if editable_fields is None:
        editable_fields = fields_payload.get('editable_fields')
    editable_fields = editable_fields or []

    department_field = next(item for item in editable_fields if _field_code(item) == 'department')
    location_field = next(item for item in editable_fields if _field_code(item) == 'location')
    custodian_field = next(item for item in editable_fields if _field_code(item) == 'custodian')

    assert _field_type(department_field) == 'department'
    assert (department_field.get('referenceDisplayField') or department_field.get('reference_display_field')) == 'name'

    assert _field_type(location_field) == 'location'
    assert (location_field.get('referenceDisplayField') or location_field.get('reference_display_field')) == 'path'

    assert _field_type(custodian_field) == 'user'
    assert (custodian_field.get('referenceDisplayField') or custodian_field.get('reference_display_field')) == 'username'
