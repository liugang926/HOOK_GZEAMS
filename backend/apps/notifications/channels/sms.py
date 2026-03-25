"""
SMS Channel Adapter

Handles SMS notifications via SMS gateway services.
Supports multiple SMS providers (Twilio, Alibaba Cloud, etc.).
"""
import time
import re
from typing import Optional, Dict, Any
from django.conf import settings
from django.utils import timezone
from .base import (
    NotificationChannel,
    NotificationMessage,
    SendResult,
    ChannelStatus,
    NonRetryableError,
)


class SMSChannel(NotificationChannel):
    """
    SMS notification channel.

    Sends SMS messages via configured SMS gateway service.
    Default implementation supports Alibaba Cloud SMS (Aliyun).
    Can be extended for other providers (Twilio, etc.).
    """

    channel_type = "sms"
    channel_name = "SMS"

    # Phone number validation (supports international format)
    PHONE_REGEX = re.compile(r'^\+?[1-9]\d{1,14}$')

    def __init__(self):
        """Initialize SMS channel with provider configuration."""
        super().__init__()
        self.provider = getattr(settings, 'SMS_PROVIDER', 'aliyun')
        self.access_key = getattr(settings, 'SMS_ACCESS_KEY', '')
        self.access_key_secret = getattr(settings, 'SMS_ACCESS_KEY_SECRET', '')
        self.sign_name = getattr(settings, 'SMS_SIGN_NAME', '')
        self.endpoint = getattr(settings, 'SMS_ENDPOINT', 'dysmsapi.aliyuncs.com')

    def validate_recipient(self, recipient: str) -> bool:
        """
        Validate recipient is a valid phone number.

        Args:
            recipient: Phone number (international format preferred)

        Returns:
            True if phone number is valid format
        """
        # Remove spaces, dashes, etc.
        cleaned = re.sub(r'[\s\-\(\)]', '', recipient)
        return bool(self.PHONE_REGEX.match(cleaned))

    def send(self, message: NotificationMessage) -> SendResult:
        """
        Send SMS notification.

        Args:
            message: NotificationMessage to send

        Returns:
            SendResult with send details
        """
        start_time = time.time()

        try:
            # Clean phone number
            phone_number = self._clean_phone_number(message.recipient)

            # Route to provider-specific implementation
            if self.provider == 'aliyun':
                result = self._send_aliyun(message, phone_number)
            elif self.provider == 'twilio':
                result = self._send_twilio(message, phone_number)
            elif self.provider == 'tencent':
                result = self._send_tencent(message, phone_number)
            else:
                # Mock send for testing without provider
                result = self._send_mock(message, phone_number)

            result.duration_ms = int((time.time() - start_time) * 1000)
            return result

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return SendResult(
                success=False,
                status=ChannelStatus.FAILED,
                message=f"Failed to send SMS: {str(e)}",
                error_code="SEND_FAILED",
                error_message=str(e),
                duration_ms=duration_ms,
            )

    def format_message(self, message: NotificationMessage) -> dict:
        """
        Format message for SMS sending.

        Args:
            message: NotificationMessage to format

        Returns:
            Dictionary with formatted SMS data
        """
        return {
            'phone_number': self._clean_phone_number(message.recipient),
            'content': self._truncate_content(message.content),
            'sign_name': self.sign_name,
            'template_code': message.data.get('sms_template_code'),
            'template_param': message.data.get('sms_template_param', {}),
        }

    def _clean_phone_number(self, phone: str) -> str:
        """
        Clean and format phone number.

        Args:
            phone: Raw phone number

        Returns:
            Cleaned phone number
        """
        # Remove all non-numeric characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)

        # Ensure international format
        if not cleaned.startswith('+'):
            # Default to China country code if not specified
            cleaned = '+86' + cleaned

        return cleaned

    def _truncate_content(self, content: str, max_length: int = 500) -> str:
        """
        Truncate content to fit SMS length limits.

        Args:
            content: Original content
            max_length: Maximum length

        Returns:
            Truncated content
        """
        if len(content) <= max_length:
            return content
        return content[:max_length - 3] + '...'

    def _send_aliyun(self, message: NotificationMessage, phone_number: str) -> SendResult:
        """
        Send SMS via Alibaba Cloud (Aliyun).

        Args:
            message: NotificationMessage to send
            phone_number: Cleaned phone number

        Returns:
            SendResult
        """
        try:
            # Check if aliyun-sdk is available
            from aliyunsdkcore.client import AcsClient
            from aliyunsdkdysmsapi.request.v20170525 import SendSmsRequest
            import json

            # Initialize client
            client = AcsClient(
                self.access_key,
                self.access_key_secret,
                'cn-hangzhou'
            )

            # Create request
            request = SendSmsRequest.SendSmsRequest()
            request.set_PhoneNumbers(phone_number)
            request.set_SignName(self.sign_name)
            request.set_TemplateCode(message.data.get('sms_template_code', 'SMS_DEFAULT'))

            # Set template parameters
            template_param = message.data.get('sms_template_param', {})
            if template_param:
                request.set_TemplateParam(json.dumps(template_param))

            # Send request
            response = client.do_action_with_exception(request)

            # Parse response
            response_data = json.loads(response.decode('utf-8'))

            if response_data.get('Code') == 'OK':
                return SendResult(
                    success=True,
                    status=ChannelStatus.SUCCESS,
                    message=f"SMS sent to {phone_number}",
                    external_id=response_data.get('BizId'),
                    response_data=response_data,
                )
            else:
                return SendResult(
                    success=False,
                    status=ChannelStatus.FAILED,
                    message=f"Aliyun SMS failed: {response_data.get('Message')}",
                    error_code=response_data.get('Code'),
                    error_message=response_data.get('Message'),
                    response_data=response_data,
                )

        except ImportError:
            # Aliyun SDK not installed, fall back to mock
            return self._send_mock(message, phone_number, error="Aliyun SDK not installed")

        except Exception as e:
            return SendResult(
                success=False,
                status=ChannelStatus.FAILED,
                message=f"Aliyun SMS error: {str(e)}",
                error_code="ALIYUN_ERROR",
                error_message=str(e),
            )

    def _send_twilio(self, message: NotificationMessage, phone_number: str) -> SendResult:
        """
        Send SMS via Twilio.

        Args:
            message: NotificationMessage to send
            phone_number: Cleaned phone number

        Returns:
            SendResult
        """
        try:
            from twilio.rest import Client

            account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
            auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
            from_number = getattr(settings, 'TWILIO_FROM_NUMBER', '')

            client = Client(account_sid, auth_token)

            twilio_message = client.messages.create(
                body=message.content,
                from_=from_number,
                to=phone_number
            )

            return SendResult(
                success=True,
                status=ChannelStatus.SUCCESS,
                message=f"SMS sent to {phone_number}",
                external_id=twilio_message.sid,
                response_data={
                    'sid': twilio_message.sid,
                    'status': twilio_message.status,
                },
            )

        except ImportError:
            return self._send_mock(message, phone_number, error="Twilio SDK not installed")

        except Exception as e:
            return SendResult(
                success=False,
                status=ChannelStatus.FAILED,
                message=f"Twilio SMS error: {str(e)}",
                error_code="TWILIO_ERROR",
                error_message=str(e),
            )

    def _send_tencent(self, message: NotificationMessage, phone_number: str) -> SendResult:
        """
        Send SMS via Tencent Cloud.

        Args:
            message: NotificationMessage to send
            phone_number: Cleaned phone number

        Returns:
            SendResult
        """
        # Tencent Cloud SMS implementation
        # Placeholder for future implementation
        return self._send_mock(message, phone_number, error="Tencent SMS not implemented")

    def _send_mock(self, message: NotificationMessage, phone_number: str, error: str = None) -> SendResult:
        """
        Mock SMS send for testing without provider.

        Args:
            message: NotificationMessage to send
            phone_number: Cleaned phone number
            error: Optional error message

        Returns:
            Mock SendResult
        """
        import uuid

        if error:
            return SendResult(
                success=False,
                status=ChannelStatus.FAILED,
                message=f"Mock SMS failed: {error}",
                error_code="MOCK_ERROR",
                error_message=error,
            )

        # Log mock send for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[MOCK SMS] To: {phone_number}, Content: {message.content[:50]}...")

        return SendResult(
            success=True,
            status=ChannelStatus.SUCCESS,
            message=f"Mock SMS sent to {phone_number}",
            external_id=f"mock_{uuid.uuid4()}",
            response_data={'mock': True, 'phone': phone_number},
        )

    def validate_message(self, message: NotificationMessage) -> tuple[bool, Optional[str]]:
        """
        Validate SMS message before sending.

        Args:
            message: NotificationMessage to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Base validation
        is_valid, error_msg = super().validate_message(message)
        if not is_valid:
            return False, error_msg

        # Phone number validation
        if not self.validate_recipient(message.recipient):
            return False, f"Invalid phone number: {message.recipient}"

        # Content length validation
        if len(message.content) > 500:
            return False, "SMS content exceeds maximum length of 500 characters"

        return True, None
