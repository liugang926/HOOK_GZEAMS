"""
WeWork Channel Adapter

Handles WeWork (WeCom) notifications via WeWork API.
Supports text, markdown, and card message formats.
"""
import time
import hashlib
import hmac
import json
from typing import Optional, Dict, Any
from django.conf import settings
from django.utils import timezone
import requests
from .base import (
    NotificationChannel,
    NotificationMessage,
    SendResult,
    ChannelStatus,
    NonRetryableError,
)


class WeWorkChannel(NotificationChannel):
    """
    WeWork (WeCom) notification channel.

    Sends messages to WeWork users via WeWork Webhook API or API.
    Supports multiple message types: text, markdown, image, news, file, card.
    """

    channel_type = "wework"
    channel_name = "WeWork"

    # WeWork API endpoints
    WEBHOOK_URL_TEMPLATE = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}"
    MESSAGE_SEND_URL = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"

    def __init__(self):
        """Initialize WeWork channel with credentials."""
        super().__init__()
        self.corp_id = getattr(settings, 'WEWORK_CORP_ID', '')
        self.agent_id = getattr(settings, 'WEWORK_AGENT_ID', '')
        self.agent_secret = getattr(settings, 'WEWORK_AGENT_SECRET', '')
        self.webhook_key = getattr(settings, 'WEWORK_WEBHOOK_KEY', '')
        self.encoding_aes_key = getattr(settings, 'WEWORK_ENCODING_AES_KEY', '')

    def validate_recipient(self, recipient: str) -> bool:
        """
        Validate recipient is a valid WeWork user ID.

        Args:
            recipient: WeWork user ID or email

        Returns:
            True if recipient format is valid
        """
        # WeWork user IDs are typically alphanumeric
        # Also accept email as recipient
        if '@' in recipient:
            return '@' in recipient and '.' in recipient.split('@')[1]
        return len(recipient) > 0 and recipient.replace('-', '').replace('_', '').isalnum()

    def send(self, message: NotificationMessage) -> SendResult:
        """
        Send WeWork notification.

        Args:
            message: NotificationMessage to send

        Returns:
            SendResult with send details
        """
        start_time = time.time()

        try:
            # Prefer webhook if configured (simpler)
            if self.webhook_key:
                result = self._send_via_webhook(message)
            else:
                result = self._send_via_api(message)

            result.duration_ms = int((time.time() - start_time) * 1000)
            return result

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return SendResult(
                success=False,
                status=ChannelStatus.FAILED,
                message=f"Failed to send WeWork notification: {str(e)}",
                error_code="SEND_FAILED",
                error_message=str(e),
                duration_ms=duration_ms,
            )

    def format_message(self, message: NotificationMessage) -> dict:
        """
        Format message for WeWork API.

        Args:
            message: NotificationMessage to format

        Returns:
            Dictionary with WeWork message format
        """
        # Determine message type
        msg_type = message.data.get('msgtype', 'text')

        if msg_type == 'text':
            return {
                "msgtype": "text",
                "text": {
                    "content": message.content
                }
            }
        elif msg_type == 'markdown':
            return {
                "msgtype": "markdown",
                "markdown": {
                    "title": message.subject,
                    "text": message.content
                }
            }
        elif msg_type == 'textcard':
            return {
                "msgtype": "textcard",
                "textcard": {
                    "title": message.subject,
                    "description": message.content,
                    "url": message.data.get('url', ''),
                    "btntxt": message.data.get('button_text', '详情')
                }
            }
        elif msg_type == 'news':
            return {
                "msgtype": "news",
                "news": {
                    "articles": message.data.get('articles', [
                        {
                            "title": message.subject,
                            "description": message.content[:50],
                            "url": message.data.get('url', ''),
                            "picurl": message.data.get('pic_url', '')
                        }
                    ])
                }
            }
        else:
            # Default to text
            return {
                "msgtype": "text",
                "text": {
                    "content": f"{message.subject}\n\n{message.content}"
                }
            }

    def _send_via_webhook(self, message: NotificationMessage) -> SendResult:
        """
        Send via WeWork Webhook (simpler, recommended for alerts).

        Args:
            message: NotificationMessage to send

        Returns:
            SendResult
        """
        url = self.WEBHOOK_URL_TEMPLATE.format(key=self.webhook_key)

        # Format message
        wework_msg = self.format_message(message)

        # Add mentioned users if specified
        if message.data.get('mentioned_list'):
            if wework_msg['msgtype'] == 'text':
                wework_msg['text']['mentioned_list'] = message.data['mentioned_list']

        try:
            response = requests.post(
                url,
                json=wework_msg,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            response_data = response.json()

            if response_data.get('errcode') == 0:
                return SendResult(
                    success=True,
                    status=ChannelStatus.SUCCESS,
                    message=f"WeWork webhook sent successfully",
                    external_id=str(time.time()),
                    response_data=response_data,
                )
            else:
                error_code = response_data.get('errcode')
                error_msg = response_data.get('errmsg', 'Unknown error')

                # Determine if error is retryable
                if error_code in [45009, 45029, 45030]:  # Rate limit errors
                    return SendResult(
                        success=False,
                        status=ChannelStatus.RETRYING,
                        message=f"WeWork rate limit: {error_msg}",
                        error_code=f"RATE_LIMIT_{error_code}",
                        error_message=error_msg,
                        response_data=response_data,
                    )
                else:
                    return SendResult(
                        success=False,
                        status=ChannelStatus.FAILED,
                        message=f"WeWork webhook failed: {error_msg}",
                        error_code=f"WEWORK_{error_code}",
                        error_message=error_msg,
                        response_data=response_data,
                    )

        except requests.RequestException as e:
            return SendResult(
                success=False,
                status=ChannelStatus.FAILED,
                message=f"WeWork webhook request failed: {str(e)}",
                error_code="REQUEST_ERROR",
                error_message=str(e),
            )

    def _send_via_api(self, message: NotificationMessage) -> SendResult:
        """
        Send via WeWork API (requires access token).

        Args:
            message: NotificationMessage to send

        Returns:
            SendResult
        """
        # Get access token
        access_token = self._get_access_token()
        if not access_token:
            return SendResult(
                success=False,
                status=ChannelStatus.FAILED,
                message="Failed to get WeWork access token",
                error_code="AUTH_ERROR",
                error_message="Could not retrieve access token from WeWork API",
            )

        url = self.MESSAGE_SEND_URL.format(token=access_token)

        # Prepare message payload
        wework_msg = self.format_message(message)
        wework_msg['touser'] = message.recipient
        wework_msg['agentid'] = int(self.agent_id)

        try:
            response = requests.post(
                url,
                json=wework_msg,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            response_data = response.json()

            if response_data.get('errcode') == 0:
                return SendResult(
                    success=True,
                    status=ChannelStatus.SUCCESS,
                    message=f"WeWork message sent to {message.recipient}",
                    external_id=response_data.get('msgid'),
                    response_data=response_data,
                )
            else:
                return SendResult(
                    success=False,
                    status=ChannelStatus.FAILED,
                    message=f"WeWork API failed: {response_data.get('errmsg')}",
                    error_code=f"WEWORK_{response_data.get('errcode')}",
                    error_message=response_data.get('errmsg'),
                    response_data=response_data,
                )

        except requests.RequestException as e:
            return SendResult(
                success=False,
                status=ChannelStatus.FAILED,
                message=f"WeWork API request failed: {str(e)}",
                error_code="REQUEST_ERROR",
                error_message=str(e),
            )

    def _get_access_token(self) -> Optional[str]:
        """
        Get WeWork API access token.

        Returns:
            Access token string or None
        """
        if not self.corp_id or not self.agent_secret:
            return None

        # Try to get from cache first
        from django.core.cache import cache
        cache_key = f'wework_access_token_{self.agent_id}'
        cached_token = cache.get(cache_key)
        if cached_token:
            return cached_token

        # Request new token from WeWork
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.corp_id}&corpsecret={self.agent_secret}"

        try:
            response = requests.get(url, timeout=10)
            data = response.json()

            if data.get('errcode') == 0:
                access_token = data.get('access_token')
                expires_in = data.get('expires_in', 7200)

                # Cache token with 5 minutes buffer
                cache.set(cache_key, access_token, expires_in - 300)
                return access_token

        except requests.RequestException:
            pass

        return None

    def send_card_message(
        self,
        recipient: str,
        title: str,
        description: str,
        url: str,
        button_text: str = "详情",
        **kwargs
    ) -> SendResult:
        """
        Send a card-type message (rich format with button).

        Args:
            recipient: WeWork user ID
            title: Card title
            description: Card description
            url: Button link URL
            button_text: Button text
            **kwargs: Additional card fields

        Returns:
            SendResult
        """
        message = NotificationMessage(
            recipient=recipient,
            subject=title,
            content=description,
            data={
                'msgtype': 'textcard',
                'url': url,
                'button_text': button_text,
                **kwargs
            }
        )
        return self.send_with_validation(message)

    def send_markdown(self, recipient: str, title: str, content: str) -> SendResult:
        """
        Send a markdown-formatted message.

        Args:
            recipient: WeWork user ID or webhook
            title: Message title
            content: Markdown content

        Returns:
            SendResult
        """
        message = NotificationMessage(
            recipient=recipient,
            subject=title,
            content=content,
            data={'msgtype': 'markdown'}
        )
        return self.send_with_validation(message)

    def validate_message(self, message: NotificationMessage) -> tuple[bool, Optional[str]]:
        """
        Validate WeWork message before sending.

        Args:
            message: NotificationMessage to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Base validation
        is_valid, error_msg = super().validate_message(message)
        if not is_valid:
            return False, error_msg

        # Check webhook or API credentials
        if not self.webhook_key and not (self.corp_id and self.agent_secret):
            return False, "WeWork webhook key or API credentials not configured"

        return True, None
