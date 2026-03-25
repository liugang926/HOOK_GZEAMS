"""
Celery Tasks for Notifications

Async tasks for notification sending, retry, and cleanup.
"""
import logging
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification, NotificationTemplate
from apps.notifications.services import notification_service, template_service

logger = get_task_logger(__name__)
User = get_user_model()


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def send_notification_task(
    self,
    recipient_id: str,
    notification_type: str,
    variables: dict,
    channels: list = None,
    priority: str = 'normal',
    sender_id: str = None,
):
    """
    Send notification asynchronously via Celery.

    Args:
        self: Task instance for retry
        recipient_id: Recipient user UUID
        notification_type: Notification type code
        variables: Template variables
        channels: List of channels to use (None = default)
        priority: Notification priority
        sender_id: Sender user UUID

    Returns:
        Dict with send results
    """
    try:
        # Get recipient
        recipient = User.objects.filter(id=recipient_id).first()
        if not recipient:
            logger.error(f"Recipient not found: {recipient_id}")
            return {'success': False, 'error': 'Recipient not found'}

        # Get sender
        sender = None
        if sender_id:
            sender = User.objects.filter(id=sender_id).first()

        # Send notification
        result = notification_service.send(
            recipient=recipient,
            notification_type=notification_type,
            variables=variables,
            channels=channels,
            priority=priority,
            sender=sender,
        )

        return result

    except Exception as e:
        logger.error(f"Error in send_notification_task: {e}")
        # Task will be retried automatically due to autoretry_for
        raise


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def send_batch_notification_task(
    self,
    recipient_ids: list,
    notification_type: str,
    variables: dict,
    channels: list = None,
    priority: str = 'normal',
    sender_id: str = None,
):
    """
    Send batch notification asynchronously via Celery.

    Args:
        self: Task instance for retry
        recipient_ids: List of recipient user UUIDs
        notification_type: Notification type code
        variables: Template variables
        channels: List of channels to use
        priority: Notification priority
        sender_id: Sender user UUID

    Returns:
        Dict with batch send results
    """
    try:
        # Get recipients
        recipients = User.objects.filter(id__in=recipient_ids, is_active=True)

        if not recipients.exists():
            logger.error(f"No valid recipients found for IDs: {recipient_ids}")
            return {'success': False, 'error': 'No valid recipients found'}

        # Get sender
        sender = None
        if sender_id:
            sender = User.objects.filter(id=sender_id).first()

        # Send batch notification
        result = notification_service.send_batch(
            recipients=list(recipients),
            notification_type=notification_type,
            variables=variables,
            channels=channels,
            priority=priority,
            sender=sender,
        )

        return result

    except Exception as e:
        logger.error(f"Error in send_batch_notification_task: {e}")
        raise


@shared_task
def retry_failed_notifications_task():
    """
    Retry failed notifications that are due for retry.

    This task should be scheduled to run periodically (e.g., every minute).
    """
    logger.info("Running retry_failed_notifications_task")

    try:
        count = notification_service.retry_failed_notifications()
        logger.info(f"Retried {count} notifications")
        return {'retried': count}
    except Exception as e:
        logger.error(f"Error in retry_failed_notifications_task: {e}")
        return {'error': str(e), 'retried': 0}


@shared_task
def send_scheduled_notifications_task():
    """
    Send notifications that are scheduled for future delivery.

    This task should be scheduled to run periodically (e.g., every minute).
    """
    logger.info("Running send_scheduled_notifications_task")

    try:
        # Get notifications scheduled for now or past
        notifications = Notification.objects.filter(
            status='pending',
            scheduled_at__lte=timezone.now(),
            sent_at__isnull=True,
        )

        count = 0
        for notification in notifications:
            try:
                # Get channel and send
                from apps.notifications.channels import get_channel, NotificationMessage

                channel_adapter = get_channel(notification.channel)

                # Render template
                rendered = template_service.render_template(
                    template_code=notification.notification_type,
                    channel=notification.channel,
                    variables=notification.data.get('variables', {}),
                )

                if rendered:
                    message = NotificationMessage(
                        recipient=str(notification.recipient_id),
                        subject=rendered.get('subject', ''),
                        content=rendered.get('content', ''),
                        data=notification.data,
                        priority=notification.priority,
                    )

                    result = channel_adapter.send(message)

                    # Update notification
                    if result.success:
                        notification.status = 'success'
                        notification.sent_at = timezone.now()
                    else:
                        notification.status = 'failed'
                    notification.save()
                    count += 1

            except Exception as e:
                logger.error(f"Error sending scheduled notification {notification.id}: {e}")
                notification.status = 'failed'
                notification.save()

        logger.info(f"Sent {count} scheduled notifications")
        return {'sent': count}

    except Exception as e:
        logger.error(f"Error in send_scheduled_notifications_task: {e}")
        return {'error': str(e), 'sent': 0}


