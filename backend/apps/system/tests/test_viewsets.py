import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.request import Request
from apps.system.viewsets import (
    UserColumnPreferenceViewSet,
    TabConfigViewSet
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
