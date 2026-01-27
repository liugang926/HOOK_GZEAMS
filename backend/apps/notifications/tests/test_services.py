"""
Tests for Notification Services

Test cases for NotificationService and TemplateService.
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

from apps.notifications.models import (
    NotificationTemplate,
    Notification,
    NotificationConfig,
)
from apps.notifications.services import (
    notification_service,
    template_service,
)
from apps.notifications.channels import (
    get_channel,
    get_supported_channels,
    NotificationMessage,
    ChannelStatus,
)


@pytest.mark.django_db
class TestTemplateService:
    """Tests for TemplateService."""

    def test_get_template(self, user):
        """Test getting a template by code and channel."""
        template = NotificationTemplate.objects.create(
            template_code='test_template',
            template_name='Test Template',
            template_type='test',
            channel='inbox',
            subject_template='Test',
            content_template='Content',
            created_by=user,
        )

        retrieved = template_service.get_template('test_template', 'inbox')
        assert retrieved is not None
        assert retrieved.template_code == 'test_template'

    def test_render_template(self, user):
        """Test rendering a template with variables."""
        NotificationTemplate.objects.create(
            template_code='test_render',
            template_name='Test Render',
            template_type='test',
            channel='inbox',
            subject_template='Hello {{ name }}',
            content_template='Message: {{ message }}',
            variables={
                'name': {'default': 'World'},
                'message': {'default': 'Test'},
            },
            created_by=user,
        )

        rendered = template_service.render_template(
            'test_render',
            'inbox',
            {'name': 'John', 'message': 'Custom message'}
        )

        assert rendered is not None
        assert rendered['subject'] == 'Hello John'
        assert rendered['content'] == 'Message: Custom message'


@pytest.mark.django_db
class TestNotificationService:
    """Tests for NotificationService."""

    def test_send_notification(self, user):
        """Test sending a notification."""
        # Create a template
        NotificationTemplate.objects.create(
            template_code='test_notification',
            template_name='Test',
            template_type='test',
            channel='inbox',
            subject_template='Test Subject',
            content_template='Test Content',
            created_by=user,
        )

        # Create user config
        NotificationConfig.objects.create(
            user=user,
            enable_inbox=True,
        )

        result = notification_service.send(
            recipient=user,
            notification_type='test_notification',
            variables={},
            channels=['inbox'],
        )

        assert result is not None
        assert 'success' in result
        assert 'results' in result

    def test_mark_as_read(self, user):
        """Test marking notification as read."""
        notification = Notification.objects.create(
            recipient=user,
            notification_type='test',
            channel='inbox',
            title='Test',
            content='Content',
            created_by=user,
        )

        result = notification_service.mark_as_read(str(notification.id), user)
        assert result is True

        notification.refresh_from_db()
        assert notification.read_at is not None

    def test_mark_all_as_read(self, user):
        """Test marking all notifications as read."""
        Notification.objects.create(
            recipient=user,
            notification_type='test',
            channel='inbox',
            title='Test1',
            content='Content1',
            created_by=user,
        )
        Notification.objects.create(
            recipient=user,
            notification_type='test',
            channel='inbox',
            title='Test2',
            content='Content2',
            created_by=user,
        )

        count = notification_service.mark_all_as_read(user)
        assert count == 2

    def test_get_unread_count(self, user):
        """Test getting unread count."""
        Notification.objects.create(
            recipient=user,
            notification_type='test',
            channel='inbox',
            title='Test',
            content='Content',
            created_by=user,
        )

        count = notification_service.get_unread_count(user)
        assert count == 1


@pytest.mark.django_db
class TestChannelAdapters:
    """Tests for channel adapters."""

    def test_get_supported_channels(self):
        """Test getting supported channels."""
        channels = get_supported_channels()
        assert 'inbox' in channels
        assert 'email' in channels
        assert 'sms' in channels

    def test_get_channel(self):
        """Test getting channel adapter."""
        inbox_channel = get_channel('inbox')
        assert inbox_channel is not None
        assert inbox_channel.channel_type == 'inbox'

    def test_inbox_channel_validate_recipient(self, user):
        """Test inbox channel recipient validation."""
        inbox_channel = get_channel('inbox')
        assert inbox_channel.validate_recipient(str(user.id)) is True
        assert inbox_channel.validate_recipient('invalid-uuid') is False

    def test_notification_message_creation(self):
        """Test creating a NotificationMessage."""
        message = NotificationMessage(
            recipient='test-recipient',
            subject='Test Subject',
            content='Test Content',
            data={'key': 'value'},
            priority='high',
        )
        assert message.recipient == 'test-recipient'
        assert message.subject == 'Test Subject'
        assert message.content == 'Test Content'
        assert message.priority == 'high'
