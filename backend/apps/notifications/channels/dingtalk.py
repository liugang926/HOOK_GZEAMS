"""
DingTalk Channel Adapter

Handles DingTalk notifications via DingTalk API.
Supports text, markdown, and card message formats.
"""
import time
import json
import hmac
import hashlib
import base64
import urllib.parse
from typing import Optional, Dict, Any, List
from django.conf import settings
import requests
from .base import (
    NotificationChannel,
    NotificationMessage,
    SendResult,
    ChannelStatus,
    NonRetryableError,
)


class DingTalkChannel(NotificationChannel):
    """
    DingTalk notification channel.

    Sends messages to DingTalk users via DingTalk Webhook API or Open API.
    Supports multiple message types: text, markdown, link, actionCard, feedCard.
    """

    channel_type = "dingtalk"
    channel_name = "DingTalk"

    # DingTalk API endpoints
    WEBHOOK_URL_TEMPLATE = "https://oapi.dingtalk.com/robot/send?access_token={token}"
    MESSAGE_SEND_URL = "https://oapi.dingtalk.com/topapi/message/corpconversation/send?access_token={token}"

    def __init__(self):
        """Initialize DingTalk channel with credentials."""
        super().__init__()
        self.app_key = getattr(settings, 'DINGTALK_APP_KEY', '')
        self.app_secret = getattr(settings, 'DINGTALK_APP_SECRET', '')
        self.webhook_token = getattr(settings, 'DINGTALK_WEBHOOK_TOKEN', '')
        self.webhook_secret = getattr(settings, 'DINGTALK_WEBHOOK_SECRET', '')
        self.agent_id = getattr(settings, 'DINGTALK_AGENT_ID', '')

    def validate_recipient(self, recipient: str) -> bool:
        """
        Validate recipient is a valid DingTalk user ID.

        Args:
            recipient: DingTalk user ID or mobile/email

        Returns:
            True if recipient format is valid
        """
        # DingTalk user IDs (unionid or userid) are typically alphanumeric
        # Also accept mobile or email as recipient
        if '@' in recipient:
            return '@' in recipient and '.' in recipient.split('@')[1]
        if recipient.isdigit() and len(recipient) == 11:
            return True  # Mobile number
        return len(recipient) > 0 and recipient.replace('-', '').replace('_', '').isalnum()

    def send(self, message: NotificationMessage) -> SendResult:
        """
        Send DingTalk notification.

        Args:
            message: NotificationMessage to send

        Returns:
            SendResult with send details
        """
        start_time = time.time()

        try:
            # Prefer webhook if configured (simpler for group notifications)
            if self.webhook_token:
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
                message=f"Failed to send DingTalk notification: {str(e)}",
                error_code="SEND_FAILED",
                error_message=str(e),
                duration_ms=duration_ms,
            )

    def format_message(self, message: NotificationMessage) -> dict:
        """
        Format message for DingTalk API.

        Args:
            message: NotificationMessage to format

        Returns:
            Dictionary with DingTalk message format
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
        elif msg_type == 'link':
            return {
                "msgtype": "link",
                "link": {
                    "title": message.subject,
                    "text": message.content,
                    "messageUrl": message.data.get('url', ''),
                    "picUrl": message.data.get('pic_url', '')
                }
            }
        elif msg_type == 'actionCard':
            return {
                "msgtype": "actionCard",
                "actionCard": {
                    "title": message.subject,
                    "text": message.content,
                    "singleTitle": message.data.get('button_text', '查看详情'),
                    "singleURL": message.data.get('url', ''),
                    "btnOrientation": message.data.get('btn_orientation', '0')
                }
            }
        elif msg_type == 'feedCard':
            return {
                "msgtype": "feedCard",
                "feedCard": {
                    "links": message.data.get('links', [
                        {
                            "title": message.subject,
                            "messageURL": message.data.get('url', ''),
                            "picURL": message.data.get('pic_url', '')
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
        Send via DingTalk Webhook (simpler, recommended for group alerts).

        Args:
            message: NotificationMessage to send

        Returns:
            SendResult
        """
        url = self.WEBHOOK_URL_TEMPLATE.format(token=self.webhook_token)

        # Format message
        dingtalk_msg = self.format_message(message)

        # Add webhook secret if configured (for signature verification)
        if self.webhook_secret:
            timestamp = str(int(time.time() * 1000))
            secret_enc = self.webhook_secret.encode('utf-8')
            string_to_sign = f'{timestamp}\n{self.webhook_secret}'
            string_enc = string_to_sign.encode('utf-8')

            hmac_code = hmac.new(secret_enc, string_enc, digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

            url += f'&timestamp={timestamp}&sign={sign}'

        # Add @ mentions if specified
        at_mobiles = message.data.get('at_mobiles', [])
        at_user_ids = message.data.get('at_user_ids', [])
        is_at_all = message.data.get('is_at_all', False)

        if at_mobiles or at_user_ids or is_at_all:
            if 'text' in dingtalk_msg:
                dingtalk_msg['at'] = {
                    'atMobiles': at_mobiles,
                    'atUserIds': at_user_ids,
                    'isAtAll': is_at_all
                }

        try:
            response = requests.post(
                url,
                json=dingtalk_msg,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            response_data = response.json()

            if response_data.get('errcode') == 0:
                return SendResult(
                    success=True,
                    status=ChannelStatus.SUCCESS,
                    message="DingTalk webhook sent successfully",
                    external_id=str(time.time()),
                    response_data=response_data,
                )
            else:
                error_code = response_data.get('errcode')
                error_msg = response_data.get('errmsg', 'Unknown error')

                return SendResult(
                    success=False,
                    status=ChannelStatus.FAILED,
                    message=f"DingTalk webhook failed: {error_msg}",
                    error_code=f"DINGTALK_{error_code}",
                    error_message=error_msg,
                    response_data=response_data,
                )

        except requests.RequestException as e:
            return SendResult(
                success=False,
                status=ChannelStatus.FAILED,
                message=f"DingTalk webhook request failed: {str(e)}",
                error_code="REQUEST_ERROR",
                error_message=str(e),
            )

    def _send_via_api(self, message: NotificationMessage) -> SendResult:
        """
        Send via DingTalk Open API (requires access token).

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
                message="Failed to get DingTalk access token",
                error_code="AUTH_ERROR",
                error_message="Could not retrieve access token from DingTalk API",
            )

        url = self.MESSAGE_SEND_URL.format(token=access_token)

        # Determine message type for API
        msg_type = message.data.get('msgtype', 'text')

        # Prepare message payload
        payload = {
            'agent_id': int(self.agent_id) if self.agent_id else 0,
            'userid_list': message.recipient if ',' in message.recipient else '',
            'dept_id_list': message.data.get('dept_id_list', ''),
            'msg': {
                'msgtype': msg_type
            }
        }

        # Set message content based on type
        if msg_type == 'text':
            payload['msg']['text'] = {'content': message.content}
        elif msg_type == 'markdown':
            payload['msg']['markdown'] = {
                'title': message.subject,
                'text': message.content
            }
        elif msg_type == 'link':
            payload['msg']['link'] = {
                'title': message.subject,
                'text': message.content,
                'messageUrl': message.data.get('url', ''),
                'picUrl': message.data.get('pic_url', '')
            }
        elif msg_type == 'actionCard':
            payload['msg']['actionCard'] = {
                'title': message.subject,
                'text': message.content,
                'singleTitle': message.data.get('button_text', '查看详情'),
                'singleURL': message.data.get('url', '')
            }

        # Handle single recipient
        if ',' not in message.recipient:
            payload['userid_list'] = message.recipient

        try:
            response = requests.post(
                url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            response_data = response.json()

            if response_data.get('errcode') == 0:
                return SendResult(
                    success=True,
                    status=ChannelStatus.SUCCESS,
                    message=f"DingTalk message sent to {message.recipient}",
                    external_id=response_data.get('task_id'),
                    response_data=response_data,
                )
            else:
                return SendResult(
                    success=False,
                    status=ChannelStatus.FAILED,
                    message=f"DingTalk API failed: {response_data.get('errmsg')}",
                    error_code=f"DINGTALK_{response_data.get('errcode')}",
                    error_message=response_data.get('errmsg'),
                    response_data=response_data,
                )

        except requests.RequestException as e:
            return SendResult(
                success=False,
                status=ChannelStatus.FAILED,
                message=f"DingTalk API request failed: {str(e)}",
                error_code="REQUEST_ERROR",
                error_message=str(e),
            )

    def _get_access_token(self) -> Optional[str]:
        """
        Get DingTalk API access token.

        Returns:
            Access token string or None
        """
        if not self.app_key or not self.app_secret:
            return None

        # Try to get from cache first
        from django.core.cache import cache
        cache_key = f'dingtalk_access_token_{self.app_key}'
        cached_token = cache.get(cache_key)
        if cached_token:
            return cached_token

        # Request new token from DingTalk
        url = f"https://oapi.dingtalk.com/gettoken?appkey={self.app_key}&appsecret={self.app_secret}"

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
        button_text: str = "查看详情",
        **kwargs
    ) -> SendResult:
        """
        Send an actionCard message (rich format with button).

        Args:
            recipient: DingTalk user ID or group
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
                'msgtype': 'actionCard',
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
            recipient: DingTalk user ID or group
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
        Validate DingTalk message before sending.

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
        if not self.webhook_token and not (self.app_key and self.app_secret):
            return False, "DingTalk webhook token or API credentials not configured"

        return True, None
