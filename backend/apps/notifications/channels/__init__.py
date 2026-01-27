"""
Notification Channels Package

Provides channel adapters for different notification delivery methods.
"""
from .base import (
    NotificationChannel,
    NotificationMessage,
    SendResult,
    ChannelStatus,
    RetryableError,
    NonRetryableError,
    ChannelConfigurationError,
)
from .inbox import InboxChannel
from .email import EmailChannel
from .sms import SMSChannel
from .wework import WeWorkChannel
from .dingtalk import DingTalkChannel


# Channel registry - maps channel types to their adapter classes
CHANNEL_REGISTRY = {
    'inbox': InboxChannel,
    'email': EmailChannel,
    'sms': SMSChannel,
    'wework': WeWorkChannel,
    'dingtalk': DingTalkChannel,
}


def get_channel(channel_type: str) -> NotificationChannel:
    """
    Get channel adapter instance for given channel type.

    Args:
        channel_type: Channel type identifier (inbox, email, sms, etc.)

    Returns:
        Channel adapter instance

    Raises:
        ValueError: If channel type is not supported
    """
    channel_class = CHANNEL_REGISTRY.get(channel_type)
    if not channel_class:
        raise ValueError(
            f"Unsupported channel type: {channel_type}. "
            f"Supported channels: {', '.join(CHANNEL_REGISTRY.keys())}"
        )
    return channel_class()


def get_supported_channels() -> list[str]:
    """
    Get list of supported channel types.

    Returns:
        List of channel type identifiers
    """
    return list(CHANNEL_REGISTRY.keys())


def register_channel(channel_type: str, channel_class: type) -> None:
    """
    Register a custom channel adapter.

    Allows third-party apps to add their own channel adapters.

    Args:
        channel_type: Channel type identifier
        channel_class: Channel adapter class (must inherit from NotificationChannel)
    """
    if not issubclass(channel_class, NotificationChannel):
        raise ValueError(
            f"Channel class must inherit from NotificationChannel, "
            f"got {channel_class.__name__}"
        )
    CHANNEL_REGISTRY[channel_type] = channel_class


__all__ = [
    # Base classes
    'NotificationChannel',
    'NotificationMessage',
    'SendResult',
    'ChannelStatus',
    'RetryableError',
    'NonRetryableError',
    'ChannelConfigurationError',
    # Channel implementations
    'InboxChannel',
    'EmailChannel',
    'SMSChannel',
    'WeWorkChannel',
    'DingTalkChannel',
    # Registry functions
    'get_channel',
    'get_supported_channels',
    'register_channel',
    'CHANNEL_REGISTRY',
]
