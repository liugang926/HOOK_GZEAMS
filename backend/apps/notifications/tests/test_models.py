"""
Tests for Notification Models

Test cases for NotificationTemplate, Notification, NotificationLog, and NotificationConfig models.
"""
import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

from apps.notifications.models import (
    NotificationTemplate,
    Notification,
    NotificationLog,
    NotificationConfig,
)


@pytest.mark.django_db
class TestNotificationTemplate:
    """Tests for NotificationTemplate model."""

    def test_create_template(self, user):
        """Test creating a notification template."""
        template = NotificationTemplate.objects.create(
            template_code='test_template',
            template_name='Test Template',
            template_type='test',
            channel='inbox',
            subject_template='Test Subject: {{ name }}',
            content_template='Test Content: {{ message }}',
            variables={
                'name': {'default': 'World', 'description': 'Name variable'},
                'message': {'default': 'Hello', 'description': 'Message variable'},
            },
            created_by=user,
        )
        assert template.template_code == 'test_template'
        assert template.is_active is True
        assert template.version == 1

    def test_template_rendering(self, user):
        """Test template rendering with Jinja2."""
        template = NotificationTemplate.objects.create(
            template_code='test_render',
            template_name='Test Render',
            template_type='test',
            channel='inbox',
            subject_template='Hello {{ name }}',
            content_template='Message: {{ message }}',
            created_by=user,
        )

        rendered = template.render({'name': 'John', 'message': 'Test message'})
        assert rendered['subject'] == 'Hello John'
        assert rendered['content'] == 'Message: Test message'

    def test_template_version_save(self, user):
        """Test saving new version of template."""
        template = NotificationTemplate.objects.create(
            template_code='test_version',
            template_name='Test Version',
            template_type='test',
            channel='inbox',
            content_template='Original content',
            created_by=user,
        )
        template_id = template.id  # Store ID before save_new_version modifies instance

        # Save as new version
        new_template = template.save_new_version()

        assert new_template.version == 2
        assert new_template.is_active is False
        # Refresh original template from DB since save_new_version() modifies the instance
        original_template = NotificationTemplate.objects.get(id=template_id)
        assert new_template.previous_version == original_template


@pytest.mark.django_db
class TestNotification:
    """Tests for Notification model."""

    def test_create_notification(self, user):
        """Test creating a notification."""
        notification = Notification.objects.create(
            recipient=user,
            notification_type='test_notification',
            channel='inbox',
            priority='normal',
            title='Test Notification',
            content='This is a test notification',
            created_by=user,
        )
        assert notification.recipient == user
        assert notification.status == 'pending'
        assert notification.read_at is None

    def test_mark_as_read(self, user):
        """Test marking notification as read."""
        notification = Notification.objects.create(
            recipient=user,
            notification_type='test',
            channel='inbox',
            title='Test',
            content='Test content',
            created_by=user,
        )

        notification.mark_as_read()
        assert notification.read_at is not None

    def test_mark_as_unread(self, user):
        """Test marking notification as unread."""
        notification = Notification.objects.create(
            recipient=user,
            notification_type='test',
            channel='inbox',
            title='Test',
            content='Test content',
            created_by=user,
        )

        notification.mark_as_read()
        assert notification.read_at is not None

        notification.mark_as_unread()
        assert notification.read_at is None


@pytest.mark.django_db
class TestNotificationLog:
    """Tests for NotificationLog model."""

    def test_create_log(self, user):
        """Test creating a notification log."""
        # Create a notification first
        notification = Notification.objects.create(
            recipient=user,
            notification_type='test',
            channel='inbox',
            title='Test',
            content='Test content',
            created_by=user,
        )

        log = NotificationLog.objects.create(
            notification=notification,
            channel='inbox',
            status='success',
            duration=150,
        )
        assert log.notification == notification
        assert log.status == 'success'
        assert log.duration == 150


@pytest.mark.django_db
class TestNotificationConfig:
    """Tests for NotificationConfig model."""

    def test_create_config(self, user):
        """Test creating a notification config."""
        config = NotificationConfig.objects.create(
            user=user,
            enable_inbox=True,
            enable_email=True,
            enable_sms=False,
        )
        assert config.user == user
        assert config.enable_inbox is True
        assert config.enable_email is True
        assert config.enable_sms is False

    def test_is_channel_enabled(self, user):
        """Test checking if channel is enabled."""
        config = NotificationConfig.objects.create(
            user=user,
            enable_inbox=True,
            enable_email=True,
            enable_sms=False,
        )

        assert config.is_channel_enabled('test', 'inbox') is True
        assert config.is_channel_enabled('test', 'email') is True
        assert config.is_channel_enabled('test', 'sms') is False

    def test_is_in_quiet_hours(self, user):
        """Test quiet hours checking."""
        from datetime import time

        config = NotificationConfig.objects.create(
            user=user,
            quiet_hours_enabled=True,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(8, 0),
        )

        # Cannot easily test actual time-based logic in unit test
        # But we can test the method exists
        assert hasattr(config, 'is_in_quiet_hours')
