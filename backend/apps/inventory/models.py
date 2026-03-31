"""
Inventory models for GZEAMS.

Provides models for inventory tasks, snapshots, scans, and differences.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

from apps.common.mixins.workflow_status import WorkflowStatusMixin
from apps.common.models import BaseModel


class InventoryTask(BaseModel, WorkflowStatusMixin):
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
    STATUS_PENDING_APPROVAL = 'pending_approval'
    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_DRAFT, _('Draft')),
        (STATUS_PENDING_APPROVAL, _('Pending Approval')),
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

    def on_workflow_submitted(self):
        """Move the task into approval once the workflow starts."""
        self.status = self.STATUS_PENDING_APPROVAL
        self.save(update_fields=['status'])

    def on_workflow_approved(self):
        """Mark the task as ready to start after workflow approval."""
        self.status = self.STATUS_PENDING
        self.save(update_fields=['status'])

    def on_workflow_rejected(self):
        """Return the task to draft so it can be corrected and resubmitted."""
        self.status = self.STATUS_DRAFT
        self.save(update_fields=['status'])

    def on_workflow_cancelled(self):
        """Keep task cancellation aligned with workflow cancellation."""
        self.status = self.STATUS_CANCELLED
        self.save(update_fields=['status'])


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
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
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
    STATUS_IN_REVIEW = 'in_review'
    STATUS_APPROVED = 'approved'
    STATUS_EXECUTING = 'executing'
    STATUS_RESOLVED = 'resolved'
    STATUS_IGNORED = 'ignored'
    STATUS_CLOSED = 'closed'

    RESOLUTION_STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_CONFIRMED, _('Confirmed')),
        (STATUS_IN_REVIEW, _('In Review')),
        (STATUS_APPROVED, _('Approved')),
        (STATUS_EXECUTING, _('Executing')),
        (STATUS_RESOLVED, _('Resolved')),
        (STATUS_IGNORED, _('Ignored')),
        (STATUS_CLOSED, _('Closed')),
    ]

    CLOSURE_TYPE_LOCATION_CORRECTION = 'location_correction'
    CLOSURE_TYPE_CUSTODIAN_CORRECTION = 'custodian_correction'
    CLOSURE_TYPE_REPAIR = 'repair'
    CLOSURE_TYPE_DISPOSAL = 'disposal'
    CLOSURE_TYPE_CREATE_CARD = 'create_asset_card'
    CLOSURE_TYPE_FINANCIAL_ADJUSTMENT = 'financial_adjustment'
    CLOSURE_TYPE_INVALID = 'invalid_difference'

    CLOSURE_TYPE_CHOICES = [
        (CLOSURE_TYPE_LOCATION_CORRECTION, _('Location Correction')),
        (CLOSURE_TYPE_CUSTODIAN_CORRECTION, _('Custodian Correction')),
        (CLOSURE_TYPE_REPAIR, _('Repair')),
        (CLOSURE_TYPE_DISPOSAL, _('Disposal')),
        (CLOSURE_TYPE_CREATE_CARD, _('Create Asset Card')),
        (CLOSURE_TYPE_FINANCIAL_ADJUSTMENT, _('Financial Adjustment')),
        (CLOSURE_TYPE_INVALID, _('Invalid Difference')),
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
    owner = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_inventory_differences',
        help_text=_('Assigned owner for difference handling')
    )
    reviewed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_inventory_differences',
        help_text=_('User who submitted or reviewed the difference resolution')
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Review submission timestamp')
    )
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_inventory_differences',
        help_text=_('User who approved the difference resolution')
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Approval timestamp')
    )
    closed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_inventory_differences',
        help_text=_('User who closed the difference')
    )
    closure_type = models.CharField(
        max_length=50,
        choices=CLOSURE_TYPE_CHOICES,
        blank=True,
        help_text=_('Closure type for the difference')
    )
    closure_notes = models.TextField(
        blank=True,
        help_text=_('Closure notes')
    )
    closure_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Difference closure timestamp')
    )
    evidence_refs = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Evidence references for the difference closure')
    )
    linked_action_code = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Linked downstream action code')
    )

    def __str__(self):
        return f"{self.task.task_code} - {self.get_difference_type_display()}"

    def get_difference_type_display(self):
        """Get difference type display label."""
        return dict(self.DIFFERENCE_TYPE_CHOICES).get(self.difference_type, self.difference_type)

    def get_status_display(self):
        """Get status display label."""
        return dict(self.RESOLUTION_STATUS_CHOICES).get(self.status, self.status)

    def get_closure_type_display(self):
        """Get closure type display label."""
        return dict(self.CLOSURE_TYPE_CHOICES).get(self.closure_type, self.closure_type)


class InventoryFollowUp(BaseModel):
    """
    Inventory manual follow-up task model.

    Tracks downstream manual work required after a difference resolution cannot
    be completed automatically, such as finance adjustments or asset card
    creation.
    """

    class Meta:
        db_table = 'inventory_follow_ups'
        verbose_name = _('Inventory Follow-up')
        verbose_name_plural = _('Inventory Follow-ups')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'follow_up_code']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'assignee']),
            models.Index(fields=['task', 'status']),
            models.Index(fields=['difference', 'status']),
        ]

    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_COMPLETED, _('Completed')),
        (STATUS_CANCELLED, _('Cancelled')),
    ]

    follow_up_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_('Unique manual follow-up code')
    )
    task = models.ForeignKey(
        'InventoryTask',
        on_delete=models.CASCADE,
        related_name='follow_up_tasks',
        help_text=_('Related inventory task')
    )
    difference = models.ForeignKey(
        'InventoryDifference',
        on_delete=models.CASCADE,
        related_name='follow_up_tasks',
        help_text=_('Related inventory difference')
    )
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_follow_up_tasks',
        help_text=_('Related asset')
    )
    title = models.CharField(
        max_length=255,
        help_text=_('Follow-up task title')
    )
    closure_type = models.CharField(
        max_length=50,
        choices=InventoryDifference.CLOSURE_TYPE_CHOICES,
        blank=True,
        help_text=_('Closure type that triggered the follow-up')
    )
    linked_action_code = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Linked downstream action code')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        help_text=_('Follow-up task status')
    )
    assignee = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_inventory_follow_ups',
        help_text=_('Follow-up assignee')
    )
    assigned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Time when the follow-up was assigned')
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Time when the follow-up was completed')
    )
    completed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_inventory_follow_ups',
        help_text=_('User who completed the follow-up')
    )
    completion_notes = models.TextField(
        blank=True,
        help_text=_('Completion notes')
    )
    evidence_refs = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Evidence references for the follow-up completion')
    )
    follow_up_notification_id = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Latest follow-up notification ID')
    )
    follow_up_notification_url = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('Notification center route for the follow-up')
    )
    last_notified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Time when the latest reminder was sent')
    )
    reminder_count = models.PositiveIntegerField(
        default=0,
        help_text=_('Reminder count')
    )

    def __str__(self):
        return f"{self.follow_up_code} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.follow_up_code:
            self.follow_up_code = self._generate_follow_up_code()
        super().save(*args, **kwargs)

    def _generate_follow_up_code(self) -> str:
        """Generate a unique follow-up code."""
        from django.utils import timezone

        prefix = timezone.now().strftime('%Y%m')
        last_follow_up = InventoryFollowUp.all_objects.filter(
            follow_up_code__startswith=f"IFU{prefix}"
        ).order_by('-follow_up_code').first()
        if last_follow_up:
            seq = int(last_follow_up.follow_up_code[-4:]) + 1
        else:
            seq = 1
        return f"IFU{prefix}{seq:04d}"


class InventoryReconciliation(BaseModel):
    """
    Inventory Reconciliation Model.

    Stores the reconciliation result generated from a completed inventory task.
    """

    class Meta:
        db_table = 'inventory_reconciliations'
        verbose_name = _('Inventory Reconciliation')
        verbose_name_plural = _('Inventory Reconciliations')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'reconciliation_no']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['task', 'status']),
            models.Index(fields=['reconciled_at']),
        ]

    STATUS_DRAFT = 'draft'
    STATUS_SUBMITTED = 'submitted'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_DRAFT, _('Draft')),
        (STATUS_SUBMITTED, _('Submitted')),
        (STATUS_APPROVED, _('Approved')),
        (STATUS_REJECTED, _('Rejected')),
    ]

    reconciliation_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_('Unique reconciliation number')
    )
    task = models.ForeignKey(
        'InventoryTask',
        on_delete=models.CASCADE,
        related_name='reconciliations',
        help_text=_('Related inventory task')
    )
    normal_count = models.IntegerField(
        default=0,
        help_text=_('Normal item count in reconciliation')
    )
    abnormal_count = models.IntegerField(
        default=0,
        help_text=_('Abnormal item count in reconciliation')
    )
    difference_count = models.IntegerField(
        default=0,
        help_text=_('Difference count in reconciliation')
    )
    adjustment_count = models.IntegerField(
        default=0,
        help_text=_('Adjustment count in reconciliation')
    )
    adjustments = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Adjustment detail rows')
    )
    note = models.TextField(
        blank=True,
        help_text=_('Reconciliation note')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
        help_text=_('Reconciliation status')
    )
    reconciled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Reconciliation time')
    )
    reconciled_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_reconciliations',
        help_text=_('User who created the reconciliation')
    )
    current_approver = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pending_inventory_reconciliations',
        help_text=_('Current reconciliation approver')
    )
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Reconciliation submission time')
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Reconciliation approval time')
    )
    rejected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Reconciliation rejection time')
    )

    def __str__(self):
        return f"{self.reconciliation_no} - {self.task.task_code}"

    def save(self, *args, **kwargs):
        if not self.reconciliation_no:
            self.reconciliation_no = self._generate_reconciliation_no()
        super().save(*args, **kwargs)

    def _generate_reconciliation_no(self) -> str:
        """Generate a unique reconciliation number."""
        from django.utils import timezone

        prefix = timezone.now().strftime('%Y%m')
        last_record = InventoryReconciliation.all_objects.filter(
            reconciliation_no__startswith=f"IRC{prefix}"
        ).order_by('-reconciliation_no').first()
        if last_record:
            sequence = int(last_record.reconciliation_no[-4:]) + 1
        else:
            sequence = 1
        return f"IRC{prefix}{sequence:04d}"


class InventoryReport(BaseModel):
    """
    Inventory Report Model.

    Stores generated inventory report snapshots and approval state.
    """

    class Meta:
        db_table = 'inventory_reports'
        verbose_name = _('Inventory Report')
        verbose_name_plural = _('Inventory Reports')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'report_no']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['task', 'status']),
            models.Index(fields=['generated_at']),
        ]

    STATUS_DRAFT = 'draft'
    STATUS_PENDING_APPROVAL = 'pending_approval'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_DRAFT, _('Draft')),
        (STATUS_PENDING_APPROVAL, _('Pending Approval')),
        (STATUS_APPROVED, _('Approved')),
        (STATUS_REJECTED, _('Rejected')),
    ]

    report_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_('Unique inventory report number')
    )
    task = models.ForeignKey(
        'InventoryTask',
        on_delete=models.CASCADE,
        related_name='reports',
        help_text=_('Related inventory task')
    )
    template_id = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Selected report template ID')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
        help_text=_('Inventory report status')
    )
    summary = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Top-level report summary')
    )
    report_data = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Structured report payload')
    )
    approvals = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Approval history payload')
    )
    generated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_inventory_reports',
        help_text=_('User who generated the report')
    )
    generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Report generation time')
    )
    current_approver = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pending_inventory_reports',
        help_text=_('Current report approver')
    )
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Report submission time')
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Report approval time')
    )
    rejected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Report rejection time')
    )

    def __str__(self):
        return f"{self.report_no} - {self.task.task_code}"

    def save(self, *args, **kwargs):
        if not self.report_no:
            self.report_no = self._generate_report_no()
        super().save(*args, **kwargs)

    def _generate_report_no(self) -> str:
        """Generate a unique report number."""
        from django.utils import timezone

        prefix = timezone.now().strftime('%Y%m')
        last_record = InventoryReport.all_objects.filter(
            report_no__startswith=f"IRP{prefix}"
        ).order_by('-report_no').first()
        if last_record:
            sequence = int(last_record.report_no[-4:]) + 1
        else:
            sequence = 1
        return f"IRP{prefix}{sequence:04d}"
