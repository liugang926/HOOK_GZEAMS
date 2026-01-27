"""
Inventory models for GZEAMS.

Provides models for inventory tasks, snapshots, scans, and differences.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class InventoryTask(BaseModel):
    """
    Inventory Task Model.

    Represents an inventory task for asset counting.
    Supports full, partial, department, and category inventory types.

    Inherits from BaseModel:
    - organization: Multi-tenant data isolation
    - is_deleted, deleted_at: Soft delete support
    - created_at, updated_at, created_by: Audit fields
    - custom_fields: Dynamic metadata storage (JSONB)
    """

    class Meta:
        db_table = 'inventory_tasks'
        verbose_name = _('Inventory Task')
        verbose_name_plural = _('Inventory Tasks')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'task_code']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'inventory_type']),
            models.Index(fields=['organization', 'planned_date']),
            models.Index(fields=['-created_at']),
        ]

    # ========== Status Choices ==========
    STATUS_DRAFT = 'draft'
    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_DRAFT, _('Draft')),
        (STATUS_PENDING, _('Pending')),
        (STATUS_IN_PROGRESS, _('In Progress')),
        (STATUS_COMPLETED, _('Completed')),
        (STATUS_CANCELLED, _('Cancelled')),
    ]

    # ========== Inventory Type Choices ==========
    TYPE_FULL = 'full'
    TYPE_PARTIAL = 'partial'
    TYPE_DEPARTMENT = 'department'
    TYPE_CATEGORY = 'category'

    INVENTORY_TYPE_CHOICES = [
        (TYPE_FULL, _('Full Inventory')),
        (TYPE_PARTIAL, _('Partial Inventory')),
        (TYPE_DEPARTMENT, _('Department Inventory')),
        (TYPE_CATEGORY, _('Category Inventory')),
    ]

    # ========== Basic Information ==========
    task_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_('Unique task code (auto-generated: PD+YYYYMM+NNNN)')
    )
    task_name = models.CharField(
        max_length=200,
        help_text=_('Task name')
    )
    description = models.TextField(
        blank=True,
        help_text=_('Task description')
    )

    # ========== Inventory Configuration ==========
    inventory_type = models.CharField(
        max_length=20,
        choices=INVENTORY_TYPE_CHOICES,
        default=TYPE_FULL,
        db_index=True,
        help_text=_('Inventory type')
    )

    # For department inventory
    department = models.ForeignKey(
        'organizations.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_tasks',
        help_text=_('Department for department inventory')
    )

    # For category inventory
    category = models.ForeignKey(
        'assets.AssetCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_tasks',
        help_text=_('Category for category inventory')
    )

    # For partial inventory (percentage)
    sample_ratio = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MinValueValidator(100)],
        help_text=_('Sample ratio for partial inventory (1-100)')
    )

    # ========== Status and Dates ==========
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
        help_text=_('Task status')
    )
    planned_date = models.DateField(
        help_text=_('Planned inventory date')
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Actual start time')
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Completion time')
    )

    # ========== Statistics (Cached) ==========
    total_count = models.IntegerField(
        default=0,
        help_text=_('Total assets to inventory')
    )
    scanned_count = models.IntegerField(
        default=0,
        help_text=_('Scanned assets count')
    )
    normal_count = models.IntegerField(
        default=0,
        help_text=_('Normal assets count')
    )
    surplus_count = models.IntegerField(
        default=0,
        help_text=_('Surplus assets count')
    )
    missing_count = models.IntegerField(
        default=0,
        help_text=_('Missing assets count')
    )
    damaged_count = models.IntegerField(
        default=0,
        help_text=_('Damaged assets count')
    )
    location_changed_count = models.IntegerField(
        default=0,
        help_text=_('Location changed assets count')
    )

    # ========== Notes ==========
    notes = models.TextField(
        blank=True,
        help_text=_('Inventory notes')
    )

    def __str__(self):
        return f"{self.task_code} - {self.task_name}"

    def save(self, *args, **kwargs):
        if not self.task_code:
            self.task_code = self._generate_task_code()
        super().save(*args, **kwargs)

    def _generate_task_code(self):
        """
        Generate task code using SequenceService.

        Uses the INVENTORY_NO sequence rule configured in system.
        Falls back to legacy logic if SequenceService is unavailable.
        """
        try:
            from apps.system.services import SequenceService
            return SequenceService.get_next_value(
                'INVENTORY_NO',
                organization_id=self.organization_id
            )
        except Exception:
            # Fallback to legacy generation
            from django.utils import timezone
            prefix = timezone.now().strftime('%Y%m')
            last_task = InventoryTask.all_objects.filter(
                task_code__startswith=f"PD{prefix}"
            ).order_by('-task_code').first()
            if last_task:
                seq = int(last_task.task_code[-4:]) + 1
            else:
                seq = 1
            return f"PD{prefix}{seq:04d}"

    @property
    def progress_percentage(self):
        """Calculate progress percentage."""
        if self.total_count == 0:
            return 0
        return round((self.scanned_count / self.total_count) * 100, 2)

    def get_status_label(self):
        """Get status display label."""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    def get_inventory_type_label(self):
        """Get inventory type display label."""
        return dict(self.INVENTORY_TYPE_CHOICES).get(self.inventory_type, self.inventory_type)

    def can_start(self):
        """Check if task can be started."""
        return self.status == self.STATUS_PENDING

    def can_complete(self):
        """Check if task can be completed."""
        return self.status == self.STATUS_IN_PROGRESS

    def can_modify(self):
        """Check if task can be modified."""
        return self.status == self.STATUS_DRAFT


class InventoryTaskExecutor(BaseModel):
    """
    Inventory Task Executor Model (M2M through model).

    Represents executors assigned to an inventory task.
    """

    class Meta:
        db_table = 'inventory_task_executors'
        verbose_name = _('Inventory Task Executor')
        verbose_name_plural = _('Inventory Task Executors')
        unique_together = [['task', 'executor']]
        indexes = [
            models.Index(fields=['task', 'executor']),
            models.Index(fields=['executor', '-created_at']),
        ]

    task = models.ForeignKey(
        'InventoryTask',
        on_delete=models.CASCADE,
        related_name='executors_relation',
        help_text=_('Inventory task')
    )
    executor = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='inventory_tasks',
        help_text=_('Task executor')
    )
    is_primary = models.BooleanField(
        default=False,
        help_text=_('Primary executor indicator')
    )
    completed_count = models.IntegerField(
        default=0,
        help_text=_('Completed scan count by this executor')
    )

    def __str__(self):
        return f"{self.task.task_code} - {self.executor.username}"


class InventorySnapshot(BaseModel):
    """
    Inventory Snapshot Model.

    Records the state of an asset at the time of inventory task creation.
    Provides immutable snapshot for comparison with actual scan results.

    Inherits from BaseModel for organization isolation and audit trail.
    """

    class Meta:
        db_table = 'inventory_snapshots'
        verbose_name = _('Inventory Snapshot')
        verbose_name_plural = _('Inventory Snapshots')
        ordering = ['task', 'asset_code']
        indexes = [
            models.Index(fields=['task', 'asset']),
            models.Index(fields=['task', 'asset_code']),
            models.Index(fields=['task', 'scanned']),
        ]
        unique_together = [['task', 'asset']]

    task = models.ForeignKey(
        'InventoryTask',
        on_delete=models.CASCADE,
        related_name='snapshots',
        help_text=_('Related inventory task')
    )
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.CASCADE,
        related_name='inventory_snapshots',
        help_text=_('Related asset')
    )

    # Snapshot data (immutable, copied from asset)
    asset_code = models.CharField(
        max_length=50,
        help_text=_('Asset code (snapshot)')
    )
    asset_name = models.CharField(
        max_length=200,
        help_text=_('Asset name (snapshot)')
    )
    asset_category_id = models.CharField(
        max_length=50,
        help_text=_('Asset category ID (snapshot)')
    )
    asset_category_name = models.CharField(
        max_length=200,
        help_text=_('Asset category name (snapshot)')
    )

    # Location and custodian snapshot
    location_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text=_('Location ID (snapshot)')
    )
    location_name = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Location name (snapshot)')
    )
    custodian_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text=_('Custodian user ID (snapshot)')
    )
    custodian_name = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Custodian name (snapshot)')
    )
    department_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text=_('Department ID (snapshot)')
    )
    department_name = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Department name (snapshot)')
    )

    # Status snapshot
    asset_status = models.CharField(
        max_length=20,
        help_text=_('Asset status (snapshot)')
    )

    # Additional snapshot data
    snapshot_data = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Complete snapshot data (JSON)')
    )

    # Scan tracking
    scanned = models.BooleanField(
        default=False,
        db_index=True,
        help_text=_('Whether asset has been scanned')
    )
    scanned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('First scan timestamp')
    )
    scan_count = models.IntegerField(
        default=0,
        help_text=_('Number of times scanned')
    )

    def __str__(self):
        return f"{self.task.task_code} - {self.asset_code}"


class InventoryScan(BaseModel):
    """
    Inventory Scan Record Model.

    Records each scan action during inventory execution.

    Inherits from BaseModel for organization isolation and audit trail.
    """

    class Meta:
        db_table = 'inventory_scans'
        verbose_name = _('Inventory Scan')
        verbose_name_plural = _('Inventory Scans')
        ordering = ['-scanned_at']
        indexes = [
            models.Index(fields=['task', 'asset']),
            models.Index(fields=['task', 'scanned_by']),
            models.Index(fields=['task', '-scanned_at']),
            models.Index(fields=['scan_status']),
            models.Index(fields=['qr_code']),
        ]

    # ========== Scan Status Choices ==========
    STATUS_NORMAL = 'normal'
    STATUS_DAMAGED = 'damaged'
    STATUS_MISSING = 'missing'
    STATUS_LOCATION_CHANGED = 'location_changed'
    STATUS_CUSTODIAN_CHANGED = 'custodian_changed'
    STATUS_SURPLUS = 'surplus'

    SCAN_STATUS_CHOICES = [
        (STATUS_NORMAL, _('Normal')),
        (STATUS_DAMAGED, _('Damaged')),
        (STATUS_MISSING, _('Missing')),
        (STATUS_LOCATION_CHANGED, _('Location Changed')),
        (STATUS_CUSTODIAN_CHANGED, _('Custodian Changed')),
        (STATUS_SURPLUS, _('Surplus')),
    ]

    # ========== Scan Method Choices ==========
    METHOD_QR = 'qr'
    METHOD_RFID = 'rfid'
    METHOD_MANUAL = 'manual'

    SCAN_METHOD_CHOICES = [
        (METHOD_QR, _('QR Code')),
        (METHOD_RFID, _('RFID')),
        (METHOD_MANUAL, _('Manual')),
    ]

    # ========== Basic Information ==========
    task = models.ForeignKey(
        'InventoryTask',
        on_delete=models.CASCADE,
        related_name='scans',
        help_text=_('Related inventory task')
    )
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_scans',
        help_text=_('Scanned asset (null for surplus)')
    )

    # ========== Scan Information ==========
    qr_code = models.CharField(
        max_length=500,
        db_index=True,
        help_text=_('Scanned QR code')
    )
    scanned_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='inventory_scans',
        help_text=_('Scanner operator')
    )
    scanned_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Scan timestamp')
    )
    scan_method = models.CharField(
        max_length=20,
        choices=SCAN_METHOD_CHOICES,
        default=METHOD_QR,
        help_text=_('Scan method')
    )

    # ========== Scan Result ==========
    scan_status = models.CharField(
        max_length=20,
        choices=SCAN_STATUS_CHOICES,
        default=STATUS_NORMAL,
        db_index=True,
        help_text=_('Scan result status')
    )

    # ========== Original Values (from snapshot) ==========
    original_location_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text=_('Original location ID')
    )
    original_location_name = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Original location name')
    )
    original_custodian_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text=_('Original custodian ID')
    )
    original_custodian_name = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Original custodian name')
    )

    # ========== Actual Values (from scan) ==========
    actual_location_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text=_('Actual location ID')
    )
    actual_location_name = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Actual location name')
    )
    actual_custodian_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text=_('Actual custodian ID')
    )
    actual_custodian_name = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Actual custodian name')
    )

    # ========== Additional Information ==========
    photos = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Photo URLs')
    )
    remark = models.TextField(
        blank=True,
        help_text=_('Scan remark')
    )

    # ========== GPS Location ==========
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text=_('GPS latitude')
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text=_('GPS longitude')
    )

    def __str__(self):
        return f"{self.task.task_code} - {self.qr_code}"

    def get_scan_status_label(self):
        """Get scan status display label."""
        return dict(self.SCAN_STATUS_CHOICES).get(self.scan_status, self.scan_status)


class InventoryDifference(BaseModel):
    """
    Inventory Difference Model.

    Records discrepancies found during inventory.
    Used for tracking and resolving differences.

    Inherits from BaseModel for organization isolation and audit trail.
    """

    class Meta:
        db_table = 'inventory_differences'
        verbose_name = _('Inventory Difference')
        verbose_name_plural = _('Inventory Differences')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task', 'asset']),
            models.Index(fields=['task', 'difference_type']),
            models.Index(fields=['task', 'status']),
            models.Index(fields=['-created_at']),
        ]

    # ========== Difference Type Choices ==========
    TYPE_MISSING = 'missing'
    TYPE_SURPLUS = 'surplus'
    TYPE_DAMAGED = 'damaged'
    TYPE_LOCATION_MISMATCH = 'location_mismatch'
    TYPE_CUSTODIAN_MISMATCH = 'custodian_mismatch'

    DIFFERENCE_TYPE_CHOICES = [
        (TYPE_MISSING, _('Missing')),
        (TYPE_SURPLUS, _('Surplus')),
        (TYPE_DAMAGED, _('Damaged')),
        (TYPE_LOCATION_MISMATCH, _('Location Mismatch')),
        (TYPE_CUSTODIAN_MISMATCH, _('Custodian Mismatch')),
    ]

    # ========== Resolution Status Choices ==========
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_RESOLVED = 'resolved'
    STATUS_IGNORED = 'ignored'

    RESOLUTION_STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_CONFIRMED, _('Confirmed')),
        (STATUS_RESOLVED, _('Resolved')),
        (STATUS_IGNORED, _('Ignored')),
    ]

    # ========== Basic Information ==========
    task = models.ForeignKey(
        'InventoryTask',
        on_delete=models.CASCADE,
        related_name='differences',
        help_text=_('Related inventory task')
    )
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_differences',
        help_text=_('Related asset (null for surplus)')
    )

    # ========== Difference Details ==========
    difference_type = models.CharField(
        max_length=20,
        choices=DIFFERENCE_TYPE_CHOICES,
        db_index=True,
        help_text=_('Type of difference')
    )
    description = models.TextField(
        help_text=_('Difference description')
    )

    # Expected vs Actual
    expected_quantity = models.IntegerField(
        default=1,
        help_text=_('Expected quantity')
    )
    actual_quantity = models.IntegerField(
        default=0,
        help_text=_('Actual quantity')
    )
    quantity_difference = models.IntegerField(
        default=0,
        help_text=_('Quantity difference')
    )

    # Field-level differences
    expected_location = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Expected location')
    )
    actual_location = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Actual location')
    )
    expected_custodian = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Expected custodian')
    )
    actual_custodian = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Actual custodian')
    )

    # ========== Resolution ==========
    status = models.CharField(
        max_length=20,
        choices=RESOLUTION_STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        help_text=_('Resolution status')
    )
    resolution = models.TextField(
        blank=True,
        help_text=_('Resolution description')
    )
    resolved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_differences',
        help_text=_('User who resolved the difference')
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Resolution timestamp')
    )

    def __str__(self):
        return f"{self.task.task_code} - {self.get_difference_type_display()}"

    def get_difference_type_display(self):
        """Get difference type display label."""
        return dict(self.DIFFERENCE_TYPE_CHOICES).get(self.difference_type, self.difference_type)

    def get_status_display(self):
        """Get status display label."""
        return dict(self.RESOLUTION_STATUS_CHOICES).get(self.status, self.status)
