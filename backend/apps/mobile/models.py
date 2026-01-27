"""
Mobile Enhancement Models.

Provides models for mobile device management, offline data synchronization,
and mobile approval features:
- MobileDevice: Device registration and management
- DeviceSecurityLog: Security event logging
- OfflineData: Offline operation data
- SyncConflict: Data sync conflict tracking
- SyncLog: Synchronization operation logs
- ApprovalDelegate: Approval delegation settings
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.common.models import BaseModel


class MobileDevice(BaseModel):
    """
    Mobile Device Management

    Records user mobile device information for security and sync management.
    Automatically inherits organization isolation, soft delete, audit fields,
    and custom fields from BaseModel.
    """
    DEVICE_TYPES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('h5', 'H5'),
    ]

    # User association
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mobile_devices',
        help_text='Device owner'
    )

    # Device information
    device_id = models.CharField(
        max_length=200,
        unique=True,
        db_index=True,
        help_text='Unique device identifier'
    )
    device_name = models.CharField(max_length=100, help_text='Device name')
    device_type = models.CharField(
        max_length=20,
        choices=DEVICE_TYPES,
        help_text='Device platform type'
    )
    os_version = models.CharField(max_length=50, blank=True, help_text='OS version')
    app_version = models.CharField(max_length=50, blank=True, help_text='App version')

    # Device details (JSON format)
    device_info = models.JSONField(
        default=dict,
        help_text='Device details including screen, CPU, memory, etc.'
    )

    # Binding status
    is_bound = models.BooleanField(default=True, help_text='Device binding status')
    is_active = models.BooleanField(default=True, help_text='Device activation status')

    # Last activity information
    last_login_at = models.DateTimeField(
        default=timezone.now,
        help_text='Last login time'
    )
    last_login_ip = models.GenericIPAddressField(
        null=True, blank=True,
        help_text='Last login IP'
    )
    last_sync_at = models.DateTimeField(
        null=True, blank=True,
        help_text='Last sync time'
    )
    last_location = models.JSONField(
        null=True, blank=True,
        help_text='Last location {latitude, longitude, address}'
    )

    # Security settings
    enable_biometric = models.BooleanField(default=False, help_text='Enable biometric authentication')
    allow_offline = models.BooleanField(default=True, help_text='Allow offline mode')

    class Meta:
        db_table = 'mobile_device'
        verbose_name = 'Mobile Device'
        verbose_name_plural = 'Mobile Devices'
        ordering = ['-last_login_at']
        indexes = [
            models.Index(fields=['user', 'is_bound']),
            models.Index(fields=['device_id']),
            models.Index(fields=['-last_login_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.device_name}"

    def unbind(self):
        """Unbind device"""
        self.is_bound = False
        self.is_active = False
        self.save()

    def update_last_activity(self, ip=None, location=None):
        """Update device last activity information"""
        self.last_login_at = timezone.now()
        if ip:
            self.last_login_ip = ip
        if location:
            self.last_location = location
        self.save()


class DeviceSecurityLog(BaseModel):
    """
    Device Security Log

    Records security events for mobile devices.
    Automatically inherits organization isolation, soft delete, audit fields,
    and custom fields from BaseModel.
    """
    EVENT_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('bind', 'Bind'),
        ('unbind', 'Unbind'),
        ('sync', 'Sync'),
        ('suspicious', 'Suspicious'),
    ]

    device = models.ForeignKey(
        MobileDevice,
        on_delete=models.CASCADE,
        related_name='security_logs',
        help_text='Associated device'
    )
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, help_text='Event type')
    ip_address = models.GenericIPAddressField(help_text='IP address')
    location = models.JSONField(null=True, blank=True, help_text='Location information')
    user_agent = models.TextField(blank=True, help_text='User Agent string')
    details = models.JSONField(default=dict, help_text='Event details')

    class Meta:
        db_table = 'mobile_device_security_log'
        verbose_name = 'Device Security Log'
        verbose_name_plural = 'Device Security Logs'
        ordering = ['-created_at']


class OfflineData(BaseModel):
    """
    Offline Data

    Stores offline operation data uploaded from clients.
    Automatically inherits organization isolation, soft delete, audit fields,
    and custom fields from BaseModel.
    """
    OPERATION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]

    SYNC_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('synced', 'Synced'),
        ('conflict', 'Conflict'),
        ('failed', 'Failed'),
    ]

    # Association
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='offline_data',
        help_text='Data owner'
    )
    device = models.ForeignKey(
        MobileDevice,
        on_delete=models.SET_NULL,
        null=True,
        related_name='offline_data',
        help_text='Source device'
    )

    # Data information
    table_name = models.CharField(max_length=100, help_text='Target table name')
    record_id = models.CharField(max_length=100, help_text='Record identifier')
    operation = models.CharField(max_length=20, choices=OPERATION_TYPES, help_text='Operation type')

    # Data content
    data = models.JSONField(help_text='Operation data')
    old_data = models.JSONField(null=True, blank=True, help_text='Original data for update/delete')

    # Sync status
    sync_status = models.CharField(
        max_length=20,
        choices=SYNC_STATUS,
        default='pending',
        help_text='Synchronization status'
    )
    synced_at = models.DateTimeField(null=True, blank=True, help_text='Sync completion time')
    sync_error = models.TextField(blank=True, help_text='Sync error message')

    # Version information
    client_version = models.IntegerField(help_text='Client data version')
    server_version = models.IntegerField(null=True, blank=True, help_text='Server data version')

    # Client timestamps
    client_created_at = models.DateTimeField(
        default=timezone.now,
        help_text='Client creation time'
    )
    client_updated_at = models.DateTimeField(
        default=timezone.now,
        help_text='Client update time'
    )

    class Meta:
        db_table = 'mobile_offline_data'
        verbose_name = 'Offline Data'
        verbose_name_plural = 'Offline Data'
        ordering = ['client_created_at']
        indexes = [
            models.Index(fields=['user', 'sync_status']),
            models.Index(fields=['table_name', 'record_id']),
            models.Index(fields=['-client_created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.operation} {self.table_name}:{self.record_id}"

    def mark_as_synced(self, server_version=None):
        """Mark offline data as synced"""
        self.sync_status = 'synced'
        self.synced_at = timezone.now()
        if server_version:
            self.server_version = server_version
        self.save()


class SyncConflict(BaseModel):
    """
    Sync Conflict

    Records data conflicts during synchronization.
    Automatically inherits organization isolation, soft delete, audit fields,
    and custom fields from BaseModel.
    """
    CONFLICT_TYPES = [
        ('version_mismatch', 'Version Mismatch'),
        ('duplicate_create', 'Duplicate Create'),
        ('delete_modified', 'Delete Modified'),
        ('concurrent_modify', 'Concurrent Modify'),
    ]

    RESOLUTIONS = [
        ('pending', 'Pending'),
        ('server_wins', 'Server Wins'),
        ('client_wins', 'Client Wins'),
        ('merge', 'Merge'),
        ('manual', 'Manual'),
    ]

    # Association
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sync_conflicts',
        help_text='Affected user'
    )
    offline_data = models.OneToOneField(
        OfflineData,
        on_delete=models.CASCADE,
        related_name='conflict',
        help_text='Related offline data'
    )

    # Conflict information
    conflict_type = models.CharField(max_length=50, choices=CONFLICT_TYPES, help_text='Conflict type')
    table_name = models.CharField(max_length=100, help_text='Affected table')
    record_id = models.CharField(max_length=100, help_text='Affected record ID')

    # Conflict data
    local_data = models.JSONField(help_text='Local (client) data')
    server_data = models.JSONField(help_text='Server data')
    merged_data = models.JSONField(null=True, blank=True, help_text='Merged data')

    # Resolution
    resolution = models.CharField(
        max_length=20,
        choices=RESOLUTIONS,
        default='pending',
        help_text='Resolution method'
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='resolved_conflicts',
        help_text='User who resolved'
    )
    resolved_at = models.DateTimeField(null=True, blank=True, help_text='Resolution time')
    resolution_note = models.TextField(blank=True, help_text='Resolution notes')

    class Meta:
        db_table = 'mobile_sync_conflict'
        verbose_name = 'Sync Conflict'
        verbose_name_plural = 'Sync Conflicts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'resolution']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.table_name}:{self.record_id} - {self.conflict_type}"

    def mark_resolved(self, resolution, merged_data=None):
        """Mark conflict as resolved"""
        self.resolution = resolution
        self.resolved_at = timezone.now()
        if merged_data is not None:
            self.merged_data = merged_data
        self.save()


class SyncLog(BaseModel):
    """
    Sync Log

    Records detailed information about data synchronization operations.
    Automatically inherits organization isolation, soft delete, audit fields,
    and custom fields from BaseModel.
    """
    SYNC_TYPES = [
        ('full', 'Full Sync'),
        ('incremental', 'Incremental Sync'),
        ('manual', 'Manual Sync'),
    ]
    SYNC_DIRECTIONS = [
        ('upload', 'Upload'),
        ('download', 'Download'),
        ('bidirectional', 'Bidirectional'),
    ]
    SYNC_STATUS = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('partial_success', 'Partial Success'),
        ('failed', 'Failed'),
    ]

    # Association
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sync_logs',
        help_text='Sync initiator'
    )
    device = models.ForeignKey(
        MobileDevice,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sync_logs',
        help_text='Sync device'
    )

    # Sync information
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES, help_text='Sync type')
    sync_direction = models.CharField(max_length=20, choices=SYNC_DIRECTIONS, help_text='Sync direction')
    status = models.CharField(max_length=20, choices=SYNC_STATUS, help_text='Sync status')

    # Sync content
    tables = models.JSONField(default=list, help_text='Synced tables')

    # Statistics
    upload_count = models.IntegerField(default=0, help_text='Uploaded records')
    download_count = models.IntegerField(default=0, help_text='Downloaded records')
    conflict_count = models.IntegerField(default=0, help_text='Conflict count')
    error_count = models.IntegerField(default=0, help_text='Error count')

    # Timing
    started_at = models.DateTimeField(
        default=timezone.now,
        help_text='Start time'
    )
    finished_at = models.DateTimeField(null=True, blank=True, help_text='End time')
    duration = models.IntegerField(null=True, blank=True, help_text='Duration (seconds)')

    # Version
    client_version = models.IntegerField(default=0, help_text='Client version')
    server_version = models.IntegerField(default=0, help_text='Server version')

    # Error info
    error_message = models.TextField(blank=True, help_text='Error message')
    error_details = models.JSONField(null=True, blank=True, help_text='Error details')

    # Network
    network_type = models.CharField(max_length=20, blank=True, help_text='Network type')
    data_size = models.BigIntegerField(default=0, help_text='Data size (bytes)')

    class Meta:
        db_table = 'mobile_sync_log'
        verbose_name = 'Sync Log'
        verbose_name_plural = 'Sync Logs'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', '-started_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.sync_type} {self.sync_direction} - {self.status}"

    def calculate_duration(self):
        """Calculate sync duration in seconds"""
        if self.started_at and self.finished_at:
            self.duration = int((self.finished_at - self.started_at).total_seconds())
            self.save()


class ApprovalDelegate(BaseModel):
    """
    Approval Delegate

    Sets up approval delegation/proxy settings.
    Automatically inherits organization isolation, soft delete, audit fields,
    and custom fields from BaseModel.
    """
    DELEGATE_TYPES = [
        ('temporary', 'Temporary'),
        ('permanent', 'Permanent'),
    ]
    DELEGATE_SCOPES = [
        ('all', 'All Approvals'),
        ('specific', 'Specific Workflows'),
        ('category', 'Specific Categories'),
    ]

    # Delegation
    delegator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delegated_approvals',
        help_text='Delegation giver'
    )
    delegate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_delegations',
        help_text='Delegation receiver'
    )

    # Configuration
    delegate_type = models.CharField(
        max_length=20,
        choices=DELEGATE_TYPES,
        default='temporary',
        help_text='Delegation type'
    )
    delegate_scope = models.CharField(
        max_length=20,
        choices=DELEGATE_SCOPES,
        default='all',
        help_text='Delegation scope'
    )

    # Time range
    start_time = models.DateTimeField(
        default=timezone.now,
        help_text='Start time'
    )
    end_time = models.DateTimeField(null=True, blank=True, help_text='End time')

    # Scope configuration
    scope_config = models.JSONField(
        default=dict,
        help_text='Scope configuration based on scope_type'
    )

    # Reason
    reason = models.TextField(blank=True, help_text='Delegation reason')

    # Status
    is_active = models.BooleanField(default=True, help_text='Active status')
    is_revoked = models.BooleanField(default=False, help_text='Revoked status')
    revoked_at = models.DateTimeField(null=True, blank=True, help_text='Revocation time')
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='revoked_delegations',
        help_text='Revoked by'
    )
    revoked_reason = models.TextField(blank=True, help_text='Revocation reason')

    # Statistics
    approved_count = models.IntegerField(default=0, help_text='Approved count')

    class Meta:
        db_table = 'mobile_approval_delegate'
        verbose_name = 'Approval Delegate'
        verbose_name_plural = 'Approval Delegates'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['delegator', 'is_active']),
            models.Index(fields=['delegate', 'is_active']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.delegator.username} -> {self.delegate.username}"

    def is_valid(self):
        """Check if delegation is valid"""
        if not self.is_active or self.is_revoked:
            return False
        from django.utils import timezone
        now = timezone.now()
        if self.start_time > now:
            return False
        if self.end_time and self.end_time < now:
            return False
        return True

    def revoke(self, revoked_by, reason=''):
        """Revoke delegation"""
        self.is_active = False
        self.is_revoked = True
        self.revoked_at = timezone.now()
        self.revoked_by = revoked_by
        self.revoked_reason = reason
        self.save()
