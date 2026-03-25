"""
Base Channel Adapter

Defines the abstract interface for all notification channel adapters.
All channel implementations must inherit from NotificationChannel.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class ChannelStatus(Enum):
    """Channel delivery status."""
    PENDING = "pending"
    SENDING = "sending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class NotificationMessage:
    """
    Unified notification message format.

    All channel adapters work with this standardized message format.
    """
    recipient: str  # Recipient identifier (email, phone, user_id, etc.)
    subject: str  # Message subject/title
    content: str  # Message body/content
    data: Dict[str, Any] = field(default_factory=dict)  # Additional metadata
    html_content: Optional[str] = None  # HTML version (for email)
    sender_name: Optional[str] = None  # Sender display name
    reply_to: Optional[str] = None  # Reply-to address
    attachments: list = field(default_factory=list)  # File attachments
    priority: str = "normal"  # Message priority
    external_id: Optional[str] = None  # External tracking ID


@dataclass
class SendResult:
    """
    Result of a notification send attempt.

    Used by channel adapters to return standardized results.
    """
    success: bool  # Whether send was successful
    status: ChannelStatus  # Detailed status
    message: str  # Human-readable result message
    external_id: Optional[str] = None  # External message ID
    error_code: Optional[str] = None  # Error code if failed
    error_message: Optional[str] = None  # Detailed error message
    duration_ms: Optional[int] = None  # Send duration in milliseconds
    response_data: Optional[Dict[str, Any]] = None  # Raw response data


class NotificationChannel(ABC):
    """
    Abstract base class for notification channel adapters.

    All channel implementations (Email, SMS, WeWork, etc.) must inherit
    from this class and implement the required methods.

    Channel adapters are responsible for:
    1. Validating recipient addresses
    2. Formatting messages for the specific channel
    3. Sending messages via the channel's API/service
    4. Returning standardized SendResult objects
    5. Handling retries with exponential backoff
    """

    channel_type: str = "base"  # Channel identifier
    channel_name: str = "Base Channel"  # Human-readable name

    @abstractmethod
    def validate_recipient(self, recipient: str) -> bool:
        """
        Validate recipient address for this channel.

        Args:
            recipient: Recipient identifier (email, phone, etc.)

        Returns:
            True if recipient is valid for this channel
        """
        pass

    @abstractmethod
    def send(self, message: NotificationMessage) -> SendResult:
        """
        Send a notification message via this channel.

        Args:
            message: NotificationMessage to send

        Returns:
            SendResult with send attempt details
        """
        pass

    @abstractmethod
    def format_message(self, message: NotificationMessage) -> Any:
        """
        Format message for this channel's API.

        Args:
            message: NotificationMessage to format

        Returns:
            Channel-specific formatted message
        """
        pass

    def get_retry_delay(self, retry_count: int, max_retries: int = 3) -> int:
        """
        Calculate retry delay with exponential backoff.

        Uses exponential backoff: delay = base_delay * (2 ^ retry_count)

        Args:
            retry_count: Current retry attempt number
            max_retries: Maximum retry attempts allowed

        Returns:
            Delay in seconds before next retry
        """
        if retry_count >= max_retries:
            return 0  # No more retries

        base_delay = 60  # 1 minute base delay
        max_delay = 3600  # 1 hour max delay

        delay = min(base_delay * (2 ** retry_count), max_delay)
        return delay

    def should_retry(self, result: SendResult, retry_count: int, max_retries: int = 3) -> bool:
        """
        Determine if a failed send should be retried.

        Args:
            result: SendResult from previous attempt
            retry_count: Current retry attempt number
            max_retries: Maximum retry attempts allowed

        Returns:
            True if should retry
        """
        if retry_count >= max_retries:
            return False

        # Don't retry on certain errors (e.g., invalid recipient, blocked)
        non_retryable_errors = [
            "INVALID_RECIPIENT",
            "BLOCKED",
            "UNSUBSCRIBED",
            "RATE_LIMIT_EXCEEDED",
        ]

        if result.error_code in non_retryable_errors:
            return False

        return not result.success

    def prepare_attachments(self, message: NotificationMessage) -> list:
        """
        Prepare attachments for sending.

        Args:
            message: NotificationMessage with attachments

        Returns:
            List of prepared attachment data
        """
        # Base implementation returns empty list
        # Override in channel-specific implementations
        return []

    def sanitize_content(self, content: str) -> str:
        """
        Sanitize message content for security.

        Args:
            content: Raw content

        Returns:
            Sanitized content
        """
        # Basic sanitization - override in specific channels
        import html
        return html.escape(content, quote=False)

    def validate_message(self, message: NotificationMessage) -> tuple[bool, Optional[str]]:
        """
        Validate message before sending.

        Args:
            message: NotificationMessage to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not message.recipient:
            return False, "Recipient is required"

        if not message.subject and not message.content:
            return False, "Subject or content is required"

        if not self.validate_recipient(message.recipient):
            return False, f"Invalid recipient for {self.channel_name} channel"

        return True, None

    def send_with_validation(self, message: NotificationMessage) -> SendResult:
        """
        Send message with pre-send validation.

        Args:
            message: NotificationMessage to send

        Returns:
            SendResult with send attempt details
        """
        # Validate message
        is_valid, error_msg = self.validate_message(message)
        if not is_valid:
            return SendResult(
                success=False,
                status=ChannelStatus.FAILED,
                message=error_msg or "Message validation failed",
                error_code="VALIDATION_ERROR",
                error_message=error_msg,
            )

        # Send the message
        return self.send(message)


class RetryableError(Exception):
    """Error that should trigger a retry."""
    pass


class NonRetryableError(Exception):
    """Error that should NOT trigger a retry."""
    pass


class ChannelConfigurationError(Exception):
    """Channel configuration error."""
    pass
