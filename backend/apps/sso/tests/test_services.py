"""
Tests for SSO Services

Test cases for SSO services.
"""
import pytest
from unittest.mock import Mock, patch
from apps.sso.services.sso_service import (
    SSOService,
    WeWorkConfigService,
    UserMappingService,
)
from apps.sso.models import WeWorkConfig, UserMapping, OAuthState


@pytest.mark.django_db
class TestSSOService:
    """Tests for SSOService base class."""

    def test_generate_state(self):
        """Test state generation."""
        state1 = SSOService.generate_state()
        state2 = SSOService.generate_state()
        assert state1 != state2
        assert len(state1) > 20

    def test_create_oauth_state(self, organization):
        """Test OAuth state creation."""
        state = SSOService.create_oauth_state('wework', {'test': 'data'})
        assert state is not None
        assert len(state) > 20

        # Verify state was created in DB
        oauth_state = OAuthState.objects.get(state=state)
        assert oauth_state.platform == 'wework'
        assert oauth_state.session_data == {'test': 'data'}

    def test_validate_and_consume_state(self, organization):
        """Test state validation and consumption."""
        # Create a state
        state = SSOService.create_oauth_state('wework', {'test': 'data'})

        # Validate and consume
        result = SSOService.validate_and_consume_state(state, 'wework')
        assert result == {'test': 'data'}

        # Second consume should return empty dict
        result = SSOService.validate_and_consume_state(state, 'wework')
        assert result == {}


@pytest.mark.django_db
class TestWeWorkConfigService:
    """Tests for WeWorkConfigService."""

    def test_get_config_by_corp_id(self, organization):
        """Test getting config by corp ID."""
        config = WeWorkConfig.objects.create(
            organization=organization,
            corp_id='ww123456789',
            corp_name='Test Corp',
            agent_id=1000001,
            agent_secret='test_secret'
        )

        service = WeWorkConfigService()
        result = service.get_config_by_corp_id('ww123456789')
        assert result is not None
        assert result.corp_id == 'ww123456789'

    def test_get_config_by_corp_id_not_found(self, organization):
        """Test getting non-existent config by corp ID."""
        service = WeWorkConfigService()
        result = service.get_config_by_corp_id('nonexistent')
        assert result is None


@pytest.mark.django_db
class TestUserMappingService:
    """Tests for UserMappingService."""

    def test_create_mapping(self, user, organization):
        """Test creating a user mapping."""
        service = UserMappingService()
        mapping = service.create_or_update_mapping(
            user=user,
            platform='wework',
            platform_userid='USER123',
            platform_name='Test User'
        )

        assert mapping.platform == 'wework'
        assert mapping.platform_userid == 'USER123'
        assert mapping.platform_name == 'Test User'

    def test_update_mapping(self, user, organization):
        """Test updating an existing mapping."""
        service = UserMappingService()
        mapping = service.create_or_update_mapping(
            user=user,
            platform='wework',
            platform_userid='USER123',
            platform_name='Test User'
        )

        # Update the mapping
        updated = service.create_or_update_mapping(
            user=user,
            platform='wework',
            platform_userid='USER456',
            platform_name='Updated Name'
        )

        assert updated.id == mapping.id
        assert updated.platform_userid == 'USER456'
        assert updated.platform_name == 'Updated Name'

    def test_get_by_platform_userid(self, user, organization):
        """Test getting mapping by platform user ID."""
        UserMapping.objects.create(
            organization=organization,
            system_user=user,
            platform='wework',
            platform_userid='USER123',
            platform_name='Test User'
        )

        service = UserMappingService()
        result = service.get_by_platform_userid('wework', 'USER123')
        assert result is not None
        assert result.platform_userid == 'USER123'

    def test_get_user_mappings(self, user, organization):
        """Test getting all mappings for a user."""
        UserMapping.objects.create(
            organization=organization,
            system_user=user,
            platform='wework',
            platform_userid='USER123',
            platform_name='Test User'
        )
        UserMapping.objects.create(
            organization=organization,
            system_user=user,
            platform='dingtalk',
            platform_userid='DT123',
            platform_name='Test DT'
        )

        service = UserMappingService()
        mappings = service.get_user_mappings(str(user.id))

        assert 'wework' in mappings
        assert 'dingtalk' in mappings
        assert mappings['wework'].platform_userid == 'USER123'
        assert mappings['dingtalk'].platform_userid == 'DT123'
