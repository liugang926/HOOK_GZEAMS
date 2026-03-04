import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.test import APIClient
from rest_framework.request import Request
from apps.system.viewsets import (
    UserColumnPreferenceViewSet,
    TabConfigViewSet,
    BusinessObjectViewSet
)
from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.system.models import BusinessObject, UserColumnPreference, TabConfig, FieldDefinition
from apps.system.services.column_config_service import ColumnConfigService


@pytest.mark.django_db
class TestUserColumnPreferenceViewSet:
    def test_list_preferences_for_current_user(self):
        """Test listing preferences returns only current user's prefs"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user1 = User.objects.create(username='user1', organization=org)
        user2 = User.objects.create(username='user2', organization=org)

        # Create preferences for both users
        UserColumnPreference.objects.create(
            user=user1,
            object_code='asset',
            column_config={},
            organization=org
        )
        UserColumnPreference.objects.create(
            user=user2,
            object_code='asset',
            column_config={},
            organization=org
        )

        # List as user1 - should only see user1's prefs
        factory = APIRequestFactory()
        wsgi_request = factory.get('/api/column-preferences/')
        force_authenticate(wsgi_request, user=user1)
        # Convert to DRF Request to properly set user attribute
        request = Request(wsgi_request)
        request.organization_id = org.id

        viewset = UserColumnPreferenceViewSet()
        viewset.request = request
        viewset.format_kwarg = None

        queryset = viewset.get_queryset()
        assert queryset.count() == 1
        assert queryset.first().user == user1

    def test_upsert_creates_new_preference(self):
        """Test upsert action creates new preference via service"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        column_config = {
            'columns': [
                {'field_code': 'code', 'visible': True}
            ],
            'columnOrder': ['code']
        }

        # Use service directly to test functionality
        pref = ColumnConfigService.save_user_config(user, 'asset', column_config)

        assert pref.user == user
        assert pref.object_code == 'asset'
        assert pref.column_config['columns'][0]['field_code'] == 'code'

    def test_reset_deletes_user_preference(self):
        """Test reset action deletes user preference via service"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        # Create preference
        ColumnConfigService.save_user_config(
            user,
            'asset',
            {'columns': [], 'columnOrder': []}
        )

        # Verify it exists
        assert UserColumnPreference.objects.filter(
            user=user,
            object_code='asset'
        ).exists()

        # Reset via service
        result = ColumnConfigService.reset_user_config(user, 'asset')

        assert result is True
        assert not UserColumnPreference.objects.filter(
            user=user,
            object_code='asset'
        ).exists()


@pytest.mark.django_db
class TestTabConfigViewSet:
    def test_list_tab_configs(self):
        """Test listing tab configurations"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)
        bo = BusinessObject.objects.create(code='asset', name='Asset', organization=org)

        TabConfig.objects.create(
            business_object=bo,
            name='form_tabs',
            organization=org
        )
        TabConfig.objects.create(
            business_object=bo,
            name='detail_tabs',
            organization=org
        )

        factory = APIRequestFactory()
        wsgi_request = factory.get('/api/tab-configs/')
        force_authenticate(wsgi_request, user=user)
        request = Request(wsgi_request)
        request.organization_id = org.id

        viewset = TabConfigViewSet()
        viewset.request = request
        viewset.format_kwarg = None

        queryset = viewset.get_queryset()
        assert queryset.count() == 2

    def test_by_object_action(self):
        """Test getting tab configs by business object"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)
        bo = BusinessObject.objects.create(code='asset', name='Asset', organization=org)

        TabConfig.objects.create(
            business_object=bo,
            name='form_tabs',
            position='top',
            organization=org
        )

        factory = APIRequestFactory()
        wsgi_request = factory.get(f'/api/tab-configs/by-object/asset/')
        force_authenticate(wsgi_request, user=user)
        request = Request(wsgi_request)
        request.organization_id = org.id

        viewset = TabConfigViewSet()
        viewset.request = request
        viewset.format_kwarg = None
        viewset.action = 'by_object'

        response = viewset.by_object(request, object_code='asset')
        assert response.status_code == 200
        assert response.data['success'] is True
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['name'] == 'form_tabs'


@pytest.mark.django_db
class TestBusinessObjectViewSetFieldTypes:
    """
    Test cases for the field_types action endpoint.

    Verifies that the frontend can dynamically fetch field type definitions
    to keep the field type selector in sync with backend capabilities.
    """

    def test_field_types_returns_success(self):
        """Test field_types endpoint returns success response"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        factory = APIRequestFactory()
        wsgi_request = factory.get('/api/system/business-objects/field-types/')
        force_authenticate(wsgi_request, user=user)
        request = Request(wsgi_request)
        request.organization_id = org.id

        viewset = BusinessObjectViewSet()
        viewset.request = request
        viewset.format_kwarg = None
        viewset.action = 'field_types'

        response = viewset.field_types(request)
        assert response.status_code == 200
        assert response.data['success'] is True

    def test_field_types_contains_groups(self):
        """Test field_types returns grouped field types"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        factory = APIRequestFactory()
        wsgi_request = factory.get('/api/system/business-objects/field-types/')
        force_authenticate(wsgi_request, user=user)
        request = Request(wsgi_request)
        request.organization_id = org.id

        viewset = BusinessObjectViewSet()
        viewset.request = request
        viewset.format_kwarg = None
        viewset.action = 'field_types'

        response = viewset.field_types(request)
        groups = response.data['data']['groups']

        # Should have at least the 6 defined groups
        assert len(groups) >= 6
        group_labels = [g['label'] for g in groups]
        assert '基础类型' in group_labels
        assert '日期时间' in group_labels
        assert '选择类型' in group_labels
        assert '引用类型' in group_labels
        assert '媒体文件' in group_labels
        assert '高级类型' in group_labels

    def test_field_types_contains_all_required_types(self):
        """Test that all important field types are included"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        factory = APIRequestFactory()
        wsgi_request = factory.get('/api/system/business-objects/field-types/')
        force_authenticate(wsgi_request, user=user)
        request = Request(wsgi_request)
        request.organization_id = org.id

        viewset = BusinessObjectViewSet()
        viewset.request = request
        viewset.format_kwarg = None
        viewset.action = 'field_types'

        response = viewset.field_types(request)
        all_types = response.data['data']['all_types']

        # Verify key field types that were missing in the original form
        assert 'file' in all_types
        assert 'image' in all_types
        assert 'qr_code' in all_types
        assert 'barcode' in all_types
        assert 'location' in all_types
        assert 'percent' in all_types
        assert 'time' in all_types
        assert 'rich_text' in all_types

    def test_field_types_has_type_config(self):
        """Test that each field type has component configuration"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        factory = APIRequestFactory()
        wsgi_request = factory.get('/api/system/business-objects/field-types/')
        force_authenticate(wsgi_request, user=user)
        request = Request(wsgi_request)
        request.organization_id = org.id

        viewset = BusinessObjectViewSet()
        viewset.request = request
        viewset.format_kwarg = None
        viewset.action = 'field_types'

        response = viewset.field_types(request)
        type_config = response.data['data']['type_config']

        # Check that important types have component mappings
        assert 'file' in type_config
        assert type_config['file']['component'] == 'AttachmentUpload'
        assert 'image' in type_config
        assert type_config['image']['component'] == 'ImageField'
        assert 'qr_code' in type_config
        assert type_config['qr_code']['component'] == 'QRCodeField'
        assert 'barcode' in type_config
        assert type_config['barcode']['component'] == 'BarcodeField'

    def test_field_types_matches_model_choices(self):
        """Test that API types match the model FIELD_TYPE_CHOICES"""
        from apps.system.models import FieldDefinition

        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        factory = APIRequestFactory()
        wsgi_request = factory.get('/api/system/business-objects/field-types/')
        force_authenticate(wsgi_request, user=user)
        request = Request(wsgi_request)
        request.organization_id = org.id

        viewset = BusinessObjectViewSet()
        viewset.request = request
        viewset.format_kwarg = None
        viewset.action = 'field_types'

        response = viewset.field_types(request)
        api_types = set(response.data['data']['all_types'])
        model_types = set(value for value, _ in FieldDefinition.FIELD_TYPE_CHOICES)

        # All model types should be in API response
        assert model_types.issubset(api_types)


@pytest.mark.django_db
class TestBusinessObjectFieldsFiltering:
    def test_hardcoded_fields_exclude_relations_by_default(self):
        org = Organization.objects.create(name='Field Filter Org', code='field-filter-org')
        user = User.objects.create(username='field_filter_user', organization=org)
        BusinessObject.objects.get_or_create(
            code='Asset',
            defaults={'name': 'Asset', 'is_hardcoded': True},
        )

        factory = APIRequestFactory()
        wsgi_request = factory.get('/api/system/business-objects/fields/?object_code=Asset')
        force_authenticate(wsgi_request, user=user)
        request = Request(wsgi_request)
        request.organization_id = org.id

        viewset = BusinessObjectViewSet()
        viewset.request = request
        viewset.format_kwarg = None
        viewset.action = 'fields'

        response = viewset.fields(request)
        assert response.status_code == 200
        assert response.data['success'] is True

        fields = response.data['data']['fields']
        assert isinstance(fields, list)
        assert not any(bool(item.get('isReverseRelation')) for item in fields)
        assert not any(str(item.get('fieldName', '')).endswith('_items') for item in fields)
        assert not any(str(item.get('fieldName', '')).endswith('_logs') for item in fields)

    def test_hardcoded_fields_include_relations_when_requested(self):
        org = Organization.objects.create(name='Field Relation Org', code='field-relation-org')
        user = User.objects.create(username='field_relation_user', organization=org)
        BusinessObject.objects.get_or_create(
            code='Asset',
            defaults={'name': 'Asset', 'is_hardcoded': True},
        )

        factory = APIRequestFactory()
        wsgi_request = factory.get('/api/system/business-objects/fields/?object_code=Asset&include_relations=true')
        force_authenticate(wsgi_request, user=user)
        request = Request(wsgi_request)
        request.organization_id = org.id

        viewset = BusinessObjectViewSet()
        viewset.request = request
        viewset.format_kwarg = None
        viewset.action = 'fields'

        response = viewset.fields(request)
        assert response.status_code == 200
        assert response.data['success'] is True

        fields = response.data['data']['fields']
        assert isinstance(fields, list)
        assert any(bool(item.get('isReverseRelation')) for item in fields)


@pytest.mark.django_db
class TestFieldDefinitionSystemGuard:
    def test_system_field_cannot_be_updated_or_deleted(self):
        org = Organization.objects.create(name='System Guard Org', code='system-guard-org')
        user = User.objects.create(username='system_guard_user', organization=org)
        bo = BusinessObject.objects.create(code='SYS_GUARD_OBJ', name='System Guard Object', is_hardcoded=False)
        fd = FieldDefinition.objects.create(
            business_object=bo,
            code='asset_code',
            name='Asset Code',
            field_type='text',
            is_system=True,
            show_in_form=True,
        )

        client = APIClient()
        client.force_authenticate(user=user)
        client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

        patch_resp = client.patch(
            f'/api/system/field-definitions/{fd.id}/',
            {'name': 'Asset Code Updated'},
            format='json',
        )
        assert patch_resp.status_code == 403
        assert patch_resp.data['success'] is False
        assert patch_resp.data['error']['code'] == 'READONLY_SYSTEM_FIELD'

        delete_resp = client.delete(f'/api/system/field-definitions/{fd.id}/')
        assert delete_resp.status_code == 403
        assert delete_resp.data['success'] is False
        assert delete_resp.data['error']['code'] == 'READONLY_SYSTEM_FIELD'

    def test_builtin_system_code_cannot_be_updated_even_when_flag_is_false(self):
        org = Organization.objects.create(name='System Code Org', code='system-code-org')
        user = User.objects.create(username='system_code_user', organization=org)
        bo = BusinessObject.objects.create(code='SYS_CODE_OBJ', name='System Code Object', is_hardcoded=False)
        fd = FieldDefinition.objects.create(
            business_object=bo,
            code='updated_at',
            name='Updated At',
            field_type='datetime',
            is_system=False,
            show_in_form=True,
        )

        client = APIClient()
        client.force_authenticate(user=user)
        client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

        patch_resp = client.patch(
            f'/api/system/field-definitions/{fd.id}/',
            {'name': 'Updated At Custom'},
            format='json',
        )
        assert patch_resp.status_code == 403
        assert patch_resp.data['success'] is False
        assert patch_resp.data['error']['code'] == 'READONLY_SYSTEM_FIELD'

    def test_cannot_create_field_with_system_flag(self):
        org = Organization.objects.create(name='Create Guard Org', code='create-guard-org')
        user = User.objects.create(username='create_guard_user', organization=org)
        bo = BusinessObject.objects.create(code='SYS_CREATE_OBJ', name='System Create Object', is_hardcoded=False)

        client = APIClient()
        client.force_authenticate(user=user)
        client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

        create_resp = client.post(
            '/api/system/field-definitions/',
            {
                'business_object': str(bo.id),
                'code': 'blocked_system_field',
                'name': 'Blocked System Field',
                'field_type': 'text',
                'is_system': True,
            },
            format='json',
        )
        assert create_resp.status_code == 400
        assert create_resp.data['success'] is False
        assert create_resp.data['error']['code'] == 'INVALID_OPERATION'
