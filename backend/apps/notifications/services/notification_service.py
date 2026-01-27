"""
Notification Service

Main service for sending notifications through multiple channels.
Handles channel selection, retry logic, and user preferences.
"""
import logging
import uuid
from typing import List, Dict, Any, Optional, Union
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.notifications.models import (
    Notification,
    NotificationLog,
    NotificationConfig,
    NotificationTemplate,
)
from apps.notifications.channels import (
    get_channel,
    get_supported_channels,
    NotificationMessage,
    SendResult,
    ChannelStatus,
)
from apps.notifications.services.template_service import template_service

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationService:
    """
    Main notification service for sending notifications.

    Features:
    - Multi-channel delivery (inbox, email, SMS, WeWork, DingTalk)
    - Template-based content rendering
    - User preference handling
    - Automatic retry with exponential backoff
    - Quiet hours support
    - Comprehensive logging
    """

    def __init__(self):
        """Initialize notification service."""
        self.max_retries = 3

    def send(
        self,
        recipient: Union[User, str],
        notification_type: str,
        variables: Dict[str, Any],
        channels: Optional[List[str]] = None,
        priority: str = 'normal',
        scheduled_at: Optional[timezone.datetime] = None,
        sender: Optional[User] = None,
        related_object: Optional[tuple] = None,
    ) -> Dict[str, Any]:
        """
        Send notification to recipient.

        Args:
            recipient: User instance or user ID
            notification_type: Notification type code
            variables: Template variables
            channels: Specific channels to use (None = use defaults)
            priority: Notification priority (urgent, high, normal, low)
            scheduled_at: Schedule send time (None = immediate)
            sender: User who triggered the notification
            related_object: Tuple of (content_type, object_id)

        Returns:
            Dict with send results for each channel
        """
        # Get recipient user
        if isinstance(recipient, User):
            recipient_user = recipient
        else:
            recipient_user = User.objects.filter(id=recipient, is_active=True).first()
            if not recipient_user:
                return {
                    'success': False,
                    'message': 'Recipient not found',
                    'results': [],
                }

        # Get user notification config
        config = self._get_user_config(recipient_user)

        # Determine channels to use
        if not channels:
            channels = self._get_default_channels(notification_type, config)

        # Filter enabled channels
        enabled_channels = []
        for channel in channels:
            if config and config.is_channel_enabled(notification_type, channel):
                # Check quiet hours
                if not config.is_in_quiet_hours() or priority == 'urgent':
                    enabled_channels.append(channel)
            elif channel == 'inbox':
                # Always enable inbox unless explicitly disabled
                if not config or config.enable_inbox:
                    enabled_channels.append(channel)

        if not enabled_channels:
            return {
                'success': False,
                'message': 'No enabled channels for this notification type',
                'results': [],
            }

        # Send to each channel
        results = []
        success_count = 0
        failure_count = 0

        for channel in enabled_channels:
            result = self._send_to_channel(
                recipient=recipient_user,
                notification_type=notification_type,
                channel=channel,
                variables=variables,
                priority=priority,
                scheduled_at=scheduled_at,
                sender=sender,
                related_object=related_object,
            )
            results.append(result)
            if result['success']:
                success_count += 1
            else:
                failure_count += 1

        return {
            'success': failure_count == 0,
            'message': f'Sent to {success_count} channels, {failure_count} failed',
            'results': results,
            'summary': {
                'total': len(results),
                'succeeded': success_count,
                'failed': failure_count,
            },
        }

    def send_batch(
        self,
        recipients: List[Union[User, str]],
        notification_type: str,
        variables: Dict[str, Any],
        channels: Optional[List[str]] = None,
        priority: str = 'normal',
        sender: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        Send notification to multiple recipients.

        Args:
            recipients: List of User instances or user IDs
            notification_type: Notification type code
            variables: Template variables (can be per-recipient)
            channels: Channels to use
            priority: Notification priority
            sender: User who triggered the notification

        Returns:
            Dict with batch send results
        """
        results = []
        success_count = 0
        failure_count = 0

        for recipient in recipients:
            # Allow per-recipient variables
            recipient_vars = variables
            if isinstance(variables, dict) and '_per_recipient' in variables:
                recipient_id = recipient.id if isinstance(recipient, User) else recipient
                recipient_vars = {
                    k: v for k, v in variables.items()
                    if k != '_per_recipient'
                }
                recipient_vars.update(
                    variables['_per_recipient'].get(str(recipient_id), {})
                )

            result = self.send(
                recipient=recipient,
                notification_type=notification_type,
                variables=recipient_vars,
                channels=channels,
                priority=priority,
                sender=sender,
            )
            results.append({
                'recipient': str(recipient),
                'result': result,
            })
            if result['success']:
                success_count += 1
            else:
                failure_count += 1

        return {
            'success': failure_count == 0,
            'message': f'Sent to {success_count} recipients, {failure_count} failed',
            'results': results,
            'summary': {
                'total': len(recipients),
                'succeeded': success_count,
                'failed': failure_count,
            },
        }

    def _send_to_channel(
        self,
        recipient: User,
        notification_type: str,
        channel: str,
        variables: Dict[str, Any],
        priority: str,
        scheduled_at: Optional[timezone.datetime],
        sender: Optional[User],
        related_object: Optional[tuple],
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Send notification to specific channel.

        Args:
            recipient: Recipient user
            notification_type: Notification type code
            channel: Channel to use
            variables: Template variables
            priority: Notification priority
            scheduled_at: Schedule time
            sender: Sender user
            related_object: Related object tuple
            retry_count: Current retry attempt

        Returns:
            Dict with send result
        """
        # Render template
        rendered = template_service.render_template(
            template_code=notification_type,
            channel=channel,
            variables=variables,
        )

        if not rendered:
            # Fallback to basic rendering
            rendered = {
                'subject': notification_type,
                'content': str(variables),
            }

        # Get channel adapter
        try:
            channel_adapter = get_channel(channel)
        except ValueError as e:
            return {
                'success': False,
                'channel': channel,
                'message': f'Channel not available: {e}',
            }

        # Prepare message
        message = NotificationMessage(
            recipient=self._get_recipient_address(recipient, channel),
            subject=rendered.get('subject', ''),
            content=rendered.get('content', ''),
            html_content=rendered.get('html'),
            data={
                'notification_type': notification_type,
                **variables
            },
            priority=priority,
            external_id=str(uuid.uuid4()),
        )

        # Create notification record (for inbox and tracking)
        notification = self._create_notification_record(
            recipient=recipient,
            notification_type=notification_type,
            channel=channel,
            priority=priority,
            rendered=rendered,
            variables=variables,
            scheduled_at=scheduled_at,
            sender=sender,
            related_object=related_object,
        )

        # Send message
        try:
            result = channel_adapter.send_with_validation(message)

            # Create log entry
            self._create_log_entry(
                notification=notification,
                channel=channel,
                result=result,
                retry_count=retry_count,
            )

            # Update notification status
            if result.success:
                notification.status = 'success'
                notification.sent_at = timezone.now()
            else:
                # Check if should retry
                if channel_adapter.should_retry(result, retry_count, self.max_retries):
                    notification.status = 'pending'
                    notification.retry_count = retry_count + 1
                    # Schedule retry
                    delay = channel_adapter.get_retry_delay(retry_count, self.max_retries)
                    notification.next_retry_at = timezone.now() + timezone.timedelta(seconds=delay)
                else:
                    notification.status = 'failed'
            notification.save(update_fields=['status', 'sent_at', 'retry_count', 'next_retry_at'])

            return {
                'success': result.success,
                'channel': channel,
                'message': result.message,
                'notification_id': str(notification.id) if notification else None,
                'error_code': result.error_code,
            }

        except Exception as e:
            logger.error(f"Error sending notification to {channel}: {e}")

            # Update notification as failed
            if notification:
                notification.status = 'failed'
                notification.save(update_fields=['status'])

            return {
                'success': False,
                'channel': channel,
                'message': str(e),
            }

    def _create_notification_record(
        self,
        recipient: User,
        notification_type: str,
        channel: str,
        priority: str,
        rendered: Dict[str, str],
        variables: Dict[str, Any],
        scheduled_at: Optional[timezone.datetime],
        sender: Optional[User],
        related_object: Optional[tuple],
    ) -> Optional[Notification]:
        """Create notification record for tracking."""
        try:
            notification = Notification.objects.create(
                recipient=recipient,
                notification_type=notification_type,
                channel=channel,
                priority=priority,
                title=rendered.get('subject', ''),
                content=rendered.get('content', ''),
                data={
                    'variables': variables,
                },
                scheduled_at=scheduled_at,
                sender=sender,
                related_content_type=related_object[0] if related_object else None,
                related_object_id=related_object[1] if related_object else None,
                status='pending',
            )
            return notification
        except Exception as e:
            logger.error(f"Error creating notification record: {e}")
            return None

    def _create_log_entry(
        self,
        notification: Optional[Notification],
        channel: str,
        result: SendResult,
        retry_count: int,
    ) -> None:
        """Create log entry for send attempt."""
        try:
            NotificationLog.objects.create(
                notification=notification,
                channel=channel,
                status=result.status.value,
                request_data={},  # Could add actual request payload
                response_data=result.response_data,
                error_code=result.error_code,
                error_message=result.error_message,
                retry_count=retry_count,
                duration=result.duration_ms,
                external_id=result.external_id,
                external_status=result.status.value,
            )
        except Exception as e:
            logger.error(f"Error creating notification log: {e}")

    def _get_user_config(self, user: User) -> Optional[NotificationConfig]:
        """Get or create user notification config."""
        try:
            return NotificationConfig.objects.get(user=user)
        except NotificationConfig.DoesNotExist:
            # Return default config
            return None

    def _get_default_channels(
        self,
        notification_type: str,
        config: Optional[NotificationConfig]
    ) -> List[str]:
        """Get default channels for notification type."""
        # Default channels
        default_channels = ['inbox']

        # Add email if enabled
        if not config or config.enable_email:
            default_channels.append('email')

        return default_channels

    def _get_recipient_address(self, user: User, channel: str) -> str:
        """Get recipient address for specific channel."""
        if channel == 'email':
            return user.email
        elif channel == 'sms':
            config = NotificationConfig.objects.filter(user=user).first()
            if config and config.phone_number:
                return config.phone_number
            return getattr(user, 'phone', '') or ''
        elif channel in ['wework', 'dingtalk']:
            # Get user's third-party ID from SSO
            # This would need to be implemented based on your SSO setup
            return str(user.id)
        else:
            # For inbox, use user ID
            return str(user.id)

    def mark_as_read(self, notification_id: str, user: User) -> bool:
        """Mark notification as read."""
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=user,
            )
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False

    def mark_all_as_read(self, user: User) -> int:
        """Mark all user notifications as read."""
        count = Notification.objects.filter(
            recipient=user,
            read_at__isnull=True,
        ).update(read_at=timezone.now())
        return count

    def get_unread_count(self, user: User) -> int:
        """Get count of unread notifications for user."""
        return Notification.objects.filter(
            recipient=user,
            read_at__isnull=True,
            is_deleted=False,
        ).count()

    def retry_failed_notifications(self) -> int:
        """
        Retry failed notifications that are due for retry.

        This method is intended to be called by a periodic task.

        Returns:
            Number of notifications retried
        """
        # Get notifications pending retry
        notifications = Notification.objects.filter(
            status='pending',
            next_retry_at__lte=timezone.now(),
            retry_count__lt=self.max_retries,
        )

        retried = 0
        for notification in notifications:
            try:
                # Get channel adapter
                channel_adapter = get_channel(notification.channel)

                # Render template again
                rendered = template_service.render_template(
                    template_code=notification.notification_type,
                    channel=notification.channel,
                    variables=notification.data.get('variables', {}),
                )

                if rendered:
                    # Prepare message
                    message = NotificationMessage(
                        recipient=self._get_recipient_address(
                            notification.recipient,
                            notification.channel
                        ),
                        subject=rendered.get('subject', ''),
                        content=rendered.get('content', ''),
                        data=notification.data,
                        priority=notification.priority,
                    )

                    # Send
                    result = channel_adapter.send(message)

                    # Update notification
                    if result.success:
                        notification.status = 'success'
                        notification.sent_at = timezone.now()
                        notification.next_retry_at = None
                    elif channel_adapter.should_retry(
                        result,
                        notification.retry_count,
                        self.max_retries
                    ):
                        notification.status = 'pending'
                        notification.retry_count += 1
                        delay = channel_adapter.get_retry_delay(
                            notification.retry_count,
                            self.max_retries
                        )
                        notification.next_retry_at = timezone.now() + timezone.timedelta(seconds=delay)
                    else:
                        notification.status = 'failed'
                        notification.next_retry_at = None

                    notification.save()
                    retried += 1

            except Exception as e:
                logger.error(f"Error retrying notification {notification.id}: {e}")

        return retried

    def cleanup_old_notifications(self, days: int = 90) -> int:
        """
        Soft delete old read notifications.

        Args:
            days: Age threshold in days

        Returns:
            Number of notifications cleaned up
        """
        cutoff = timezone.now() - timezone.timedelta(days=days)
        count = Notification.objects.filter(
            read_at__isnull=False,
            read_at__lt=cutoff,
            is_deleted=False,
        ).update(is_deleted=True, deleted_at=timezone.now())
        return count


# Singleton instance
notification_service = NotificationService()
