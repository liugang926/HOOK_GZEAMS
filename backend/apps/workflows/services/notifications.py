"""
Enhanced workflow notification helpers.

Builds richer notification payloads, resolves delivery preferences, and
stores notifications with content structured for UI rendering.
"""
from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union
from uuid import UUID

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Model
from django.utils import timezone
from django.utils.html import escape

from apps.notifications.models import Notification, NotificationLog
from apps.users.services.user_preferences import user_preferences_service

User = get_user_model()


class SafeFormatDict(dict):
    """Gracefully ignore missing format keys."""

    def __missing__(self, key: str) -> str:
        return ''


@dataclass(frozen=True)
class WorkflowNotificationTemplate:
    """Notification template definition."""

    title: str
    summary: str
    body: str
    badge: str
    action_label: str
    default_channels: Sequence[str]


class EnhancedNotificationService:
    """
    Send workflow notifications with richer UX metadata.
    """

    DELIVERABLE_CHANNELS = ('inbox', 'email')
    TEMPLATES = {
        'task_assigned': WorkflowNotificationTemplate(
            title='Approval required: {task_name}',
            summary='{workflow_name} is waiting for your review.',
            body='Document: {business_reference}\nPriority: {priority_label}\nDue: {due_date_label}',
            badge='Assigned',
            action_label='Review task',
            default_channels=('inbox', 'email'),
        ),
        'task_completed': WorkflowNotificationTemplate(
            title='Task completed: {task_name}',
            summary='{completed_by_name} completed a workflow task.',
            body='Workflow: {workflow_name}\nDocument: {business_reference}\nResult: {task_result}',
            badge='Completed',
            action_label='View activity',
            default_channels=('inbox',),
        ),
        'task_overdue': WorkflowNotificationTemplate(
            title='Task overdue: {task_name}',
            summary='A workflow task has passed its due time and needs attention.',
            body='Workflow: {workflow_name}\nDocument: {business_reference}\nDue: {due_date_label}',
            badge='Overdue',
            action_label='Open overdue task',
            default_channels=('inbox', 'email'),
        ),
        'workflow_completed': WorkflowNotificationTemplate(
            title='Workflow completed: {workflow_name}',
            summary='The workflow reached a completed state.',
            body='Document: {business_reference}\nPriority: {priority_label}\nCompleted: {completed_at_label}',
            badge='Completed',
            action_label='View result',
            default_channels=('inbox',),
        ),
        'workflow_rejected': WorkflowNotificationTemplate(
            title='Workflow rejected: {workflow_name}',
            summary='The workflow was rejected and needs follow-up.',
            body='Document: {business_reference}\nRejected by: {completed_by_name}\nReason: {reason}',
            badge='Rejected',
            action_label='Review rejection',
            default_channels=('inbox', 'email'),
        ),
        'workflow_cancelled': WorkflowNotificationTemplate(
            title='Workflow cancelled: {workflow_name}',
            summary='The workflow was cancelled before completion.',
            body='Document: {business_reference}\nCancelled at: {completed_at_label}\nReason: {reason}',
            badge='Cancelled',
            action_label='View details',
            default_channels=('inbox',),
        ),
    }

    def get_template(self, event_type: str) -> WorkflowNotificationTemplate:
        """Get a notification template for a workflow event."""
        if event_type not in self.TEMPLATES:
            raise ValueError(f'Unsupported workflow notification event: {event_type}')
        return self.TEMPLATES[event_type]

    def build_payload(
        self,
        event_type: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build rich notification content from a workflow event.
        """
        template = self.get_template(event_type)
        formatted = self._prepare_context(context)
        title = template.title.format_map(SafeFormatDict(formatted))
        summary = template.summary.format_map(SafeFormatDict(formatted))
        body = template.body.format_map(SafeFormatDict(formatted))

        actions = self._build_actions(template, formatted)
        metrics = self._build_metrics(formatted)
        rich_content = {
            'badge': template.badge,
            'summary': summary,
            'body': body,
            'actions': actions,
            'metrics': metrics,
            'workflow': {
                'name': formatted.get('workflow_name'),
                'instance_no': formatted.get('instance_no'),
                'business_reference': formatted.get('business_reference'),
            },
        }

        html_content = self._render_html_content(title, rich_content)
        return {
            'title': title,
            'content': '\n\n'.join(part for part in [summary, body] if part),
            'html_content': html_content,
            'data': {
                'notification_type': event_type,
                'rich_content': rich_content,
                'context': self._to_json_safe(formatted),
            },
        }

    def resolve_delivery_channels(
        self,
        user: User,
        event_type: str,
        requested_channels: Optional[Iterable[str]] = None,
        priority: str = 'normal',
    ) -> List[str]:
        """
        Resolve preferred delivery channels for a user and event.
        """
        preferences = user_preferences_service.get_notification_preferences(user)
        workflow_events = preferences.get('workflow_events', {})
        if not workflow_events.get(event_type, True):
            return []

        event_channels = preferences.get('event_channels', {})
        default_channels = self.get_template(event_type).default_channels
        raw_channels = list(requested_channels or event_channels.get(event_type) or default_channels)
        channels = []

        quiet_hours = preferences.get('quiet_hours', {})
        in_quiet_hours = self._is_in_quiet_hours(quiet_hours)
        for channel_name in raw_channels:
            if channel_name not in self.DELIVERABLE_CHANNELS:
                continue
            if not preferences.get('channels', {}).get(channel_name, False):
                continue
            if channel_name == 'email' and not user.email:
                continue
            if in_quiet_hours and priority != 'urgent' and channel_name != 'inbox':
                continue
            if channel_name not in channels:
                channels.append(channel_name)

        if not channels and preferences.get('channels', {}).get('inbox', True):
            channels.append('inbox')
        return channels

    def send(
        self,
        event_type: str,
        recipient: Union[User, str],
        context: Dict[str, Any],
        channels: Optional[Iterable[str]] = None,
        priority: str = 'normal',
        sender: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        Send a rich workflow notification to one user.
        """
        user = self._resolve_user(recipient)
        if not user:
            return {
                'success': False,
                'message': 'Recipient not found',
                'results': [],
            }

        payload = self.build_payload(event_type, context)
        delivery_channels = self.resolve_delivery_channels(
            user,
            event_type,
            requested_channels=channels,
            priority=priority,
        )
        if not delivery_channels:
            return {
                'success': False,
                'message': 'No enabled delivery channels for this notification',
                'results': [],
            }

        results = []
        for channel_name in delivery_channels:
            if channel_name == 'email':
                results.append(
                    self._send_email_notification(
                        user=user,
                        event_type=event_type,
                        payload=payload,
                        priority=priority,
                        sender=sender,
                    )
                )
            else:
                results.append(
                    self._send_inbox_notification(
                        user=user,
                        event_type=event_type,
                        payload=payload,
                        priority=priority,
                        sender=sender,
                    )
                )

        success_count = sum(1 for result in results if result['success'])
        return {
            'success': success_count == len(results),
            'message': f'Sent to {success_count} channels',
            'results': results,
            'summary': {
                'total': len(results),
                'succeeded': success_count,
                'failed': len(results) - success_count,
            },
        }

    def send_batch(
        self,
        event_type: str,
        recipients: Iterable[Union[User, str]],
        context: Dict[str, Any],
        channels: Optional[Iterable[str]] = None,
        priority: str = 'normal',
        sender: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        Send a rich workflow notification to multiple users.
        """
        results = []
        for recipient in recipients:
            result = self.send(
                event_type=event_type,
                recipient=recipient,
                context=context,
                channels=channels,
                priority=priority,
                sender=sender,
            )
            results.append({
                'recipient': str(getattr(recipient, 'id', recipient)),
                'result': result,
            })

        success_count = sum(1 for item in results if item['result']['success'])
        return {
            'success': success_count == len(results),
            'message': f'Sent to {success_count} recipients',
            'results': results,
            'summary': {
                'total': len(results),
                'succeeded': success_count,
                'failed': len(results) - success_count,
            },
        }

    def notify_task_assigned(
        self,
        task: Any,
        recipients: Optional[Iterable[Union[User, str]]] = None,
    ) -> Dict[str, Any]:
        """Send a task assignment notification."""
        context = self._build_task_context(task)
        targets = list(recipients) if recipients is not None else [task.assignee]
        return self.send_batch('task_assigned', targets, context, priority=task.priority)

    def notify_task_overdue(
        self,
        task: Any,
        recipients: Optional[Iterable[Union[User, str]]] = None,
    ) -> Dict[str, Any]:
        """Send an overdue task notification."""
        context = self._build_task_context(task)
        targets = list(recipients) if recipients is not None else [task.assignee]
        return self.send_batch('task_overdue', targets, context, priority='high')

    def notify_workflow_completed(
        self,
        instance: Any,
        recipients: Optional[Iterable[Union[User, str]]] = None,
    ) -> Dict[str, Any]:
        """Send a workflow completion notification."""
        context = self._build_instance_context(instance)
        targets = list(recipients) if recipients is not None else [instance.initiator]
        return self.send_batch('workflow_completed', targets, context, priority=instance.priority)

    def _resolve_user(self, recipient: Union[User, str]) -> Optional[User]:
        """Resolve a recipient to a user instance."""
        if isinstance(recipient, User):
            return recipient
        return User.objects.filter(id=recipient, is_active=True).first()

    def _send_inbox_notification(
        self,
        user: User,
        event_type: str,
        payload: Dict[str, Any],
        priority: str,
        sender: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Persist an inbox notification record."""
        notification = Notification.objects.create(
            organization=user.current_organization or user.organization,
            recipient=user,
            notification_type=event_type,
            priority=priority,
            channel='inbox',
            title=payload['title'],
            content=payload['content'],
            data=payload['data'],
            status='success',
            sent_at=timezone.now(),
            sender=sender,
            created_by=sender,
        )
        self._create_log(notification, 'inbox', True, response_data={'delivery': 'stored'})
        return {
            'success': True,
            'channel': 'inbox',
            'notification_id': str(notification.id),
        }

    def _send_email_notification(
        self,
        user: User,
        event_type: str,
        payload: Dict[str, Any],
        priority: str,
        sender: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Send an email notification and track the result."""
        notification = Notification.objects.create(
            organization=user.current_organization or user.organization,
            recipient=user,
            notification_type=event_type,
            priority=priority,
            channel='email',
            title=payload['title'],
            content=payload['content'],
            data=payload['data'],
            status='pending',
            sender=sender,
            created_by=sender,
        )

        try:
            send_mail(
                subject=payload['title'],
                message=payload['content'],
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                recipient_list=[user.email],
                html_message=payload['html_content'],
                fail_silently=False,
            )
            notification.status = 'success'
            notification.sent_at = timezone.now()
            notification.save(update_fields=['status', 'sent_at', 'updated_at'])
            self._create_log(notification, 'email', True, response_data={'recipient': user.email})
            return {
                'success': True,
                'channel': 'email',
                'notification_id': str(notification.id),
            }
        except Exception as exc:
            notification.status = 'failed'
            notification.save(update_fields=['status', 'updated_at'])
            self._create_log(notification, 'email', False, error_message=str(exc))
            return {
                'success': False,
                'channel': 'email',
                'notification_id': str(notification.id),
                'message': str(exc),
            }

    def _create_log(
        self,
        notification: Notification,
        channel: str,
        success: bool,
        response_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> NotificationLog:
        """Create a notification delivery log."""
        return NotificationLog.objects.create(
            organization=notification.organization,
            created_by=notification.sender,
            notification=notification,
            channel=channel,
            status='success' if success else 'failed',
            request_data=notification.data,
            response_data=response_data or {},
            error_code='' if success else 'DELIVERY_FAILED',
            error_message=error_message,
            retry_count=notification.retry_count,
            external_status='success' if success else 'failed',
        )

    def _prepare_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build a safe formatting context for notification templates."""
        due_date = context.get('due_date')
        completed_at = context.get('completed_at') or context.get('updated_at')
        business_reference = context.get('business_no') or context.get('business_id') or 'N/A'
        completed_by = context.get('completed_by')

        return {
            **context,
            'task_name': context.get('task_name') or context.get('node_name') or 'Workflow task',
            'workflow_name': context.get('workflow_name') or context.get('title') or 'Workflow',
            'instance_no': context.get('instance_no') or context.get('business_no') or '',
            'business_reference': business_reference,
            'priority_label': str(context.get('priority') or 'normal').upper(),
            'due_date_label': self._format_datetime(due_date, fallback='No due date'),
            'completed_at_label': self._format_datetime(completed_at, fallback='Not completed'),
            'completed_by_name': self._resolve_user_name(completed_by) or context.get('completed_by_name') or 'Workflow system',
            'task_result': context.get('task_result') or context.get('status') or 'Completed',
            'reason': context.get('reason') or 'No reason provided',
        }

    def _build_actions(
        self,
        template: WorkflowNotificationTemplate,
        context: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """Build action links for rich notification content."""
        actions = []
        primary_link = context.get('approval_link') or context.get('detail_link')
        if primary_link:
            actions.append({
                'label': template.action_label,
                'url': str(primary_link),
                'type': 'primary',
            })

        mobile_link = context.get('mobile_link')
        if mobile_link:
            actions.append({
                'label': 'Open on mobile',
                'url': str(mobile_link),
                'type': 'secondary',
            })

        return actions

    def _build_metrics(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build compact metric rows for UI rendering."""
        metrics = []
        for label, value in (
            ('Workflow', context.get('workflow_name')),
            ('Document', context.get('business_reference')),
            ('Priority', context.get('priority_label')),
            ('Due', context.get('due_date_label')),
        ):
            if value:
                metrics.append({
                    'label': label,
                    'value': str(value),
                })
        return metrics

    def _render_html_content(self, title: str, rich_content: Dict[str, Any]) -> str:
        """Render lightweight HTML content for email delivery."""
        actions_html = ''.join(
            f'<li><a href="{escape(action["url"])}">{escape(action["label"])}</a></li>'
            for action in rich_content.get('actions', [])
        )
        metrics_html = ''.join(
            f'<li><strong>{escape(item["label"])}:</strong> {escape(item["value"])}</li>'
            for item in rich_content.get('metrics', [])
        )
        return (
            f'<h3>{escape(title)}</h3>'
            f'<p>{escape(rich_content.get("summary", ""))}</p>'
            f'<p>{escape(rich_content.get("body", ""))}</p>'
            f'<ul>{metrics_html}</ul>'
            f'<ul>{actions_html}</ul>'
        )

    def _format_datetime(self, value: Any, fallback: str) -> str:
        """Format a datetime-like value for display."""
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d %H:%M')
        return fallback

    def _to_json_safe(self, value: Any) -> Any:
        """Normalize rich notification context for JSON storage."""
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()
        if isinstance(value, Model):
            return str(value.pk)
        if isinstance(value, dict):
            return {
                str(key): self._to_json_safe(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple, set)):
            return [self._to_json_safe(item) for item in value]
        if hasattr(value, 'isoformat') and callable(value.isoformat):
            return value.isoformat()
        return str(value)

    @staticmethod
    def _resolve_user_name(value: Any) -> str:
        """Resolve a user-like object to a display name."""
        if not value:
            return ''
        full_name = getattr(value, 'get_full_name', None)
        if callable(full_name):
            resolved = full_name()
            if resolved:
                return resolved
        return getattr(value, 'username', '') or str(value)

    def _is_in_quiet_hours(self, quiet_hours: Dict[str, Any]) -> bool:
        """Check if the current time falls inside quiet hours."""
        if not quiet_hours.get('enabled'):
            return False

        start = user_preferences_service._parse_time_string(quiet_hours.get('start'))
        end = user_preferences_service._parse_time_string(quiet_hours.get('end'))
        if not start or not end:
            return False

        now = timezone.localtime().time().replace(second=0, microsecond=0)
        if start <= end:
            return start <= now <= end
        return now >= start or now <= end

    def _build_task_context(self, task: Any) -> Dict[str, Any]:
        """Create notification context from a workflow task."""
        instance = task.instance
        return {
            'task_name': task.node_name or task.node_id,
            'workflow_name': instance.definition.name,
            'business_id': instance.business_id,
            'business_no': instance.business_no,
            'instance_no': instance.instance_no,
            'priority': task.priority or instance.priority,
            'due_date': task.due_date,
            'status': task.status,
            'approval_link': f'/workflows/tasks/{task.id}',
            'detail_link': f'/workflows/instances/{instance.id}',
        }

    def _build_instance_context(self, instance: Any) -> Dict[str, Any]:
        """Create notification context from a workflow instance."""
        return {
            'workflow_name': instance.definition.name,
            'business_id': instance.business_id,
            'business_no': instance.business_no,
            'instance_no': instance.instance_no,
            'priority': instance.priority,
            'completed_at': instance.completed_at,
            'status': instance.status,
            'detail_link': f'/workflows/instances/{instance.id}',
        }


enhanced_notification_service = EnhancedNotificationService()
