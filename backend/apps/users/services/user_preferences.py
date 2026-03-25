"""
User preference service for UX customization.

Stores lightweight user experience settings on the User.custom_fields
namespace while synchronizing delivery-related fields with NotificationConfig.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import time
from typing import Any, Dict, Optional

from django.db import transaction

from apps.accounts.models import User
from apps.notifications.models import NotificationConfig


class UserPreferencesService:
    """
    Manage persisted user experience preferences.

    Preferences are stored under a dedicated custom_fields namespace so the
    sprint can add UX behavior without introducing new schema.
    """

    STORAGE_KEY = 'ux_preferences'
    SUPPORTED_CHANNELS = ('inbox', 'email', 'sms', 'wework', 'dingtalk')
    WORKFLOW_EVENTS = (
        'task_assigned',
        'task_completed',
        'task_overdue',
        'workflow_completed',
        'workflow_rejected',
        'workflow_cancelled',
    )

    DEFAULT_EVENT_CHANNELS = {
        'task_assigned': ['inbox', 'email'],
        'task_completed': ['inbox'],
        'task_overdue': ['inbox', 'email'],
        'workflow_completed': ['inbox'],
        'workflow_rejected': ['inbox', 'email'],
        'workflow_cancelled': ['inbox'],
    }

    THEME_MODES = {'light', 'dark', 'system'}
    THEME_ACCENTS = {'default', 'blue', 'green', 'amber', 'teal'}
    DASHBOARD_DENSITIES = {'comfortable', 'compact'}
    WORKFLOW_VIEWS = {'list', 'kanban', 'timeline'}
    WORKFLOW_GROUPINGS = {'status', 'priority', 'due_date', 'assignee'}
    DIGEST_FREQUENCIES = {'off', 'daily', 'weekly'}

    def get_preferences(self, user: User) -> Dict[str, Any]:
        """
        Return fully hydrated preferences for a user.
        """
        stored = self._get_stored_preferences(user)
        preferences = self._deep_merge(self._get_default_preferences(), stored)
        preferences = self._normalize_preferences(preferences)
        preferences['notification_preferences'] = self._hydrate_notification_preferences(
            user,
            preferences['notification_preferences'],
        )
        return preferences

    def update_preferences(
        self,
        user: User,
        updates: Dict[str, Any],
        actor: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        Merge and persist a partial preference payload.
        """
        current = self.get_preferences(user)
        merged = self._deep_merge(current, updates or {})
        normalized = self._normalize_preferences(merged)

        with transaction.atomic():
            self._save_preferences(user, normalized, actor=actor)
            self._sync_notification_config(
                user,
                normalized['notification_preferences'],
                actor=actor,
            )

        return normalized

    def get_dashboard_layout(self, user: User) -> Dict[str, Any]:
        """Get dashboard layout preferences."""
        return self.get_preferences(user)['dashboard_layout']

    def update_dashboard_layout(
        self,
        user: User,
        layout: Dict[str, Any],
        actor: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Update dashboard layout preferences."""
        return self.update_preferences(
            user,
            {'dashboard_layout': layout},
            actor=actor,
        )['dashboard_layout']

    def get_notification_preferences(self, user: User) -> Dict[str, Any]:
        """Get notification preferences."""
        return self.get_preferences(user)['notification_preferences']

    def update_notification_preferences(
        self,
        user: User,
        preferences: Dict[str, Any],
        actor: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Update notification preferences."""
        return self.update_preferences(
            user,
            {'notification_preferences': preferences},
            actor=actor,
        )['notification_preferences']

    def get_theme_selection(self, user: User) -> Dict[str, Any]:
        """Get theme selection preferences."""
        return self.get_preferences(user)['theme']

    def update_theme_selection(
        self,
        user: User,
        theme: Dict[str, Any],
        actor: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Update theme selection preferences."""
        return self.update_preferences(
            user,
            {'theme': theme},
            actor=actor,
        )['theme']

    def get_workflow_display_settings(self, user: User) -> Dict[str, Any]:
        """Get workflow display preferences."""
        return self.get_preferences(user)['workflow_display']

    def update_workflow_display_settings(
        self,
        user: User,
        settings: Dict[str, Any],
        actor: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Update workflow display preferences."""
        return self.update_preferences(
            user,
            {'workflow_display': settings},
            actor=actor,
        )['workflow_display']

    def _get_default_preferences(self) -> Dict[str, Any]:
        """Return a fresh default preference payload."""
        return {
            'dashboard_layout': {
                'widgets': [
                    'pending_tasks',
                    'workflow_summary',
                    'recent_notifications',
                ],
                'sections': [],
                'density': 'comfortable',
                'show_quick_actions': True,
                'show_welcome_panel': True,
            },
            'notification_preferences': {
                'channels': {
                    'inbox': True,
                    'email': True,
                    'sms': False,
                    'wework': True,
                    'dingtalk': False,
                },
                'event_channels': deepcopy(self.DEFAULT_EVENT_CHANNELS),
                'workflow_events': {
                    event: True for event in self.WORKFLOW_EVENTS
                },
                'desktop_enabled': True,
                'sound_enabled': False,
                'digest_frequency': 'daily',
                'quiet_hours': {
                    'enabled': False,
                    'start': '22:00',
                    'end': '08:00',
                },
            },
            'theme': {
                'mode': 'system',
                'accent': 'default',
                'high_contrast': False,
            },
            'workflow_display': {
                'default_view': 'list',
                'group_by': 'status',
                'show_completed_steps': True,
                'show_activity_timeline': True,
                'show_filters_panel': True,
            },
        }

    def _get_stored_preferences(self, user: User) -> Dict[str, Any]:
        """Get stored preference payload from custom_fields."""
        custom_fields = user.custom_fields or {}
        stored = custom_fields.get(self.STORAGE_KEY, {})
        return stored if isinstance(stored, dict) else {}

    def _save_preferences(
        self,
        user: User,
        preferences: Dict[str, Any],
        actor: Optional[User] = None,
    ) -> None:
        """Persist preference payload to user.custom_fields."""
        payload = dict(user.custom_fields or {})
        payload[self.STORAGE_KEY] = preferences
        user.custom_fields = payload

        update_fields = ['custom_fields', 'updated_at']
        if actor is not None:
            user.updated_by = actor
            update_fields.append('updated_by')
        user.save(update_fields=update_fields)

    def _hydrate_notification_preferences(
        self,
        user: User,
        preferences: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Merge NotificationConfig values into the preference payload."""
        hydrated = deepcopy(preferences)
        config = NotificationConfig.objects.filter(user=user).first()
        if not config:
            return hydrated

        channels = dict(hydrated.get('channels', {}))
        channels.update({
            'inbox': bool(config.enable_inbox),
            'email': bool(config.enable_email),
            'sms': bool(config.enable_sms),
            'wework': bool(config.enable_wework),
            'dingtalk': bool(config.enable_dingtalk),
        })
        hydrated['channels'] = channels

        hydrated['quiet_hours'] = {
            'enabled': bool(config.quiet_hours_enabled),
            'start': config.quiet_hours_start.strftime('%H:%M') if config.quiet_hours_start else hydrated['quiet_hours']['start'],
            'end': config.quiet_hours_end.strftime('%H:%M') if config.quiet_hours_end else hydrated['quiet_hours']['end'],
        }

        channel_settings = config.channel_settings or {}
        event_channels = dict(hydrated.get('event_channels', {}))
        workflow_events = dict(hydrated.get('workflow_events', {}))
        for event_name, channel_map in channel_settings.items():
            if not isinstance(channel_map, dict):
                continue
            enabled_channels = [
                channel_name
                for channel_name, is_enabled in channel_map.items()
                if channel_name in self.SUPPORTED_CHANNELS and bool(is_enabled)
            ]
            event_channels[event_name] = enabled_channels
            workflow_events[event_name] = bool(enabled_channels)

        hydrated['event_channels'] = event_channels
        hydrated['workflow_events'] = workflow_events
        return self._normalize_notification_preferences(hydrated)

    def _sync_notification_config(
        self,
        user: User,
        preferences: Dict[str, Any],
        actor: Optional[User] = None,
    ) -> NotificationConfig:
        """Synchronize delivery-related preferences to NotificationConfig."""
        organization = user.current_organization or user.organization
        config, _ = NotificationConfig.all_objects.get_or_create(
            user=user,
            defaults={
                'organization': organization,
                'created_by': user,
            },
        )

        channels = preferences.get('channels', {})
        quiet_hours = preferences.get('quiet_hours', {})
        workflow_events = preferences.get('workflow_events', {})
        event_channels = preferences.get('event_channels', {})

        config.organization = organization
        config.enable_inbox = bool(channels.get('inbox', True))
        config.enable_email = bool(channels.get('email', True))
        config.enable_sms = bool(channels.get('sms', False))
        config.enable_wework = bool(channels.get('wework', True))
        config.enable_dingtalk = bool(channels.get('dingtalk', False))
        config.quiet_hours_enabled = bool(quiet_hours.get('enabled', False))
        config.quiet_hours_start = self._parse_time_string(quiet_hours.get('start'))
        config.quiet_hours_end = self._parse_time_string(quiet_hours.get('end'))

        channel_settings = {}
        for event_name in self.WORKFLOW_EVENTS:
            allowed_channels = set(event_channels.get(event_name, []))
            is_event_enabled = bool(workflow_events.get(event_name, True))
            channel_settings[event_name] = {
                channel_name: (
                    is_event_enabled
                    and bool(channels.get(channel_name, False))
                    and channel_name in allowed_channels
                )
                for channel_name in self.SUPPORTED_CHANNELS
            }

        config.channel_settings = channel_settings
        config.updated_by = actor or user
        config.save()
        return config

    def _normalize_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize the complete preference payload."""
        normalized = self._deep_merge(self._get_default_preferences(), preferences or {})

        dashboard_layout = normalized.get('dashboard_layout', {})
        dashboard_layout['widgets'] = self._ensure_string_list(dashboard_layout.get('widgets'))
        dashboard_layout['sections'] = self._ensure_list(dashboard_layout.get('sections'))
        dashboard_layout['density'] = self._normalize_choice(
            dashboard_layout.get('density'),
            self.DASHBOARD_DENSITIES,
            'comfortable',
        )
        dashboard_layout['show_quick_actions'] = bool(dashboard_layout.get('show_quick_actions', True))
        dashboard_layout['show_welcome_panel'] = bool(dashboard_layout.get('show_welcome_panel', True))
        normalized['dashboard_layout'] = dashboard_layout

        normalized['notification_preferences'] = self._normalize_notification_preferences(
            normalized.get('notification_preferences', {})
        )

        theme = normalized.get('theme', {})
        theme['mode'] = self._normalize_choice(
            theme.get('mode'),
            self.THEME_MODES,
            'system',
        )
        theme['accent'] = self._normalize_choice(
            theme.get('accent'),
            self.THEME_ACCENTS,
            'default',
        )
        theme['high_contrast'] = bool(theme.get('high_contrast', False))
        normalized['theme'] = theme

        workflow_display = normalized.get('workflow_display', {})
        workflow_display['default_view'] = self._normalize_choice(
            workflow_display.get('default_view'),
            self.WORKFLOW_VIEWS,
            'list',
        )
        workflow_display['group_by'] = self._normalize_choice(
            workflow_display.get('group_by'),
            self.WORKFLOW_GROUPINGS,
            'status',
        )
        workflow_display['show_completed_steps'] = bool(
            workflow_display.get('show_completed_steps', True)
        )
        workflow_display['show_activity_timeline'] = bool(
            workflow_display.get('show_activity_timeline', True)
        )
        workflow_display['show_filters_panel'] = bool(
            workflow_display.get('show_filters_panel', True)
        )
        normalized['workflow_display'] = workflow_display

        return normalized

    def _normalize_notification_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize notification preference payload."""
        defaults = self._get_default_preferences()['notification_preferences']
        normalized = self._deep_merge(defaults, preferences or {})

        normalized['channels'] = {
            channel_name: bool(normalized.get('channels', {}).get(channel_name, defaults['channels'].get(channel_name, False)))
            for channel_name in self.SUPPORTED_CHANNELS
        }

        normalized['workflow_events'] = {
            event_name: bool(normalized.get('workflow_events', {}).get(event_name, True))
            for event_name in self.WORKFLOW_EVENTS
        }

        event_channels = {}
        raw_event_channels = normalized.get('event_channels', {})
        for event_name in self.WORKFLOW_EVENTS:
            has_explicit_value = event_name in raw_event_channels
            requested_channels = raw_event_channels.get(
                event_name,
                defaults['event_channels'][event_name],
            )
            normalized_channels = [
                channel_name
                for channel_name in self._ensure_string_list(requested_channels)
                if channel_name in self.SUPPORTED_CHANNELS
            ]
            event_channels[event_name] = (
                normalized_channels
                if has_explicit_value
                else (normalized_channels or list(defaults['event_channels'][event_name]))
            )
        normalized['event_channels'] = event_channels

        normalized['desktop_enabled'] = bool(normalized.get('desktop_enabled', True))
        normalized['sound_enabled'] = bool(normalized.get('sound_enabled', False))
        normalized['digest_frequency'] = self._normalize_choice(
            normalized.get('digest_frequency'),
            self.DIGEST_FREQUENCIES,
            'daily',
        )

        quiet_hours = normalized.get('quiet_hours', {})
        normalized['quiet_hours'] = {
            'enabled': bool(quiet_hours.get('enabled', False)),
            'start': self._format_time_value(quiet_hours.get('start'), fallback='22:00'),
            'end': self._format_time_value(quiet_hours.get('end'), fallback='08:00'),
        }
        return normalized

    @staticmethod
    def _deep_merge(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge two dictionaries."""
        merged = deepcopy(base)
        for key, value in (updates or {}).items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = UserPreferencesService._deep_merge(merged[key], value)
            else:
                merged[key] = deepcopy(value)
        return merged

    @staticmethod
    def _normalize_choice(value: Any, allowed_values: set[str], fallback: str) -> str:
        """Normalize a choice field against a known set."""
        candidate = str(value or fallback).lower()
        return candidate if candidate in allowed_values else fallback

    @staticmethod
    def _ensure_list(value: Any) -> list[Any]:
        """Normalize arbitrary input to a list."""
        if isinstance(value, list):
            return value
        if value in (None, ''):
            return []
        return [value]

    @staticmethod
    def _ensure_string_list(value: Any) -> list[str]:
        """Normalize input to a list of non-empty strings."""
        return [
            str(item).strip()
            for item in UserPreferencesService._ensure_list(value)
            if str(item).strip()
        ]

    @staticmethod
    def _parse_time_string(value: Any) -> Optional[time]:
        """Parse a HH:MM string into a time object."""
        if isinstance(value, time):
            return value
        if not isinstance(value, str) or ':' not in value:
            return None
        try:
            hours, minutes = value.split(':', 1)
            return time(hour=int(hours), minute=int(minutes))
        except (TypeError, ValueError):
            return None

    def _format_time_value(self, value: Any, fallback: str) -> str:
        """Normalize time-like input to HH:MM."""
        parsed = self._parse_time_string(value)
        if parsed:
            return parsed.strftime('%H:%M')
        return fallback


user_preferences_service = UserPreferencesService()
