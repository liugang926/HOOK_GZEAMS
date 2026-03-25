import pytest
from django.core.exceptions import ValidationError
from apps.system.models import UserColumnPreference, TabConfig
from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.system.models import BusinessObject


@pytest.mark.django_db
class TestUserColumnPreference:
    def test_create_column_preference(self):
        """Test creating a user column preference"""
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

        assert pref.user == user
        assert pref.object_code == 'asset'
        assert pref.is_default is True

    def test_unique_constraint(self):
        """Test that user+object_code+config_name is unique"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        UserColumnPreference.objects.create(
            user=user,
            object_code='asset',
            column_config={},
            config_name='default',
            organization=org
        )

        # Should raise error on duplicate
        with pytest.raises(ValidationError):
            pref2 = UserColumnPreference(
                user=user,
                object_code='asset',
                column_config={},
                config_name='default',
                organization=org
            )
            pref2.full_clean()

    def test_multiple_configs_per_user(self):
        """Test that user can have multiple configs for different objects"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        UserColumnPreference.objects.create(
            user=user,
            object_code='asset',
            column_config={},
            config_name='default',
            organization=org
        )

        UserColumnPreference.objects.create(
            user=user,
            object_code='procurement',
            column_config={},
            config_name='default',
            organization=org
        )

        assert UserColumnPreference.objects.filter(user=user).count() == 2


@pytest.mark.django_db
class TestTabConfig:
    def test_create_tab_config(self):
        """Test creating a tab configuration"""
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
            tabs_config=[
                {'id': 'basic', 'title': 'Basic Info', 'content': []}
            ],
            organization=org
        )

        assert tab_config.business_object == bo
        assert tab_config.name == 'form_tabs'
        assert tab_config.position == 'top'
        assert len(tab_config.tabs_config) == 1

    def test_tab_config_default_values(self):
        """Test default values for tab config options"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        bo = BusinessObject.objects.create(
            code='asset',
            name='Asset',
            organization=org
        )

        tab_config = TabConfig.objects.create(
            business_object=bo,
            name='form_tabs',
            organization=org
        )

        assert tab_config.position == 'top'
        assert tab_config.type_style == ''
        assert tab_config.stretch is False
        assert tab_config.lazy is True
        assert tab_config.animated is True
        assert tab_config.addable is False
        assert tab_config.draggable is False
        assert tab_config.is_active is True
