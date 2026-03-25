"""
Tests for user preference service UX helpers.
"""
import pytest

from apps.notifications.models import NotificationConfig
from apps.users.services.user_preferences import user_preferences_service


@pytest.mark.django_db
class TestUserPreferencesService:
    """Verify persisted UX preference behavior."""

    def test_returns_default_preferences(self, user):
        """Default UX settings should be available without prior persistence."""
        preferences = user_preferences_service.get_preferences(user)

        assert preferences['dashboard_layout']['density'] == 'comfortable'
        assert preferences['theme']['mode'] == 'system'
        assert preferences['workflow_display']['default_view'] == 'list'
        assert preferences['notification_preferences']['channels']['inbox'] is True
        assert preferences['notification_preferences']['event_channels']['task_assigned'] == ['inbox', 'email']

    def test_updates_notification_preferences_and_syncs_notification_config(self, user):
        """Updating delivery settings should also update NotificationConfig."""
        preferences = user_preferences_service.update_notification_preferences(
            user,
            {
                'channels': {
                    'email': False,
                    'wework': False,
                },
                'event_channels': {
                    'task_assigned': ['inbox'],
                },
                'workflow_events': {
                    'task_completed': False,
                },
                'quiet_hours': {
                    'enabled': True,
                    'start': '21:30',
                    'end': '07:30',
                },
            },
            actor=user,
        )

        config = NotificationConfig.all_objects.get(user=user)
        assert preferences['channels']['email'] is False
        assert config.enable_email is False
        assert config.enable_wework is False
        assert config.quiet_hours_enabled is True
        assert config.quiet_hours_start.strftime('%H:%M') == '21:30'
        assert config.channel_settings['task_assigned']['inbox'] is True
        assert config.channel_settings['task_assigned']['email'] is False
        assert config.channel_settings['task_completed']['inbox'] is False

    def test_updates_theme_and_workflow_display_preferences(self, user):
        """Theme and workflow display settings should be persisted in custom_fields."""
        theme = user_preferences_service.update_theme_selection(
            user,
            {
                'mode': 'dark',
                'accent': 'teal',
                'high_contrast': True,
            },
            actor=user,
        )
        workflow_display = user_preferences_service.update_workflow_display_settings(
            user,
            {
                'default_view': 'kanban',
                'group_by': 'priority',
                'show_activity_timeline': False,
            },
            actor=user,
        )

        user.refresh_from_db()
        assert theme['mode'] == 'dark'
        assert workflow_display['default_view'] == 'kanban'
        assert workflow_display['group_by'] == 'priority'
        assert user.custom_fields['ux_preferences']['theme']['accent'] == 'teal'
        assert user.custom_fields['ux_preferences']['workflow_display']['show_activity_timeline'] is False
