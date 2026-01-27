import pytest
from django.core.cache import cache
from apps.system.services.column_config_service import ColumnConfigService
from apps.system.models import UserColumnPreference, PageLayout, BusinessObject
from apps.accounts.models import User
from apps.organizations.models import Organization


@pytest.mark.django_db
class TestColumnConfigService:
    def test_get_column_config_returns_default_when_no_user_pref(self):
        """Test that default config is returned when user has no preference"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)
        bo = BusinessObject.objects.create(code='asset', name='Asset', organization=org)

        # Create default layout
        PageLayout.objects.create(
            business_object=bo,
            layout_code='asset_list_default',
            layout_name='Asset List Default',
            layout_type='list',
            is_default=True,
            layout_config={
                'columns': [
                    {'field_code': 'code', 'label': '编号', 'width': 120, 'visible': True},
                    {'field_code': 'name', 'label': '名称', 'width': 200, 'visible': True}
                ]
            },
            organization=org
        )

        config = ColumnConfigService.get_column_config(user, 'asset')

        assert 'columns' in config
        assert len(config['columns']) == 2
        assert config['source'] == 'default'

    def test_get_column_config_merges_user_preferences(self):
        """Test that user config overrides default"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)
        bo = BusinessObject.objects.create(code='asset', name='Asset', organization=org)

        # Create default layout
        PageLayout.objects.create(
            business_object=bo,
            layout_code='asset_list_default',
            layout_name='Asset List Default',
            layout_type='list',
            is_default=True,
            layout_config={
                'columns': [
                    {'field_code': 'code', 'label': '编号', 'width': 120, 'visible': True},
                    {'field_code': 'name', 'label': '名称', 'width': 200, 'visible': True}
                ]
            },
            organization=org
        )

        # Create user preference (hide 'code', change 'name' width)
        UserColumnPreference.objects.create(
            user=user,
            object_code='asset',
            column_config={
                'columns': [
                    {'field_code': 'code', 'visible': False},
                    {'field_code': 'name', 'width': 300}
                ]
            },
            organization=org
        )

        config = ColumnConfigService.get_column_config(user, 'asset')

        # User preference should override
        name_col = next(c for c in config['columns'] if c['field_code'] == 'name')
        assert name_col['width'] == 300
        code_col = next(c for c in config['columns'] if c['field_code'] == 'code')
        assert code_col['visible'] is False
        assert config['source'] == 'user'

    def test_save_user_config(self):
        """Test saving user configuration"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        config = {
            'columns': [
                {'field_code': 'code', 'width': 150}
            ]
        }

        pref = ColumnConfigService.save_user_config(user, 'asset', config)

        assert pref.user == user
        assert pref.object_code == 'asset'
        assert pref.column_config == config

    def test_reset_user_config(self):
        """Test resetting user configuration"""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        UserColumnPreference.objects.create(
            user=user,
            object_code='asset',
            column_config={'columns': []},
            organization=org
        )

        result = ColumnConfigService.reset_user_config(user, 'asset')

        assert result is True
        assert UserColumnPreference.objects.filter(user=user, object_code='asset').count() == 0