@shared_task
def cleanup_old_notifications_task(days: int = 90):
    """
    Soft delete old read notifications.

    This task should be scheduled to run periodically (e.g., daily).

    Args:
        days: Age threshold in days (default: 90)
    """
    logger.info(f"Running cleanup_old_notifications_task for {days} days")

    try:
        count = notification_service.cleanup_old_notifications(days=days)
        logger.info(f"Cleaned up {count} old notifications")
        return {'cleaned': count}
    except Exception as e:
        logger.error(f"Error in cleanup_old_notifications_task: {e}")
        return {'error': str(e), 'cleaned': 0}


@shared_task
def cleanup_old_logs_task(days: int = 180):
    """
    Delete old notification logs.

    This task should be scheduled to run periodically (e.g., weekly).

    Args:
        days: Age threshold in days (default: 180)
    """
    logger.info(f"Running cleanup_old_logs_task for {days} days")

    try:
        from apps.notifications.models import NotificationLog

        cutoff = timezone.now() - timezone.timedelta(days=days)
        count, _ = NotificationLog.objects.filter(
            created_at__lt=cutoff
        ).delete()

        logger.info(f"Cleaned up {count} old logs")
        return {'cleaned': count}
    except Exception as e:
        logger.error(f"Error in cleanup_old_logs_task: {e}")
        return {'error': str(e), 'cleaned': 0}


@shared_task
def mark_notifications_sent_task():
    """
    Mark notifications as sent if they've been pending too long.

    This is a safety task to prevent notifications from being stuck
    in 'pending' status forever.
    """
    logger.info("Running mark_notifications_sent_task")

    try:
        # Mark notifications pending for more than 1 hour as failed
        cutoff = timezone.now() - timezone.timedelta(hours=1)
        count = Notification.objects.filter(
            status='pending',
            created_at__lt=cutoff,
            retry_count__gte=3,
        ).update(status='failed')

        logger.info(f"Marked {count} stale notifications as failed")
        return {'marked': count}
    except Exception as e:
        logger.error(f"Error in mark_notifications_sent_task: {e}")
        return {'error': str(e), 'marked': 0}


@shared_task
def send_daily_digest_task():
    """
    Send daily notification digest to users.

    This task should be scheduled to run daily at a specific time.
    """
    logger.info("Running send_daily_digest_task")

    try:
        from apps.notifications.models import NotificationConfig

        # Get users who have daily digest enabled
        # (This would need a flag in NotificationConfig)

        # For each user, collect unread notifications
        # and send a digest summary

        return {'sent': 0}  # Placeholder

    except Exception as e:
        logger.error(f"Error in send_daily_digest_task: {e}")
        return {'error': str(e), 'sent': 0}


@shared_task
def broadcast_notification_task(
    notification_type: str,
    variables: dict,
    channels: list = None,
    exclude_user_ids: list = None,
    priority: str = 'normal',
    sender_id: str = None,
):
    """
    Send notification to all active users (broadcast).

    Use with caution - this sends to ALL users.

    Args:
        notification_type: Notification type code
        variables: Template variables
        channels: Channels to use
        exclude_user_ids: List of user IDs to exclude
        priority: Notification priority
        sender_id: Sender user UUID

    Returns:
        Dict with broadcast results
    """
    logger.info(f"Running broadcast_notification_task: {notification_type}")

    try:
        # Get all active users except excluded ones
        queryset = User.objects.filter(is_active=True)
        if exclude_user_ids:
            queryset = queryset.exclude(id__in=exclude_user_ids)

        recipients = list(queryset)

        # Get sender
        sender = None
        if sender_id:
            sender = User.objects.filter(id=sender_id).first()

        # Send batch notification
        result = notification_service.send_batch(
            recipients=recipients,
            notification_type=notification_type,
            variables=variables,
            channels=channels,
            priority=priority,
            sender=sender,
        )

        logger.info(f"Broadcast completed: {result.get('summary', {})}")
        return result

    except Exception as e:
        logger.error(f"Error in broadcast_notification_task: {e}")
        return {'error': str(e), 'sent': 0}


# Celery Beat schedule configuration
# These tasks should be registered in celery.py
CELERY_BEAT_SCHEDULE = {
    'retry-failed-notifications': {
        'task': 'apps.notifications.tasks.retry_failed_notifications_task',
        'schedule': 60.0,  # Run every 60 seconds
    },
    'send-scheduled-notifications': {
        'task': 'apps.notifications.tasks.send_scheduled_notifications_task',
        'schedule': 60.0,  # Run every 60 seconds
    },
    'cleanup-old-notifications': {
        'task': 'apps.notifications.tasks.cleanup_old_notifications_task',
        'schedule': 86400.0,  # Run daily (24 hours)
    },
    'cleanup-old-logs': {
        'task': 'apps.notifications.tasks.cleanup_old_logs_task',
        'schedule': 604800.0,  # Run weekly (7 days)
    },
    'mark-stale-notifications': {
        'task': 'apps.notifications.tasks.mark_notifications_sent_task',
        'schedule': 3600.0,  # Run every hour
    },
}
