"""
Lifecycle Management Models

Models for managing the complete asset lifecycle:
- PurchaseRequest: Asset procurement requests with approval workflow
- AssetReceipt: Goods receipt with quality inspection
- Maintenance: Repair requests and maintenance records
- MaintenancePlan: Scheduled maintenance plans
- MaintenanceTask: Generated maintenance tasks
- DisposalRequest: Asset disposal requests
- DisposalItem: Disposal item details with appraisal
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from apps.common.models import BaseModel


# ========== Purchase Request Models ==========

class PurchaseRequestStatus(models.TextChoices):
    """Purchase request status choices"""
    DRAFT = 'draft', 'Draft'
    SUBMITTED = 'submitted', 'Submitted'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class PurchaseRequest(BaseModel):
    """
    Purchase Request Model

    Manages asset procurement requests from employees.
    Inherits from BaseModel for organization isolation and soft delete.
    """
    class Meta:
        db_table = 'lifecycle_purchase_request'
        verbose_name = 'Purchase Request'
        verbose_name_plural = 'Purchase Requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'request_no']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'applicant']),
            models.Index(fields=['organization', 'department']),
        ]

    # Basic Information
    request_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Request number (auto-generated: PR+YYYYMM+NNNN)'
    )
    status = models.CharField(
        max_length=20,
        choices=PurchaseRequestStatus.choices,
        default=PurchaseRequestStatus.DRAFT,
        db_index=True,
        help_text='Request status'
    )

    # Applicant Information
    applicant = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='purchase_requests',
        help_text='Request applicant'
    )
    department = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.PROTECT,
        related_name='purchase_requests',
        limit_choices_to={'org_type': 'department'},
        help_text='Applicant department'
    )

    # Request Details
    request_date = models.DateField(help_text='Request date')
    expected_date = models.DateField(help_text='Expected delivery date')
    reason = models.TextField(help_text='Request reason')
    budget_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Budget amount'
    )
    # Note: Cost center field removed as CostCenter model doesn't exist yet
    # Can be added later via custom_fields or dedicated CostCenter model

    # Approval Information
    current_approver = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pending_purchase_approvals',
        help_text='Current approver'
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Approval time'
    )
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_purchase_requests',
        help_text='Approver'
    )
    approval_comment = models.TextField(
        blank=True,
        help_text='Approval comment'
    )

    # M18 Integration (external procurement system)
    m18_purchase_order_no = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        help_text='M18 purchase order number'
    )
    pushed_to_m18_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Time pushed to M18'
    )
    m18_sync_status = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text='M18 sync status'
    )

    # Additional Information
    remark = models.TextField(
        blank=True,
        help_text='Additional remarks'
    )

    def __str__(self):
        return f"{self.request_no} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        """Generate request number if not set"""
        if not self.request_no:
            self.request_no = self._generate_request_no()
        super().save(*args, **kwargs)

    def _generate_request_no(self):
        """Generate request number: PR+YYYYMM+NNNN"""
        prefix = timezone.now().strftime('%Y%m')
        last_request = PurchaseRequest.objects.filter(
            request_no__startswith=f"PR{prefix}"
        ).order_by('-request_no').first()
        if last_request:
            seq = int(last_request.request_no[-4:]) + 1
        else:
            seq = 1
        return f"PR{prefix}{seq:04d}"

    def calculate_total_amount(self):
        """Calculate total amount from items"""
        total = sum(item.total_amount for item in self.items.all())
        return total


class PurchaseRequestItem(BaseModel):
    """
    Purchase Request Line Item

    Line items for purchase requests.
    Inherits from BaseModel for organization isolation and soft delete.
    """
    class Meta:
        db_table = 'lifecycle_purchase_request_item'
        verbose_name = 'Purchase Request Item'
        verbose_name_plural = 'Purchase Request Items'
        unique_together = [['purchase_request', 'sequence']]
        ordering = ['sequence']
        indexes = [
            models.Index(fields=['organization', 'purchase_request']),
            models.Index(fields=['organization', 'asset_category']),
        ]

    # References
    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Purchase request'
    )
    asset_category = models.ForeignKey(
        'assets.AssetCategory',
        on_delete=models.PROTECT,
        related_name='purchase_request_items',
        help_text='Asset category'
    )

    # Item Information
    sequence = models.IntegerField(default=1, help_text='Sequence number')
    item_name = models.CharField(max_length=200, help_text='Item name')
    specification = models.TextField(blank=True, help_text='Specification')
    brand = models.CharField(max_length=100, blank=True, help_text='Brand')
    quantity = models.IntegerField(help_text='Quantity')
    unit = models.CharField(max_length=20, help_text='Unit')
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Unit price'
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text='Total amount'
    )
    suggested_supplier = models.CharField(
        max_length=200,
        blank=True,
        help_text='Suggested supplier'
    )

    # Additional Information
    remark = models.TextField(
        blank=True,
        help_text='Item remarks'
    )

    def __str__(self):
        return f"{self.purchase_request.request_no} - {self.item_name}"

    def save(self, *args, **kwargs):
        """Calculate total amount if not set"""
        if not self.total_amount:
            self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)


# ========== Asset Receipt Models ==========

class AssetReceiptStatus(models.TextChoices):
    """Asset receipt status choices"""
    DRAFT = 'draft', 'Draft'
    SUBMITTED = 'submitted', 'Submitted'
    INSPECTING = 'inspecting', 'Inspecting'
    PASSED = 'passed', 'Passed'
    REJECTED = 'rejected', 'Rejected'
    CANCELLED = 'cancelled', 'Cancelled'


class AssetReceipt(BaseModel):
    """
    Asset Receipt Model

    Records goods receipt and quality inspection.
    Inherits from BaseModel for organization isolation and soft delete.
    """
    class Meta:
        db_table = 'lifecycle_asset_receipt'
        verbose_name = 'Asset Receipt'
        verbose_name_plural = 'Asset Receipts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'receipt_no']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'purchase_request']),
        ]

    # Basic Information
    receipt_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Receipt number (auto-generated: RC+YYYYMM+NNNN)'
    )
    status = models.CharField(
        max_length=20,
        choices=AssetReceiptStatus.choices,
        default=AssetReceiptStatus.DRAFT,
        db_index=True,
        help_text='Receipt status'
    )

    # Linked Purchase Request
    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='receipts',
        help_text='Linked purchase request'
    )
    m18_purchase_order_no = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        help_text='M18 purchase order number'
    )

    # Receipt Information
    receipt_date = models.DateField(help_text='Receipt date')
    receipt_type = models.CharField(
        max_length=20,
        choices=[
            ('purchase', 'Purchase'),
            ('transfer', 'Transfer'),
            ('return', 'Return'),
        ],
        default='purchase',
        help_text='Receipt type'
    )

    # Supplier/Source Information
    supplier = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text='Supplier name'
    )
    delivery_no = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text='Delivery number'
    )

    # Receipt Personnel
    receiver = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='received_receipts',
        help_text='Receiver'
    )
    inspector = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='inspected_receipts',
        null=True,
        blank=True,
        help_text='Inspector'
    )

    # Inspection Result
    inspection_result = models.TextField(
        null=True,
        blank=True,
        help_text='Inspection result'
    )
    passed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Passed time'
    )

    # Additional Information
    remark = models.TextField(
        blank=True,
        help_text='Additional remarks'
    )

    def __str__(self):
        return f"{self.receipt_no} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        """Generate receipt number if not set"""
        if not self.receipt_no:
            self.receipt_no = self._generate_receipt_no()
        super().save(*args, **kwargs)

    def _generate_receipt_no(self):
        """Generate receipt number: RC+YYYYMM+NNNN"""
        prefix = timezone.now().strftime('%Y%m')
        last_receipt = AssetReceipt.objects.filter(
            receipt_no__startswith=f"RC{prefix}"
        ).order_by('-receipt_no').first()
        if last_receipt:
            seq = int(last_receipt.receipt_no[-4:]) + 1
        else:
            seq = 1
        return f"RC{prefix}{seq:04d}"


class AssetReceiptItem(BaseModel):
    """
    Asset Receipt Line Item

    Line items for asset receipts.
    Inherits from BaseModel for organization isolation and soft delete.
    """
    class Meta:
        db_table = 'lifecycle_asset_receipt_item'
        verbose_name = 'Asset Receipt Item'
        verbose_name_plural = 'Asset Receipt Items'
        unique_together = [['asset_receipt', 'sequence']]
        ordering = ['sequence']
        indexes = [
            models.Index(fields=['organization', 'asset_receipt']),
            models.Index(fields=['organization', 'asset_category']),
        ]

    # References
    asset_receipt = models.ForeignKey(
        AssetReceipt,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Asset receipt'
    )
    asset_category = models.ForeignKey(
        'assets.AssetCategory',
        on_delete=models.PROTECT,
        related_name='receipt_items',
        help_text='Asset category'
    )

    # Item Information
    sequence = models.IntegerField(default=1, help_text='Sequence number')
    item_name = models.CharField(max_length=200, help_text='Item name')
    specification = models.TextField(blank=True, help_text='Specification')
    brand = models.CharField(max_length=100, blank=True, help_text='Brand')

    # Quantity Inspection
    ordered_quantity = models.IntegerField(help_text='Ordered quantity')
    received_quantity = models.IntegerField(help_text='Received quantity')
    qualified_quantity = models.IntegerField(default=0, help_text='Qualified quantity')
    defective_quantity = models.IntegerField(default=0, help_text='Defective quantity')

    # Amount Information
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Unit price'
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text='Total amount'
    )

    # Asset Card Generation
    asset_generated = models.BooleanField(
        default=False,
        help_text='Asset cards generated'
    )

    # Additional Information
    remark = models.TextField(
        blank=True,
        help_text='Item remarks'
    )

    def __str__(self):
        return f"{self.asset_receipt.receipt_no} - {self.item_name}"

    def save(self, *args, **kwargs):
        """Calculate defective quantity if not set"""
        if not self.defective_quantity:
            self.defective_quantity = self.received_quantity - self.qualified_quantity
        if not self.total_amount:
            self.total_amount = self.received_quantity * self.unit_price
        super().save(*args, **kwargs)


# ========== Maintenance Models ==========

class MaintenanceStatus(models.TextChoices):
    """Maintenance status choices"""
    REPORTED = 'reported', 'Reported'
    ASSIGNED = 'assigned', 'Assigned'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class MaintenancePriority(models.TextChoices):
    """Maintenance priority choices"""
    LOW = 'low', 'Low'
    NORMAL = 'normal', 'Normal'
    HIGH = 'high', 'High'
    URGENT = 'urgent', 'Urgent'


class Maintenance(BaseModel):
    """
    Maintenance Record Model

    Records asset failure reports and repair processes.
    Inherits from BaseModel for organization isolation and soft delete.
    """
    class Meta:
        db_table = 'lifecycle_maintenance'
        verbose_name = 'Maintenance Record'
        verbose_name_plural = 'Maintenance Records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'maintenance_no']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'asset']),
            models.Index(fields=['organization', 'priority']),
        ]

    # Basic Information
    maintenance_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Maintenance number (auto-generated: MT+YYYYMM+NNNN)'
    )
    status = models.CharField(
        max_length=20,
        choices=MaintenanceStatus.choices,
        default=MaintenanceStatus.REPORTED,
        db_index=True,
        help_text='Maintenance status'
    )
    priority = models.CharField(
        max_length=20,
        choices=MaintenancePriority.choices,
        default=MaintenancePriority.NORMAL,
        help_text='Priority level'
    )

    # Asset Information
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.PROTECT,
        related_name='maintenance_records',
        help_text='Asset being maintained'
    )

    # Report Information
    reporter = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='reported_maintenance',
        help_text='Reporter'
    )
    report_time = models.DateTimeField(help_text='Report time')
    fault_description = models.TextField(help_text='Fault description')
    fault_photo_urls = models.JSONField(
        default=list,
        blank=True,
        help_text='Fault photo URLs'
    )

    # Technician Assignment
    technician = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='assigned_maintenance',
        null=True,
        blank=True,
        help_text='Assigned technician'
    )
    assigned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Assignment time'
    )

    # Maintenance Information
    start_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Start time'
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text='End time'
    )
    work_hours = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text='Work hours'
    )

    # Maintenance Result
    fault_cause = models.TextField(
        null=True,
        blank=True,
        help_text='Fault cause'
    )
    repair_method = models.TextField(
        null=True,
        blank=True,
        help_text='Repair method'
    )
    replaced_parts = models.TextField(
        null=True,
        blank=True,
        help_text='Replaced parts'
    )
    repair_result = models.TextField(
        null=True,
        blank=True,
        help_text='Repair result'
    )

    # Cost Information
    labor_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Labor cost'
    )
    material_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Material cost'
    )
    other_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Other cost'
    )
    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='Total cost'
    )

    # Verification Information
    verified_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='verified_maintenance',
        null=True,
        blank=True,
        help_text='Verifier'
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Verification time'
    )
    verification_result = models.TextField(
        null=True,
        blank=True,
        help_text='Verification result'
    )

    # Additional Information
    remark = models.TextField(
        blank=True,
        help_text='Additional remarks'
    )

    def __str__(self):
        return f"{self.maintenance_no} - {self.asset.asset_name}"

    def save(self, *args, **kwargs):
        """Generate maintenance number if not set"""
        if not self.maintenance_no:
            self.maintenance_no = self._generate_maintenance_no()
        super().save(*args, **kwargs)

    def _generate_maintenance_no(self):
        """Generate maintenance number: MT+YYYYMM+NNNN"""
        prefix = timezone.now().strftime('%Y%m')
        last_maintenance = Maintenance.objects.filter(
            maintenance_no__startswith=f"MT{prefix}"
        ).order_by('-maintenance_no').first()
        if last_maintenance:
            seq = int(last_maintenance.maintenance_no[-4:]) + 1
        else:
            seq = 1
        return f"MT{prefix}{seq:04d}"

    def calculate_total_cost(self):
        """Calculate total cost"""
        self.total_cost = self.labor_cost + self.material_cost + self.other_cost


class MaintenancePlanStatus(models.TextChoices):
    """Maintenance plan status choices"""
    ACTIVE = 'active', 'Active'
    PAUSED = 'paused', 'Paused'
    ARCHIVED = 'archived', 'Archived'


class MaintenancePlanCycle(models.TextChoices):
    """Maintenance plan cycle choices"""
    DAILY = 'daily', 'Daily'
    WEEKLY = 'weekly', 'Weekly'
    MONTHLY = 'monthly', 'Monthly'
    QUARTERLY = 'quarterly', 'Quarterly'
    YEARLY = 'yearly', 'Yearly'
    CUSTOM = 'custom', 'Custom'


class MaintenancePlan(BaseModel):
    """
    Maintenance Plan Model

    Defines scheduled maintenance plans.
    Inherits from BaseModel for organization isolation and soft delete.
    """
    class Meta:
        db_table = 'lifecycle_maintenance_plan'
        verbose_name = 'Maintenance Plan'
        verbose_name_plural = 'Maintenance Plans'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'plan_code']),
            models.Index(fields=['organization', 'status']),
        ]

    # Basic Information
    plan_name = models.CharField(max_length=200, help_text='Plan name')
    plan_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Plan code'
    )
    status = models.CharField(
        max_length=20,
        choices=MaintenancePlanStatus.choices,
        default=MaintenancePlanStatus.ACTIVE,
        help_text='Plan status'
    )

    # Target Objects
    target_type = models.CharField(
        max_length=20,
        choices=[
            ('category', 'By Category'),
            ('asset', 'By Asset'),
            ('location', 'By Location'),
        ],
        default='category',
        help_text='Target type'
    )
    asset_categories = models.ManyToManyField(
        'assets.AssetCategory',
        blank=True,
        related_name='maintenance_plans',
        help_text='Asset categories'
    )
    assets = models.ManyToManyField(
        'assets.Asset',
        blank=True,
        related_name='maintenance_plans',
        help_text='Specific assets'
    )
    # Note: Location field removed as Location model doesn't exist yet
    # Can be added later via custom_fields or dedicated Location model

    # Cycle Settings
    cycle_type = models.CharField(
        max_length=20,
        choices=MaintenancePlanCycle.choices,
        help_text='Cycle type'
    )
    cycle_value = models.IntegerField(default=1, help_text='Cycle value')
    start_date = models.DateField(help_text='Start date')
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text='End date'
    )

    # Reminder Settings
    remind_days_before = models.IntegerField(
        default=3,
        help_text='Remind days before'
    )
    remind_users = models.ManyToManyField(
        'accounts.User',
        blank=True,
        related_name='maintenance_plans_reminded',
        help_text='Remind users'
    )

    # Maintenance Content
    maintenance_content = models.TextField(help_text='Maintenance content')
    estimated_hours = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        help_text='Estimated hours'
    )

    # Additional Information
    remark = models.TextField(
        blank=True,
        help_text='Additional remarks'
    )

    def __str__(self):
        return f"{self.plan_code} - {self.plan_name}"


class MaintenanceTaskStatus(models.TextChoices):
    """Maintenance task status choices"""
    PENDING = 'pending', 'Pending'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    SKIPPED = 'skipped', 'Skipped'
    OVERDUE = 'overdue', 'Overdue'


class MaintenanceTask(BaseModel):
    """
    Maintenance Task Model

    Generated tasks from maintenance plans.
    Inherits from BaseModel for organization isolation and soft delete.
    """
    class Meta:
        db_table = 'lifecycle_maintenance_task'
        verbose_name = 'Maintenance Task'
        verbose_name_plural = 'Maintenance Tasks'
        ordering = ['scheduled_date', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'task_no']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'plan']),
            models.Index(fields=['organization', 'asset']),
        ]

    # Basic Information
    task_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Task number'
    )
    status = models.CharField(
        max_length=20,
        choices=MaintenanceTaskStatus.choices,
        default=MaintenanceTaskStatus.PENDING,
        help_text='Task status'
    )

    # Linked Plan
    plan = models.ForeignKey(
        MaintenancePlan,
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text='Maintenance plan'
    )

    # Task Information
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.PROTECT,
        related_name='maintenance_tasks',
        help_text='Asset'
    )

    # Schedule
    scheduled_date = models.DateField(help_text='Scheduled date')
    deadline_date = models.DateField(help_text='Deadline date')

    # Execution
    executor = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='maintenance_tasks',
        null=True,
        blank=True,
        help_text='Executor'
    )
    start_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Start time'
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text='End time'
    )

    # Execution Result
    execution_content = models.TextField(
        null=True,
        blank=True,
        help_text='Execution content'
    )
    execution_photo_urls = models.JSONField(
        default=list,
        blank=True,
        help_text='Execution photo URLs'
    )
    finding = models.TextField(
        null=True,
        blank=True,
        help_text='Findings'
    )
    next_maintenance_suggestion = models.TextField(
        null=True,
        blank=True,
        help_text='Next maintenance suggestion'
    )

    # Verification
    verified_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='verified_maintenance_tasks',
        null=True,
        blank=True,
        help_text='Verifier'
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Verification time'
    )

    # Additional Information
    remark = models.TextField(
        blank=True,
        help_text='Additional remarks'
    )

    def __str__(self):
        return f"{self.task_no} - {self.asset.asset_name}"


# ========== Disposal Models ==========

class DisposalRequestStatus(models.TextChoices):
    """Disposal request status choices"""
    DRAFT = 'draft', 'Draft'
    SUBMITTED = 'submitted', 'Submitted'
    APPRAISING = 'appraising', 'Appraising'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'
    EXECUTING = 'executing', 'Executing'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class DisposalType(models.TextChoices):
    """Disposal type choices"""
    SCRAP = 'scrap', 'Scrap'
    SALE = 'sale', 'Sale'
    DONATION = 'donation', 'Donation'
    TRANSFER = 'transfer', 'Transfer'
    DESTROY = 'destroy', 'Destroy'


class DisposalReason(models.TextChoices):
    """Disposal reason choices"""
    DAMAGE = 'damage', 'Damaged Beyond Repair'
    OBSOLETE = 'obsolete', 'Obsolete'
    EXPIRED = 'expired', 'Expired'
    EXCESS = 'excess', 'Excess'
    OTHER = 'other', 'Other'


class DisposalRequest(BaseModel):
    """
    Disposal Request Model

    Manages asset disposal requests with technical appraisal.
    Inherits from BaseModel for organization isolation and soft delete.
    """
    class Meta:
        db_table = 'lifecycle_disposal_request'
        verbose_name = 'Disposal Request'
        verbose_name_plural = 'Disposal Requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'request_no']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'disposal_type']),
        ]

    # Basic Information
    request_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Request number (auto-generated: DS+YYYYMM+NNNN)'
    )
    status = models.CharField(
        max_length=20,
        choices=DisposalRequestStatus.choices,
        default=DisposalRequestStatus.DRAFT,
        help_text='Request status'
    )
    disposal_type = models.CharField(
        max_length=20,
        choices=DisposalType.choices,
        default=DisposalType.SCRAP,
        help_text='Disposal type'
    )

    # Applicant Information
    applicant = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='disposal_requests',
        help_text='Applicant'
    )
    department = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.PROTECT,
        related_name='disposal_requests',
        limit_choices_to={'org_type': 'department'},
        help_text='Applicant department'
    )
    request_date = models.DateField(help_text='Request date')

    # Request Reason
    disposal_reason = models.TextField(help_text='Disposal reason')
    reason_type = models.CharField(
        max_length=50,
        choices=DisposalReason.choices,
        help_text='Reason type'
    )

    # Approval Information
    current_approver = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pending_disposal_approvals',
        help_text='Current approver'
    )

    # Additional Information
    remark = models.TextField(
        blank=True,
        help_text='Additional remarks'
    )

    def __str__(self):
        return f"{self.request_no} - {self.get_disposal_type_display()}"

    def save(self, *args, **kwargs):
        """Generate request number if not set"""
        if not self.request_no:
            self.request_no = self._generate_request_no()
        super().save(*args, **kwargs)

    def _generate_request_no(self):
        """Generate request number: DS+YYYYMM+NNNN"""
        prefix = timezone.now().strftime('%Y%m')
        last_request = DisposalRequest.objects.filter(
            request_no__startswith=f"DS{prefix}"
        ).order_by('-request_no').first()
        if last_request:
            seq = int(last_request.request_no[-4:]) + 1
        else:
            seq = 1
        return f"DS{prefix}{seq:04d}"


class DisposalItem(BaseModel):
    """
    Disposal Item Model

    Line items for disposal requests with technical appraisal.
    Inherits from BaseModel for organization isolation and soft delete.
    """
    class Meta:
        db_table = 'lifecycle_disposal_item'
        verbose_name = 'Disposal Item'
        verbose_name_plural = 'Disposal Items'
        unique_together = [['disposal_request', 'sequence']]
        ordering = ['sequence']
        indexes = [
            models.Index(fields=['organization', 'disposal_request']),
            models.Index(fields=['organization', 'asset']),
        ]

    # References
    disposal_request = models.ForeignKey(
        DisposalRequest,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Disposal request'
    )
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.PROTECT,
        related_name='disposal_items',
        help_text='Asset to dispose'
    )

    # Item Information
    sequence = models.IntegerField(default=1, help_text='Sequence number')

    # Original Value Information
    original_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text='Original value'
    )
    accumulated_depreciation = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text='Accumulated depreciation'
    )
    net_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text='Net value'
    )

    # Appraisal Information
    appraisal_result = models.TextField(
        null=True,
        blank=True,
        help_text='Appraisal result'
    )
    residual_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Estimated residual value'
    )
    appraised_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='appraised_disposal_items',
        null=True,
        blank=True,
        help_text='Appraiser'
    )
    appraised_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Appraisal time'
    )

    # Execution
    disposal_executed = models.BooleanField(
        default=False,
        help_text='Disposal executed'
    )
    executed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Execution time'
    )
    actual_residual_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Actual residual value'
    )
    buyer_info = models.TextField(
        null=True,
        blank=True,
        help_text='Buyer information'
    )

    # Additional Information
    remark = models.TextField(
        blank=True,
        help_text='Item remarks'
    )

    def __str__(self):
        return f"{self.disposal_request.request_no} - {self.asset.asset_name}"
