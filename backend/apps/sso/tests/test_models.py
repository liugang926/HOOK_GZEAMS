"""
Tests for SSO Models

Test cases for WeWorkConfig, UserMapping, and OAuthState models.
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from apps.sso.models import WeWorkConfig, UserMapping, OAuthState


@pytest.mark.django_db
class TestWeWorkConfig:
    """Tests for WeWorkConfig model."""

    def test_create_config(self, organization):
        """Test creating a WeWork configuration."""
        config = WeWorkConfig.objects.create(
            organization=organization,
            corp_id='ww123456789',
            corp_name='Test Corp',
            agent_id=1000001,
            agent_secret='test_secret',
            is_enabled=True
        )
        assert config.corp_id == 'ww123456789'
        assert config.corp_name == 'Test Corp'
        assert config.agent_id == 1000001
        assert config.is_enabled is True

    def test_config_str(self, organization):
        """Test string representation of config."""
        config = WeWorkConfig.objects.create(
            organization=organization,
            corp_id='ww123456789',
            corp_name='Test Corp',
            agent_id=1000001,
            agent_secret='test_secret'
        )
        assert str(config) == 'Test Corp (ww123456789)'


@pytest.mark.django_db
class TestUserMapping:
    """Tests for UserMapping model."""

    def test_create_mapping(self, user, organization):
        """Test creating a user mapping."""
        mapping = UserMapping.objects.create(
            organization=organization,
            system_user=user,
            platform='wework',
            platform_userid='USER123',
            platform_name='Test User'
        )
        assert mapping.system_user == user
        assert mapping.platform == 'wework'
        assert mapping.platform_userid == 'USER123'
        assert mapping.platform_name == 'Test User'

    def test_mapping_str(self, user, organization):
        """Test string representation of mapping."""
        mapping = UserMapping.objects.create(
            organization=organization,
            system_user=user,
            platform='wework',
            platform_userid='USER123',
            platform_name='Test User'
        )
        assert 'testuser' in str(mapping)
        assert 'WeWork' in str(mapping)


@pytest.mark.django_db
class TestOAuthState:
    """Tests for OAuthState model."""

    def test_create_state(self, organization):
        """Test creating an OAuth state."""
        state = OAuthState.objects.create(
            organization=organization,
            state='test_state_token',
            platform='wework',
            session_data={'test': 'data'},
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        assert state.state == 'test_state_token'
        assert state.platform == 'wework'
        assert state.session_data == {'test': 'data'}
        assert state.consumed is False

    def test_state_is_valid(self, organization):
        """Test state validation."""
        # Valid state
        state = OAuthState.objects.create(
            organization=organization,
            state='test_state_token',
            platform='wework',
            session_data={'test': 'data'},
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        assert state.is_valid() is True

        # Consumed state
        state.consumed = True
        state.save()
        assert state.is_valid() is False

    def test_state_consume(self, organization):
        """Test state consumption."""
        state = OAuthState.objects.create(
            organization=organization,
            state='test_state_token',
            platform='wework',
            session_data={'test': 'data'},
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        # First consume should return data
        result = state.consume_instance()
        assert result == {'test': 'data'}

        # Refresh from DB
        state.refresh_from_db()
        assert state.consumed is True
        assert state.consumed_at is not None

        # Second consume should return None
        result = state.consume_instance()
        assert result is None

    def test_expired_state(self, organization):
        """Test expired state validation."""
        state = OAuthState.objects.create(
            organization=organization,
            state='test_state_token',
            platform='wework',
            session_data={'test': 'data'},
            expires_at=timezone.now() - timedelta(minutes=1)  # Expired
        )
        assert state.is_valid() is False

    def test_consume_class_method(self, organization):
        """Test OAuthState.consume() class method."""
        OAuthState.objects.create(
            organization=organization,
            state='test_state_token',
            platform='wework',
            session_data={'test': 'data'},
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        # Valid consume
        result = OAuthState.consume('test_state_token', 'wework')
        assert result == {'test': 'data'}

        # Second consume should return None
        result = OAuthState.consume('test_state_token', 'wework')
        assert result is None

        # Non-existent state
        result = OAuthState.consume('invalid_state', 'wework')
        assert result is None
