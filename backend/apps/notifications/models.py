"""
Notification Models

Defines all models for the unified notification service:
- NotificationTemplate: Template-based notification content
- Notification: Notification records sent to users
- NotificationLog: Sending attempt logs
- NotificationConfig: User notification preferences
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.common.models import BaseModel


class NotificationTemplate(BaseModel):
    """
    Notification Template

    Defines template content for different notification types and channels.
    Supports Jinja2 template syntax for dynamic content.
    """

    CHANNEL_TYPES = [
        ('inbox', 'Inbox'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('wework', 'WeWork'),
        ('dingtalk', 'DingTalk'),
        ('feishu', 'Feishu'),
    ]

    # Basic information
    template_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Unique template code, e.g., workflow_approval'
    )
    template_name = models.CharField(
        max_length=100,
        help_text='Human-readable template name'
    )
    template_type = models.CharField(
        max_length=50,
        help_text='Notification type, e.g., workflow_approval, inventory_assigned'
    )
    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_TYPES,
        help_text='Delivery channel for this template'
    )

    # Template content
    subject_template = models.TextField(
        blank=True,
        help_text='Subject line template (Jinja2 syntax)'
    )
    content_template = models.TextField(
        help_text='Content body template (Jinja2 syntax)'
    )

    # Template variables definition (JSON format)
    variables = models.JSONField(
        default=dict,
        help_text='Template variables definition with default values'
    )

    # Template configuration
    language = models.CharField(
        max_length=10,
        default='zh-CN',
        help_text='Template language code'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this template is active'
    )
    is_system = models.BooleanField(
        default=False,
        help_text='Whether this is a system template (cannot be deleted)'
    )

    # Version control
    version = models.IntegerField(
        default=1,
        help_text='Template version number'
    )
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_versions',
        help_text='Previous version of this template'
    )

    # Description and example
    description = models.TextField(
        blank=True,
        help_text='Template description and usage notes'
    )
    example_data = models.JSONField(
        null=True,
        blank=True,
        help_text='Example data for template preview'
    )

    class Meta:
        db_table = 'notification_template'
        verbose_name = 'Notification Template'
        verbose_name_plural = 'Notification Templates'
        ordering = ['template_type', 'channel']
        indexes = [
            models.Index(fields=['template_code']),
            models.Index(fields=['template_type', 'channel']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.template_name} ({self.channel})"

    def render(self, context: dict) -> dict:
        """
        Render template with given context.

        Args:
            context: Template variables

        Returns:
            Dict with rendered subject and content
        """
        from jinja2 import Template

        subject = ''
        content = ''

        if self.subject_template:
            subject = Template(self.subject_template).render(**context)

        if self.content_template:
            content = Template(self.content_template).render(**context)

        return {'subject': subject, 'content': content}

    def save_new_version(self):
        """Save as a new version of the template."""
        if self.pk:
            # Store the original template_code and instance ID
            original_code = self.template_code
            original_id = self.id

            # Count existing versions for this template code
            max_version = NotificationTemplate.objects.filter(
                template_code=original_code
            ).aggregate(models.Max('version'))['version__max'] or 0

            # Create new version
            self.pk = None
            self.version = max_version + 1
            self.is_active = False  # New version is inactive by default
            self.previous_version_id = original_id
            # Generate unique template_code for new version
            self.template_code = f"{original_code}_v{max_version + 1}"

        self.save()
        return self


class Notification(BaseModel):
    """
    Notification Record

    Records notifications sent to users.
    Tracks delivery status, read status, and retry information.
    """

    PRIORITIES = [
        ('urgent', 'Urgent'),
        ('high', 'High'),
        ('normal', 'Normal'),
        ('low', 'Low'),
    ]

    STATUSES = [
        ('pending', 'Pending'),
        ('sending', 'Sending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    # Recipient
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text='Notification recipient'
    )

    # Template reference
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        help_text='Template used for this notification'
    )

    # Notification information
    notification_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text='Notification type code'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITIES,
        default='normal',
        help_text='Notification priority level'
    )
    channel = models.CharField(
        max_length=20,
        choices=NotificationTemplate.CHANNEL_TYPES,
        help_text='Delivery channel'
    )

    # Content
    title = models.CharField(
        max_length=200,
        help_text='Notification title'
    )
    content = models.TextField(
        help_text='Notification content'
    )
    data = models.JSONField(
        default=dict,
        help_text='Additional data (links, metadata, etc.)'
    )

    # Delivery status
    status = models.CharField(
        max_length=20,
        choices=STATUSES,
        default='pending',
        help_text='Delivery status'
    )

    # Timing
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Scheduled send time'
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Actual send time'
    )

    # Read status (for inbox channel only)
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the notification was read'
    )

    # Retry information
    retry_count = models.IntegerField(
        default=0,
        help_text='Number of retry attempts'
    )
    max_retries = models.IntegerField(
        default=3,
        help_text='Maximum retry attempts allowed'
    )
    next_retry_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Next retry time'
    )

    # Related object (generic foreign key)
    related_content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Related object type'
    )
    related_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Related object ID'
    )

    # Sender
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications',
        help_text='User who triggered the notification'
    )

    class Meta:
        db_table = 'notification'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['status', 'next_retry_at']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['priority', 'status']),
        ]

    def __str__(self):
        return f"{self.recipient.username} - {self.title}"

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])

    def mark_as_unread(self):
        """Mark notification as unread."""
        self.read_at = None
        self.save(update_fields=['read_at'])


class NotificationLog(BaseModel):
    """
    Notification Send Log

    Records detailed information about each send attempt.
    Used for troubleshooting and audit purposes.
    """

    # Related notification
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='logs',
        help_text='Related notification'
    )

    # Send information
    channel = models.CharField(
        max_length=20,
        help_text='Delivery channel used'
    )
    status = models.CharField(
        max_length=20,
        help_text='Send status'
    )

    # Request and response data
    request_data = models.JSONField(
        null=True,
        blank=True,
        help_text='Request payload sent to channel'
    )
    response_data = models.JSONField(
        null=True,
        blank=True,
        help_text='Response received from channel'
    )

    # Error information
    error_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Error code from channel'
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text='Detailed error message'
    )

    # Execution information
    retry_count = models.IntegerField(
        default=0,
        help_text='Attempt number'
    )
    duration = models.IntegerField(
        null=True,
        blank=True,
        help_text='Send duration in milliseconds'
    )

    # Channel-specific information
    external_id = models.CharField(
        max_length=200,
        blank=True,
        help_text='External message ID (e.g., email ID, SMS ID)'
    )
    external_status = models.CharField(
        max_length=50,
        blank=True,
        help_text='Status from external service'
    )

    class Meta:
        db_table = 'notification_log'
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.notification} - {self.status}"


class NotificationConfig(BaseModel):
    """
    User Notification Configuration

    Stores user preferences for notification delivery.
    Controls which channels are used for different notification types.
    """

    # Related user
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_config',
        help_text='User who owns this configuration'
    )

    # Channel settings (JSON format)
    # Example: {'workflow_approval': {'inbox': true, 'email': false}}
    channel_settings = models.JSONField(
        default=dict,
        help_text='Per-type channel preferences'
    )

    # Global channel switches
    enable_inbox = models.BooleanField(
        default=True,
        help_text='Enable inbox notifications'
    )
    enable_email = models.BooleanField(
        default=True,
        help_text='Enable email notifications'
    )
    enable_sms = models.BooleanField(
        default=False,
        help_text='Enable SMS notifications'
    )
    enable_wework = models.BooleanField(
        default=True,
        help_text='Enable WeWork notifications'
    )
    enable_dingtalk = models.BooleanField(
        default=False,
        help_text='Enable DingTalk notifications'
    )

    # Quiet hours (do not disturb)
    quiet_hours_enabled = models.BooleanField(
        default=False,
        help_text='Enable quiet hours'
    )
    quiet_hours_start = models.TimeField(
        null=True,
        blank=True,
        help_text='Quiet hours start time'
    )
    quiet_hours_end = models.TimeField(
        null=True,
        blank=True,
        help_text='Quiet hours end time'
    )

    # Contact information override
    email_address = models.EmailField(
        blank=True,
        help_text='Override email for notifications'
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text='Override phone number for SMS'
    )

    class Meta:
        db_table = 'notification_config'
        verbose_name = 'Notification Config'
        verbose_name_plural = 'Notification Configs'

    def __str__(self):
        return f"{self.user.username} Configuration"

    def is_channel_enabled(self, notification_type: str, channel: str) -> bool:
        """
        Check if a channel is enabled for a notification type.

        Args:
            notification_type: Type of notification
            channel: Channel to check

        Returns:
            True if channel is enabled
        """
        # Check global switch
        global_enable = getattr(self, f'enable_{channel}', True)
        if not global_enable:
            return False

        # Check type-specific configuration
        type_config = self.channel_settings.get(notification_type, {})
        return type_config.get(channel, True)

    def is_in_quiet_hours(self) -> bool:
        """
        Check if current time is within quiet hours.

        Returns:
            True if in quiet hours
        """
        if not self.quiet_hours_enabled:
            return False

        now = timezone.now().time()

        if self.quiet_hours_start and self.quiet_hours_end:
            if self.quiet_hours_start <= self.quiet_hours_end:
                return self.quiet_hours_start <= now <= self.quiet_hours_end
            else:
                # Crosses midnight
                return now >= self.quiet_hours_start or now <= self.quiet_hours_end

        return False


class NotificationChannel(BaseModel):
    """
    Notification Channel Configuration

    Defines delivery channels for notifications.
    Each channel has specific configuration and can be enabled/disabled per organization.
    """

    CHANNEL_TYPE_CHOICES = [
        ('wework', 'WeWork'),
        ('dingtalk', 'DingTalk'),
        ('feishu', 'Feishu'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('inapp', 'In-App'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
    ]

    # Channel identification
    channel_type = models.CharField(
        max_length=20,
        choices=CHANNEL_TYPE_CHOICES,
        unique=True,
        db_index=True,
        help_text='Channel type identifier'
    )
    channel_name = models.CharField(
        max_length=100,
        help_text='Human-readable channel name'
    )

    # Channel configuration (JSON format - varies by channel type)
    # Example for WeWork: {'corp_id': 'xxx', 'agent_id': 123, 'secret': 'xxx'}
    # Example for Email: {'smtp_host': 'smtp.example.com', 'smtp_port': 587, ...}
    config = models.JSONField(
        default=dict,
        help_text='Channel-specific configuration'
    )

    # Channel settings
    priority = models.IntegerField(
        default=0,
        help_text='Channel priority (higher = preferred)'
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text='Whether this channel is enabled'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text='Channel operational status'
    )

    # Rate limiting
    rate_limit_per_minute = models.IntegerField(
        default=60,
        help_text='Maximum messages per minute'
    )
    rate_limit_per_hour = models.IntegerField(
        default=1000,
        help_text='Maximum messages per hour'
    )

    # Retry settings
    max_retries = models.IntegerField(
        default=3,
        help_text='Maximum retry attempts for failed sends'
    )
    retry_delay_seconds = models.IntegerField(
        default=60,
        help_text='Delay between retries in seconds'
    )

    # Template mapping (JSON format)
    # Maps notification types to channel-specific template codes
    template_mapping = models.JSONField(
        default=dict,
        help_text='Notification type to template code mapping'
    )

    # Error tracking
    last_error_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last error timestamp'
    )
    last_error_message = models.TextField(
        blank=True,
        help_text='Last error message'
    )
    consecutive_failures = models.IntegerField(
        default=0,
        help_text='Number of consecutive failures'
    )

    # Webhook configuration for async delivery status updates
    webhook_url = models.URLField(
        blank=True,
        help_text='Webhook URL for delivery status callbacks'
    )
    webhook_secret = models.CharField(
        max_length=100,
        blank=True,
        help_text='Secret for webhook signature verification'
    )

    class Meta:
        db_table = 'notification_channel'
        verbose_name = 'Notification Channel'
        verbose_name_plural = 'Notification Channels'
        ordering = ['-priority', 'channel_type']
        indexes = [
            models.Index(fields=['channel_type']),
            models.Index(fields=['is_enabled', 'status']),
            models.Index(fields=['-priority']),
        ]

    def __str__(self):
        return f"{self.channel_name} ({self.channel_type})"

    def is_available(self) -> bool:
        """Check if channel is available for sending."""
        return (
            self.is_enabled and
            self.status == 'active' and
            self.consecutive_failures < 5
        )

    def record_success(self):
        """Reset failure counters on successful send."""
        self.consecutive_failures = 0
        self.last_error_at = None
        self.last_error_message = ''
        if self.status == 'error':
            self.status = 'active'
        self.save(update_fields=[
            'consecutive_failures',
            'last_error_at',
            'last_error_message',
            'status'
        ])

    def record_failure(self, error_message: str):
        """Record failure and update status if needed."""
        from django.utils import timezone

        self.consecutive_failures += 1
        self.last_error_at = timezone.now()
        self.last_error_message = error_message[:500]  # Limit length

        if self.consecutive_failures >= 5:
            self.status = 'error'

        self.save(update_fields=[
            'consecutive_failures',
            'last_error_at',
            'last_error_message',
            'status'
        ])

    def get_config(self, key: str, default=None):
        """Get configuration value by key."""
        return self.config.get(key, default)

    def set_config(self, key: str, value):
        """Set configuration value."""
        self.config[key] = value
        self.save(update_fields=['config'])


class NotificationMessage(BaseModel):
    """
    Centralized Notification Message Tracking

    Tracks all outgoing notification messages across all channels.
    Provides centralized management and statistics for multi-channel sends.
    """

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('sent', 'Sent'),
        ('partial', 'Partially Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('urgent', 'Urgent'),
        ('high', 'High'),
        ('normal', 'Normal'),
        ('low', 'Low'),
    ]

    # Message identification
    message_code = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text='Unique message identifier (auto-generated)'
    )
    notification_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text='Notification type code'
    )

    # Message content
    title = models.CharField(
        max_length=200,
        help_text='Message title'
    )
    content = models.TextField(
        help_text='Message content body'
    )
    subject = models.CharField(
        max_length=200,
        blank=True,
        help_text='Subject line (for email, etc.)'
    )

    # Template reference
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        help_text='Template used for this message'
    )

    # Target configuration
    target_type = models.CharField(
        max_length=20,
        help_text='Target type: user, role, department, or all'
    )
    target_ids = models.JSONField(
        default=list,
        help_text='List of target IDs (users, roles, departments)'
    )

    # Channel configuration
    channels = models.JSONField(
        default=list,
        help_text='List of channel types to use'
    )
    primary_channel = models.CharField(
        max_length=20,
        blank=True,
        help_text='Primary delivery channel'
    )

    # Priority and scheduling
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='normal',
        help_text='Message priority'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text='Message status'
    )
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Scheduled send time'
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Actual send time'
    )

    # Delivery statistics
    total_recipients = models.IntegerField(
        default=0,
        help_text='Total number of recipients'
    )
    sent_count = models.IntegerField(
        default=0,
        help_text='Successfully sent count'
    )
    failed_count = models.IntegerField(
        default=0,
        help_text='Failed send count'
    )
    read_count = models.IntegerField(
        default=0,
        help_text='Read/acknowledged count'
    )

    # Delivery progress
    progress = models.IntegerField(
        default=0,
        help_text='Delivery progress percentage (0-100)'
    )

    # Additional data
    data = models.JSONField(
        default=dict,
        help_text='Additional message data and metadata'
    )

    # Related object (generic foreign key)
    related_content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Related object type'
    )
    related_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Related object ID'
    )

    # Sender
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_messages',
        help_text='User who created/sent this message'
    )

    # Error information
    error_message = models.TextField(
        blank=True,
        help_text='Overall error message if send failed'
    )

    class Meta:
        db_table = 'notification_message'
        verbose_name = 'Notification Message'
        verbose_name_plural = 'Notification Messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['message_code']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['status', 'scheduled_at']),
            models.Index(fields=['priority', 'status']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.message_code} - {self.title}"

    def generate_message_code(self):
        """Generate unique message code."""
        import uuid
        prefix = self.notification_type.upper()[:8]
        suffix = uuid.uuid4().hex[:8].upper()
        self.message_code = f"MSG_{prefix}_{suffix}"
        return self.message_code

    def mark_sent(self):
        """Mark message as sent."""
        from django.utils import timezone
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.progress = 100
        self.save(update_fields=['status', 'sent_at', 'progress'])

    def mark_failed(self, error_message: str):
        """Mark message as failed."""
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])

    def update_progress(self, sent: int, failed: int):
        """Update delivery progress."""
        self.sent_count = sent
        self.failed_count = failed
        if self.total_recipients > 0:
            self.progress = int((sent + failed) / self.total_recipients * 100)

        # Update status based on progress
        if sent + failed >= self.total_recipients:
            if failed > 0 and sent == 0:
                self.status = 'failed'
            elif failed > 0:
                self.status = 'partial'
            else:
                self.status = 'sent'

        self.save(update_fields=['sent_count', 'failed_count', 'progress', 'status'])

    def get_recipient_users(self):
        """
        Get list of recipient user IDs based on target configuration.

        Returns:
            List of user IDs
        """
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user_ids = set()

        if self.target_type == 'user':
            # Direct user targets
            user_ids.update(self.target_ids)

        elif self.target_type == 'role':
            # Users with specified roles
            from apps.accounts.models import Role
            for role_id in self.target_ids:
                try:
                    role = Role.objects.get(id=role_id, is_deleted=False)
                    user_ids.update(role.users.values_list('id', flat=True))
                except Role.DoesNotExist:
                    pass

        elif self.target_type == 'department':
            # Users in specified departments
            from apps.organizations.models import Department
            for dept_id in self.target_ids:
                users = User.objects.filter(
                    department_id=dept_id,
                    is_deleted=False
                ).values_list('id', flat=True)
                user_ids.update(users)

        elif self.target_type == 'all':
            # All active users in organization
            if self.organization:
                user_ids.update(
                    User.objects.filter(
                        organization=self.organization,
                        is_active=True,
                        is_deleted=False
                    ).values_list('id', flat=True)
                )

        return list(user_ids)


class InAppMessage(BaseModel):
    """
    In-App Message Model

    Separate from Notification model for dedicated in-app messaging.
    Used for announcements, system messages, and user-to-user messages.
    """

    MESSAGE_TYPE_CHOICES = [
        ('announcement', 'Announcement'),
        ('system', 'System'),
        ('reminder', 'Reminder'),
        ('user', 'User Message'),
    ]

    PRIORITY_CHOICES = [
        ('urgent', 'Urgent'),
        ('high', 'High'),
        ('normal', 'Normal'),
        ('low', 'Low'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('scheduled', 'Scheduled'),
        ('archived', 'Archived'),
    ]

    # Message identification
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        default='announcement',
        help_text='Type of in-app message'
    )

    # Message content
    title = models.CharField(
        max_length=200,
        help_text='Message title'
    )
    content = models.TextField(
        help_text='Message content (supports Markdown)'
    )

    # Priority and display
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='normal',
        help_text='Message priority level'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text='Message publication status'
    )

    # Targeting
    target_type = models.CharField(
        max_length=20,
        default='all',
        help_text='Target: all, users, roles, departments'
    )
    target_ids = models.JSONField(
        default=list,
        help_text='List of target IDs'
    )

    # Excluding specific users
    exclude_users = models.JSONField(
        default=list,
        help_text='List of user IDs to exclude'
    )

    # Display settings
    show_popup = models.BooleanField(
        default=False,
        help_text='Show as popup/modal instead of notification'
    )
    dismissible = models.BooleanField(
        default=True,
        help_text='Whether user can dismiss the message'
    )
    requires_acknowledgment = models.BooleanField(
        default=False,
        help_text='Require user acknowledgment to dismiss'
    )

    # Scheduling
    publish_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Scheduled publish time'
    )
    expire_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Message expiration time'
    )

    # Display statistics
    view_count = models.IntegerField(
        default=0,
        help_text='Number of times message was viewed'
    )
    acknowledge_count = models.IntegerField(
        default=0,
        help_text='Number of acknowledgments received'
    )
    dismiss_count = models.IntegerField(
        default=0,
        help_text='Number of times message was dismissed'
    )

    # Attachment/Action button
    action_url = models.URLField(
        blank=True,
        help_text='URL for action button'
    )
    action_label = models.CharField(
        max_length=50,
        blank=True,
        help_text='Label for action button'
    )

    # Related object
    related_content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text='Related object type'
    )
    related_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Related object ID'
    )

    # Author
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authored_messages',
        help_text='Message author'
    )

    class Meta:
        db_table = 'in_app_message'
        verbose_name = 'In-App Message'
        verbose_name_plural = 'In-App Messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['message_type', 'status']),
            models.Index(fields=['status', 'publish_at']),
            models.Index(fields=['priority', 'status']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.get_message_type_display()}: {self.title}"

    def is_active(self) -> bool:
        """Check if message is currently active."""
        from django.utils import timezone

        now = timezone.now()

        if self.status != 'published':
            return False

        if self.publish_at and self.publish_at > now:
            return False

        if self.expire_at and self.expire_at < now:
            return False

        return True

    def get_target_users(self):
        """
        Get list of target user IDs.

        Returns:
            List of user IDs
        """
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user_ids = set()

        if self.target_type == 'all':
            user_ids.update(
                User.objects.filter(
                    organization=self.organization,
                    is_active=True,
                    is_deleted=False
                ).values_list('id', flat=True)
            )

        elif self.target_type == 'users':
            user_ids.update(self.target_ids)

        elif self.target_type == 'roles':
            from apps.accounts.models import Role
            for role_id in self.target_ids:
                try:
                    role = Role.objects.get(id=role_id, is_deleted=False)
                    user_ids.update(role.users.values_list('id', flat=True))
                except Role.DoesNotExist:
                    pass

        elif self.target_type == 'departments':
            users = User.objects.filter(
                department_id__in=self.target_ids,
                is_active=True,
                is_deleted=False
            ).values_list('id', flat=True)
            user_ids.update(users)

        # Exclude specified users
        exclude_set = set(self.exclude_users)
        user_ids = user_ids - exclude_set

        return list(user_ids)

    def increment_view(self):
        """Increment view count."""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def increment_acknowledge(self):
        """Increment acknowledgment count."""
        self.acknowledge_count += 1
        self.save(update_fields=['acknowledge_count'])

    def increment_dismiss(self):
        """Increment dismiss count."""
        self.dismiss_count += 1
        self.save(update_fields=['dismiss_count'])

    def publish(self):
        """Publish the message."""
        from django.utils import timezone

        self.status = 'published'
        if not self.publish_at:
            self.publish_at = timezone.now()
        self.save(update_fields=['status', 'publish_at'])

    def archive(self):
        """Archive the message."""
        self.status = 'archived'
        self.save(update_fields=['status'])
