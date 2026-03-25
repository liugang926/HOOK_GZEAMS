"""
Email Channel Adapter

Handles email notifications via SMTP or external email services.
Supports HTML emails, attachments, and custom reply-to addresses.
"""
import time
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import engines
from .base import (
    NotificationChannel,
    NotificationMessage,
    SendResult,
    ChannelStatus,
    NonRetryableError,
)


class EmailChannel(NotificationChannel):
    """
    Email notification channel.

    Sends emails using Django's email backend configuration.
    Supports both plain text and HTML emails.
    """

    channel_type = "email"
    channel_name = "Email"

    # Email validation regex
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    def validate_recipient(self, recipient: str) -> bool:
        """
        Validate recipient is a valid email address.

        Args:
            recipient: Email address

        Returns:
            True if email is valid format
        """
        return bool(self.EMAIL_REGEX.match(recipient))

    def send(self, message: NotificationMessage) -> SendResult:
        """
        Send email notification.

        Args:
            message: NotificationMessage to send

        Returns:
            SendResult with send details
        """
        start_time = time.time()

        try:
            # Prepare email
            subject = message.subject
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
            reply_to = [message.reply_to] if message.reply_to else None

            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=message.content,
                from_email=from_email,
                to=[message.recipient],
                reply_to=reply_to,
            )

            # Add HTML version if provided
            if message.html_content:
                email.attach_alternative(message.html_content, "text/html")
            else:
                # Generate basic HTML from plain text
                html_content = self._generate_html(message.content, message.subject)
                email.attach_alternative(html_content, "text/html")

            # Add attachments if any
            for attachment in message.attachments:
                if isinstance(attachment, dict):
                    self._add_attachment(email, attachment)

            # Send email
            email.send()

            duration_ms = int((time.time() - start_time) * 1000)

            return SendResult(
                success=True,
                status=ChannelStatus.SUCCESS,
                message=f"Email sent to {message.recipient}",
                external_id=self._generate_message_id(),
                duration_ms=duration_ms,
                response_data={
                    'recipient': message.recipient,
                    'subject': subject,
                },
            )

        except smtplib.SMTPRecipientsRefused as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return SendResult(
                success=False,
                status=ChannelStatus.FAILED,
                message=f"Email recipient rejected: {message.recipient}",
                error_code="INVALID_RECIPIENT",
                error_message=str(e),
                duration_ms=duration_ms,
            )

        except smtplib.SMTPAuthenticationError as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return SendResult(
                success=False,
                status=ChannelStatus.FAILED,
                message="Email authentication failed",
                error_code="AUTH_ERROR",
                error_message=str(e),
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return SendResult(
                success=False,
                status=ChannelStatus.FAILED,
                message=f"Failed to send email: {str(e)}",
                error_code="SEND_FAILED",
                error_message=str(e),
                duration_ms=duration_ms,
            )

    def format_message(self, message: NotificationMessage) -> EmailMultiAlternatives:
        """
        Format message for email sending.

        Args:
            message: NotificationMessage to format

        Returns:
            EmailMultiAlternatives object
        """
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')

        email = EmailMultiAlternatives(
            subject=message.subject,
            body=message.content,
            from_email=from_email,
            to=[message.recipient],
        )

        if message.html_content:
            email.attach_alternative(message.html_content, "text/html")

        return email

    def _generate_html(self, plain_text: str, subject: str) -> str:
        """
        Generate basic HTML from plain text.

        Args:
            plain_text: Plain text content
            subject: Email subject

        Returns:
            HTML string
        """
        # Convert line breaks to <br> and wrap in basic HTML structure
        body = plain_text.replace('\n', '<br>\n')

        html_template = getattr(settings, 'EMAIL_HTML_TEMPLATE', '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{subject}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .footer {{ text-align: center; padding: 20px; color: #777; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>{subject}</h2>
        </div>
        <div class="content">
            {body}
        </div>
        <div class="footer">
            <p>This is an automated notification. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
        ''')

        return html_template.format(subject=subject, body=body)

    def _add_attachment(self, email: EmailMultiAlternatives, attachment: dict):
        """
        Add attachment to email.

        Args:
            email: EmailMultiAlternatives object
            attachment: Attachment dict with 'filename', 'content', 'type'
        """
        filename = attachment.get('filename')
        content = attachment.get('content')
        content_type = attachment.get('type', 'application/octet-stream')

        if filename and content:
            part = MIMEBase(*content_type.split('/', 1))
            part.set_payload(content)
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{filename}"'
            )
            email.attach(part)

    def _generate_message_id(self) -> str:
        """Generate unique message ID for tracking."""
        import uuid
        return f"<{uuid.uuid4()}@example.com>"

    def send_bulk(self, messages: List[NotificationMessage]) -> List[SendResult]:
        """
        Send multiple emails in batch.

        Args:
            messages: List of NotificationMessages to send

        Returns:
            List of SendResults
        """
        results = []
        for message in messages:
            results.append(self.send(message))
        return results

    def validate_message(self, message: NotificationMessage) -> tuple[bool, Optional[str]]:
        """
        Validate email message before sending.

        Args:
            message: NotificationMessage to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Base validation
        is_valid, error_msg = super().validate_message(message)
        if not is_valid:
            return False, error_msg

        # Email-specific validation
        if not self.validate_recipient(message.recipient):
            return False, f"Invalid email address: {message.recipient}"

        return True, None
