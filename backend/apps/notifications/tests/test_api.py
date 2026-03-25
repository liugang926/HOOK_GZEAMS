"""
Tests for Notification API endpoints.

Tests all notification ViewSet endpoints including:
- List and retrieve notifications
- Mark as read/unread
- Bulk operations
- Unread count
"""
import pytest
from django.urls import reverse
from rest_framework import status
from apps.notifications.models import Notification, NotificationTemplate
from apps.accounts.models import User


@pytest.mark.django_db
class TestNotificationAPI:
    """Test Notification API endpoints."""

    def test_list_notifications(self, auth_client, notification):
        """Test listing notifications."""
        url = reverse('notification-list')
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'data' in response.data

    def test_retrieve_notification(self, auth_client, notification):
        """Test retrieving a single notification."""
        url = reverse('notification-detail', kwargs={'pk': notification.id})
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['id'] == str(notification.id)

    def test_mark_notification_as_read(self, auth_client, notification):
        """Test marking a notification as read."""
        url = reverse('notification-mark-read', kwargs={'pk': notification.id})
        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

        # Refresh and verify
        notification.refresh_from_db()
        assert notification.read_at is not None

    def test_mark_notification_as_unread(self, auth_client, notification):
        """Test marking a notification as unread."""
        # First mark as read
        notification.mark_as_read()

        url = reverse('notification-mark-unread', kwargs={'pk': notification.id})
        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

        # Refresh and verify
        notification.refresh_from_db()
        assert notification.read_at is None

    def test_mark_all_as_read(self, auth_client, user, organization):
        """Test marking all notifications as read."""
        # Create multiple notifications
        Notification.objects.create(
            organization=organization,
            recipient=user,
            notification_type='test',
            title='Test 1',
            content='Content 1',
            channel='inbox'
        )
        Notification.objects.create(
            organization=organization,
            recipient=user,
            notification_type='test',
            title='Test 2',
            content='Content 2',
            channel='inbox'
        )

        url = reverse('notification-mark-all-read')
        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['count'] == 2

    def test_unread_count(self, auth_client, user, organization):
        """Test getting unread notification count."""
        # Create notifications
        Notification.objects.create(
            organization=organization,
            recipient=user,
            notification_type='test',
            title='Test 1',
            content='Content 1',
            channel='inbox'
        )
        Notification.objects.create(
            organization=organization,
            recipient=user,
            notification_type='test',
            title='Test 2',
            content='Content 2',
            channel='inbox',
            read_at=timezone.now()
        )

        url = reverse('notification-unread-count')
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['count'] == 1

    def test_user_cannot_see_others_notifications(self, auth_client, other_user, organization):
        """Test that users can only see their own notifications."""
        # Create notification for other user
        Notification.objects.create(
            organization=organization,
            recipient=other_user,
            notification_type='test',
            title='Other User Notification',
            content='Content',
            channel='inbox'
        )

        url = reverse('notification-list')
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Should not contain the other user's notification
        assert not any(
            n['title'] == 'Other User Notification'
            for n in response.data['data']['results']
        )


@pytest.mark.django_db
class TestNotificationTemplateAPI:
    """Test NotificationTemplate API endpoints."""

    def test_list_templates(self, admin_client, notification_template):
        """Test listing notification templates."""
        url = reverse('notificationtemplate-list')
        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

    def test_create_template(self, admin_client, organization):
        """Test creating a notification template."""
        url = reverse('notificationtemplate-list')
        data = {
            'template_code': 'test_template',
            'template_name': 'Test Template',
            'template_type': 'test',
            'channel': 'inbox',
            'content_template': 'Test content: {{ var }}',
            'organization': str(organization.id)
        }
        response = admin_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert response.data['data']['template_code'] == 'test_template'

    def test_preview_template(self, admin_client, notification_template):
        """Test previewing a template."""
        url = reverse('notificationtemplate-preview', kwargs={'pk': notification_template.id})
        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

    def test_non_admin_cannot_delete_system_template(self, auth_client, notification_template):
        """Test that non-admin users cannot delete system templates."""
        notification_template.is_system = True
        notification_template.save()

        url = reverse('notificationtemplate-detail', kwargs={'pk': notification_template.id})
        response = auth_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
