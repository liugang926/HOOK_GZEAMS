"""
Notifications Module - Unified Notification Service

Provides a unified notification framework for GZEAMS system.
Supports multiple channels: inbox, email, SMS, WeWork, DingTalk, Feishu.

Features:
- Template-based notification rendering
- Multi-channel delivery
- Retry mechanism with exponential backoff
- User notification preferences
- Quiet hours support
"""
default_app_config = 'apps.notifications.apps.NotificationsConfig'
