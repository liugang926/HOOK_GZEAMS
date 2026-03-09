import pytest
from django.core.cache import cache
from apps.common.middleware import clear_current_organization, set_current_organization
from apps.system.services.column_config_service import ColumnConfigService
from apps.system.models import UserColumnPreference, BusinessObject, FieldDefinition
from apps.accounts.models import User
from apps.organizations.models import Organization


@pytest.mark.django_db
class TestColumnConfigService:
    def test_get_column_config_returns_default_when_no_user_pref(self):
        """Test that default config is field-driven when user has no preference."""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)
        bo = BusinessObject.objects.create(code='asset', name='Asset', organization=org)

        FieldDefinition.objects.create(
            business_object=bo,
            code='code',
            name='Code',
            field_type='text',
            show_in_list=True,
            sort_order=1,
            organization=org,
        )
        FieldDefinition.objects.create(
            business_object=bo,
            code='name',
            name='Name',
            field_type='text',
            show_in_list=True,
            sort_order=2,
            organization=org,
        )

        config = ColumnConfigService.get_column_config(user, 'asset')

        assert 'columns' in config
        assert len(config['columns']) == 2
        assert config['source'] == 'default'

    def test_get_column_config_merges_user_preferences(self):
        """Test that user config overrides field-driven default columns."""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)
        bo = BusinessObject.objects.create(code='asset', name='Asset', organization=org)

        FieldDefinition.objects.create(
            business_object=bo,
            code='code',
            name='Code',
            field_type='text',
            show_in_list=True,
            sort_order=1,
            organization=org,
        )
        FieldDefinition.objects.create(
            business_object=bo,
            code='name',
            name='Name',
            field_type='text',
            show_in_list=True,
            sort_order=2,
            organization=org,
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
        assert pref.column_config['columns'][0]['field_code'] == 'code'
        assert pref.column_config['columnOrder'] == ['code']

    def test_save_user_config_normalizes_legacy_and_camel_case_keys(self):
        """Saved column configs should preserve order regardless of key style."""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)

        config = {
            'columns': [
                {'fieldCode': 'name', 'width': 260},
                {'field_code': 'code', 'visible': False}
            ],
            'column_order': ['name', 'code']
        }

        pref = ColumnConfigService.save_user_config(user, 'asset', config)

        assert pref.column_config['columnOrder'] == ['name', 'code']
        assert pref.column_config['columns'][0]['field_code'] == 'name'
        assert pref.column_config['columns'][1]['field_code'] == 'code'

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

    def test_get_column_config_preserves_saved_column_order(self):
        """Merged config should honor saved order after reload."""
        org = Organization.objects.create(name='Test Org', code='test-org')
        user = User.objects.create(username='testuser', organization=org)
        bo = BusinessObject.objects.create(code='asset', name='Asset', organization=org)

        FieldDefinition.objects.create(
            business_object=bo,
            code='code',
            name='Code',
            field_type='text',
            show_in_list=True,
            sort_order=1,
            organization=org,
        )
        FieldDefinition.objects.create(
            business_object=bo,
            code='name',
            name='Name',
            field_type='text',
            show_in_list=True,
            sort_order=2,
            organization=org,
        )

        UserColumnPreference.objects.create(
            user=user,
            object_code='asset',
            column_config={
                'columns': [
                    {'fieldCode': 'name', 'width': 260, 'visible': True},
                    {'field_code': 'code', 'visible': False}
                ],
                'column_order': ['name', 'code']
            },
            organization=org
        )

        cache.clear()
        config = ColumnConfigService.get_column_config(user, 'asset')

        assert [col['field_code'] for col in config['columns'][:2]] == ['name', 'code']
        assert config['columnOrder'] == ['name', 'code']

    def test_get_column_config_ignores_request_org_filter_for_saved_preference(self):
        """User column prefs should still load when request org differs from user.organization."""
        org = Organization.objects.create(name='Demo Org', code='demo-org')
        user = User.objects.create(username='admin-like-user', organization=None)
        bo = BusinessObject.objects.create(code='Asset', name='Asset', organization=org)

        FieldDefinition.objects.create(
            business_object=bo,
            code='asset_code',
            name='Asset Code',
            field_type='text',
            show_in_list=True,
            sort_order=1,
            organization=org,
        )
        FieldDefinition.objects.create(
            business_object=bo,
            code='asset_name',
            name='Asset Name',
            field_type='text',
            show_in_list=True,
            sort_order=2,
            organization=org,
        )

        ColumnConfigService.save_user_config(user, 'Asset', {
            'columns': [
                {'fieldCode': 'asset_name', 'visible': True},
                {'fieldCode': 'asset_code', 'visible': True},
            ],
            'columnOrder': ['asset_name', 'asset_code']
        })

        cache.clear()
        set_current_organization(str(org.id))
        try:
            config = ColumnConfigService.get_column_config(user, 'Asset')
        finally:
            clear_current_organization()

        assert config['source'] == 'user'
        assert config['columnOrder'][:2] == ['asset_name', 'asset_code']
        assert [col['field_code'] for col in config['columns'][:2]] == ['asset_name', 'asset_code']
