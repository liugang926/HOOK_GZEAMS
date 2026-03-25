"""
Tests for workflow UX services.
"""
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.notifications.models import Notification
from apps.users.services.user_preferences import user_preferences_service
from apps.workflows.services.onboarding import onboarding_service
from apps.workflows.services.notifications import enhanced_notification_service


@pytest.mark.django_db
class TestOnboardingService:
    """Verify workflow onboarding checklist behavior."""

    def test_marks_steps_complete_and_tracks_progress(self, user):
        """Checklist progress should advance as steps are completed."""
        checklist = onboarding_service.mark_step_complete(
            user,
            'open_workflow_workspace',
            metadata={'source': 'dashboard'},
            actor=user,
        )

        assert checklist['summary']['completed_steps'] == 1
        assert checklist['summary']['progress_percent'] > 0
        assert checklist['next_step']['code'] == 'personalize_workflow_view'
        assert checklist['steps'][0]['metadata']['source'] == 'dashboard'

    def test_records_known_events(self, user):
        """Known workflow UX events should complete the mapped onboarding step."""
        checklist = onboarding_service.record_event(
            user,
            'workflow_notifications_configured',
            actor=user,
        )

        configured_step = next(
            step for step in checklist['steps']
            if step['code'] == 'configure_notifications'
        )
        assert configured_step['is_completed'] is True


@pytest.mark.django_db
class TestEnhancedNotificationService:
    """Verify rich workflow notifications."""

    def test_build_payload_contains_rich_content(self):
        """Payload should include rich content metadata for UI rendering."""
        payload = enhanced_notification_service.build_payload(
            'task_assigned',
            {
                'task_name': 'Approve transfer',
                'workflow_name': 'Asset Transfer',
                'business_no': 'AT-001',
                'priority': 'high',
                'due_date': timezone.now(),
                'approval_link': '/workflows/tasks/1',
            },
        )

        assert payload['title'] == 'Approval required: Approve transfer'
        assert payload['data']['rich_content']['badge'] == 'Assigned'
        assert payload['data']['rich_content']['actions'][0]['url'] == '/workflows/tasks/1'

    @patch('apps.workflows.services.notifications.send_mail')
    def test_send_uses_delivery_preferences(self, mock_send_mail, user):
        """Disabled email should keep delivery on inbox only."""
        user_preferences_service.update_notification_preferences(
            user,
            {
                'channels': {
                    'email': False,
                },
                'event_channels': {
                    'task_assigned': ['inbox'],
                },
            },
            actor=user,
        )

        result = enhanced_notification_service.send(
            event_type='task_assigned',
            recipient=user,
            context={
                'task_name': 'Approve transfer',
                'workflow_name': 'Asset Transfer',
                'business_no': 'AT-001',
                'priority': 'high',
                'approval_link': '/workflows/tasks/1',
            },
            sender=user,
        )

        notifications = Notification.all_objects.filter(
            recipient=user,
            notification_type='task_assigned',
            is_deleted=False,
        )

        assert result['success'] is True
        assert result['summary']['total'] == 1
        assert notifications.count() == 1
        assert notifications.first().channel == 'inbox'
        mock_send_mail.assert_not_called()

    @patch('apps.workflows.services.notifications.send_mail')
    def test_notify_task_assigned_supports_task_objects(self, mock_send_mail, user):
        """Task helper should derive context and send notifications."""
        mock_send_mail.return_value = 1
        task = SimpleNamespace(
            id='task-1',
            node_id='approve',
            node_name='Approval Node',
            assignee=user,
            due_date=timezone.now(),
            priority='normal',
            status='pending',
            instance=SimpleNamespace(
                id='instance-1',
                instance_no='WF-001',
                business_id='business-1',
                business_no='AT-001',
                priority='normal',
                definition=SimpleNamespace(name='Asset Transfer'),
            ),
        )

        result = enhanced_notification_service.notify_task_assigned(task)

        assert result['success'] is True
        assert result['summary']['total'] >= 1
