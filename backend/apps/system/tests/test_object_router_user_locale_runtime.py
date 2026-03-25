import pytest
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from rest_framework.test import APIClient

from apps.accounts.models import User, UserOrganization
from apps.organizations.models import Organization
from apps.system.models import BusinessObject, FieldDefinition, SystemConfig, Translation

pytestmark = pytest.mark.skipif(
    connection.vendor == 'sqlite',
    reason='System router locale tests require PostgreSQL test stack.',
)


def _extract_editable_fields_from_response(resp_data):
    payload = resp_data.get('data', {}) if isinstance(resp_data, dict) else {}
    fields_payload = payload.get('fields', {}) if isinstance(payload, dict) else {}
    editable_fields = fields_payload.get('editableFields')
    if editable_fields is None:
        editable_fields = fields_payload.get('editable_fields')
    return editable_fields or []


def _field_code(item):
    return item.get('fieldCode') or item.get('field_code') or item.get('code')


def _preferred_language(user_payload):
    return user_payload.get('preferredLanguage') or user_payload.get('preferred_language')


@pytest.mark.django_db
def test_user_me_profile_reads_and_updates_preferred_language():
    org = Organization.objects.create(name='Locale Org', code='locale-org')
    user = User.objects.create_user(
        username='locale_user',
        password='pass123456',
        organization=org,
        preferred_language='zh-CN',
    )
    UserOrganization.objects.create(
        user=user,
        organization=org,
        role='admin',
        is_active=True,
        is_primary=True,
    )
    user.current_organization = org
    user.save(update_fields=['current_organization'])

    BusinessObject.objects.get_or_create(
        code='User',
        defaults={
            'name': 'User',
            'is_hardcoded': False,
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

    me_resp = client.get('/api/system/objects/User/me/')
    assert me_resp.status_code == 200
    assert me_resp.data['success'] is True
    assert _preferred_language(me_resp.data['data']) == 'zh-CN'

    patch_resp = client.patch(
        '/api/system/objects/User/me/profile/',
        {'preferredLanguage': 'en-US'},
        format='json',
    )
    assert patch_resp.status_code == 200
    assert patch_resp.data['success'] is True
    assert _preferred_language(patch_resp.data['data']) == 'en-US'

    user.refresh_from_db()
    assert user.preferred_language == 'en-US'


@pytest.mark.django_db
def test_user_detail_route_uses_membership_scope_instead_of_base_organization_filter():
    org = Organization.objects.create(name='User Detail Org', code='user-detail-org')
    user = User.objects.create_user(
        username='user_detail_member',
        password='pass123456',
        organization=None,
        email='user-detail@example.com',
    )
    UserOrganization.objects.create(
        user=user,
        organization=org,
        role='admin',
        is_active=True,
        is_primary=True,
    )
    user.current_organization = org
    user.save(update_fields=['current_organization'])

    BusinessObject.objects.get_or_create(
        code='User',
        defaults={
            'name': 'User',
            'is_hardcoded': False,
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

    list_resp = client.get('/api/system/objects/User/')
    assert list_resp.status_code == 200
    assert list_resp.data['success'] is True
    results = list_resp.data['data']['results']
    assert any(str(item['id']) == str(user.id) for item in results)

    detail_resp = client.get(f'/api/system/objects/User/{user.id}/')
    assert detail_resp.status_code == 200
    assert detail_resp.data['success'] is True
    assert str(detail_resp.data['data']['id']) == str(user.id)


@pytest.mark.django_db
def test_runtime_returns_locale_and_localized_field_name():
    org = Organization.objects.create(name='Runtime Locale Org', code='runtime-locale-org')
    user = User.objects.create_user(
        username='runtime_locale_user',
        password='pass123456',
        organization=org,
        preferred_language='zh-CN',
    )
    UserOrganization.objects.create(
        user=user,
        organization=org,
        role='admin',
        is_active=True,
        is_primary=True,
    )
    user.current_organization = org
    user.save(update_fields=['current_organization'])

    bo = BusinessObject.objects.create(
        code='RTLOCALEOBJ',
        name='Runtime Locale Object',
        is_hardcoded=False,
    )
    fd = FieldDefinition.objects.create(
        business_object=bo,
        code='asset_name',
        name='资产名称',
        field_type='text',
        show_in_form=True,
        show_in_detail=True,
    )

    content_type = ContentType.objects.get_for_model(fd)
    Translation.objects.create(
        content_type=content_type,
        object_id=fd.id,
        field_name='name',
        language_code='en-US',
        text='Asset Name',
    )

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(
        HTTP_X_ORGANIZATION_ID=str(org.id),
        HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9',
    )

    runtime_resp = client.get('/api/system/objects/RTLOCALEOBJ/runtime/?mode=readonly')
    assert runtime_resp.status_code == 200
    assert runtime_resp.data['success'] is True

    payload = runtime_resp.data['data']
    assert payload['locale'] == 'en-US'
    assert 'layoutSource' in payload or 'layout_source' in payload
    assert 'layoutLayers' in payload or 'layout_layers' in payload

    editable_fields = _extract_editable_fields_from_response(runtime_resp.data)
    target_field = next((item for item in editable_fields if _field_code(item) == 'asset_name'), None)
    assert target_field is not None
    assert target_field.get('name') == 'Asset Name'


@pytest.mark.django_db
def test_runtime_i18n_feature_flag_off_returns_original_field_name():
    org = Organization.objects.create(name='Runtime Locale Org 2', code='runtime-locale-org-2')
    user = User.objects.create_user(
        username='runtime_locale_user_2',
        password='pass123456',
        organization=org,
        preferred_language='zh-CN',
    )
    UserOrganization.objects.create(
        user=user,
        organization=org,
        role='admin',
        is_active=True,
        is_primary=True,
    )
    user.current_organization = org
    user.save(update_fields=['current_organization'])

    SystemConfig.objects.create(
        organization=org,
        config_key='runtime_i18n_enabled',
        config_value='false',
        value_type='boolean',
        name='Runtime i18n Enabled',
    )

    bo = BusinessObject.objects.create(
        code='RTLOCALEOBJ2',
        name='Runtime Locale Object 2',
        is_hardcoded=False,
    )
    fd = FieldDefinition.objects.create(
        business_object=bo,
        code='asset_name',
        name='Asset Name Default',
        field_type='text',
        show_in_form=True,
        show_in_detail=True,
    )

    content_type = ContentType.objects.get_for_model(fd)
    Translation.objects.create(
        content_type=content_type,
        object_id=fd.id,
        field_name='name',
        language_code='en-US',
        text='Asset Name Localized',
    )

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(
        HTTP_X_ORGANIZATION_ID=str(org.id),
        HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9',
    )

    runtime_resp = client.get('/api/system/objects/RTLOCALEOBJ2/runtime/?mode=readonly')
    assert runtime_resp.status_code == 200
    assert runtime_resp.data['success'] is True

    editable_fields = _extract_editable_fields_from_response(runtime_resp.data)
    target_field = next((item for item in editable_fields if _field_code(item) == 'asset_name'), None)
    assert target_field is not None
    assert target_field.get('name') == 'Asset Name Default'


@pytest.mark.django_db
def test_fields_strict_mode_returns_field_code_only():
    org = Organization.objects.create(name='Strict Field Org', code='strict-field-org')
    user = User.objects.create_user(
        username='strict_field_user',
        password='pass123456',
        organization=org,
        preferred_language='en-US',
    )
    UserOrganization.objects.create(
        user=user,
        organization=org,
        role='admin',
        is_active=True,
        is_primary=True,
    )
    user.current_organization = org
    user.save(update_fields=['current_organization'])

    SystemConfig.objects.create(
        organization=org,
        config_key='field_code_strict_mode',
        config_value='true',
        value_type='boolean',
        name='Field Code Strict Mode',
    )

    bo = BusinessObject.objects.create(
        code='STRICTOBJ',
        name='Strict Object',
        is_hardcoded=False,
    )
    FieldDefinition.objects.create(
        business_object=bo,
        code='asset_name',
        name='Asset Name',
        field_type='text',
        show_in_form=True,
    )

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

    fields_resp = client.get('/api/system/objects/STRICTOBJ/fields/?context=form')
    assert fields_resp.status_code == 200
    assert fields_resp.data['success'] is True

    data = fields_resp.data.get('data', {})
    editable_fields = data.get('editableFields')
    if editable_fields is None:
        editable_fields = data.get('editable_fields')
    editable_fields = editable_fields or []
    target_field = next((item for item in editable_fields if _field_code(item) == 'asset_name'), None)
    assert target_field is not None
    assert 'code' not in target_field
    assert (target_field.get('fieldCode') or target_field.get('field_code')) == 'asset_name'


@pytest.mark.django_db
def test_fields_default_mode_keeps_legacy_code_for_compatibility():
    org = Organization.objects.create(name='Compat Field Org', code='compat-field-org')
    user = User.objects.create_user(
        username='compat_field_user',
        password='pass123456',
        organization=org,
        preferred_language='en-US',
    )
    UserOrganization.objects.create(
        user=user,
        organization=org,
        role='admin',
        is_active=True,
        is_primary=True,
    )
    user.current_organization = org
    user.save(update_fields=['current_organization'])

    bo = BusinessObject.objects.create(
        code='COMPACTOBJ',
        name='Compat Object',
        is_hardcoded=False,
    )
    FieldDefinition.objects.create(
        business_object=bo,
        code='asset_name',
        name='Asset Name',
        field_type='text',
        show_in_form=True,
    )

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

    fields_resp = client.get('/api/system/objects/COMPACTOBJ/fields/?context=form')
    assert fields_resp.status_code == 200
    assert fields_resp.data['success'] is True

    data = fields_resp.data.get('data', {})
    editable_fields = data.get('editableFields')
    if editable_fields is None:
        editable_fields = data.get('editable_fields')
    editable_fields = editable_fields or []
    target_field = next((item for item in editable_fields if _field_code(item) == 'asset_name'), None)
    assert target_field is not None
    assert target_field.get('code') == 'asset_name'
    assert (target_field.get('fieldCode') or target_field.get('field_code')) == 'asset_name'


@pytest.mark.django_db
def test_runtime_layout_layers_fallback_when_unified_merge_disabled():
    org = Organization.objects.create(name='Legacy Merge Org', code='legacy-merge-org')
    user = User.objects.create_user(
        username='legacy_merge_user',
        password='pass123456',
        organization=org,
        preferred_language='en-US',
    )
    UserOrganization.objects.create(
        user=user,
        organization=org,
        role='admin',
        is_active=True,
        is_primary=True,
    )
    user.current_organization = org
    user.save(update_fields=['current_organization'])

    SystemConfig.objects.create(
        organization=org,
        config_key='layout_merge_unified_enabled',
        config_value='false',
        value_type='boolean',
        name='Layout Merge Unified Enabled',
    )

    bo = BusinessObject.objects.create(
        code='LAYOUTFLAGOBJ',
        name='Layout Flag Object',
        is_hardcoded=False,
    )
    FieldDefinition.objects.create(
        business_object=bo,
        code='asset_name',
        name='Asset Name',
        field_type='text',
        show_in_form=True,
    )

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

    runtime_resp = client.get('/api/system/objects/LAYOUTFLAGOBJ/runtime/?mode=readonly')
    assert runtime_resp.status_code == 200
    assert runtime_resp.data['success'] is True

    payload = runtime_resp.data['data']
    layout_layers = payload.get('layoutLayers')
    if layout_layers is None:
        layout_layers = payload.get('layout_layers')
    assert layout_layers == ['default']


@pytest.mark.django_db
def test_runtime_locale_falls_back_to_profile_when_header_missing():
    org = Organization.objects.create(name='Profile Locale Org', code='profile-locale-org')
    user = User.objects.create_user(
        username='profile_locale_user',
        password='pass123456',
        organization=org,
        preferred_language='en-US',
    )
    UserOrganization.objects.create(
        user=user,
        organization=org,
        role='admin',
        is_active=True,
        is_primary=True,
    )
    user.current_organization = org
    user.save(update_fields=['current_organization'])

    bo = BusinessObject.objects.create(
        code='PROFILELOCALEOBJ',
        name='Profile Locale Object',
        is_hardcoded=False,
    )
    FieldDefinition.objects.create(
        business_object=bo,
        code='asset_name',
        name='Asset Name',
        field_type='text',
        show_in_form=True,
    )

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

    runtime_resp = client.get('/api/system/objects/PROFILELOCALEOBJ/runtime/?mode=readonly')
    assert runtime_resp.status_code == 200
    assert runtime_resp.data['success'] is True
    assert runtime_resp.data['data']['locale'] == 'en-US'


@pytest.mark.django_db
def test_runtime_locale_falls_back_to_system_default_when_profile_unsupported():
    org = Organization.objects.create(name='Default Locale Org', code='default-locale-org')
    user = User.objects.create_user(
        username='default_locale_user',
        password='pass123456',
        organization=org,
        preferred_language='es-ES',
    )
    UserOrganization.objects.create(
        user=user,
        organization=org,
        role='admin',
        is_active=True,
        is_primary=True,
    )
    user.current_organization = org
    user.save(update_fields=['current_organization'])

    bo = BusinessObject.objects.create(
        code='DEFAULTLOCALEOBJ',
        name='Default Locale Object',
        is_hardcoded=False,
    )
    FieldDefinition.objects.create(
        business_object=bo,
        code='asset_name',
        name='Asset Name',
        field_type='text',
        show_in_form=True,
    )

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

    runtime_resp = client.get('/api/system/objects/DEFAULTLOCALEOBJ/runtime/?mode=readonly')
    assert runtime_resp.status_code == 200
    assert runtime_resp.data['success'] is True
    assert runtime_resp.data['data']['locale'] == 'zh-CN'


@pytest.mark.django_db
def test_runtime_localized_field_falls_back_to_original_when_translation_missing():
    org = Organization.objects.create(name='Fallback Translation Org', code='fallback-translation-org')
    user = User.objects.create_user(
        username='fallback_translation_user',
        password='pass123456',
        organization=org,
        preferred_language='en-US',
    )
    UserOrganization.objects.create(
        user=user,
        organization=org,
        role='admin',
        is_active=True,
        is_primary=True,
    )
    user.current_organization = org
    user.save(update_fields=['current_organization'])

    bo = BusinessObject.objects.create(
        code='FALLBACKFIELDOBJ',
        name='Fallback Field Object',
        is_hardcoded=False,
    )
    FieldDefinition.objects.create(
        business_object=bo,
        code='asset_name',
        name='资产名称',
        field_type='text',
        show_in_form=True,
        show_in_detail=True,
    )

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(
        HTTP_X_ORGANIZATION_ID=str(org.id),
        HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9',
    )

    runtime_resp = client.get('/api/system/objects/FALLBACKFIELDOBJ/runtime/?mode=readonly')
    assert runtime_resp.status_code == 200
    assert runtime_resp.data['success'] is True

    editable_fields = _extract_editable_fields_from_response(runtime_resp.data)
    target_field = next((item for item in editable_fields if _field_code(item) == 'asset_name'), None)
    assert target_field is not None
    assert target_field.get('name') == '资产名称'
    assert target_field.get('name') != ''


@pytest.mark.django_db
def test_runtime_locale_query_param_overrides_header_and_profile():
    org = Organization.objects.create(name='Query Locale Org', code='query-locale-org')
    user = User.objects.create_user(
        username='query_locale_user',
        password='pass123456',
        organization=org,
        preferred_language='zh-CN',
    )
    UserOrganization.objects.create(
        user=user,
        organization=org,
        role='admin',
        is_active=True,
        is_primary=True,
    )
    user.current_organization = org
    user.save(update_fields=['current_organization'])

    bo = BusinessObject.objects.create(
        code='QUERYLOCALEOBJ',
        name='Query Locale Object',
        is_hardcoded=False,
    )
    FieldDefinition.objects.create(
        business_object=bo,
        code='asset_name',
        name='Asset Name',
        field_type='text',
        show_in_form=True,
    )

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(
        HTTP_X_ORGANIZATION_ID=str(org.id),
        HTTP_ACCEPT_LANGUAGE='zh-CN,zh;q=0.9',
    )

    runtime_resp = client.get('/api/system/objects/QUERYLOCALEOBJ/runtime/?mode=readonly&locale=en-US')
    assert runtime_resp.status_code == 200
    assert runtime_resp.data['success'] is True
    assert runtime_resp.data['data']['locale'] == 'en-US'
