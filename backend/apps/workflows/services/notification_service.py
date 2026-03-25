"""
Notification Service for Workflow Events.

Handles sending notifications for workflow lifecycle events:
- Task assignment
- Task completion
- Workflow approval/rejection
- Task overdue alerts
"""

from typing import List, Dict, Any, Optional
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationService:
    """
    Send notifications for workflow events.
    
    Supports multiple notification channels:
    - Email (via Django email backend)
    - Push notifications (extensible)
    - In-app messages (extensible)
    """
    
    NOTIFICATION_TYPES = {
        'task_assigned': {
            'template': 'workflows/notifications/task_assigned.html',
            'subject': _('New Task Assigned: {task_name}'),
            'channels': ['email', 'push']
        },
        'task_completed': {
            'template': 'workflows/notifications/task_completed.html',
            'subject': _('Task Completed: {task_name}'),
            'channels': ['email']
        },
        'task_overdue': {
            'template': 'workflows/notifications/task_overdue.html',
            'subject': _('⚠️ Overdue Task: {task_name}'),
            'channels': ['email', 'push']
        },
        'workflow_completed': {
            'template': 'workflows/notifications/workflow_completed.html',
            'subject': _('Workflow Completed: {workflow_name}'),
            'channels': ['email']
        },
        'workflow_rejected': {
            'template': 'workflows/notifications/workflow_rejected.html',
            'subject': _('Workflow Rejected: {workflow_name}'),
            'channels': ['email', 'push']
        },
        'workflow_cancelled': {
            'template': 'workflows/notifications/workflow_cancelled.html',
            'subject': _('Workflow Cancelled: {workflow_name}'),
            'channels': ['email']
        }
    }
    
    def __init__(self):
        """Initialize notification service."""
        self.email_enabled = getattr(settings, 'EMAIL_ENABLED', True)
        self.push_enabled = getattr(settings, 'PUSH_NOTIFICATIONS_ENABLED', False)
    
    def send_notification(
        self,
        event_type: str,
        context: Dict[str, Any],
        recipients: List[User],
        channels: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Send notification for workflow event.
        
        Args:
            event_type: Type of notification event (e.g., 'task_assigned')
            context: Template context variables
            recipients: List of User objects to notify
            channels: Optional list of channels to use (defaults to config)
            
        Returns:
            Dict mapping channel names to success status
        """
        config = self.NOTIFICATION_TYPES.get(event_type)
        if not config:
            logger.warning(f"Unknown notification type: {event_type}")
            return {}
        
        if not recipients:
            logger.warning(f"No recipients for notification: {event_type}")
            return {}
        
        # Use provided channels or default from config
        use_channels = channels or config['channels']
        
        # Render subject with context
        try:
            subject = str(config['subject']).format(**context)
        except KeyError as e:
            logger.error(f"Missing context variable for subject: {e}")
            subject = str(config['subject'])
        
        # Render HTML content
        try:
            html_content = render_to_string(config['template'], context)
        except Exception as e:
            logger.error(f"Failed to render notification template: {e}")
            html_content = f"<p>{subject}</p>"
        
        results = {}
        
        # Send via each configured channel
        for channel in use_channels:
            if channel == 'email':
                results['email'] = self._send_email(recipients, subject, html_content)
            elif channel == 'push':
                results['push'] = self._send_push(recipients, subject, context)
            elif channel == 'in_app':
                results['in_app'] = self._send_in_app(recipients, subject, context)
        
        return results
    
    def _send_email(
        self,
        recipients: List[User],
        subject: str,
        html_content: str
    ) -> bool:
        """Send email notification."""
        if not self.email_enabled:
            logger.debug("Email notifications disabled")
            return False
        
        try:
            from django.core.mail import send_mail
            
            recipient_emails = [
                user.email for user in recipients
                if user.email
            ]
            
            if not recipient_emails:
                logger.warning("No valid email addresses for recipients")
                return False
            
            send_mail(
                subject=subject,
                message='',  # Plain text body (empty for HTML emails)
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_emails,
                html_message=html_content,
                fail_silently=False
            )
            
            logger.info(f"Email sent to {len(recipient_emails)} recipients: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _send_push(
        self,
        recipients: List[User],
        title: str,
        context: Dict[str, Any]
    ) -> bool:
        """Send push notification (placeholder for future implementation)."""
        if not self.push_enabled:
            logger.debug("Push notifications disabled")
            return False
        
        # Push notification service placeholder
        # Integration with Firebase Cloud Messaging, Apple Push Notification Service, etc.
        # Currently returns False as push notifications are not implemented.
        # To implement, integrate with FCM/APNS provider.
        
        logger.debug(f"Push notification would be sent: {title}")
        return False
    
    def _send_in_app(
        self,
        recipients: List[User],
        title: str,
        context: Dict[str, Any]
    ) -> bool:
        """Send in-app notification.
        
        Note: In-app notifications are fully implemented via Notification model
        and NotificationViewSet with inbox channel. See apps/notifications module.
        """
        # In-app notifications are already implemented
        # via apps.notifications.models.Notification and inbox channel
        # See NotificationViewSet for API endpoints
        
        logger.debug(f"In-app notification would be sent: {title}")
        return False
    
    def notify_task_assigned(
        self,
        task,
        assignees: List[User]
    ) -> Dict[str, bool]:
        """
        Send notification when a task is assigned.
        
        Args:
            task: WorkflowTask instance
            assignees: List of User objects assigned to the task
            
        Returns:
            Dict mapping channels to success status
        """
        workflow_instance = task.instance
        
        context = {
            'task_name': task.node_name or task.node_id,
            'workflow_name': workflow_instance.definition.name,
            'business_object': workflow_instance.business_object_code,
            'business_id': workflow_instance.business_id,
            'business_no': workflow_instance.business_no,
            'due_date': task.due_date,
            'priority': workflow_instance.priority,
            'approval_link': self._get_approval_link(task),
            'site_name': getattr(settings, 'SITE_NAME', 'Workflow System'),
        }
        
        return self.send_notification('task_assigned', context, assignees)
    
    def notify_task_completed(
        self,
        task,
        approver: Optional[User]
    ) -> Dict[str, bool]:
        """
        Send notification when a task is completed.
        
        Args:
            task: WorkflowTask instance
            approver: User who completed the task
            
        Returns:
            Dict mapping channels to success status
        """
        workflow_instance = task.instance
        latest_approval = self._get_latest_approval(task)
        
        context = {
            'task_name': task.node_name or task.node_id,
            'workflow_name': workflow_instance.definition.name,
            'approver_name': self._get_user_display_name(approver),
            'comment': latest_approval.comment if latest_approval and latest_approval.comment else '',
            'completed_at': task.completed_at,
        }
        
        # Notify workflow initiator
        recipients = [workflow_instance.initiator] if workflow_instance.initiator else []
        
        return self.send_notification('task_completed', context, recipients)
    
    def notify_task_overdue(
        self,
        task,
        assignees: List[User]
    ) -> Dict[str, bool]:
        """
        Send notification when a task is overdue.
        
        Args:
            task: WorkflowTask instance
            assignees: List of User objects assigned to the task
            
        Returns:
            Dict mapping channels to success status
        """
        from django.utils import timezone
        
        workflow_instance = task.instance
        
        context = {
            'task_name': task.node_name or task.node_id,
            'workflow_name': workflow_instance.definition.name,
            'due_date': task.due_date,
            'hours_overdue': (timezone.now() - task.due_date).total_seconds() / 3600
                              if task.due_date else 0,
            'approval_link': self._get_approval_link(task),
        }
        
        return self.send_notification('task_overdue', context, assignees)
    
    def notify_workflow_completed(
        self,
        workflow_instance
    ) -> Dict[str, bool]:
        """
        Send notification when a workflow is completed (approved).
        
        Args:
            workflow_instance: WorkflowInstance instance
            
        Returns:
            Dict mapping channels to success status
        """
        context = {
            'workflow_name': workflow_instance.definition.name,
            'business_object': workflow_instance.business_object_code,
            'business_id': workflow_instance.business_id,
            'business_no': workflow_instance.business_no,
            'result': 'approved',
            'completed_at': workflow_instance.completed_at,
        }
        
        recipients = [workflow_instance.initiator] if workflow_instance.initiator else []
        
        return self.send_notification('workflow_completed', context, recipients)
    
    def notify_workflow_rejected(
        self,
        workflow_instance,
        rejector: Optional[User]
    ) -> Dict[str, bool]:
        """
        Send notification when a workflow is rejected.
        
        Args:
            workflow_instance: WorkflowInstance instance
            rejector: User who rejected the workflow
            
        Returns:
            Dict mapping channels to success status
        """
        # Get rejection comment from last task
        last_task = workflow_instance.tasks.filter(
            completed_at__isnull=False
        ).order_by('-completed_at').first()
        latest_approval = self._get_latest_approval(last_task) if last_task else None
        
        context = {
            'workflow_name': workflow_instance.definition.name,
            'business_object': workflow_instance.business_object_code,
            'business_id': workflow_instance.business_id,
            'business_no': workflow_instance.business_no,
            'result': 'rejected',
            'rejector_name': self._get_user_display_name(rejector),
            'rejection_comment': latest_approval.comment if latest_approval and latest_approval.comment else '',
            'completed_at': workflow_instance.completed_at,
        }
        
        recipients = [workflow_instance.initiator] if workflow_instance.initiator else []
        
        return self.send_notification('workflow_rejected', context, recipients)
    
    def notify_workflow_cancelled(
        self,
        workflow_instance,
        cancelled_by: Optional[User],
        reason: str = ''
    ) -> Dict[str, bool]:
        """
        Send notification when a workflow is cancelled.
        
        Args:
            workflow_instance: WorkflowInstance instance
            cancelled_by: User who cancelled the workflow
            reason: Cancellation reason
            
        Returns:
            Dict mapping channels to success status
        """
        context = {
            'workflow_name': workflow_instance.definition.name,
            'business_object': workflow_instance.business_object_code,
            'business_id': workflow_instance.business_id,
            'business_no': workflow_instance.business_no,
            'cancelled_by': self._get_user_display_name(cancelled_by),
            'reason': reason,
            'cancelled_at': workflow_instance.updated_at,
        }
        
        recipients = [workflow_instance.initiator] if workflow_instance.initiator else []
        
        return self.send_notification('workflow_cancelled', context, recipients)
    
    def _get_approval_link(self, task) -> str:
        """Generate approval link for a task."""
        # TODO: Implement proper URL generation
        base_url = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:3000')
        return f"{base_url}/workflow/approvals/{task.id}"

    def _get_latest_approval(self, task):
        """Get the most recent approval record for a task."""
        if task is None:
            return None
        return task.approvals.order_by('-created_at').first()

    def _get_user_display_name(self, user: Optional[User]) -> str:
        """Get a display name for a user."""
        if user is None:
            return ''
        return user.get_full_name() or user.username


# Singleton instance
notification_service = NotificationService()
