import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.request import Request
from apps.system.viewsets import (
    UserColumnPreferenceViewSet,
    TabConfigViewSet,
    BusinessObjectViewSet
)
from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.system.models import BusinessObject, UserColumnPreference, TabConfig
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
