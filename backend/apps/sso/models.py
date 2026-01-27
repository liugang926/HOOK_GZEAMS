"""
SSO Models

Defines all models for Single Sign-On (SSO) integration:
- WeWorkConfig: WeWork (企业微信) configuration
- UserMapping: User platform mapping (WeWork, DingTalk, Feishu)
- OAuthState: OAuth state for CSRF protection
- SyncLog: Sync log for WeWork contacts sync
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.common.models import BaseModel


class WeWorkConfig(BaseModel):
    """
    WeWork (企业微信) Configuration

    Stores configuration for WeWork SSO integration.
    Each organization can have its own WeWork configuration.
    """

    # WeWork credentials
    corp_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text='WeWork Corp ID (企业ID)'
    )
    corp_name = models.CharField(
        max_length=200,
        help_text='WeWork Corp Name (企业名称)'
    )
    agent_id = models.IntegerField(
        help_text='WeWork Agent ID (应用ID)'
    )
    agent_secret = models.CharField(
        max_length=200,
        help_text='WeWork Agent Secret (应用Secret)'
    )

    # Sync settings
    sync_department = models.BooleanField(
        default=True,
        help_text='Sync departments from WeWork'
    )
    sync_user = models.BooleanField(
        default=True,
        help_text='Sync users from WeWork'
    )
    auto_create_user = models.BooleanField(
        default=True,
        help_text='Auto-create user on first SSO login'
    )

    # Default role for auto-created users
    default_role_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Default role ID for auto-created users'
    )

    # Callback settings
    redirect_uri = models.URLField(
        max_length=500,
        blank=True,
        help_text='Custom redirect URI for OAuth callback'
    )

    # Status
    is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Whether WeWork SSO is enabled'
    )

    class Meta:
        db_table = 'wework_config'
        verbose_name = 'WeWork Config'
        verbose_name_plural = 'WeWork Configs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['corp_id']),
            models.Index(fields=['is_enabled']),
            models.Index(fields=['organization', 'is_enabled']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'is_deleted'],
                condition=models.Q(is_deleted=False),
                name='unique_active_wework_config_per_org'
            )
        ]

    def __str__(self):
        return f"{self.corp_name} ({self.corp_id})"


class UserMapping(BaseModel):
    """
    User Platform Mapping

    Maps system users to third-party platform users.
    Supports multiple platforms: WeWork, DingTalk, Feishu.
    """

    PLATFORM_CHOICES = [
        ('wework', 'WeWork'),
        ('dingtalk', 'DingTalk'),
        ('feishu', 'Feishu'),
    ]

    # System user
    system_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='platform_mappings',
        help_text='System user'
    )

    # Platform information
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        db_index=True,
        help_text='Platform type'
    )
    platform_userid = models.CharField(
        max_length=100,
        db_index=True,
        help_text='Platform user ID'
    )
    platform_unionid = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text='Platform UnionID (cross-app unique ID)'
    )
    platform_name = models.CharField(
        max_length=200,
        blank=True,
        help_text='Platform display name'
    )

    # Extra platform data (JSON)
    extra_data = models.JSONField(
        default=dict,
        help_text='Extra platform data (avatar, position, etc.)'
    )

    class Meta:
        db_table = 'user_mapping'
        verbose_name = 'User Mapping'
        verbose_name_plural = 'User Mappings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['system_user', 'platform']),
            models.Index(fields=['platform', 'platform_userid']),
            models.Index(fields=['platform', 'platform_unionid']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['platform', 'platform_userid', 'is_deleted'],
                condition=models.Q(is_deleted=False),
                name='unique_platform_userid'
            )
        ]

    def __str__(self):
        return f"{self.system_user.username} - {self.get_platform_display()} ({self.platform_userid})"


class OAuthState(BaseModel):
    """
    OAuth State

    Stores OAuth state tokens for CSRF protection during OAuth flow.
    States are single-use and expire after a short time.
    """

    state = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text='OAuth state token (防CSRF)'
    )
    platform = models.CharField(
        max_length=20,
        help_text='Platform type (wework/dingtalk/feishu)'
    )
    session_data = models.JSONField(
        default=dict,
        help_text='Session data stored with state'
    )
    expires_at = models.DateTimeField(
        db_index=True,
        help_text='State expiration time'
    )
    consumed = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Whether state has been consumed'
    )
    consumed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When state was consumed'
    )

    class Meta:
        db_table = 'oauth_state'
        verbose_name = 'OAuth State'
        verbose_name_plural = 'OAuth States'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['state', 'consumed']),
            models.Index(fields=['platform', 'expires_at']),
        ]

    def __str__(self):
        return f"OAuth State: {self.state[:8]}... ({self.platform})"

    def is_valid(self) -> bool:
        """Check if state is valid (not consumed and not expired)."""
        if self.consumed:
            return False
        if timezone.now() > self.expires_at:
            return False
        return True

    def consume_instance(self) -> dict:
        """
        Instance method to consume the state (mark as used and return session data).

        Returns:
            Session data if valid, None otherwise
        """
        if not self.is_valid():
            return None

        self.consumed = True
        self.consumed_at = timezone.now()
        self.save(update_fields=['consumed', 'consumed_at'])
        return self.session_data

    @classmethod
    def consume(cls, state: str, platform: str) -> dict:
        """
        Class method to consume state by state string and platform.

        Args:
            state: State token string
            platform: Platform type

        Returns:
            Session data if valid, None otherwise
        """
        try:
            state_obj = cls.objects.get(
                state=state,
                platform=platform,
                consumed=False
            )
            # Mark as consumed directly without recursive call
            if not state_obj.is_valid():
                return None
            state_obj.consumed = True
            state_obj.consumed_at = timezone.now()
            state_obj.save(update_fields=['consumed', 'consumed_at'])
            return state_obj.session_data
        except cls.DoesNotExist:
            return None


class SyncLog(BaseModel):
    """
    Sync Log

    Records sync operations for WeWork contacts synchronization.
    Tracks departments, users sync status and statistics.
    """

    class SyncTypeChoices(models.TextChoices):
        DEPARTMENT = 'department', 'Department Sync'
        USER = 'user', 'User Sync'
        FULL = 'full', 'Full Sync'

    class SourceChoices(models.TextChoices):
        WEWORK = 'wework', 'WeWork'
        DINGTALK = 'dingtalk', 'DingTalk'
        FEISHU = 'feishu', 'Feishu'

    class StatusChoices(models.TextChoices):
        RUNNING = 'running', 'Running'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        PARTIAL = 'partial', 'Partial Success'

    # Sync type and source
    sync_type = models.CharField(
        max_length=20,
        choices=SyncTypeChoices.choices,
        verbose_name='Sync Type'
    )
    sync_source = models.CharField(
        max_length=20,
        default='wework',
        choices=SourceChoices.choices,
        verbose_name='Sync Source'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.RUNNING,
        verbose_name='Status'
    )

    # Timestamps
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Started At'
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Finished At'
    )

    # Statistics
    total_count = models.IntegerField(
        default=0,
        verbose_name='Total Count'
    )
    created_count = models.IntegerField(
        default=0,
        verbose_name='Created Count'
    )
    updated_count = models.IntegerField(
        default=0,
        verbose_name='Updated Count'
    )
    deleted_count = models.IntegerField(
        default=0,
        verbose_name='Deleted Count'
    )
    failed_count = models.IntegerField(
        default=0,
        verbose_name='Failed Count'
    )

    # Error information
    error_message = models.TextField(
        blank=True,
        verbose_name='Error Message'
    )
    error_details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Error Details'
    )

    class Meta:
        db_table = 'sso_sync_log'
        verbose_name = 'Sync Log'
        verbose_name_plural = 'Sync Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'sync_type']),
            models.Index(fields=['status']),
            models.Index(fields=['started_at']),
        ]

    def __str__(self):
        return f"{self.get_sync_type_display()} - {self.get_status_display()}"

    @property
    def duration(self) -> int:
        """
        Calculate sync duration in seconds.

        Returns:
            Duration in seconds, or None if not finished
        """
        if self.finished_at:
            delta = self.finished_at - self.started_at
            return int(delta.total_seconds())
        return None

    def mark_success(self, total: int = 0, created: int = 0,
                     updated: int = 0, deleted: int = 0):
        """Mark sync as successful."""
        from django.utils import timezone
        self.status = self.StatusChoices.SUCCESS
        self.total_count = total
        self.created_count = created
        self.updated_count = updated
        self.deleted_count = deleted
        self.failed_count = 0
        self.finished_at = timezone.now()
        self.save(update_fields=[
            'status', 'total_count', 'created_count',
            'updated_count', 'deleted_count', 'failed_count',
            'finished_at'
        ])

    def mark_failed(self, error_message: str, error_details: dict = None):
        """Mark sync as failed."""
        from django.utils import timezone
        self.status = self.StatusChoices.FAILED
        self.error_message = error_message
        self.error_details = error_details or {}
        self.finished_at = timezone.now()
        self.save(update_fields=[
            'status', 'error_message', 'error_details', 'finished_at'
        ])
