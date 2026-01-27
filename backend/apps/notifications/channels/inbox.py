"""
Inbox Channel Adapter

Handles internal inbox notifications stored in the database.
This is the default channel for all system notifications.
"""
import time
from typing import Optional
from django.utils import timezone
from django.contrib.auth import get_user_model
from .base import (
    NotificationChannel,
    NotificationMessage,
    SendResult,
    ChannelStatus,
    NonRetryableError,
)

User = get_user_model()


class InboxChannel(NotificationChannel):
    """
    Inbox notification channel.

    Stores notifications directly in the database for users to view
    in their inbox. This is the most reliable channel as it doesn't
    depend on external services.
    """

    channel_type = "inbox"
    channel_name = "Inbox"

    def validate_recipient(self, recipient: str) -> bool:
        """
        Validate recipient is a valid user ID.

        Args:
            recipient: User UUID string

        Returns:
            True if user exists
        """
        try:
            User.objects.filter(id=recipient, is_active=True).exists()
            return True
        except (ValueError, Exception):
            return False

    def send(self, message: NotificationMessage) -> SendResult:
        """
        Send inbox notification by creating/updating database record.

        Args:
            message: NotificationMessage to send

        Returns:
            SendResult with send details
        """
        start_time = time.time()

        try:
            from apps.notifications.models import Notification

            # Get recipient user
            try:
                recipient = User.objects.get(id=message.recipient)
            except User.DoesNotExist:
                return SendResult(
                    success=False,
                    status=ChannelStatus.FAILED,
                    message="Recipient user not found",
                    error_code="INVALID_RECIPIENT",
                    error_message=f"User with id {message.recipient} does not exist",
                )

            # Check if notification already exists (by external_id)
            notification = None
            if message.external_id:
                notification = Notification.objects.filter(
                    data__external_id=message.external_id
                ).first()

            # Create or update notification
            if notification:
                # Update existing notification
                notification.title = message.subject
                notification.content = message.content
                notification.data = {**notification.data, **message.data}
                notification.save(update_fields=['title', 'content', 'data', 'updated_at'])
            else:
                # Create new notification
                notification = Notification.objects.create(
                    recipient=recipient,
                    notification_type=message.data.get('notification_type', 'general'),
                    priority=self._map_priority(message.priority),
                    channel=self.channel_type,
                    title=message.subject,
                    content=message.content,
                    data={
                        **message.data,
                        'external_id': message.external_id,
                    },
                    status='pending',
                )

            duration_ms = int((time.time() - start_time) * 1000)

            return SendResult(
                success=True,
                status=ChannelStatus.SUCCESS,
                message=f"Inbox notification sent to {recipient.username}",
                external_id=str(notification.id),
                duration_ms=duration_ms,
                response_data={
                    'notification_id': str(notification.id),
                    'recipient': recipient.username,
                },
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return SendResult(
                success=False,
                status=ChannelStatus.FAILED,
                message=f"Failed to send inbox notification: {str(e)}",
                error_code="SEND_FAILED",
                error_message=str(e),
                duration_ms=duration_ms,
            )

    def format_message(self, message: NotificationMessage) -> dict:
        """
        Format message for inbox storage.

        Args:
            message: NotificationMessage to format

        Returns:
            Dictionary with formatted data
        """
        return {
            'title': message.subject,
            'content': message.content,
            'data': message.data,
            'priority': self._map_priority(message.priority),
            'notification_type': message.data.get('notification_type', 'general'),
        }

    def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """
        Mark notification as read.

        Args:
            notification_id: Notification UUID
            user_id: User UUID

        Returns:
            True if marked successfully
        """
        try:
            from apps.notifications.models import Notification

            notification = Notification.objects.get(
                id=notification_id,
                recipient_id=user_id,
            )
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False

    def mark_all_as_read(self, user_id: str) -> int:
        """
        Mark all user notifications as read.

        Args:
            user_id: User UUID

        Returns:
            Number of notifications marked as read
        """
        from apps.notifications.models import Notification

        count = Notification.objects.filter(
            recipient_id=user_id,
            read_at__isnull=True,
        ).update(read_at=timezone.now())

        return count

    def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications for user.

        Args:
            user_id: User UUID

        Returns:
            Number of unread notifications
        """
        from apps.notifications.models import Notification

        return Notification.objects.filter(
            recipient_id=user_id,
            read_at__isnull=True,
            is_deleted=False,
        ).count()

    def _map_priority(self, priority: str) -> str:
        """Map message priority to notification priority."""
        priority_map = {
            'urgent': 'urgent',
            'high': 'high',
            'normal': 'normal',
            'low': 'low',
        }
        return priority_map.get(priority, 'normal')
