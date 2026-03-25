import pytest
from apps.system.serializers import (
    UserColumnPreferenceSerializer,
    UserColumnPreferenceListSerializer,
    TabConfigSerializer,
    TabConfigListSerializer
)
from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.system.models import BusinessObject, UserColumnPreference, TabConfig


@pytest.mark.django_db
class TestUserColumnPreferenceSerializer:
    def test_serialize_column_preference(self):
        """Test serializing a user column preference"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        pref = UserColumnPreference.objects.create(
            user=user,
            object_code='asset',
            column_config={
                'columns': [
                    {'field_code': 'code', 'visible': True, 'width': 120},
                    {'field_code': 'name', 'visible': True, 'width': 200}
                ],
                'columnOrder': ['code', 'name']
            },
            config_name='default',
            is_default=True,
            organization=org
        )

        serializer = UserColumnPreferenceSerializer(pref)
        data = serializer.data

        assert data['object_code'] == 'asset'
        assert data['config_name'] == 'default'
        assert data['is_default'] is True
        assert 'columns' in data['column_config']
        assert len(data['column_config']['columns']) == 2

    def test_create_column_preference(self):
        """Test creating a column preference via serializer"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        data = {
            'user': user.id,
            'object_code': 'asset',
            'column_config': {
                'columns': [
                    {'field_code': 'code', 'visible': True}
                ]
            },
            'config_name': 'my_config',
            'organization': org.id
        }

        serializer = UserColumnPreferenceSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        pref = serializer.save()

        assert pref.object_code == 'asset'
        assert pref.config_name == 'my_config'

    def test_validate_column_config(self):
        """Test column_config validation"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        # Invalid column_config (not a dict)
        data = {
            'user': user.id,
            'object_code': 'asset',
            'column_config': 'invalid',
            'organization': org.id
        }

        serializer = UserColumnPreferenceSerializer(data=data)
        assert not serializer.is_valid()
        assert 'column_config' in serializer.errors


@pytest.mark.django_db
class TestTabConfigSerializer:
    def test_serialize_tab_config(self):
        """Test serializing a tab configuration"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        bo = BusinessObject.objects.create(
            code='asset',
            name='Asset',
            organization=org
        )

        tab_config = TabConfig.objects.create(
            business_object=bo,
            name='form_tabs',
            position='top',
            type_style='card',
            lazy=True,
            animated=True,
            tabs_config=[
                {
                    'id': 'basic',
                    'title': 'Basic Info',
                    'icon': 'document',
                    'closable': False,
                    'content': []
                }
            ],
            organization=org
        )

        serializer = TabConfigSerializer(tab_config)
        data = serializer.data

        assert data['name'] == 'form_tabs'
        assert data['position'] == 'top'
        assert data['type_style'] == 'card'
        assert data['lazy'] is True
        assert len(data['tabs_config']) == 1

    def test_create_tab_config(self):
        """Test creating a tab config via serializer"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        bo = BusinessObject.objects.create(
            code='asset',
            name='Asset',
            organization=org
        )

        data = {
            'business_object': bo.id,
            'name': 'detail_tabs',
            'position': 'left',
            'tabs_config': [
                {'id': 'info', 'title': 'Info'}
            ],
            'organization': org.id
        }

        serializer = TabConfigSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        tab = serializer.save()

        assert tab.name == 'detail_tabs'
        assert tab.position == 'left'

    def test_validate_tabs_config(self):
        """Test tabs_config validation"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        bo = BusinessObject.objects.create(
            code='asset',
            name='Asset',
            organization=org
        )

        # Invalid tabs_config (not a list)
        data = {
            'business_object': bo.id,
            'name': 'form_tabs',
            'tabs_config': 'invalid',
            'organization': org.id
        }

        serializer = TabConfigSerializer(data=data)
        assert not serializer.is_valid()
        assert 'tabs_config' in serializer.errors
